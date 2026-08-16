# 占星知识库与运行时再审查（2026-08-16）

> 本文是当前状态快照。计算事实仍以本地星历引擎为唯一权威；知识卡和主题模板只能补充责任链，不能覆盖 Chart Facts、严格接纳或显式时限结果。

## 当前结论

项目已经从“核心算法 + 分散资料”推进到“核心算法 + 主题适配器 + 插件契约 + 路由测试”的可运行闭环：

- `interpretation-topic-adapters` 已接入身份、财富、职业、工作、关系、家庭、子女/教育主题；
- 关系/家庭、子女/教育路由已补齐 `topic_knowledge`，且主题查询能返回受限模板、反证和可观察验证项；
- 主题别名已与查询器对齐：`children / education / schooling / parenting` 统一进入子女教育适配器，`household / parents` 进入家庭适配器，房产别名进入财富/房产模板；
- `home` 保留给房产/置业路由，`household` 保留给家庭关系路由，避免同一别名在规划器中产生隐式冲突；
- 时限模块继续保持显式激活，不能由本命出生资料自动生成日期；
- 公共 natal/predictive API 已统一校验出生点、行运/回归目标点的坐标、时区、当地时间和宫制，predictive 输出也与 natal 使用一致的宫制显示名称。
- 时限扫描器也已统一拒绝带时区的窗口、NaN/无穷步长与轨道、负的联系人上限，避免扫描窗口被静默平移或产生不可解释的截断。

因此，当前系统可称为：**本命核心稳定、主题编排可调用、知识扩展受控；古典高级技术仍有候选层，尚非完整传统技术库。**

## 仍缺的工程化知识能力（P0）

### 1. 知识卡机器字段不完整

`references/knowledge-modules/core/cards.jsonl` 目前主要记录来源、文本、条件、反证、等级和状态。要支持长期蒸馏、去重和冲突处理，还应统一补齐：

`claim_type`, `applicability`, `evidence_layer`, `independence_group`, `conflict_set`, `test_status`, `supersedes`, `superseded_by`。

没有这些字段，新增材料容易变成文本堆积，重复传统来源也可能被错误算作独立证据。

### 2. 研究资产到发布版本缺少自动交叉引用

仍缺一条机器可检查的流水线：

`来源定位 → Quote/Insight Card → 候选规则 → 支持/反证 → 回归测试 → 插件版本 → 检索索引`。

目前插件契约已经有依赖、证据上限、回滚和安全闸门，但 source registry、研究台账、规则卡、测试结果之间尚未形成强制 foreign-key 关系。

### 3. 代表性命盘回归集不足

现有测试已覆盖输入边界、MBTI/TPES 计分、路由和插件架构，但还缺每个主题的正例、反例、跨主题污染、重复计分和规则版本 diff。后续应建立脱敏的固定命盘集，并把“规则加入前/后”输出差异纳入发布门禁。

## 仍缺的古典技术插件（P1）

以下内容在候选研究资料中已有线索，但当前没有达到 `active` 生产插件标准：

1. `lots-and-formulas`：Fortuna、Daimon、Exaltation、Accomplishment 等 Lot 的日/夜盘公式、版本差异和度数校验；
2. `antiscia-contra-antiscia`：反照点与反反照点的精确几何、容许度、角点/主星连接条件；
3. `planetary-condition`：燃烧、cazimi、日光下、晨昏相、速度、停滞与可见性；
4. `bonification-maltreatment`：扶助/虐待、光线传递、光线收集、阻截和交付顺序；
5. `dignity-variants`：三分主、界、面等传统表格的版本可配置比较与冲突降级；
6. `planetary-joys`：行星喜乐的历史技术层，不能直接替代现代宫位意义；
7. `visibility-and-observation`：太阳关系、观测条件和现实观察校验的独立层。

建议顺序：`lots/formulas → antiscia → planetary_condition → bonification/maltreatment → dignity_variants → joys`。每个插件都应先具备来源定位、算法校验、适用条件、反证和回归测试，再从 `candidate` 升为 `active`。

## 时限与范围边界

### P2：继续独立建设的时限体系

annual profections、zodiacal releasing、solar/lunar returns、primary directions、secondary progressions、transits、firdaria 和校时都必须拥有独立数据契约、误差容忍度和回测集，不能与本命主题适配器混发。

### 明确不属于当前本命知识库的范围

合盘/比较盘、卜卦、择日、世俗/政治占星、医疗诊断式占星、现代外行星人格覆盖，以及死亡、犯罪、疾病、生育结果的确定性预测，应另立产品边界或保持禁用。历史文献中的相关语义只能保留为研究背景和表达约束。

## 本轮验证结果

- `pytest -q tests/test_input_validation.py tests/test_insights.py tests/test_knowledge_runtime.py`：24 passed；
- `scripts/check_plugin_architecture.py`：8 plugins，契约/索引/依赖通过；
- `scripts/check_module_dispatch.py`：14 modules、8 routes、大小写检查通过；
- MBTI/TPES 随机性质检查：维度和为 100，TPES 总分为 100，分数范围合法。

## 下一步最有价值的工作

优先不是继续增加行星关键词，而是：

1. 升级 cards schema 并建立来源—规则—测试—插件版本的交叉引用；
2. 建立最小代表性命盘回归集和主题反例集；
3. 先实现 `lots-and-formulas` 与 `antiscia` 两个技术插件，再决定是否接入更复杂的行星状态和交付技术；
4. 保持所有高级技术为候选/辅助层，直到通过独立证据和现实观察回归。
