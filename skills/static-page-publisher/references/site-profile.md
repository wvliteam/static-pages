# 仓库配置与可移植性

技能本身不固定本机路径和账号。优先读取用户指定仓库的远端、README 和 AGENTS.md，确定统一站点、默认分支、URL 基路径及发布工作流。没有指定且上下文无法推断时，先完成本地页面再澄清目标。

此版本随 `wvliteam/static-pages` 统一仓库维护，其仓库文档是该站点配置的依据：

| 项目 | 当前约定 |
| --- | --- |
| 正式源 | main 的 docs/ |
| 预览分支 | preview/<task> |
| 预览文件 | artifacts/<task>/public/，task 为小写字母、数字、连字符 |
| 本地私有工作文件 | scratch/，Git 忽略 |
| 发布产物 | gh-pages 分支与官方 Pages 部署 artifact |
| 预览 URL | 站点基 URL + previews/pr-<编号>/<task>/ |
| 正式 URL | 站点基 URL + reports/<代码>/<日期>/ 或 pages/<名称>/、tools/<名称>/ |
| 公开部署记录 | 站点基 URL + deployment.json |

只提交将用于浏览的静态文件。不得把原始账户数据、凭据、下载的浏览器或工作区绝对路径写入公开内容。

若在其他仓库使用此 skill，需要明确配置相同预览机制，或采用实际可用的预览提供商。不要误以为新建 preview 分支后 GitHub 就会自动产生预览网址。

技能与站点分开：`skills/static-page-publisher/` 只作版本管理，部署只读取 main/docs 及符合条件的 PR public 目录。不要将 skill 放进 docs 或 public。
