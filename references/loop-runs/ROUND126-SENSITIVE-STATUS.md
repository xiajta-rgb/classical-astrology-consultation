# Round 126：死亡、疾病、破财、关系背叛与父母征象

状态：`PASS / PARTIAL`

## 检索范围

本轮交叉读取了 Ptolemy《Tetrabiblos》、Dorotheus《Carmen Astrologicum》、Al-Qabisi《Introduction to Astrology》、Bonatti《Liber Astronomiae》Treatise 8.2，以及美国国家癌症研究所的现代诊断说明。Firmicus《Mathesis》只找到书目/短篇导论线索，未把不完整材料升级为规则来源。

## 新增来源

- R33：Dorotheus，父母、父母死亡、财富、疾病、婚姻和灾祸章节。
- R34：Al-Qabisi，宫位语义与疾病/死亡/父母/婚姻/财富 Lots 的校勘版材料。
- R35：Bonatti Treatise 8.2，婚姻/放纵、死亡、身体/财富、父母 Parts 及 Hermes/Valens/Abu Ma'shar 版本差异。
- R36：NCI，癌症诊断必须依赖临床流程；只作医学安全边界，不作占星证据。
- R37：Firmicus《Mathesis》全文获取线索，保持 `registered`，等待完整技术文本。

## 新增研究卡

- `QI-026`：死亡/寿限是prorogator、主限、Lot、sect、角宫、吉凶援助和时限的多层技术，不是八宫单点。
- `QI-027`：疾病与癌症分离；古代身体象征不能建立现代癌症诊断库。
- `QI-028`：破财是资源链、主宰、福点、共同资金和时限的交付问题，不是单一二宫凶星。
- `QI-029`：出轨/淫乱是历史婚姻语境；现代只能讨论契约、边界、公开性和信任风险，不作指控。
- `QI-030`：父亲/母亲分别建模并进行多重确认；不能预测父母寿命或病亡。
- `QI-031`：Lot公式和传承差异是敏感征象的降级条件，必须保留版本分支。
- `QI-032`：禁忌词统一经过G1/G2/G3、独立证据、反证和现实专业转介。

## 资产与门禁

- 研究卡：32 张完整卡，8 张待核读卡。
- 来源：34 个登记来源；其中 R37 仍是未全文核验的研究线索。
- `check_source_registry.py`：通过。
- `check_research_assets.py`：通过，0 findings；辅助卡、医疗安全卡和待核读卡继续保留限制。
- 真实本命盘：没有任何死亡、癌症、出轨、父母病亡或破财结论被写入；报告继续 `HOLD`。

## 本轮没有升级的内容

没有发现足以把上述禁忌主题转成现代确定性预测的新证据。不同传统反而显示公式、宫制、sect、Lot、主限和吉凶援助差异很大，因此“更多禁忌词”不等于“更高确定性”。

下一轮：继续查找 Firmicus 完整技术文本、Abu Ma'shar/Al-Qabisi 的独立译本，以及 Bonatti/Ptolemy 的版本对读；同步为敏感主题建立专门的反事实测试夹具。
