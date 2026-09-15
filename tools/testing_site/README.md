# AxisMeld 公开测试门户

原生 HTML、CSS、JavaScript 静态页面，可放在 GitHub Pages 的 `/AxisMeld/` 子路径，无构建依赖、CDN、分析脚本或后台写入。所有资源使用相对路径。

## 数据与记录

- `config.json` 是项目、构建、下载与反馈入口的单一配置来源。只有发布完成后才填写真实 `releaseUrl`；为空时下载按钮明确显示尚未发布。
- `catalog.json` 只包含可公开的测试编号、标题、分组、操作步骤和预期结果。不得放入私人服务地址、本机路径、令牌、个人备注或私人服务器测试记录。
- `items` 的必填字段：`id`、`title`、`group`、`steps`（字符串数组）、`expected`（字符串数组）。可选 `isNew`、`superseded`、`maintainerStatus`。`superseded` 表示历史条目，不作为当前构建验收，默认不显示但可切换查看。
- `maintainerStatus` 仅展示维护者已公开的历史测试信息。每个新访客的初始状态始终为「待测试」，不会继承维护者记录。
- 访客的状态、备注、测试版本仅保存到当前浏览器的 `localStorage`，不自动上传、不跨设备同步。JSON 导出用于自行备份或作为反馈附件。浏览器禁止存储时会明确提示记录尚未持久保存。

## 反馈

默认 `feedback.mode` 为 `github`。点击条目「创建公开反馈」会先预览，再打开 GitHub Issue 的预填页面；使用者仍需登录 GitHub 并自行确认提交。页面不会创建 Issue，不会把本地勾选误报为已提交维护者。

Issue 包含测试编号、构建版本、结果与备注。备注最多 2000 字符；URL 较长时使用只预填简短标题的链接，保留完整正文并提示复制粘贴，也可导出 JSON 后在 GitHub 手动附加。`feedback.mode` 可改为 `external` 并设置公开 HTTPS `externalUrl`，或 `disabled`。不得配置私人 Site 地址、局域网或本机地址。

## 本地预览与校验

在此目录运行 `python -m http.server 8765 --bind 127.0.0.1`，打开 `http://127.0.0.1:8765/`。直接双击 HTML 会受到浏览器本地文件加载限制，请使用 HTTP 预览。

`python tests/validate_site.py` 检查公开配置、目录内容、唯一编号与静态资源引用。`node tests/state_check.mjs` 验证状态、筛选和反馈等独立逻辑。`tests/browser_check.mjs` 是使用 Playwright 的维护者浏览器验收脚本；Playwright 仅用于开发校验，不是网站运行依赖。它在 `/AxisMeld/` 前缀下验证首次进度、状态/备注/版本持久化、筛选、分页、反馈编码、历史条目、窄屏和注入文本安全性。浏览器测试不会提交 Issue。

浏览器脚本默认使用本机 Edge；可通过 `PLAYWRIGHT_MODULE` 指向本机 Playwright 的 `index.mjs`，通过 `BROWSER_EXECUTABLE` 指定其他 Chromium 浏览器。运行 `node tests/browser_check.mjs <审计输出目录>` 会启动临时环回 HTTP 服务，结束后自动关闭浏览器与服务；截图、导出样本和 JSON 报告只写入指定审计目录。

部署时仅发布本目录的前端文件；`tests/` 与本 README 无需作为运行资源。不得将私人测试站点目录或其数据库一并发布。
