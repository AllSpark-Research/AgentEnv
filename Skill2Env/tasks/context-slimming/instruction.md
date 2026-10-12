You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

我维护着一个 OpenClaw agent（代号项目夜航星，我们自己的运维助理），它工作区里的注入上下文已经失控了。OpenClaw 每轮对话会把 agent_workspace/ 目录顶层的所有 *.md 文件原样注入系统提示——现在这些文件一共 18,975 字节，中文按每 3 字节约 1 token 估算，每轮光注入就要烧掉六千多 token，账单吃不消。请你做一次彻底的上下文瘦身。

agent_workspace/ 是一个 git 仓库（已有一次初始提交）。请直接在仓库里动手，最终交付三件事：

一、瘦身后的 agent_workspace/：
- 目标：顶层注入的 *.md 总字节数 ≤ 6,000 字节，且单个文件 ≤ 1,500 字节（utf-8 字节计）。
- 每轮真正必须知道的信息留在顶层：完整的安全红线必须原义保留在每轮注入的内容里（它们的唯一权威来源应当是 AGENTS.md），凭证位置、维护窗口、技能索引也要留在注入集里。
- 详细操作手册（审查流程、命令参考之类的长文）移到按需加载的子目录里，并在顶层文件里留下准确的引用，不许直接把内容弄丢。
- 过期的引导文件、纯重复的身份文件、模板残留、过时段落——该删就删。删之前想清楚有没有独家信息要先抢救。
- 跨文件重复的内容（红线、记忆管理规则、身份描述等）收敛到唯一来源，其他地方最多留一句引用。文件之间有口径冲突时以文件自己声明的优先级为准。

二、瘦身报告：写到 ./SLIMMING_REPORT.md（当前工作目录根，注意别放进 agent_workspace/ 里——放那儿它自身也会被注入）。报告用中文，至少包含：逐文件的字节数前后对照表；你对每个文件做了什么（保留/改写/移出/删除）和理由；跨文件去重复的"唯一来源"对照表；详细内容移去了哪里；以及按 3 字节 ≈ 1 token 估算的每轮节省量。报告里的数字必须是你瘦身完成后实测的。

三、在 agent_workspace/ 仓库里把全部变更提交成一个 commit，提交信息说明这是上下文瘦身；提交后工作区要干净。

提示：不妨先看看 _skill_ref/ 里有什么可参考的方法，再决定怎么动手。