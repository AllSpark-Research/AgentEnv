You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

你是云弈围棋道场的教务助手。周五上期末复盘课，需要把学员对局做成一批可以在浏览器里互动打谱的复盘网页。工作区里的 sgf_dump/ 收集了各处来的素材，README.md 和 STUDY_PLAN.md 是教务会定的整理规范（收录条件、命名约定、关键手要求、清单格式都在里面）。

请按规范办三件事：
1. 从 sgf_dump/ 里筛出所有符合收录条件的对局棋谱，用道场统一自带的 SGF 打谱网页工具（工作区内已附带，含说明文档，全班页面样式要保持一致）为每一盘生成互动打谱网页，全部放在 study_pack/ 目录下，文件名按规范的命名约定来；
2. 复盘课要求网页打开后直接停在关键手上，认定规则和处理方式见规范；
3. 在 study_pack/ 下生成 manifest.json 清单，字段与统计口径严格按规范，家长会照着清单逐条核对。

提醒：sgf_dump/ 里有损坏的文件、旧编码（GB2312）的棋谱，也有同一盘棋的重复导出和往年的旧谱，请妥善处理，不要为了凑数生成规范之外的页面。