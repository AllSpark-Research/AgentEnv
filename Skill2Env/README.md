<div align="center">

# Skill2Env

**Capability-Oriented Environment Synthesis from Skills for General Agents**

**[✦ AllSpark Research](https://github.com/AllSpark-Research)**

[![Paper](https://img.shields.io/badge/arXiv-2609.33772-B31B1B?style=flat-square&logo=arxiv)](https://arxiv.org/abs/2609.33772)
[![Model](https://img.shields.io/badge/Hugging_Face-Skill2Env-FFD21E?style=flat-square&logo=huggingface)](https://huggingface.co/AllSpark-Research/Skill2Env)
[![Tasks](https://img.shields.io/badge/Data-20_example_tasks-2563EB?style=flat-square)](#example-tasks)

[← AgentEnv](../README.md) · [Paper](https://arxiv.org/abs/2609.33772) · [Model](https://huggingface.co/AllSpark-Research/Skill2Env) · [Example tasks](#example-tasks)

</div>

## Overview

Skill2Env turns reusable skills into executable environments for agent post-training. Capability-oriented difficulty patterns and task blueprints guide the construction of task instructions, execution substrates, workspaces, and rubric-based evaluators. Iterative Task Hardening uses solver execution evidence to strengthen task designs.

We construct **2,963 tasks** and train Qwen3.6-35B-A3B with **1.5K SFT trajectories**, achieving an average improvement of **8.4 points across seven agent benchmarks**. 

| Benchmark | Qwen3.6-35B-A3B | Skill2Env | Improvement |
| :--- | ---: | ---: | ---: |
| Terminal-Bench 2.1 | 44.9 | **58.4** | +13.5 |
| SWE-bench Multilingual | 63.3 | **71.0** | +7.7 |
| SkillsBench | 32.5 | **46.9** | +14.3 |
| Claw-Eval | 55.8 | **61.3** | +5.5 |
| τ³-Banking | 10.7 | **15.1** | +4.5 |
| AutomationBench | 10.3 | **17.7** | +7.3 |
| VitaBench | 38.9 | **44.8** | +5.9 |
| **Average** | **36.6** | **45.0** | **+8.4** |

Scores and gains are rounded independently to one decimal place; gains are computed from unrounded scores. Average is the unweighted mean across the seven benchmarks. See the [paper](https://arxiv.org/abs/2609.33772) for details.

## Example tasks

The [`tasks/`](./tasks/) directory contains **20 example tasks** in [Harbor task format](https://github.com/harbor-framework/harbor).

Each task includes its instruction, environment, initial workspace, source skill, and evaluator.

## Task format

```text
tasks/<task-name>/
├── instruction.md
├── task.toml
├── environment/
│   ├── Dockerfile
│   ├── setup.sh
│   └── workspace/
│       ├── _skill_ref/
│       │   ├── SKILL.md
│       │   └── ...
│       └── ...
└── tests/
    ├── test.sh
    ├── run_verifier.py
    ├── hybrid_verify.py
    ├── verify.py
    └── eval_spec.json
```

| File or directory | Contents |
| :--- | :--- |
| `instruction.md` | Task instructions. |
| `task.toml` | Task configuration. |
| `environment/Dockerfile` | Container build recipe with runtime dependencies. |
| `environment/setup.sh` | Task-specific setup executed during the container build. |
| `environment/workspace/` | Initial input files, reference materials, and local tools. |
| `environment/workspace/_skill_ref/` | Source skill documentation and accompanying resources available to the agent. |
| `tests/test.sh` | Verifier entry point. |
| `tests/verify.py` | Task-specific deterministic checks. |
| `tests/eval_spec.json` | Evaluation rubric, weights, methods, and judge instructions where applicable. |
| `tests/hybrid_verify.py` | Executes rubric evaluation and aggregates item scores. |
| `tests/run_verifier.py` | Writes the final reward in Harbor's verifier output format. |

## Evaluation

Tasks receive a **continuous reward between 0 and 1**, aggregated from weighted rubric items.

- **16 tasks** combine deterministic checks with LLM judging.
- **4 tasks** use deterministic evaluation only.

Hybrid evaluation requires `JUDGE_BASE_URL` and `JUDGE_MODEL`, plus `JUDGE_API_KEY` when required by the endpoint.

For citation information, see [AgentEnv's BibTeX](../README.md#citation).
