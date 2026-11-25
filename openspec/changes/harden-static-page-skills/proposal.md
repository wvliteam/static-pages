# Proposal

## Why

Builder 与 publisher 已能分别检查页面和线上版本，但本地检查产物、用户确认的预览版本与正式迁入文件之间仍主要靠人工传递。多文件资源、正式页面依赖和多项线上错误也无法在一次检查中完整表达，容易把“某个 HTML 已通过”误认为整套产物已经被验证。

## What Changes

- 为 builder 检查结果增加可复核的整套产物文件清单、文件哈希和 bundle 摘要。
- 增加 publisher 对产物摘要的复核脚本，发现检查后文件漂移时失败。
- 增加批准预览源目录与正式目标目录的只读比较工具，报告文件新增、删除和字节差异。
- 扩展正式部署核验器，支持按 manifest 核验全部正式文件，并在单文件失败时继续收集结果。
- 扩展本地 HTML 检查器，递归核对独立 CSS 的 `url()` 与 `@import` 本地依赖。
- 更新两个 skill 的交接、迁移、合并前检查和线上验收步骤，并加入 skill 合同回归测试。

## Capabilities

### New Capabilities

- `artifact-provenance`: 为本地静态产物提供可复核的文件集合、哈希和交接验证。
- `deployment-verification`: 对预览和正式部署按明确文件范围进行完整、可审计的版本与资源核验。

### Modified Capabilities

无。

## Impact

- 影响 `skills/static-page-builder/scripts/check_static_html.py`、`skills/static-page-publisher/scripts/verify_deployment.py` 及新增 publisher 校验/比较脚本。
- 更新 `static-page-builder`、`static-page-publisher` 的 SKILL.md 与参考流程。
- 增加 Python 标准库测试；不引入运行时依赖，不改变静态页面源文件或 Pages 触发策略。
