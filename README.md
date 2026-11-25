# Static Pages · 静态发布与预览

本仓库统一托管已生成的报告、独立页面和静态工具，提供 PR 在线预览、正式部署和版本验收。页面制作与业务数据处理在交付前完成。

- [正式页面目录](https://wvliteam.github.io/static-pages/)
- [发布与维护指南](CONTRIBUTING.md)
- [Agent 工作约定](AGENTS.md)
- [部署工作流](https://github.com/wvliteam/static-pages/actions/workflows/pages.yml)
- [线上版本记录](https://wvliteam.github.io/static-pages/deployment.json)

页面目录统一在站点首页维护；本文件介绍仓库定位、结构和用法。

## 发布已有页面

需要 Git、Python 3.10+、已认证的 GitHub CLI，以及目标仓库的相应权限。脚本仅使用 Python 标准库。

在干净检出中从最新 main 创建 preview/<task> 分支，将入口 index.html 和必要资源放到 artifacts/<task>/public/。完整分支、PR 与发布命令见 [使用指南](CONTRIBUTING.md)。核心检查入口为：

~~~bash
python3 scripts/check_static_html.py --root artifacts/example-page/public --output scratch/example-page.json
python3 scripts/verify_artifact_manifest.py --root artifacts/example-page/public --manifest scratch/example-page.json
~~~

同仓库、base=main、分支为 preview/<task> 的 PR 会被组合进站点。预览 URL、head SHA 和文件哈希以成功部署的摘要及 deployment.json 为准。确认具体版本后，将干净产物迁到 docs，移除 tracked artifacts，检查并合并。

目录、授权与确认要求见 [Agent 工作约定](AGENTS.md)。

## 仓库结构

| 位置 | 职责 |
| --- | --- |
| docs/ | 正式静态内容、导航与历史快照 |
| artifacts/<task>/public/ | 仅 PR 分支跟踪的待审阅静态产物 |
| .github/workflows/ | 候选校验、站点组合与官方 Pages 部署 |
| scripts/build_pages.py、stage_pages.py | 组合正式源与活动预览，保存生成站点 |
| scripts/check_candidate.py | 固定 Git 版本的候选与合并就绪检查 |
| scripts/ 内的四个校验工具 | 本地检查、摘要核对、批准版本迁移与线上验收 |
| tests/ | 独立的发布设施回归测试 |
| scratch/ | 忽略的本地日志、数据和截图 |

发布工作流组合正式内容和符合条件的 PR 预览，独立候选工作流检查候选版本。权限与隔离规则见 [发布基础设施](AGENTS.md#发布基础设施)。预览链接公开可达，noindex 不提供访问控制。

## 维护资料

校验工具和部署脚本随仓库固定版本运行，来源记录和文件哈希用于核对校验工具的版本。维护方法见 [使用指南](CONTRIBUTING.md#7-校验工具与自动报告)。
