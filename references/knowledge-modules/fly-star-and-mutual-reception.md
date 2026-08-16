# 飞星、接纳与互容：本轮提炼模块

## 1. 资料中的可复用骨架

第一份笔记把“宫主星落入另一宫”称为飞星，并强调方向：A 宫宫主落入 B 宫，可先问 A 宫责任如何进入 B 宫语境。它还把穿刺、截夺、双宫主和宫内星列为代理人识别的特殊情况。这个骨架可以转译为本项目已有的 `rulership_fly_ins` 和主题责任链，但不能直接继承笔记里的固定比例或旺衰分数。

第二份表格把 1-1 到 12-12 的宫位对写成经验结论，例如 2-10 被描述为创业/现金流联动，4-10 被描述为家庭/房产与事业联动，7-11 被描述为关系与社群资源的张力。它适合生成假设，不适合直接生成断言。

## 2. 分层后的数据模型

```text
house_flow:
  from_house: A
  to_house: B
  ruler: [planet]
  source: Chart Facts / validated calculation
  direction: A -> B
  status: verified / uncertain

reception:
  planet_a: ...
  planet_b: ...
  dignity_type: domicile / exaltation / triplicity / term / face
  direction: a_received_by_b / b_received_by_a / mutual
  aspect_connection: degree_confirmed / sector_unconfirmed / no_aspect_claim
  applying_status: applying / separating / unknown

house_pair_hypothesis:
  pair: [A, B]
  mechanism: resource / responsibility / risk / identity
  hypothesis: ...
  grade_cap: C
  counter_test: ...
```

## 3. 不可混用的三个概念

| 概念 | 本项目定义 | 本轮资料的处理 |
|---|---|---|
| 宫主飞宫 | 宫主的落宫方向，属于责任链摘要 | 可作为已验证 Chart Facts 的辅助索引 |
| 行星接纳 | 有方向的尊贵关系，并检查相位连接和交付 | 继续沿用 `reception_connection` 闸门 |
| 行星互容 | 双方互在对方尊贵中；仍需声明尊贵类型与版本 | 不因“宫位对互容表”而放宽条件 |

资料中“互容不需要相位”“接纳必然利好”等表述属于该笔记的操作口径，和本项目已注册的严格接纳条件存在冲突，因此只保留为待测试的来源差异，不改变核心算法。

## 4. 经验矩阵的安全转译

不要把下列句子直接输出：

- “2-4 互容 = 富二代/大概率有钱有房”；
- “2-8 互容 = 大财格局”；
- “7-11 互容 = 婚姻一定出问题”；
- “12 宫互容 = 玄学躺赚”。

应转译为：

> 2/8 责任链的联动提出“个人资源与共享资金/风险工具绑定”的假设；需要检查 2、8 宫主的能力、债务与退出条件。现有宫位对笔记只能作为 C 级辅助，不能确认收益、债务或具体事件。

## 5. 完整条目文件

本模块的摘要规则之外，完整经验条目已经拆出保存：

- [fly-star-corpus.md](fly-star-corpus.md)：12 个出发宫位 × 12 个目标宫位，共 144 个有向飞宫条目。
- [mutual-reception-matrix.md](mutual-reception-matrix.md)：1-1 至 12-12，共 78 个无序宫位对互容条目。
- [insight-cards.md](insight-cards.md)：对应的 QI-013–015 洞见卡和调用边界。

## 6. 现实验证契约

每张使用本模块的命盘至少记录三类观察：

1. 责任流：该宫位责任是否真的通过 B 宫的事项被处理；
2. 交付能力：宫主的尊贵、sect、角性、速度、可见性和相位是否支持交付；
3. 代价/反证：债务、控制、合同、家庭责任、隐私或工作负荷是否改变了结果。

没有现实观察或独立来源时，模块保持 `candidate/auxiliary`，不升级。
