# Spec Delta

## Purpose

让 publisher 能把批准的预览源、待收录正式文件和线上部署内容按明确范围逐项核对，并在多文件失败时保留完整的审计结果。

## ADDED Requirements

### Requirement: Promotion comparison SHALL expose source-to-target drift
正式收录前的比较 MUST 对源产物和正式目标目录按相对路径与字节生成新增、删除、修改和相同文件结果。

#### Scenario: Clean promotion has matching files
- **WHEN** 批准预览源与正式目标包含相同相对路径和字节
- **THEN** 比较结果 MUST 成功，并记录两侧集合摘要

#### Scenario: Promotion changes a resource
- **WHEN** 正式目标遗漏、增加或修改任一 HTML、CSS、脚本、图片或数据文件
- **THEN** 比较结果 MUST 失败并列出路径和差异类别

### Requirement: Formal verification SHALL support the complete manifest
正式部署核验 MUST 支持选择 manifest 中的全部正式文件，同时保留按页面选择的轻量模式。

#### Scenario: Formal entry HTML is valid but a dependency is wrong
- **WHEN** 入口 HTML 哈希正确但其正式 CSS、脚本或图片哈希不匹配或无法下载
- **THEN** 全量核验 MUST 失败并指出该依赖文件

### Requirement: Verification SHALL aggregate independent file failures
线上核验 MUST 将单个文件的下载、内容类型、哈希或本地比较错误写入对应文件记录，并继续核验其他选定文件；manifest 结构错误仍可作为全局失败立即停止。

#### Scenario: Multiple files fail
- **WHEN** 两个或更多目标文件分别返回错误或哈希不匹配
- **THEN** 结果 MUST 保留每个文件的失败原因和整体 `ok=false`，而不是只返回首个错误
