# Static Pages · 统一静态页面仓库

[正式页面目录](https://wvliteam.github.io/static-pages/)

报告、页面和小工具统一使用此仓库。草稿在独立分支中审阅，通过后才合入 main；预览和正式站点都由 GitHub Pages 托管。

## 已发布页面

- [513310 · 2026年11月20日收盘复盘](https://wvliteam.github.io/static-pages/reports/513310/2026-11-20/)：分时与日K、量能、溢价、关键价位和情景计算器。

## 分支与目录

| 分支 | 内容 | 用途 |
| --- | --- | --- |
| `main` | `docs/` 中的正式网页、工作流、skill | 已确认版本 |
| `preview/<task>` | `artifacts/<task>/public/` 中的可审阅网页 | PR 审阅 |
| `gh-pages` | 工作流生成的正式页面与全部活动预览 | 部署产物，勿手动编辑 |

```text
.github/workflows/pages.yml        # 统一构建和部署
scripts/                          # 可信的静态发布脚本
tests/                            # 发布规则测试
skills/static-page-publisher/     # 可安装、可版本追踪的页面创建与发布 skill
docs/
  index.html                      # 正式导航首页
  .nojekyll
  reports/<代码>/<日期>/index.html
  pages/<名称>/index.html
  tools/<名称>/index.html
artifacts/<task>/public/index.html # 只存在于 preview 分支，确认后迁到 docs
scratch/                          # 本机源数据、日志、截图，Git 忽略
```

## 创建与预览

1. 从最新 main 创建 `preview/<task>`，在 `artifacts/<task>/public/` 分阶段创建网页；task 为小写字母、数字和连字符。
2. 提交 HTML 和必要资源，推送并创建指向 main 的同仓库 PR。不要上传原始账户资料、临时依赖或整个工作区。
3. PR 打开、更新或重新打开时，Actions 自动生成 `/previews/pr-<编号>/<task>/`。具体链接见 Actions 运行摘要，主站的 `deployment.json` 记录 PR head SHA 和生成网页哈希。
4. 通过在线预览检查内容和交互。预览自动加“预览稿”及 noindex；不加入正式导航，也不修改正式页面。

预览可公开直达，noindex 只是搜索引擎提示，不提供权限控制。工作流仅处理同仓库、分支名以 `preview/` 开头的活动 PR。它只复制 `artifacts/<task>/public/` 里的普通文件，不执行预览分支代码。

## 确认并正式发布

用户确认当前预览版本后，在 PR 分支将最终文件移动到对应 `docs/` 正式目录，清理该任务的 tracked artifacts，并更新导航与上面的正式列表；然后合入 main。不能把草稿目录直接合入 main。若移动后 artifacts 已为空，该 PR 的临时预览会在下一次部署中消失，确认记录仍对应此前检查的 head SHA。

main 更新会自动部署正式版本；PR 关闭或合并后，下次成功部署会清理对应预览。网页日期快照保持原日期，不能被其他交易日覆盖。

## 部署实现

Pages 的发布类型是 GitHub Actions。每次使用最新 main/docs 和所有符合条件的活动 PR 组合完整站点，保留正式页原字节，预览输出到 `previews/pr-<编号>/`。产物快照保存在 gh-pages，并在同一次 workflow 中通过官方 upload-pages-artifact / deploy-pages 发布，不依赖 GITHUB_TOKEN 推送触发第二次构建。运行互斥，避免相互覆盖；构建产物只保留1天。

`deployment.json` 包含 main SHA、正式文件哈希、活动预览及其 PR head SHA，供上线核对。失败时现有部署保持不变。可在 Actions 中手动运行 `Publish site and PR previews` 重建。

## Skill

[static-page-publisher](skills/static-page-publisher/SKILL.md) 与流程一起版本管理。它涵盖分阶段建页、UI 与数据核对、分支预览、正式批准、部署验证。仓库内仅保留可移植说明与脚本；账号配置通过仓库远端、AGENTS.md 和会话确定，不包含本机绝对路径或凭据。skill 不属于 docs，不会被当作网页发布。
