# R01：发布事件策略兼容性与可信触发方案调研

- 调研日期：2026-11-21。
- 对应计划：[OPTIMIZATION_PLAN.md](../../OPTIMIZATION_PLAN.md) 中 R01，与 R02 的候选代码 CI 联动。
- 代码基线：本地 `main`，`ee180b1e36d71b600f324ddbaa8d64e493862565`。
- 工作范围：读取本地实现、查询官方资料和实际仓库配置，形成实施方案；未修改工作流、仓库策略、部署环境，未触发线上运行。
- 文档中的新增流程和配置均为拟议方案，实际采用前需要按本节验收。

## 1. 结论与推荐顺序

1. **2026-12-02 的政策节点有当前官方依据。** GitHub 当前文档说明，将对适用公共仓库强制执行默认 `pull_request_target` 事件限制；适用性取决于已有事件策略，不能扩大解释为所有仓库在同一天一律停用该事件。[S1][S2]
2. **仓库实际策略 API 可以读取，但返回空列表。** 本次以现有认证执行只读查询，`has_parents=true` 返回 `total_count=0`。这说明该响应没有列出适用策略；它不能证明平台默认策略不会在之后适用，也不能证明某个未暴露的默认策略当前处于何种状态。
3. **近期最小方案是保留可信 main 组合站点，核实并配置适用的窄范围事件规则。** 现有实现没有执行 PR 脚本，符合其选择 `pull_request_target` 的主要前提；需要解决事件许可和候选验证分工，无需为了验证 PR 脚本而将 PR head 检出到发布 job 中。
4. **若实际管理规则不允许继续使用该事件，采用低权限 PR 工作流加可信 `workflow_run` 重建作为自动化备选。** 下游重新查询当前 main 与全部合格 PR，不执行、导入上游的脚本或安装包，不将上游成功等同于页面正式批准。
5. **保留现有 `workflow_dispatch --ref main` 作为可操作的恢复入口。** 在事件策略未核实或迁移期间，它可以提供明确的人工重建路径；是否补充周期性重建，应按所需清理时效单独决定。

上述建议以当前单一统一站点、同仓库 PR、公开静态预览为前提。PRT 下文指 `pull_request_target`。

## 2. 当前实现和实际配置

### 2.1 代码中已经成立的行为

| 项目 | 当前实现 | 对方案的约束 |
| --- | --- | --- |
| 触发事件 | main 的 `push`；面向 main 的 PRT；`workflow_dispatch` | 应保持正式更新、预览变化和手动恢复三类入口 |
| PRT 活动类型 | `opened`、`synchronize`、`reopened`、`closed`、`edited` | 不能在迁移时只保留新建和推送，遗漏关闭清理 |
| PRT job 筛选 | 同仓库，head 分支以 `preview/` 开头 | fork 和普通分支不会作为当前事件的发布入口 |
| 执行代码 | checkout 明确使用 `ref: main`，不保留 Git 凭据 | 候选测试应独立，不将 PR head 改为发布执行源 |
| 预览资格 | 打开的同仓库 PR，base 为 main，head 为 `preview/` 前缀 | 资格由可信脚本重新判断 |
| 文件读取 | 按 PR head 的完整 40 位 SHA 下载归档 | 内容不能按可变分支名或上游 artifact 代替 |
| 站点生成 | main/docs 加全部合格活动 PR，生成版本和哈希记录 | 每次执行都是当前源集合的完整重建 |
| 发布锁 | 全工作流固定 concurrency group，`cancel-in-progress: false` | 所有发布入口应共用同一把锁 |
| build 权限 | `contents: write`、`pull-requests: read` | 写权限用于保存生成的 gh-pages；不应传给候选代码测试 |
| deploy 权限 | `pages: write`、`id-token: write`，使用 github-pages 环境 | 上传与官方部署仍在同一次 workflow 中完成 |

本地依据：[pages.yml](../../.github/workflows/pages.yml)、[build_pages.py](../../scripts/build_pages.py)、[stage_pages.py](../../scripts/stage_pages.py)。

### 2.2 实际 GitHub 只读查询结果

本轮查询时间约为 2026-11-21 13:59–14:00 UTC，即北京时间 21:59–22:00。以下为已脱离身份信息的必要配置摘要。

| 查询项 | 实际返回 | 可得结论和限制 |
| --- | --- | --- |
| 仓库元数据 | public；默认分支 main；owner 类型 User | 当前是个人账号所属的公共仓库，不应假设存在某个组织策略 |
| Actions 总开关 | `enabled=true`，`allowed_actions=all` | Actions 可用；这是 action 允许范围，不能代替事件策略查询 |
| 仓库级 SHA 固定要求 | `sha_pinning_required=false` | 仓库没有通过该配置强制固定 SHA；现有 workflow 的 action 仍明确固定了 SHA |
| 默认 workflow token | `default_workflow_permissions=read` | job 显式声明仍可申请其所需权限；不能据此称所有 job 均只读 |
| 自动批准审阅 | `can_approve_pull_request_reviews=false` | 此配置不构成用户页面确认机制 |
| Pages | `build_type=workflow`，状态 built，HTTPS enforced | 当前使用 Actions 发布；响应含 source 字段并不表示改为分支构建 |
| github-pages 环境 | custom branch policies | 环境确有分支限制 |
| 环境分支列表 | main 和 gh-pages，两条 branch 规则 | 当前不能描述成“环境只允许 main”；本轮没有调整它 |
| Actions policies | HTTP 成功，`total_count=0`、`policies=[]`，请求含 `has_parents=true` | 没有可进一步读取详情的策略 ID；默认政策的实际命中情况仍需 UI 或平台可见信息核实 |
| Repository rulesets | 成功返回空列表，请求含 `includes_parents=true` | 本次没有读取到规则集，不应假定某个 required check 已强制启用 |
| main 分支保护 | HTTP 404，正文明确为 `Branch not protected` | 该具体响应指向传统分支保护未启用；一般的 404 不能据此推论其他资源或策略也不存在 |
| Pages workflow 元数据 | active | 当前 workflow 没有被禁用 |

原始配置摘要与查询状态保存在忽略目录 `scratch/research-r01-2026-11-21/`。它们是本次调查记录，不作为需要发布的站点文件；未保存 token 或登录账号资料。

### 2.3 历史运行只能证明什么

查询到最近一次成功运行是 2026-11-20 的 main push，head 为分析基线；另有同日成功的 PRT 运行。它们证明这些历史事件曾执行成功，不能证明未来策略允许，也不能单独证明当前浏览器读取内容与该运行一致。

本轮未发起新运行、未创建测试 PR、未执行线上文件哈希验收。

## 3. 官方规则核查

### 3.1 默认 PRT 事件限制

GitHub 的安全说明、Actions policies 概念页和执行控制页均列出了 2026-12-02 这一节点。安全说明还限定：默认策略面向没有已有适用事件策略的公共仓库，不替换已有适用策略；当前说明中该默认策略处于评估阶段。[S1][S2][S3]

因此，本仓库需要完成的判断链是：

1. 仓库属于公共仓库：已由 API 核实。
2. API 列出的适用策略：当前为空。
3. 平台是否已经为该仓库设置默认策略、是否会在节点后命中：本轮 API 响应不能直接证明。
4. 若保留 PRT，是否能够通过适用范围正确的事件规则继续使用：需要读取实际管理界面和策略效果，再实施、验收。

这里不能把 `allowed_actions=all`、过去运行成功或者空策略列表当作豁免证明。

### 3.2 事件和权限的两条独立边界

- 事件策略控制某类事件能否启动目标 workflow。
- `permissions` 控制运行中的 `GITHUB_TOKEN` 可访问哪些仓库能力。[S3][S6]

允许 PRT 事件，并不授权执行 PR 代码；保持 token 只读，也不一定解决事件被策略阻止的问题。实施时应分别验证这两层。

### 3.3 当前可复用的信任设计

PRT 使用默认分支上下文；普通 `pull_request` 运行候选合并上下文。前者适合可信调度和静态读取，后者适合低权限候选测试。`workflow_run` 可在上游完成后运行默认分支中的下游定义，并获得其显式申请的权限，因此下游必须重新建立输入信任边界。[S1][S4]

本方案选择保留“可信代码决定发布、候选文件仅为静态输入”的约束，不以事件名称本身作为安全证明。

## 4. 可选方案比较

| 方案 | 工作方式 | 优点 | 代价和限制 | 建议 |
| --- | --- | --- | --- | --- |
| A：保留可信 PRT | main 的 PRT 发布流程继续重建全部源，核实窄范围事件规则；R02 单独验证 PR | 改动最小；不依赖候选测试成功；PR 冲突时仍可响应 | 需要确认实际策略允许；仍须处理遗漏事件后的清理 | 近期首选，条件是实际策略可合法配置并验证 |
| B：低权限 PR 加可信 workflow_run | PR 工作流完成后通知 main 下游重新查询全部合格 PR | 自动化预览可脱离 PRT；复用 R02 的候选运行 | 链路更长；候选工作流被删、过滤或 PR 冲突可能没有通知；需要兜底 | PRT 不可用且仍需自动预览时采用 |
| C：main 手动或周期重建 | 由已授权发布操作调用现有 main dispatch；可按需增加 schedule | 可信入口明确；恢复路径简单；无需新服务或长期密钥 | 手动步骤更多；周期调度有延迟，不能承诺即时响应 | 迁移期间恢复方案，也可作为 A/B 的对账兜底 |
| D：直接把发布改为 pull_request | 在候选工作流中授予写入和部署权限 | 表面改动少 | 候选定义或代码与发布权限耦合，破坏现有信任边界 | 不采用 |
| E：直接从 preview push 发布 | 由预览分支上的 workflow 触发整站部署 | 推送响应直观 | 执行源来自预览分支；关闭/改 base 也没有对应 push 保证 | 不采用此种直接部署形态 |

上表中方案 A/B 的分析是对本仓库的工程判断。周期调度、PR 冲突、workflow_run 的行为限制以官方事件文档为依据。[S4]

## 5. 方案 A：最小实施设计

### 5.1 先完成实际事件许可判断

只读入口已验证可用：

```bash
gh api --method GET \
  'repos/wvliteam/static-pages/actions/policies?has_parents=true&per_page=100'
```

当前空列表无需进一步分页；未来列表增大时应完整读取。API 官方说明 `has_parents` 默认包含更高层级的适用策略，权限和资源可见性仍需按实际响应判断。[S5]

若界面中显示默认评估策略，应查看 Policy insights，核实是否命中 `.github/workflows/pages.yml`。若无法获取 insights，记录该限制，不能写成“已排除影响”。

若实际需要保留 PRT 并可以按官方机制配置规则，拟议目标为：

- 作用范围限定到 Pages 发布 workflow，避免无关扩大其他工作流范围。
- 允许该流程实际需要的 `push`、`pull_request_target` 和 `workflow_dispatch`；采用 schedule 时再纳入它。
- 其他层级存在显式限制时，先确认规则组合效果；不假设仓库级规则能覆盖上层禁止。
- 不全局关闭保护，也不为了完成此项顺便扩大 token 默认权限。

具体策略 ID、API 请求体与界面操作以实施时的真实对象为准，本调研没有创建或修改策略。

### 5.2 保持 job 权限和执行源

| 运行单元 | 执行代码来源 | 数据输入 | 必要权限 | 不承担的任务 |
| --- | --- | --- | --- | --- |
| R02 候选验证 | 候选 head 或合并结果，由该项明确记录 | PR 文件 | 初始只给 `contents: read`；其他只读权限按实际需要增加 | 发布、保存 gh-pages、申请生产 OIDC |
| trusted build | 本次明确检出的 main 提交 | main/docs、API 当前 PR 列表、精确 head 归档 | 当前 `contents: write` 用于保存快照，`pull-requests: read` 用于查询 | 执行 PR 构建脚本或页面 JS |
| trusted deploy | 主流程的可信定义和已组合产物 | 同次运行上传的完整站点 | `pages: write`、`id-token: write` | 检出或测试 PR 代码 |

保留当前 action 的完整 SHA 固定、`persist-credentials: false` 和单次 workflow 上传加部署方式。

对于手动入口，操作命令保持 `--ref main`。可以增加 main ref 条件防止误操作，但单独在可变候选 YAML 中写一个条件，不能作为抵御恶意 workflow 修改者的完整边界。当前仓库没有读取到 main 保护与规则集，方案的可信 main 前提仍包含对拥有写权限协作者的信任。

环境当前允许 main 与 gh-pages。是否收窄为 main，应先审计是否有其他实际使用者；这不是让本次事件兼容性生效的必要前置，不能在调研中静默修改。

### 5.3 事件覆盖与清理

| 事件或状态变化 | 推荐处理 | 需要核对的结果 |
| --- | --- | --- |
| main push | 重建正式内容和全部合格预览 | main_sha 与检出的 main 一致 |
| 合格 PR opened / reopened | 重新查询源并重建 | manifest 出现对应 PR 的精确 head |
| 合格 PR synchronize | 使用查询到的当前 head，不直接信任旧事件 SHA | 新预览哈希匹配 manifest |
| PR closed，未合并 | 重建完整集合 | 该 PR 预览移除，其他 PR 和正式内容保留 |
| PR merged | main push 与 closed 均可触发，允许冗余但共用锁 | 正式内容更新且旧预览移除 |
| PR base 从其他分支改到 main | 按编辑事件和当前资格重查 | 新合格预览被收录 |
| PR base 从 main 改到其他分支 | 当前 base 过滤可能使本次事件不触发 | 下次受信重建移除其旧预览；如要求及时清理，补充无 base 过滤的元数据入口或周期对账 |
| PR head 资格变化 | 当前前缀 job 条件可能跳过该事件 | 同上，避免把“事件被跳过”当作预览已清理 |
| 手动恢复 | 明确 dispatch main | 读取当时完整源集合，而非部署调用者分支 |

资格变化造成的及时清理缺口，来自当前触发过滤和重建模型的组合。最小发布修正可以先明确人工重建入口；若采用周期对账，应明确其为最终一致性兜底，不承诺固定分钟内一定执行。

## 6. 方案 B：低权限 PR 加可信调度

### 6.1 推荐的数据流

1. R02 的低权限候选验证 workflow 响应适用 PR 事件并完成其检查。
2. main 上另一个可信入口响应指定 workflow 的 `completed` 事件。
3. 下游校验 GitHub 提供的运行元数据：事件类型、源仓库、目标 workflow 标识和当前仓库。
4. 下游仅将该事件作为需要重新对账的信号，重新列出全部当前合格 PR。
5. 使用 main 的脚本，按当前每个 PR 的精确 head SHA 下载静态归档。
6. 进入与 main push、手动恢复共用的完整发布流程和锁。

上游 artifact、日志、PR 标题或评论都不作为下游命令、安装内容或授权输入。无需让上游上传可执行发布包。

### 6.2 候选失败与关闭事件

预览用于审阅，不能简单要求候选测试全部成功后才允许生成预览。拟议下游可以接收不同 conclusion 的完成事件，再由 main 的静态校验决定源文件能否进入站点；候选测试失败应独立明确显示。

`pull_request` 在冲突场景可能不运行，候选分支也可能修改、删除或路径过滤掉信号 workflow。因此 B 需要保留 main push、手动重建，并视需求增加 schedule；不能以 workflow_run 取代所有生命周期入口。

若上游同时承担 required check 与调度信号，应确保主检查不会因路径过滤导致永远没有检查结果。具体候选 job 和 required check 设计由 R02 细化。

### 6.3 拟议配置范围

- 增加或复用低权限候选 workflow；不在其中持有部署凭据。
- Pages 主流程在默认分支新增受信 workflow_run 入口或调用层。
- 下游只使用 GitHub 事件元数据和 main 的 API 读取，不 checkout 上游 head。
- 通过 API 重新核对来源 workflow 的固定标识，不能仅依赖可重名的展示名称。
- 复用同一全局发布锁，禁止为每个 PR 各建整站部署锁。
- 严格限制链路深度和触发范围，避免自身发布再次触发自身。

本节描述的是方案，不是已安装 workflow。最终采用前需要在真实事件环境验证，不能仅以 YAML 能解析作为完成。

## 7. 源版本、并发和发布一致性

### 7.1 每次运行记录真实快照

main 可以在事件创建后继续前进，PR 也可以在排队期间更新。发布器应在获得发布锁后读取本次 main，列出当前合格 PR，将 `main_sha` 与每个 `head_sha` 绑定到产物。

原事件的 head 只用于诊断，不用于覆盖当前完整源集合。source manifest 的含义是“本次读取并构建的源版本”，而不是对全平台状态不再变化的保证。

### 7.2 串行不等于所有事件逐一执行

当前官方 concurrency 说明：默认最多一个运行中和一个 pending；新的 pending 可替换旧 pending，且调度顺序不能按事件创建时间保证。现有 `cancel-in-progress: false` 有利于避免中途取消完整发布，但不能解释成每个事件都逐一 FIFO 执行。[S7]

所以可靠性依靠每次重新查询当前源集合，而不是重放所有事件。发布中发生的新变化由后续重建收敛；发布结果仍按明确 SHA 验收。

### 7.3 可选的过期快照检查

若实际运行中出现明显的排队或发布时源频繁变化，可在上传前比较关键源指纹，报告结果已被后续源变化替代，并安排重新对账。该增强应设置有界重试；不得连续无条件重建，也不得把旧部署宣称为当前最新版。

这一增强可以与 R04 的版本变化检测协调，近期事件兼容性修复不必先引入新的全局状态服务。

## 8. 分阶段迁移和回退

| 阶段 | 实施内容 | 进入下一阶段的条件 |
| --- | --- | --- |
| 0：保全基线 | 保存当前 SHA、必要配置摘要和已有恢复命令 | 能追溯当前行为与当前策略 |
| 1：确定策略路线 | 完成实际 insights/默认策略适用性判断，选 A 或 B | 不再依赖“空列表即豁免”的推断 |
| 2：先落候选检查 | R02 低权限检查在独立分支验证，保留现有发布主线 | 候选缺陷可发现，发布权限未扩散 |
| 3A：实施 A | 在必要且允许时调整窄范围事件配置，补充入口限制和清理说明 | 真正的打开、更新和关闭事件验证通过 |
| 3B：实施 B | 添加受信下游与来源校验，先对账观察再接入完整发布 | 数据来源、事件覆盖和权限矩阵验证通过 |
| 4：验收当前版本 | 本次 workflow 成功，manifest 和文件核对通过 | 记录实际 main、PR head、运行与结果 |
| 5：观察与收敛 | 核对重复事件、资格变化和清理行为 | 决定是否需要周期兜底等后续增强 |

回退按具体改动执行有针对性的配置恢复或提交 revert，不改写 main 历史、不手工改 gh-pages。若 PRT 被实际策略禁止，单纯恢复旧 YAML不会恢复该事件，应使用已保留的 main 手动入口重建，并继续修复触发路线。

如果某次构建失败，现有线上内容不自动变为新版本；gh-pages 可能已写入但官方 Pages 尚未成功，必须区分两者。

## 9. 测试与验收矩阵

| 验证项 | 场景 | 通过条件 |
| --- | --- | --- |
| 策略实际效果 | 目标事件在真实适用策略下启动 | 不被事件规则拒绝，且未全局放松无关规则 |
| 候选与发布隔离 | PR 修改脚本或测试 | 在低权限环境测试候选；发布仍执行 main |
| 精确版本 | 排队期间 PR 从 A 更新到 B | manifest 明确真实构建版本，不混用分支名和旧 SHA |
| 多预览保留 | 两个合格 PR 同时存在 | 同一站点保留两个当前预览 |
| 关闭清理 | 关闭其中一个 PR | 下次成功重建只移除该预览 |
| 正式迁移 | 移除 PR artifacts 后合并 | 保留确认 SHA，正式 main 部署正确，预览按当前集合移除 |
| 资格变更 | base 改离 main 或 head 不再合格 | 入口或兜底完成清理，未触发时明确尚未清理 |
| 来源拒绝 | fork、普通分支或错误上游 workflow | 不作为预览源；B 的来源校验拒绝不合格通知 |
| 手动 ref | 从 main 和非 main 分别尝试入口 | 允许 main；非 main 按实际防误操作与环境约束报告，不执行候选发布逻辑 |
| 并发 | main push 与多个 PR 更新相近发生 | 全站发布不并行覆盖；最终有效运行包含当时全部源集合 |
| 完整部署 | gh-pages 已更新但 deploy job 失败 | 准确报告部署失败，不以快照推送代替上线验收 |

真实线上事件验证会产生 PR、运行或部署，需要在后续实施授权范围内安排；本次调研仅制定验收项。

## 10. 与其他优化项的衔接

- **R02**：候选 CI 与发布分开；若选 B，确定哪个 workflow 提供信号及哪些生命周期事件需要兜底。
- **R03**：事件触发成功不等于内容已批准；继续保存迁移前确认 SHA，不能把 workflow conclusion 当作批准记录。
- **R04**：成功运行后按真实 main/PR SHA 和全部所选资源核对；源在等待期间变化应明确报告。
- **R05**：后续诊断工具可只读展示当前策略列表、事件许可未知项、运行状态及可用恢复入口。

## 11. 本次完成与未决事项

### 已完成

- 读取当前工作流、组合和保存快照实现及仓库约定。
- 使用官方当前资料重新核实 2026-12-02 节点和相关事件语义。
- 查询实际仓库元数据、Actions 设置、默认 token、Pages、环境分支规则、Actions policies、规则集、传统分支保护和最近运行。
- 将必要查询结果保存到忽略的 scratch 目录，并形成可实施方案。

### 仍需实施阶段核实

- 管理界面中是否出现平台默认评估策略、Policy insights 是否显示本仓库命中。
- 作用于发布 workflow 的事件许可配置如何与平台默认或未来上层规则组合。
- 选定路线在真实 opened、synchronize、closed、retarget 等事件下的运行结果。
- 是否需要对资格变化提供更及时的周期或元数据对账入口。
- 是否有其他流程依赖 github-pages 环境中的 gh-pages 规则。

若未来某个 API 返回 403 或 404，记录 endpoint、响应正文和访问限制，不能直接改写成“没有策略”。当前 policies 查询是成功返回空集合，与不可访问是不同状态。

## 12. 官方资料

以下资料查询日期均为 2026-11-21；实际实施时再次核对当前平台行为。

- [S1] [Securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)：默认限制日期、适用条件和可信执行边界。
- [S2] [About Actions policies](https://docs.github.com/en/actions/concepts/about-actions-policies)：策略层级和事件许可。
- [S3] [Governing execution of GitHub Actions workflows](https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution)：作用范围、管理入口和 Policy insights。
- [S4] [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)：PR、PRT、workflow_run、dispatch 与 schedule 语义。
- [S5] [REST API endpoints for GitHub Actions policies](https://docs.github.com/en/rest/actions/policies)：实际使用的只读策略列表 API 和权限要求。
- [S6] [Use GITHUB_TOKEN for authentication in workflows](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)：job token 权限控制。
- [S7] [Control the concurrency of workflows and jobs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)：运行互斥、pending 替换和顺序限制。
