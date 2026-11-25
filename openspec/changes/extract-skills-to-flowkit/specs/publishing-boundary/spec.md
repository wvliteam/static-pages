## Purpose

划分 FlowKit 的页面技能与 static-pages 的部署责任，保证校验快照可追溯、预览授权明确，并在准确验收后交付自动报告。

## ADDED Requirements

### Requirement: 独立运行静态发布设施

static-pages MUST 使用仓库内固定版本的脚本完成候选校验、预览组合、正式部署与部署验收，不依赖安装业务技能或在线获取 flowkit 源码。

#### Scenario: 独立检出部署仓库
- **WHEN** 环境只有 static-pages 检出和其声明的运行工具
- **THEN** 发布设施测试和校验入口可用，不从 skills 目录或相邻 flowkit 导入代码

### Requirement: 校验快照可追溯

共享检查器 MUST 记录来源路径、内容版本和每个脚本的 SHA-256；同步 MUST 是显式维护操作。

#### Scenario: 快照文件被意外修改
- **WHEN** 任一脚本字节与本仓库清单不一致
- **THEN** 本地快照测试失败，不通过自动下载最新代码掩盖差异

### Requirement: 分离预览和已授权自动发布

普通页面 MUST 采用版本确认后的正式收录；已获持续授权的金融工作流 MAY 直接提交其报告和导航，并 MUST 在本次部署成功且内容验收后通知。

#### Scenario: 普通页面只有预览授权
- **WHEN** 调用方仅请求在线预览
- **THEN** 产物位于 PR 的 artifacts，不加入正式导航或 main/docs

#### Scenario: 自动报告部署失败或线上仍是旧版本
- **WHEN** Git push 成功，但部署 workflow 失败、超时或线上版本/文件不匹配
- **THEN** 发布不返回 deployed，金融流水线不发送成功通知

#### Scenario: 本地预演和仅提交
- **WHEN** 使用 dry-run 或 no-push
- **THEN** 结果明确为 dry-run 或 committed，deployed 为 false，不执行线上验收或真实通知

### Requirement: 站点基地址一致

站点组合、候选校验和发布调用方 MUST 采用一致的基地址约定，支持显式配置、CNAME 和 GitHub 项目或根站点地址。

#### Scenario: 使用自定义域名预览
- **WHEN** 正式源包含 docs/CNAME 且没有显式基地址覆盖
- **THEN** manifest 的预览 URL 与候选资源校验使用该域名的根路径，不额外添加仓库名
