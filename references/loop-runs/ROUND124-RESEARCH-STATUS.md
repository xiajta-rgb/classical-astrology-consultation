# Round 124：稀缺技法、深层条件链与禁忌语境研究

状态：`PASS / PARTIAL`

## 本轮检索材料

- R29：Valens《Anthologies》Riley/Griscti PDF，Book II §§2.9–2.20，重点阅读第二宫、第五/第六宫、宫位别名、福点/Daimon、财富、相位、整体命盘和极端案例的条件链。
- R28：Chris Brennan《The Planetary Joys and the Origins of the Significations of the Houses and Triplicities》，重点阅读 joys、sect、角宫三角、宫位命名、房屋象义的历史构造及 Manilius 变体。
- R29 的归档版 Riley PDF 作为交叉版本线索；未把两个译本差异压成单一原典。
- R30：Traditional Astrology 的 bonification/maltreatment 教学文章，完整读取扶助、虐待、接纳、燃烧与 cazimi 段落；仅作为二手方法线索，固定orb/评分不进入核心规则。
- R31：Augurine 透明评分卡，读取扶助/虐待条件、sect 权重与 counteraction 说明；其“权重非单一古典作者规则”的自我限制被保留为反过拟合证据。

## 已沉淀的洞见卡

- `QI-019`：第二宫不是独立钱袋；必须连同2宫主、11宫/福点、10宫交付和8宫共同资金读取。
- `QI-020`：古典文本中的暴力、犯罪、死亡、性和污名词汇必须保留历史语境与条件链，转译为资源、权力、法律、边界和高压机制，不得现代化成断言。
- `QI-021`：福点与Daimon分别把身体/手的工作、心智/行动和收益结果拆成可审计路径，不能制造命运标签。
- `QI-022`：Planetary Joys 是宫位意义的历史构造假说；可作背景层，不能替代宫主责任链。
- `QI-023`：相位强弱取决于精确度数、方向、有效宫位、sect、尊贵、主宰身份和整盘支持；相位名称不是结论。
- `QI-024`：扶助/虐待是行星“承诺强度”和“交付能力”的第二层审计；接纳、应用/分离、sect、尊贵和来源版本决定是否能提升或降级。
- `QI-025`：透明评分只能枚举候选和冲突，不能伪装成古典统一权重；同时有扶助与压力时保留 counteraction 分支。

## 规则变更

1. 研究层新增 R28/R29/R30/R31，均保持 `auxiliary`，不自动升级核心规则。
2. 解释模块新增 `@wealth` 能力映射，财富模块明确要求2/11/10/8责任链与共同资金审计。
3. 敏感表达门禁强化：历史极端词汇只能在用户主动提出主题且通过 G1/G2/G3 后展示；现代输出只允许机制化、可观察的翻译。
4. Joys 作为可插拔背景层，不改变当前 Chart Facts 和责任链算法。
5. bonification/maltreatment 只登记为候选状态字段；固定orb、商业评分和“吉星保护/凶星毁坏”式句式被明确拦截；counteraction 保留为冲突分支。

## 测试与门禁

- `check_research_assets.py`：`pass`，25 张完整卡、7 张待核读卡，29 个登记来源，0 findings；辅助卡和待核读卡保留 warning。
- `check_source_registry.py`：`pass`，来源指纹已更新。
- PDF 逐页提取：R28 32 页、R29 710 页，重点页码已写入卡片 locator。
- 未将 Valens 的历史极端措辞直接写入本命报告，也未将 Joys 当作强制性现代解释。

## 未完成与下一轮

- R29 仍是 preliminary/unperfected 翻译，关键数学、术语和极端案例需与希腊文批校本或独立译本互校。
- R28 的 Joys 解释需继续回到 Paulus、Firmicus、Valens 的 primary text，确认“joys先于宫位象义”的历史论证边界。
- 下一轮重点：燃烧/光线下/可见性、速度与站留、左右相位/阻断、bonification/maltreatment 的 primary-text 交叉校对、隐性连接（antiscia/contra-antiscia）及其在本命主题模块中的降级规则。
