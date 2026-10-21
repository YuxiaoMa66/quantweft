# 仓库范围 / Repository scope

QuantWeft · 量化经纬由 Yuxiao Ma 编著，提供 45 章双语正文、练习册、六个项目、Capstone 和共用代码。
QuantWeft by Yuxiao Ma includes 45 bilingual chapters, workbooks, six projects, a Capstone, and shared code.

[开始学习 / Start learning](../../README.md) · [逐章正文 / Chapters](../../course/README.md) · [仓库导航 / Repository guide](../README.md)

## 阅读与运行 / Reading and execution

- 完整教材与练习册位于 `editions/{zh,en}/`；按章 Markdown 位于 `course/{zh,en}/chapters/`。两种语言共用运行库、依赖和运行器。
- PDFs live under `editions/{zh,en}/`; chapter Markdown lives under `course/{zh,en}/chapters/`. Both languages share the execution library, dependencies, and runner.
- Markdown 与 PDF 保留各自的编辑组织，不能据此假定逐段一致；仓库不包含完整 PDF 排版构建链。运行方法见 [Notebook 导读](../../editions/zh/NOTEBOOK_GUIDE.md) / [English guide](../../editions/en/NOTEBOOK_GUIDE.md)。
- Markdown and PDFs retain their respective editorial organization. The repository does not contain the complete PDF layout toolchain; use the linked guides for code execution.

## 数据、结果与许可 / Data, results, and licenses

默认教学路线使用构造输入，French 原始、提取及处理数据不随包。保留的历史图表和摘要不是新市场证据，构造算例通过也不代表真实策略有效。数据使用条件与既有证据缺口见各语言的 [Optional data](../../editions/en/OPTIONAL_DATA.md) 和 [Remaining items](../../editions/en/REMAINING_ITEMS.md)。
The default teaching route uses constructed inputs. French raw, extracted, and processed data are not bundled. Historical charts and summaries are not new market evidence; constructed examples do not establish strategy performance.

原创代码采用 MIT，作者有权许可的原创教学内容采用 CC BY-NC-SA 4.0，仅限非商业使用；商业使用须另行许可。第三方例外见 [许可范围](../../LICENSE.md)。[公开前权利核查](../legal/RIGHTS_REVIEW.md)尚未完成；网页版已通过 Cloudflare Pages 公开，仓库保持私有。已展示微信与支付宝收款码，GitHub Sponsors 仍待审核。
Original code uses MIT; author-controlled original educational content uses CC BY-NC-SA 4.0 for non-commercial use, and commercial use requires separate permission. See the linked scope and exceptions. The website is public through Cloudflare Pages and the repository remains private. Rights-review items remain pending. WeChat Pay and Alipay QR images are displayed; GitHub Sponsors awaits approval.

内部调试、构建、审阅与接受收据保留在维护者的本地编辑工作区，不随读者仓库分发。正文中的历史记录名称仅说明原有证据身份，不表示仓库提供这些内部文件。
Internal debugging, build, review, and acceptance records remain in the maintainer's local editorial workspace. Historical record names in the course identify prior evidence; those internal files are not distributed here.
