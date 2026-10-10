<div align="center">

<h1 align="center">
  <a href="https://github.com/AllSpark-Research"><img src="https://avatars.githubusercontent.com/u/277376690?s=200&amp;v=4" alt="AllSpark logo" width="64" height="64" align="absmiddle"></a>
  &nbsp;AgentEnv
</h1>

### Environments for agents. Data from interaction. Diversity at scale.

**AllSpark Research · Agent Environment & Data Synthesis**

[![GitHub](https://img.shields.io/badge/GitHub-AgentEnv-181717?style=flat-square&logo=github)](https://github.com/AllSpark-Research/AgentEnv)
[![CompoWorld](https://img.shields.io/badge/arXiv-CompoWorld-B31B1B?style=flat-square&logo=arxiv)](https://arxiv.org/abs/2609.33665)
[![Skill2Env](https://img.shields.io/badge/arXiv-Skill2Env-B31B1B?style=flat-square&logo=arxiv)](https://arxiv.org/abs/2609.33772)

**English** · [简体中文](README_CN.md)

</div>

---

## Vision

General agents need rich environments to act in, meaningful tasks to solve, and reliable feedback to learn from. **AgentEnv** brings together AllSpark's research on environment synthesis, interaction data generation, and environment scaling.

We explore how reusable tools, services, and skills can become executable environments, and how interaction with these environments can produce useful training signals. Our goal is to scale the diversity of environments and tasks, spanning more domains, service combinations, and workflows to create richer training experiences for general agents.

| Environment synthesis | Data synthesis | Environment scaling |
| :--- | :--- | :--- |
| Build executable worlds with tools, state, workspaces, and task evaluators. | Turn agent interaction into trajectories and feedback for post-training. | Expand environment and task diversity across domains, service combinations, and workflows. |

<div align="center">

**Tools, Services & Skills → Executable Environments → Interaction & Feedback → Agent Training**

</div>

## Research

Our work explores complementary directions: **composing environments to broaden experience**, **shaping environments to challenge capabilities**, and **constructing verifiable tasks from real-world documents**.

### CompoWorld

**Compositional Environment Scaling for General Agents**

CompoWorld composes reusable services into tasks that require information and actions to flow across services. Verified trajectories support supervised fine-tuning, while a completion-focused rubric reward supports reinforcement learning.

**448 services · 10,130 tools · 3K SFT trajectories · 1K RL tasks**

Training Qwen3.6-35B-A3B yields a **9.17-point average improvement across eight benchmarks**, as reported in the paper.

[Read the paper ↗](https://arxiv.org/abs/2609.33665) · [Model](https://huggingface.co/AllSpark-Research/CompoWorld) · [Project & examples](CompoWorld/README.md) · [Example data](CompoWorld/compoworld_example_data_20.jsonl)

### Skill2Env

**Capability-Oriented Environment Synthesis from Skills for General Agents**

Skill2Env turns reusable skills into executable tasks through capability-driven difficulty patterns and task blueprints. **Iterative Task Hardening** uses solver execution evidence to refine environments and strengthen challenges.

**2,963 executable tasks · 1.5K SFT trajectories**

Supervised fine-tuning on the generated trajectories produces improvements across a broad range of agent benchmarks, as reported in the paper.

[Read the paper ↗](https://arxiv.org/abs/2609.33772) · [Model](https://huggingface.co/AllSpark-Research/Skill2Env) · [Example tasks](./Skill2Env/)

## Resources

| Work | Focus | Paper |
| :--- | :--- | :--- |
| **CompoWorld** | Scaling through service composition | [arXiv:2609.33665](https://arxiv.org/abs/2609.33665) |
| **Skill2Env** | Synthesis and task hardening guided by capability demands | [arXiv:2609.33772](https://arxiv.org/abs/2609.33772) |

These works are collected here at **[AllSpark-Research/AgentEnv](https://github.com/AllSpark-Research/AgentEnv)**.

## Citation

If these works inform your research, please cite the corresponding papers.

<details>
<summary><strong>BibTeX</strong></summary>

```bibtex
@article{yang2026compoworld,
  title   = {CompoWorld: Compositional Environment Scaling for General Agents},
  author  = {Yang, Xiao-Wen and Xu, Weiyi and Da, Wen and Xu, Hang and Li, Canwei and You, Hong-Jie and Dong, Pusen and Zeng, Yucheng and Luo, Zhaokai and Li, Yu-Feng and Hu, Yao and Chuan, Mu},
  journal = {arXiv preprint arXiv:2609.33665},
  year    = {2026},
  url     = {https://arxiv.org/abs/2609.33665}
}

@article{xu2026skill2env,
  title={Skill2Env: Capability-Oriented Environment Synthesis from Skills for General Agents},
  author={Xu, Weiyi and Yang, Xiaowen and Da, Wen and Xu, Hang and Li, Canwei and You, Hongjie and Dong, Pusen and Zeng, Yucheng and Luo, Zhaokai and Chuan, Mu},
  journal={arXiv preprint arXiv:2609.33772},
  year={2026}
}
```

</details>

---

<div align="center">

**[AllSpark Research](https://github.com/AllSpark-Research)** · Building environments for agents to learn by doing.

</div>
