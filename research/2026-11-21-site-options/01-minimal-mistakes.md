# Minimal Mistakes：最小接入验证与采用分析

- 验证日期：2026-11-21。
- 本仓库基线：`ee180b1e36d71b600f324ddbaa8d64e493862565`。
- 本地分支：`preview/site-options-comparison`。
- 状态：本地真实构建与接入比较；尚未选择为正式站点，也未提供线上预览或执行部署。
- 产物目录：`artifacts/site-option-minimal-mistakes/public/`；源码、工具与原始记录仅保存在忽略的 `scratch/site-options/minimal-mistakes/`。
- 子任务完成后，主任务补充了真实浏览器检查，最终范围见 [统一验证记录](VALIDATION.md)。

## 1. 结论

**Minimal Mistakes 可以复用为“个人／项目入口、文章、报告目录”一体的站点外壳，且已在本环境真实构建成功。** 现有独立报告可以作为静态文件原样保留，继续位于 `reports/513310/2026-11-20/`。

它能明显减少页面布局、文章列表、归档、订阅和搜索界面的自建工作。接入当前仓库时的主要成本是 Ruby/Jekyll 构建依赖，以及正式与嵌套预览 base 不同造成的重建和审阅版本问题。

本次实证表明：**常规主题输出不能在这两种 base 之间原样搬迁。** 正式产物错误挂载到嵌套预览位置时，本地检查出现 71 个路径问题；分别使用正确 base 构建后，两套输出的全部 7 个 HTML 均通过现有静态检查。

因此，建议将它视为完整内容站点的可用候选。若最终采用，先明确构建与预览策略，再接入现有“确认具体干净字节后迁移”的流程，不能只把主题文件复制进当前发布器便宣称完成。

## 2. 上游与固定版本

| 项目 | 本次采用或核对的版本 | 使用范围 |
| --- | --- | --- |
| `mmistakes/minimal-mistakes` | commit `411699970e028cd5545d40fbcd3e2159275f72c2`，包版本 4.28.1 | 本次布局、includes、Sass、前端资源的实际来源 |
| `mmistakes/mm-github-pages-starter` | commit `dfed5db462e438daac700832237b907834906e7d` | 核对官方起步方式；本次没有直接复制完整 starter |
| Ruby | 3.3.8 | 本地隔离运行时 |
| Jekyll | 4.4.1 | 实际执行构建 |
| 主要插件 | include-cache 0.2.1、paginate 1.1.0、feed 0.17.0、sitemap 1.4.0 | 本次使用的 Ruby 包 |

主题提供 Gem 和 remote theme 引用方式，官方起步文档建议通过 starter 快速建站，并明确需要 `jekyll-include-cache`。本次采用固定 commit 的完整主题资源，是为了在本地控制来源并验证最小构建，不等于要求今后在本仓库维护上游主题副本。

来源：[固定主题提交](https://github.com/mmistakes/minimal-mistakes/tree/411699970e028cd5545d40fbcd3e2159275f72c2)、[官方 starter](https://github.com/mmistakes/mm-github-pages-starter)、[Quick-Start Guide](https://mmistakes.github.io/minimal-mistakes/docs/quick-start-guide/)。查询日期均为 2026-11-21。

## 3. 共同场景和实际产物

使用已有品牌“页面集”，没有填写用户未提供的姓名、简历、头像或联系方式。页面包括：

- 首页：站点介绍、报告入口和自动文章列表。
- 报告目录：从一份 `_data/reports.yml` 读取既有报告的标题、日期和链接。
- 文章目录：使用主题的 posts 归档布局。
- 关于页面：说明内容组织与本地接入验证目的。
- Markdown 文章“模板接入验证”。
- 第二篇 Markdown“新增内容验证”，用于实测新增文章后的自动更新。
- 既有 513310 报告的完整原文件。

首页、文章、归档和关于页面沿用上游 home、posts、archive、single 布局。没有重写主题 CSS、JavaScript 或 `_layouts`／`_includes`，未为对比另外设计一套视觉系统。

实际自定义源码为配置、导航数据、报告数据、首页、三个内容页面和两篇文章，共 9 个文件；其余主题文件来自固定上游快照，报告来自本仓库现有 `docs/`。

| 输出 | 内容 |
| --- | --- |
| `index.html` | 入口与文章列表 |
| `reports/index.html` | 报告归档 |
| `reports/513310/2026-11-20/index.html` | 原样复制的独立报告 |
| `articles/index.html` | 文章归档 |
| `articles/template-integration/index.html` | 第一篇 Markdown 构建结果 |
| `articles/second-entry/index.html` | 第二篇 Markdown 构建结果 |
| `about/index.html` | 关于页面 |
| `assets/`、`feed.xml`、`sitemap.xml`、`robots.txt` | 主题资源与生成文件 |
| `LICENSE` | 上游原文许可证 |

最终正式 base 样例共 **27 个文件、1,401,628 字节**，约 1.34 MiB；包含上游资源和 source map。统计对应本次样例配置，不代表任意 Minimal Mistakes 站点的固定体积。

## 4. 实际运行环境与构建方式

### 4.1 环境准备

本机为 aarch64 Ubuntu 26.04，开始时没有 Ruby、Bundler、Jekyll。Docker 客户端存在，但没有可用 daemon。

本次通过 `apt-get -s` 读取依赖，再用 `apt-get download` 下载 **73 个发行版包**，仅以 `dpkg-deb -x` 解包到本路线 `scratch/` 前缀。没有全局安装、sudo、系统包配置或 daemon 启动。

下载约 15.7 MB，解包前缀约 87 MB。为支持非系统前缀，只在该隔离前缀中将 SassC 的绝对 libsass 路径改为实际本地前缀，并通过进程环境传入 Ruby 库路径。

**这些是本机缺少运行时的首次实验成本，不是正常 CI 每次发布的必要步骤。** 正式接入应使用适当 Ruby 环境、Gemfile 与锁文件管理依赖；本次未实现新的构建 workflow，也未验证未来锁文件组合。

### 4.2 实际执行的构建

本地试验使用隔离 Ruby 执行发行版 Jekyll 入口，核心参数为：

```text
ruby3.3 <隔离前缀>/usr/bin/jekyll build
  --source <本地样例源码>
  --destination <对应输出目录>
  --baseurl <正式或模拟预览base>
  --trace
```

以上是实际调用形式的路径简写；完整执行记录在忽略的 `scratch/site-options/minimal-mistakes/build_probe.py` 与构建日志中。记录不属于正式发布脚本，不能直接当作已经安装的通用接口。

首次试验发现 `jekyll-paginate` 要求首页采用 `index.html`；使用 `index.md` 时有分页跳过警告。本次已按主题通常方式改成带 front matter 的 `index.html`，内容用少量 HTML 和 Liquid 组织；两篇文章仍用 Markdown。最终三次构建退出码均为 0，最终日志无分页警告。

| 构建阶段 | 实际耗时 | 结果 |
| --- | --- | --- |
| 仅第一篇文章 | 6.898 秒 | 成功 |
| 新增第二篇，正式 base | 7.450 秒 | 成功 |
| 相同内容，嵌套预览 base | 7.054 秒 | 成功 |

时间包含本地进程启动，受当前环境影响；不能作为跨机器性能结论。本次未启用增量构建。

## 5. 既有报告 URL 与字节保留

将既有报告直接放入站点源的同名相对路径，不添加 front matter。Jekyll 将没有 front matter 的文件视为静态文件，本次输出也实际保持原文件字节。

来源：[Jekyll Static Files](https://jekyllrb.com/docs/static-files/)。

正式网址路径仍为：

```text
/static-pages/reports/513310/2026-11-20/
```

既有源文件和正式／模拟预览输出中的报告 SHA-256 均为：

```text
e7fbd1ecd16e6395a07adf1d6026ef3b81d5d8f6a1bc6d739a7227ab8867ddc2
```

这证明本次复制未改变报告正文、数据或交互代码。它不自动证明报告内部所有链接在所有未来部署位置都正确；本次两种路径配置下均已运行静态检查，浏览器检查结果另行记录。

## 6. 新增第二篇内容的实测

实际操作为：在 `_posts/` 增加 `2026-11-21-second-entry.md`，填写标题、日期、分类和正文，然后执行相同 Jekyll 构建。

构建自动新增 `articles/second-entry/index.html`，并更新：首页、文章归档、第一篇文章的前后篇关系、Lunr 搜索数据、feed 和 sitemap。没有手工修改这些输出文件。

对于以后新增“独立 HTML 报告”，仍需复制报告文件并添加一条报告元数据。现有独立报告并不会自动转换成 Markdown 文章或进入文章全文搜索；这一点需要在内容策略中明确。

主题可以替代常规文章列表、归档和基础布局的自建实现。正式 README 的已发布列表、任意独立 HTML 的元数据采集和本仓库特有的确认记录，仍需另外处理，不能认为采用主题后这些维护工作已经全部消失。

## 7. 正式与预览 base 验证

### 7.1 两种实际配置

| 构建 | 配置 base | 输出位置 |
| --- | --- | --- |
| 正式样例 | `/static-pages/` | `artifacts/site-option-minimal-mistakes/public/` |
| 模拟嵌套预览 | `/static-pages/previews/pr-999/site-option-minimal-mistakes/` | 忽略的 `scratch/site-options/minimal-mistakes/preview-output/` |

`999` 仅是本地路径夹具，不是真实 PR 编号，也不是可访问的线上预览 URL。以后提供真实 PR 预览，需要按实际路径配置重新生成产物。

调用现有 [check_static_html.py](../../skills/static-page-builder/scripts/check_static_html.py)，分别对全部 7 个 HTML 使用对应 `--base-path`，两次均退出 0、问题数 0。没有修改或放宽检查器。

把正式产物直接按嵌套预览 base 检查，退出 1，出现 71 条问题，主要包括 `/static-pages/assets/`、导航和 feed 等路径与当前 base 不一致。

### 7.2 两套产物的字节差异

共 10 个文件不同：

- 首页、关于、报告目录、文章目录和两篇文章的 HTML。
- `assets/js/lunr/lunr-store.js`。
- `feed.xml`、`sitemap.xml`、`robots.txt`。

主要原因是页面资源 URL、导航、canonical、搜索索引和站点地址包含 base；feed 等还可能带构建元数据。`main.css`、主 JS、其他静态资源、许可证和既有报告字节相同。

### 7.3 对当前确认／迁移约定的影响

现有发布约定强调确认具体预览版本后迁移干净源文件。若确认的是“预览 base 的已生成 HTML”，随后为正式 base 重新构建，上述文件字节会改变，因此不能直接复用“原样移动且字节完全相等”的结论。

可选处理方向包括：采用经验证的可搬迁资源策略；改变预览承载位置以保持生成 base；或者明确采用“确认源版本和生成配置，再核对正式重建结果”的审阅模型。后两者都涉及当前发布架构或确认语义，应在选型后独立决定。

本次保持上游布局和路径生成方式，没有为通过测试而重写主题所有 URL，也没有修改仓库既有确认约定。

## 8. 运行时依赖与资源边界

- 页面主体 CSS、主 JavaScript、Lunr 库和索引在产物中。
- 固定上游的 head 默认从 jsDelivr 加载 `@fortawesome/fontawesome-free@latest` 图标 CSS。它是外部运行依赖，而且 URL 未固定具体版本；固定主题 commit 不会固定该远端依赖的未来内容。
- 默认中文 locale 下，本次主题的 Lunr 脚本选择逻辑回退到 `lunr-en.js`。已经生成中文内容索引，但尚不能把它解释为中文分词和任意中文查询质量已经验证。
- 没有配置评论、分析统计、联系表单或其他需要账号／服务的能力。
- 原报告的资源仍按原文件保持，本次没有刷新数据来源。

如果要求离线、自包含或严格固定运行资源，采用前需处理图标 CSS／字体本地化，并核对具体版本和归属。统一浏览器已检查基础布局、菜单、键盘和样例中文查询；外部图标完整视觉及更广泛检索质量仍需进一步验证。

上游实现依据：[固定版本 head](https://github.com/mmistakes/minimal-mistakes/blob/411699970e028cd5545d40fbcd3e2159275f72c2/_includes/head.html)、[Lunr 脚本选择](https://github.com/mmistakes/minimal-mistakes/blob/411699970e028cd5545d40fbcd3e2159275f72c2/_includes/search/lunr-search-scripts.html)。

## 9. 与当前发布机制和 skill 的接入成本

| 部分 | 可直接复用或保留 | 仍需适配 |
| --- | --- | --- |
| 站点内容 | 上游布局、文章列表、归档、订阅、搜索 UI | 原生 HTML 报告的元数据与列表关系 |
| 当前静态发布器 | 接收已经生成的 public 文件，继续组合正式站点与 PR 预览 | 新增 Jekyll 构建／导出环节和 base 选择 |
| 候选 CI | 在低权限环境执行普通 Jekyll 构建和静态检查 | Ruby、Gemfile/锁文件和构建缓存 |
| 可信发布 job | 继续只执行可信代码、读取静态产物 | 不直接拷贝上游整套发布 workflow 覆盖现有站点 |
| builder skill | 从零写页面转为配置主题、写 Markdown 和内容数据、构建及检查 | 明确本地／CI 运行时和未执行的浏览器检查 |
| publisher skill | 继续管理预览、真实版本、正式交付与验收 | 明确生成 base 与确认后重建的版本语义 |

采用主题不会自动提供本仓库当前的全部活动 PR 组合、确认 SHA 对应关系或部署文件哈希验证。只有明确继续需要这些能力时，才保留并适配对应自定义代码。

## 10. 更新、升级与归属

日常文章以 Markdown 和 front matter 管理，导航通过 `_data/navigation.yml` 配置。报告目录可以继续保持一份数据源；无需编辑生成后的 HTML。

长期采用时，优先使用受控 Gem 或带固定 ref 的 remote theme，减少主题副本维护。升级先在隔离环境更新版本并重建，比较路径、布局与依赖行为；不要默认追踪 master。官方支持按 release 或 commit 固定主题并回退。

来源：[Navigation](https://mmistakes.github.io/minimal-mistakes/docs/navigation/)、[Upgrading](https://mmistakes.github.io/minimal-mistakes/docs/upgrading/)。

上游 MIT 原文 `LICENSE` 已保留在本次产物中，HTML/CSS/JS 的主题版权注释和页面署名仍在。外部图标依赖与主题主体分开记录，本次未将其下载重打包。

## 11. 实际完成与未完成

| 验证项 | 结果 |
| --- | --- |
| 固定上游 commit 和版本 | 已完成 |
| 隔离 Ruby/Jekyll 运行 | 已完成，无全局安装 |
| 正式／嵌套 base 真实构建 | 均成功 |
| 新增第二篇文章自动更新 | 已实测 |
| 原报告相对路径与 SHA-256 | 保留且相同 |
| 两套输出全部 HTML 静态检查 | 均通过，未放宽检查器 |
| 同一正式产物跨 base 搬迁 | 失败，已记录 71 个路径问题 |
| 产物中本机绝对路径检查 | 未发现本次 `/home/work/` 路径 |
| 浏览器布局、菜单、键盘和中文搜索 | 主任务已完成两种 base 的基础浏览器检查；手机菜单 Enter 可展开，两条中文查询各命中 1 篇，英文对照命中 2 篇；图标 CSS 被主动阻断，详见统一记录 |
| 真实 GitHub PR 预览与正式部署 | 未执行 |

本地记录包括 `build-results.json`、`check-summary.json`、两套完整检查 JSON、依赖清单与构建日志，均位于忽略的 `scratch/site-options/minimal-mistakes/`。

## 12. 采用建议

如果目标是长期维护“文章＋报告＋项目入口”的统一内容站，Minimal Mistakes 值得进入最终候选：常用内容组织已经现成，真实构建和旧报告保留均已验证。

如果目标只是给现有独立 HTML 增加一个入口，Ruby/Jekyll 与 base 重建的维护成本需要与直接静态首页路线比较。特别是当前要求的预览确认后字节一致迁移，需要先解决生成路径策略；这项成本不能被“支持 GitHub Pages”一句话掩盖。

本次结论是可用性与接入成本判断，尚未批准替换正式首页或改变发布约定。
