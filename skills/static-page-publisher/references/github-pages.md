# GitHub Pages 分支预览

## 目标与可信边界

先检查仓库 AGENTS.md、分支、远端、未提交改动、GitHub 身份和 Pages 发布类型。此流程使用 GitHub Actions 构建完整站点，而不是给每个分支创建独立 Pages 站点。

可信 main 工作流读取同仓库、分支以 preview/ 开头且 base 为 main 的活动 PR，并按精确 head SHA 下载静态文件。不要执行 PR 的脚本、安装 PR 的依赖或运行其 workflow。尤其不能在 pull_request_target 的写权限下运行 PR 代码。

当前仓库工作流依次：测试发布规则；组合 main/docs 和活动预览；保存到 gh-pages；在同一次 workflow 上传并部署。GITHUB_TOKEN 写 gh-pages 不会自动触发另一条 Pages 工作流，因此不能只依赖一次 push。全部部署互斥，避免覆盖；每次重新组合全部预览，关闭 PR 自动清理。

## 创建预览

1. 保留用户改动，从最新 main 创建 preview/<task> 分支，必要时使用隔离检出；不 force push、不 reset 用户文件。
2. 源数据、检查日志和截图放在忽略的 scratch/。可审阅网页位于 artifacts/<task>/public/，目录内使用相对资源；HTML 本身保存干净版本，预览标记由部署注入。
3. 本地检查页面。只显式暂存该任务所需的 HTML 和静态资源；不改正式首页或正式页数量。推送分支、创建同仓库 PR 指向 main，获取 PR 编号。
4. 等待本次 Pages workflow；从 Actions 摘要或 deployment.json 获取真实预览链接。不要仅凭推测路径声称上线。
5. 核对 deployment.json 的 PR head_sha 等于本次源提交，下载预览 HTML，核对它与部署记录的 SHA-256 一致，检查可见预览标记。正式页面的哈希应仍等于 main/docs 文件。

预览任务缺 index.html 时可显示为尚未就绪，不应破坏正式站点。文件过大、路径越界或符号链接被拒绝时先修复文件，勿绕过验证。

## 审阅后正式收录

先确定用户批准的是哪次预览 SHA。预览后有实质内容改动，需要重新提供对应预览；不能静默合并不同版本。当前会话明确授权正式发布相同产出时，无需重复申请。

在 PR 分支将 artifacts/<task>/public/ 中最终文件迁至 docs 的正式目录，移除该任务的 tracked artifacts，更新 docs/index.html、正式数量及 README 列表。之后检查 diff 与链接再合并。main 不得包含 tracked artifacts，也不得手写 docs/previews；它们是部署时生成的内容。

如果移动后该 PR 不再含 artifacts，预览会在下一次部署消失；这不影响此前精确 SHA 的审阅记录。合入 main 后按正式路径验证内容；PR 关闭会自动移除它的预览，其他活动 PR 必须保留。

## 认证与部署验收

不要打印凭据、读出 token、把 token 写进 URL 或网页。gh 已登录但 HTTPS git 不能获取用户名时，可以为该条命令配置凭据助手：

```bash
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin HEAD
```

提交 Actions workflow 需要账号的相应 workflow 权限。如果当前 OAuth 登录被拒绝，保留已经完成的代码、diff 和验证结果，再说明需要授予哪个 scope，不通过另建仓库或更换身份绕过。

Pages 配置为 workflow 时，默认通过 github-pages 环境限制可信 main 执行部署；无需给所有 PR 放开部署权限，因为部署代码来自 main。

记录本次 main SHA、PR head SHA、运行 URL 和 deployment.json。只有本次运行成功且内容核对通过，才称已部署；HTTP 200 可能是旧版本或错误页。CDN 缓存时可先使用版本查询参数诊断，再核对交付的干净链接。权限错误停止盲目重试；网络问题与正在构建可有界等待，保持进度沟通。

## 公开性与费用

预览网址是公开的，noindex 不提供权限保护。公开仓库文件也可通过 GitHub/Raw 读取。标准 runner 的公开仓库计算用量免费，存储、并发和运行时间仍有额度；短期部署 artifact 应设置适当保留期。费用规则可能变化，询问费用时查官方最新文档，不沿用历史分钟数。

官方参考：

- [发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [deploy-pages](https://github.com/actions/deploy-pages)
- [工作流事件与 pull_request_target](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Actions 计费](https://docs.github.com/en/actions/concepts/billing-and-usage)
