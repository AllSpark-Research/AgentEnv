from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import yaml

from .agent import run_agent
from .client import ModelClient
from .sandbox import SandboxBackendRequired, TaskSandbox
from .tools import TOOL_SCHEMAS


def load_tasks(path: Path) -> list[dict]:
    tasks, seen = [], set()
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        task_id = raw.get("task_id", raw.get("spec_id", raw.get("uid")))
        if task_id is None or not str(task_id) or str(task_id) in seen:
            raise ValueError(f"Missing or duplicate task ID on line {line_number}")
        if not isinstance(raw.get("question"), str) or not raw["question"].strip():
            raise ValueError(f"Missing question on line {line_number}")
        subset = raw.get("corpus_subset")
        if not isinstance(subset, list) or not subset or not all(isinstance(p, str) and p for p in subset):
            raise ValueError(f"corpus_subset must be a nonempty list of paths on line {line_number}")
        source_files = raw.get("source_files")
        if source_files is not None and (
            not isinstance(source_files, list) or not all(isinstance(p, str) for p in source_files)
        ):
            raise ValueError(f"source_files must be a list on line {line_number}")
        seen.add(str(task_id))
        tasks.append(
            {
                "task_id": str(task_id),
                "question": raw["question"],
                "corpus_subset": subset,
                "source_files": source_files,
            }
        )
    return tasks


def save_json(path: Path, data: dict):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def validate_config(config: dict):
    model = config["model"]
    if not model.get("name") or not model.get("base_url"):
        raise ValueError("model.name and model.base_url are required")
    agent = config.get("agent", {})
    if agent.get("max_turns", 200) != 200:
        raise ValueError("The provided system prompt specifies a 200-turn budget; keep max_turns at 200")
    if not 0 <= agent.get("fifo_min_turns", 20) < agent.get("fifo_max_turns", 30):
        raise ValueError("FIFO limits must satisfy 0 <= min < max")


async def run(args):
    config = yaml.safe_load(args.config.read_text())
    validate_config(config)
    if args.concurrency < 1:
        raise ValueError("concurrency must be positive")
    tasks = load_tasks(args.input)
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("limit must be positive")
        tasks = tasks[: args.limit]
    if not tasks:
        raise ValueError("No tasks found")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Use an empty output directory to keep previous trajectories intact")
    corpus = args.corpus.resolve(strict=True) if args.corpus is not None else None
    system = (args.config.parent / config.get("system_prompt", "system.txt")).read_text()
    user_suffix = (args.config.parent / config.get("user_suffix", "user_suffix.txt")).read_text()
    args.output.mkdir(parents=True, exist_ok=True)
    save_json(
        args.output / "run.json",
        {
            "schema_version": 2,
            "config": config,
            "system_prompt": system,
            "user_suffix": user_suffix,
            "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
            "task_count": len(tasks),
            "concurrency": args.concurrency,
        },
    )
    client = ModelClient(config["model"])
    semaphore = asyncio.Semaphore(args.concurrency)
    agent = config.get("agent", {})

    async def one(task):
        async with semaphore:
            filename = hashlib.sha256(task["task_id"].encode()).hexdigest()[:24] + ".json"
            try:
                async with TaskSandbox(
                    task["task_id"], task["corpus_subset"], config.get("sandbox", {}), corpus
                ) as env:
                    result = await run_agent(
                        client,
                        uid=task["task_id"],
                        question=task["question"],
                        source_files=task["source_files"],
                        sandbox=env.sandbox,
                        max_steps=agent.get("max_turns", 200),
                        fifo_max=agent.get("fifo_max_turns", 30),
                        fifo_min=agent.get("fifo_min_turns", 20),
                        verbose=False,
                        tool_schemas=TOOL_SCHEMAS,
                        system_prompt=system,
                        user_suffix=user_suffix,
                    )
                    trace = asdict(result)
                    trace.update(sandbox_id=env.id, corpus_preparation=env.preparation)
                    save_json(args.output / filename, trace)
            except SandboxBackendRequired:
                raise
            except Exception as error:
                trace = {
                    "uid": task["task_id"],
                    "question": task["question"],
                    "error": type(error).__name__,
                    "finish_reason": "collection_error",
                }
                save_json(args.output / filename, trace)
            print(f"{task['task_id']}: {trace['finish_reason']}", flush=True)
            return trace.get("error") is not None

    jobs = [asyncio.create_task(one(task)) for task in tasks]
    try:
        errors = await asyncio.gather(*jobs)
    finally:
        for job in jobs:
            if not job.done():
                job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
        await client.aclose()
    return 1 if any(errors) else 0


def main():
    parser = argparse.ArgumentParser(
        description="Collect raw FIFO tool-use trajectories. Requires a user-supplied sandbox backend."
    )
    parser.add_argument("--config", type=Path, default=Path("conf/default.yaml"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--corpus", type=Path, help="Upload local task documents; omit to use a preloaded sandbox corpus"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(run(args)))
    except (ValueError, FileNotFoundError, KeyError, ImportError, SandboxBackendRequired) as error:
        parser.exit(2, f"Configuration error: {error}\n")


if __name__ == "__main__":
    main()
