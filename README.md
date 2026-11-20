# Static Pages · 统一静态页面仓库

[打开页面目录](https://wvliteam.github.io/static-pages/)

所有报告与独立静态页面统一存放在这个仓库，通过不同目录直接访问。新增页面无需创建仓库或单独配置 GitHub Pages。

## 已发布页面

- [513310 · 2026年11月20日收盘复盘](https://wvliteam.github.io/static-pages/reports/513310/2026-11-20/)：分时与日K、量能、溢价、关键价位及情景计算器。

## 目录约定

```text
index.html                         # 导航首页
.nojekyll
reports/<证券代码>/<日期>/index.html # 按标的与日期归档的报告
pages/<页面名称>/index.html         # 其他独立静态页面（按需新增）
tools/<工具名称>/index.html         # 独立工具（按需新增）
```

每个目录放置 `index.html` 后，可以直接访问对应目录地址，不必填写文件名。页面资源使用相对路径；不得假定站点位于域名根目录。

## 发布

GitHub Pages 已配置从 `main` 分支的根目录 `/` 发布。保留 `.nojekyll`，推送后由 GitHub 自动部署。

新增页面时，将网页和所需资源加入独立目录，更新首页入口和本文件的页面列表，然后提交并推送。已归档的历史报告保持原日期，不覆盖为其他交易日。

此仓库由原 `513310-market-brief` 改名而来，保留提交历史。旧 GitHub Pages 网址不再作为访问入口。

行情来源与计算口径见各报告页面。行情研究页面仅用于研究与条件分析。
