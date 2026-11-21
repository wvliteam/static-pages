# 直接静态模板路线：Start Bootstrap Personal 最小接入验证

- 研究与验证日期：2026-11-21。
- 仓库基线：`ee180b1e36d71b600f324ddbaa8d64e493862565`。
- 本地分支：`preview/site-options-comparison`。
- 本地产物入口：`artifacts/site-option-personal/public/index.html`；样例产物不随本次文档提交上传。
- 状态：已生成并检查本地样例；尚未上传预览或正式收录。

## 1. 结论

**直接采用 Personal 的 `dist/`，是三条路线中最接近当前静态文件交付方式的候选。** 本次无需 Ruby、Hugo、Node 或 npm 构建，即可得到项目首页、报告入口和普通文章页面；所有页面和必要资源均可由现有发布器直接读取。

代价也已实测：它没有内置 Markdown 文章管线、自动目录、分类与搜索。新增第二篇文章时，实际需要新增一份 HTML，再手动修改首页和文章列表，共涉及三份文件。适合内容较少、重视独立页面自由度的入口网站；持续积累较多文章时，列表维护成本会高于生成器路线。

此判断基于本次样例和现有仓库结构，不代表未来不能给静态模板增加目录生成。但如果采用该方向，应将新增生成能力单独计入维护成本。

## 2. 固定的上游与复用范围

| 项目 | 本次实际使用 |
| --- | --- |
| 上游仓库 | `StartBootstrap/startbootstrap-personal` |
| 固定提交 | `6a1ebcc76a93ead054412fcbdf417d9c83dc762b` |
| 提交时间 | 2023-03-25 22:06:34 UTC |
| 产物内版本头 | Personal v1.0.1 |
| 样式框架 | 上游 `dist/css/styles.css`，内含 Bootstrap 5.2.3 |
| 导航脚本 | Bootstrap 5.2.3 bundle，本地保存 |
| 页面语言 | 本地适配为 `zh-CN` |
| 项目名称 | 沿用本仓库“页面集” |

固定提交来源于本次对官方仓库 `commits/main` 的查询，再按完整 SHA 下载归档。完整仓库和下载归档仅放在忽略的 `scratch/site-options/personal/`，交付目录只包含实际浏览需要的文件。

官方 README 明确支持直接编辑 `dist` 中 HTML/CSS；其 Pug、SCSS 与 npm 构建流程用于高级源文件开发，本次没有启用。[上游固定版本](https://github.com/StartBootstrap/startbootstrap-personal/tree/6a1ebcc76a93ead054412fcbdf417d9c83dc762b) · [上游使用说明](https://github.com/StartBootstrap/startbootstrap-personal#usage)

提交时间较早是本次实际观察，不据此断言项目已经停止维护。本次没有顺便升级内含 Bootstrap；如正式采用，应另行评估所选版本的维护和升级安排。

## 3. 最小样例具体做了什么

### 3.1 沿用的内容

- 原始首页的 Bootstrap 网格、导航、渐变标题、按钮、profile 背景和点阵装饰。
- 原始项目列表的卡片布局与间距体系。
- 完整上游 CSS、空的扩展脚本文件和通用 favicon。
- 原有布局的响应式 class 与移动导航 collapse 机制。

本次没有新增另一套主题或颜色系统。手机导航是否实际可用、页面是否有横向溢出，需要真实浏览器验证，不能仅由这些 class 的存在推定。

### 3.2 实际适配

| 范围 | 修改 |
| --- | --- |
| 品牌与导航 | 改为“页面集”；链接到真实存在的首页、报告、文章和关于页 |
| 首屏内容 | 改为报告与页面入口；原默认人像替换为项目文字，保留原布局背景 |
| 报告展示 | 使用现有报告标题和日期，不新增行情结论 |
| 履历和联系 | 不复制未提供的姓名、履历、联系方式或默认联系表单 |
| 模板占位 | 移除 Lorem ipsum、`Your Website`、`#!` 假链接和默认 profile 图片引用 |
| 字体 | 移除 Google Fonts 请求，增加系统字体回退 |
| 图标资源 | 移除本样例已不用的 Bootstrap Icons 外部样式 |
| JavaScript | 将上游导航所需 Bootstrap bundle 下载到本地，保持版本一致 |
| 基础可访问性 | 增加跳至主要内容链接、可见焦点、中文导航按钮标签及装饰 SVG 隐藏标识 |

适配过程以一次性研究脚本完成，脚本留在 `scratch/`；交付物中没有新建站点生成器或运行时模板引擎。

### 3.3 实际文件结构

```text
artifacts/site-option-personal/public/
  index.html
  reports.html
  notes.html
  about.html
  articles/
    template-integration.html
    second-content.html
  reports/513310/2026-11-20/index.html
  assets/favicon.ico
  css/styles.css
  css/site.css
  js/bootstrap.bundle.min.js
  js/scripts.js
  LICENSE-startbootstrap.txt
  LICENSE-bootstrap.txt
  LICENSE-popper.txt
```

最终样例共 **15 个文件、504,984 字节**，其中 7 份 HTML。该大小是未压缩文件总和，不等于一次页面访问的网络流量。

## 4. 原报告 URL 与字节是否保留

现有报告由 [正式源文件](../../docs/reports/513310/2026-11-20/index.html) 原样复制至样例同相对路径：

```text
reports/513310/2026-11-20/index.html
```

源文件和样例文件 SHA-256 均为：

```text
e7fbd1ecd16e6395a07adf1d6026ef3b81d5d8f6a1bc6d739a7227ab8867ddc2
```

首页和报告目录中的入口均指向该原报告。报告不套入 Personal 页面壳，不改动其行情日期、数据、来源、样式或交互。

在正式站点根目录采用本样例后，原有项目基路径加相对路径可继续组成同一报告地址。本次只在本地挂载验证了这个关系，没有覆盖线上页面。

## 5. 两种 base 路径的实际验证

本样例的导航、样式和脚本使用相对路径，文章页按自身深度引用 `../`。没有把 `/static-pages/` 或某个 PR 编号写死进资源链接。

对**同一份产物**分别进行：

1. 现有 `check_static_html.py` 全部 7 份 HTML 检查，包含首页收录检查。
2. 环回 HTTP 服务分别挂载到两个路径，对所有文件逐字节下载比较，并跟随 HTML 中本地链接读取目标。

| 挂载路径 | 静态检查 | HTTP 文件比较 | 本地链接目标 | 结果 |
| --- | --- | --- | --- | --- |
| `/static-pages/` | 7 页，退出 0 | 15 文件 | 15 个不同目标均可读取 | 通过 |
| `/static-pages/previews/pr-999/site-option-personal/` | 7 页，退出 0 | 同样 15 文件 | 同样 15 个不同目标均可读取 | 通过 |

每个 HTTP 挂载执行了 96 次请求，其中包含重复引用的检查；这不是浏览器真实加载请求数。`pr-999` 仅为本地路径夹具，不代表实际存在的 PR 或线上预览。

静态检查实际命令的正式路径版本：

```bash
python3 skills/static-page-builder/scripts/check_static_html.py \
  --root artifacts/site-option-personal/public \
  --page . --page reports.html --page notes.html --page about.html \
  --page articles/template-integration.html \
  --page articles/second-content.html \
  --page reports/513310/2026-11-20/ \
  --base-path /static-pages/ --require-homepage-link \
  --output scratch/site-options/personal/check-formal.json
```

嵌套检查仅替换 `--base-path` 与输出记录文件。没有修改检查器或放宽规则。

原始记录保存在忽略的 `scratch/site-options/personal/check-formal.json`、`check-nested.json`、`mount-results.json`。这些记录与本地 HTTP 脚本不进入公开产物目录。

## 6. 新增第二篇内容的实际步骤

首次样例只有“模板接入验证”一篇说明文章。保留该状态的文件快照后，实际执行以下操作：

1. 新增 `articles/second-content.html`，沿用第一篇文章的 HTML 页面壳，替换标题和正文。
2. 手动在 `notes.html` 增加一张文章卡片。
3. 手动在 `index.html` 的“最新内容”区域增加该文章入口。
4. 再次运行完整静态检查和两种路径挂载检查。

文件哈希比较确认：新增 1 份文件，已有文件中只有 `index.html` 和 `notes.html` 发生变化。原报告和资源文件保持相同字节。

因此，这条路线的日常编辑方式是 **HTML 正文＋显式列表维护**。本次没有把 Markdown 当作可直接发布的文章，也没有通过引入一个新生成脚本来隐藏该成本。

若以后只在文章列表提供新内容入口，可以少改首页；如果首页有最新内容、类别页和其他聚合入口，则各入口也需要同步维护，或另行建设元数据驱动目录。

## 7. 运行时依赖与功能边界

### 7.1 当前样例

- 本地 `css/styles.css` 包含主题与 Bootstrap 样式；外部 CSS 导入未发现。
- 本地 `js/bootstrap.bundle.min.js` 提供移动导航所需交互。
- 系统字体不发起 Google Fonts 请求。
- 没有加载外部图标字体、评论、统计或表单服务。
- HTML 静态资源引用扫描未发现 HTTP(S) 外部运行资源；报告中的来源超链接仍保留。
- CSS 中图标为 data URI，本地检查不将 SVG 命名空间当作网络请求。

这只是静态扫描与 HTTP 路径结果，不等于浏览器网络面板或完整离线行为已经验收。

### 7.2 未采用的联系表单

上游联系页使用 SB Forms，需要相应服务配置和 API token。本样例没有复制该页、表单 token 占位或 SB Forms 脚本，避免展示并不存在的联系能力。[上游 Contact Form 说明](https://github.com/StartBootstrap/startbootstrap-personal#contact-form)

### 7.3 与博客主题的差别

本样例没有自动文章目录、标签、分类、分页、RSS、全文搜索和 Markdown 生成。后续可以自行增加，但这些应作为新增实现评估，不能计为当前模板已经交付的能力。

## 8. 与现有发布机制的最小接入

### 8.1 可以直接复用的部分

- 当前 public 目录就是完整静态交付物，不需要在发布 job 中安装 npm 依赖或执行模板源码。
- 现有预览归档读取、横幅注入、manifest 和部署校验可以继续使用。
- 相对链接可在实际 PR 嵌套路径复用；正式收录时仍按真实授权、目录迁移和导航规则处理。
- 原报告独立保存，避免为了更换首页主题而重写历史内容。

### 8.2 仍需决策的部分

- 本样例作为整个站点入口使用时，获确认后才迁入相应正式位置；目前没有修改 `docs/index.html`。
- 采用上游主题不自动替代多 PR 预览、确认 SHA、main 草稿隔离或线上版本核验。
- 若目标收敛为简单个人首页，可重新评估所需发布能力；在实际规则变更前仍遵守本仓库约定。
- 首页数量和 README 正式列表仍需按本仓库流程更新，模板不会自动维护它们。

对于当前仓库，直接模板能明显减少 R09 的布局实现工作；对 R08 的自动目录需求帮助有限。R01–R04 是否全部实施，取决于最终保留的发布与审阅要求。

## 9. 源码维护与上游升级

本次采用直接维护 HTML/CSS 的方式，不依赖 Pug／SCSS 源码。上游 npm 构建会重新生成 `dist/`，因此正式采用后不能一边修改生成后的 HTML，一边假设重新运行上游构建会保留这些改动。

建议记录上游固定提交、本地适配说明、第三方依赖版本和产物检查结果。后续升级按以下方式进行：

1. 在隔离目录取得新的明确上游版本。
2. 比较它与本次固定版本的布局、样式和脚本差异。
3. 对本地品牌、导航、文章和资源适配逐项保留或重新应用。
4. 重做报告哈希、全部页面链接、双 base 及浏览器验收。

这种方式起步依赖少，但本地 HTML 改动较多时，上游更新需要人工合并。若内容持续增长，应把该维护负担与 Hugo/Jekyll 的配置和构建负担一起比较。

## 10. 许可与来源保留

本样例保留了上游样式、脚本中的版权头，并附带以下许可文件：

- Start Bootstrap 许可：`artifacts/site-option-personal/public/LICENSE-startbootstrap.txt`。
- Bootstrap 许可：`artifacts/site-option-personal/public/LICENSE-bootstrap.txt`。
- Popper 许可：`artifacts/site-option-personal/public/LICENSE-popper.txt`。

首页与关于页保留 Personal／Start Bootstrap 来源入口。没有复制上游默认人像或 dummyimage 示例图，也没有引入额外图片授权负担。本节记录本次来源与保留方式；正式采用时仍需核对最终使用版本及资源清单。

官方依据：[Personal 固定版本 LICENSE](https://github.com/StartBootstrap/startbootstrap-personal/blob/6a1ebcc76a93ead054412fcbdf417d9c83dc762b/LICENSE)、[Bootstrap 5.2.3 LICENSE](https://github.com/twbs/bootstrap/blob/v5.2.3/LICENSE)、[Bootstrap 编译产物说明](https://getbootstrap.com/docs/5.2/getting-started/download/)。资料查询日期：2026-11-21。

## 11. 实际完成与未完成检查

| 项目 | 本轮状态 |
| --- | --- |
| 固定上游提交并取得真实 dist | 已完成 |
| 直接静态适配，无 npm／Ruby／Hugo 构建 | 已完成 |
| 7 份 HTML 的现有检查器检查 | 正式与嵌套路径均通过 |
| 15 文件双挂载下载与字节比较 | 均通过 |
| HTML 本地链接目标检查 | 均通过 |
| 原报告 SHA-256 | 与正式源一致 |
| 第二篇新增流程与文件差异 | 已实际执行 |
| 占位内容与外部资源静态扫描 | 已完成，未发现遗留的示例占位或外部运行资源引用 |
| 手机／桌面视觉、键盘和 collapse 行为 | 主任务统一 Chromium 已完成副标题精简后的最终回读；两种 base、375/768/1440 宽度无横向溢出，移动导航 Enter 操作成功，详见统一验证记录 |
| 实际 GitHub Pages 预览与部署 | 未执行 |

浏览器初轮检查发现首页副标题在 375px 下出现单字尾行，已仅将文案精简为“按主题与日期整理内容”，保留原布局，并重新通过全部静态检查与两种路径挂载检查。该文案调整后的最终浏览器回读已完成，见 [统一验证记录](VALIDATION.md)。

上述检查不改变现有正式站点。样例是可审阅的本地产物，后续仍需按选定路线完成实际预览、适用的交互验收和具体版本确认。

## 12. 适用建议

优先考虑此路线的情况：已有内容主要是独立 HTML 报告或工具，需要一个稳定、可定制的入口，新增普通文章频率较低，希望减少构建工具依赖。

如果主要目标转为长期写 Markdown 博客、自动归档或多类别内容积累，建议将此样例作为最小接入成本的对照，再结合另外两条生成器路线的实际构建结果做最终选择。
