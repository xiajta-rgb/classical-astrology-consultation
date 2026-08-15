# Round 119 — CET API 只读烟测

日期：2026-08-14  
目标：核验 `https://cet.pythonanywhere.com/api/calculate-ephemeris` 是否能返回本命盘输入所需的原始字段；样例为公开的合成请求，不是任何人的个人资料。

## 请求

```text
year=1990&month=1&day=1&hour=12&minute=0
lat=39.9042&lon=116.4074&tz=8&house_system=P
```

## 实测结果

- HTTP `200`，`status=success`，`content-type=application/json`。
- `ephemeris` 返回 15 个点：Sun–Pluto、North Node、Chiron、Juno、South Node、Fortune；每项含黄经、黄纬、星座、度数、宫位及速度/逆行等字段。
- `axes` 返回 Asc/MC/Desc/IC；样例上升为白羊座 11°50′。
- `house_cusps_detail` 返回 12 个宫头，含黄经和星座度数。
- `aspects` 返回 26 条站点相位候选，含两点、相位名、角度和 orb。
- `mutual_receptions` 返回 7 条站点候选文本；其中存在重复和泛化的“宫主星落宫”描述，不能直接视为古典接纳/互容事实。
- 本地只读适配器标准化后：`planets=15`、`houses=12`、`aspects=26`、`fortune` 可用、站点接纳候选 7 条，并保留 `raw_response`。

## 结论与门禁

1. **可以通过 API 获取**行星/点的宫位、黄经黄纬、上升轴、12 宫头、相位候选和福点；因此可作为 Chart Facts 的输入源。
2. API **不能凭已给出的“太阳天蝎4宫……”清单反向验证出生资料**。验证仍需出生年月日、准确时间、经纬度、时区、黄道制和宫制。
3. API 相位只有角度/orb，未提供可靠的应用/分离状态；本体系继续标记为 `sector_candidate_without_motion`，不升级为交付性相位。
4. 站点 `mutual_receptions` 仅作外部候选线索；古典接纳必须由本地锁定的尊贵规则、方向和**实际相位连接**重新计算。
5. 本轮为 `PASS`（接口可达、字段映射通过、限制已登记）；没有把样例数据并入用户 1996 星盘。

## 复现

```powershell
python -X utf8 scripts/cet_api_client.py `
  --year 1990 --month 1 --day 1 --hour 12 --minute 0 `
  --lat 39.9042 --lon 116.4074 --tz 8 --house-system P `
  --output references/loop-runs/ROUND119-cet-normalized.json
```

该命令只读请求并写入明确指定的本地输出路径，不向远端写入数据。
