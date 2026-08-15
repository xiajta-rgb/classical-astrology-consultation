# P0 研究资产元数据审计（2026-08-14）

## 审计范围

本轮只核对 DOI、题名、作者、期刊/年份和可公开取得的摘要元数据；没有把期刊元数据当作全文结果，也没有据此升级任何占星规则。

## R13 / QI-105

- 作品：Catherine S. Fichten & Betty Sunerton, “Popular Horoscopes and the ‘Barnum Effect’”。
- 期刊/年份：The Journal of Psychology，1983。
- DOI：[10.1080/00223980.1983.9915405](https://doi.org/10.1080/00223980.1983.9915405)。
- 元数据状态：题名、作者、期刊和 DOI 已由 Crossref 元数据核对；当前接口未提供摘要。
- 当前可用范围：只能作为“需要反泛化、避免巴纳姆式套话”的研究入口；不能写成该研究已经证明某一具体占星技术无效。
- 仍需：全文/出版社页面、样本、实验设计、量表、统计结果、作者限制与可复现实验定位。
- 状态：`draft / registered`。
- 可得性复核：DOI 元数据可定位；Crossref 返回题录但无摘要；开放馆藏索引未返回可用全文，当前未取得开放全文。

## R14 / QI-106

- 作品：G. A. Tyson, “An empirical test of the astrological theory of personality”。
- 期刊/年份：Personality and Individual Differences，1984。
- DOI：[10.1016/0191-8869(84)90059-X](https://doi.org/10.1016/0191-8869(84)90059-X)。
- 元数据状态：题名、作者、期刊和 DOI 已由 Crossref 元数据核对；当前接口未提供摘要。
- 当前可用范围：只能确认其研究主题属于“人格占星经验检验”；不能从题名推断结果方向，更不能推广为对所有本命技术的总否定。
- 仍需：全文、研究对象、占星变量定义、人格测量、统计结果、阴性/阳性结果和局限。
- 状态：`draft / registered`。
- 可得性复核：Elsevier API 仅返回 coredata，标记 `openaccessArticle=false`；OpenAlex 标记 closed、无 repository fulltext；当前没有摘要/全文内容，不能从标题或题录推断结果。

## R15 / QI-107

- 作品：Nick Allum, “What Makes Some People Think Astrology Is Scientific?”
- 期刊/年份：Science Communication，2010 online / 2011卷期。
- DOI：[10.1177/1075547010389819](https://doi.org/10.1177/1075547010389819)。
- 可复核摘要要点：文章使用欧洲调查，检验三类解释——科学素养不足、对占星实际含义的混淆，以及权威主义价值观与相信占星主张之间的关系；摘要称三项假设均得到支持。
- 当前可用范围：可支持“咨询输出必须区分科学证据、信念形成和占星解释框架”的方法学护栏；不能把它当作占星有效性检验，也不能从调查摘要推断个体盘主的心理特征。
- 仍需：全文定位、样本/变量/模型、效应大小、替代解释和适用人群边界。
- 状态：`draft / registered`。
- 可得性复核：Crossref 返回摘要，但摘要不是全文；开放全文未取得，样本、变量和效应量仍未核读。

## 结论

本轮只提升了来源元数据可追溯性和输出护栏，没有任何 P0 卡升级为 verified，也没有改变核心规则资格计数。
