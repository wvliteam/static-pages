## Context

static-pages 的候选校验与测试从 skills 下导入 HtmlChecker 和 relative_path。flowkit 原金融发布器直接推送 main 后即通知，且流水线另行拼接站点 URL。

## Goals / Non-Goals

目标：FlowKit 管理通用技能和业务适配，static-pages 可独立测试部署。技能保持离线可用；预览确认仍绑定具体 SHA；金融自动直发限于已有持续授权的工作流。

不处理：页面重设计、删除历史内容、改变 GitHub 权限或分支保护、执行线上发布。

## Decisions

1. 校验源码由 flowkit skills 维护；static-pages/scripts 保存四个标准库脚本快照和 flowkit-checks.json。版本由来源路径和内容哈希计算。同步显式执行，CI 只验证本仓库固定副本。
2. 站点继续拥有 main/docs、artifacts、预览注入、站点组装、生成分支与部署工作流。技能和业务说明迁入 flowkit；本仓库开发用 OpenSpec 集成保留。
3. 报告适配器保留金融元数据与导航卡片，复用通用发布模块管理 Git 事务、URL、结构化结果、部署等待与验收。普通页面继续先预览后发布。
4. 发布结果区分 dry-run、committed、deployed；只有本次成功 workflow、精确 main SHA 与线上/本地内容一致时返回 deployed。流水线只消费该结果，不自行生成 URL；失败时不通知。

## Risks / Trade-offs

快照存在两份文件，使用内容寻址清单、独立行为测试和显式同步检查控制漂移。flowkit 的新代码需先在本地验收，再同步站点快照。GitHub CLI 认证/网络失败会阻断通知，不会误报已上线。

## Migration Plan

先解除 CI 的路径依赖，再迁技能和测试，更新发布结果契约与文档。两个仓库分别提交审阅；static-pages 的独立脚本可先落地，flowkit 不依赖站点删目录才能运行。回退时对各自迁移提交做定向 revert，不改 docs 或共享历史。
