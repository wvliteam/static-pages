# R03：确认版本到正式版本一致性的实现调研

- 调研日期：2026-11-21。
- 仓库基线：`ee180b1e36d71b600f324ddbaa8d64e493862565`。
- 对应计划：[OPTIMIZATION_PLAN.md 中的 R03](../../OPTIMIZATION_PLAN.md)。
- 状态：实现方案，尚未实现比较器、迁移工具或远端发布检查。
- 调研范围：阅读现有发布代码、核对 Git／Python／GitHub 官方文档，并在忽略的 `scratch/r03-research/` 内运行隔离夹具试验。

## 1. 推荐结论

首版建设一个**只读的确认版本比较器**，提供迁移预演和迁移后核对两个模式。它比较的是“获确认预览使用的干净文件集合”与“明确选定状态的正式目标文件集合”，覆盖相对路径和所有文件字节。

推荐同时明确五个边界：

1. 确认依据仍是用户对具体版本的真实授权；比较器只产生一致性证据。
2. 以完整预览 SHA 固定确认源，以迁移后的候选提交固定提交结果，最终 main SHA 另外记录。
3. 预览源应来自同 SHA 的 GitHub 归档，经现有静态文件选择规则处理，不能直接假定 Git blob 就等于用户审阅的输入。
4. `worktree`、`index` 和 `commit` 是三种不同目标，必须在输入和结果中明确标注。
5. 第一个版本保持只读；复制、删除、暂存、提交和合并继续由发布流程执行，并在每个版本边界重新核对。

建议暂用仓库级工具 `scripts/compare_promotion.py` 承载实现，复用仓库静态产物规则。该路径与下文命令均为**拟议接口**。通用 publisher skill 调用仓库已提供的能力，不立即把本仓库假设扩散到所有安装环境。

## 2. 当前实现与缺口

| 环节 | 当前代码或约定 | 能证明什么 | 尚不能单独证明什么 |
| --- | --- | --- | --- |
| 获确认版本 | 发布约定记录预览 head SHA | 审阅指向一个具体提交 | 迁移后文件仍是该版本内容 |
| 预览输入 | `GitHub.archive(sha)` 下载源码归档，`archive_files()` 选择 public 文件 | 文件来自明确 SHA 的合格静态范围 | Git 原始树与归档输出必然相同 |
| 预览注入 | `preview_html()` 改写 robots 并注入横幅与样式 | 部署预览有可见状态标记 | 注入后 HTML 与干净源字节相同 |
| 正式迁移 | 在原 PR 分支移动 public 到 docs，并更新导航 | 人工或 Agent 可以完成迁移 | 所有资源和删除操作都保持范围正确 |
| 正式部署 | 复制 main 的 docs，记录正式文件哈希 | 本次部署实际输入与文件哈希对应 | 文件与此前用户批准源之间的关系 |

依据：[发布操作说明](../../CONTRIBUTING.md)、[站点组合脚本](../../scripts/build_pages.py)、[部署校验器](../../skills/static-page-publisher/scripts/verify_deployment.py)、[publisher skill](../../skills/static-page-publisher/SKILL.md)。

现有 `test_approved_move_does_not_publish_artifacts_from_main` 测试覆盖正式目录和草稿目录隔离，不检查真实确认 SHA 到目标文件的完整对应。后续应新增该行为测试，而不是把已有测试名称解释为审批或一致性已自动验证。[现有测试](../../tests/test_pages.py)

## 3. 必须区分的三个版本与三种字节

### 3.1 版本关系

| 标识 | 含义 | 变化规则 |
| --- | --- | --- |
| `approved_preview_sha` | 用户确认的预览源提交 | 固定，不能随当前 PR head 自动替换 |
| `candidate_sha` | 迁移后等待合并的候选提交 | 移动目录、改导航等会产生新提交 |
| `deployed_main_sha` | 实际正式部署采用的 main 提交 | 合并策略可能使其不同于候选提交 |

三个提交可以不同。正确条件是：选定正式目录内容与获确认的干净文件集合对应，且之后部署的正式文件又与目标 main 对应；不能把三者 SHA 必须相同作为判断标准。

### 3.2 字节关系

| 集合 | 建议名称 | 用途 |
| --- | --- | --- |
| 归档中、预览注入前的合格文件 | `approved_clean_files` | R03 的确认源比较基准 |
| 横幅等注入后的预览文件 | `preview_generated_files` | 现有 manifest 的预览哈希及线上预览验收 |
| main/docs 实际交付的正式文件 | `production_files` | 正式 manifest 与 R04 完整资源验收 |

对 HTML，第一组与第二组通常不同。R03 不从线上下载横幅页面再“去掉标记”重建确认源；逆向删除容易误删正文或忽略部署变换。

R03 的内容树摘要应命名为 `clean_tree_sha256` 或同等明确名称，不能覆盖现有 manifest 中注入后文件的 `sha256` 字段。R04 可以保留原有字段兼容性，新增源信息时另行定义可选字段。

## 4. 关键调研发现：Git 原始树不一定等于预览输入

GitHub 官方说明，源码归档由 `git archive` 生成。Git 的 `export-ignore` 会移除归档成员，`export-subst` 会替换归档文件中的占位符。因此，仅从 `git ls-tree` 和 `git cat-file` 取原始 blob，不能充分证明取到了此前预览的干净输入。[GitHub 源码归档说明](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives) · [Git archive 属性](https://git-scm.com/docs/git-archive)

本次隔离试验已实际复现：原始 public 树有 5 个文件，归档经当前 `archive_files()` 读取后有 4 个文件；一个被 `export-ignore` 排除，另一个 `$Format:%H$` 被替换为提交 ID。

此外，`text`、`eol` 等属性可能使 checkout 文件字节与 Git blob 不同。试验中，LF blob 被 checkout 为 CRLF。本方案因此不对内容做换行、空白、编码或 JSON 格式“归一化”后再宣布相同。[Git attributes](https://git-scm.com/docs/gitattributes)

### 4.1 首版处理建议

1. 从已指定仓库、完整确认 SHA 的 GitHub 归档读取源，复用当前 `archive_files()` 的静态选择与限制。
2. 同时用本地 Git 对象读取确认提交中的原始 public 文件，作为源类型、模式及归档变换诊断。
3. 首版仅支持原始 public 文件集合和归档有效集合的相对路径、字节完全相同的普通静态任务。
4. 如果两者不一致，返回 `unsupported_source_transform`，列出差异；不自动忽略或复制被变换后的集合。
5. 如果确认 Git 对象在本地缺失，返回 `source_objects_unavailable`，不将其解释为内容变化，也不隐式 fetch、checkout 或改写本地仓库。

这套限制使首版能可靠支持当前常见的干净静态页面迁移。后续若确有 `export-subst` 等需求，应单独设计“按归档有效字节物化”的发布方式，明确它与 `git mv public docs` 的差异并补齐测试。

本基线受版本管理的文件中未见 `.gitattributes`。这只是本地仓库观察，不排除本机 Git 配置和未来提交引入变换。比较器始终读取实际结果，不依赖“当前没有属性文件”的长期假设。

## 5. 备选方案比较

| 方案 | 收益 | 缺口或代价 | 建议 |
| --- | --- | --- | --- |
| 仅人工检查迁移 diff | 无新增工具 | 容易漏二进制、额外文件与暂存状态 | 保留人工审阅，增加确定性比较 |
| 仅比 HTML 文本 | 易实现 | 漏掉图片、JS、CSS、数据和删除 | 不作为完成证据 |
| 直接比较 Git 子树 OID | 对原始 Git 树高效 | 模式会影响树 ID；归档变换与 checkout 可能不同 | 用作诊断，不作唯一判断 |
| 从确认归档比较全部干净文件 | 与现有预览输入语义一致 | 需要固定 SHA 的源读取及明确文件范围 | 推荐作为比较主线 |
| 首版直接加入自动迁移、提交与合并 | 一次调用完成更多步骤 | 额外引入覆盖、删除、授权与恢复复杂度 | 先做只读 plan/check，后续按需要增加写操作 |
| 新建签名、审批机器人与完整证明系统 | 可支持复杂跨组织信任 | 当前尚无对应使用需求 | 继续使用真实授权记录与版本证据 |

## 6. 推荐工具结构与数据读取方式

### 6.1 最小模块

- `source_reader`：固定仓库和确认 SHA，读取归档有效字节；读取 Git 原始对象作一致性诊断。
- `target_reader`：按明确模式读取 worktree、index 或候选 commit。
- `manifest_builder`：验证相对路径和类型，生成文件哈希及内容树摘要。
- `comparator`：生成缺失、额外、内容变化、类型错误及模式差异。
- `planner`：只读地列出计划复制、保留、删除和需要进一步人工判断的目标。
- `reporter`：输出稳定 JSON；人类摘要写 stderr 或另选格式，避免混入机器 stdout。

这些可以先放在一个较小脚本中，只有出现实际复用时再拆模块。复用现有规则时，使用仓库可信或低权限候选环境内的代码，不在高权限流程导入任意 PR 提供的帮助脚本。

### 6.2 源提交读取

- 确认 SHA 接受当前仓库现有的完整 40 位小写十六进制格式；不接受短 SHA、分支名或自动跟随的 PR head。
- 用 `git rev-parse --verify --end-of-options <sha>^{commit}` 检查本地对象，单独确认对象类型。
- 使用 `git ls-tree -r -z --full-tree` 得到类型、模式、OID 与完整路径，用 NUL 拆记录，首次 TAB 拆元数据和路径。
- 对 blob OID 使用 `git cat-file blob <oid>` 或按大小解析的 batch 读取原始字节；不使用 `--filters`、`--textconv` 或跟随符号链接。
- 参数用进程参数数组传递，不把路径和 SHA 拼到 shell 字符串中。
- 尽可能在干净的 Git 读取环境禁用 replace refs 和隐式 lazy fetch；发现需要下载的对象时明确报源不可用，由调用方决定如何准备对象。

NUL 输出和 `--full-tree` 可避免工作目录影响及含空格、TAB、换行路径的解析问题；`cat-file` 的过滤选项会显式改变内容，应与原始字节读取区分。[Git ls-tree](https://git-scm.com/docs/git-ls-tree) · [Git cat-file](https://git-scm.com/docs/git-cat-file) · [Git rev-parse](https://git-scm.com/docs/git-rev-parse)

### 6.3 目标状态选择

| 状态 | 数据来源 | 典型用途 | 需要额外报告的事项 |
| --- | --- | --- | --- |
| `worktree` | 明确目标目录内实际普通文件 | 迁移后本地核对 | 所有额外文件，包括未跟踪和被忽略文件；相关未暂存变化 |
| `index` | `git ls-files --stage -z` 的 stage 0 条目与 blob | 提交前核对暂存内容 | 未合并 stage 1/2/3、intent-to-add、源草稿残留、worktree 与 index 不一致 |
| `commit` | 固定候选提交的目标子树 | 推送、合并前和 main 上再次核对 | 候选完整 SHA、相对 main 的变更范围、相关草稿是否仍存在 |

Git 官方明确区分索引、工作区和提交树。`--cached` 比较不读取工作区文件；因此不能把 index 通过写成“本地文件也已通过”。[Git diff-index](https://git-scm.com/docs/git-diff-index) · [Git ls-files](https://git-scm.com/docs/git-ls-files)

首版建议要求显式传入目标状态。`worktree` 比较可以发现未跟踪额外文件；`index` 和 `commit` 比较只声称覆盖其明确状态，不把不在该快照中的本地文件算作已提交。

## 7. 文件范围、路径和类型规则

### 7.1 路径映射

源根固定为 `artifacts/<task>/public/`，目标根限制为任务对应的 `docs/reports/<symbol>/<date>/`、`docs/pages/<slug>/` 或 `docs/tools/<slug>/`。除根前缀映射外，相对路径一一对应。

- 目标不能是整个 `docs/`、其他任务父目录或部署保留目录。
- 使用分段前缀判断，不能用 `startswith('docs/pages/demo')` 误包含 `docs/pages/demo-other`。
- 要求非空 `index.html` 和明确文件清单；目录本身和空目录不参与内容摘要。
- 不做大小写折叠或 Unicode 归一化。无法在目标平台无损表示的路径应报告，而不是自动改名。
- 对原始路径先验证再构造规范路径，避免 `PurePosixPath` 自动折叠 `.` 等成分后掩盖原始异常。
- 路径公共规则应与发布器及校验器对齐：拒绝绝对路径、越界段、反斜杠、URL 式参数及无法验证的编码；`%`、隐藏文件等已有组件差异应明确统一，不能由比较器自行放宽。
- 首版可以拒绝控制字符和非法 UTF-8，并报告具体不支持原因。NUL 解析仍然必要，不能因为后续会拒绝某类名称而使用不可靠的按行拆分。

### 7.2 类型与模式

- Git `100644`、`100755` 且类型为 blob 的普通文件可以进入内容比较。
- `120000` 符号链接、`160000` gitlink/submodule 和其他特殊类型明确拒绝，不跟随或递归进入。
- 工作区读取使用 `lstat` 或 `stat(..., follow_symlinks=False)` 分类，拒绝目录链接、FIFO、socket、设备文件等。
- 内容摘要包含相对路径和字节；Git 可执行位单独报告。普通静态文件 `100644` 与 `100755` 字节相同可以标记 `content_equal=true`、`metadata_equal=false`，不声称源 Git 树完全相同。
- 如仓库未来要求统一静态文件可执行位，应作为单独明示规则，不把本机文件系统模拟出的权限当作用户内容变化。

Python 的跟随链接选项和部分 `O_NOFOLLOW` 能力受平台支持限制。worktree 读取应检测实际能力；不支持时降级为明确的预检查加读前后检查，不宣称已经消除并发替换风险。[Python os](https://docs.python.org/3/library/os.html)

### 7.3 已有目标、删除与共享资源

- 新增页面：预演展示所有拟新增文件；目标已有文件时报告冲突，不能按“新增”静默覆盖。
- 更新已有页面：要求指定完整的目标任务目录及已固定的 main 基线；展示覆盖和删除清单。
- 目标中确认源没有的文件，在 `check` 中均为 `extra`；不能用忽略规则让旧 JS 或数据文件继续留在正式目录。
- 预演只列出删除建议，不执行删除。调用方确认这些路径属于本任务既有授权范围后，再按发布流程处理。
- `docs/index.html` 和根 README 的导航调整单独列入范围核对，不能要求它们与 public 树相同，也不能把其他正文变化隐藏在导航例外中。
- 首版要求可交付资源位于本任务树内。相对引用外部共享目录的页面，需要把被审阅的共享资源版本和范围明确列入方案；未建模时返回依赖不完整，不声称整页已证明一致。
- 同一 PR 多个任务逐项比较，目标根不得重叠。不能为了满足 main 无 artifacts 的要求，删除同 PR 中尚未确认任务的文件；应继续审阅或拆分任务。

## 8. 拟议 CLI、JSON 与退出码

以下命令只说明拟议接口，仓库当前没有该脚本。

```text
python3 scripts/compare_promotion.py plan
  --repository wvliteam/static-pages
  --approved-sha <完整确认提交>
  --task <任务名>
  --target docs/pages/<页面名>
  --base-main-sha <固定main基线>
  --output scratch/<任务名>-promotion-plan.json

python3 scripts/compare_promotion.py check
  --repository wvliteam/static-pages
  --approved-sha <完整确认提交>
  --task <任务名>
  --target docs/pages/<页面名>
  --target-state commit
  --candidate-sha <完整候选提交>
  --output scratch/<任务名>-promotion-check.json
```

`plan` 的结果是拟执行范围，不表示尚未移动的目标已经等于确认源。`check` 才对明确目标快照给出相等或不等结论。两个模式均不 fetch、checkout、移动文件、删除、暂存、提交、推送或合并。

建议 JSON 契约：

| 字段 | 建议语义 |
| --- | --- |
| `schema_version` | 初版固定为 1，后续兼容性变化显式升级 |
| `operation` | `plan` 或 `check` |
| `status` | `planned`、`equal`、`different`、`invalid_input`、`unavailable`、`unstable_target` |
| `repository` | 确认源所属仓库，不从任意归档内容自行推断 |
| `source` | 确认 SHA、任务、读取方式、文件数、总大小、干净内容树摘要 |
| `target` | 目标根、状态类别、固定候选 SHA 或本地快照摘要 |
| `scope` | 固定 main 基线、目标映射及必要导航变更范围 |
| `comparison` | `content_equal`、类型与模式结果、按路径的 missing/extra/changed |
| `planned_actions` | 仅 plan 使用，区分新增、覆盖、删除与需要处理的冲突 |
| `diagnostics` | 归档变换、对象缺失、未合并索引、目标不稳定等机器可读代码 |
| `authorization_reference` | 可选的真实确认记录引用；工具不由此自行判定授权成立 |
| `checked_at` | 观察时间；不用于替代版本身份 |

建议沿用现有检查器的退出码习惯：`0` 表示对应操作完整成功，`1` 表示检查未通过，`2` 表示 CLI 参数或用法错误。内容不同、源不可用、策略拒绝和目标读取期间变化均以非零结果返回，并在 JSON 的 `status`、`diagnostics[].error_code` 中区分；调用方不能把它们统一当作“文件不同”。plan 返回 0 仅代表计划成功生成且没有未处理冲突，不能作为 check 相等结果复用。

报告默认写 stdout。若指定 `--output`，必须位于公开产物树之外，写入失败返回失败；正常文件差异也应尽量输出完整诊断，不能只给 traceback。

## 9. 内容树摘要建议

使用与 Git OID 分离的 SHA-256 内容摘要，便于归档、文件系统、索引和提交之间比较。[Python hashlib](https://docs.python.org/3/library/hashlib.html)

拟议 `static-pages-content-tree-v1` 算法：

1. 每个条目为 `(UTF-8 相对路径, 文件长度, SHA256(原始字节))`，仅接受前述通过验证的普通文件。
2. 按相对路径的 UTF-8 字节顺序排序，不按本地 locale 排序。
3. 先输入固定域分隔字节 `static-pages-content-tree\0v1\0`，再输入 8 字节大端文件数量。
4. 对每个条目，依次输入 8 字节大端路径长度、路径字节、8 字节大端文件长度、32 字节文件 SHA-256 摘要。
5. 对完整字节序列计算 SHA-256，输出小写十六进制。

根目录前缀、时间戳、绝对路径、提交作者和 Git 可执行位不进入内容摘要，类型和模式另列证据。长度前缀避免直接字符串拼接产生字段边界歧义；显式版本便于未来演进。

逐文件比较和清单仍需保留。不能仅输出一个整体摘要，使执行者无法找到差异。摘要相等证明的是指定文件集合按该算法一致，不证明用户授权、页面结论正确或线上实际部署成功。

## 10. 竞态、版本漂移与闭环

1. 读取开始时解析并固定所有提交，之后不重新把分支名解析成新的目标。
2. worktree 模式记录读前后文件属性和目录清单；读取期间替换、文件增删或大小变化时返回 `unstable_target`，不发布部分通过结果。
3. 支持的平台可用目录描述符和不跟随链接的打开方式降低替换风险；这些方法仍不能为任意并发写入提供全局原子快照。
4. index 模式读取并核对索引前后状态，拒绝非 stage 0 或未解析条目；不能仅信任 mtime 或 `git status` 的干净结论。
5. 本地检查后提交候选版本，再对该固定 commit 运行 check。提交前后差异不自动继承通过结果。
6. 推送后核对远端 PR head；如果又有新提交，使用明确的新候选重新比较，确认源 SHA 仍保持原值。
7. 合并后对最终 main 的任务树再核对；合并冲突处理或其他同路径修改可能改变内容。
8. 最后交由 R04 将实际部署的 main、manifest 和线上正式资源字节闭环核验。

某次 worktree/index 通过只对当时观察结果有效。冻结候选 commit 能为后续读取提供稳定对象，但不能保证未来 main 合并结果或部署目录完全相同。

## 11. 本次已执行的隔离试验

环境：Git 2.53.0、Python 3.15.2。试验脚本与原始 JSON 仅保存在忽略的 `scratch/r03-research/`，没有进入公开内容或修改主仓库代码。

| 试验 | 实际结果 | 对方案的影响 |
| --- | --- | --- |
| 根前缀改变、有效相对路径与字节不变 | 内容树摘要相同，提交 SHA 可以不同 | 摘要不包含根前缀和提交身份 |
| export-ignore / export-subst | 原始 5 文件变成有效 4 文件，stamp 内容也变化 | 不能只比较原始 Git blob |
| index 与 worktree 分离 | index 二进制仍等于确认版，worktree 已修改 | 结果必须标注目标状态 |
| 目标增加未跟踪文件 | 文件系统存在，普通 ls-files 不列出 | worktree 完整扫描必须包含额外文件 |
| eol=crlf checkout | blob 为 LF，checkout 字节含 CRLF | 不以逻辑文本一致代替字节一致 |
| NUL 枚举特殊文件名 | 换行文件名可完整读取 | 先可靠解析，再按策略拒绝 |
| Git 类型与模式读取 | 链接为 120000，可执行普通文件为 100755 | 类型检查与内容比较分开 |
| 清单枚举顺序变化 | 摘要不变 | 使用确定排序 |
| 相同文件改名 | 摘要改变 | 路径是内容集合身份的一部分 |

这些试验只验证读取原理和拟议摘要算法，不是正式比较器测试，也没有运行迁移、远端合并或正式部署。

## 12. 实施文件与回归矩阵

### 12.1 拟议文件变更

| 位置 | 变更内容 |
| --- | --- |
| `scripts/compare_promotion.py` | 新增仓库级只读 plan/check 工具 |
| `tests/test_promotion.py` | 新增真实 Git 夹具、归档与目标状态测试 |
| 现有发布文件选择逻辑 | 按需要提取或复用可信规则，保持已有校验约束 |
| `skills/static-page-publisher/SKILL.md` | 增加何时调用仓库比较工具及如何解释结果 |
| publisher 的相关 references | 描述确认源、候选版本与部署字节边界 |
| `CONTRIBUTING.md` | 增加迁移预演、候选提交核对和失败处理说明 |

### 12.2 必须覆盖的行为

- 正常新建任务迁移、现有任务更新、仅目录前缀变化。
- HTML、CSS、JS、图片、二进制数据任一变化；文件新增、删除和重命名。
- 目标额外文件、未跟踪与被忽略文件；不同 target-state 的准确范围。
- 符号链接、gitlink、特殊文件、错误任务名、保留目录和越界映射。
- 空格、中文和非法路径；大小写或 Unicode 不可表示冲突不被静默改名。
- 归档导出变换被明确拒绝；源对象缺失、归档请求失败与真实内容差异区分。
- 未合并索引、intent-to-add、部分暂存、扫描中变更和推送后 head 改变。
- 多任务根重叠、共享资源未建模、非本任务文件变化。
- 迁移后仍有跟踪 artifacts；无 artifacts 后预览已消失但确认 SHA 仍可使用。
- 合并后目标树被冲突处理改变；正式 hash 校验不能代替确认源比较。
- 所有模式不修改工作区、索引、引用、远端或公开文件。

## 13. 实施次序、回滚与待决策

### 13.1 分阶段实施

1. 先固定 source/target/file-manifest/diagnostic 契约，以只读库函数实现清单和差异。
2. 增加 plan/check CLI 与临时 Git 仓库回归测试，保留现有人工发布路径。
3. 在 publisher 流程中试运行，先以报告方式检查正常迁移和已知负例。
4. 将提交态 check 接入 R02 的适当低权限检查；如何选择真实确认源仍由真实授权流程提供，不从 PR 任意字段自动赋权。
5. 配合 R04 记录最终 main 和线上文件闭环，再按实际需要扩大批量、多仓库或写入能力。

### 13.2 回滚

首版只读工具不会自行产生文件迁移。工具回滚可撤销调用入口与对应代码，保留已产生的诊断记录；原有授权、迁移 diff 检查和正式校验流程继续适用。实际内容发布若已发生，按仓库现有定向 revert/新提交流程处理，不改写共享 main 历史。

### 13.3 实施时需要决定

- 同 SHA 归档下载与本地源对象的准备方式，以及缓存保留位置；缓存仍需按内容和来源核对。
- 是否采用本文的首版归档变换拒绝策略；若支持物化变换，需先单独定义其行为。
- 路径公共验证如何在发布器、比较器和线上校验器间复用。
- 普通静态文件可执行位差异是信息项还是额外项目规则。
- 更新现有目标时，如何明确目录归属与允许的导航变更范围。
- 真实授权引用如何以合适方式留存；不要将任何新状态字段解释成自动批准。
- 是否把后续可复用的比较逻辑下沉到 publisher 技能包；首版以仓库规则正确为先。

## 14. 与其他优先任务的交接

| 对接项 | R03 提供 | 对方负责 |
| --- | --- | --- |
| R01 | 确认提交、候选提交、main 三者身份必须分离 | 工作流触发和部署权限保证可信执行 |
| R02 | 固定候选提交 check、退出码和测试夹具 | 低权限候选检查，不能执行高权限 PR 自带校验器 |
| R04 | `approved_clean_files` 身份及内容一致性证据 | 对目标 main 和正式线上所有所选资源进行核验 |
| R05 | 可机器读取的源、目标和失败诊断 | 任务恢复，不把旧报告直接视为新版本通过 |

本调研推荐先完成只读比较与固定版本核对。它补齐的是确认源到正式候选的证据链，与用户授权、内容质量检查和实际部署验收共同构成交付闭环。
