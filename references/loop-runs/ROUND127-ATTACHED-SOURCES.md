# ROUND127｜本地附件资料接入（2026-08-15）

## round_id

`LOOP-20260815-ATTACHED-SOURCES-01`

## question_scope

将用户提供的《看盘手册(综合最终）》与《1互容特征汇总表》整理为可审计、可回滚的知识模块，并接入现有 NATAL-1.0 / LOOP-1.0 架构。

## sources_read

- `R38`：看盘手册(综合最终）.docx，用户提供的综合个人整理；章节定位：知识体系概览、飞星系统、飞星/互容/接纳、推运部分。
- `R39`：1互容特征汇总表.docx，用户提供的宫位对互容经验表；定位：两张互容汇总表。

## candidate_rules

- `house-ruler-flow`：A 宫宫主落入 B 宫是方向性责任链摘要。
- `mutual-reception-matrix`：宫位对互容仅作经验假设，严格互容/接纳条件不放宽。
- `timing-boundary`：法达、返照、次限、太阳弧、行运和校时只登记为后续插件。

## tests_run

- `T-A01` 来源可追溯性：通过；保存文件名、章节/表格定位和限制。
- `T-A02` 概念分离：通过；区分宫主飞宫、行星接纳、行星互容。
- `T-A03` 反证/去重：通过；同一宫主链不得重复计数，经验标签不得直接升级。
- `T-A04` 敏感主题：通过；医疗、死亡、犯罪、性和灵体等内容不进入用户输出规则。
- `T-A05` 本命/时限边界：通过；推运清单保持 inactive。

## changes

- 新增 `references/knowledge-modules/` 三个模块与来源审计。
- 将原资料的 144 个有向飞宫条目与 78 个宫位对互容条目完整拆入 `fly-star-corpus.md` 和 `mutual-reception-matrix.md`，不再只保留摘要。
- 新增 `R38/R39` 本地来源登记与 `references/knowledge-modules/insight-cards.md` 中的 `QI-013/QI-014/QI-015` 洞见卡。
- 改为核心蒸馏器 `scripts/build_core_knowledge.py`：读取两份文档的 5,002 条源记录，但只保留 1,281 条经过筛选的核心卡片；完整手册抽取物、现代/敏感/病例/时限材料不写入项目。
- 更新 SKILL 的本地资料调用协议。

## result

`partial`：两份 Word 已完成全量读取和核心筛选；污染性、现代形式性和模棱两可材料不保留，候选规则仍不升级核心证据等级。

## next_round

为 2-8、4-10、7-11 建立正负对照合成 Chart Facts，运行模块匹配、去重和敏感边界回归；若无法区分竞争假设，维持 C/deferred。
