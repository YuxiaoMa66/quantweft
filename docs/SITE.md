# 双语课程网站 / Bilingual course website

静态页面入口：[`index.html`](index.html)。页面包含中英文切换、明暗主题、四册 PDF、课程路线、六个项目、Capstone 和 Notebook 运行命令。语言和手动主题偏好保存在浏览器本地；`?lang=zh` 或 `?lang=en` 可指定打开语言。禁用 JavaScript 时仍可阅读中文页面和使用文档链接。

The static entry is [`index.html`](index.html). It includes Chinese/English switching, light/dark themes, four PDF links, curriculum, six projects, Capstone, and Notebook commands. Language and manual theme preferences are stored locally. Use `?lang=zh` or `?lang=en` to choose a language. Without JavaScript, the Chinese page and document links remain available.

## 阅读入口 / Reading entry

**[打开中文网页版](https://quantweft.yuxiao.win/read/zh/)** · **[Open the English reader](https://quantweft.yuxiao.win/read/en/)**

正式首页：[https://quantweft.yuxiao.win](https://quantweft.yuxiao.win)。网站由 Cloudflare Pages 托管；本地预览方法见下文。

The website is hosted on Cloudflare Pages. These public reading links do not require a local preview server; local preview instructions follow below.

## 完整在线教材 / Complete online reader

推荐从仓库根目录构建并预览完整网站：

Build and preview the complete site from the repository root:

```sh
npm ci
npm run build
npm run check
npm run preview
```

打开 [中文教材](http://127.0.0.1:8765/read/zh/index.html)、[English textbook](http://127.0.0.1:8765/read/en/index.html) 或 [介绍首页](http://127.0.0.1:8765/)。安装要求、内容来源和构建说明见 [site/README.md](../site/README.md)。完整输出位于不提交的 `dist/`，发布时使用整个目录；使用相对路径，支持仓库子路径。

Open either textbook or the introduction above. Requirements and maintenance instructions are in the build guide. The complete output is ignored `dist/`; publish that entire directory. Relative URLs support a repository subpath.

只预览原介绍页时，也可运行 `python3 -m http.server 8765 --directory docs --bind 127.0.0.1`；此模式不包含生成的教材页面，学习链接指向 GitHub。

To preview only the original introduction, serve `docs/` with the Python command above. That mode uses GitHub learning links and does not include generated textbook pages.

## 托管状态 / Hosting status

2026-10-20 已由维护者确认发布网页版，托管于 Cloudflare Pages；GitHub 仓库仍为私有，GitHub Pages 未启用。生产分支 `main`，Node.js 24，构建命令 `npm run build && npm run check`，输出目录 `dist`。后续推送会自动构建发布。网站包含正文、图片与搜索全文；四册 PDF 下载跳转 GitHub，仍需仓库访问权限。

The maintainer confirmed publication of the web edition on 2026-10-20 through Cloudflare Pages. The GitHub repository remains private; GitHub Pages is disabled. Production uses `main`, Node.js 24, build command `npm run build && npm run check`, and output directory `dist`. Pushes trigger automatic deployments. Prose, images and full-text search are public; PDF downloads link to GitHub and still require repository access.

网站上线不等于第三方材料权利核查已经完成；[既有核查项](legal/RIGHTS_REVIEW.md)继续保留原状态。

Website deployment does not close the existing third-party rights review; its recorded items remain pending.

## 设计与校验 / Design and checks

采用纸本学术风格：白天米白、夜晚中性炭黑，少量墨蓝点缀，使用原生 CSS 编辑式布局。页面主题整体切换，支持手机和键盘操作，减少动态偏好下关闭平滑滚动。封面曲面为概念插画，不代表市场实证数据。

The native CSS editorial layout uses paper cream by day, neutral charcoal by night, and restrained ink-blue accents. The full page switches themes together, supports mobile and keyboard use, and disables smooth scrolling for reduced motion. The cover surfaces are conceptual artwork, not market evidence.

页面已检查语言切换、主题、手机显示和复制命令；这不代表重新运行课程或验证研究结果。内部审阅记录不随读者仓库分发。

Language switching, themes, mobile layout, and command copying have been checked. These checks do not rerun the course or validate research results. Internal review logs are not distributed with the reader repository.

## 访问统计 / Traffic analytics

2026-10-20 在 Cloudflare Pages 启用 Web Analytics，由随后部署自动接入，网站不重复嵌入统计脚本。维护者从 Cloudflare 的 QuantWeft 项目 → Metrics → View Web Analytics 查看；分析正式站点时按主机名 `quantweft.yuxiao.win` 筛选，避免混入 `pages.dev` 预览访问。

页面浏览量表示页面加载，不等于独立人数、按钮点击或成功下载；初期也可能包含维护与验证访问。统计从接入生效后积累，不补造历史访问。前端拦截或未发送统计信标可能造成漏计。

先在后台观察访问趋势、来源、设备与热门章节。有真实数据后，再评估公开累计浏览量、最近 30 天每日浏览量和热门章节；累计值应注明起始日期，跨越平台保留期时须使用实际留存的日汇总。当前不公开访客明细，也不展示模拟访问数字。

Cloudflare Pages Web Analytics was enabled on 2026-10-20 and is injected automatically on subsequent deployments; the source does not embed a duplicate beacon. Open QuantWeft → Metrics → View Web Analytics in Cloudflare and filter by hostname `quantweft.yuxiao.win` to separate production traffic from `pages.dev` previews.

Page views count page loads, not distinct people, button clicks, or completed downloads. Early traffic may include maintenance and verification. Counts accumulate after activation; historical traffic is not fabricated. Blocked or missing beacons can cause undercounting. Start with the private dashboard. A later public summary may show cumulative views from a stated start date, daily views over the last 30 days, and popular chapters, using actual retained daily aggregates when platform retention is exceeded. No visitor-level data or simulated counts are published.

## 许可与赞助 / Licensing and support

网站功能代码适用 MIT，原创教学文字与作者有权许可的插画适用 CC BY-SA 4.0，例外见 [许可范围](../LICENSE.md)。已展示作者提供的微信和支付宝收款码，详见 [支持方式](../.github/SUPPORT.md)；GitHub Sponsors 等待审核，尚未启用 `.github/FUNDING.yml`。网页版已公开，仓库保持私有；既有 [权利核查](legal/RIGHTS_REVIEW.md)仍待完成。

Functional site code uses MIT; original educational prose and licensable rights in the identified illustrations use CC BY-SA 4.0, subject to the linked exceptions. Maintainer-supplied WeChat Pay and Alipay QR images are displayed; payment acceptance has not been tested. GitHub Sponsors awaits approval, and no live `FUNDING.yml` is enabled.
