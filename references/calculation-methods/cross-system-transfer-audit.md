# Horosa 与 Vedic 技能的跨体系迁移审查

版本：`CROSS-SYSTEM-TRANSFER-2026-08-15-1`

这不是把吠陀占星或 Horosa 的规则直接并入古典西占，而是提炼它们在“如何计算、如何留痕、如何控制推断强度”方面的工程与推理经验。项目生产口径仍为热带黄道＋Placidus；外来体系只作为隔离插件或方法论来源。

**最高优先级原则：征象以本项目实际计算出的星盘为准。** 外部技能只能帮助我们把已有征象联想成机制、事件链、竞争假设或时间层级；它们不能凭空增加星盘没有的征象，也不能覆盖行星、宫位、守护、尊贵、相位、互容、sect 或角度事实。没有本命支持的联想必须标记为 `unsupported/deferred`。

## 一、可直接迁移的高价值逻辑

| 来源能力 | 提炼后的通用规则 | 在本项目中的落点 |
| --- | --- | --- |
| Horosa 的工具契约 | 预测技法必须声明端点、地点、时区、方法参数、版本与来源；不能拿本命盘冒充预测结果 | `astrology_engine/technique_registry.json`、预测 API 返回的 provenance 字段 |
| Vedic-calculator 的一次计算、多次消费 | 先生成完整、可校验的 Chart Facts/结构化产物，解释器只读产物，不重复猜测或重算 | `astrology_engine/natal.py`、现有 Chart Facts 与模块检索链 |
| Vedic-core 的信号分诊 | 先列出有效征象、缺失字段、冲突和限制，再进入解释；不可用模板覆盖数据 | 本命审计、假设卡、发布门禁 |
| Vedic 的 MD→AD→PD | 时间预测采用“背景周期→领域窗口→微触发”的层级；没有相应分辨率的方法就拒绝月/日级断言 | `technique_registry.json` 的 `resolution` 与 timing contract |
| Vedic-rectifier 的候选矩阵 | 校时按候选时间批量重算，硬事件高权重、软性格近零权重；更改时间后所有衍生数据必须重算 | 未来校时插件的设计约束，不自动启用 |
| Vedic-rectifier 的边界降级 | 宫头、纳瓦姆沙/星宿边界之类敏感点不能自证；边界附近必须降低置信度并寻找独立事件验证 | 本项目宫头/角度/度数敏感性标记 |
| Vedic-synastry 的双向通道 | A→B 与 B→A 分开计算；关系类型由用户声明；不压缩成一个“匹配分” | 合盘/关系事件模块的输入契约 |
| Vedic-prashna 的问题时刻隔离 | 提问盘、出生盘、推运盘是不同证据层；没有明确问题、时刻和地点时保持 suspended | 未来时盘插件；不混入本命默认解释 |
| Reader 的来源/精度标签 | 每个值保留来源、精度、边界风险和是否经验证 | Chart Facts 与计算引擎 provenance |
| Horosa 的失败闭环 | 未知方法、缺失参数或引擎回退必须显式标记，不能静默降级 | 注册表的 `status`、`fallback_policy`、QA 脚本 |

## 二、只隔离、不移植为古典规则的内容

以下内容可以作为独立研究插件，但不会成为古典西占生产证据，也不能与热带/Placidus 结果混合计数：恒星黄道与 ayanamsa、Nakshatra、Vimshottari/Chara Dasha、D1/D9/D10 等分盘、Shadbala/SAV/BAV、Drishti、Karaka、Ashtakoota、KP/Tajika 专属规则，以及 Vedic 特有的行星尊卑和宫位映射。

Horosa 的 primary directions、zodiacal releasing、decennials、distributions、age point 等西方预测技法具有迁移价值，但只有在本地算法、参数和回归样本达到来源等价后，才从 `candidate_external_parity` 晋升为生产插件。其方法名、计算口径和版本必须保留，不能用“古典预测”这一泛称掩盖差异。

## 三、组合征象的学习框架

跨体系真正值得学习的是“组合方式”，不是把所有征象堆在一起：

1. **事实层**：行星、宫位、尊贵、相位、守护链、角度和时间端点分别来自可复核计算。
2. **机制层**：把多个事实压缩为资源、责任、阻力、转化和事件通道；同一行星在同一结论中不得重复计数。
3. **验证层**：寻找至少两条独立支持，并列出反证、缺失信息和竞争假设。
4. **时间层**：先判断本命是否允许该主题，再用相应层级的激活技法缩窄窗口；本命盘不能独自产生具体年份或死亡断言。
5. **输出层**：按“占星事实→结构推断→世俗事件形式→不确定性/边界”表达，并对敏感主题使用非决定论语言。

## 四、迁移后的启用顺序

`natal facts → signal triage → association operator → topic/event cluster → technique contract → exact calculation → independent corroboration → calibrated wording`

可复用的联想算子见 `association-operators.json`。本文件与
`astrology_engine/technique_registry.json` 是设计与审查层；真正调用仍走本地
`natal.py`/`predictive.py`。注册表中未启用的技法不会因用户只提供出生资料而自动运行。
