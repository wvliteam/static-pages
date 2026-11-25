---
name: static-page-publisher
description: "接收已有静态 HTML 产物，按统一仓库规则准备预览分支与PR，验证 GitHub Pages 在线预览，在当前版本获确认后归档、合并、部署并清理预览。适用于上传、在线预览、正式发布及部署验收；页面制作与本地布局检查由创建技能处理。"
---

# 静态页面预览与发布

接收已有 HTML 目录，完成在线预览、正式收录和部署核对。按会话授权执行上传或合并；预览不自动等于正式发布许可。复用用户指定统一仓库，不逐页建仓库。

## 输入与交接

确定产物目录、入口 HTML、必要资源、相关数据日期和本地检查记录。记录包含 builder 输出的 `artifact_manifest.bundle_sha256`；已有网页可直接发布，不要求重新创作或刷新其分析数据。若没有该记录，publisher 先用 builder 检查器为现有产物生成，不声称此前执行过 builder。

用户同时要求创建页面时，组合 `static-page-builder`：本技能先按仓库规则准备分支和输出目录，创建器负责生成与本地检查，再接收产物继续预览。如果 builder 不可用，publisher 只可在用户明确要求编辑内容且现有检查足以验证时使用可用工具接手，并标明未执行 builder；否则完成发布准备后说明缺少的创建或检查步骤，不把职责不清的内容修改混入发布。

## 分支预览与正式发布

执行前读取 [references/github-pages.md](references/github-pages.md) 和 [references/site-profile.md](references/site-profile.md)，核对仓库的 AGENTS.md、远端与发布机制。

- `main/docs/` 只保存已确认的正式网页，根首页作为正式导航。
- 在 `preview/<task>` 分支创建 `artifacts/<task>/public/index.html` 及必要资源，创建指向 main 的同仓库 PR。暂存前运行 `scripts/verify_artifact_manifest.py --root artifacts/<task>/public --manifest <builder-check.json>`，确保检查后文件集合和字节未变化；已有页面先生成本地检查 JSON。
- 工作流将这些静态文件发布到 `/previews/pr-<number>/<task>/`，提供直达链接。它们不进入 main、正式导航或正式页数量。
- 预览自动带有预览标记及 noindex。链接是公开的，不能称为私有、鉴权或禁止访问。原始数据、日志和本地工具放在 Git 忽略的 `scratch/`，不要写进 public。
- 用户确认本次具体版本后，才在 PR 分支将最终文件迁到正式 `docs/reports/`、`docs/pages/` 或 `docs/tools/`，移除 tracked artifacts，更新正式导航与 README。迁移后运行 `scripts/compare_promotion.py --repo-root . --preview-sha <approved-preview-sha> --task <task> --manifest <builder-check.json> --target-root <formal-page-directory>`；只有检查摘要与批准 SHA 的产物一致、目标目录无增删改差异才可继续。已有适用于该产出的正式发布授权时不重复询问；预览授权本身不等于正式发布授权。
- `gh-pages` 是工作流生成的部署产物分支，不手动编辑，也不合入 main。不要把预览分支直接部署为整个站点覆盖生产。
- 迁移会产生新的 PR head。重新运行本地检查并推送后，确认 `static-pages-candidate` 和 `static-pages-main-ready` 都针对最新 head / 测试合并提交通过，且 tracked artifacts 已清空，再依仓库保护规则合并。此前预览的通过结果不能代替迁移后提交的检查。

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

正式检查默认只核对指定 HTML。需要完整核对正式站点时使用 `--all-production`（与 `--page` 互斥）；它按 `deployment.json` 的 `production_sha256` 清单核对全部正式文件，并逐文件记录下载、内容类型、哈希和本地比较错误，继续检查其余文件：

```bash
python3 <skill-dir>/scripts/verify_deployment.py --base-url https://<owner>.github.io/<repo>/ --main-sha <approved-main-sha> --all-production --local-root <checkout>/docs
```

预览模式仍按该预览任务 manifest 的全部文件核验，不与正式模式选项混用。

- 预览：PR、Pages 预览链接、已部署 head SHA、完成的检查；不称为正式收录。
- 正式：导航首页、正式直达链接、仓库、对应 main 提交与部署核对结果。
- 本机 localhost 或本地文件不能替代用户要求的在线预览。未取得权限时先完成可审阅的本地成果，准确说明缺失的认证，不虚构公开链接。
