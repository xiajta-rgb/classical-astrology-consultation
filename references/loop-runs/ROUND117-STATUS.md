# 研究体系状态快照（Round 117）

## 本轮研究增量

接纳连接状态已进入假设卡评分。只要卡片使用 `no_aspect_claim`、`sector_connection_unconfirmed`、`boundary_connection_unconfirmed`、`not_supplied` 或 `unknown_connection`，评分层就加入 `reception_connection_unconfirmed` 发布理由并把实际等级上限压到 B；`degree_confirmed_connection` 不触发该项降级。

## 验证

独立负例测试证明四种连接分支均可区分，并证明未确认接纳不能逃过评分上限。合成交付夹具仍能保留带度数连接证据；用户盘 9 条方向接纳仍全部阻塞在无相位声明。

## 当前状态

真实用户盘仍 `decision=hold`、`publishable=false`。研究卡 17 张已抽取，7 张待抽取（P0=3、P1=4）；所有机器回归和发布门禁继续通过。
