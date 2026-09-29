<div align="center">

# CompoWorld

**Compositional Environment Scaling for General Agents**

**[✦ AllSpark Research](https://github.com/AllSpark-Research)**

[![Paper](https://img.shields.io/badge/arXiv-2609.33665-B31B1B?style=flat-square&logo=arxiv)](https://arxiv.org/abs/2609.33665)
[![Model](https://img.shields.io/badge/Hugging_Face-CompoWorld-FFD21E?style=flat-square&logo=huggingface)](https://huggingface.co/AllSpark-Research/CompoWorld)
[![Data](https://img.shields.io/badge/Data-20_example_trajectories-2563EB?style=flat-square)](compoworld_example_data_20.jsonl)

[← AgentEnv](../README.md) · [Paper](https://arxiv.org/abs/2609.33665) · [Model](https://huggingface.co/AllSpark-Research/CompoWorld) · [Example data](compoworld_example_data_20.jsonl)

</div>

## Overview

CompoWorld scales environment and task diversity by composing reusable services into executable workflows. Tasks require agents to discover tools, connect information, and coordinate actions across services. Verified trajectories support supervised fine-tuning (SFT), and a completion-focused rubric reward guides reinforcement learning (RL).

The paper constructs **448 services with 10,130 tools**. Training Qwen3.6-35B-A3B with **3K SFT trajectories and 1K RL tasks** improves its average score by **9.17 points across eight benchmarks**. See the [paper](https://arxiv.org/abs/2609.33665) for details.

## Performance

**+9.17 points on average across eight benchmarks**, with **+22.00 on AutomationBench**, **+15.19 on SkillsBench**, and **+10.50 on VitaBench** over the Qwen3.6-35B-A3B backbone.

| Benchmark | Qwen3.6-35B-A3B | CompoWorld | Improvement |
| :--- | ---: | ---: | ---: |
| τ³-Banking | 10.65 | **16.49** | +5.84 |
| DeepPlanning | 26.04 | **35.21** | +9.17 |
| VitaBench | 38.94 | **49.44** | +10.50 |
| VitaBench 2.0 | 34.47 | **36.09** | +1.62 |
| AutomationBench | 10.33 | **32.33** | +22.00 |
| WildClawBench | 44.28 | **47.46** | +3.18 |
| SkillsBench | 32.52 | **47.71** | +15.19 |
| ALE | 7.77 | **13.59** | +5.82 |

Results from [Table 1 of the paper](https://arxiv.org/pdf/2609.33665#page=8). Higher is better; improvements are absolute score-point differences, not relative percentages. See the paper for benchmark-specific metrics and evaluation settings.

## Example data

[**compoworld_example_data_20.jsonl**](compoworld_example_data_20.jsonl) contains **20 example interaction trajectories** (approximately **3.85 MB**), stored as one JSON object per line. This is a sample, not the full training dataset.

| Field | Contents |
| :--- | :--- |
| `tools` | Tool definitions and parameter schemas. |
| `messages` | System and user messages, assistant responses and tool calls, and tool results. Some assistant messages include `reasoning_content`. |
| `meta` | Task identifiers, services, domain, capabilities, scores, and rollout statistics. |
| `source` | Source label for the trajectory. |

For citation information, see [AgentEnv's BibTeX](../README.md#citation).
