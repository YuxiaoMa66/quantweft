# 双语课程网站 / Bilingual course website

静态页面入口：[`index.html`](index.html)。页面包含中英文切换、明暗主题、四册 PDF、课程路线、六个项目、Capstone 和 Notebook 运行命令。语言和手动主题偏好保存在浏览器本地；`?lang=zh` 或 `?lang=en` 可指定打开语言。禁用 JavaScript 时仍可阅读中文页面和使用文档链接。

The static entry is [`index.html`](index.html). It includes Chinese/English switching, light/dark themes, four PDF links, curriculum, six projects, Capstone, and Notebook commands. Language and manual theme preferences are stored locally. Use `?lang=zh` or `?lang=en` to choose a language. Without JavaScript, the Chinese page and document links remain available.

## 本地预览 / Local preview

从仓库根目录运行 / From the repository root:

```sh
python3 -m http.server 8765 --directory docs --bind 127.0.0.1
```

打开 [中文页面](http://127.0.0.1:8765/?lang=zh)或 [English page](http://127.0.0.1:8765/?lang=en)。按 Ctrl-C 停止服务。无构建步骤，无第三方运行依赖。

Open either link above. Stop the server with Ctrl-C. No build step or third-party runtime dependencies are required.

## GitHub Pages

本轮未启用 Pages。仓库仍为私有。启用个人账户下的 GitHub Pages 可能使网页公开访问，即使仓库仍为私有；发布前需单独确认站点受众和账户支持范围。后续使用 Pages 时，发布源为 `main` 分支的 `/docs` 目录，入口无需改动。站内资源采用相对路径，可兼容仓库子路径。

Pages is not enabled by this change; the repository remains private. Pages for a personal account can expose the website publicly even when its source repository is private. Confirm the intended site audience and account support before enabling it. The prepared publishing source is `/docs` on `main`; relative asset paths support a repository subpath.

PDF、Notebook 和学习文档均指向 GitHub 仓库，仍受仓库访问权限约束；网站目录不复制或分发教材及数据。公开介绍页不自动使教材可公开阅读。

PDFs, Notebooks, and learning documents link to the GitHub repository and retain its access requirements. The website directory does not copy or distribute the books or data. A public introduction page does not make the course materials public.

官方说明 / Official documentation: [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site), [Pages access control](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site).

## 设计与校验 / Design and checks

延续已有课程封面与青绿色，使用原生 CSS 编辑式布局。页面主题整体切换，支持手机和键盘操作，减少动态偏好下关闭平滑滚动。封面曲面为概念插画，不代表市场实证数据。

The native CSS editorial layout continues the course cover's teal identity. The full page switches themes together, supports mobile and keyboard use, and disables smooth scrolling for reduced motion. The cover surfaces are conceptual artwork, not market evidence.

本次校验记录见 [`../qa/site_20261019/REPORT.json`](../qa/site_20261019/REPORT.json)。课程运行与教材 PDF 未因网站设计而重新核验。

See the report above for this website's checks. Website checks do not rerun or extend the course's PDF or execution validation.

## 许可与赞助 / Licensing and support

网站功能代码适用 MIT，原创教学文字与作者有权许可的插画适用 CC BY-SA 4.0，例外见 [许可范围](../LICENSE.md)。收款渠道尚未启用，仅准备 [赞助说明](../SUPPORT.md)与 `.github/FUNDING.yml.example`。Pages 与仓库仍未公开，公开前须处理 [权利核查](../RIGHTS_REVIEW.md)。

Functional site code uses MIT; original educational prose and licensable rights in the identified illustrations use CC BY-SA 4.0, subject to the linked exceptions. No payment channels are active.
