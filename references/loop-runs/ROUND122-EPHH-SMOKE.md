# Round 122 — ephh 直接本命盘计算烟测

## 状态

`PASS / HOLD`。直接计算、适配、度数事实库存和负例自测通过；解释发布因行政区中心坐标导致的 ASC 29°34′ 边界风险而保持 HOLD。

## 可复现命令

```powershell
& 'C:\Users\xmls\AppData\Local\Programs\Python\Python312\python.exe' -X utf8 scripts/ephh_chart_client.py `
  --year 1996 --month 11 --day 11 --hour 22 --minute 25 `
  --lat 27.8065115 --lon 113.2582282 --tz 8 `
  --place '湖南省株洲市芦淞区（行政区中心坐标）' `
  --location-source 'Nominatim行政区中心：27.8065115,113.2582282' `
  --house-system P `
  --output references/fixtures/ephh-1996-11-11-zhuzhou-lusong.json

python -X utf8 scripts/check_ephh_chart_client.py
python -X utf8 scripts/build_natal_facts.py `
  references/fixtures/ephh-1996-11-11-zhuzhou-lusong.json `
  --output references/loop-runs/ROUND122-EPHH-FACTS.json
```

若只提供地点名称，可省略 `--lat/--lon`；适配器会调用 Nominatim 并记录解析结果。但地名解析得到的是行政区/搜索结果坐标，精度警告不会被关闭。

## 事实摘要

| 项目 | ephh 结果 |
| --- | --- |
| Julian Day (UT) | 2450399.1006944445 |
| UTC | 1996-11-11 14:25:00 |
| ASC / MC | 巨蟹 29°34′ / 白羊 22°11′ |
| 宫制 | Placidus |
| 盘型 | 夜盘（由太阳落 4 宫推断，低置信度） |
| 行星/附加点 | 15 个（含适配器补算凯龙） |
| 几何相位候选 | 45 条，五类主要相位，最大 orb 8° |
| 入相/出相 | 未解释，统一 unknown |
| 事实门 | `fact_inventory_ready=true` |
| 解释门 | `natal_interpretation_ready=false` |
| 最终决策 | `HOLD` |

## 与用户旧表的关键分歧

本地 ephh 的 5 宫宫头为天蝎 26°23′，月亮 24°50′和水星 25°11′因此落 4 宫；用户旧表及 CET 版本列为 5 宫。该项不能凭“多数来源”拍板，必须保留为宫制/坐标/服务实现冲突。土星则由 ephh 明确给出逆行（速度 -0.037791°/日），而 CET 缺少可用速度，不能把 CET 的顺行标记当作已确认事实。

同一坐标的 CET 响应已保存为 `ROUND122-CET-COMPARISON.json`；请求不携带城市名称，因为该服务的城市数据库对中文行政区名称返回错误，坐标计算本身仍成功。CET 仅作为独立比较源，不覆盖本轮 ephh 主结果。

## 下一轮

1. 获取精确出生地址或确认采用芦淞区行政区中心，并对 ASC 29°附近做坐标/时间敏感度矩阵。
2. 在同一 JD 上显式锁定真节点/平节点、凯龙版本和宫位实现，形成可比较的 engine profile。
3. 为相位建立经测试的入相/出相规则；在此之前，45 条仅属于几何候选，不进入确定性判断。
