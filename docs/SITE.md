# 双语课程网站 / Bilingual course website

静态首页为 [index.html](index.html)，提供中英文切换、主题切换、课程路线、六个项目、Capstone 和 Notebook 运行说明。?lang=zh 与 ?lang=en 可指定打开语言。

The static entry is [index.html](index.html). It provides language and theme switching, curriculum navigation, six projects, the Capstone, and Notebook instructions. Use ?lang=zh or ?lang=en to choose a language.

## 阅读入口 / Reading entry

**[中文网页版](https://quantweft.yuxiao.win/read/zh/)** · **[English reader](https://quantweft.yuxiao.win/read/en/)** · [网站首页](https://quantweft.yuxiao.win)

## 本地构建与预览 / Build and preview

From the repository root:

    npm ci
    npm run build
    npm run check
    npm run preview

在本地打开中文教材、英文教材或首页。完整构建输出位于 dist/；部署时发布整个目录。安装要求与维护细节见 [site/README.md](../site/README.md)。

Open either textbook or the introduction in the local preview. The complete build is written to dist/; deploy the entire directory. See [site/README.md](../site/README.md) for requirements and maintenance details.

如只需预览原介绍页，可运行 python3 -m http.server 8765 --directory docs --bind 127.0.0.1。此模式不包含生成的教材页面。

To preview only the original introduction page, run python3 -m http.server 8765 --directory docs --bind 127.0.0.1. This does not include the generated textbook pages.

## 托管 / Hosting

网站通过 Cloudflare Pages 发布，生产分支为 main，使用 Node.js 24，运行 npm run build && npm run check，并发布 dist/。推送到生产分支会触发部署。GitHub Pages 未启用；GitHub 仓库自 2026-10-21 起公开。

The site is deployed through Cloudflare Pages from main, using Node.js 24, npm run build && npm run check, and the dist/ output. Pushes to the production branch trigger deployment. GitHub Pages is disabled, and the GitHub repository has been public since 2026-10-21.

网站上线不代表第三方材料权利核查已经完成；当前记录见[权利核查](legal/RIGHTS_REVIEW.md)。

Deployment does not complete the third-party materials review. See the current [rights review](legal/RIGHTS_REVIEW.md).

## 许可与支持 / Licensing and support

网站功能代码适用 MIT；作者有权许可的原创教学文字与插画适用 CC BY-NC-SA 4.0，商业使用须另行许可。例外见[许可范围](../LICENSE.md)。可用支持方式见[支持页面](../.github/SUPPORT.md)。

Functional site code uses MIT. Author-controlled original educational prose and illustration rights use CC BY-NC-SA 4.0; commercial use requires separate permission. See the [license](../LICENSE.md) for exceptions and the [support page](../.github/SUPPORT.md) for current support channels.
