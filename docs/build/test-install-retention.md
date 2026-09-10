# 测试安装保留规则

用户于 2026-09-10 要求清理旧测试版本，避免构建产物持续膨胀。

- 测试安装常态只保留两份：当前待验收版，以及最近一个可回退版。
- 不删除正在运行的版本；若它不属于上述两份，暂时额外保留，待用户退出后再清理。
- 新版本验证后轮换清理，不为每次中间修复长期保存一整套程序。不设置后台定时删除。
- 清理对象仅限已核实的旧测试安装目录；源码、Git、依赖、增量编译缓存、普通 `install` 和测试证据不在此规则中自动删除。
- 删除前核对绝对路径、目录链接、运行进程和额外文件；先备份 `portable` 中的个人配置，并逐文件校验。
- 程序副本可从源码重新构建，因此旧程序目录可永久删除以实际释放空间；配置备份与删除记录单独保留。

## 2026-09-10 清理

最新原生 Style 入口／4px 二级间距更新继续复用 `phase2b-ui-test-install`，未新增
完整程序副本。安装前确认 Blender 未运行，6 个 portable 文件已备份至
`D:/source/AxisMeld-build/preserved-test-configs/2026-09-10-tight-entry/phase2b-ui-test-install/portable`。
本次不修改个人配置（当前用户已将 hotbox settings 清为空对象），安装后逐文件哈希
与该备份一致；不把此前报告中的 rows 恢复操作再次套用。回退目录保持不变。

紧凑二级／原生 Style 更新继续复用 `phase2b-ui-test-install`，确认旧用户进程退出后再安装。
最新 6 个 portable 文件备份至
`D:/source/AxisMeld-build/preserved-test-configs/2026-09-10-compact/phase2b-ui-test-install/portable`，
复制后逐文件 SHA-256 校验。仅按用户要求把 `hotbox_user.json` 的 style 从 zones 恢复为 rows，
其他配置保持不变；`phase2b-roomy-test-install` 未覆盖，无新增整套测试安装目录。

后续二级叠加修复继续复用 `phase2b-ui-test-install`，覆盖前确认其未运行。最新
`portable` 的 6 个文件备份至
`D:/source/AxisMeld-build/preserved-test-configs/2026-09-10-overlay/phase2b-ui-test-install/portable`，
逐文件 SHA-256 校验。`phase2b-roomy-test-install` 保持不变，无新增完整安装目录。

本日后续参考图修复复用了未运行的 `phase2b-ui-test-install` 作为新测试版；正在运行的
`phase2b-roomy-test-install` 原样保留为回退版。覆盖前，旧 ui 版 `portable` 的 5 个文件
已复制到 `D:/source/AxisMeld-build/preserved-test-configs/2026-09-10-reference/phase2b-ui-test-install/portable`
并逐文件 SHA-256 校验；安装不删除个人配置。没有新增整套测试安装目录。

以下为此前清理时的历史记录，不表示目录仍对应同一个构建：

保留当前 `D:/source/AxisMeld-build/phase2b-roomy-test-install` 和上一版 `phase2b-ui-test-install`（清理时正在运行）。

拟清理的两份旧程序为 `phase2a-test-install`（921,931,167 字节）、`phase2b-test-install`（922,172,850 字节），合计约 1.72 GiB。

当前执行环境拦截了递归删除命令，未删除任何旧目录，也未释放上述空间；不尝试绕过安全策略。两份 `portable` 内容已复制到 `D:/source/AxisMeld-build/preserved-test-configs/2026-09-10/` 下对应版本目录，10 个文件共 367,712 字节，逐文件 SHA-256 与原件一致。待用户手工删除两份旧程序目录后再核验；不要误删当前与回退版本。
