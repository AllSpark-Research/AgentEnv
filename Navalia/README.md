<h1 align="center">Navalia</h1>

<p align="center"><strong>Advancing Cowork Agents through Verifiable Task Synthesis and Long-Horizon Post-Training</strong></p>

<p align="center">
  🤗 <a href="https://huggingface.co/AllSpark-Research/Navalia-35B-A3B"><b>Hugging Face</b></a> &nbsp;|&nbsp;
  📄 <b>Tech Report</b> &nbsp;|&nbsp;
  🔬 <a href="Navalia-Harness"><b>Agent Harness</b></a>
</p>

## Introduction

Navalia-35B-A3B is an open-weight cowork agent post-trained from
[Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B). It is designed for tasks that
combine document retrieval, cross-document evidence integration, numerical analysis, and tool use.

The Navalia framework connects verifiable task synthesis with long-horizon agent post-training.
Starting from public corporate financial reports, it selects supporting evidence and builds
executable computation chains to construct analytical tasks with traceable sources and verifiable
answers. These tasks provide a foundation for training agents to investigate documents, perform
calculations, and carry an analysis through multiple tool interactions.

| Base | Qwen3.6-35B-A3B |
| --- | --- |
| Parameters | 35B total / 3B active (256 experts, 8 active) |
| Layers / hidden | 40 / 2048 |
| Context | 256K |
| Precision | bfloat16 |

## Performance

Results reported in the Navalia paper on financial research and professional workplace tasks.
Navalia improves over Qwen3.6-35B-A3B on all five benchmarks. Scores are percentages;
parentheses in the final row show gains over the base model in percentage points.

| Model | OfficeQA Pro<br>Correctness ↑ | FinSearchComp<br>T2&T3 Acc. ↑ | Finance Agent<br>Public-77 CB All-Pass ↑ | APEX-Agents-AA<br>Pass@1 ↑ | Workspace-Bench-Lite<br>Rubric Pass Rate ↑ |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Proprietary Frontier Models** | | | | | |
| GPT-5.4<sup>*</sup> | 50.40 | – | – | 33.26 | 52.9 |
| Claude Opus 4.6<sup>*</sup> | 55.60 | – | – | 33.04 | – |
| Claude Opus 4.7<sup>*</sup> | 46.6<sup>†</sup> | – | – | – | 66.6 |
| Gemini 3.1 Pro Preview<sup>*</sup> | 39.10 | – | – | 32.01 | 38.7 |
| Seed2.1 Pro<sup>*</sup> | 70.9<sup>†</sup> | – | – | – | 53.0<sup>†</sup> |
| Qwen3.7 Plus | 55.39 | 61.1 | 56.94 | 22.42<sup>*</sup> | 55.01 |
| **Large Open-Weight Models** | | | | | |
| Kimi-K3 | 67.92 | 68.8 | 65.02 | 37.13 | 60.56 |
| DeepSeek-V4 Flash | 65.66 | 65.2 | 58.87 | 36.43 | 58.08 |
| Qwen3.8 Flash Next | 64.04 | 70.3 | 58.48 | 38.86 | 61.96 |
| GLM-5.2 | 63.41 | 65.7 | 63.1 | 33.89 | 59.34 |
| Kimi-K2.6 | 58.65 | 59.1 | 54.49 | 29.28 | 54.96 |
| Qwen3.5-397B-A17B | 47.62 | 50.4 | 51.82 | 14.60 | 50.51 |
| **Baseline** | | | | | |
| Qwen3.6-35B-A3B | 39.6 | 41.7 | 43.19 | 12.24 | 46.2 |
| **Navalia-35B-A3B** | **62.66** (+23.06) | **55.80** (+14.10) | **57.10** (+13.91) | **25.44** (+13.20) | **59.27** (+13.07) |

<sup>*</sup> Results taken from the original papers, technical reports, or official websites;
other results were obtained under the paper's unified evaluation setup. A marker on a model name
applies to the entire row; a marker on a score applies only to that entry.
<sup>†</sup> Results use a different document representation or agent harness and are included
for reference.

## Agent Harness

[Navalia-Harness](Navalia-Harness) is an agent harness for trajectory collection and online RL
rollouts, with a lightweight ReAct loop and FIFO context management. It connects to a model
served by SGLang and defines shell, file, and search tools.

Our experiments execute shell and file operations in an isolated sandbox for each task.
This repository includes the agent loop, tool definitions, and a generic sandbox interface;
the sandbox backend is not included. Connect your own execution environment to run trajectory collection.

```text
Navalia-Harness/
├── navalia/
│   ├── agent.py             Agent loop and FIFO context
│   ├── client.py            Model API client
│   ├── tools.py             Tool definitions and dispatch
│   ├── sandbox.py           Sandbox interface and task lifecycle
│   ├── corpus.py            Task document preparation
│   ├── file_state_cache.py  File read and edit state
│   ├── prompts.py           User prompt builder
│   └── run.py               Collection entry point
├── conf/                    Model settings and prompts
└── examples/                Example task and document
```

The system prompt and original question stay in context. When more than 30 assistant turns
accumulate, the oldest 10 are removed together with their tool calls and results. Historical
reasoning is preserved for the turns that remain, and working files persist throughout the task.
Raw traces retain model responses, reasoning, and tool interactions.

See the [Harness README](Navalia-Harness/README.md) for setup and trajectory collection.
Model serving instructions are in the
[model card](https://huggingface.co/AllSpark-Research/Navalia-35B-A3B).

## Acknowledgements

We thank the teams behind the following models and training frameworks:

- [Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)
- [Dressage](https://github.com/Accio-Lab/Dressage)
- [slime](https://github.com/THUDM/slime)
- [Seed2.0](https://seed.bytedance.com/en/seed2)
