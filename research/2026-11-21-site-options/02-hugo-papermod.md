# Hugo PaperMod：现成主题最小接入验证

- 调研与验证日期：2026-11-21。
- 项目基线：`wvliteam/static-pages`，`ee180b1e36d71b600f324ddbaa8d64e493862565`。
- 当前任务分支：`preview/site-options-comparison`。
- 状态：已完成真实本地构建和静态检查；未创建 PR、未部署、未选定为正式主题。
- 页面品牌：沿用“页面集”，没有填入个人姓名、头像或虚构履历。
- 主任务已补充真实浏览器检查，最终范围见 [统一验证记录](VALIDATION.md)。

## 1. 结论

**PaperMod 可以直接承担首页、Markdown 文章、标签与文章归档，已有独立 HTML 报告也能保留原路径和原字节。** 本次不修改上游模板代码，只增加项目配置、内容和本地静态资源，即完成了可构建的最小站点。

需要明确的接入成本有两项：

1. 新增 Hugo 工具与站点源文件的版本管理；当前仓库原本只接收已生成的静态文件。
2. 默认构建会把正式或预览 base 写入链接和元数据。两种 base 的输出不是同一份字节，不能直接声称符合现有“确认干净产物后原样迁移”的流程。

因此，它适合希望持续用 Markdown 写作，并需要个人／项目介绍和文章归档的路线。若当前主要需求是少量独立报告与工具的入口页，还需比较直接静态模板能否以更少工具解决问题。

## 2. 固定的上游与工具版本

| 项目 | 本次固定值 | 验证方式 |
| --- | --- | --- |
| PaperMod 仓库 | `adityatelange/hugo-PaperMod` | 官方仓库与文档 |
| 主题提交 | `118119693d8b5ac211b939775678310973bcb232` | GitHub API 查询并按完整 SHA 下载归档 |
| 该提交日期 | 2026-10-25 | GitHub API 返回 |
| Hugo | `0.170.1`，标准版 linux/arm64 | 官方 release 下载，实跑 `hugo version` |
| Hugo 下载文件 | `hugo_0.170.1_linux-arm64.tar.gz` | 官方 release asset |
| Hugo 下载包 SHA-256 | `6f57f13bc47c000c0d36c7f5a446d6c06f7956d8e102cc2a13735e0c0225b2d2` | 与同一官方 release 的 checksums 文件逐项一致 |
| 本地平台 | Ubuntu 26.04.1，aarch64，Python 3.15.2 | 本机只读查询 |

官方安装页当前说明需要 Hugo 0.146.0 或以上；本次只验证了上表固定版本，不宣称所有最低版本均通过。主题说明提供 Regular、Home-Info、Profile 三种布局，并说明不需要 Node.js 等 JavaScript 构建工具。本次实际采用标准 Hugo 二进制，未安装 Ruby、Node 依赖或 Sass。[主题仓库](https://github.com/adityatelange/hugo-PaperMod/tree/118119693d8b5ac211b939775678310973bcb232) · [安装说明](https://github.com/adityatelange/hugo-PaperMod/wiki/Installation) · [Hugo release](https://github.com/gohugoio/hugo/releases/tag/v0.170.1)

工具、主题源码及下载包都保存在忽略的 `scratch/site-options/papermod/`，没有全局安装或修改用户配置。checksum 验证用于核对下载是否匹配官方清单，不将它扩大解释为独立的软件签名验证。

## 3. 最小场景与产物位置

### 3.1 实际完成的页面

- 首页：上游 Profile 布局，提供“报告”“文章”“归档”三个入口。
- 报告归档：明确链接已有 513310 历史报告。
- 关于页：说明页面集的用途和本地比较状态。
- 第一篇 Markdown：“模板接入验证”。
- 第二篇 Markdown：“第二篇内容加入验证”，实际新增后验证文章归档自动更新。
- 上游自动生成的文章列表、标签、RSS、sitemap 和内容 JSON。
- 原有报告：`reports/513310/2026-11-20/index.html`，未经正文重写。

### 3.2 文件位置

| 内容 | 位置 | 是否为本次可审阅静态产物 |
| --- | --- | --- |
| 正式 base 构建结果 | `artifacts/site-option-papermod/public/` | 是，本地候选产物，尚未正式收录 |
| 嵌套 base 构建结果 | `scratch/site-options/papermod/build-nested/` | 本地路径兼容夹具，不是已上线预览 |
| 原始主题与项目源文件 | `scratch/site-options/papermod/source/` | 否，原型源码与上游归档 |
| Hugo 二进制 | `scratch/site-options/papermod/tools/hugo/hugo` | 否，本地工具 |
| 构建日志和检查 JSON | `scratch/site-options/papermod/` | 否，本地验证证据 |

本地候选入口为 `artifacts/site-option-papermod/public/index.html`。样例产物不随本次文档提交上传；该产物使用项目 base，浏览时应通过匹配 base 的 HTTP 挂载；直接以 `file://` 打开或任意子目录打开，不构成本次路径验收。

原型源码的结构为：

```text
source/
  hugo.toml
  portable.toml                  # 仅用于 relativeURLs 负例试验
  themes/PaperMod/                # 固定上游提交，未改模板
  content/
    about.md
    archives.md
    reports-index.md
    posts/
      template-integration.md
      second-entry.md
  static/
    reports/513310/2026-11-20/index.html
    licenses/PaperMod-LICENSE.txt
    favicon.ico
    favicon-16x16.png
    favicon-32x32.png
    apple-touch-icon.png
    safari-pinned-tab.svg
```

如果后续选用该路线，项目源可以迁入仓库中独立的站点源码目录；具体目录需要与最终构建方式一并确定。当前没有把研究源码放入正式 `docs/`。

## 4. 最小改动与实跑构建

### 4.1 保留上游布局，使用配置接入

核心配置如下，完整原型配置保存在本地 source 目录：

```toml
baseURL = 'https://wvliteam.github.io/static-pages/'
locale = 'zh-CN'
defaultContentLanguage = 'zh'
title = '页面集'
theme = 'PaperMod'
timeZone = 'Asia/Shanghai'

[pagination]
disableAliases = true

[outputs]
home = ['HTML', 'RSS', 'JSON']

[params]
mainSections = ['posts']
defaultTheme = 'auto'
ShowToc = true
ShowBreadCrumbs = true

[params.profileMode]
enabled = true
title = '页面集'
subtitle = '报告、文章与工具的统一入口。此页用于成熟主题的最小接入比较。'

[[params.profileMode.buttons]]
name = '报告'
url = 'reports-index/'
```

配置、五个 Markdown 内容文件、原报告静态副本、许可证和本地图标构成项目改动。未覆盖 `_partials` 或其他上游布局，没有新增页面生成器或 JavaScript 构建链。

最初构建出的两个 `/page/1/` 自动重定向页没有 viewport，现有检查器因此返回失败。为这个不依赖第一页别名的比较站点设置 `pagination.disableAliases=true` 后，两套最终产物的全部 12 份 HTML 均通过。该设置是 Hugo 官方支持的分页配置；没有放宽检查器。[分页配置](https://gohugo.io/configuration/pagination/)

本次最终使用 `locale`。较旧的 `languageCode` 在实际运行的 Hugo 版本中会给出弃用提示，因此没有继续照搬旧示例。

### 4.2 实际执行的构建命令

以下命令在仓库根目录执行，依赖已经准备好的本地 source 和固定二进制。下载与校验记录另存于 `upstream.json`，不要求全局安装。

```bash
scratch/site-options/papermod/tools/hugo/hugo build \
  --source scratch/site-options/papermod/source \
  --destination /home/work/code/static-pages/artifacts/site-option-papermod/public \
  --baseURL https://wvliteam.github.io/static-pages/ \
  --cacheDir /home/work/code/static-pages/scratch/site-options/papermod/cache \
  --minify --cleanDestinationDir
```

嵌套夹具使用相同源码，将 destination 指向本地 `build-nested`，base 改为：

```text
https://wvliteam.github.io/static-pages/previews/pr-999/site-option-papermod/
```

`999` 仅用于本地路径测试，不对应真实 PR，不能将该地址当作已经部署的链接。实际创建预览时必须使用真实 PR 编号和任务路径重新准备对应产物。

本机绝对路径仅用于记录此次实际命令；未来通用脚本和 skill 应通过参数接受输出与缓存目录。

Hugo 不会默认清理所有旧输出，删除或重命名文章后应使用新的输出目录或受控的清理选项，避免旧页面继续留下。本次 `--cleanDestinationDir` 仅作用于本任务独立生成目录。[构建清理说明](https://gohugo.io/configuration/build/)

## 5. 原报告 URL 与字节保留

Hugo 官方说明 `static/` 内文件会复制到构建输出。原报告放在 `static/reports/513310/2026-11-20/index.html`，无需改为 Markdown 或套进主题正文模板。[目录结构](https://gohugo.io/getting-started/directory-structure/)

| 检查对象 | 结果 |
| --- | --- |
| 原文件路径 | `docs/reports/513310/2026-11-20/index.html` |
| 正式构建相对路径 | `reports/513310/2026-11-20/index.html`，不变 |
| 嵌套构建相对路径 | 同上，不变 |
| 原文件长度 | 99,445 字节 |
| 原文件及所有测试输出 SHA-256 | `e7fbd1ecd16e6395a07adf1d6026ef3b81d5d8f6a1bc6d739a7227ab8867ddc2` |

因此正式站点的既有 `/static-pages/reports/513310/2026-11-20/` 路径可以保留。模拟预览只增加其外层 PR／任务前缀，没有改报告相对路径或历史数据。

**静态复制不等于自动归档。** 这份原始 HTML 不会自动成为 `site.RegularPages` 中的 Markdown 文章。本次报告目录使用一个明确维护的链接；今后若希望报告自动出现在标签、搜索或归档中，需要增加内容条目／元数据映射，或接受报告目录与文章目录分开维护。这是应计入的适配成本。

## 6. 新增第二篇内容的实测

操作只有新增 `content/posts/second-entry.md`，然后执行同一构建命令，没有修改首页、文章列表或归档模板。

最小内容格式为：

```toml
+++
title = '第二篇内容加入验证'
date = '2026-11-21T12:30:00+08:00'
description = '仅新增 Markdown，验证文章列表与归档自动更新。'
tags = ['integration']
+++
```

以上是 Markdown 的 TOML front matter，之后继续填写正文。

实际观察：

- `archives/index.html` 中的 `archive-entry` 数量从 1 增加为 2。
- `/posts/`、标签集合、RSS 和内容 JSON 随构建更新。
- Profile 首页仍保持介绍和入口布局；它不会自动变成文章列表首页。
- 若需要首页直接展示文章，可以评估上游 Home-Info／Regular 布局，不必先自建列表组件。

两篇内容均是接入验证样例，不表示已批准加入正式内容目录。

## 7. 正式与预览路径的兼容性

### 7.1 两套 base 构建结果

| 项目 | 正式 base | 模拟嵌套 base |
| --- | --- | --- |
| 路径 | `/static-pages/` | `/static-pages/previews/pr-999/site-option-papermod/` |
| 输出文件 | 26 | 26 |
| HTML 文件 | 12 | 12 |
| 总字节 | 224,506 | 233,867 |
| 最近一次本机构建耗时 | 1.048 秒 | 0.663 秒 |
| 原报告 SHA | 与原文件一致 | 与原文件一致 |
| 全部 HTML 静态检查 | 通过，退出 0 | 通过，退出 0 |
| 补充同源导航／资源解析 | 无缺失 | 无缺失 |

耗时是此次原型的单次观察，不是通用性能承诺，也不包含工具下载。

正式与嵌套输出有 **18 个文件字节不同**，包括生成 HTML、RSS、内容 JSON 和 sitemap。首页 canonical 分别指向各自构建 base。外层 URL 前缀会影响输出，不能只比较原报告不变就宣称整个站点不变。

将默认正式产物保持原样、直接按模拟嵌套 base 解析时，记录到 152 处越出本地挂载范围或缺失的导航／资源引用。这是额外的同一产物双挂载负例，不能用两套各自正确的构建结果替代该项验证。

默认页面中的部分导航和图标为绝对同源 URL。用 localhost 验证时应对该站点 origin 做本地映射；否则点击链接会跳到真实站点，不能作为本地产物通过的证据。

### 7.2 `relativeURLs=true` 的实际负例

额外构建了 `portable.toml`，只添加：

```toml
relativeURLs = true
```

结果没有解决同一份产物双挂载问题：

- 正式 base 的某些 CSS URL 变为 `./static-pages/assets/...` 或 `../static-pages/assets/...`，在对应路径下找不到文件。
- 仍保留指向正式 base 的绝对导航、图标等引用。
- 本地解析记录中，正式挂载有 20 项缺失；同一正式产物挂到嵌套 base 有 152 项越出挂载范围或缺失。
- 两种 base 的 portable 输出仍有 18 个文件不同，canonical、RSS 和 sitemap 也没有变成与部署位置无关的统一产物。

这组实验只说明当前固定版本、配置与主题组合的行为。Hugo 官方将该选项说明为较脆弱的后处理，并建议仅在需要通过文件系统导航的站点中使用，不应把它当作默认托管路径适配方案。[URL 管理](https://gohugo.io/content-management/urls/)

失败实验保留在忽略的 `build-portable-*` 目录；交付的 public 使用正常构建，没有采用失败配置。

### 7.3 对现有确认流程的影响

当前仓库约定要求确认具体预览版本后迁移干净源文件。若预览构建与正式构建采用不同 base，最终输出发生变化，需要明确处理这些差异，不能静默把“同一内容源码”解释为“同一已确认文件字节”。

后续有三种路线可以评估：

1. 保留现有产物审阅方式，为导航、资源和元数据建立范围很窄的可审阅适配，并验证同一产物双挂载。
2. 明确审阅固定源码和两种构建结果，记录构建参数与差异，再调整对应发布约定。
3. 若需求收敛为普通个人博客，另行确认是否需要当前自定义的多 PR 静态预览，再选择更简单的可信构建与发布方式。

本次没有选择或实施上述流程变更。相对于直接静态模板，PaperMod 在这里存在额外的路径与确认契约成本。

## 8. 运行时资源、许可证与升级

### 8.1 资源观察

本次输出仅有一份本地生成 CSS，没有外部 JS 文件。主题交互脚本在 HTML 中，报告本身也保留原内联代码。对 HTML 运行资源引用及输出 CSS 的静态枚举共检查 55 处引用，未找到外部 origin 的运行资源地址；上游和来源超链接不算运行资源。

这不代替浏览器网络跟踪。主任务随后完成的基础布局、入口、首个 Tab 焦点和明暗切换检查见 [统一验证记录](VALIDATION.md)；本轮没有穷尽阅读位置、报告图表和所有交互状态。

本地补充了主题默认引用的图标，避免默认 favicon 文件缺失。未引入远程字体、统计、评论或联系表单服务。

### 8.2 许可证与归属

固定提交的上游 LICENSE 为 MIT，列出 nanxiaobei 和 adityatelange 的版权信息。本地输出保留完整许可证副本：`artifacts/site-option-papermod/public/licenses/PaperMod-LICENSE.txt`。页脚保留上游 Hugo 与 PaperMod 归属链接。

这里记录的是所用版本的许可证与实际保留内容。引入其他模板素材、字体或插件时仍需逐项核对对应来源，不能由主题许可证推导所有外部素材均相同。

### 8.3 维护方式

- 固定 Hugo 版本和主题提交，保留 checksum 与来源记录。
- 项目配置、内容和静态报告单独维护，不修改 vendored 主题模板。
- 升级时先替换隔离的上游版本，重新构建正式和嵌套夹具，执行路径、报告哈希和布局检查。
- 站点源进入版本管理后，可以选择固定归档、Git submodule 或 Hugo module；本次使用归档，不要求为比较任务先引入仓库 submodule。
- 构建缓存和下载工具留在临时目录，不能进入 public。

## 9. 对当前仓库发布代码的影响

### 9.1 最小接入方式

近期可以保持“本地构建 → 静态产物交付 → 既有发布器”的结构。只在可信本地环境运行固定 Hugo 和主题，再将正确 base 的生成文件交给发布流程。

若之后改为 Actions 构建，应在可信 main 上执行固定构建工具，再交给统一发布流程。不能照搬一个新部署 workflow 与现有整站部署并行覆盖站点，也不能在带发布权限的环境中运行 PR 提供的 Hugo 构建配置、脚本或扩展。

Hugo 官方提供 GitHub Pages 构建与部署指南，但本仓库有自己的多预览组合和版本约定，需按实际需要整合构建步骤，不能把示例 workflow 直接视为完整替换。[官方部署指南](https://gohugo.io/host-and-deploy/deploy-to-github-pages/)

### 9.2 能复用与仍需决定的工作

| 能力 | PaperMod 能提供的部分 | 本仓库仍需处理 |
| --- | --- | --- |
| 首页与文章布局 | Profile、文章、归档、标签、明暗模式 | 内容与导航配置、实际视觉验收 |
| Markdown 新内容 | 自动生成列表、归档、RSS 等 | 内容真实性、日期和发布授权 |
| 已有独立 HTML | 通过 static 保留字节和路径 | 报告目录条目与元数据接入 |
| 常规站点构建 | 单个 Hugo 工具完成生成 | 固定版本、缓存、可重复构建 |
| 多 PR 预览 | 不是本次主题集成直接提供的能力 | 当前发布器或经确认的简化方案 |
| 确认版本迁移 | 主题不决定用户授权 | base 差异与源码／产物确认契约 |
| 线上版本与文件核验 | 生成静态文件供验收 | 现有或增强的 manifest／哈希校验 |

因此，可以优先复用主题避免重做布局与文章归档；R01–R04 中哪些机制继续建设，要结合最终是否保留自定义预览流程决定。

## 10. 证据、限制与建议

已执行：

- 查询官方版本和主题提交，下载官方 arm64 工具并核对 checksum。
- 真实构建一篇内容基线、加入第二篇内容后的正式和嵌套版本。
- 两种 base 的全部 12 份 HTML 执行现有检查器，均退出 0。
- 检查原报告所有输出副本的 SHA-256，完全一致。
- 解析同源资源和导航到本地文件，正常两套输出均无缺项。
- 实际试验 `relativeURLs=true` 并记录失败，而非假设其解决嵌套路径。

原始证据保存在本地 `scratch/site-options/papermod/`：`upstream.json`、`measurements.json`、`check-formal.json`、`check-nested.json`、`check-summary.json`、`runtime-assets.json` 和构建日志。

本子任务没有创建真实 PR、提供公网预览、变更正式 `docs/` 或运行正式部署。主任务的浏览器结果已在 [统一验证记录](VALIDATION.md) 中补充，不由静态检查结果替代。

**建议**：将 PaperMod 保留为 Markdown 内容站的有力候选。它已经证明可以原样承载已有报告，并用配置获得成熟文章功能；在选定前，应把默认构建的 base 差异作为重要决策项，与直接静态模板的原样迁移成本一起比较。

## 11. 主要来源

来源查询日期：2026-11-21。

- [PaperMod 固定提交](https://github.com/adityatelange/hugo-PaperMod/tree/118119693d8b5ac211b939775678310973bcb232)。
- [PaperMod 安装文档](https://github.com/adityatelange/hugo-PaperMod/wiki/Installation)。
- [Hugo v0.170.1 release](https://github.com/gohugoio/hugo/releases/tag/v0.170.1)。
- [Hugo 官方 checksum 文件](https://github.com/gohugoio/hugo/releases/download/v0.170.1/hugo_0.170.1_checksums.txt)。
- [Hugo 目录结构](https://gohugo.io/getting-started/directory-structure/)。
- [Hugo URL 管理](https://gohugo.io/content-management/urls/)。
- [Hugo 分页配置](https://gohugo.io/configuration/pagination/)。
- [Hugo 构建与清理](https://gohugo.io/configuration/build/)。
- [Hugo GitHub Pages 部署](https://gohugo.io/host-and-deploy/deploy-to-github-pages/)。
- 本仓库：[README](../../README.md)、[AGENTS](../../AGENTS.md)、[本地 HTML 检查器](../../skills/static-page-builder/scripts/check_static_html.py)。
