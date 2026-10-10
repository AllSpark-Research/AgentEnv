<div align="center">

<h1 align="center">
  <a href="https://github.com/AllSpark-Research"><img src="https://avatars.githubusercontent.com/u/277376690?s=200&amp;v=4" alt="AllSpark logo" width="64" height="64" align="absmiddle"></a>
  &nbsp;AgentEnv
</h1>

### 构建交互环境，合成训练数据，扩展环境与任务多样性。

**AllSpark Research · 智能体环境与数据合成**

[![GitHub](https://img.shields.io/badge/GitHub-AgentEnv-181717?style=flat-square&logo=github)](https://github.com/AllSpark-Research/AgentEnv)
[![CompoWorld](https://img.shields.io/badge/arXiv-CompoWorld-B31B1B?style=flat-square&logo=arxiv)](https://arxiv.org/abs/2609.33665)
[![Skill2Env](https://img.shields.io/badge/arXiv-Skill2Env-B31B1B?style=flat-square&logo=arxiv)](https://arxiv.org/abs/2609.33772)

[English](README.md) · **简体中文**

</div>

---

## 研究愿景

通用智能体需要丰富的交互环境、有意义的任务，以及可靠的学习反馈。**AgentEnv** 汇集 AllSpark 在环境合成、交互数据生成与环境扩展（Environment Scaling）方面的研究。

我们探索如何将可复用的工具、服务与技能转化为可执行环境，再通过环境交互产生有效的训练信号。我们的目标是扩展环境与任务的多样性，覆盖更多领域、服务组合与工作流，为通用智能体提供更丰富的训练经验。

| 环境合成 | 数据合成 | 环境扩展 |
| :--- | :--- | :--- |
| 构建包含工具、状态、工作空间与任务评估器的可执行环境。 | 将智能体交互转化为用于后训练的轨迹与反馈。 | 覆盖更多领域、服务组合与工作流，扩展环境与任务的多样性。 |

<div align="center">

**工具、服务与技能 → 可执行环境 → 交互与反馈 → 智能体训练**

</div>

## 研究工作

我们沿着互补路径展开研究：**通过环境组合拓宽经验**、**围绕能力需求构建更具挑战性的环境**，以及**从真实文档构造可验证任务**。

### CompoWorld

**Compositional Environment Scaling for General Agents**  
面向通用智能体的组合式环境扩展

CompoWorld 将可复用服务组合为需要跨服务传递信息、协同执行操作的任务。经过验证的轨迹用于监督微调，以任务完成为导向的评分准则奖励用于强化学习。

**448 个服务 · 10,130 个工具 · 3K 条 SFT 轨迹 · 1K 个 RL 任务**

论文报告：基于 Qwen3.6-35B-A3B 训练后，在 **8 个基准上平均提升 9.17 分**。

[阅读论文 ↗](https://arxiv.org/abs/2609.33665) · [模型](https://huggingface.co/AllSpark-Research/CompoWorld) · [项目与示例](CompoWorld/README.md) · [示例数据](CompoWorld/compoworld_example_data_20.jsonl)

### Skill2Env

**Capability-Oriented Environment Synthesis from Skills for General Agents**  
从技能出发、以能力为导向的通用智能体环境合成

Skill2Env 通过能力导向的难度模式与任务蓝图，将可复用技能转化为可执行任务。**迭代式任务强化（Iterative Task Hardening）** 利用求解智能体的执行证据改进环境，逐步增强任务挑战。

**2,963 个可执行任务 · 1.5K 条 SFT 轨迹**

论文报告：使用生成的轨迹进行监督微调，在多项智能体基准上取得提升。

[阅读论文 ↗](https://arxiv.org/abs/2609.33772) · [模型](https://huggingface.co/AllSpark-Research/Skill2Env) · [示例任务](./Skill2Env/)

## 资源入口

| 工作 | 研究重点 | 论文 |
| :--- | :--- | :--- |
| **CompoWorld** | 通过服务组合扩展环境与任务 | [arXiv:2609.33665](https://arxiv.org/abs/2609.33665) |
| **Skill2Env** | 能力需求引导的环境合成与任务强化 | [arXiv:2609.33772](https://arxiv.org/abs/2609.33772) |

相关工作统一收录于 **[AllSpark-Research/AgentEnv](https://github.com/AllSpark-Research/AgentEnv)**。

## 引用

如果这些工作对你的研究有所帮助，欢迎引用对应论文。

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

**[AllSpark Research](https://github.com/AllSpark-Research)** · 让智能体在交互中学习。

</div>
