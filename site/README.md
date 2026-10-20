# 在线教材构建 / Online reader build

将现有 Markdown 在构建时转换为静态 HTML，保留 QuantWeft 介绍首页。网页包含中英文各 45 章、项目与 Capstone、同章语言切换、全文搜索、本章目录、公式和代码高亮。搜索按当前语言匹配关键词；多词查询取交集。

The build turns the repository Markdown into static HTML and retains the QuantWeft introduction page. It includes 45 chapters per language, projects, Capstone, same-chapter language switching, full-text search, section navigation, equations, and highlighted code. Search matches keywords in the current language; multiple words must all match.

## 构建与预览 / Build and preview

需要 Node.js 22.16+ 或 24+、npm，以及用于预览的 Python 3。在仓库根目录运行：

Use Node.js 22.16+ or 24+, npm, and Python 3 for the preview. From the repository root:

```sh
npm ci
npm run build
npm run check
npm run preview
```

打开 [中文概览](http://127.0.0.1:8765/read/zh/index.html)、[English overview](http://127.0.0.1:8765/read/en/index.html) 或 [介绍首页](http://127.0.0.1:8765/)。Ctrl-C 停止预览。需通过 HTTP 打开，全文搜索不能在 `file://` 下读取索引。

Open an overview or the introduction above. Stop with Ctrl-C. Use HTTP: search cannot fetch its index from `file://`.

## 内容与输出 / Content and output

- 编辑 `course/{zh,en}/chapters/chNN/content.md` 与既有项目、资源文档；重新构建后更新网页。构建器读取 Git 跟踪的 Markdown，新文档先 `git add`。不要直接编辑生成文件。
- `docs/` 保留无需构建的介绍页；`site/` 存放阅读器构建与界面。`dist/` 是完整网站输出，`node_modules/` 是本地依赖，两者均不提交。
- 网页完整渲染仓库 Markdown；PDF 另行排版，内容组织可能不同。构建不会修改 Markdown、PDF 或 Notebook，也不会运行课程代码。
- 图片与公式字体复制到输出，四册 PDF、代码及 Notebook 下载链接指向 GitHub。仓库私有时，PDF 仅限有仓库访问权限的用户下载。搜索索引按需加载；无 JavaScript 时仍可阅读正文和公式。
- 网页忽略独立的 PDF 分页、留白指令（如 `\clearpage`、`\needspace`），包括 `{=latex}` 围栏里的纯排版块；正文源文件、公式和教学代码保留。
- 第 8 章的 TikZ 教学图由 `regression.svg` 在网页中呈现；原文和数据点不变。排版用 `qink` 颜色标记只在网页构建时去除。
- 定义、条件、例题与易错点的 `:::` 标记渲染为教学提示框，支持框内公式和列表。Mermaid 图表按需加载本站模块，支持明暗主题、放大和源文查看；禁用 JavaScript 或加载失败时保留完整图表源文。网页将横向生命周期图改为纵向排列，原 Markdown 不变。
- `npm run check` 检查提示框与图表数量是否对应源文，并检查生成页面、站内目标与锚点、45 组同章语言链接和公式解析；不替代课程结果验证。

Edit the existing chapter, project, and resource Markdown, then rebuild. New documents must be tracked with `git add`. The complete website is generated into ignored `dist/`; dependencies stay in ignored `node_modules/`. Source Markdown and PDFs remain unchanged. The web and PDF editions may organize content differently. The build copies images and math fonts; PDFs, code, and Notebook downloads link to GitHub. PDF access requires repository permission while the repository is private. Search loads on demand; prose and math remain readable without JavaScript. Pandoc-style teaching boxes render with their titles, lists, and math. Mermaid diagrams load self-hosted modules only on diagram pages, support themes and enlargement, and retain their source without JavaScript or on load failure. Left-to-right lifecycles are stacked vertically for readable labels; source Markdown is preserved. The checker also compares box and diagram counts with the source corpus. Standalone print-only pagination and spacing commands are omitted from the web edition, including layout-only `{=latex}` blocks; source files, equations, and teaching code are preserved. Chapter 8's TikZ teaching plot uses the equivalent `regression.svg`; the print-only `qink` marker is removed only during conversion. The checker validates local targets, anchors, paired chapter routes, and math parsing; it does not validate course results.

## 发布 / Hosting

部署时发布整个 `dist/`，支持域名根路径或仓库子路径。构建依赖在本地运行，浏览器不加载远程公式脚本或 CDN 字体。正式托管应启用压缩与静态资源缓存。

Publish the entire `dist/`, at a domain root or repository subpath. Prose and math render during the build; diagrams render in the browser from self-hosted modules; browsers do not need remote math scripts or CDN fonts. Enable compression and static-asset caching on the production host.

目前未启用公开托管。`dist/` 包含教材正文与搜索全文，不含 PDF，发布前完成既有[权利核查](../docs/legal/RIGHTS_REVIEW.md)。依赖许可见[第三方声明](../docs/legal/THIRD_PARTY_NOTICES.md)。内部调试与审阅记录保留在仓库之外。

Public hosting remains disabled. The output contains course prose and full search text, with PDFs hosted on GitHub; complete the existing rights review before publishing. See the dependency notices above. Internal debugging and review records stay outside the repository.
