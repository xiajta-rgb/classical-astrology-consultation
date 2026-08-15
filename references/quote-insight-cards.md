# 经典摘录与洞见卡

> 用途：把书籍、论文和优质文章转成可按主题检索的短卡。短引文保留版本信息；长段落一律改写为摘要，不把摘录伪装成原典规则。

## 调用字段

```text
card_id: QI-xxx
source_id: Rxx
locator: [Book/Part/Chapter/Page/DOI]
tags: [@chart_validation, @sect, @timing, @lots, @sensitive, @methodology, @history]
quote: [不超过25个英文单词；无可靠版本时填 none]
paraphrase: [中文洞见，忠实但不冒充直译]
operational_rule: [能否进入算法；进入哪一步]
conditions: [适用条件]
counter_test: [反证、限制或竞争解释]
output_guardrail: [用户可见表达边界]
status: [draft / verified / auxiliary / retired]
```

## 已建立的洞见卡

### QI-001｜预知是有条件的，不是命运保证

```text
card_id: QI-001
source_id: R01
locator: Tetrabiblos, Book I, Chapter III
tags: [@chart_validation, @methodology, @ethics]
quote: "prescience by astronomy is possible under certain adaptation"
paraphrase: 托勒密在理论序言中把占星式预知描述为受条件限制的能力，而非脱离资料质量与适用条件的绝对预言。
operational_rule: 写入所有咨询的边界层与 Chart Facts；先核验星历、宫制、出生时刻和技术适用性，再判断。
conditions: 必须区分本命结构、时限技术和现实事实；缺数据时降级为 N/A。
counter_test: 传统文本的理论主张本身不能证明现代预测效度；需参考 R08、R13–R15 的方法学材料。
output_guardrail: 使用“在这些条件下可作结构性推断”，禁止写成“必然发生”。
status: verified
```

### QI-002｜吉凶星不是二元开关

```text
card_id: QI-002
source_id: R01
locator: Tetrabiblos, Book I, Chapters V–VII
tags: [@sect, @planetary_state, @evidence]
quote: none
paraphrase: 托勒密将吉星/凶星、昼夜属性与行星性质放在同一体系内讨论；这支持“性质 + 位置 + 关系 + 盘型”的组合判断，而不是把某星永远等同于好运或坏运。
operational_rule: 保留现有 sect、尊贵、角宫、可见性、接纳和相位的分层审计；禁止单一 dignity 直接决定结论。
conditions: 需要明确日盘/夜盘、应用/分离和行星状态。
counter_test: 某行星即使在传统上被视为 benefic，也可能因失势、受克或不能交付而受限；反之亦然。
output_guardrail: 用“交付能力增强/受限”替代“绝对吉/凶”。
status: verified
```

### QI-003｜主题要走宫位责任链，不追逐最醒目的星

```text
card_id: QI-003
source_id: R02
locator: Anthologies, Book II（Riley 译本；章节级索引待逐条复核）
tags: [@house_rulership, @timing, @hypothesis]
quote: none
paraphrase: 瓦伦斯的案例材料把上升、月亮、福点、命运点/灵魂点、角宫和时限放在不同主题中使用，提示同一主题应扫描完整链条，而非抓住一个强烈象征。
operational_rule: 继续执行“主题宫位 → 宫主 → 宫主落宫 → 尊贵/状态 → 相位/接纳 → 时限”的最小扫描。
conditions: 年龄或事件问题必须补充 profection、主限或其他明确时限技术。
counter_test: Riley 译本标为 preliminary/unperfected；章节语境和术语需要与底本及其他译本互校。
output_guardrail: 每个核心判断至少展示两条独立证据，并保留竞争假设。
status: auxiliary
```

### QI-025｜透明评分可以枚举假设，但不能伪装成古典统一权重

```text
card_id: QI-025
source_id: R31
locator: sections What bonification means; What maltreatment means; The bonification conditions this calculator scores; The maltreatment conditions this calculator scores; How sect changes the reading; What counteraction looks like in practice
tags: [@dignity, @sect, @reception, @aspects, @anti_overfit, @source_criticism]
quote: none
paraphrase: Augurine 明确把扶助/虐待条件做成可见的假设清单，并承认不同作者的条件、阈值和权重并不统一；“clean/pressured/strongly maltreated”只是本工具的评分标签，不是命运结论。它还把同时存在扶助和压力称为 counteraction，而不是把两者粗暴相消。
operational_rule: 允许把扶助、虐待、围护、压制、sect 权重、尊贵、接纳、相位和 counteraction 记录为候选特征集合；不允许把候选数量相加为吉凶分数，也不允许跨作者混合orb、权重和整宫/象限宫规则；来源批评必须显示在结果中。
conditions: 必须保存采用的作者/版本、宫制、sect、度数、相位方向和接纳；缺少运动、精确度数或规则版本时只输出 unknown/候选集合。
counter_test: 相同几何相位在昼夜盘、不同宫制或不同作者规则下出现不同权重时，系统必须保留分支；同时有扶助与压力时不得写成“抵消为零”，应测试哪一条责任链能实际交付。
output_guardrail: 写“当前版本枚举到扶助与压力两组证据，交付方向仍需核验”，不写“评分高所以一定吉”或“分数抵消所以没事”。
status: auxiliary
```

### QI-004｜禁忌征象首先是历史语境，不是现代身份标签

```text
card_id: QI-004
source_id: R02
locator: Anthologies, Book II（行星/星座身体与社会象征段落）
tags: [@sensitive, @history, @ethics]
quote: none
paraphrase: 瓦伦斯保存了大量把疾病、性、精神状态、奴役和道德评价混在一起的古代措辞；这些材料能说明当时的世界观，却不能直接翻译成现代诊断或身份判断。
operational_rule: 任何相关条目必须经过 G1/G2/G3 敏感闸门，并把历史词汇转译为“压力、约束、资源、关系边界”等可观察机制。
conditions: 用户主动提出主题；现实医疗、法律和安全资料优先。
counter_test: 历史标签含时代偏见，且单一行星/星座不能承担现代身份结论。
output_guardrail: 不预测死亡、疾病、犯罪、性取向、怀孕结果、诅咒或暴力事实。
status: verified
```

### QI-005｜传本链本身就是证据的一部分

```text
card_id: QI-005
source_id: R03
locator: Masha’allah, On Eclipses and Planetary Conjunctions（译者说明）
tags: [@history, @source_criticism]
quote: "The original Arabic text is lost."
paraphrase: 当原语文本失传、现存材料依靠中世纪拉丁传本时，必须把翻译、抄本和版本链写进证据，而不能声称掌握无争议的“作者原意”。
operational_rule: 在研究卡中强制记录作者、语言、译者、传本和印本；来源冲突未解决时不得升级为核心规则。
conditions: 每条规则必须能回到具体章节或页码。
counter_test: 后世译者可能重排术语、加入时代解释或改变技术边界。
output_guardrail: 用“现存传本显示/该译本将其解释为”，不写“原典明确证明”。
status: verified
```

### QI-006｜传统权威与现代效度是两条线

```text
card_id: QI-006
source_id: R08
locator: Carlson, Nature 318 (1985), 419–425, DOI 10.1038/318419a0
tags: [@methodology, @evidence, @ethics]
quote: none
paraphrase: 双盲研究的存在本身提醒我们：历史传统的丰富性不能替代可检验的研究设计；咨询系统应把传统解释、现实观察和现代验证分开记录。
operational_rule: 为每条重要规则增加 modern_status 字段；没有现代检验时，不得把传统等级写成科学确定性。
conditions: 需要阅读全文的方法、样本、统计和后续复核；本卡暂不概括论文结果。
counter_test: 单项研究也不能自动裁决所有占星技术；应记录研究对象、方法边界和可重复性。
output_guardrail: 使用“传统框架中的结构性解释”，避免“科学证明/科学证伪”的过度表述。
status: auxiliary
```

### QI-007｜反照点只能作为隐性连接候选

```text
card_id: QI-007
source_id: R16
locator: Skyscript article, historical overview of antiscia
tags: [@antiscia, @hidden_technique, @source_criticism]
quote: none
paraphrase: 反照点在古典材料中有早期来源，但其功能应被理解为对称/隐性联系的候选，不是自动等同于实际相位。
operational_rule: 只有在来源版本、实际度数、对称轴、相关宫主链和至少一条主证据同时成立时，才作为 C/B 辅助。
conditions: 必须声明计算方式，并与普通相位分开记录。
counter_test: 无应用连接、无主题宫位责任或仅有反照点时，不升级判断。
output_guardrail: 写“辅助连接可能把两个主题拉到同一语境”，不写“反照点必然触发事件”。
status: auxiliary
```

### QI-008｜Lots 的价值取决于公式、盘型与责任链

```text
card_id: QI-008
source_id: R17/R20
locator: Fortuna, Spirit and the Lunation Cycle; Finding Fortuna
tags: [@lots, @sect, @formula_control]
quote: none
paraphrase: 福点与灵魂点不是装饰性标记；但历史上存在昼夜公式、反转计算和传本争议，必须先固定公式，再检查其宫位、宫主与交付路径。
operational_rule: 先固定 sect（日/夜）与公式版本；Lots 只能补强已经由宫位/宫主链提出的假设，不能单独制造财富、事业或命运结论。
conditions: 记录公式、日夜盘、度数、计算工具和版本。
counter_test: 公式未锁定或不同版本产生不同宫位时，降为 N/A/待核读。
output_guardrail: 明确写“按本次公式计算的福点”，不把争议公式当成唯一传统。
status: auxiliary
```

### QI-009｜接纳必须是有方向的技术关系

```text
card_id: QI-009
source_id: R19
locator: Masha’allah, On Reception, Chapter 1 excerpt
tags: [@reception, @delivery, @hidden_technique]
quote: none
paraphrase: 接纳不是泛泛的“互相喜欢”或“有联系”；要记录谁在谁的守护/擢升等尊贵中、是否存在七曜相位连接以及关系方向。
operational_rule: 接纳字段拆成 type、direction、applying_connection、delivery_effect；没有相位连接不得称为互容完成。
conditions: 必须同时检查尊贵类型、应用/分离和行星能力。
counter_test: 单向接纳不能写成 mutual reception；接纳也不能抵消严重的不能交付。
output_guardrail: 写“行星 A 得到行星 B 的接纳，因此更容易获得某种交付条件”，不写“关系很好”。
status: auxiliary
```

### QI-010｜相位容许度属于行星体系，不是机械固定数字

```text
card_id: QI-010
source_id: R21
locator: The Classical Origin and Traditional Use of Aspects
tags: [@aspects, @visibility, @orb]
quote: none
paraphrase: 传统容许度更接近行星光束、行星重要性和可见性体系；把所有相位机械套成同一个固定度数会丢失历史条件。
operational_rule: 相位判断记录行星、光线、应用/分离、容许度依据和宫位责任，不只记录“有/无相位”。
conditions: 度数与时间精度必须足够；没有度数时不判断精确应用关系。
counter_test: 宽容许度但无实际交付、或只靠现代外行星的相位，不升级本命结论。
output_guardrail: 使用“相位连接强/弱、交付可能性高/低”，不使用绝对触发语言。
status: auxiliary
```

### QI-011｜界/terms 是版本化细化，不是统一常识

```text
card_id: QI-011
source_id: R22
locator: Ptolemy’s Terms & Conditions
tags: [@terms, @dignity, @source_conflict]
quote: none
paraphrase: 界的分配存在埃及、托勒密及其他历史体系，传统作者之间本来就有争议；混用表格会制造虚假的精确性。
operational_rule: 在系统配置中锁定尊贵与 terms_version；不同版本只能作为来源冲突并列，不能悄悄合并。
conditions: 先判断界是否真的能区分 H1/H2，再决定是否使用。
counter_test: 若主宫位、宫主、sect 和相位已指向相反方向，界只能作为次级修正。
output_guardrail: 写“在所选界表下的次级修正”，不写“界证明了某种性格”。
status: verified
```

### QI-012｜医学史洞见不能越过现代医学边界

```text
card_id: QI-012
source_id: R23
locator: Hippocrates, Humours and Temperament-Theory
tags: [@medical_history, @sensitive, @ethics]
quote: none
paraphrase: 体液与气质理论可帮助理解古代占星如何谈身体和环境，但它属于历史医学语境，不是现代病理学或诊断工具。
operational_rule: 身体象征只可转译成压力、节律、负荷或照护议题，并在 G2 闸门中明确现实专业支持。
conditions: 用户主动提出健康主题；不输出病名、病程、死亡或治疗建议。
counter_test: 任何单一星体、星座或相位都不足以诊断疾病。
output_guardrail: 写“传统文本将其与某类身体负荷相连”，不写“你会得某病”。
status: verified
```

### QI-013｜相位先过几何一致性闸门

```text
card_id: QI-013
source_id: R21
locator: The Classical Origin and Traditional Use of Aspects; chart sign geometry check
tags: [@aspects, @chart_validation, @anti_overfit]
quote: none
paraphrase: 相位不是标签清单，而是两个实际黄经位置之间的几何关系。星座只可做粗筛；最终相位、orb、应用/分离必须依赖度数。若所列星座连基本角距都不可能，先退回数据校验，不进入解释层。
operational_rule: 新命盘先运行 sign_geometry_gate；通过后才计算相位权重。度数缺失时只能保留“待核验”，不得把相位名当作事实。
conditions: 需要确认黄道体系、行星度数和相位定义；现代点与七曜分层。
counter_test: 同一星座组合可能在度数上没有有效 orb；几何可行也不代表有应用连接或能交付主题。
output_guardrail: 直接指出“相位表与星座位置不一致，暂不解释”，不要为了完整而补写相位意义。
status: verified
```

### QI-014｜本质尊贵与偶然尊贵不能压成一个吉凶分数

```text
card_id: QI-014
source_id: R25
locator: Ptolemy’s Table of Essential Dignity Explained
tags: [@dignity, @accidental_dignity, @anti_overfit]
quote: none
paraphrase: 本质尊贵描述行星与星座的固有关系，偶然尊贵描述角性、运动、可见性等位置条件；二者同时存在时，不能用一个总分抹掉“有能力但可能造成伤害”或“失势但仍有交付机会”的差异。
operational_rule: 行星状态分别记录 essential_dignity、sect、angularity、visibility、motion 和 reception；禁止用总分直接生成结论。
conditions: 必须锁定尊贵表版本，并在缺度数时降级界、面和精细可见性。
counter_test: 一颗强势行星若主凶宫或受严重限制，力量增强不等于结果良好；一颗失势行星也可能通过接纳和角性完成职责。
output_guardrail: 写“表达能力/交付能力增强或受限”，不写“分数高所以必然吉”。
status: verified
```

### QI-015｜三分主宰必须声明日夜盘与版本

```text
card_id: QI-015
source_id: R26
locator: The Classical Use of Triplicities; Dorotheus/Valens discussion
tags: [@sect, @triplicity, @source_conflict]
quote: none
paraphrase: 三分主宰有日夜优先级和参与主宰，古典与后世常用表并不完全相同；三分只能在声明采用的版本和盘型后作为能力修正，不能脱离宫位责任链独立定论。
operational_rule: 配置中记录 triplicity_version、sect 和 ruler_role（day/night/participating）；若版本未锁定，降级为辅助。
conditions: 先确定日夜盘，再解释三分；本项目默认 Dorotheus-style 三主宰表。
counter_test: 三分主宰与宫主、尊贵、角性相冲时，不能用三分单独推翻主结构。
output_guardrail: 写“在所选三分表下提供次级支持/限制”，不写“某元素决定一生”。
status: verified
```

### QI-016｜译本自我标注“初译”时，不能把它当成无争议原典

```text
card_id: QI-016
source_id: R02
locator: Skyscript, Vettius Valens—Riley translation, “Riley’s Release and Notes on this Text”
tags: [@source_criticism, @version_control, @evidence]
quote: "there are no guarantees of accuracy"
paraphrase: Riley 译本页面明确说明该译文是 1990 年代完成的 preliminary/unperfected 版本，依据 Kroll 与 Pingree 版本，并提醒读者自行承担校读责任。
operational_rule: R02 可用于发现术语和案例候选，但不能单独把某个译句升级为 S/A 核心规则；关键规则需与底本、其他译本或独立来源交叉核对。
conditions: 记录译者、底本、数字版本和章节定位；遇到关键术语先回到希腊文/批校本或另一译本。
counter_test: 译本中的补词、校正括号和术语选择可能改变技术边界；若只有该译本支持，等级最高为 auxiliary/B。
output_guardrail: 写“Riley 译本在该处如此呈现”，不写“Valens 原典无争议地证明”。
status: verified
```

### QI-017｜先确定主题位置，再选择真正的主宰

```text
card_id: QI-017
source_id: R01
locator: Tetrabiblos, Book III, Chapter IV, Distribution of the Doctrine of Nativities; Project Gutenberg 70850, paragraph beginning “Firstly, notice must be taken”
tags: [@chart_validation, @house_rulership, @dignity, @anti_overfit]
quote: "Firstly, notice must be taken of that place in the zodiac which corresponds"
paraphrase: 托勒密把本命判断写成一个有顺序的选择过程：先定位与问题相应的宫位或主点，再比较哪些行星以不同尊贵方式拥有主宰权；不能因为某颗星最醒目就跳过主题定位。
operational_rule: Chart Facts 先锁定主题位置与宫位责任链，再按 domicile、exaltation、triplicity、terms、face 的 dignity 逐层筛选主宰；若存在多个候选，保留竞争假设，不用单一星座捷径替代裁决。
conditions: 必须先锁定黄道、宫制、出生时间和所选尊贵版本；主题点、宫主、主宰行星的度数和相位数据缺失时只能列为候选。
counter_test: 若候选主宰之间无法由尊贵、sect、角性、相位或接纳区分，结论必须保持并列；若主题宫位本身未确定，任何主宰优先级都不可升级。
output_guardrail: 写“按已锁定主题位置与尊贵版本，A/B 是候选主宰”，不写“最强的那颗星就是答案”或必然事件。
status: verified
```

### QI-018：反泛化测试必须把“可套用性”当作反证变量

```text
card_id: QI-018
source_id: R27
locator: Cao & Xuan 2022, pp. 74-78, DOI 10.25236/FSST.2022.041210, open PDF
tags: [@methodology, @anti_overfit, @evidence]
quote: none
paraphrase: 一项 12 人的探索性眼动实验把 12 条无星座标签的太阳星座描述作为刺激；不限选择组多数选择多条描述，限选一条组回看次数更高。该结果支持把“同一文本能同时套到多人”作为输出反证，但不检验完整本命盘技术，也不足以判定占星有效性。
operational_rule: 作为方法层的反泛化检查，每条本命判断都必须通过 swap-chart/alternate-reading 测试：若去掉宫位责任、度数、相位连接和现实观察后，文本仍可无差别套用多数人，则降级为 generic_language_blocked，不得升级为核心洞见。
conditions: 只把该研究用于措辞和反泛化门禁；记录样本量、刺激材料、选择限制和结果，不把小样本探索性结果当作占星有效性证据。
counter_test: 结构化判断若包含明确宫位责任链、竞争假设、可观察分辨项和失败条件，即使文字简洁也不应因“可泛化”而自动否定；反之，只有星座性格形容词且无法指出独立分辨项时必须拦截。
output_guardrail: 写“本段通过具体责任链与可反驳条件降低套话风险”，不写“该研究证明占星无效”或“眼动实验验证了本命规则”。
status: auxiliary
```

### QI-019｜第二宫不是单独的“钱袋”，必须看其主宰与交付路径

```text
card_id: QI-019
source_id: R29
locator: Anthologies, Book II §2.14, PDF p. 110; §2.15, PDF p. 112
tags: [@house_rulership, @lots, @wealth, @sensitive, @source_criticism]
quote: none
paraphrase: 瓦伦斯把第二宫称为哈得斯之门，并以福点/上升的主宰、行星所在位置、sect、尊贵和时限条件来描述资源的获得与流失；他还把婚姻、父母、子女、身体和职业分别连接到不同的宫位名称。这个传统层不支持把“二宫有吉星”直接翻译成财富保证。
operational_rule: 财富模块必须扫描2宫、2宫主、11宫/福点及其主宰、10宫交付和8宫共同资源；二宫单点征象最高只作 B/C 候选；sensitive topics 仍需 G1/G2/G3 闸门；source translation must be tracked。
conditions: 必须锁定宫制、福点公式、sect、宫主落宫和相位/接纳；不同译本的第二宫措辞需并列记录。
counter_test: 若2宫主不能交付、被严重限制或现实现金流相反，二宫吉星不能抵消；若2宫本身无强星，仍可能通过宫主链获得收入。
output_guardrail: 写“财富路径由个人资源、职业定价、家庭/共同资金共同构成”，不写“二宫好所以必发财”。
status: auxiliary
```

### QI-020｜古典文本的极端禁忌语必须保留条件链，不能现代化为犯罪/死亡断言

```text
card_id: QI-020
source_id: R29
locator: Anthologies, Book II §2.16, PDF pp. 113-123; Delineation Notes on exact degree, operative/inoperative places and overall nativity
tags: [@sensitive, @aspects, @sect, @source_criticism, @anti_overfit]
quote: none
paraphrase: 瓦伦斯在相位案例中保存了暴力、监禁、性、死亡和社会污名等极端措辞，但同一节反复加入“整体命盘是否支持、是否为主宰/总主宰、是否在有效宫位、是否有帮助行星、度数是否精确”等条件。深层可用洞见是：极端结果不是单一相位的含义，而是多重责任链、交付能力与现实权力结构叠加后的历史性叙述。
operational_rule: 把极端历史词汇转换为资源损失、法律/权力冲突、关系边界、强制性约束等可观察机制；aspect 与 sect 必须入条件链；只有在用户主动提出敏感主题且完成 G1/G2/G3 门禁时才展示历史语境；source translation remains historical context。
conditions: 必须有完整度数、宫位责任链、sect、主宰层级、相位方向和现实观察；单一现代外行星相位不适用。
counter_test: 缺少任一关键条件时，极端解释应降为 N/A；历史译本的时代偏见、译者补词和方法差异也可能改变含义。
output_guardrail: 禁止预测死亡、犯罪、疾病、性取向、暴力或诅咒；只能说明历史文本曾把某类结构与高压/损失/权力冲突相连，并明确现代证据不足。
status: auxiliary
```

### QI-021｜福点与Daimon的价值在于行动/身体分层，不在于制造“命运标签”

```text
card_id: QI-021
source_id: R29
locator: Anthologies, Book II §§2.17-2.20, PDF pp. 124-129
tags: [@lots, @sect, @wealth, @house_rulership, @source_criticism]
quote: none
paraphrase: 瓦伦斯把福点等同于生命、身体和手的工作，把Daimon及其主宰连接到心智、给予/接受与行动，并要求检查它们的宫位、星座、主宰和相位；福点的第11位还被描述为取得/成就之处。洞见不是“福点决定财富”，而是把身体劳作、心智行动、收益和结果分成可审计的路径。
operational_rule: Lots层只作为已存在的财富/职业责任链的辅助分支；记录公式、sect、Lot所在宫位、主宰、相位和现实交付，不单独生成等级；source formula and source translation must be versioned。
conditions: 必须锁定昼夜公式和计算版本；福点或Daimon缺失、公式争议或宫位跨界时降为 N/A。
counter_test: Lot的良好位置不能抵消主宰失势、无交付或现实现金流反证；不同公式产生不同位置时保留分支。
output_guardrail: 写“按本次公式，Lot提供一条身体/行动或资源路径的辅助证据”，不写“命中福点就注定富贵”。
status: auxiliary
```

### QI-022｜Planetary Joys 是宫位意义的历史构造假说，不是现代宫位等号

```text
card_id: QI-022
source_id: R28
locator: PDF pp. 1-5, 9, 18, 25-27
tags: [@house_rulership, @sect, @aspects, @history, @source_conflict]
quote: none
paraphrase: Brennan的研究把七曜的joys、宫位别名、sect、角宫三角和宫位象义放在一个早期地中海传统的系统构造中讨论，并明确指出Manilius存在不同joys排列。它提供的是历史解释框架：宫位意义可能由角性、可见配置、joys和传统命名共同形成，而不是“第一宫等于白羊座”式现代等号。
operational_rule: 允许在宫位语义层调用joys作为 C/B 辅助标签；不得替代宫主、宫位责任链或具体度数；记录采用主流joys表还是Manilius变体；sect 和 aspects 只作历史构造的辅助语境。
conditions: 必须声明该来源是二手历史重构，并与Valens、Paulus、Firmicus等 primary text 交叉核验。
counter_test: joys排列存在历史变体，且joys语义不能解释全部本命结果；若与具体宫主交付相冲，只保留为背景层。
output_guardrail: 写“该宫位在joys框架中具有某种传统语义背景”，不写“因为某星喜乐于此宫，所以事件必然发生”。
status: auxiliary
```

### QI-023｜同一相位的强弱取决于精确度数、方向、有效性与整盘支持

```text
card_id: QI-023
source_id: R29
locator: Anthologies, Book II §2.16, PDF pp. 113-123; §2.22, PDF pp. 141-149
tags: [@aspects, @sect, @dignity, @anti_overfit, @source_criticism]
quote: none
paraphrase: 瓦伦斯反复区分三分、六合、对冲、精确到度数的相位、左右方向、有效/无效宫位、主宰身份和整盘贵贱；他还明确写出同一星体组合会因星座、度数、宫位和整体盘势而改变结果。相位名称本身不是结论，配置质量决定可交付程度。
operational_rule: 相位层必须记录几何角距、orb、应用/分离、左右方向、evidence_layer、sect、dignity、行星状态和是否为主题宫主；缺其中一项时降级为几何候选；source translation requires cross-check。
conditions: 需要精确度数和运动数据；Riley译本的数学与术语仍需交叉校对。
counter_test: 宽orb、无运动、无主题宫主责任或只有现代外行星的相位不升级；若整盘基础不支持，单一“好相位”不能制造高阶结论。
output_guardrail: 写“该相位在当前度数与责任链下提供支持/摩擦”，不写“某相位必然带来某事件”。
status: auxiliary
```

### QI-024｜扶助/虐待不是“吉凶开关”，而是交付能力的第二层审计

```text
card_id: QI-024
source_id: R30
locator: sections What Bonification and Maltreatment Are; Bonification; Maltreatment; Reception; Cazimi
tags: [@dignity, @reception, @aspects, @sect, @source_criticism, @anti_overfit]
quote: none
paraphrase: 该教学文把本质尊贵与偶然状态分开：吉星的入相三分/六合、接纳或围护可提供“救援路径”，而凶星的硬相位、燃烧或缺乏接纳会降低行星的独立交付能力；接纳决定帮助是否有实质、压力是否有边界。其真正可迁移的洞见是“承诺强度”和“交付能力”必须分开审计。
operational_rule: 行星状态层增加 bonification/maltreatment 候选字段，但只在相位的精确度数、应用/分离、sect、接纳、行星尊贵和主题宫主责任链齐备时提升；不能用商业文章的固定orb或评分直接升级；来源批评必须保留。
conditions: 先用R29、R19及其他primary/translation材料核验；燃烧、入光线、cazimi必须使用版本锁定的度数阈值；互容不自动等于完整交付。
counter_test: 若吉星本身失势、逆行、出界或无主题责任，所谓bonification只能保留为弱辅助；若凶星有接纳、整盘有交付链，maltreatment应降为有边界的压力而非“毁坏”；分离相位不能冒充当前正在发生的援助/打击。
output_guardrail: 写“该行星的承诺与交付之间存在扶助/压力差异”，不写“被吉星保护所以必然成功”或“被凶星虐待所以必然失败”；敏感历史词仍受G1/G2/G3门禁。
status: auxiliary
```

### QI-026｜死亡/寿限传统是多层时限技术，不是单一八宫征象

```text
card_id: QI-026
source_id: R01, R29, R33, R34, R35
locator: Ptolemy Tetrabiblos Book III ch. XI-XV and Book IV ch. IX; Dorotheus Book I §§15,25-27, PDF pp.10,18-21; Al-Qabisi ch.5-6 pp.51-66,143-149; Bonatti Treatise 8.2 ch.11
tags: [@sensitive, @timing, @lots, @sect, @aspects, @source_criticism, @anti_overfit]
quote: none
paraphrase: Ptolemy先区分寿限技术与死亡类型，要求选择prorogator、prorogatory places、主宰和anaretic因素，再讨论下降、会合、角宫/续宫、星体性质与时限；Dorotheus、Al-Qabisi和Bonatti又加入父母/死亡之Lot、年限、岁限或方向等变体。共同洞见不是“八宫有凶星=死亡”，而是只有完整的时限链和多重确认才构成历史作者所谓的严重征象。
operational_rule: 死亡/寿限主题只能作为历史技术审计：记录prorogator、主限/时限技术、Lots与Lot公式、sect、度数、角宫状态、相位、凶吉星援助和版本；来源批评与G1/G2/G3门禁必须通过；没有独立时间技术时，本命模块输出N/A，不把死亡写成可预测事件。
conditions: 必须锁定宫制、昼夜、原典/译本、prorogation方法和应用/分离；必须有至少两条独立支持与一个缓解/反证；用户未主动提出时不主动展开。
counter_test: 单一八宫、土星、冥王星、对冲或“死亡Lot”不能升级；若主宰失势但有吉星、救援或现实资料相反，保留竞争解释；缺出生度数或时间技术时直接降级。
output_guardrail: 禁止给出死亡日期、方式、年龄、自杀或他人死亡结论；最多说明“历史传统把该结构视为需要谨慎审计的脆弱/终结主题”，并明确现代证据不足。
status: auxiliary
```

### QI-027｜疾病与“癌症”必须分离：历史身体象征不等于医学诊断

```text
card_id: QI-027
source_id: R01, R34, R35, R36
locator: Ptolemy Tetrabiblos Book III ch.XVII, pp.103-107; Al-Qabisi ch.5 and ch.6 lot of illness/chronic disease, pp.55-66,144-149; Bonatti Treatise 8.2 ch.11; NCI Diagnosis overview
tags: [@medical_history, @sensitive, @source_criticism, @anti_overfit]
quote: none
paraphrase: Ptolemy和后世作者按行星、角宫、身体部位与体液解释“伤病/身体负担”，Al-Qabisi另列疾病与慢性病之Lot；这些是古代医学宇宙观的历史分类，不是现代病理学。现代癌症诊断没有单一测试，通常需要病史、体检、实验室/影像及常常的活检；因此传统文本没有可移植的“癌症星盘征象”。
operational_rule: 疾病层只允许记录传统身体象征、生活负荷、就医延误风险和现实观察；“癌症”不得建立星盘特征库，不得由行星/宫位/相位推断诊断或预后；来源批评与医疗内容必须进入G2/G3门禁并转介专业检查。
conditions: 必须区分历史医疗语境与现代医学；不得把第六宫、土星、冥王星、天蝎或某个Lot当作癌症指标；现实症状和筛查优先于任何占星讨论。
counter_test: 同一历史配置可对应多种身体体验、环境负担或无明显疾病；若没有现实医学资料，任何具体病名都降为N/A；NCI的临床诊断流程是独立反证层。
output_guardrail: 禁止写“你会得癌症/某病”“没有这个相位就没事”“星盘能排除癌症”；只能说“传统文本曾把此类结构与身体压力联系起来”，并建议按症状及时就医。
status: auxiliary
```

### QI-028｜破财/财富坠落需要资源链、主宰和时限共同确认

```text
card_id: QI-028
source_id: R29, R33, R34, R35
locator: Valens Book II §§2.14,2.19-2.20 pp.110,127-129; Dorotheus Book I §§22,24-27, PDF pp.13-21; Al-Qabisi ch.5-6 pp.51-66,143-149; Bonatti Treatise 8.2 ch.11
tags: [@wealth, @lots, @sect, @source_criticism, @anti_overfit]
quote: none
paraphrase: 传统财富判断会同时看2宫/财产位、其主宰、福点及其主宰、11宫获得、10宫交付、8宫继承/共同资源，并区分角宫/续宫/果宫、sect、吉凶星援助、燃烧/逆行和时限。Dorotheus把财富下降写成“承诺与交付分离”的阶段性过程，而不是一次相位自动等于破产。
operational_rule: 财富损失只输出可观察的现金流、债务、共同资金、合同和职业定价风险；必须先完成2/11/10/8责任链、Lots与Lot公式、sect和现实财务证据审计；来源批评未完成时不得升级；没有时限技术不得给出破财年份。
conditions: 锁定宫制、福点公式、sect、宫主尊贵/失势、接纳、相位方向和现实资产负债；投资、税务和法律判断必须独立尽调。
counter_test: 二宫凶星或福点受损不能单独推出破产；若10宫交付、11宫获得或吉星缓解链强，保留“压力但可修复”；现实现金流与文本相反时以现实资料为准。
output_guardrail: 不写“必破财/注定贫穷/一定破产”；写“资源链中存在需要审计的损耗点”，并给出合同、预算、回款和退出条件。
status: auxiliary
```

### QI-029｜“出轨/淫乱”是历史婚姻语境，不能转成事实指控

```text
card_id: QI-029
source_id: R01, R29, R34, R35
locator: Ptolemy Tetrabiblos Book IV ch.V, pp.124-127; Valens Book II sensitive delineations; Al-Qabisi ch.6 marriage lots pp.144-149; Bonatti Treatise 8.2 ch.10, printed p.82 and following
tags: [@sensitive, @reception, @aspects, @source_criticism, @anti_overfit]
quote: none
paraphrase: Ptolemy以婚姻主指标、月亮/太阳、金星、火星、土星、应用与相位和双方命盘比较讨论婚姻稳定/冲突；Bonatti列出男性/女性婚姻、享乐、通奸/放纵等多个Part，并明确存在Hermes、Valens、Abu Ma’shar不同公式。可迁移的核心是契约、边界、欲望与公开关系之间的张力，而不是“某相位=某人已出轨”。
operational_rule: 关系敏感层只输出承诺结构、边界协商、公开/隐私、共同资源和冲突机制；只有用户主动提出且具备现实语境时，才可说明历史文本的关系风险模型，并核对接纳与相位；来源批评未完成时不升级；不建立忠诚/出轨人格标签。
conditions: 必须锁定双方资料、婚姻/关系Lot公式、sect、接纳、相位应用/分离和现实行为证据；单盘不能证明伴侣事实。
counter_test: 同一配置可对应多段关系、开放式契约、欲望表达、名誉压力或纯粹理论变体；没有现实证据时不得选择“出轨”作为唯一解释。
output_guardrail: 禁止指控用户或伴侣出轨、淫乱、性取向或违法性行为；使用“契约边界/信任/诱因/公开性风险”并要求现实沟通与证据。
status: auxiliary
```

### QI-030｜父亲/母亲征象必须分开且多重确认，不能预测父母寿命

```text
card_id: QI-030
source_id: R01, R33, R34, R35
locator: Ptolemy Tetrabiblos Book III ch.V, pp.77-80; Dorotheus Book I §§6,12-16, PDF pp.4,7-10; Al-Qabisi ch.5-6 pp.55-66,143-149; Bonatti Treatise 8.2 Parts of Father/Mother and Death of Parents
tags: [@sensitive, @lots, @sect, @aspects, @source_criticism]
quote: none
paraphrase: Ptolemy以太阳/土星看父亲、月亮/金星看母亲，并检查doryphory、尊贵、角宫/果宫与吉凶星；Dorotheus再按昼夜、三分主宰和父母Lot区分父母的资产、关系、分离与历史上的寿限叙述；Al-Qabisi与Bonatti记录多个父母/父母死亡Lot公式。重要结构是“父母各自的责任链与盘主受到的影响”，不是把一颗星等同于某位家长。
operational_rule: 家庭模块可以讨论父母支持、资产、沟通、距离、照护和边界；父母健康、死亡、寿命、社会身份只能作为历史研究，不得写成现实断言；父母主题必须通过G1/G2/G3，完成昼夜sect、太阳/月亮、宫主、Lots、相位、来源批评和现实观察核对。
conditions: 必须锁定父母指示体系、sect、宫制、Lot公式、相位方向和盘主与父母的实际关系；“父亲/母亲”也可能因文化、照护者或家庭结构发生替代。
counter_test: 同一父母指标可反映盘主的主观体验、家庭资产或照护责任，而非父母本人事件；若现实资料不支持，降为N/A；单一凶星、四宫或十宫不能确认父母病亡。
output_guardrail: 禁止预测父母死亡日期、寿命、癌症或具体疾病；只能讨论“传统模型会检查的家庭压力/资源/照护链”，并建议现实医疗和家庭沟通。
status: auxiliary
```

### QI-031｜Lot公式和传承版本冲突本身就是敏感征象的降级条件

```text
card_id: QI-031
source_id: R33, R34, R35
locator: Dorotheus Book I §§13-15, PDF pp.8-10; Al-Qabisi ch.6 pp.143-149 and critical notes; Bonatti Treatise 8.2 ch.10-14 with Hermes/Valens/Abu Ma’shar variants
tags: [@lots, @source_conflict, @formula_control, @source_criticism, @sensitive]
quote: none
paraphrase: Al-Qabisi的校勘注释和Bonatti的汇编清楚显示：父亲、母亲、死亡、疾病、婚姻、淫行和财富Lot存在不同作者、昼夜公式、投射点和译本差异。敏感主题最容易因公式换位而制造“命中”，所以版本冲突不是脚注，而是降级理由。
operational_rule: 每个敏感Lots必须保存作者、公式、昼夜、投射点、宫制、精确度数和替代分支；来源批评必须可追踪；若两个权威版本给出不同位置，结果只保留为候选，不得进入A/S正文。
conditions: Lot缺度数、出生时间、sect或公式版本时直接N/A；不得把现代软件默认Lot当作古典共识。
counter_test: 对同一星盘运行至少两个合法版本；若结论随公式改变，必须展示冲突并降低等级；若删去Lot后责任链仍成立，Lot不能独立抬升主题。
output_guardrail: 写“不同传承公式产生分支，当前不作确定判断”，不写“这个Lot命中所以禁忌事件确定发生”。
status: auxiliary
```

### QI-032｜禁忌词的现代输出必须经过机制化翻译和现实转介

```text
card_id: QI-032
source_id: R01, R29, R33, R35, R36
locator: Ptolemy Book III-IV; Valens Book II §§2.14-2.20; Dorotheus Book I §§12-27; Bonatti Treatise 8.2 ch.10-14; NCI diagnosis overview
tags: [@sensitive, @medical_history, @source_criticism, @methodology, @anti_overfit]
quote: none
paraphrase: 这些原典保存了死亡、疾病、破产、奴役、通奸、父母死亡等强烈历史词汇，但它们的规则常依赖完整盘、主宰、角宫、sect、Lot、救援星和时限。现代系统必须把它们拆成可观察的机制：身体负荷、资源损耗、契约边界、照护压力、权力/法律风险；医学与现实证据优先，历史术语只作为知识史索引。
operational_rule: 所有敏感主题都执行G1/G2/G3门禁、至少两条独立证据、一个反证和现实专业转介；现代方法边界与来源批评必须可见；“癌症、死亡、出轨、父母病亡”等词不能由星盘自动生成，未主动提出时不主动展开。
conditions: 必须保留原典时代、译本、作者和版本冲突；涉及医疗、法律、投资、安全、性或他人隐私时最小化记录，不把观察变成占星证据。
counter_test: 若机制化翻译仍可无差别套用多数人，标记generic_language_blocked；若没有现实资料、关键度数或时限技术，输出N/A而不是补写禁忌含义。
output_guardrail: 历史研究可以直面文本曾经如何描述，但用户报告只输出中性、可观察、可反驳的结构，并明确占星不能诊断、指控或预测死亡。
status: auxiliary
```

## 待核读文章卡（先登记，读完再升级）

| 卡片 | 来源 | 预定用途 | 当前状态 |
|---|---|---|---|
| QI-101 | R09 Barton, *Ancient Astrology* | 建立希腊—罗马占星的社会与知识史背景 | draft |
| QI-102 | R10 Beck, *A Brief History of Ancient Astrology* | 校对古代术语和时代分界 | draft |
| QI-103 | R11 Lehoux, “Observation and prediction in ancient astrology” | 分析古代观察/预测概念与现代验证的差异 | draft |
| QI-104 | R12 Kassell, “Stars, spirits, signs” | 研究 1100–1800 年语境转换，避免跨时代混用 | draft |
| QI-105 | R13 Fichten & Sunerton, “Popular Horoscopes and the ‘Barnum Effect’” | 强化反泛化与 swap-chart 检验 | draft |
| QI-106 | R14 Tyson, “An empirical test of the astrological theory of personality” | 检查人格占星的经验检验边界 | draft |
| QI-107 | R15 Allum, “What Makes Some People Think Astrology Is Scientific?” | 改进咨询中的证据沟通与信念边界 | draft |
| QI-108 | R37 Firmicus Maternus, *Mathesis* (Holden translation lead) | 交叉核对疾病、父母、婚姻与死亡章节 | draft |

## 调用方式

按主题检索标签即可：

```text
@sect       -> QI-002
@timing     -> QI-003
@sensitive  -> QI-004
@history    -> QI-005
@methodology -> QI-001, QI-006, QI-103–QI-107
@antiscia   -> QI-007
@lots       -> QI-008
@reception  -> QI-009
@aspects    -> QI-010
@terms      -> QI-011
@medical_history -> QI-012
@wealth      -> QI-019, QI-021
@sensitive   -> QI-020, QI-024
@source_criticism -> QI-019–QI-024
@history     -> QI-022
@dignity     -> QI-024
@reception   -> QI-024
@anti_overfit -> QI-018, QI-023–QI-025
```

在最终输出中，洞见卡只能作为“规则来源”和“表达边界”；具体命盘结论仍必须回到 Chart Facts、宫位责任链、行星状态、反证和 S/A/B/C/N/A 评级。
