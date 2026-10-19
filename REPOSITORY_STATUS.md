# Private repository snapshot / 私有仓库快照

Author / 作者：Yuxiao Ma

This private repository starts from the accepted local formal bilingual edition of 2026-10-19 (BIL23B5 PDFs; unchanged C3 execution layer). Start reading at [README.md](README.md). It contains 45 chapters, six projects, a Capstone, both languages of the complete body and workbook PDFs, editable course Markdown, bilingual Notebook views, shared code/tests, and the offline companions.

本仓库的首个版本逐字节继承已接受的本地正式双语包842文件。四本PDF、Markdown、代码和Notebook保持原字节；新增的仓库说明、忽略规则及来源清单单独记录。教材路线以完整PDF为准；源Markdown与PDF的既有版本说明及历史证据限度沿用原记录。

## Scope / 范围

This is a lightweight reader and code snapshot, not a backup of the entire editorial workspace. Historical batch archives, private review/job logs, build environments, intermediate renders and the PDF assembly toolchain are not included. Some original documentation links to historical QA evidence remain local-workspace references as already documented by the accepted package. This repository does not claim to regenerate the published PDF layout from Markdown alone.

此仓库保存当前正式教材与离线代码配套，不上传历史备份、审阅截图、运行目录或虚拟环境，也不包含原项目完整PDF构建链。原项目及其历史恢复包继续本地保留。既有文档中指向历史QA的链接不在本快照分发范围，已接受的相应证据限度不变。

## Data and rights / 数据与权利

Only the four small constructed CSV fixtures under `data/fixtures/` are bundled. Other constructed fixtures and teaching figures already present in the accepted edition remain included. French raw/extracted/processed market datasets and derived research series are not uploaded. Historical teaching charts and disclosed summaries are not new market evidence. The G01/G05/PIT gates, Chapter 39 and Project 6 historical gaps, and negative/zero results retain their existing status. No market research or A10-B is executed by this repository setup.

Current licensing: MIT for project-original software and CC BY-SA 4.0 for project-original educational content, subject to LICENSE.md and third-party exceptions. This does not establish rights in market data, copied materials, or embedded third-party components. Keep the repository private until the itemized rights review is resolved; Pages remains disabled.

## Provenance / 来源

- `provenance/FORMAL_MANIFEST.json`: the accepted 842-file source manifest.
- `provenance/ORIGIN.json`: source identity and snapshot scope.
- `provenance/verify_snapshot.py`: verifies the original 842 accepted files without running research or changing artifacts.

```sh
python3 provenance/verify_snapshot.py
```

For later intentional edits, keep the original manifest as a dated baseline; record the change rather than rewriting historical acceptance claims. `runs/`, local environments and optional market data remain ignored.

## 练习册名称与来源修订 / Workbook naming and attribution

2026-10-19：读者入口中的 Loom 改称“练习册 / Workbook”；完整练习册 PDF 迁移至 `editions/zh/workbook/quantweft-workbook-zh.pdf` 与 `editions/en/workbook/quantweft-workbook-en.pdf`，PDF 原字节不变。README、网站与当前学习入口同步更新，练习设计与版式的部分上游借鉴详见 [来源与致谢](ACKNOWLEDGEMENTS.md)。这不是完整采用 Loom 模板，也不改变课程整体的许可范围。

Reader-facing names are now **Workbook**. The two PDFs have descriptive filenames and unchanged bytes. Current navigation and the website use the new paths; [Attribution](ACKNOWLEDGEMENTS.md) explains the selective influence of loom-notes. Technical source paths needed by embedded PDF links, original acceptance records, the original source manifest, and legacy PDF prose remain unchanged.

The original `verify_snapshot.py` checks the initial dated layout and is expected to report intentional changes. To verify the current naming revision, use:

```sh
python3 provenance/verify_workbook_revision.py
```

## QuantWeft 品牌与仓库更名 / Brand and repository rename

当前项目名为 **QuantWeft · 量化经纬**，副标题“量化金融与系统化研究双语课程”。仓库为 `YuxiaoMa66/quantweft`。四册 PDF 采用 `quantweft-textbook-{zh,en}.pdf` 和 `quantweft-workbook-{zh,en}.pdf`，目录深度、PDF 字节及配套实现保持不变。

The current brand is **QuantWeft** with the subtitle **A Bilingual Course in Quantitative Finance and Systematic Research**. Historic acceptance and origin records keep their original project names. PDF contents and internal titles have not been rebuilt for this branding change. The editorial workspace and checkout retain their existing local folder paths to preserve historical references.

Current revision verification: `python3 provenance/verify_brand_revision.py`. Earlier snapshot/workbook verifiers retain their dated scope.

## Licensing and support preparation / 许可与赞助准备

用户于 2026-10-19 授权采用“原创代码 MIT、原创教材 CC BY-SA 4.0、自愿赞助”。详见 [许可范围](LICENSE.md)、[第三方声明](THIRD_PARTY_NOTICES.md)、[贡献规则](CONTRIBUTING.md)与[赞助说明](SUPPORT.md)。尚无收款账户，只有配置示例，未启用 Sponsor 按钮。公开再分发待办见 [RIGHTS_REVIEW.md](RIGHTS_REVIEW.md)；选定许可不代表第三方内容已获许可或仓库已公开。原始来源与接受收据保持历史身份。

The earlier snapshot and naming entries describe dated actions. The current software/content licenses apply to the owner’s licensable original contributions, with no new course, research, or PDF validation. Current verification uses `python3 provenance/verify_current_revision.py`; earlier verifiers retain their dated revision scope.
