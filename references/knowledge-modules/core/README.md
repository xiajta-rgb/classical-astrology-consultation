# 核心知识库

本目录只保留两份用户资料中筛选出的核心结构：144 条有向飞宫、78 条宫位对互容，以及经过敏感/现代/案例过滤的 R38 方法摘录。

规范调用文件：`cards.jsonl`；统计和哈希：`index.json`。完整原手册抽取物不保留。
# 检索索引

`retrieval-index.json` 按卡片、模块、主题、来源和宫位建立快速定位；它由 `scripts/build_knowledge_index.py` 从 `cards.jsonl` 可重复生成，不能替代 JSONL canonical store。
# Event-first retrieval layer

The canonical cards remain unchanged. Event-first retrieval is stored in
`../event-clusters.json`, `../event-links.jsonl`, and
`../event-retrieval-index.json`. Rebuild it with
`scripts/build_event_retrieval_index.py`; choose a route with
`scripts/plan_knowledge_retrieval.py`.

Links are candidate retrieval hints capped at C, never independent proof.
