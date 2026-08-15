# 本命盘事实与发布审计报告

- chart_id：`user-1996-hunan-supplied`
- 来源：`user_supplied_summary`
- 发布决策：**HOLD**

> 本文档只发布已验证的事实、状态和缺失项；它不是在数据不足时自动生成的命理结论。

## 数据契约

| 字段 | 状态 |
| --- | --- |
| 黄道体系 | unknown |
| 宫制 | unknown |
| 日夜盘 | night（inferred_from_sun_below_horizon，confidence=low） |
| 行星度数 | 缺失 |
| 上升边界风险 | high |
| 规则版本 | {"terms": "egyptian", "triplicity": "dorotheus_style_three_rulers", "faces": "chaldean", "reception": "direction_plus_connection_required", "aspect": "application_separation_required"} |
| 规则版本锁 | 已锁定 |
| 缺失字段 | birth_date, birth_time, birth_place, zodiac, house_system, planetary_degrees |

## Chart Facts：行星与宫位

| 对象 | 星座 | 度数 | 宫位 |
| --- | --- | --- | --- |
| 太阳 | 天蝎 | N/A | 4 |
| 月亮 | 天蝎 | N/A | 5 |
| 水星 | 天蝎 | N/A | 5 |
| 金星 | 天秤 | N/A | 3 |
| 火星 | 处女 | N/A | 2 |
| 木星 | 摩羯 | N/A | 6 |
| 土星 | 白羊 | N/A | 9 |
| 天王星 | 水瓶 | N/A | 7 |
| 海王星 | 摩羯 | N/A | 6 |
| 冥王星 | 射手 | N/A | 5 |
| 北交点 | 天秤 | N/A | 3 |
| 凯龙 | 天秤 | N/A | 4 |
| 婚神 | 白羊 | N/A | 9 |
| 南交点 | 白羊 | N/A | 9 |
| 福点 | 巨蟹 | N/A | 12 |

### 事实来源层

| 字段 | 来源/计算状态 |
| --- | --- |
| placements | user_declared_unrecomputed |
| cusps | user_declared_unrecomputed |
| aspect_claims | user_declared_sector_validated |
| rulership_fly_ins | computed_traditional_from_declared_cusps |
| reception_validation | computed_from_declared_signs_and_locked_rule_version |
| planetary_state | computed_from_declared_signs_houses_with_provisional_zodiac |
| rulership_candidates | computed_from_declared_cusp_signs_and_locked_dignity_versions |

## 宫位责任与飞宫

| 宫位 | 宫头 | 传统宫主 | 宫主落宫 |
| --- | --- | --- | --- |
| 1 | 巨蟹 | 月亮 | 5 |
| 2 | 狮子 | 太阳 | 4 |
| 3 | 处女 | 水星 | 5 |
| 4 | 天秤 | 金星 | 3 |
| 5 | 天蝎 | 火星 | 2 |
| 6 | 射手 | 木星 | 6 |
| 7 | 摩羯 | 土星 | 9 |
| 8 | 水瓶 | 土星 | 9 |
| 9 | 双鱼 | 木星 | 6 |
| 10 | 白羊 | 火星 | 2 |
| 11 | 金牛 | 金星 | 3 |
| 12 | 双子 | 水星 | 5 |

## 行星状态

| 行星 | 本质状态 | sect | 角性 | 界 | 面 |
| --- | --- | --- | --- | --- | --- |
| 太阳 | 未发现已确认本质尊贵 | out_of_sect | angular | unknown_due_to_missing_degree | unknown_due_to_missing_degree |
| 月亮 | fall, triplicity_participating | in_sect | succedent | unknown_due_to_missing_degree | unknown_due_to_missing_degree |
| 水星 | 未发现已确认本质尊贵 | variable | succedent | unknown_due_to_missing_degree | unknown_due_to_missing_degree |
| 金星 | domicile | in_sect | cadent | unknown_due_to_missing_degree | unknown_due_to_missing_degree |
| 火星 | triplicity_participating | in_sect | succedent | unknown_due_to_missing_degree | unknown_due_to_missing_degree |
| 木星 | fall | out_of_sect | cadent | unknown_due_to_missing_degree | unknown_due_to_missing_degree |
| 土星 | fall, triplicity_participating | out_of_sect | cadent | unknown_due_to_missing_degree | unknown_due_to_missing_degree |

## 相位验证

| 对象1 | 对象2 | 相位 | 证据层 | 状态 | 支持等级 | orb | 需度数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 太阳 | 月亮 | 合 | classical_core | sign_supported | sector_supported | N/A | 是 |
| 太阳 | 水星 | 合 | classical_core | sign_supported | sector_supported | N/A | 是 |
| 太阳 | 木星 | 六合 | classical_core | sign_supported | sector_supported | N/A | 是 |
| 太阳 | 海王 | 六合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 太阳 | 福点 | 拱 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 月亮 | 水星 | 合 | classical_core | sign_supported | sector_supported | N/A | 是 |
| 月亮 | 土星 | 拱 | classical_core | boundary_sensitive | boundary_only | N/A | 是 |
| 月亮 | 海王 | 六合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 月亮 | 冥王 | 合 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 月亮 | 福点 | 拱 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 水星 | 土星 | 拱 | classical_core | boundary_sensitive | boundary_only | N/A | 是 |
| 水星 | 天王 | 六合 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 水星 | 海王 | 六合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 水星 | 冥王 | 合 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 水星 | 福点 | 拱 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 金星 | 木星 | 刑 | classical_core | sign_supported | sector_supported | N/A | 是 |
| 金星 | 北交 | 合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 金星 | 凯龙 | 合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 火星 | 木星 | 拱 | classical_core | sign_supported | sector_supported | N/A | 是 |
| 火星 | 冥王 | 刑 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 木星 | 北交 | 刑 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 木星 | 南交 | 刑 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 土星 | 天王 | 六合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 土星 | 海王 | 六合 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 土星 | 冥王 | 拱 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 土星 | 北交 | 冲 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 土星 | 婚神 | 合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 土星 | 南交 | 合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 土星 | 福点 | 拱 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 天王 | 海王 | 合 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 天王 | 冥王 | 六合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 天王 | 北交 | 拱 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 天王 | 凯龙 | 刑 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 天王 | 婚神 | 六合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 天王 | 福点 | 冲 | auxiliary_context | boundary_sensitive | boundary_only | N/A | 是 |
| 海王 | 凯龙 | 刑 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 海王 | 福点 | 冲 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 冥王 | 北交 | 六合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 冥王 | 婚神 | 拱 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 冥王 | 南交 | 拱 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 北交 | 婚神 | 冲 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 凯龙 | 福点 | 刑 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |
| 婚神 | 南交 | 合 | auxiliary_context | sign_supported | sector_supported | N/A | 是 |

## 接纳与互容验证

| 方向 | 类型 | 出发星座 | 接收星座 |
| --- | --- | --- | --- |
| 太阳->火星 | domicile_reception | 天蝎 | 处女 |
| 月亮->火星 | domicile_reception | 天蝎 | 处女 |
| 水星->火星 | domicile_reception | 天蝎 | 处女 |
| 火星->水星 | domicile_reception | 处女 | 天蝎 |
| 木星->土星 | domicile_reception | 摩羯 | 白羊 |
| 土星->火星 | domicile_reception | 白羊 | 处女 |
- 接纳方向审计：支持宫主接纳 9 条；未匹配 0 条；互容缺反向 0 条；连接状态 {"no_aspect_claim": 9}；规则版本 `direction_plus_connection_required`。

已识别双向守护互容：水星—火星

## 主题覆盖

| 主题 | 责任宫位 | 已有宫位事实 | 状态 |
| --- | --- | --- | --- |
| self_decision | 1 | 1 | available |
| money_income | 2, 11, 10 | 2, 11, 10 | available |
| shared_resources | 8, 7, 2 | 8, 7, 2 | available |
| career_public_role | 10, 1, 6, 7, 11 | 10, 1, 6, 7, 11 | available |
| relationship_family | 7, 4, 1, 8 | 7, 4, 1, 8 | available |
| creation_children | 5, 1, 4, 8 | 5, 1, 4, 8 | available |
| pressure_risk | 6, 8, 12 | 6, 8, 12 | available |

## 责任链与共享证据审计

| 主题 | 宫位→宫主→落宫 | 去重后宫主 | 主题内重复 |
| --- | --- | --- | --- |
| self_decision | 1:月亮→5 | 月亮 | 无 |
| money_income | 2:太阳→4 → 11:金星→3 → 10:火星→2 | 太阳, 火星, 金星 | 无 |
| shared_resources | 8:土星→9 → 7:土星→9 → 2:太阳→4 | 土星, 太阳 | 土星 |
| career_public_role | 10:火星→2 → 1:月亮→5 → 6:木星→6 → 7:土星→9 → 11:金星→3 | 土星, 月亮, 木星, 火星, 金星 | 无 |
| relationship_family | 7:土星→9 → 4:金星→3 → 1:月亮→5 → 8:土星→9 | 土星, 月亮, 金星 | 土星 |
| creation_children | 5:火星→2 → 1:月亮→5 → 4:金星→3 → 8:土星→9 | 土星, 月亮, 火星, 金星 | 无 |
| pressure_risk | 6:木星→6 → 8:土星→9 → 12:水星→5 | 土星, 木星, 水星 | 无 |
- 跨主题共享宫主：土星, 太阳, 月亮, 木星, 火星, 金星。相同宫主的行星状态在评分层只计一次；宫位责任链仍分别保留。

## 尊贵主宰候选审计

此表保留各项尊贵主张，不把它们相加为单一吉凶分数；传统宫主仍是责任链锚点。
三分主宰依赖 sect：night（inferred_from_sun_below_horizon，confidence=low）；低置信度只作候选，不作裁决。

| 位置 | 星座 | 传统宫主 | 尊贵候选（主张） | 状态 | 未能核验 |
| --- | --- | --- | --- | --- | --- |
| 1 | 巨蟹 | 月亮 | 月亮[domicile,triplicity_participating]; 木星[exaltation]; 火星[triplicity_night] | provisional_sign_only | term,face |
| 2 | 狮子 | 太阳 | 土星[triplicity_participating]; 太阳[domicile]; 木星[triplicity_night] | provisional_sign_only | term,face |
| 3 | 处女 | 水星 | 月亮[triplicity_night]; 水星[domicile]; 火星[triplicity_participating] | provisional_sign_only | term,face |
| 4 | 天秤 | 金星 | 土星[exaltation]; 木星[triplicity_participating]; 水星[triplicity_night]; 金星[domicile] | provisional_sign_only | term,face |
| 5 | 天蝎 | 火星 | 月亮[triplicity_participating]; 火星[domicile,triplicity_night] | provisional_sign_only | term,face |
| 6 | 射手 | 木星 | 土星[triplicity_participating]; 木星[domicile,triplicity_night] | provisional_sign_only | term,face |
| 7 | 摩羯 | 土星 | 土星[domicile]; 月亮[triplicity_night]; 火星[exaltation,triplicity_participating] | provisional_sign_only | term,face |
| 8 | 水瓶 | 土星 | 土星[domicile]; 木星[triplicity_participating]; 水星[triplicity_night] | provisional_sign_only | term,face |
| 9 | 双鱼 | 木星 | 月亮[triplicity_participating]; 木星[domicile]; 火星[triplicity_night]; 金星[exaltation] | provisional_sign_only | term,face |
| 10 | 白羊 | 火星 | 土星[triplicity_participating]; 太阳[exaltation]; 木星[triplicity_night]; 火星[domicile] | provisional_sign_only | term,face |
| 11 | 金牛 | 金星 | 月亮[exaltation,triplicity_night]; 火星[triplicity_participating]; 金星[domicile] | provisional_sign_only | term,face |
| 12 | 双子 | 水星 | 木星[triplicity_participating]; 水星[domicile,triplicity_night] | provisional_sign_only | term,face |

### 主题级主宰分歧

分歧本身是结果：在缺少区分证据时保留并列，不把候选数量当作结论强度。

| 主题 | 传统宫主 | 其他候选 | 分歧宫位 | 状态 |
| --- | --- | --- | --- | --- |
| self_decision | 月亮 | 木星, 火星 | 1 | competing_candidates |
| money_income | 太阳, 火星, 金星 | 土星, 月亮, 木星 | 2, 10, 11 | competing_candidates |
| shared_resources | 土星, 太阳 | 月亮, 木星, 水星, 火星 | 2, 7, 8 | competing_candidates |
| career_public_role | 土星, 月亮, 木星, 火星, 金星 | 太阳 | 1, 6, 7, 10, 11 | competing_candidates |
| relationship_family | 土星, 月亮, 金星 | 木星, 水星, 火星 | 1, 4, 7, 8 | competing_candidates |
| creation_children | 土星, 月亮, 火星, 金星 | 木星, 水星 | 1, 4, 5, 8 | competing_candidates |
| pressure_risk | 土星, 木星, 水星 | 无 | 6, 8, 12 | domicile_only_candidate_set |

### 高风险主题输出闸门

| 主题 | 前置限制 |
| --- | --- |
| self_decision | standard_structural_language |
| money_income | standard_structural_language |
| shared_resources | financial_due_diligence_required |
| career_public_role | standard_structural_language |
| relationship_family | no_deterministic_relationship_or_family_outcome |
| creation_children | G2_context_only_no_reproductive_outcome |
| pressure_risk | G1_no_medical_or_mortality_claim |

## 证据层级

- 古典七曜：太阳、月亮、水星、金星、火星、木星、土星建立宫位责任、sect、尊贵与核心交付判断。
- 现代辅助：天王星、海王星、冥王星、交点、凯龙、婚神和现代相位不能独立升级本命结论。
- 来源与版本：R25（本质/偶然尊贵）、R26（三分主宰）、R19（接纳）、R21（相位）；具体规则仍需与 Chart Facts 一起调用。

## 核心判断

N/A：发布闸门未通过时只报告事实，不生成生活结论。

## 结构性优势

N/A：当前报告不是解释层，避免把单一状态包装成能力结论。

## 结构性矛盾

N/A：当前报告不是解释层，矛盾假设需在完整度数和主题责任链齐备后生成。

## 风险边界

当前主要风险是数据边界而非命理结论：缺失度数、宫制或上升临界资料会改变相位与宫位判断。

## 咨询建议

先补齐出生日期、准确时间、地点/经纬度、黄道体系、宫制和行星度数，再进入本命解释。

## 证据链与发布闸门


## 来源冲突簇状态

| 冲突簇 | 版本键 | 状态 | 当前值 |
| --- | --- | --- | --- |
| terms_version | terms | locked | {"terms": "egyptian"} |
| triplicity_version | triplicity | locked | {"triplicity": "dorotheus_style_three_rulers"} |
| reception_condition | reception, aspect | locked | {"reception": "direction_plus_connection_required", "aspect": "application_separation_required"} |
| modern_validity | N/A | not_versioned | {} |

- 来源版本闸门：**PUBLISH**
- 来源闸门阻塞：无

## 段落级证据标签

下表是正文写作的硬闸门；`BLOCKED` 段落只能写事实与边界，不能用模板句替代推断。
| 段落 | 证据状态 | 允许范围 | 阻塞项 |
| --- | --- | --- | --- |
| 核心判断 | BLOCKED | 仅可报告事实、缺失项和限制；不得写生活结论 | chart_contract_incomplete |
| 结构性优势 | BLOCKED | 仅可报告事实、缺失项和限制；不得写生活结论 | chart_contract_incomplete |
| 结构性矛盾 | BLOCKED | 仅可报告事实、缺失项和限制；不得写生活结论 | chart_contract_incomplete |
| 风险边界 | BLOCKED | 仅可报告事实、缺失项和限制；不得写生活结论 | chart_contract_incomplete |
| 咨询建议 | BLOCKED | 仅可报告事实、缺失项和限制；不得写生活结论 | chart_contract_incomplete |

## 现实观察与隐私状态

现实观察只作为 H1/H2 判别层，不等同于星盘事实；敏感陈述只保留最小必要字段。`uncollected` 不等于没有反证，`withdrawn` 不等于支持任何假设。
| 状态 | 总记录 | active | 撤回/删除墓碑 | 校验发现 | 隐私处理 | 词典版本 | 词典变更 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| not_collected | 0 | 0 | 0 | 无 | 未发现敏感记录 | SENSITIVE-0.3 | 新增英文术语、空格/连字符归一化和寿命/自伤隐喻；保留既有中文类别。 |
- 事实库存：通过
- 本命解释就绪：未通过
- 阻塞项：chart_contract_incomplete
- 警告项：duplicate_reception_claims；duplicate_fly_in_claims；reception_connection_requires_degree_validation；aspect_degrees_required；ascendant_boundary_risk_high

### 证据链状态

在发布闸门通过前，不生成‘主体—机制—可观察表现’的生活结论；每条结论仍需补充 Evidence → Rule → Inference → Counter-test。

## 不可判断项

- 缺失出生资料、黄道/宫制或度数时，不能确认精确相位、应用/分离、界/面、燃烧、速度、可见性或事件时间/事件日期。
- 未来时间技术尚未激活；本命盘不输出年份、月份或日期。
- 本命事实不能单独确认具体婚期、投资结果、医疗结论、疾病、法律结果或他人行为。

