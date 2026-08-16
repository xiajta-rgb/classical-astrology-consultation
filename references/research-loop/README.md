# 网络研究循环体系

本目录是知识模块的外部研究层。它负责把网站、书籍、PDF、视频、论坛帖子和用户案例转化为可追溯的候选知识；只有经过来源核验、反例审查和回测的内容，才允许进入核心知识卡。

## 循环流程

```text
提出缺口/问题
  -> 建立检索任务
  -> 采集来源元数据
  -> 保存短摘录或忠实转述
  -> 来源分级与版本锁定
  -> 关键词/主题初聚类
  -> 机制抽取（对象、宫位责任、主星状态、可观察表现）
  -> 支持案例 + 反例 + 交换宫位测试
  -> 与 Chart Facts 回测
  -> 核心 / 辅助 / 假设池 / 排除
  -> 生成下一轮缺口
```

## 来源等级

- `primary`: 原典、批校本、原始研究论文；可作为规则候选的最高层，但仍需版本和章节定位。
- `secondary`: 学者导读、传统技术文章、课程或播客；用于解释、发现原典线索和提出假设。
- `case_or_forum`: 帖子、论坛、博客、个案；只进入假设池，必须保留失败案例和原始盘数据。
- `empirical_or_safety`: 现代实证、心理学、医学或法律资料；用于限制表达和反过拟合，不用于证明占星规则。

## 每张研究卡的最低字段

`source_id`, `url_or_locator`, `source_type`, `retrieved_at`, `claim`, `faithful_summary`, `candidate_mechanism`, `event_clusters`, `counter_test`, `status`, `grade_cap`。

搜索引擎摘要、AI 摘要和无法定位原文的转述必须标记 `status: candidate`、`grade_cap: C`，不能直接改写核心规则。

## 当前轮次

当前研究文件见 `rounds/LOOP-20260815-03.json`；上一轮为 `LOOP-20260815-02`。本轮聚焦4飞2/2飞4配对回测、Valens财富交叉核对和取得/持续性拆分。候选来源在 `source-queue.jsonl`，初步摘录在 `candidate-extracts.jsonl`，候选缺口在 `gap-registry.json`。

每批检索保存于 `batches/`，批次只追加来源和候选摘录，不覆盖上一批结果。第二批示例为 `batches/BATCH-20260815-02.json`。

可用 `scripts/run_research_loop.py --round-id LOOP-20260815-03 --passes 3` 执行本轮有界的本地循环并生成可恢复状态。外部网页需在用户触发后读取；循环不会把候选资料自动升级为核心规则。

若需要自动处理公开来源队列，可运行 `scripts/auto_research_loop.py --max-pages 6`。它逐条保存页面标题、元描述、关键词命中和失败状态；PDF、超时、HTTP错误都会被标记后跳过，循环不会因单个网站卡住。它不保存整页正文、不自动升级规则，也不在对话外宣称持续运行。

自动摘要可用 `scripts/cluster_research_extracts.py --include-auto --output references/research-loop/clustered-auto-extracts.json` 加入候选聚类；这些条目仍保持 C 级，必须人工回到原文复核。

需要连续自动发现和处理多批来源时，运行 `scripts/continuous_research_loop.py --rounds 3 --pages-per-round 8`。它轮换检索主题、去重新增网址、调用自动抓取器、聚类并保存 `continuous-loop-state.json`；达到轮次上限后正常返回，下一次运行从查询游标继续。

需要在后台持续运行时，运行 `scripts/daemon_research_loop.py --interval-seconds 300 --rounds-per-cycle 2`。它每轮只执行可控的小批次，保存断点、日志和心跳；网络异常会记录后自动重试。创建 `references/research-loop/STOP-DAEMON` 即可平滑停止。后台监督器仍不会自动把网络材料升级为核心规则。
