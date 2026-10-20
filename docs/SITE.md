# 双语课程网站 / Bilingual course website

静态页面入口：[`index.html`](index.html)。页面包含中英文切换、明暗主题、四册 PDF、课程路线、六个项目、Capstone 和 Notebook 运行命令。语言和手动主题偏好保存在浏览器本地；`?lang=zh` 或 `?lang=en` 可指定打开语言。禁用 JavaScript 时仍可阅读中文页面和使用文档链接。

The static entry is [`index.html`](index.html). It includes Chinese/English switching, light/dark themes, four PDF links, curriculum, six projects, Capstone, and Notebook commands. Language and manual theme preferences are stored locally. Use `?lang=zh` or `?lang=en` to choose a language. Without JavaScript, the Chinese page and document links remain available.

## 阅读入口 / Reading entry

**[打开中文网页版](http://127.0.0.1:8765/read/zh/index.html)** · **[Open the English reader](http://127.0.0.1:8765/read/en/index.html)**

上述链接需要本机已启动预览服务，启动方法见下文。目前尚未部署公网地址；仓库侧边的 Website 链接指向本页，提供预览入口与说明。

These links require the local preview server below. No public reader URL is deployed yet. The repository sidebar links here for preview access and instructions.

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

目前未启用 Pages，仓库保持私有。完整站点应由构建后的 `dist/` 部署，不能仅发布 `/docs`。输出包含正文、四册 PDF 与搜索全文；公开前需完成既有权利核查及发布确认。仅推送构建源码不会自动开放站点。

Pages remains disabled and the repository private. Deploy the built `dist/` for the complete site; `/docs` alone is only the introduction. The output includes prose, four PDFs, and full-text search data. Complete the existing rights review and release confirmation before publication. Pushing build source does not publish the site.

## 设计与校验 / Design and checks

采用纸本学术风格：白天米白、夜晚中性炭黑，少量墨蓝点缀，使用原生 CSS 编辑式布局。页面主题整体切换，支持手机和键盘操作，减少动态偏好下关闭平滑滚动。封面曲面为概念插画，不代表市场实证数据。

The native CSS editorial layout uses paper cream by day, neutral charcoal by night, and restrained ink-blue accents. The full page switches themes together, supports mobile and keyboard use, and disables smooth scrolling for reduced motion. The cover surfaces are conceptual artwork, not market evidence.

页面已检查语言切换、主题、手机显示和复制命令；这不代表重新运行课程或验证研究结果。内部审阅记录不随读者仓库分发。

Language switching, themes, mobile layout, and command copying have been checked. These checks do not rerun the course or validate research results. Internal review logs are not distributed with the reader repository.

## 许可与赞助 / Licensing and support

网站功能代码适用 MIT，原创教学文字与作者有权许可的插画适用 CC BY-SA 4.0，例外见 [许可范围](../LICENSE.md)。收款渠道尚未启用，仅准备 [赞助说明](../.github/SUPPORT.md)与 `.github/FUNDING.yml.example`。Pages 与仓库仍未公开，公开前须处理 [权利核查](legal/RIGHTS_REVIEW.md)。

Functional site code uses MIT; original educational prose and licensable rights in the identified illustrations use CC BY-SA 4.0, subject to the linked exceptions. No payment channels are active.
