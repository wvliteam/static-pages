---
name: static-page-publisher
description: "接收已有静态 HTML 产物，按统一仓库规则准备预览分支与PR，验证 GitHub Pages 在线预览，在当前版本获确认后归档、合并、部署并清理预览。适用于上传、在线预览、正式发布及部署验收；页面制作与本地布局检查由创建技能处理。"
---

# 静态页面预览与发布

接收已有 HTML 目录，完成在线预览、正式收录和部署核对。按会话授权执行上传或合并；预览不自动等于正式发布许可。复用用户指定统一仓库，不逐页建仓库。

## 输入与交接

确定产物目录、入口 HTML、必要资源、相关数据日期和已完成的本地检查。已有网页可直接发布，不要求重新创作或刷新其分析数据。

用户同时要求创建页面时，组合 `static-page-builder`：本技能先按仓库规则准备分支和输出目录，创建器负责生成与本地检查，再接收产物继续预览。创建器不可用时可用现有工具完成内容，但不能声称执行了该技能。

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

## 线上验收

`scripts/verify_deployment.py` 使用标准库，只发 GET，核对站点 deployment.json 的源版本和实际发布文件哈希。它不解析页面布局或重复创建器的 HTML 结构检查。

正式检查示例：

```bash
python3 <skill-dir>/scripts/verify_deployment.py \
  --base-url https://<owner>.github.io/<repo>/ --main-sha <approved-main-sha> \
  --page . --page reports/<symbol>/<date>/ --local-root <checkout>/docs
```

预览检查示例：

```bash
python3 <skill-dir>/scripts/verify_deployment.py \
  --base-url https://<owner>.github.io/<repo>/ \
  --preview-pr <number> --preview-sha <reviewed-head-sha> --task <task>
```

预览含自动注入标记，脚本按部署记录的生成文件哈希核对，不能与干净源 HTML 强求字节相同。正式页可追加本地根目录逐字节核对。HTTP 200 或旧运行成功不足以证明本次上线；源提交和下载内容必须同时匹配。

布局、内容和交互的缺陷交回创建流程修复；实质内容变更后重新部署并指明新的待审阅版本，不静默沿用旧确认。平台基路径或资源搬移造成的问题在发布流程中解决。

## 交付

- 预览：PR、Pages 预览链接、已部署 head SHA、完成的检查；不称为正式收录。
- 正式：导航首页、正式直达链接、仓库、对应 main 提交与部署核对结果。
- 本机 localhost 或本地文件不能替代用户要求的在线预览。未取得权限时先完成可审阅的本地成果，准确说明缺失的认证，不虚构公开链接。
