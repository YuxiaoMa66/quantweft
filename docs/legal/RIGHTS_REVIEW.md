# Public-release rights review / 公开前权利核查

**Status: pending; repository private; GitHub Pages disabled; payment channels inactive.** The selected MIT and CC BY-SA 4.0 licenses apply only to licensable project-original rights as stated in [LICENSE.md](../../LICENSE.md). This register is not a finding that the items below are infringing; it records evidence still needed for a public release.

**当前状态：核查未闭合，仓库私有，Pages 未启用，收款未启用。** 许可已按根说明选定，但不能据此替第三方授权。下列待办不等于认定侵权，而是公开前仍需证据的项目。

| ID | Item / 核查项 | Evidence and next action / 证据与后续动作 | State / 状态 |
| --- | --- | --- | --- |
| R01 | Author/contributor authority / 作者与贡献者授权范围 | Confirm the rights needed for original content and software, including any material subject to employment, co-author or publisher arrangements. The current instruction authorizes the license choice; a repository scan cannot determine every outside agreement. | Confirmation pending / 待确认 |
| R02 | Source expression and adapted exercises / 来源表达与改编题 | Start with `part02/chapter10/source_notes.md` (MIT OCW and possible material-level NC-SA terms), then review chapter `source_notes.md`, references and inline attributions against the actual source material where wording, figures or exercise structure was reproduced or closely adapted. Record permission, applicable open license, defensible exception, or an original replacement. Merely citing a source is insufficient. | Itemized review pending / 待逐项核查 |
| R03 | Historical data-derived charts/tables / 历史数据衍生图表 | `projects/project02/data_manifest.json`, `projects/project03/data_manifest.json`, `figures/a4/ch17_french_industry_trindex.png`, `figures/a4/ch20_french_estimated_frontiers.png` and `figures/a6/ch31_french_rolling_validation.png` identify French historical inputs/results; PDF and figure summaries may retain derived results. Determine the relevant source terms and permitted distribution for each retained artifact. Do not download data or rerun research for this task. | Evidence pending / 待权利证据 |
| R04 | Image-to-source and font mapping / 图片与字体来源映射 | Match the tracked figures to original plotting source or external provenance (including the Apple-filing chart `figures/a3/ch12_apple_cashflow.png`). PDF font inventory identifies embedded subsets of Computer Modern, Latin Modern, Fandol, Libertinus, DejaVu and TeX Gyre; verify exact versions, notices and embedding/distribution terms. No inference of permission from a PNG filename or successful PDF compilation. | Mapping pending / 待映射 |
| R05 | Loom source and license / Loom 来源与许可 | Pinned upstream author, selective-use credit and full upstream LICENSE are retained. Broader source-expression review remains R02; this item does not clear unrelated course content. | Notice prepared / 声明已备齐 |
| R06 | AI illustration provenance / AI 插画来源 | Three website images are identified in THIRD_PARTY_NOTICES.md. Retain generation provenance and assess any actual third-party rights concern; do not claim exclusive copyright merely because an image was generated. | Provenance identified / 来源已标识 |
| R07 | Release payload, history and private information / 发布载荷与历史信息 | The pre-change tracked inventory covers 870 files. Credential-pattern checks found no matching candidates in the selected text formats; this is not a history-wide or binary-content guarantee. Review the intended public tree and Git history, remove any content that cannot be distributed, and keep restricted data excluded. | Public release check pending / 待发布核验 |
| R09 | Synthetic text corpus / 构造文本语料 | `fixtures/late/ch43/constructed_documents.csv` uses `CONSTRUCTED_TEACHING_CORPUS_OPEN_ACADEMIC_USE` as a historical identifier, not a license. Confirm original authorship and any upstream inputs; apply the current content terms only to rights the author can grant. Do not silently relabel or rerun accepted examples. | Source/authority pending / 待来源与授权确认 |
| R08 | Real payment profiles / 真实收款页面 | The owner has no Sponsors/Ko-fi page yet. Only `.github/FUNDING.yml.example` is present. Complete platform onboarding outside the repository, then verify public profile ownership before enabling funding or payment links. | Not configured / 未配置 |

## What has been checked / 已检查内容

The initial tracked-file inventory classified 870 files, including 115 Python files, 162 Notebooks, 205 PNGs, four PDFs, and nine CSVs. Categories and source markers are triage signals, not proof of authorship. The four small constructed fixtures remain separate from unbundled market data. The license work does not execute the course, train models, rebuild PDFs, change research claims, or establish data rights.

初步清点覆盖现有 870 个受跟踪文件，包括 115 个 Python 文件、162 个 Notebook、205 张 PNG、4 册 PDF 和 9 个 CSV。分类、关键词和无命中均不能代替著作权判断。四个构造 fixture 与未分发市场数据继续区分；本轮不运行课程、不训练、不重编 PDF、不提升研究结论，也不授予数据权利。

## Closing an item / 如何闭合

For each affected file or source group, record its path and SHA-256, rights holder, original source URL/revision, applicable license or permission evidence, permitted reuse, required attribution, and the disposition. If replacing an item, retain a private before/after record and check all affected links and PDF pages. Public release should follow the resolved payload and final owner approval, rather than treating an automated scan as legal clearance.

每项记录路径与哈希、权利人、来源、许可或授权依据、允许用途、署名要求和处置结果。需要替换时保留私有备份，检查相关链接与 PDF 页面。公开应基于核清后的实际载荷和最终发布确认，而不是仅凭自动扫描。

The implementation and independent review receipts are in `qa/open_license_20261019/`; detailed local triage evidence is retained in the editorial workspace. This public-facing checklist does not expose credentials, identity documents, banking records, or private permissions correspondence.

许可实施与独立审阅记录位于 `qa/open_license_20261019/`，详细清点保留在编辑工作区。本文件不收录认证信息、身份证件、银行卡资料或私有授权往来。

The bounded independent inventory identified concrete review targets above and did not establish legal clearance. The 870-file figure is the pre-change GitHub checkout, not the full editorial workspace. / 独立初筛已提供上述具体对象，但未完成法律权利核清；870 文件指改动前 GitHub 副本，不是整个编辑工作区。
