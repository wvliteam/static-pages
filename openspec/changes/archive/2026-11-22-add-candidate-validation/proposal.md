## Why

现有 Pages 工作流在受信任的 main 上运行测试。审阅者需要看到 PR 实际候选版本的测试结果，也需要区分可用于页面预览的文件和尚不允许进入 main 的草稿。

## What Changes

- 实施 [SP-40/R02 的候选检查试点](../../../../design/static-portal/IMPLEMENTATION_PLAN.md)，分别报告候选验证和合并就绪结果。
- 复用现有 Python 检查器与发布规则，在独立的低权限 PR 工作流运行。
- 保留 Pages 部署流程、正式内容及预览确认规则。本次不启用 required checks，不把 OpenSpec CLI 接入 CI。

## Capabilities

### New Capabilities

- `candidate-validation`：验证候选代码、静态内容及合并树的草稿隔离。

### Modified Capabilities

无。

## Impact

新增 `.github/workflows/validate.yml`、候选检查脚本及测试；在项目指南中记录本地调用和结果含义。回退时可移除独立工作流及检查入口，Pages 不依赖其输出。
