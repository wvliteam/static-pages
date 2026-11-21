# R02：候选代码 CI 与静态产物检查实现方案

- 调研日期：2026-11-21。
- 基线：`main`，`ee180b1e36d71b600f324ddbaa8d64e493862565`。
- 对应计划：[OPTIMIZATION_PLAN.md](../../OPTIMIZATION_PLAN.md) 中的 R02。
- 状态：实现方案与本地验证结论，尚未增加或运行新的 GitHub 工作流。
- 范围：独立候选验证、静态产物检查和合并就绪检查。正式部署仍按可信 main 的发布机制执行。

## 1. 结论

建议增加一个独立的低权限 `pull_request` 验证工作流，覆盖所有指向 main 的 PR，并提供两个固定检查：

1. **`static-pages-candidate`**：验证候选代码和当前变更对应的静态产物。
2. **`static-pages-main-ready`**：验证候选合并结果能够进入 main，尤其是不含任何跟踪的 `artifacts/` 文件。

两个结果需要分别呈现。一个预览 PR 可以内容检查通过、在线供审阅，同时因仍有草稿文件而暂不能合并。迁移到正式目录、清理跟踪的 artifacts 后，合并就绪检查才通过。该检查覆盖普通功能分支和维护分支，不能只覆盖 `preview/`。

候选验证运行候选脚本与测试；带发布权限的流程继续执行可信 main 代码。不要为了复用现有发布 job，在 `pull_request_target` 的写权限环境中检出并运行 PR 代码或页面 JavaScript。

## 2. 已核实的现状

### 2.1 当前实现

| 位置 | 当前行为 | 对方案的影响 |
| --- | --- | --- |
| [pages.yml](../../.github/workflows/pages.yml) | 检出 main，再运行单元测试、组合静态产物和部署 | 不能验证 PR 修改后的脚本与测试 |
| [build_pages.py](../../scripts/build_pages.py) 的 `assemble()` | 使用当前进程工作目录执行 `git ls-files artifacts`，发现跟踪草稿即拒绝 | 不能把现有全站生产组合入口直接作为候选 PR 检查入口 |
| [test_pages.py](../../tests/test_pages.py) | 组合测试以临时目录为根，并 mock `pages.git` | 当前单元测试可在包含草稿的候选检出中运行 |
| [check_static_html.py](../../skills/static-page-builder/scripts/check_static_html.py) | 默认只检查根入口；额外页面要重复指定 `--page` | CI 需要明确枚举待检查页面 |
| 同上 | 不执行 JavaScript、不递归解析外部 CSS、不完整解析非单文件模式的 `srcset` | 静态结果不能标成完整资源依赖、布局或交互验收 |
| [preview_html()](../../scripts/build_pages.py) | 要求 `html/head/body`，拒绝源中已有预览标记 | 候选预览应复用这些边界，不能只运行现有本地 HTML 检查 |

### 2.2 本地最小复现

本次在忽略的 `scratch/r02-research/` 下创建临时候选仓库，加入并暂存 `artifacts/demo/public/index.html`，没有修改真实仓库索引或正式实现。

| 实验 | 实际结果 | 结论 |
| --- | --- | --- |
| 在含 tracked artifacts 的临时候选仓库运行完整单元测试 | 20 项测试，19 项通过、1 项环境跳过，退出码 0 | 单元测试可直接纳入低权限候选验证 |
| 在同一临时仓库直接调用 `assemble()` | 拒绝，错误为 `main must not contain tracked draft artifacts` | 应提供独立候选检查入口，保留生产入口的拒绝规则 |
| HTML 片段有 title、viewport，但没有 html/head/body | 本地 HTML 检查退出码 0；`preview_html()` 拒绝 | 本地检查通过不等于满足预览部署格式 |
| HTML 引用存在的 style.css，CSS 引用不存在的字体 | 本地检查退出码 0 | 外部 CSS 的间接依赖不在当前检查覆盖内 |
| HTML 直接引用不存在的 stylesheet | 本地检查退出码 1 | 现有 HTML 直接资源检查可复用 |

实验记录位于本地 `scratch/r02-research/probe-results.json` 和 `candidate-unit-tests.log`。它们为忽略的研究记录，不作为公开网页或必须跟踪的交付文件。

### 2.3 仓库保护读取结果

本次只读查询确认仓库为 PUBLIC、默认分支为 main。传统分支保护接口返回 HTTP 404，响应为 `Branch not protected`；仓库 rulesets 列表和 main 有效分支规则接口均返回空列表。

这表示本次可见结果未显示已配置的 main 合并检查门禁，不能将下文拟议检查描述为当前已强制执行，也不能据此推断组织全部策略。启用 required checks 是后续实施中的明确配置步骤，本次没有执行。

## 3. 已核对的 GitHub 与 Git 语义

| 事项 | 官方语义 | 设计决策 |
| --- | --- | --- |
| PR 测试版本 | 可合并 PR 的 `pull_request` 默认使用测试合并提交；`GITHUB_SHA` 与 PR head SHA 是不同概念 | 单元测试推荐测事件对应的合并结果，同时记录 head SHA |
| 合并冲突 | 存在合并冲突时，`pull_request` 工作流不会运行 | 要求先解决冲突，不回退到高权限环境执行 PR 代码 |
| 权限 | 显式指定部分 `permissions` 后，未指定的权限设为 none | 候选 job 仅授予 `contents: read`，不使用 Pages、OIDC 或仓库写权限 |
| 路径过滤 | 整个工作流因路径等条件被跳过，关联的必需检查可能停留在 Pending | 工作流不设置 `paths` 或 `paths-ignore`；在运行内部选择检查 |
| 条件跳过 job | job 条件跳过可报告成功；失败依赖导致的后续 job 跳过也需要谨慎处理 | 两个固定检查始终创建，不以 job 跳过代替合并就绪判断 |
| 必需检查版本 | 必需检查要求最新对应 SHA 的结果，合并提交与 head 提交结果不能混称 | 报告同时记录 base、head 和实际测试提交 |
| 变更文件名 | Git 的 `-z` 输出保留文件名并以 NUL 分隔 | 在 Python 中解析字节记录，不使用换行切分、shell 单词拆分或拼接执行文件名 |

来源：[G1：工作流事件](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)、[G2：必需检查排障](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)、[G3：工作流权限](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions)、[G4：Git diff](https://git-scm.com/docs/git-diff)。查询日期均为 2026-11-21。

## 4. 备选方案比较

| 方案 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- |
| 在现有发布 job 直接测试 PR | 代码位置看似集中 | 将候选执行混入写权限发布环境，且破坏可信 main 边界 | 不采用 |
| 仅在本地手工测试 | 基础设施改动少 | 缺少共享、可重复的合并前结果 | 保留为补充 |
| 独立低权限 `pull_request` 工作流 | 与候选代码一致，可生成 PR 检查；部署机制可独立演进 | 需要增加检查入口、处理草稿与正式规则差异 | 推荐 |
| 首轮就增加跨工作流产物传递、自动发布和浏览器矩阵 | 可提供更多自动化 | 扩大来源核验和运行成本，尚无必要 | 后续按需求扩展 |

推荐先建立简单的独立验证面。R01 是否调整预览触发方式，不影响 R02 使用低权限候选验证的基本结构。

## 5. 版本、差异与检查范围

### 5.1 区分三种版本

- `base_sha`：本次事件中 main 的基提交。
- `head_sha`：本次 PR 源分支提交；预览发布读取此版本。
- `tested_merge_sha`：本次 `pull_request` 事件的 `GITHUB_SHA`；候选代码与拟合入 main 的结果使用此版本。

推荐以 `tested_merge_sha` 检出并测试候选代码，以 `base_sha → tested_merge_sha` 的二点树差异选择受影响检查。不要用运行中可能变化的 `origin/main` 代替事件基线，也不要仅以 `head_sha` 结果宣称已检查与 main 集成后的行为。

预览产物还需检查 `head_sha` 的对应任务快照，因为实际预览归档读取 PR head。合并快照中的 artifacts 检查不能代替这一项。若两种快照的任务内容不同，报告具体差异并分别检查。

获取不足的固定提交时只按明确 SHA 补取；缺失对象应失败并说明原因，不能静默切换到更新的分支版本。

### 5.2 差异分类

拟议入口内部使用类似 `git diff --name-status -z --find-renames BASE CANDIDATE --` 的参数数组调用，处理新增、修改、删除、重命名与类型变化。重命名同时纳入旧路径和新路径；删除任务也必须形成检查记录。

| 变更范围 | 推荐首版检查 |
| --- | --- |
| 仅 Markdown、说明资料 | 相对文件链接、引用命令与格式；不执行完整页面制作流程 |
| scripts、tests、skill 检查器、工作流 | 候选完整单元测试；工作流变更另核对触发、权限和实际运行结果 |
| skill 说明或参考资料 | 本地文件引用、元数据和命令检查；涉及流程行为时交给 R06 案例验证 |
| `docs/` 内容、资源或导航 | 检查全部正式 HTML 及直接资源引用，覆盖删除和共享资源影响 |
| `artifacts/<task>/public/` | 检查相关快照中的全部有效任务及全部 HTML，不只检查变更入口 |
| `.gitattributes` 或归档处理相关代码 | 强制运行预览快照与归档口径检查 |
| 无法可靠分类 | 采取完整静态扫描与完整单元测试，避免未覆盖却报告成功 |

当前站点体积小，首版对出现网页变更的 PR 扫描全部正式 HTML 和相关快照全部预览任务，优于维护复杂的反向依赖图。检查范围扩大后再评估优化。

### 5.3 文档检查边界

相对文件链接要核对目标存在；已删除文件按候选树检查入链。涉及 Markdown 锚点时应采用与目标渲染器匹配的规则，否则单列未校验范围。外部链接检查可独立运行并设置重试，不能把临时网络波动混成文档内容错误。

仓库里的 shell 示例与拟议接口需要区别：现有命令核对脚本及参数；实现方案中的尚不存在接口应明确标注拟议，不作为死链接或命令可用性的成功证明。

## 6. 静态产物规则与归档口径

### 6.1 预览检查

拟议入口分别完成：

1. 从 Git 树或归档枚举候选路径，按任务规则分组，统计每个 PR 的总文件数和字节。
2. 复用 `archive_files()` 对任务 slug、普通文件、符号链接、隐藏路径、越界、重复条目和大小的拒绝规则。
3. 对每个 HTML 复用 `preview_html()` 的格式和干净源文件检查；注入测试结果只写临时目录。
4. 对每个任务枚举全部 HTML，使用现有 `HtmlChecker` 核对 title、viewport、重复 ID、锚点和已覆盖的本地资源。
5. 提前报告与部署校验器路径契约不兼容的文件名，例如百分号、问号、片段符号或非规范路径；采用现有规则的交集，不能为检查方便而放宽线上限制。

**缺入口策略**：仅有 `public/` 资源、缺 `index.html` 的在建任务，保留现有发布器“记录 skipped、暂不生成预览”的语义。在候选报告中标为 `incomplete`，使静态产物检查失败并解释原因；线上组合不必因此改变既有宽容策略。整个任务被有意删除则记录删除，不能对已经不存在的入口继续执行检查。

这里的候选失败不阻止可信发布器按现有规则展示其他已就绪预览；也不表示有入口的产物已经获准正式收录。

### 6.2 正式目录检查

- 始终要求 `docs/index.html` 存在，拒绝部署保留路径和符号链接等现有生产禁项。
- `docs/` 有变更时扫描当前候选树的全部 HTML，处理共享资源删除造成的其他页面损坏。
- 对页面路径使用站点基路径映射，例如本仓库的 `/static-pages/`；该值属于仓库配置，不写死进通用 builder。
- 在正式收录检查中核对新页面导航关系；预览不要求加入正式首页。
- CSS、JS 等非 HTML 文件变化同样触发完整正式 HTML 扫描。

当前 HTML 检查器不能证明所有外部 CSS、JavaScript 动态请求或 `srcset` 依赖正确。首版摘要应明确列出覆盖范围，间接资源检查和浏览器行为检查逐步补充，避免宣称已完成全部运行时资源验收。

### 6.3 基路径与两个站点位置

正式模式以 `docs/` 为站点根、站点项目路径为 base path。预览任务以自身 public 目录为资源根，优先相对链接，必要时使用完整的嵌套预览基路径检查。

同一任务在正式位置和 `/previews/pr-N/task/` 位置深度不同。指向正式首页的导航可按现有仓库约定使用完整站点 URL，避免用 `../../` 猜测深度。预览 HTML 自带的相对资源不能越出任务根；跨任务资源需要明确设计与部署支持，不能由 CI 静默当作存在。

### 6.4 Git blobs 与归档文件不能混称

Git 官方明确：`export-ignore` 会从归档省略文件，`export-subst` 会在归档时替换指定占位符。因此原始 Git 树中的文件列表、blob 哈希，不天然等于归档成员与字节。[G5：git archive](https://git-scm.com/docs/git-archive)

本仓库实际发布从 GitHub tarball 读取文件，R02 的源树检查必须明确标注来源。推荐与 R03 统一以下契约：

- 离线源树检查使用固定 `head_sha` 的原始路径、模式和字节。
- 对预览任务做本地归档与原始 blob 的成员、字节对照，发现影响任务的归档变换即阻止“源与预览一致”的结论。
- 获取实际 GitHub 归档的校验是独立阶段；未请求实际归档时，报告 `github_archive_equivalence: not_verified`，不能用本地 `git archive` 推导 GitHub 所有实现细节。
- 实际归档检查仍遵循发布器的根目录剥离、路径限制、任务识别和大小限制；发现差异先失败并报告，而非忽略缺文件或替换。
- `.gitattributes` 的相关变化强制进入此检查，即使 HTML 本身未变化。

R03 决定最终源哈希与归档证据格式后，R02 复用其公共函数和测试样例。发布器仍在可信 main 上对实际归档重新验证；候选检查不能替代部署端边界。

## 7. 拟议最小工作流

以下是**实现草案**。其中 `check_candidate.py`、`check_main_readiness.py` 尚不存在，不能直接部署此示例。Action 的完整 SHA 复用当前仓库已有固定版本，实施时核对其来源和适用 runner，不在本任务顺便升级依赖。

```yaml
name: Validate candidate

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, edited, ready_for_review]

permissions: {}

concurrency:
  group: candidate-${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  candidate:
    name: static-pages-candidate
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          ref: ${{ github.sha }}
          fetch-depth: 0
          persist-credentials: false
      - name: Validate selected candidate checks
        run: >-
          python3 scripts/check_candidate.py
          --event-path "$GITHUB_EVENT_PATH"
          --candidate-sha "$GITHUB_SHA"
          --output "$RUNNER_TEMP/candidate-validation.json"

  main-readiness:
    name: static-pages-main-ready
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          ref: ${{ github.sha }}
          fetch-depth: 0
          persist-credentials: false
      - name: Check the entire candidate tree for main
        run: >-
          python3 scripts/check_main_readiness.py
          --candidate-sha "$GITHUB_SHA"
          --output "$RUNNER_TEMP/main-readiness.json"
```

工作流内不使用分支名前缀、draft 状态或路径过滤跳过整个检查。新增提交可取消同 PR 的旧候选验证；发布工作流继续保留独立的串行组和不取消正在执行部署的策略。

该 YAML 只提供候选验证，不能直接作为 R01 方案 B 的完整预览生命周期调度源：示例未监听 `closed`，且 `branches: [main]` 可能漏掉 PR 改为以其他分支为 base 的清理事件。如后续接入 `workflow_run`，必须另设可信的关闭清理或定期对账入口；下游也不能只接受整个候选工作流 `success` 的结论，因为预览阶段的 `static-pages-main-ready` 预期失败，内容有效的页面仍应能够提供预览。可信调度器应重新核对当前 PR 状态与精确 head SHA，不执行上游候选代码，也不把候选验证结果当作发布授权。

合并冲突可能导致工作流无法产生，需在 PR 界面和操作说明中明确先解决冲突。若未来采用 merge queue，再增加并验证 `merge_group` 处理；当前不能只添加事件名而沿用仅支持 PR payload 的检查入口。[G1](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)、[G2](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

### 7.1 两个入口的最小职责

`check_candidate.py` 负责校验输入 SHA、确认对应对象、分类差异、选择检查、收集所有结果及输出摘要。它不执行提交、推送、合并、发布，也不运行被提交页面的构建脚本。

`check_main_readiness.py` 从完整候选 Git 树检查 main 禁项，不只检查 diff、不只看工作区或索引。任意分支的候选树存在跟踪的 `artifacts/` 文件都返回不就绪；空目录本身不属于 Git 文件。报告明确解释“仍处预览阶段，需迁移后才可合并”。

首版可将两个入口实现为一个模块的两个子命令，避免重复 Git 枚举代码；固定检查名称和运行职责保持分开。

### 7.2 输出与退出码

- JSON 记录 `base_sha`、`head_sha`、`tested_merge_sha`、检查类型、所检任务、失败原因和已知未覆盖项。
- 与 R03、R04 统一退出码：0 为所选检查通过，1 为检查失败（包括内容差异、规则不通过或运行不可用），2 为调用参数错误。对象缺失、超时、执行失败等由 JSON 的 `error_code` 分别记录为 `missing_object`、`timeout`、`execution_error`，不增加新的退出码。所有非零都使相应 job 失败。
- 检查报告输出到 `RUNNER_TEMP`；本地调试放 `scratch/`，不写回 public 或 docs。
- 路径与内容作为数据输出到 JSON，不能拼入 shell 命令、执行表达式或未转义地写入 GitHub 环境文件。
- 不向候选步骤提供部署环境、仓库秘密或写权限 token，不从候选缓存恢复可信发布执行内容。

## 8. 合并门禁的启用与局限

工作流成功运行并确认检查名称后，再由维护者按实际规则配置两个必需检查。工作流上线、检查产出、required checks 配置属于三个独立状态。

`static-pages-main-ready` 必须显式运行并对 artifacts 返回失败。不能用 `if: artifacts-empty` 跳过 job，因为官方语义允许 skipped 结果满足必需检查。两个 job 独立运行，避免其中一个失败导致另一个依赖 job 被跳过。

候选工作流和检查脚本本身也能在 PR 中被修改。因此这些检查首先是防止操作失误的工程门禁，不能自行证明用户发布授权，也不能被描述为对恶意工作流改动不可绕过。涉及工作流、检查器和发布约束的更改，需要按仓库实际支持的审阅与保护机制核查；不要仅凭同名检查报告成功就推导其实现未变化。

本次没有修改保护规则或 required checks。未来回滚时先处理对应必需检查配置，再删除或重命名 workflow/job，避免永久 Pending。

## 9. 预计改动清单

以下路径为实施建议，新增文件尚不存在：

| 文件或范围 | 改动 |
| --- | --- |
| `.github/workflows/validate.yml` | 新增独立候选工作流与两个固定检查 |
| `scripts/check_candidate.py` 或对应公共模块 | 差异分类、页面枚举、结果汇总，复用现有静态检查 |
| `scripts/check_main_readiness.py` 或子命令 | 完整候选树的 main 禁项检查 |
| `scripts/` 内最小公共辅助模块 | 仅在多个入口确实复用时抽出 SHA、Git 枚举与路径契约 |
| `tests/test_candidate_checks.py` | 真实临时 Git 仓库与文件产物的正、负例 |
| 现有发布器、检查器测试 | 保持既有边界并增加跨工具路径、归档契约用例 |
| `CONTRIBUTING.md`、相关 skill 引用 | 解释预览可用与合并就绪两个结果，列出新检查方式 |

正式发布工作流可以原样保留其可信 main 测试。候选检查使用的公共函数需要在测试中验证，不能为绕过 artifacts guard 而直接删除或放宽 `assemble()` 中的生产保护。

## 10. 验收与负例矩阵

| 场景 | Candidate | Main ready | 核心观察 |
| --- | --- | --- | --- |
| 仅修正文档 | 文档检查通过 | 通过 | 不触发页面制作或正式收录审批 |
| 普通分支新增 tracked artifacts | 静态结果按内容判断 | 失败 | 普通分支同样不能将草稿合入 main |
| 有效 preview PR，public 完整 | 通过 | 失败 | 预览仍可由可信流程展示，明确暂不可合并 |
| 迁移到 docs 并清理全部 artifacts | 通过 | 通过 | 不靠分支名猜测完成状态 |
| 候选脚本加入会破坏行为的修改 | 失败 | 独立判断 | 确实执行候选测试，而非 main 的旧版本 |
| 缺 html/head/body、带预览标记 | 失败 | 依目录判断 | 复用预览格式拒绝规则 |
| 缺 title、重复 ID、坏锚点或直接资源缺失 | 失败 | 依目录判断 | 检查器问题完整汇总 |
| 同 PR 有多个任务，一个缺入口 | 失败并列明 incomplete | 有 artifacts 则失败 | 不能只检查第一个或最新任务 |
| 删除整个任务 | 正确记录删除 | 依剩余树判断 | 不读取已删除入口 |
| 删除被其他正式 HTML 引用的共享资源 | 失败 | 依目录判断 | 扫描剩余 HTML，发现入链损坏 |
| 重命名页面或资源，含空格／中文文件名 | 按规范路径判断 | 依目录判断 | NUL 解析，旧新路径都覆盖 |
| 符号链接、gitlink、越界或不兼容特殊文件名 | 失败 | 正式源存在禁项则失败 | 不以读取解析后的文件替代 Git 模式检查 |
| `.gitattributes` 改变 public 归档成员或字节 | 失败并报告差异 | 独立判断 | 不把 blob 哈希等同实际归档 |
| 外部 CSS 间接字体或 JS 动态 URL 错误 | 首版不能保证发现 | 独立判断 | 摘要列明覆盖局限，另做运行时验收 |
| 工作流被路径条件跳过 | 工作流设计不采用该过滤 | 同左 | required checks 不因 docs-only 变更悬空 |
| PR 有合并冲突 | 官方事件可能不运行 | 同左 | 提示解决冲突，不能宣称检查通过 |
| 缺 Git 对象、测试超时或检查器崩溃 | 失败并给出运行错误 | 独立判断 | 不回退成跳过或 success |

新增测试使用临时目录和受控文件，不向真实远端写入。可选浏览器阶段单独测试无横向溢出、键盘操作和交互结果；未运行浏览器时只报告静态检查完成。

## 11. 实施步骤、依赖和回滚

1. **先实现本地入口和测试。** 验证候选 root、任务枚举、main 禁项、删除重命名与归档差异；保留现有生产脚本边界。
2. **再上线非强制候选 CI。** 用真实 PR 观察两个检查名称与版本，分别验证文档、脚本、预览、正式迁移案例。
3. **最后启用必需检查。** 按实际可见权限和仓库规则配置，确认有 artifacts 的普通分支也不能合入 main。
4. **后续补充检查范围。** 根据真实失败案例增加间接资源检查或隔离浏览器检查，避免首轮扩张为通用前端构建平台。

依赖关系：

- **R01**：提供发布触发机制的兼容性结论；候选验证保持独立低权限执行。
- **R03**：统一干净源、归档成员及确认版本的哈希口径。R02 只判断候选内容质量与 main 就绪，不推定发布授权。
- **R04**：线上校验负责目标提交和实际下载文件；候选检查通过不能代替正式部署验收。
- **R06**：后续用真实 Agent 任务检验是否正确理解两个检查结果，避免把 main-ready 失败误当成必须取消预览。

回滚时保留既有可信发布能力与本地检查命令。若新检查存在误报，先定位并修复分类或映射；确需临时撤销必需检查时记录原因和范围，再回滚工作流。禁止以放宽路径、大小或 source SHA 约束来消除错误。

## 12. 本次验证范围与未决事项

已完成：阅读相关源码与测试、官方文档联网核对、公开仓库及当前可见 main 保护规则只读查询、含 tracked artifacts 的临时测试、现有检查器覆盖边界实验。

未执行：新增工作流、真实 GitHub 候选 CI、浏览器验收、required checks 配置、页面预览或正式部署。没有修改业务代码、工作流、skill 或远端状态。

实施前仍需确定：

- 两个新增入口采用独立脚本还是同模块子命令，以及公共路径函数放置位置。
- 实际 GitHub 归档的额外预检由 R02 调用还是由可信发布前检查提供，如何限制请求与日志。
- 首版文档锚点检查的渲染器范围，以及外部链接是否进入可选定时检查。
- 主分支保护或规则集的实际可用配置与维护者操作方式。
- 是否已有 merge queue、工作流路径审阅要求或需保留的特殊分支规则；本次可见 API 结果不替代实施时核查。

## 13. 资料

仓库内依据：

- [项目说明](../../README.md)、[Agent 约定](../../AGENTS.md)、[操作与维护指南](../../CONTRIBUTING.md)。
- [现有工作流](../../.github/workflows/pages.yml)、[站点组合代码](../../scripts/build_pages.py)。
- [本地静态检查器](../../skills/static-page-builder/scripts/check_static_html.py)、[线上校验器](../../skills/static-page-publisher/scripts/verify_deployment.py)。
- [组合测试](../../tests/test_pages.py)、[检查器测试](../../tests/test_skill_checks.py)、[生成分支测试](../../tests/test_staging.py)。

官方资料，查询于 2026-11-21：

- [GitHub：Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)。
- [GitHub：Troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)。
- [GitHub：Workflow syntax／permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions)。
- [GitHub：Securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)。
- [Git：git-diff](https://git-scm.com/docs/git-diff)、[Git：git-archive](https://git-scm.com/docs/git-archive)。
