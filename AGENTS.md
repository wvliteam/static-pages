# Agent 工作约定

## 开始任务

- 项目为 `wvliteam/static-pages`，统一托管报告、页面和静态工具，不为每个页面创建新仓库。
- 先读 [README.md](README.md)；需要具体命令、配置或故障处理时读 [CONTRIBUTING.md](CONTRIBUTING.md)。再检查远端、当前分支、未提交修改和适用的 skill。
- 保留用户与其他任务的文件。已有适合本任务的分支或检出时优先复用；不要 force push、重置用户文件或改写共享 main 历史。
- 页面内容任务走预览和确认流程；项目说明、skill 与发布基础设施的维护不等于新增页面正式收录，按该任务授权和仓库规则处理，不额外引入无关审批。
- 门户能力、复杂静态工具和发布基础设施的行为变更使用 [OpenSpec](CONTRIBUTING.md#使用-openspec)；日常报告更新、文案和样式小修沿用现有流程。规范和技能文件留在仓库根目录对应路径，规范归档不等同于页面版本确认。

## 技能与交接

- `skills/static-page-builder/` 负责内容、图表、交互、数据核对和本地页面检查；可接受任意输出目录，不要求 GitHub。
- `skills/static-page-publisher/` 负责分支、PR、线上预览、确认和正式发布；可直接接收已有页面，不强制重做。
- 端到端任务先由发布器确定分支和输出目录，再由创建器制作并检查，最后交给发布器部署。交接提供产物路径、入口、必要资源、数据日期和检查结果。
- 技能源文件在仓库版本管理；只有修改 skill 时才按需同步已安装副本，并先保护本机改动。不要在通用 skill 中固定本机路径或账号。

## 页面与目录边界

- `main/docs/` 只存放已批准的正式网站内容；根目录文档、脚本、测试和 skill 不放入 docs。docs 是部署源，不能当作私有操作文档目录。
- 报告路径为 `docs/reports/<symbol>/<YYYY-MM-DD>/index.html`；普通页面和工具分别为 `docs/pages/<slug>/index.html`、`docs/tools/<slug>/index.html`。保留其他页面及历史日期快照。
- 新页面或待审阅的页面修改使用 `preview/<task>` 分支，可审阅文件只放 `artifacts/<task>/public/`。任务名匹配 `[a-z0-9][a-z0-9-]{0,79}`，必须有入口 index.html。
- 原始数据、检查记录、日志、截图和本机工具放忽略的 `scratch/` 或仓库外。只显式暂存任务所需文件；不得上传凭据、账户资料或整个工作区。
- 使用适用于项目基路径与嵌套预览路径的资源链接。源 HTML 保持干净，不手写部署横幅或 `data-static-preview` 标记。

## 预览与正式收录

- 创建同仓库、base 为 main 的 PR，分支须以 `preview/` 开头。预览 URL 形如 `https://wvliteam.github.io/static-pages/previews/pr-<number>/<task>/`，以成功运行的摘要和 manifest 为准。
- 预览公开可直达；noindex 不是权限控制。预览不等于正式批准，不能提前加到正式首页、数量或 README 的已发布列表。
- 记录用户确认的具体预览 head SHA。对当前会话已经批准的相同产出无需重复申请；有实质内容变化时重新提供对应版本审阅。
- 确认后在 PR 分支把干净源文件移到正式 docs 目录，清理全部跟踪的 artifacts，更新 `docs/index.html` 的链接与数量（如有）及 README 正式列表，检查 diff 后再合并。
- 迁移使 PR 无有效 artifacts 时，下次部署便可能移除预览；保留迁移前的确认 SHA，另记录最终 main SHA。main 严禁跟踪 artifacts 文件。

## 发布基础设施

- `.github/workflows/pages.yml` 在可信 main 上测试、组合站点、写 gh-pages，并在同一次 workflow 调用官方 Pages 上传和部署 Action；部署串行执行。
- 每次重新组合 main/docs 与全部符合条件的活动 PR，按精确 PR head SHA 读取静态文件。不要执行 PR 构建脚本、安装 PR 依赖或在带写权限的 pull_request_target 中运行 PR 代码。
- `gh-pages` 为生成分支，不手动编辑或合入 main。`docs/previews/`、`docs/artifacts/`、`docs/deployment.json` 为保留路径，不得创建。
- PR 关闭或合并后，预览在下一次成功部署清理；不要通过删除整个站点清理单个任务。不要随意关闭或合并其他任务的 PR。
- 调整发布逻辑时维持路径、大小、文件类型和源版本校验，勿为消除报错绕过边界。发布配置、权限或费用结论应以实际仓库和当前官方说明为准。

## 验证与交付

- 页面改动运行创建器的 `check_static_html.py`，并按条件检查布局、键盘和交互；脚本不运行 JavaScript，不代替视觉审阅。没有本机浏览器时可提供 Pages 在线预览，勿声称完成了未执行的检查。
- 工作流、发布脚本或检查器改动运行相关测试：`python3 -m unittest discover -s tests -v`。仅文档改动检查链接、命令与 `git diff --check`；不为低影响文档改动增加测试代码。
- 部署后使用发布器的 `verify_deployment.py`，核对 manifest 的 main/PR head SHA 及实际文件哈希。正式文件可与本地 docs 比较；预览文件按 manifest 的注入后哈希核对。
- 只有本次运行成功且版本、内容核对通过，才称已部署；HTTP 200、gh-pages 更新或旧运行成功均不足以证明当前上线。输出检查记录放 scratch，交付说明包含 URL、版本及仍未完成的验收项。
