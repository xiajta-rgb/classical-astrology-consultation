# 本地附件洞见卡（QI-013–015）

这些卡片沿用 `quote-insight-cards.md` 的字段，但由于本地附件没有可核验作者和出版版本，状态最高为 `auxiliary`。

## QI-013｜宫主飞宫可作责任链方向摘要

```text
card_id: QI-013
source_id: R38
locator: 本地文档“飞星：占星系统的压舱石”段落 3346-3410；“飞星系统”段落 2761-3214
tags: [@house_rulership, @fly_in, @hypothesis, @anti_overfit]
quote: none
paraphrase: A 宫宫主落入 B 宫可记录为 A→B 的方向性责任摘要；穿刺、截夺和双宫主会改变代理人识别。
operational_rule: 从已验证 Chart Facts 读取 rulership_fly_ins；只生成 B/C 或 deferred 假设，不重复计数宫主本身。
conditions: 黄道、宫制、宫头、宫主版本和穿刺/截夺状态已锁定。
counter_test: 同一颗星可守护多个宫位；若飞宫解释与尊贵、sect、相位或现实观察冲突，保留竞争假设并降级。
output_guardrail: 写“该责任被带入某宫语境，可能表现为……”，不写必然事件。
status: auxiliary
```

## QI-014｜宫位对互容只能生成经验假设

```text
card_id: QI-014
source_id: R39
locator: 两张“互容详解汇总表”中的 1-1 至 12-12 行
tags: [@house_pair, @reception, @hypothesis, @source_criticism]
quote: none
paraphrase: 宫位对表把财富、家庭、事业、关系和远方主题的联动写成经验标签；缺少作者、版本、样本和条件时，只能用来生成资源/责任/风险假设。
operational_rule: 将宫位对拆成 mechanism、support、counter_test、missing_discriminator；默认 grade_cap=C。
conditions: 先完成相关宫位责任链和行星状态审计，并提供可观察的现实记录。
counter_test: “富二代、大财、婚姻不错、躺赚”等标签不能由宫位对单独推出；还需审查债务、授权、边界和关系合同。
output_guardrail: 使用“提出一种待验证的宫位联动假设（C）”，不使用保证式财富、婚姻或事件语言。
status: auxiliary
```

## QI-015｜推运清单不是已激活的时限证据

```text
card_id: QI-015
source_id: R38
locator: 本地文档“推运部分”段落 13-23；高阶合盘推运段落 4132-4465
tags: [@timing, @natal_first, @boundary]
quote: none
paraphrase: 法达、太阳弧、次限/三限、返照、行运和校时先作为方法库存；本命盘不能单独生成具体年份或事件日期。
operational_rule: 只有用户提出未来时间问题且数据满足要求时，才激活时限模块；先保存本命基线，再记录时间技术和激活区间。
conditions: 需要出生时间精度、地点、度数、历表/推运版本和问题范围。
counter_test: 单一本命指标不能确认结婚、发财、升职、搬家、疾病或灾难日期。
output_guardrail: 未激活时只写“需要补充时限技术”，不输出年份/月份。
status: auxiliary
```

