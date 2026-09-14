# Maya 创建与建模伴随菜单验收

本轮按用户截图对齐菜单内容、顺序和分组，不删除未实现占位。Object 保留 22 个主项、7 个细分隔；创建新增 16 个主项、3 个细分隔。创建八方向及 Object 五个指定方向补齐独立 Options 格；本轮新增参数格均灰显，不执行主动作，已有 Object 修改器参数入口保留。

创建列表复用现有 Icosphere、Pyramid、Prism、Text 与 Backface Culling 命令；Platonic Solid 明确只是 Blender Icosphere 适配，其余 Maya 专有生成器及交互创建保留灰显原因。Interactive Creation 显示禁用未勾选，Exit On Completion 显示禁用勾选，不写入全局偏好。Soften/Harden 目录依据本机 Maya 2026 `scripts/others/contextPolyToolsObjectMM.mel:139-176` 保留四项顺序及独立参数格；本轮全部灰显，不以其他着色命令替代。

普通行保持 24 逻辑像素，分隔为 6 像素；分页、命中、级联定位和遮挡共用实际高度。Options 独立占 24 像素，径向主按钮加参数格的整体内缘与 Views 标杆一致。实际净距 1×为 95/127/95 像素，单视图 2×为 185/249/185 像素。各参数格现在分别绘制背景，修复连续参数列遮住 Mapping、Booleans 子菜单箭头的问题；布局和命中不因此改变。

完整 JSON 快照上限从 256KiB 调整为 512KiB，不删字段、标签或原因；2048 节点及深度限制未放宽。真实目录 1461 节点、深度 7，默认快照 251934 字节，包含 10 个 Recent 及已知禁用上下文的压力样本最大 272786 字节。边界测试确认恰好 512KiB 可接受，多 1 字节拒绝。

## 最终验证

- Python 125 项通过：`D:/source/AxisMeld-build/maya-companion-python-green.log`。
- 原生 CTest 6 组通过：`D:/source/AxisMeld-build/maya-companion-native-green.log`。
- 最终候选完整跑过以下 12 套真实 GUI 回归。独立静态复核及 `git diff --check` 通过；静态复核不替代 GUI 或人工结果。

| GUI 套件 | 最终日志 |
|---|---|
| maya-companion | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-new-green.log` |
| icons | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-icons-green.log` |
| object-menu | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-object-menu-green.log` |
| object-modeling | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-object-modeling-green.log` |
| context-modeling | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-context-modeling-green.log` |
| create | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-create-green.log` |
| components | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-components-green.log` |
| tools | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-tools-green.log` |
| modeling | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-modeling-green.log` |
| menus | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-menus-green.log` |
| native-style | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-native-style-green.log` |
| release | `D:\source\AxisMeld-build\maya-companion-batch-v2\maya-companion-release-green.log` |

新增套件覆盖两种目录的完整内容、顺序、分隔高度、变高分页、独立参数格、子目录、禁用工作流勾选、四角、1×/2×、重复唤出和取消。Platonic Solid、Pyramid、Prism、Type 实际创建并各自单次 Undo；Backface Culling 只切换视口显示。Mapping、Booleans、Polygon Display 的右侧箭头像素在 1×均为 24，在 2×均为 84；修复前前两者均为 0，实际 RED 图与日志保留在 `maya-companion-arrows-red.log` 及对应 artifacts。

正常主题原图为 `D:/source/AxisMeld-build/maya-companion-normal-object.png` 与 `maya-companion-normal-create.png`，均为 1920×1080，分别完整显示 22/16 个主项，已独立查看。回执记录两图哈希。前一轮全部测试、原图和回执保留在 `maya-companion-batch-v1`；最终结果明确使用 `maya-companion-batch-v2/log-map.json`。

## 已知边界与失败证据

伴随列表可能占据原 S 方向长划落点。列表区域优先命中列表或独立参数格；禁用行、分隔与遮挡间隔不穿透执行径向动作，只有未被菜单遮挡的区域继续支持外延。旧创建回归现在验证七个方向成功，其中六个有效方向长划，S 在 Cube 主行释放。旧 S=-260 实际命中 Soccer Ball 的图保留；S=-82 的失败创建断言与取消一致，不宣称该坐标已被单独完整 GUI 状态断言覆盖。

其他早期失败涉及测试观察器截掉 2× 字形下伸部分、角落落入真实 Header，以及把 Texture Border Edges 后缀当作 Border Edges。相应失败图片和调整依据均保留，未降低文字阈值或列对齐断言。最后普通主题复核发现的箭头遮挡是真实生产显示缺陷，已单独修复并重跑上述 12 套，不能归为测试脚本问题。

不足以容纳主环与最低分页列表的 2×小四视口仍安全拒绝，验证场景不变、无残留 modal 且下一次 Views 输入可用；未缩小 Views 留白。释放套件覆盖同一窗口释放，不补造跨窗口结论。本轮未额外重跑 profile、保存配置启动或未修改的 launcher；复制配置以文件哈希核验。实体鼠标、个人布局及系统 125/150/200% 缩放由人工清单继续确认。

## 安装与人工记录

最终候选：`D:/source/AxisMeld-build/maya-companion-test-install/blender.exe`。

程序 SHA-256：`9E84E857BB41BC8E073ECE0BF782678BB0D51D1F4141441631ED3165FA21A173`。

配置来自 `hotbox-icons-test-install/portable/config`。独立脚本 `C:/Users/张吴斌/Documents/Codex/2026-09-12/new-chat/work/verify_maya_companion_install.py` 核对构建与安装程序、28 个 Python 资源、4 个复制配置、129 个旧文件、最终 12 套 GUI 日志、125 项 Python 与 6 组原生测试。无缺项运行生成 `D:/source/AxisMeld-build/maya-companion-install-verification.json`，记录源码 HEAD、修改状态、生产文件与全部证据哈希；内嵌 build-info 可能仍保留编译时的父提交，应按回执判断来源。

统一人工目录共 191 项，初始历史已测试 47 项、待测 144 项，其中本轮新增 MC-01 至 MC-14 共 14 项。历史 47 项逐行与原基线一致；已测试不等于逐项通过，自动化不改人工状态。私人网页已实现服务端保存、同账号多设备读回、版本冲突拒绝和身份限制；源码独立位于 `D:/source/AxisMeld-test-tracker`。后续用户进度以网页服务端记录为准，更新目录不覆盖已保存状态。
