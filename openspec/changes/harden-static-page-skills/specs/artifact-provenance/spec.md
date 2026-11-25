# Spec Delta

## Purpose

让页面创建与发布之间传递的是一份可复核的完整静态产物，而不是只凭入口 HTML 或口头说明判断检查结果仍然适用。

## ADDED Requirements

### Requirement: Builder SHALL record the complete artifact snapshot
Builder 的本地检查结果 MUST 记录所检查产物根目录下的规范化相对路径、文件大小、SHA-256 和可重复计算的 bundle 摘要。

#### Scenario: Multi-file artifact is checked
- **WHEN** 检查器成功处理包含 HTML、CSS、脚本和图片的产物目录
- **THEN** 输出包含全部普通文件的稳定清单和 bundle 摘要，且输出文件不被计入产物清单

#### Scenario: Artifact changes after checking
- **WHEN** 交接前任一已记录文件被修改、删除或新增
- **THEN** publisher 的产物复核 MUST 失败并指出受影响路径，而不是沿用旧的通过结果

### Requirement: CSS dependencies SHALL be checked transitively
本地页面检查 MUST 在有限递归和循环保护下检查独立 CSS 文件中的本地 `url()` 与 `@import` 依赖。

#### Scenario: CSS references a missing asset
- **WHEN** HTML 引用的 CSS 文件再引用不存在的字体、图片或 CSS 文件
- **THEN** 检查结果 MUST 指出该缺失的间接资源

#### Scenario: CSS import cycle exists
- **WHEN** CSS 文件形成循环导入
- **THEN** 检查 MUST 终止递归并报告可诊断结果，不进入无限循环
