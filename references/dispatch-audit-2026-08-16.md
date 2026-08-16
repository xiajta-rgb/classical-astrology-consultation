# 调用与扩展审查记录（2026-08-16）

## 本轮结论

运行时已经收敛为一条可审计路径：

`planner → Chart Facts → planetary state → responsibility chain → reception audit → bounded knowledge → composition → renderer`

新增主题只需要在 `config/interpretation_routes.yaml` 注册主题别名、在
`config/module_dispatch.yaml` 注册路由和插件；执行别名不再在两个配置文件中重复维护。

## 已修复的问题

1. 责任链不再二次计算本命盘。`calculate_responsibilities(..., chart_facts=...)`复用同一
   `chart_id`；不传入时才独立计算，兼容直接 API 调用。
2. 地点名称现在先查 `config/place_aliases.json`，再使用网络地理编码；地点解析结果会保留
   `location_source` 和行政中心精度警告。
3. 仅有地点名称时，尊贵和互容模块继续传递 `place`，不会因后续模块丢失地点而失败。
4. “未来/趋势”等主题若未显式打开时限，规划器返回 `hold`，不会静默降级为本命结构。
5. 运行流水线的模块追踪从规划器动态生成，并带模块版本，避免新增模块后手工维护第二份 trace。
6. 知识查询对未知插件、未知模块和负数 limit 给出明确错误/延迟信息；主题和模块别名统一归一化。
7. 旧的 `ephh_core.astro.significations` 已标为兼容适配器，出生资料新流程只走顶层生产接口。
8. 审查器增加了路由双向同步、重复别名、核心来源漂移、规划器契约和时限闸门检查。

## 仍然保留的边界

- 行政中心坐标只能支持低精度地点输入；有经纬度时优先使用经纬度。
- `run_natal_pipeline.py`默认只输出结果；只有显式 `--output` 或 `--case-id` 时才写文件，`--case-id` 会写入已存在案件的标准目录。
- 时限方法仍须由问题显式指定一种；本命出生资料本身不会自动生成未来断语。
- `validate_chart_facts.py` 与 `build_natal_facts.py`继续作为外部图表兼容审计，不取代新出生资料的本地计算引擎。

## 回归状态

本轮通过：插件、模块调度、项目架构、客户目录、知识模块、本地星历引擎、技术注册表、模块化解释、研究循环，以及 skill-creator `quick_validate`。

## 第三轮结构修复

- `chart_id` 升级为包含出生时间、经纬度、时区、黄道制和宫制的稳定摘要；本命与推运 envelope 现在共享同一身份，避免同一时刻不同地点互相覆盖。
- timing 扫描器统一处理字符串/带时区时间，支持 `place` 输入，并把 `chart_id` 写入每个候选事件。
- 单一流水线现在可用 `--timing --technique ...` 激活一次明确的时限快照；窗口扫描仍需显式调用，不把单次快照伪装成事件窗口。
- 增加 `--case-id`：校验客户案件、把本命包写入该案件的 `analysis/chart-facts/`，无 `--output` 时使用稳定的 chart ID 文件名。
- `scripts` 成为正式 Python 包；主题对应的知识模块由路由配置提供，删除流水线内的主题硬编码。
- `topic_question` 与 `timing_question` 不再重复维护别名列表，统一从主题责任图读取；路由检查器会验证知识模块索引和规划器契约。
- 新增 `config/quality_gate.yaml` 与 `scripts/run_quality_gate.py`，把全部必需回归检查收敛成一个固定入口；质量闸门失败时停止后续交付。
- 第四轮把关联算子、飞宫方向、互容连接、行星状态、假设卡、出生盘优先级、敏感词典和来源注册表等原先未进入总闸门的检查全部纳入；当前总闸门共覆盖 18 项必需检查。
- 后续审查补上了发布状态机：流水线明确输出 `publication_status=hold`、`release_gate` 原因和 `timing_status`，并在调度图中新增 `release_gate` 模块；“计算完成”不再被误认为“可交付”。
