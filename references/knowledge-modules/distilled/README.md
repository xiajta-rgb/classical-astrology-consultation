# 微信占星文章候选蒸馏

本目录是用户提供的 `(公众号数据)表格视图.xlsx` 的候选抽取层，不是古典核心规则库。

- `cards.jsonl`：仅保存正文中可定位的‘条件—机制/表现’原文片段；全部为 `candidate` 或 `deferred`，证据上限 C。
- `exclusions.jsonl`：记录空正文、营销、案例堆砌、敏感/确定性表述、煽动性语言和无结构正文的排除原因。
- `retrieval-index.json`：按主题和模块定位候选卡。
- `index.json`：来源哈希、计数、筛选和晋级政策。
- `exploration.json`：第二轮主题簇、近重复审计、来源集中度和人工复核队列；只用于探索，不改变卡片证据等级。
- `review-queue.jsonl`：按复核分数排序的前 40 张卡，附质量标记、反证要求和下一动作。
- `module-drafts.json` / `module-drafts.md`：从主题簇生成的模块边界草案、代表卡和晋级测试；仍为 candidate-only。
- `article-coverage.jsonl`：工作簿全部 14,978 行的覆盖台账；每行都有 disposition 和 link_kind，不复制正文全文。当前 6,633 行是直接文章链接、7,447 行是合集链接，但正文列为空。
- `judgment-ledger.jsonl`：从 898 篇有正文文章中登记的判断片段；当前 2,177 条严格片段加 3,809 条 `broad_review` 片段，candidate、deferred、review_needed 和 quarantined 分层保存。
- `judgment-ledger-index.json`：判断台账计数、哈希、隔离政策和晋级门槛。

使用前必须先完成 Chart Facts、宫位责任链、行星状态和项目敏感主题门禁。现代外行星、莉莉丝和时限材料只保留为研究候选；时限卡保持 deferred。原文是二手公众号语料，不能直接生成诊断、事件保证或日期。

重建顺序：先运行 `distill_wechat_astrology.py`，再运行 `explore_distilled_articles.py`、`build_article_module_drafts.py` 和 `build_article_judgment_ledger.py`，最后运行 `check_article_distillation.py`。判断台账是覆盖/隔离层，不代表所有片段都可调用。抽样访问直接文章链接若进入微信验证页就停止，不绕过；公开合集页可按官方分页继续抓取。

正文恢复使用 `scripts/retrieve_wechat_public_sources.py`，结果写入 `retrieval/`，可断点续跑；成功获取的正文再由 `scripts/distill_retrieved_wechat_articles.py` 写入 `retrieved-distilled/`，不会覆盖原始 R60 蒸馏卡。
全量完成的判据是：运行 `scripts/check_retrieved_distillation_coverage.py` 后，每个 `retrieved` 正文均有候选卡或明确排除理由；`verification_required`、`no_js_content` 和 `error` 仍算待处理，不得计入“全部沉淀”。
