# 研究体系状态快照（Round 115）

当前发布决策：`HOLD`；解除 HOLD 仍需补齐出生契约、度数与来源门槛。

## 当前能解读

可以报告接纳方向、相位声明、连接状态和缺失证据；不能把方向候选直接写成交付结论。

## 本轮研究增量

接纳审计现在同时检查方向和相位连接：`degree_confirmed_connection`、`sector_connection_unconfirmed`、`boundary_connection_unconfirmed`、`no_aspect_claim`、`unknown_connection`。锁定规则 `direction_plus_connection_required` 下，只有第一类可以称为已确认连接。

## 用户盘结果

9 条接纳声明全部通过守护方向校验，但当前全部为 `no_aspect_claim`；因此报告不再把它们写成交付完成，而是明确标记“方向存在、连接未声明”。这保持 HOLD，并暴露了最关键的补数缺口：水星—火星等接纳对的实际相位与度数。

## 不能解读

不能确认应用/分离、精确容许度、事件时间或任何敏感主题的确定性结果。

## 合成反例

`synthetic-chart-delivery-evidence.json` 提供带度数的双向接纳与水星—火星六合，连接状态为 `degree_confirmed_connection`，可进入候选卡交付证据层；假设卡审计、评分、NATAL-first 和咨询语言检查通过。

## 机器状态

用户盘仍 `decision=hold`、`publishable=false`；研究卡 17 张已抽取、7 张待抽取（P0=3、P1=4）。下一步继续测试“方向有、相位无”“相位有、方向反向”“边界相位”三种冲突负例。
