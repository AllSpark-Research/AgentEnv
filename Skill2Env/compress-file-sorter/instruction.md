You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

月底归档日。我是恒宇贸易有限公司的财务助理，`incoming_archives/` 下攒了五个压缩包（有 zip、tar.gz、7z，其中一个带密码、一个来源不太放心），需要全部按公司《单据分类规范》整理归档。

请你完成：

1. 阅读 `documents/单据分类规范.md` 和 `notes/王经理的邮件.md`，两者都是本次整理的依据，缺一不可。
2. 把 `incoming_archives/` 下的压缩包按规范解压并分类到 `sorted_documents/`：文件名命中类目的归入对应类目目录（多个类目同时命中时严格按规范给定的优先级归类；分类依据是文件名，不是文件内容）；不命中任何类目的放入规范指定的目录；同名文件按规范的冲突策略处理，不得覆盖或丢弃。
3. 规范的安全条款必须遵守——不符合安全检查的压缩包不得强制解出，按规范处置，其余压缩包照常处理。
4. 在 `sorted_documents/` 整理完成后，写一份 `sorting_report.md`（工作区根目录）给王经理，内容至少包括：每个压缩包的处理结果（成功/失败及原因）、各类目的文件数量、待人工复核的文件清单、同名冲突与安全异常的处理说明。

要求整理结果真实反映实际落位，数量与实际文件一致，报告要能直接交给主管审阅。