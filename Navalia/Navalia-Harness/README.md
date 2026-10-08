# Navalia Harness

An agent harness for trajectory collection and online RL rollouts, with FIFO context management.

## Quick Start

Use Python 3.11+ and a running SGLang model service. See the
[model card](https://huggingface.co/AllSpark-Research/Navalia-35B-A3B#quickstart) for deployment.
Our experiments use a separate sandbox for each task. The backend is not included;
connect your sandbox through `create_sandbox()` in `navalia/sandbox.py` before running.

Set `SERPER_API_KEY` for web search and `MODEL_API_KEY` if your model service requires
authentication; otherwise use `EMPTY`. Match `model.name` in `conf/default.yaml` to the
served model name. From the repository root:

```bash
cd Navalia/Navalia-Harness
pip install -e .

export SERPER_API_KEY=your_serper_key
export MODEL_API_KEY=EMPTY
export MODEL_BASE_URL=http://localhost:8000/v1

navalia-collect \
  --config conf/default.yaml \
  --input examples/tasks.jsonl \
  --corpus examples/corpus \
  --output runs/example \
  --concurrency 1
```

Each input line contains a task ID, question, and document list:

```json
{"task_id":"example-revenue","question":"What was the revenue growth?","corpus_subset":["sample.txt"]}
```

`corpus_subset` lists files relative to `--corpus`. Use an empty output directory;
raw trajectories are saved under `--output`. For online RL, call `run_agent()` in
`navalia/agent.py` from your training framework's rollout worker.
