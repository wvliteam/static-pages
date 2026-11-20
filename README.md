# Static Pages · 统一静态页面仓库

[打开页面目录](https://wvliteam.github.io/static-pages/)

所有报告与独立静态页面统一存放在这个仓库，通过不同目录直接访问。新增页面无需创建仓库或单独配置 GitHub Pages。

## 已发布页面

- [513310 · 2026年11月20日收盘复盘](https://wvliteam.github.io/static-pages/reports/513310/2026-11-20/)：分时与日K、量能、溢价、关键价位及情景计算器。

## 目录约定

```text
artifacts/<任务>/                   # 草稿、源数据与临时产出，仅本地保留，不提交
docs/                               # 唯一的 GitHub Pages 发布源
  index.html                        # 导航首页
  .nojekyll
  reports/<证券代码>/<日期>/index.html
  pages/<页面名称>/index.html
  tools/<工具名称>/index.html
```

每个目录放置 `index.html` 后，可以直接访问对应目录地址，不必填写文件名。页面资源使用相对路径；不得假定站点位于域名根目录。

## 发布

GitHub Pages 从 `main` 分支的 `/docs` 发布。保留 `docs/.nojekyll`，推送后由 GitHub 自动部署。发布目录前缀 `docs/` 不出现在网址中，现有页面地址不变。

先在 `artifacts/<任务>/` 创建完整可审阅的页面并检查。用户确认本次具体产出可以发布后，才将最终网页与必要资源复制到 `docs/` 的对应目录，更新 `docs/index.html` 和本文件的页面列表，再提交并推送。已归档的历史报告保持原日期，不覆盖为其他交易日。

`artifacts/` 由 `.gitignore` 排除，新检出可按需用 `mkdir -p artifacts` 创建。不要使用 `git add -f` 上传临时文件，也不要将整个任务工作区复制进 `docs/`。GitHub Pages 不提供公开站点的逐目录权限控制；公开仓库中已提交的文件仍可通过 GitHub/Raw 访问，所以“不发布草稿”同时依赖发布源隔离与不提交临时文件。

此仓库由原 `513310-market-brief` 改名而来，保留提交历史。旧 GitHub Pages 网址不再作为访问入口。

行情来源与计算口径见各报告页面。行情研究页面仅用于研究与条件分析。
