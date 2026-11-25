## Why

页面创建和发布技能属于 FlowKit 的可复用能力；static-pages 只负责静态文件托管、在线预览、正式部署与必要校验。当前 CI 导入技能内部路径，无法直接搬迁。

## What Changes

- 将两个业务 skill、参考资料、UI 元数据与技能契约测试迁入 flowkit。
- 在 scripts 保留带内容版本和文件哈希的校验工具快照，解除 CI 的技能目录依赖。
- 保持现有 PR 预览隔离与可信 main 部署；明确已授权金融自动报告的直接正式发布边界。
- 在 flowkit 共享 URL 解析、部署等待和 SHA/哈希验收，金融流水线验收后通知。

## Capabilities

### New Capabilities
- publishing-boundary: 技能与部署仓库分离、固定校验快照与授权模式。

### Modified Capabilities

无；现有 candidate-validation 的输入、失败条件和权限边界保持不变。

## Impact

影响两仓库的 skills、scripts、tests 及入口文档。已有 docs 页面、历史快照、部署工作流权限和 PR 预览规则不变。本次不执行远端推送、PR 合并、安装副本覆盖或实际部署。
