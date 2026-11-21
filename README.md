# Static Pages · 统一静态页面仓库

在一个仓库中制作、审阅和发布分析报告、独立网页与静态小工具。页面先通过 PR 获得在线预览，确认当前版本后再加入正式目录；预览和正式页面都可直接在浏览器中访问。

- [正式页面目录](https://wvliteam.github.io/static-pages/)
- [使用指南：创建、预览、发布、维护](CONTRIBUTING.md)
- [Agent 工作约定](AGENTS.md)
- [已采纳方案：直接静态门户设计与实施计划](design/static-portal/README.md)
- [部署工作流与运行记录](https://github.com/wvliteam/static-pages/actions/workflows/pages.yml)
- [当前部署版本记录](https://wvliteam.github.io/static-pages/deployment.json)

## 项目功能

| 功能 | 使用方式 |
| --- | --- |
| 统一托管 | 报告放 `reports/`，普通页面放 `pages/`，工具放 `tools/`，各有独立网址 |
| 分阶段制作 | 先确认内容结构，再补充布局、图表、交互和检查；支持单文件 HTML 或 HTML 加本地资源 |
| 在线审阅 | 在 `preview/<task>` 分支提交静态产物并创建 PR，Actions 自动部署临时预览 |
| 正式收录 | 确认具体预览版本后，迁移到 `main/docs/` 并更新导航 |
| 多任务并存 | 每次组合正式页面和全部符合条件的活动 PR 预览；关闭 PR 后下次成功部署清理其预览 |
| 版本验收 | 用 `deployment.json` 中的提交 SHA 与文件 SHA-256 核对线上内容 |
| 可复用技能 | 页面创建和发布流程拆成两个独立 skill，可分别使用或组合 |

发布的是静态 HTML、CSS、JavaScript 和资源文件，不提供服务器端程序或数据库。页面可以在浏览器执行交互逻辑；发布流程不会运行预览分支的构建脚本或安装其依赖。使用前端框架时，应先在本地生成静态产物。

预览链接可公开访问，部署注入的 `noindex` 仅提示搜索引擎，不提供访问控制。本仓库也公开可读，未正式收录不等于私密。

## 已发布页面

| 页面 | 内容 |
| --- | --- |
| [513310 · 2026年11月20日收盘复盘](https://wvliteam.github.io/static-pages/reports/513310/2026-11-20/) | 分时与日 K、量能、溢价、关键价位和情景计算器 |

## 从哪里开始

仅阅读报告，打开上面的正式页面链接即可。

让 agent 创建并预览页面，可使用以下请求；已有 HTML 时直接使用发布器。

```text
使用 $static-page-builder 和 $static-page-publisher，
在 wvliteam/static-pages 为本次分析分阶段制作静态网页。
先提供在线预览供我检查，正式收录前等待我确认具体版本。
```

手动操作需要 Git、Python 3.10+、GitHub CLI，以及该仓库的推送和 PR 权限。Python 脚本仅使用标准库，无需安装 Python 依赖；浏览器用于查看效果，不是运行静态检查或发布脚本的前置条件。

```bash
git clone https://github.com/wvliteam/static-pages.git
cd static-pages
gh auth status
git switch -c preview/example-page
mkdir -p artifacts/example-page/public
```

在该目录创建完整的 `index.html`，将必要资源一并放入其中；已有页面也可以复制过来。然后进行本地检查、提交和创建 PR：

```bash
python3 skills/static-page-builder/scripts/check_static_html.py \
  --root artifacts/example-page/public
git add artifacts/example-page/public
git commit -m "Add example page preview"
git push -u origin preview/example-page
gh pr create --base main --head preview/example-page \
  --title "Preview: example page" --body "提供 example-page 在线预览，待审阅后正式收录。"
```

等待 [Pages 工作流](https://github.com/wvliteam/static-pages/actions/workflows/pages.yml) 成功，从运行摘要或 `deployment.json` 获取本次预览链接。地址形如 `https://wvliteam.github.io/static-pages/previews/pr-<编号>/example-page/`，实际是否上线以版本和文件校验为准。

继续修改、线上校验、正式发布和关闭预览的命令见 [使用指南](CONTRIBUTING.md)。

## 分支和文件位置

| 位置 | 内容 | 是否作为网页部署 |
| --- | --- | --- |
| `main` 的 `docs/` | 已确认的正式页面和导航 | 是 |
| 活动 PR 的 `artifacts/<task>/public/` | 可审阅的 HTML 和必要资源 | 是，部署到对应预览路径 |
| `gh-pages` 分支 | 工作流生成的完整站点快照 | 作为部署产物保存，勿手动编辑或合入 main |
| 根目录文档、`scripts/`、`tests/`、`skills/` | 使用说明、发布代码、测试、技能源文件 | 否，但 GitHub 仓库可读 |
| 本地 `scratch/` | 原始数据、检查记录、截图和临时文件 | 否，已被 Git 忽略 |

```text
README.md                         # 项目概览
CONTRIBUTING.md                   # 完整操作与维护指南
AGENTS.md                         # agent 执行约定
.github/workflows/pages.yml       # 测试、组合、保存快照和部署
scripts/build_pages.py            # 读取正式页面和活动 PR 的静态文件
scripts/stage_pages.py            # 更新生成的 gh-pages 分支
tests/                            # 发布流程和 skill 检查器的测试
skills/static-page-builder/       # 页面内容、图表、交互、本地检查
skills/static-page-publisher/     # 分支预览、确认、正式发布、线上校验
docs/
  index.html                      # 正式导航首页
  .nojekyll
  reports/<代码>/<YYYY-MM-DD>/index.html
  pages/<名称>/index.html
  tools/<名称>/index.html
artifacts/<task>/public/index.html # 只在预览分支跟踪，正式合并前移除
scratch/                          # 本地临时目录，按需创建
```

`docs/` 是网站源码目录，维护说明应写在根目录等站点源码之外。`docs/previews/`、`docs/artifacts/`、`docs/deployment.json` 为保留路径，不得创建；`main` 不得跟踪 `artifacts/` 中的文件。

## 两个 skill 如何配合

| Skill | 职责 | 可以独立完成 |
| --- | --- | --- |
| [static-page-builder](skills/static-page-builder/SKILL.md) | 分阶段组织内容、制作图表与交互、检查数据和本地页面 | 在任意指定目录制作静态产物，无需 GitHub 登录 |
| [static-page-publisher](skills/static-page-publisher/SKILL.md) | 准备预览分支与 PR、核对部署、按确认版本正式收录 | 接收已有 HTML，不要求重新制作 |

完整任务按“发布器准备分支与输出目录 → 创建器制作并检查 → 发布器提供在线预览 → 用户确认该版本 → 正式收录”进行。交接时提供产物目录、入口、必要资源、数据日期和检查结果。UI 设计可结合 `ui-ux-pro-max`；金融报告参考属于创建器的可选内容，普通页面无需加载。

安装方式和两个检查脚本的示例见 [使用指南](CONTRIBUTING.md)。技能源码保存在仓库 `skills/` 下，安装到本机的副本需要单独同步。

## 部署原理

仓库的 Pages 发布来源为 **GitHub Actions**。推送 main、符合条件的 PR 事件或手动运行，会触发 [pages.yml](.github/workflows/pages.yml)：

1. 检出可信的 main，执行测试。
2. 复制 `main/docs/`，按各 PR 的精确 head SHA 读取静态预览文件。
3. 为预览 HTML 注入状态横幅和 `noindex`，生成版本与文件哈希记录；正式页面字节保持不变。
4. 将完整站点保存到生成的 `gh-pages` 分支，在同一次 workflow 上传产物并部署到 Pages。

所有部署串行执行，每次重建完整站点。`gh-pages` 只是生成快照，不能仅靠向它推送来替代本工作流的部署步骤。工作流的上传产物保留 1 天；这不是预览网址的有效期。预览通常持续到 PR 关闭、合并或其有效产物被移除后的下一次成功部署。

代码入口、环境配置、体积限制、验证方法和故障处理见 [使用指南](CONTRIBUTING.md)。
