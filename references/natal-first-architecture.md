# 本命优先分析架构

> 版本：NATAL-1.0
>
> 当前系统只把本命盘作为激活层。推运、行运、主限、年限和其他时间技术保留接口，但不得提前参与本命结论。

## 一、系统分层

```text
ACTIVE: Natal Core
  N0 数据契约
  N1 Chart Facts
  N2 行星与宫位责任
  N3 主题责任链
  N4 竞争假设与反证
  N5 全貌综合
  N6 专业文档发布

INACTIVE: Timing Extensions
  T1 年度 profections
  T2 推运/次限
  T3 行运
  T4 主限、zodiacal releasing、太阳回归等
```

时间技术只有在用户明确提出未来时间问题、且数据达到要求时才激活。激活后仍必须先完成本命核心层。

## 二、N0 数据契约

```text
chart_id: [匿名 ID]
zodiac: tropical / sidereal / unknown
house_system: [明确名称]
birth_date: [日期]
birth_time: [时间与精度，例如 ±5 分钟 / 约 / 不详]
birth_place: [地点与坐标]
source: [软件、截图、PDF 或用户手工数据]
degrees_available: true / false
ascendant_boundary_risk: low / medium / high
sect_status: day / night / uncertain
rule_versions:
  terms: [egyptian / ptolemaic / unknown]
  triplicity: [declared version]
  faces: [chaldean / unknown]
  reception: [declared policy]
  aspect: [declared policy]
```

当数据来自 CET 公共接口时，原始 `input`、`ephemeris`、`axes`、`house_cusps_detail`、`aspects` 和 `Fortune` 必须随 Chart Facts 一起留存。CET 的 `mutual_receptions` 只作为外部候选字段；宫主飞宫、严格接纳/互容、应用/分离相位和尊贵类型仍由本地规则重算。

terms、triplicity、faces、reception 和 aspect 的版本/政策必须在 Chart Facts 中锁定；未锁定时可以展示诊断结果，但不能发布高等级尊贵、接纳或相位结论。

若 `zodiac`、`house_system`、出生时间精度或度数缺失：

- 仍可提取确定的星座/行星事实，但不能假定精确宫位、应用相位或事件时间。
- 上升位于 0° 或 29°–30°，必须建立分支盘或降低结论等级。
- 日夜盘由太阳相对于地平线的位置判定，不由太阳星座或钟表时间猜测。

## 三、N1 Chart Facts 清单

只记录事实，不写“所以你是……”：

1. 上升、天顶、太阳、月亮、七曜行星的星座、度数、宫位。
2. 十二宫宫头与宫主；每个宫主落入何宫、何座。
3. 尊贵：守护、擢升、三分、界、面；不得把尊贵直接等同于好坏。
4. 状态：日夜盘、角宫/续宫/果宫、顺逆、速度、可见性、燃烧、光线下、cazimi。
5. 应用/分离相位、接纳类型与方向、互容是否真的成立。
6. 福点及其他已明确计算公式的 Lots；现代外行星只列为辅助事实。
7. 位于关键宫位的星体、dispositor 链，以及资料缺失项。

## 四、N2 本命核心判断顺序

固定顺序：

```text
宫位责任
→ 宫主与落宫
→ 行星能力（尊贵、sect、角性、可见性、速度）
→ 相位与接纳
→ dispositor 交付路径
→ 支持/限制/反证
→ 结构性翻译
```

七曜建立古典核心判断；Uranus、Neptune、Pluto 的位置、宫位和相位仍应在同一轮本命 Chart Facts 中登记，再由 `natal_core_extension` 路由解释。它们不是古典主宰星，不能单独升级或推翻结论；Chiron、节点、星座小行星和现代专属相位仍保持辅助层。

## 五、N3 主题责任链

本命盘先做结构性主题，不做事件日期：

| 主题 | 最小扫描 |
|---|---|
| 自我与决策 | 1 → 1 宫主 → sect/light |
| 财富与收入 | 2 → 2 宫主 → 1 → 11 → 10 |
| 债务与共享资源 | 8 → 8 宫主 → 2 → 7 |
| 职业与公共角色 | 10 → 10 宫主 → 1 → 6 → 7 → 11 |
| 关系与婚姻 | 7 → 7 宫主 → 1 → 8 → 4 |
| 家庭与房产 | 4 → 4 宫主 → 2 → 8 → 10 |
| 创作与子女 | 5 → 5 宫主 → 1 → 4 → 8 |
| 压力与工作负荷 | 6 → 6 宫主 → 1 → sect/light |

单一星体、单一星座或单一现代相位不能承担整个人生结论。

## 六、N4 假设与反证卡

每个重要主题至少生成：

```text
H1_leading: 最有支持的结构解释
H2_runner_up: 第二解释
support: 独立证据列表
counter: 限制或相反证据
missing_discriminator: 还缺什么数据/技术
observation_contract: 现实观察记录（支持 H1/H2、反驳 H1 或中性；含来源与时间范围）
record_version/state: [版本号；active / withdrawn / superseded / deleted]
withdrawal_reason: [撤回、替代或删除时必填]
grade: S / A / B / C / N/A
```

例：2 宫主落 4 宫不能直接等于“靠房产发财”，至少要竞争：

- H1：家庭资源、房产或固定资产成为财富渠道。
- H2：家庭义务、居住成本或家族资金绑定成为财务负担。
- 判别：4 宫主、2/8/10/11 链、尊贵、接纳、现实资料与时限技术。

## 七、N5 全貌快照

本命文档开头先输出 5–8 条高信息密度判断：

1. 核心驱动：这个人如何做决定、获得资源和交付能力。
2. 主导领域：职业、财富、关系、家庭或创作中哪条链最强。
3. 最大矛盾：哪两组宫位/行星争夺同一资源。
4. 代价机制：压力、债务、控制、失信、过度承诺或关系边界如何形成。
5. 可用杠杆：哪种现实行为能改善交付路径。
6. 最强证据与最弱证据：明确区分 S/A 与 B/C。
7. 不能判断的内容：时间、具体事件、医学、法律、投资和他人行为。

每条都必须通过 `Evidence → Rule → Inference → Counter-test → Conclusion`。

现实观察属于独立的判别层，不得伪装成星盘事实。每条 active 观察至少记录 `id`、`record_version`、具体陈述、来源定位、观察期间、关系方向（`supports_H1` / `supports_H2` / `contradicts_H1` / `neutral`）、置信类型和 `state=active`；撤回/替代/删除记录只保留墓碑与理由，不进入评分。`superseded` 必须指向同一 ID 下存在的目标版本，禁止自指；同一版本不得在墓碑后静默复活，恢复必须使用新版本号。缺失或格式错误时只标记 `uncollected/invalid`，不补写成反证。

## 八、未来时限接口（暂不激活）

未来需要推运时，新增而不是改写本命层：

```text
timing_method: profection / transit / secondary_progression / primary_direction / other
activation_date_range: [起止]
activated_natal_chain: [被激活的本命宫主/宫位]
timing_evidence: [时间技术证据]
natal_baseline: [本命先验结构]
event_claim_limit: [允许到哪一级，不得超过资料能力]
```

没有本命基线，不允许单独解释推运；没有时间技术，不允许从本命盘给出年份、月份或事件日期。

## 九、本命发布门槛

本命文档只有在以下条件全部满足时才标记 `published`：

1. 数据契约完整，或明确列出缺失项。
2. Chart Facts 与解释分离。
3. 每个核心判断至少两条独立证据或降级为 B/C。
4. 至少有一条反证或竞争假设。
5. 7 个主题域有材料则写判断，无材料则写 N/A。
6. 不使用时间技术制造事件日期。
7. 敏感主题经过 G1/G2/G3 闸门。
8. 通过 [check_research_loop.py](../scripts/check_research_loop.py) 和 [check_natal_first.py](../scripts/check_natal_first.py)。

## 十、飞宫责任链与主题去重

`build_natal_facts.py` 同时保留传统宫主计算结果与用户/软件提供的 `fly_ins` 原始声明。每个主题输出 `path=[宫位, 宫主, 宫主落宫]`，并建立跨主题宫主索引。相同宫主可以承担多个主题，但在评分层只计一次行星状态证据；宫位责任仍分别保留，避免把“同一颗星重复出现”误写成多条独立证据。

现代共主或附加飞宫只作为并列辅助事实；只有传统宫主目的地缺失时才进入冲突闸门。重复声明不静默删除，而是进入输入审计警告。
