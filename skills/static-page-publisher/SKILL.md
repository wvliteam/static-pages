---
name: static-page-publisher
description: "把分析、报告或小工具分阶段制作成静态 HTML，核对数据与交互，通过 GitHub Pages 提供 PR 分支预览，确认后合入统一站点正式发布。适用于页面创建、更新、归档、预览与部署验收；不用于后端部署。"
---

# 静态页面创建与发布

先交付可在线审阅的预览版本，再按当前任务授权正式收录。所有页面复用用户指定的统一仓库，不逐页建仓库。此技能不授权向任意账号上传或合并；按会话和仓库规则判断授权。

## 创建页面

需要建页时读取 [references/page-creation.md](references/page-creation.md)。按以下阶段落盘，每阶段更新可打开的 HTML，不要求阶段间暂停确认：

1. 页面结构和视觉样式。
2. 已核验内容、数据和图表。
3. 交互、关键数值、布局和键盘检查。

使用实际存在的技术栈；原生静态页默认可用 HTML/CSS/JavaScript。若可用，先读取 `ui-ux-pro-max`，按其流程生成并核对设计系统；结果不适合产品时不要盲目套用。优先自包含 HTML 或同目录静态资源，不为单页引入不必要的框架和远程字体。

沿用已核验的分析与日期，不擅自改变数据后保留旧结论。事实、推断、估值、情景假设和未来条件需清楚区分。图表和交互有文字或键盘替代；浏览器用于验收，不是用户查看网页的安装前置条件。

## 分支预览与正式发布

执行前读取 [references/github-pages.md](references/github-pages.md) 和 [references/site-profile.md](references/site-profile.md)，核对仓库的 AGENTS.md、远端与发布机制。

- `main/docs/` 只保存已确认的正式网页，根首页作为正式导航。
- 在 `preview/<task>` 分支创建 `artifacts/<task>/public/index.html` 及必要资源，创建指向 main 的同仓库 PR。
- 工作流将这些静态文件发布到 `/previews/pr-<number>/<task>/`，提供直达链接。它们不进入 main、正式导航或正式页数量。
- 预览自动带有预览标记及 noindex。链接是公开的，不能称为私有、鉴权或禁止访问。原始数据、日志和本地工具放在 Git 忽略的 `scratch/`，不要写进 public。
- 用户确认本次具体版本后，才在 PR 分支将最终文件迁到正式 `docs/reports/`、`docs/pages/` 或 `docs/tools/`，移除 tracked artifacts，更新正式导航与 README，再合入 main。已有适用于该产出的正式发布授权时不重复询问；预览授权本身不等于正式发布授权。
- `gh-pages` 是工作流生成的部署产物分支，不手动编辑，也不合入 main。不要把预览分支直接部署为整个站点覆盖生产。
- PR 更新自动更新预览；关闭/合并后，下次成功部署自动清理该 PR 的预览。

GitHub Pages 原生并非每分支一个站点：此流程通过可信的 main 工作流组合 main/docs 和全部活动 PR 的静态文件，部署一个完整站点。未配置该机制的仓库不能直接套用预览 URL。

## 验证

`scripts/verify_site.py` 仅依赖标准库，只读检查 HTML、链接、模板占位、资源路径，以及可选线上字节匹配。它不执行 JavaScript，也不替代视觉或数据真实性检查。

从 skill 的实际位置执行，`<checkout>` 与 `<skill-dir>` 为实际路径：

```bash
python3 <skill-dir>/scripts/verify_site.py \
  --root <checkout>/docs --page . --page reports/513310/2026-11-20 \
  --require-single-file --require-homepage-link
```

部署后的正式检查添加站点 `--base-url`。预览含自动注入的标记，需对照公开 `deployment.json` 中对应 PR 的精确 head SHA 与生成 HTML 哈希；不能用原始干净 HTML 的哈希冒充预览哈希，也不能用 HTTP 200 或旧 run 成功证明当前上线。

Chrome/Playwright 可用时检查移动和桌面、键盘与关键操作；不可用时如实报告范围，不将 DOM 模拟说成真实浏览器验收。每次检查只覆盖当前改动所需的行为，失败后依据证据修复。

## 交付

- 预览：PR、Pages 预览链接、已部署 head SHA、完成的检查；不称为正式收录。
- 正式：导航首页、正式直达链接、仓库、对应 main 提交与部署核对结果。
- 本机 localhost 或本地文件不能替代用户要求的在线预览。未取得权限时先完成可审阅的本地成果，准确说明缺失的认证，不虚构公开链接。
