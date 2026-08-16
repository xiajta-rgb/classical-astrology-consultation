# 本地资料知识模块

本目录保存从用户提供的本地资料中提炼、审计并可回滚的知识模块。它不是“规则越多越好”的资料堆，而是把来源、适用条件、竞争假设、反证和输出边界一起保存。

## 本轮输入

- `看盘手册(综合最终）.docx`：综合笔记，包含初阶映射、飞星、互容/接纳、推运、主题案例和现代占星材料。
- `1互容特征汇总表.docx`：宫位—宫位互容的经验汇总表。

两份资料均为用户提供的二手/个人整理材料，不能替代古典原典或现代实证。它们的规则默认处于 `auxiliary/candidate` 层，不直接提高 S/A 结论等级。

## 模块索引

| 模块 | 作用 | 默认状态 | 主要限制 |
|---|---|---|---|
| `house-ruler-flow` | 将“宫主落入何宫”作为主题责任链的方向性摘要 | candidate | 只有在宫主、宫制、度数和飞入关系已验证时才可用；不能用笔记中的旺衰分数替代行星状态审计 |
| `mutual-reception-matrix` | 保存宫位对互容的经验假设，并与严格的行星接纳/互容分开 | auxiliary | 不得把宫位对经验表称为古典互容；不得跳过尊贵类型、方向和相位连接 |
| `pluto-aspect-synthesis` | 本命核心中的冥王位置、宫位和相位事件化扩展 | active / natal-core extension | 现代外行星证据上限 C；不得覆盖古典责任链 |
| `mars-personal-aspect-synthesis` | 火星与太阳、月亮、水星、金星相位的本命事件化扩展 | active / natal-core extension | 网络相位解释仅作支持性假设，必须叠加火星状态、宫位责任和时限 |
| `timing-boundary` | 将资料中的法达、返照、次限、太阳弧等整理为后续插件清单 | inactive | 本命资料不足以启动时限或输出具体日期 |

完整条目见 [fly-star-corpus.md](fly-star-corpus.md)（144 个有向飞宫条目）与 [mutual-reception-matrix.md](mutual-reception-matrix.md)（78 个宫位对条目）；洞见卡见 [insight-cards.md](insight-cards.md)。两份 Word 只保留筛选后的核心知识，机器规范源是 `core/cards.jsonl`。

## 调用协议

### 符号路由

每个需要被模型快速调用的扩展模块必须在插件 manifest 的 `invocation` 字段声明唯一符号、别名、触发条件和回退规则；[config/knowledge_symbols.yaml](../../config/knowledge_symbols.yaml) 只保存符号到插件 ID 的稳定索引，不重复维护调用契约。

通用符号表当前包含：

```text
@NAT = natal-core
@MSC = multi-significator-composition
@ADL = advanced-delineation-logic
@CNM = core-natal-method
@HFR = house-ruler-flow
@MRX = mutual-reception-matrix
@PLO = pluto-aspect-synthesis
@MAR = mars-personal-aspect-synthesis
@TOP = interpretation-topic-adapters
@TIM = timing-boundary (inactive/deferred)
```

命令行等价调用：

```text
python scripts/query_knowledge_plugins.py --symbol @PLO
python scripts/query_knowledge_plugins.py --symbol @MAR
python scripts/query_knowledge_plugins.py --symbol @HFR
python scripts/query_knowledge_plugins.py --symbol @MRX
```

本命核心路由会在 Chart Facts 阶段登记冥王的位置、宫位和相位；之后再按符号 trigger 决定是否进入事件化解释，不靠文件名猜测模块。以 `@PLO` 为例，系统检查冥王是否与个人星体/角点相位、是否主宰或落入问题宫位、或用户是否出现注册别名。条件不满足时保留事实但不展开解释，避免冥王资料污染文案；宫制或相位版本冲突时返回 deferred candidate，不强行解释。

以后新增知识模块必须同时具备：`plugin_id`、稳定版本、唯一 `@` 符号、别名、主题标签、触发条件、输入输出契约、证据上限、反证和回退路径。只有文件没有路由符号的模块，不算可调用模块。

1. 先执行 `NATAL-1.0` 的 Chart Facts、宫位责任链和行星状态审计。
2. 再调用本目录模块；模块输出只能作为 `supporting/deferred` 证据，除非经过独立来源和合成命盘回归测试。
3. 每条输出必须写明：资料来源、提炼规则、适用条件、竞争解释、反证和可观察验证。
4. 涉及疾病、精神健康、性、犯罪、死亡或确定性事件的原文，保留为历史/来源审计，不转写为用户诊断或预言。

## 插件层

`plugins.json` 是唯一可调用插件清单，`plugin-contract.json` 是统一契约，`core/retrieval-index.json` 是快速检索索引。`registry.json` 只记录附件蒸馏、来源和排除项，不参与运行时激活；不得把两个 registry 当成两套知识路由。插件分为核心层和扩展层：核心 `natal-core` 必须先运行；附件蒸馏内容只能以显式主题插件加载，不能覆盖核心判断。

多重征象不通过无限增加条目解决，而由 `multi-significator-composition` 按 [composition-framework.md](../composition-framework.md) 把责任链、载体、条件、连接和激活组合为现实机制。

可用检查与查询：

- `python scripts/build_knowledge_index.py`
- `python scripts/check_plugin_architecture.py`
- `python scripts/query_knowledge_plugins.py --topic house_flow --limit 10`

时间相关插件保持 inactive，除非调用方明确激活时间问题和必要数据。
