# 接纳—相位冲突负例记录（Round 116）

| 夹具 | 预期状态 | 实际结果 |
|---|---|---|
| 用户盘：9 条守护方向、无对应相位声明 | `no_aspect_claim` | 9/9 `no_aspect_claim`，进入 `connection_required_unmet` |
| 合成盘：有度数、双向守护方向、六合 | `degree_confirmed_connection` | 2/2 确认连接 |
| 合成盘：保留相位声明、移除水星/火星度数 | `sector_connection_unconfirmed` | 2/2 扇区候选，未升级 |
| 合成盘：月亮→火星非守护方向 | `unsupported_domicile_claim` + `no_aspect_claim` | 两个负例条件均触发 |

结论：接纳方向、相位存在、度数确认和规则资格已分成四个独立状态；任何一个状态不足都会降低或阻止交付判断。
