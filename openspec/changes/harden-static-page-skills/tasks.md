# Tasks

## 1. 产物摘要与 builder 检查

- [x] 1.1 扩展 `check_static_html.py`，输出稳定的完整文件清单、bundle SHA-256，并拒绝/报告 CSS 间接资源缺失；用单元测试覆盖新增、缺失、循环导入和输出文件排除。
- [x] 1.2 新增 publisher 产物摘要复核脚本，验证文件集合、字节数和哈希；测试修改、删除、新增文件都会失败。

## 2. 发布比较与线上核验

- [x] 2.1 新增只读 promotion 比较脚本，报告源/目标的相同、修改、新增和删除文件；测试干净迁移和各类漂移。
- [x] 2.2 扩展 `verify_deployment.py` 的 `--all-production` 和逐文件错误聚合；测试入口正确但依赖错误、多文件失败和页面级兼容模式。

## 3. Skills、交接和回归

- [x] 3.1 更新 builder/publisher SKILL.md、references 和 CONTRIBUTING.md，写明摘要交接、迁移比较、迁移后候选检查和正式全量核验命令；通过 skill 合同测试核对关键入口。
- [x] 3.2 运行 `python3 -m unittest discover -s tests -v`、`openspec validate --all --strict --no-interactive` 和所有新增脚本 `--help`，记录结果并更新本任务状态。

## Workflow follow-up

- 实施完成后按仓库审阅要求检查 diff；OpenSpec 归档与线上发布是后续独立步骤。
