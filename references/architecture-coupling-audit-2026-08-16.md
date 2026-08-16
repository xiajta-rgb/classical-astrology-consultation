# 架构耦合审查记录（2026-08-16）

## 结论

当前系统没有发现会阻断本命计算或知识路由的循环依赖。主要耦合点集中在“注册表重复声明”和“核心引擎导入辅助大模块”，已完成收敛。

### 0. 语义覆盖与输出层解耦

完整占星语义不直接塞进文案生成器。`references/signification-ontology.yaml` 只维护受控的关键词、事件动词和关系操作符；`scripts/expand_signification_map.py` 将 Chart Facts 展开为内部 coverage map；组合与渲染层再按责任链、证据等级、反证和时限压缩输出。这样既能审计是否遗漏征象，又避免把“穷举”误写成无差别的关键词清单。

## 已修正

### 1. 知识符号的单一权威

以前 `plugins.json`、`knowledge_symbols.yaml` 和 `module_dispatch.yaml` 同时保存符号、别名、触发条件和回退路径，存在配置漂移风险。

现在：

- `references/knowledge-modules/plugins.json` 唯一负责插件的调用契约；
- `config/knowledge_symbols.yaml` 只负责 `@符号 → plugin_id` 的稳定索引；
- `config/module_dispatch.yaml` 只负责本命扩展的执行顺序；
- `check_architecture_coupling.py` 检查三者是否漂移。

### 2. 核心引擎与辅助画像解耦

`astrology_engine/__init__.py` 以前在导入基础星盘计算时立即加载 MBTI 和职业画像模块。现在保留兼容 API，但改为函数内部惰性导入；本命、推运和校时不会因为辅助画像而加载大型规则集。

### 3. 冥王模块归位

冥王相位不再作为孤立专题加载，而是登记在 `natal_core_extensions`：本命 Chart Facts 阶段登记位置、宫位和相位，主题命中后才展开事件化解释。

## 保留的有意耦合

| 位置 | 判断 | 原因 |
|---|---|---|
| `module_dispatch.yaml` + `interpretation_routes.yaml` | 保留 | 前者管执行顺序，后者管主题别名；两者职责不同，并由检查器验证指针一致 |
| `run_natal_pipeline.py` | 保留为编排器 | 只负责调用顺序和结果封装，当前约 253 行，低于 320 行预算，不承载具体占星规则 |
| `check_release_gates.py` | 保留为质量编排器 | 文件较大，但只属于发布检查层，不被本命计算引擎反向依赖 |
| `mbti_modules/`、`tpes.py` | 保留独立辅助层 | 规则量较大，但现在只通过显式辅助调用加载，不进入本命核心计算链 |

## 机器门禁

新增 `scripts/check_architecture_coupling.py`，检查：

- 注册表是否只有一个权威来源；
- 符号索引是否与插件清单一致；
- `astrology_engine` 是否反向依赖 `scripts`；
- 核心门面是否重新引入大型辅助模块；
- 运行时编排器是否超过规模预算；
- 旧的重复插件路由是否重新出现。

完整质量门禁结果：`PASSED`。
