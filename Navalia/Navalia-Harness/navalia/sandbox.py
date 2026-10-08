from __future__ import annotations

import logging
import shlex
from pathlib import Path
from typing import Protocol

from .corpus import DEFAULT_CORPUS_ROOT, trim_corpus_to_task
from .tools import sandbox_run

logger = logging.getLogger(__name__)


class Sandbox(Protocol):
    id: str

    async def run(self, command: str, *, timeout_ms: int = 120000) -> tuple[str, str, int]:
        """Run a fresh shell in /workspace; stop the command on timeout."""
        ...

    async def write_file(self, path: str, content: bytes) -> None: ...

    async def close(self) -> None: ...


class SandboxBackendRequired(RuntimeError):
    pass


async def create_sandbox(task_id: str, config: dict) -> Sandbox:
    raise SandboxBackendRequired(
        "No sandbox backend is included. Implement create_sandbox() in navalia/sandbox.py "
        "with your execution environment before collecting trajectories."
    )


class TaskSandbox:
    def __init__(self, task_id: str, subset: list[str], config: dict, corpus: Path | None = None):
        self.task_id, self.subset, self.config, self.corpus = task_id, subset, config, corpus
        self.sandbox = None
        self.id = None
        self.preparation = None

    async def __aenter__(self):
        self.sandbox = await create_sandbox(self.task_id, self.config)
        try:
            self.id = self.sandbox.id
            if self.corpus is not None:
                root = self.corpus.resolve(strict=True)
                selected = []
                names = set()
                for name in self.subset:
                    path = (root / name).resolve(strict=True)
                    if not path.is_relative_to(root) or not path.is_file() or path.name in names:
                        raise ValueError("Corpus paths must be files inside --corpus with distinct basenames")
                    names.add(path.name)
                    selected.append(path)
                _, _, code = await sandbox_run(self.sandbox, f"mkdir -p {shlex.quote(DEFAULT_CORPUS_ROOT)}")
                if code not in (0, None):
                    raise RuntimeError("Cannot create the sandbox corpus directory")
                for path in selected:
                    await self.sandbox.write_file(f"{DEFAULT_CORPUS_ROOT}/{path.name}", path.read_bytes())
            self.preparation = await trim_corpus_to_task(self.sandbox, self.subset)
            if not self.preparation["ok"]:
                raise ValueError("The sandbox corpus does not contain all requested documents")
            return self
        except BaseException:
            await self.__aexit__(None, None, None)
            raise

    async def __aexit__(self, exc_type, exc, tb):
        if self.sandbox is not None:
            try:
                await self.sandbox.close()
            except Exception as error:
                logger.warning("Sandbox cleanup failed: %s", type(error).__name__)
