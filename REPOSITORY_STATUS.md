# Private repository snapshot / 私有仓库快照

Author / 作者：Yuxiao Ma

This private repository starts from the accepted local formal bilingual edition of 2026-10-19 (BIL23B5 PDFs; unchanged C3 execution layer). Start reading at [README.md](README.md). It contains 45 chapters, six projects, a Capstone, both languages of the complete body and Loom PDFs, editable course Markdown, bilingual Notebook views, shared code/tests, and the offline companions.

本仓库的首个版本逐字节继承已接受的本地正式双语包842文件。四本PDF、Markdown、代码和Notebook保持原字节；新增的仓库说明、忽略规则及来源清单单独记录。教材路线以完整PDF为准；源Markdown与PDF的既有版本说明及历史证据限度沿用原记录。

## Scope / 范围

This is a lightweight reader and code snapshot, not a backup of the entire editorial workspace. Historical batch archives, private review/job logs, build environments, intermediate renders and the PDF assembly toolchain are not included. Some original documentation links to historical QA evidence remain local-workspace references as already documented by the accepted package. This repository does not claim to regenerate the published PDF layout from Markdown alone.

此仓库保存当前正式教材与离线代码配套，不上传历史备份、审阅截图、运行目录或虚拟环境，也不包含原项目完整PDF构建链。原项目及其历史恢复包继续本地保留。既有文档中指向历史QA的链接不在本快照分发范围，已接受的相应证据限度不变。

## Data and rights / 数据与权利

Only the four small constructed CSV fixtures under `data/fixtures/` are bundled. Other constructed fixtures and teaching figures already present in the accepted edition remain included. French raw/extracted/processed market datasets and derived research series are not uploaded. Historical teaching charts and disclosed summaries are not new market evidence. The G01/G05/PIT gates, Chapter 39 and Project 6 historical gaps, and negative/zero results retain their existing status. No market research or A10-B is executed by this repository setup.

Private visibility is not a publication or data-rights grant. No open-source license or new redistribution permission is selected by this setup. Keep the repository private unless the owner separately authorizes publication and resolves license/data rights.

## Provenance / 来源

- `provenance/FORMAL_MANIFEST.json`: the accepted 842-file source manifest.
- `provenance/ORIGIN.json`: source identity and snapshot scope.
- `provenance/verify_snapshot.py`: verifies the original 842 accepted files without running research or changing artifacts.

```sh
python3 provenance/verify_snapshot.py
```

For later intentional edits, keep the original manifest as a dated baseline; record the change rather than rewriting historical acceptance claims. `runs/`, local environments and optional market data remain ignored.
