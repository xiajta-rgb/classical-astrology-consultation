# 客户资料统一管理

本目录是客户输入、出生资料、计算结果和咨询交付物的统一入口。每个客户或家庭案例使用以下命名格式：

`YYYYMMDD-HHMM-地点Slug`

出生时间或地点缺失时使用：

`YYYY-unknown-unknown-place`

目录名不强制写姓名；姓名只保存在 `profile.json` 的 `display_name` 字段中。这样既能按时间和地点检索，也能减少姓名泄露。

目录约定：

- `profile.json`：客户已提供的基本资料、来源、资料完整度和咨询主题。
- `input/`：用户原始输入或原始星盘数据。
- `analysis/`：计算结果、回测、咨询稿和研究交付物。
- `analysis/interpretations/CHART-INSIGHTS.json` 与 `.md`：盘主洞见账本。每次本命或推运分析后，必须把关键征象、责任链、现实验证、反证、证据等级和未决问题写入这里；后续复盘先读取账本，不得从零重建。
- `related/`：家庭成员或关联客户资料（如需要）。

根目录 [`../clients.json`](../clients.json) 是机器可读索引。旧的 `references/fixtures/` 与 `references/loop-runs/` 文件暂时保留为兼容副本，后续新资料只进入本目录；索引中的 `legacy_sources` 用于追溯旧路径。
新建案例请使用 `python scripts/new_client_case.py --date YYYY-MM-DD --time HH:MM --place-slug PlaceSlug --place "地点"`，资料不完整时省略缺失参数并先保留 `unknown` 状态。
