# ROUND134：跨体系联想技法蒸馏

日期：2026-08-15  
输入：本地 `horosa-agent` 技能说明、Horosa predictive reference、`vedic-calculator`、`vedic-reader`、`vedic-core`、`vedic-rectifier`、`vedic-synastry`、`vedic-prashna`、`vedic-love` 与 `vedic-career` 技能说明。  
范围：只提炼方法论和联想逻辑，不迁移吠陀规则为古典西占征象。

## 本轮保留

1. **Chart Facts 优先**：星盘计算产物是唯一征象来源；解释器不得从外部体系补造征象。
2. **一次计算、多次消费**：先生成可校验事实，再由主题模块和事件模块复用，避免重复重算和口径漂移。
3. **信号分诊**：解释前列出支持、冲突、缺失和边界；模板不能覆盖实际数据。
4. **分辨率阶梯**：本命允许主题，周期技法给出窗口，微触发才可收窄到更短时间；没有对应技法就拒绝伪精确。
5. **候选矩阵校时**：重大事件优先，性格标签不作为强校时依据；改时间后全量重算；保留盲测和边界降级。
6. **双向关系通道**：关系类型由用户给出，A→B 与 B→A 分开，再判断共同机制或不对称性。
7. **证据来源与精度标签**：每个事实、推断和外部联想都保留来源、精度和验证状态。
8. **失败显式化**：未知方法、缺失参数和外部回退必须标记，不得静默采用替代口径。

## 本轮拒绝

恒星黄道、ayanamsa、Nakshatra、Dasha、分盘、Shadbala、SAV/BAV、Drishti、Karaka、Ashtakoota、KP/Tajika 专属规则没有进入古典西占生产层。它们可另建隔离研究插件，但不能增加本项目的星盘征象权重。

## 新沉淀

联想算子已写入 `references/calculation-methods/association-operators.json`，包括责任转移、条件调制、载体连接、独立汇聚、瓶颈、轴线转译、事件阶梯、时间激活、双向关系和反事实删除。注册表与 QA 分别位于 `astrology_engine/technique_registry.json`、`scripts/check_technique_registry.py` 和 `scripts/check_association_operators.py`。

## 下一轮建议

- 用 3 个已验证家庭/事业案例测试“事件阶梯 + 反事实删除”，检查是否会把单一征象夸大为重大事件。
- 为每个主题模块补充 `chart_anchor_ids` 与 `operator_id`，让检索结果能回到具体星盘事实。
- 只有完成本地算法等价、参数审计和回归样本后，才考虑实现 Horosa 的主限或 Zodiacal Releasing；在此之前保持候选状态。

