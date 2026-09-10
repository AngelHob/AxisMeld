# AxisMeld 五小时开发批次

## 授权与时限

用户于 2026-09-10 要求继续开发 5 小时，把需要手工确认的内容集中起来统一审核。
本轮允许在既有方向内安排局部实现与测试，不逐项等待视觉偏好确认；这不是全局架构、
数据风险、外部发布或上游合并的无限授权。保留设计先行、测试驱动和独立审查门槛。

- 起点：2026-09-10 23:53:35 Asia/Shanghai。
- 截止：2026-09-11 04:53:35 Asia/Shanghai；04:23 起停止新切片，优先回归和交付。
- 当前任务续作自动化：`axismeld`；每 10 分钟唤起当前任务，最晚调度至 05:00。
  到截止时必须停止新增实现；最后一次只整理状态并停用此自动化。不新建任务，不重复创建自动化。
- 时间是工作窗口，不承诺 5 小时不间断计算；记录实际进展。若应用休眠、额度或环境中断，
  恢复时先核对截止时间，不能通过顺延窗口掩盖中断。

## 当前基线（现场核验）

- 仓库 `D:/source/AxisMeld-phase0`，现有 linked worktree，分支 `axismeld/phase-2a`。
- 起始提交 `137c428cf0d`；原生 Style 入口、二级 4px 间隔、窄窗避让已完成。
- 构建 `D:/source/AxisMeld-build`；复用 `phase2b-ui-test-install/blender.exe`。
- 起始 exe SHA-256：`32BF08140F8F66DE0E832455E6D7B2189A4836ACC79049FA2E424A2EB5A92C1D`。
- 回退 `phase2b-roomy-test-install/blender.exe` 不动，SHA-256：
  `F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`。
- 当前 portable 6 文件和 tight-entry 备份一致；后续安装前重新备份实际配置并逐文件核验，
  不把历史报告中的 rows 恢复操作再执行一次，不复制个人配置进发行默认值。
- 本轮起始纯测试：30 项 native 布局 + 26 项 hotbox Python + 14 项输入通过。
  证据 `batch5h-baseline-native.log` / `batch5h-baseline-python.log`；当前 GUI 基线见
  [上一轮报告](../compatibility/2026-09-10-native-entry-tight-gap-report.md)。

## 产品范围和顺序

1. **设置目录组合**：沿用 [组合规范](../design/hotbox-menu-composition.md)，把 Menu Rows、
   Transparency 等纯选项列表也接入原生连续菜单；保留 Views 快捷动作环、父级显示、字号、
   真实原点与所有松键行为。先处理短列表，再处理长的中心鼠标映射列表和分页/滚动。
2. **稳定性与可读性**：针对前述新增内容测试窄窗、高 DPI、真实原点、disabled/hover、
   点击/按住划选、Back/Space/Esc、配置即时生效；遇到可复现缺陷先修复。
3. **低风险建模适配（前两项通过且时间足够才做）**：优先已有 Blender 原生 operator
   能准确说明的选择全选/清空/反选、选择扩展/收缩/连通，以及安全可撤销的重复对象入口。
   先检查 Maya 默认语义与本地 Blender 实现，差异标记 adapted；新增语义 ID、能力检查、
   上下文限制和安装态真实行为测试，不污染已公布默认快捷键、不用空操作解锁目录。
   不强求本批涵盖所有候选项，少而完整优先于大量未验证菜单。
4. **集中交付**：全量相关回归、最新构建身份、统一改动表、单一人工清单和已知差异。

## 明确不做

- 不重启 Global 物体缩放开发；不改 UV 算法、Mesh/UV 数据结构或 .blend 格式。
- 不修跨新窗口全局释放 guard，不解锁文件/新窗口命令，不猜测未复现输入故障。
- 不覆盖工作场景、个人配置；不关闭用户 Blender；运行中 stage 不安装。
- 不增加完整测试安装目录、不自动删除旧版本、不推送/发布/合并上游、不安装新依赖。
- 遇重大取舍写入验收表待决，转做其他已授权切片；必要的新权限才即时向用户请求。

## 每个切片的执行契约

- 读取当前 git status、本文最新进度及相关源码，不能凭旧计划勾选状态判断未实现。
- 先补局部设计/实现计划，再写能在旧实现上失败的测试，记录 RED，然后实施 GREEN。
- 输入坐标夹具仅负责投递事件；真实命令/设置/场景结果必须独立断言，不为绿灯删行为断言。
- 原生代码改动构建 blender 和对应测试 target；普通 Python 改动也需安装态核验。
- GUI runner 必须串行、隐藏、factory-startup、私有 TEMP 和用户配置；不触碰用户会话。
- 独立代码审查按技能执行；不得为并行而并行修改共享文件/构建/GUI。
- 每批测试通过后本地提交；人工尚未验收不能标为正式发布通过。
- 一次执行可持续完成多个切片；无需为了下一次 10 分钟唤起空等，临近截止优先收尾。
- 更新本文的进度、下一步以及 [集中验收表](../compatibility/2026-09-10-batch-review.md)。
  下一轮直接接续；调度唤起本身不算开发成果、不需要向用户重复报告。

## 工具与验证入口

Python `C:/Python314/python.exe`；CMake/CTest 位于
`C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/`。
clang-format：`lib/windows_x64/llvm/bin/clang-format.exe`。

```powershell
& C:/Python314/python.exe -m unittest discover -s tests/python -p 'axismeld_hotbox_*_test.py'
& C:/Python314/python.exe tests/python/axismeld_input_test.py
& D:/source/AxisMeld-build/bin/tests/Release/axismeld_hotbox_menu_test.exe
```

构建使用 `--build D:/source/AxisMeld-build --config Release --target blender axismeld_hotbox_menu_test --parallel 8`。
仅安装至 `--prefix D:/source/AxisMeld-build/phase2b-ui-test-install`，不使用默认旧 install。
CTest 定向正则 `^(axismeld_(hotbox_menu|hotbox_state|identity|transform_axis)|editor_hotbox_hotbox_model)$`。

GUI：`tests/python/axismeld_hotbox_ui_runner.py --blender <stage exe> --suite native-style|menus|hotbox|release|profiles`；
`tests/python/axismeld_manipulator_ui_runner.py --blender <stage exe>`；附加 menus 专项每次只设一个环境变量：
`AXISMELD_TEST_OVERLAY=1`、`AXISMELD_TEST_DRAG_GUIDE=1`、`AXISMELD_TEST_NAVIGATION_PROBE=quad`。
日志统一 `D:/source/AxisMeld-build/batch5h-<slice>-<check>.log`，最终报告不得引用中间失败构建冒充最新成果。

## 进度（每次实际执行后更新）

| 批次 | 状态 | 结果 / 下一步 |
|---|---|---|
| 0：准备 | 完成 | 读取现有实现和范围；复用工作树；起始纯测试通过；定时续作与集中验收表已建立 |
| 1：短设置列表原生菜单 | 待实施 | 从 Menu Rows / Transparency 开始，执行下面链接的独立小计划 |
| 2：映射列表及交互回归 | 未开始 | 只有批次 1 通过后细化，不提前宣称完成 |
| 3：常用建模适配 | 未开始、时间允许才做 | 先能力/语义与数据安全审查，逐命令完成测试再接通菜单 |
| 4：收尾 | 未开始 | 04:23 起集中回归，04:53 截止；停止自动化并交付统一报告 |

**下一步明确入口：** [短设置列表计划](../superpowers/plans/2026-09-10-hotbox-settings-lists.md)。
先读取该计划涉及实现和测试，再按 TDD 执行，不再次要求用户单独确认视觉偏好。
