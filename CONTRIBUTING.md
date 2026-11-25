# 使用与维护指南

本指南提供 `wvliteam/static-pages` 的操作命令与排错方法。项目概览见 [README](README.md)；目录、授权、确认与验收规则统一见 [AGENTS.md](AGENTS.md)。以下命令均在仓库根目录执行；示例任务名为 `example-page`，执行时替换为本次名称。

## 1. 准备环境

- Git、Python 3.10+；脚本仅使用 Python 标准库。
- GitHub CLI（`gh`），已登录有仓库写入权限的账号；`gh auth status` 可检查登录状态，不要打印 token。
- 在线预览和发布需要网络、GitHub Actions 与 Pages；仅制作页面或检查本地 HTML 不需要 GitHub 认证。

复用已有仓库时先执行 `git status --short --branch`，保留其他人的未提交修改，再从最新 main 建立预览分支。下面更新命令以工作区干净为前提：

```bash
git switch main
git pull --ff-only origin main
git switch -c preview/example-page
mkdir -p artifacts/example-page/public scratch
```

任务命名与存放要求见 [页面与目录边界](AGENTS.md#页面与目录边界)。网址中的任务名取自产物目录，示例中与分支名保持一致。

## 2. 接收静态产物

将已有的 index.html、HTML/CSS/JavaScript 和必要资源放入 artifacts/example-page/public/。页面创作、数据核验和交互检查由交付方在提交前完成。

框架项目先在本地构建，再交付静态产物；本仓库不会运行 PR 构建代码。HTML 使用 UTF-8，包含 html、head、body、标题和移动视口。使用适合嵌套预览路径的相对资源链接。预览横幅由部署注入，源文件不手写 data-static-preview 标记。

## 3. 本地检查

```bash
python3 scripts/check_static_html.py \
  --root artifacts/example-page/public \
  --output scratch/example-page-local.json
```

检查器默认检查根目录的 `index.html`，可重复使用 `--page` 指定其他 HTML。它检查标题、移动视口、重复 ID、已知占位符、HTML 引用的本地资源和锚点等；失败会返回非零退出码。完整选项可用 `--help` 查看。

检查 JSON 的 `artifact_manifest` 列出整个根目录的普通文件相对路径、字节数与 SHA-256，并对排序后的清单生成 `bundle_sha256`。检查记录必须放在根目录外。检查器还会递归检查独立 CSS 的本地 `url()` 和 `@import` 资源；不执行 JavaScript 或验证外网运行资源。多页面目录需对每个 HTML 重复提供 `--page`。

交给发布器前确认文件仍与检查摘要一致：

```bash
python3 scripts/verify_artifact_manifest.py \
  --root artifacts/example-page/public \
  --manifest scratch/example-page-local.json
```

文件增删、改字节或路径变化都会返回非零，并列出对应状态。若接收的已有 HTML 没有检查记录，发布器先创建一份新记录再复核，不沿用过期摘要。

| 选项 | 适用情况 |
| --- | --- |
| `--page detail.html` | 检查额外页面，可重复传入 |
| `--require-single-file` | 禁止引用需另行交付的本地或外部运行资源；外部来源链接仍可保留 |
| `--base-path /static-pages/` | 按所设 URL 前缀将根路径链接映射到本地目录，不会请求网络 |
| `--require-homepage-link` | 要求根导航首页已收录所检查的页面，适合正式收录检查 |
| `--output scratch/result.json` | 保存检查记录；输出记录必须在被检查目录之外 |

此检查不运行 JavaScript，也不验证图表含义或视觉布局。能使用浏览器时检查移动布局、键盘操作和交互；本机没有浏览器时，通过下一步的 Pages 在线预览审阅，并说明尚未完成的视觉检查。

## 4. 创建和更新在线预览

```bash
git add artifacts/example-page/public
git diff --cached --stat
git commit -m "Add example page preview"
git push -u origin preview/example-page
gh pr create --base main --head preview/example-page \
  --title "Preview: example page" --body "新增静态页面预览，待确认当前版本后正式收录。"
```

在 [Actions](https://github.com/wvliteam/static-pages/actions/workflows/pages.yml) 中等待 `Publish site and PR previews` 成功，从运行摘要打开预览。也可以查看 [deployment.json](https://wvliteam.github.io/static-pages/deployment.json) 中 `previews` 的 `url`。

```text
https://wvliteam.github.io/static-pages/previews/pr-<PR编号>/example-page/
```

预览资格和隔离规则见 [预览与正式收录](AGENTS.md#预览与正式收录)。横幅显示 PR 编号、任务名和版本前 7 位，并带审阅记录链接。

继续审阅时，修改同一分支的页面、重新检查、提交并推送即可，PR 的新 head SHA 会触发重建。预览使用同一个 URL，版本是否更新要以部署记录为准。

### 校验具体预览版本

将 `123` 替换为实际 PR 编号；预期 SHA 从 GitHub 的 PR head 读取，避免将其他分支的本地 HEAD 当成审阅版本：

```bash
PREVIEW_PR=123
PREVIEW_SHA=$(gh pr view "$PREVIEW_PR" --json headRefOid --jq .headRefOid)
python3 scripts/verify_deployment.py \
  --base-url https://wvliteam.github.io/static-pages/ \
  --preview-pr "$PREVIEW_PR" --preview-sha "$PREVIEW_SHA" \
  --task example-page --output scratch/example-page-preview.json
```

校验器先确认 manifest 中的 PR head SHA，再下载对应文件核对 SHA-256。预览 HTML 因横幅注入会与本地源文件不同，应与 manifest 中的生成文件哈希比较；预览模式不接受 `--local-root`。

向审阅者交付预览 URL、对应完整 head SHA、检查结果和待确认事项。HTTP 200 或 workflow 成功本身均不能证明浏览器拿到的是本次版本。

## 5. 确认后正式发布

按 [预览与正式收录](AGENTS.md#预览与正式收录) 取得具体版本的确认后，记录完整预览 head SHA，下文以 `APPROVED_PREVIEW_SHA` 引用。

在原 PR 分支操作，将批准的干净源文件移到正式目录。普通页面示例：

```bash
mkdir -p docs/pages
git mv artifacts/example-page/public docs/pages/example-page
```

迁移后、提交前将正式目标目录与用户确认的预览 head 比较：

```bash
python3 scripts/compare_promotion.py \
  --repo-root . --preview-sha "$APPROVED_PREVIEW_SHA" \
  --task example-page --manifest scratch/example-page-local.json \
  --target-root docs/pages/example-page \
  --output scratch/example-page-promotion.json
```

比较器从指定 SHA 的 Git archive 读取预览源，不使用当前工作树中可能已变化的草稿。目标需与批准产物拥有相同相对路径及字节；任何新增、缺失或修改都在合并前处理。

按 [页面与目录边界](AGENTS.md#页面与目录边界) 选择正式路径。上述移动命令用于新增目录；更新已有页面时检查实际目标，仅应用本次变更。不要从在线预览下载带横幅的 HTML 作为正式源文件。

更新 `docs/index.html` 的链接和页面数量（如有），再检查迁移后的文件和暂存范围：

```bash
python3 scripts/check_static_html.py \
  --root docs --page . --page pages/example-page/ --base-path /static-pages/ \
  --require-homepage-link --output scratch/example-page-formal-local.json
git ls-files artifacts
git diff --check
git add docs/index.html docs/pages/example-page
git diff --cached --stat
git commit -m "Publish approved example page"
git push
```

迁移提交改变了 PR head。推送后等待候选工作流对最新 head 与测试合并提交运行 `static-pages-candidate` 和 `static-pages-main-ready`；确认两者通过、摘要检查通过、`git ls-files artifacts` 无输出，并遵循当前分支保护规则后再合并：

```bash
git ls-files artifacts
gh pr checks "$PREVIEW_PR"
gh pr merge "$PREVIEW_PR" --merge --delete-branch
```

这里的 `PREVIEW_PR` 沿用上一节的实际编号；`git ls-files artifacts` 应没有输出，暂存 diff 应保留迁移产生的删除。合并前还应检查完整 diff 和仓库要求的检查状态。若仓库保护规则要求其他合并方式或审阅，遵循实际规则。

迁移提交会更新 PR head；如果已无 `artifacts/`，下一次部署就不再生成该预览，即使 PR 尚未合并也会如此。因此批准记录应保留迁移前的预览 SHA，发布记录另记合并后的 main SHA。

### 校验正式部署

合并后等待本次 Pages 工作流成功，再校验 main 与正式文件：

```bash
git switch main
git pull --ff-only origin main
MAIN_SHA=$(git rev-parse HEAD)
python3 scripts/verify_deployment.py \
  --base-url https://wvliteam.github.io/static-pages/ \
  --main-sha "$MAIN_SHA" --page . --page pages/example-page/ \
  --local-root docs --output scratch/example-page-formal.json
```

`--main-sha` 必须是完整 40 位提交 SHA；`--page` 可重复，默认只核对首页。正式模式核对所选页面的线上哈希，可用 `--local-root docs` 额外比较本地字节；它不代替浏览器交互验收。若检查期间 main 又更新，应明确重新验收哪个提交，避免拿旧提交误判新部署。

需要完整核对正式站点全部文件时，使用 `--all-production` 替代 `--page`；该模式按 manifest 清单检查 HTML 与所有正式资源。每个文件记录自己的下载、哈希、MIME 与本地比较错误，单个文件失败不会隐藏其他文件结果；整体结果仍为失败。单页轻量模式保持不变。

```bash
python3 scripts/verify_deployment.py \
  --base-url https://wvliteam.github.io/static-pages/ \
  --main-sha "$MAIN_SHA" --all-production --local-root docs \
  --output scratch/example-page-formal-all.json
```

正式 URL 为 `https://wvliteam.github.io/static-pages/pages/example-page/`。交付时记录 URL、main SHA、Actions 运行链接和校验结果。

## 6. 结束预览与撤回发布

放弃草稿时关闭 PR；预览会在下一次成功部署中移除，源分支是否保留可按需要决定。关闭不会自动删除已合入 main 的正式页面。

撤回正式页面时，通过新提交删除对应 `docs/` 页面并更新站点导航；撤销错误修改时可对相关提交做定向 revert。操作边界见 [开始任务](AGENTS.md#开始任务)，之后重新运行部署校验。

## 7. 校验工具与自动报告

本地检查、产物复核、迁移比较与部署验收均使用本仓库 scripts 中的工具，无需安装页面生成工具或检出其他项目。

check_static_html.py、verify_artifact_manifest.py、compare_promotion.py 和 verify_deployment.py 使用固定版本，scripts 中的来源清单记录各文件来源路径、SHA-256 和由完整来源清单计算的内容版本。

维护校验工具时，先检查本机改动，按来源记录取得明确版本的脚本与匹配清单，审阅差异和兼容性后一起更新。运行下一节的回归测试，确认脚本字节与清单一致，并在同一 PR 中说明来源版本、变更和检查结果。CI 只验证仓库内固定副本，不在部署时下载最新代码。

### 已授权金融自动报告

持续授权与可写范围见 [已授权自动报告](AGENTS.md#已授权自动报告)。自动任务复用 [正式部署校验](#校验正式部署) 的命令，将本次 main push 的完整 SHA 传给 `--main-sha`，保存对应运行与验收结果。通知条件见 [验证与交付](AGENTS.md#验证与交付)。

## 8. 维护工作流与测试

发布脚本和校验工具的测试命令：

```bash
python3 -m unittest discover -s tests -v
```

检查类型按 [验证与交付](AGENTS.md#验证与交付) 选择。仅文档改动使用 `git diff --check`，并核对本地链接和命令入口。部分 Andronix 环境的裸仓库推送测试会跳过，GitHub Ubuntu runner 负责执行该项。

[Pages 工作流](.github/workflows/pages.yml) 中的测试使用可信 main 的代码；独立的低权限候选工作流测试 PR 对应的合并候选版本。在线静态预览不能替代发布脚本的回归测试。

### 候选检查和合并就绪

[候选验证工作流](.github/workflows/validate.yml) 为以 main 为目标的 PR 提供两个独立结果：

| 检查 | 检查内容 |
| --- | --- |
| `static-pages-candidate` | 对测试合并提交运行 Python 测试并检查全部正式 HTML；对 PR head 的归档检查所有预览任务、入口和直接资源。 |
| `static-pages-main-ready` | 检查完整的测试合并树中是否仍跟踪 `artifacts/` 文件，不受分支名或未跟踪本地文件影响。 |

检查日志记录事件 base、PR head 和测试合并提交；无法取得指定 Git 对象或提交版本关系不符时，检查失败，不改用分支最新版本。有效预览的候选检查可以通过，同时合并就绪检查会因草稿仍在而失败；按现有流程确认并迁移后再看新的检查结果。候选工作流仅授予 `contents: read`，不运行浏览器、不解析所有间接资源，也不向 Pages 提供任何部署权限。PR 有合并冲突时先解决冲突，再重跑检查。当前实现只报告结果；是否强制通过取决于仓库的合并规则。

本地可先运行下面的候选检查，再运行本节开头的回归测试。检出事件对应的测试合并提交并获取其两个父提交；事件 JSON 放在 `scratch/pr-event.json`，需要 `pull_request.number`、`base.ref`、`base.sha` 和 `head.sha`（后三项位于 `pull_request` 内）。

```bash
python3 scripts/check_candidate.py candidate --event-path scratch/pr-event.json --candidate-sha "$(git rev-parse HEAD)"
python3 scripts/check_candidate.py main-ready --event-path scratch/pr-event.json --candidate-sha "$(git rev-parse HEAD)"
```

回退候选检查时，移除独立工作流及其脚本即可；如果之后已将检查设为必需，先调整对应仓库规则。Pages 发布不依赖候选工作流。

### 新仓库复用时的配置

当前仓库已完成配置。若复制到其他项目仓库，需要检查这些项目，不能仅创建预览分支：

1. 使用 main 为正式源分支，提交 `docs/index.html`、本项目工作流和脚本。
2. 在仓库 Settings → Pages 中将 Source 设为 GitHub Actions，允许仓库运行工作流及其声明的权限。
3. 保证 `github-pages` environment 允许可信 main 的部署；按实际仓库保护规则配置，勿为执行 PR 代码开放部署权限。
4. 确认构建 job 可写生成的 gh-pages 分支、读取同仓库 PR，部署 job 可写 Pages 并申请 OIDC token。组织策略或分支保护可能需要维护者调整。
5. 更新 README、导航和仓库约定中的站点地址，再运行一次工作流并校验正式首页。

站点组合器从 STATIC_PAGES_BASE_URL、docs/CNAME 或仓库名推导基地址；调用方的验收基地址须与其一致。main、docs、artifacts 等目录约定仍由代码固定。提交 workflow 的账号若被提示缺少 workflow 授权，应补足相应权限；勿通过打印 token 或更换未经授权的身份绕过。

### 构建限制与信任范围

- PR 下载归档上限 50 MiB；单个 PR 内被选中的全部预览文件合计不超过 20 MiB、1000 个文件。
- 预览只接收符合目录规则的普通文件；拒绝符号链接、硬链接、隐藏路径、路径越界和重复文件。
- 一个任务缺少 `public/index.html` 时记入 `deployment.json` 的 `skipped`，暂不生成该任务；非法路径或超限等错误会使构建失败。

目录和执行权限边界见 [发布基础设施](AGENTS.md#发布基础设施)。

`deployment.json` 的 `main_sha` 标识正式源，`production_sha256` 按正式相对路径记录文件哈希，`previews` 记录 PR、分支、head SHA、任务 URL 与生成文件哈希，`skipped` 记录未就绪任务。它由工作流生成，不要手动编辑。

## 9. 常见问题

| 现象 | 排查与处理 |
| --- | --- |
| PR 没有预览 | 检查是否为同仓库、base=main、分支以 preview/ 开头的打开状态 PR；确认任务目录及 index.html；查看 Actions 和 manifest 的 skipped |
| URL 返回 404 | 从运行摘要获取真实 URL，等待部署成功；检查任务名及 PR 是否已关闭或移走产物 |
| 页面仍为旧版 | 核对 manifest 的 main/head SHA 和实际文件哈希；缓存诊断可加版本查询参数，但最终验收仍核对交付 URL |
| CSS、图片、脚本丢失 | 确认资源已提交到 public 内，路径大小写正确，未使用错误的域名根路径；检查器不解析全部 JavaScript 动态加载逻辑 |
| 构建提示 main 有 artifacts | 移除跟踪的草稿文件后再合并/部署；不要通过放宽脚本规则绕过 |
| gh 已登录，git push 仍要用户名 | 可仅为该命令使用下面的 gh 凭据助手，不把 token 写入远端地址 |
| 构建或部署失败 | 查看对应 job 日志，先修复根因；现有线上部署不因失败自动更新。gh-pages 快照可能已更新，不能据此宣称上线 |
| 想重新部署 | 在 Actions 的该工作流选择 Run workflow，或执行 `gh workflow run pages.yml --ref main`；重建使用当时 main 和活动 PR 状态 |

```bash
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin HEAD
```

Actions 用量、存储和平台限额以 GitHub 当前规则为准；本项目不承诺固定免费额度。参考 [Pages 发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)、[官方部署 Action](https://github.com/actions/deploy-pages)、[Actions 事件与权限边界](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)。
