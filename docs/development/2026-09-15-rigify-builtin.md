# Rigify 默认内置模块

## 用户确认与范围

用户选择将 Rigify 自动绑定工具作为 Blender 默认模块提供，无需安装或启用插件。本次保留现有 Rigify 0.6.10 算法、operator 名称、RNA 属性、metarig 和生成骨架数据；不把 AxisMeld 的 Maya Rigging 灰占位冒充已经适配。

## 设计

- 将 `scripts/addons_core/rigify` 移至 `scripts/modules/rigify`，保留 `import rigify` 及全部内部相对路径。新增 `scripts/startup/rigify_builtin.py`，在原生 UI 注册后加载、在脚本重载及退出时反向卸载，脱离 `addon_utils.enable` 生命周期。
- 旧 `preferences.addons['rigify']` 仅用作与现有配置兼容的偏好存储；缺失时创建，不改动已有内容。插件管理器明确识别原生模块，跳过扫描、自动 enable/disable 和缺失插件提示，防止旧配置或残留安装造成第二次注册。
- Preferences → Animation 增加 Rigify 设置面板，复用现有 Feature Sets 设置绘制。原生 Add → Armature、骨架属性和生成控制器继续使用 Rigify 自己的入口。
- 通过成对的 persistent `_extension_repos_update_pre/post` 处理普通/工厂偏好重读：替换偏好前注销实际已注册的外部 Feature Sets；替换后按新的偏好恢复。原生 Rigify 始终存在，外部 Feature Sets 仍由用户选择。未记录的扩展包不因本次内置化自动开启。
- 新安装只保留一份 Rigify 模块；保留旧发布包不覆盖。使用全新隔离配置验证，当前个人配置和场景不参与测试输入或发布。

## 实施计划

- [x] 在旧构建以 `--factory-startup` 验证 metarig、generate 和 Rigify RNA 缺席，留存失败证据。
- [x] 迁移包、加入原生启动与设置面板，保留旧偏好存储及 Feature Sets 生命周期。
- [x] 插件管理器隔离原生 Rigify；旧配置、用户残留脚本与 reload 不重复注册。
- [x] 隔离候选验证工厂/普通启动、实际生成骨架、保存后新进程重开、两次 Reload Scripts、普通/工厂偏好重读与禁用扩展状态。
- [x] 实际 GUI 验证 Add → Armature 和 Preferences → Animation 入口，复查建模菜单保持。
- [x] 更新 RG 人工测试清单、公开网页与修改日志；提交推送源码，发布与源码对应的新便携包，匿名核验。

## 验证边界

生成 operator 返回 `FINISHED` 不足以证明成功，必须验证 metarig 指向的真实目标骨架、DEF/控制骨、约束与保存数据。自动验证不代替用户对骨架变形质量和第三方 Feature Sets 的人工验收。

额外验证已覆盖已启用扩展的偏好重读与两次脚本重载，每次注册/注销严格配平；恢复工厂偏好后可选包保持关闭。初始化中的参数注册或设置面板注册失败均已注入复现，修复后清理 RNA、回调和面板，再次正常注册成功。候选共 136 项审计资源，原生程序 SHA256 为 `969c97c527df661df34fea41400ecea921195550c6440b697fc505683ac9fb29`。

## 发布验收 · 2026-09-16

源码 `3a673dcf1e078d277f87a985724bb4be0b3be654` 对应 [Rigify 内置预览版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.15-rigify-preview)。ZIP 为 294,922,072 字节，SHA256 为 `7ad57bf6a11a9266c6c834107d856bce471d9eb1080f34bf619641f57cf6bacf`；GitHub 资产摘要与本地一致。重新解压后启动通过，独立审计核对全部 136 项资源、88 个 Rigify 文件和许可证，未检出个人配置或测试输入。

[公开测试页](https://angelhob.github.io/AxisMeld/) Pages 提交 `8a2e1010735702693c42eb32c1ee6ff53fd62ca7` 已部署。匿名获取的六个静态文件与部署提交逐字节一致；6 项线上浏览器验收通过，覆盖 300 项目录、6 项新增 RG、有效下载、记录重载、独立访客和正确反馈版本。未向 GitHub 提交测试 Issue，自动结果不改变人工待测状态。
