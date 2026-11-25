# Static Pages · 静态发布与预览

本仓库托管已生成的静态网页，提供 PR 在线预览、正式部署和版本验收。页面制作与 Agent 技能由 [FlowKit](https://github.com/wvliteam/flowkit) 维护；本仓库不再分发业务 skill。

- [正式页面目录](https://wvliteam.github.io/static-pages/)
- [发布与维护指南](CONTRIBUTING.md)
- [Agent 工作约定](AGENTS.md)
- [部署工作流](https://github.com/wvliteam/static-pages/actions/workflows/pages.yml)
- [线上版本记录](https://wvliteam.github.io/static-pages/deployment.json)

## 发布已有页面

需要 Git、Python 3.10+、已认证的 GitHub CLI，以及目标仓库的相应权限。脚本仅使用 Python 标准库。

在干净检出中从最新 main 创建 preview/<task> 分支，将入口 index.html 和必要资源放到 artifacts/<task>/public/。完整分支、PR 与发布命令见 [使用指南](CONTRIBUTING.md)。核心检查入口为：

~~~bash
python3 scripts/check_static_html.py --root artifacts/example-page/public --output scratch/example-page.json
python3 scripts/verify_artifact_manifest.py --root artifacts/example-page/public --manifest scratch/example-page.json
~~~

同仓库、base=main、分支为 preview/<task> 的 PR 会被组合进站点。预览 URL、head SHA 和文件哈希以成功部署的摘要及 deployment.json 为准。确认具体版本后，将干净产物迁到 docs，移除 tracked artifacts，检查并合并。

普通页面默认先预览后正式收录。已有持续授权的金融自动报告可由 FlowKit 的 report-publisher 直接更新其归档和首页索引；这不构成其他页面绕过预览的授权。

## 保留的发布设施

| 位置 | 职责 |
| --- | --- |
| docs/ | 正式静态内容、导航与历史快照 |
| artifacts/<task>/public/ | 仅 PR 分支跟踪的待审阅静态产物 |
| .github/workflows/ | 候选校验、站点组合与官方 Pages 部署 |
| scripts/build_pages.py、stage_pages.py | 组合正式源与活动预览，保存生成站点 |
| scripts/check_candidate.py | 固定 Git 版本的候选与合并就绪检查 |
| scripts/ 内的四个校验工具 | 本地检查、摘要核对、批准版本迁移与线上验收 |
| scripts/flowkit-checks.json | 校验工具来源、固定内容版本与哈希 |
| tests/ | 独立的发布设施回归测试 |
| scratch/ | 忽略的本地日志、数据和截图 |

CI 只运行可信 main 的部署代码，按精确 PR head SHA 读取静态文件；不会执行 PR 构建脚本。main/docs 不得包含 previews、artifacts 或 deployment.json 保留路径。gh-pages 是生成快照，不能手动编辑或合入 main。

预览链接公开可达，noindex 不提供访问控制。只有当前部署运行成功且版本和文件核对通过，才算上线。

## 已发布页面

| 页面 | 内容 |
| --- | --- |
| [513310 · 2026年11月20日收盘复盘](https://wvliteam.github.io/static-pages/reports/513310/2026-11-20/) | 分时与日 K、量能、溢价、关键价位和情景计算器 |

## 技能与开发资料

页面创建和发布技能的唯一维护位置是 FlowKit 的 skills/static-page-builder 与 skills/static-page-publisher；安装与使用见 [FlowKit](https://github.com/wvliteam/flowkit)。本仓库不需要安装它们即可检查和部署。

维护校验工具时，先在 FlowKit 修改源码并测试，再显式同步固定快照；步骤见 [使用指南](CONTRIBUTING.md#7-校验工具与技能边界)。现有 .agents/skills/openspec-* 仅服务本仓库基础设施开发，继续保留。历史方案与规范位于 design/ 和 openspec/，不作为网页部署。
