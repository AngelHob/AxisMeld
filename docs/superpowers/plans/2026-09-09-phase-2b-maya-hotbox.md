# Phase 2B Maya 主热盒 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Space 主菜单 → 中央鼠标七视图的两层热盒，并接通基础命令、分层配置与安全退出。

**Architecture:** 保留现有视图缓存及原生区域注册接点。Python 管声明式目录、配置、能力及语义调用；原生侧持有校验后的只读快照，负责布局、命中和完整按键生命周期。每次命令提交才进入适配层，鼠标移动不进入 Python。

**Tech Stack:** 当前 Blender 5.3.0 Alpha 源码、C++、内置 Python、BLI serialization、GTest、unittest、现有隐藏 GUI runner；无新外部依赖。

**Spec:** [已批准的 Phase 2B 规格](../specs/2026-09-09-phase-2b-maya-hotbox-design.md)。同时完整读取 [菜单清单](../../maya-mapping/hotbox-maya2026.md)。

状态：用户已确认逐项子代理实现与审查，进入执行；进度记录在本计划专属 SDD ledger。执行基线 `4a6ea4c819c`；该提交没有新版热盒实现。
续作顺序：先完成用户新增的镜头双轴/方向修复并审查，再继续 Task 3–5。跨新窗口交接按更新规格
延期；所有新开窗口命令仍禁用，保留其失败诊断。热盒主界面未接入前不得称新版交互可用。

## Global Constraints

- Global 对象缩放保持 Blender 原生行为，无开发计划；Phase 1.1 的审核状态不因本规格改变。
- 本轮不扩大 Space 的生效范围：仍仅本预设的 3D WINDOW，Object 或 mesh Edit Mode。
- 默认触发 Space，使用实际 invoke 键追踪释放。短按默认 0.4 秒，范围 0.1–1.0 秒；等于阈值为保持。
- 中央死区仍为 12 个逻辑像素；本轮受支持视口下限为 480×320 逻辑像素，测试 UI 缩放 1.0、1.25、1.5、2.0。
- 行序：公共、当前视窗、中央、Modeling。不得将七视图直接作为第一层。
- 默认未自定义中央 LMB/MMB/RMB 都是七视图；RMB 是核心人工验收路径。
- 原生 Z-up、.blend 数据、数值槽位和 BOXCLIP 安全规则保持；不引入 Maya 相机或 UV 算法。
- 菜单目录不随对象/组件模式重排；未接入项禁用并说明原因，不把规划写成完成。
- 保留原有 profile schema 1 的读取；菜单配置采用独立版本化配置。
- Recent 最多 10 项，仅本会话内热盒成功且明确可重放的叶命令，不保存文件路径或对象引用。
- 保留可复现 RED/GREEN 证据；测试必须以新版契约更新，不能用旧四向左键测试代替 B1/B2/B3。
- 禁止给用户正在运行的进程注入事件；不覆盖正常安装。不合并、推送或发布。
- 只提交独立实现；不复制/分发 Autodesk 源码、菜单资源或品牌素材。

## 执行环境与文件边界

沿用已有链接工作树 `D:/source/AxisMeld-phase0`，执行时先用 worktree 技能确认状态，不新建第二个源码副本。
当前分支 `axismeld/phase-2a`；在用户确认执行前不改分支。计划本身不授权合并或上传。
保护 `D:/source/AxisMeld-build/install` 和 `phase2a-test-install`；新版安装到 `D:/source/AxisMeld-build/phase2b-test-install`。
使用已有 `D:/source/AxisMeld-build` 构建树，构建前确认 CMake source 指向本工作树。
所有本轮日志放 `D:/source/AxisMeld-build/phase2b-validation-20260909`，每轮 RED/GREEN 用不同文件名。
不得清理之前被工具拒绝删除的目录或执行记录，不能换工具绕过拒绝。

| 单元 | 创建/修改文件 | 责任 |
|---|---|---|
| 目录与配置 | 新建 `scripts/modules/axismeld/hotbox_catalog.py`、`hotbox_profiles.py` | 无 bpy 的目录及层校验 |
| 会话快照/历史 | 新建 `scripts/modules/axismeld/hotbox_runtime.py` | 能力快照、设置变更、重放历史 |
| 现有适配 | 修改 `commands.py`、`adapter.py`、`runtime.py`（同目录） | 七视图、reload、语义提交 |
| 输入核心 | 修改 `source/blender/axismeld/AXM_hotbox_state.hh`；新建 `AXM_hotbox_menu.hh`、`intern/hotbox_menu.cc` | 生命周期和纯布局/命中 |
| JSON 接点 | 新建 `source/blender/editors/space_view3d/view3d_axismeld_hotbox_model.cc` | BLI JSON 转类型快照、严格校验 |
| 原生 UI | 修改 `view3d_axismeld_hotbox.cc`；新建 `view3d_axismeld_hotbox_draw.cc`、`view3d_axismeld_hotbox_release.cc`（同目录） | modal、绘制、退出键保护 |
| 视图 | 修改同目录 `view3d_axismeld_views.cc`、`view3d_axismeld.hh` | 补三方向、内部注册声明 |
| 设置 | 修改 `scripts/startup/bl_operators/axismeld.py` | 菜单参数及内部命令桥 |
| 构建 | 修改两个模块的 `CMakeLists.txt` | 源码与测试目标注册 |
| 测试 | 下列各任务明确的 C++/Python 文件 | 纯行为、安装态与真实 GUI |

任务顺序 1 → 2 → 3 → 4 → 5。每项完成覆盖测试并经审查后再接下一项；不得同时运行多个 GUI suite 或构建。

## 共享接口（任务间不得各自改名）

### Python 与 native 的唯一输入快照

`hotbox_runtime.snapshot(context) -> str` 返回 JSON 字符串，传入原生 operator 的 `menu_json` StringProperty。
JSON schema 为独立版本 1，不是键位 profile schema。使用树形节点而不是任意 Python 表达式：

```json
{"schema_version":1,"generation":1,"settings":{"style":"rows","transparency":25,"rows":["common","pane","modeling"],"center_buttons":{"LEFTMOUSE":"views","MIDDLEMOUSE":"views","RIGHTMOUSE":"views"}},"menus":[{"id":"pane.view","kind":"menu","label":"View","command":"","enabled":true,"reason":"","children":[{"id":"pane.view.frame_all","kind":"command","label":"Frame All","command":"view.frame_all","enabled":true,"reason":"","children":[]}]}]}
```

节点 kind 为 `menu|command|separator|disabled|setting`。command 节点的 command 值必须在只读命令注册表中；节点 id 是独立且唯一的菜单项 ID。
节点还允许 `value` 字符串字段，默认空串；setting 节点以 command 保存设置 ID、value 保存选项值
（如 command=`style`、value=`center`），其他 kind 的 value 必须为空。
setting 节点只允许下面明确列出的设置 ID。用户覆盖不能提供 operator 名称、脚本或 close_before/replayable 策略。
最多 256 节点、8 层、256 KiB JSON；标签上限 128 字符，ID 上限 128 个 ASCII 字符。
重复 ID、悬空菜单映射、循环/超深、非有限数、非法类型/字段全部拒绝。Python 与 native 都校验。
`generation` 单调递增；一次显示周期持有自己的快照，reload 不使该快照悬空。

### 语义调用与返回状态

```python
# hotbox_runtime.py; uses adapter.available/run, never stores context pointers.
def snapshot(context) -> str: ...
def dispatch(context, command: str) -> set[str]: ...
def apply_setting(context, setting: str, value: str) -> None: ...
def reload_settings(context, *, session: dict | None = None) -> None: ...

# hotbox_catalog.py: immutable metadata; independent of bpy.
def default_catalog() -> tuple: ...
def command_policy(command: str) -> tuple[bool, bool]: ... # close_before, replayable

# hotbox_profiles.py: pure validation, errors reject one entire layer.
def resolve_hotbox(layers: list[tuple[str, dict]]) -> tuple[dict, list[str]]: ...

# hotbox_runtime.py: successful-only bounded history; independent class testable without bpy.
class RecentCommands:
    def record(self, command: str, *, finished: bool, replayable: bool) -> None: ...
    def items(self) -> tuple[str, ...]: ...
```

上述 `...` 仅为接口签名，不是实现步骤。任务中给出最小实现及测试；最终代码不得留空函数。
内部 operator `AXISMELD_OT_hotbox_dispatch` 的 RNA 属性为 `command`，直接透传 FINISHED/CANCELLED；
若子工具返回 RUNNING_MODAL，其 handler 属于子工具，内部 wrapper 返回 FINISHED 但不得记为成功历史。
内部 `AXISMELD_OT_hotbox_setting` 属性为 `setting`、`value`。设置 ID 仅有 `style`、`transparency`、
`row.common`、`row.pane`、`row.modeling`；设置后允许一次新快照，不在 motion 中重读。
行设置点击使用 value=`toggle`，按当前有效配置切换；持久化仍保存规范顺序的显式 rows 列表。
中央与 Controls 的样式子菜单复用构造函数，但使用不同节点 ID 前缀，避免全树 ID 重复。

刷新接口为内部 `AXISMELD_OT_hotbox_refresh`（EXEC，无参数）：调用 snapshot(context)，把 JSON
写入 Python 注册的 `WindowManager.axismeld_hotbox_snapshot` StringProperty（HIDDEN、SKIP_SAVE）。
原生使用 `WM_operator_name_call` 同步执行后，立即通过 RNA 读取该字符串并复制为本会话 snapshot。
它是同步返回数据通道，不是共享的活动菜单状态；各窗口仍拥有独立快照。只在主线程同步调用，
失败时不读旧值，关闭当前热盒并报告原因。unregister 删除该 Python 属性，不新增 DNA 字段。

native 的 `bool hotbox_command_closes(std::string_view command)` 位于 AXM_hotbox_menu.hh/intern/hotbox_menu.cc：
`view.toggle_quad`、所有 `selection.*`、`transform.move/rotate/scale` 返回 true，其他本轮已注册的
即时视图命令返回 false，未知命令保守返回 true。Python command_policy 与 native 的逐命令
布尔结果用同一套字面测试表核对；用户目录不能决定此策略。新增公开命令必须补该测试表，
以后扩展接口再独立消除这份有限的语言边界映射，不在首批实现任意插件调度框架。

新建 native 内部头 `view3d_axismeld_hotbox_internal.hh` 共享：

```cpp
namespace blender::axismeld {
enum class MenuKind { Menu, Command, Separator, Disabled, Setting };
struct MenuNode {
  std::string id, label, command, reason, value;
  MenuKind kind;
  bool enabled;
  std::vector<MenuNode> children;
};
struct MenuSnapshot {
  uint64_t generation;
  std::string style;
  int transparency;
  std::vector<std::string> rows;
  std::array<std::string, 3> center_buttons; // LMB, MMB, RMB
  std::vector<MenuNode> menus;
};
bool parse_menu_snapshot(std::string_view json, MenuSnapshot &out, std::string &error);
}
```

纯布局模型使用同一个 MenuNode/MenuSnapshot 定义：把这些纯类型放 `AXM_hotbox_menu.hh`，
内部头只 include 该公共头并声明编辑器函数，禁止复制一份类型。接口中的 std 容器只持有数值/字符串。

JSON 的 null 中央映射在 native parser 内转为空 string；合法菜单 ID 非空，必须覆盖禁用映射的
往返测试。不要把 JSON null 与字面字符串 "null" 混淆。

## Task 1：声明式目录、覆盖校验与快照契约

**Files:** 创建 `hotbox_catalog.py`、`hotbox_profiles.py`、`hotbox_runtime.py`；创建 `tests/python/axismeld_hotbox_catalog_test.py`；修改 `commands.py`。
**Consumes:** 已批准菜单对照表、现有 COMMANDS、共享 JSON schema。
**Produces:** 上述 Python 接口；默认目录、固定策略、三方向无默认键位的元数据。

执行前所有权澄清：本任务实现 catalog/policy、严格校验/层合并及 snapshot 序列化；dispatch、
内存 settings 和其所需 Recent 容器在 Task 3 实现，文件/偏好持久化和历史 UI 在 Task 5 接入。
不为后续函数添加空实现。各项仍沿用共享接口签名。

- [ ] **1. 写首个失败测试：目录顺序、三方向元数据、层回退。** 测试文件在脚本开头把源码 `scripts/modules` 加入 sys.path；不加载 bpy。让 hotbox_runtime 的 bpy import 延迟到需要 context 的函数。

```python
from axismeld.hotbox_catalog import default_catalog
from axismeld.hotbox_profiles import resolve_hotbox
from axismeld.commands import COMMANDS

def test_defaults_and_atomic_layer():
    common = next(row for row in default_catalog() if row['id'] == 'common')
    assert [n['label'] for n in common['children']] == [
        'File', 'Edit', 'Create', 'Select', 'Modify', 'Display', 'Windows']
    assert all(COMMANDS[x].key is None for x in ('view.left', 'view.back', 'view.bottom'))
    good = {'schema_version': 1, 'settings': {'transparency': 50}}
    bad = {'schema_version': 1, 'settings': {'style': 'center', 'transparency': 101}}
    value, errors = resolve_hotbox([('studio', good), ('user', bad)])
    assert value['settings']['transparency'] == 50
    assert value['settings']['style'] == 'rows'
    assert len(errors) == 1
```

- [ ] **2. 运行 RED。** `C:/Python314/python.exe -m unittest discover -s tests/python -p axismeld_hotbox_catalog_test.py -v`；将上述函数包装为 unittest.TestCase 方法，禁止“0 tests OK”。预期缺模块/新命令失败，保存完整输出。
- [ ] **3. 实现最小目录与逐层原子合并。** 默认值：style=`rows`，transparency=25（允许 0/25/50/75/100），三行全开，三鼠标键=`views`。行样式 `rows|zones|center`；中心映射为已存在菜单 ID 或 null。schema 只容许 settings 与中心绑定，首批不开放任意代码/节点注入。

```python
from copy import deepcopy
def apply_validated_layer(base, patch, validate):
    candidate = deepcopy(base)
    for key, value in patch.get('settings', {}).items():
        if key == 'center_buttons':
            candidate['settings'][key].update(value)
        else:
            candidate['settings'][key] = value
    validate(candidate)  # raises ValueError, caller preserves base
    return candidate
```

把该 helper 放 hotbox_profiles；完整 validate 必须执行共享接口列出的限制。文件命名：
`profile_directory()/hotbox_studio.json`、`hotbox_user.json`，顺序默认→studio→user→session；旧 studio.json/user.json 不变。
公开中心 `views` 固定包含七方向及 style 子菜单，映射到普通下拉菜单时按该菜单类型打开而不是强行按方向。

- [ ] **4. 填完本轮实际叶项。** Select 对象/组件及点边面；Modify W/E/R；View 聚焦全部/选择；Shading 线框/实体；Panels 的七视图子菜单和单/四视图；中央与 Controls。其余顶级项 disabled+reason。每个节点具有稳定 ID；具体顺序来自清单，不给未注册 UV 命令建立 enabled 叶项。
- [ ] **5. 添加并跑边界测试。** 断言全部三行完整顺序、菜单 ID 唯一、样式/行显隐、每键 null/重映射、错误类型/超深/循环/未知 ID、旧键位 schema 不变；测试 snapshot 的 JSON 通过 roundtrip，不共享可变字典。
- [ ] **6. 验证并提交。** 同时运行 `tests/python/axismeld_input_test.py`；提交该任务文件，报告实际用例数量及 RED/GREEN，不宣称 native 已接通。

## Task 2：七视图与纯输入/布局核心

**Files:** 修改 `AXM_hotbox_state.hh`、`view3d_axismeld_views.cc`、`view3d_axismeld.hh`、两个模块 `CMakeLists.txt`、`adapter.py`；创建 `AXM_hotbox_menu.hh`、`intern/hotbox_menu.cc`、`tests/hotbox_menu_test.cc`；修改 `tests/hotbox_state_test.cc` 和 GUI 视图断言。
**Consumes:** Task 1 的目录身份；共享 MenuSnapshot 类型。
**Produces:** 七方向 HotboxAction；纯 hit/layout 接口；保留旧调用编译直到 Task 4 替换 modal。

```cpp
namespace blender::axismeld {
struct MenuRect {
  std::string id;
  float x, y, width, height;
  int depth;
  bool interactive = true;
};
struct MenuLayout { std::vector<MenuRect> rects; bool supported; };
MenuLayout layout_menu(const MenuSnapshot &, float width, float height,
                       float center_x, float center_y,
                       const std::vector<std::string> &open_path,
                       const std::unordered_map<std::string, int> &scroll_offsets,
                       const std::unordered_map<std::string, float> &label_widths);
std::string hit_menu(const MenuLayout &, float x, float y);
}
```

label_widths 以节点 ID 映射逻辑像素宽度；原生在打开/缩放重布局时用 BLF 测量并除 UI scale，
MenuRect.interactive 对禁用项和分隔项为 false：保留绘制/提示所需 ID，但 hit_menu 不返回它们。
scroll_offsets 按 root row / menu ID 保存各自偏移；打开或滚动子菜单不得改变祖先标题的位置。
普通标题路径为 `{titleId,...}`；中央改绑菜单用 `{"center",mappedMenuId,...}` 明确中央锚点。
首项 center 是内部锚点前缀，不算树层级；真实路径从第二项开始，映射 center root 时为
`{"center","center"}`。首层仅显示目标菜单 children，滚动 owner 仍为真实 menu ID。
Task 2 测试 center 样式下普通菜单映射及中央/标题不同锚点；Task 4 使用该路径，不另写布局。
布局只做保持 open_path 当前父项可见的最小归一化；Task 4 滚动祖先时先收起其更深路径。
这是未发布内部接口的直接替换，不保留单 int 兼容 wrapper；测试父级锚点和子级滚动相互独立。
单个实测标签无法完整放入可用宽度时 supported=false；默认目录在支持尺寸仍须完整可达。
布局滚动控件使用保留 ID `@scroll:<owner>:previous` / `@scroll:<owner>:next`，只导航，不派发命令。
普通目录节点不得以 `@scroll:` 开头；Python（Task 2 补充）与 native（Task 4）边界都校验并测试。
纯测试使用固定字面宽度。非空目录缺失宽度或出现非有限/负宽度时返回 supported=false，不能
用另一套猜测字宽造成绘制与命中不一致。该纯头显式 include array/cstdint/string/string_view/vector/unordered_map。

- [ ] **1. 写七方向 RED。** 保持旧 enum 数值，追加 Left/Back/Bottom，不挤占现有 RNA action 值。

```cpp
TEST(axismeld_hotbox, SevenDirections)
{
  EXPECT_EQ(hotbox_direction(-40, 40, 12), HotboxAction::Left);
  EXPECT_EQ(hotbox_direction(-40, -40, 12), HotboxAction::Back);
  EXPECT_EQ(hotbox_direction(40, -40, 12), HotboxAction::Bottom);
  EXPECT_EQ(hotbox_direction(40, 40, 12), HotboxAction::None);
  EXPECT_EQ(hotbox_direction(0, 12, 12), HotboxAction::None);
}
```

- [ ] **2. 跑该 GTest 目标确认 RED，然后实现八扇区。** `atan2` 将角度转换为以 E=0 的最近八方向，NE 留空；与边界差小于浮点容差（1e-6 radians）时 None，死区距离先判定。非有限输入仍 None。保留 N/E/S/W 原义。
- [ ] **3. 接入三视图最小映射并测几何。** RNA action 新增 LEFT/BACK/BOTTOM；adapter.VIEW_ACTIONS 同名；复用 next.axis(RV3D_VIEW_LEFT/BACK/BOTTOM)，不改 cache/clip 算法。

```cpp
const int axis = action == HotboxAction::Left ? RV3D_VIEW_LEFT :
                 action == HotboxAction::Back ? RV3D_VIEW_BACK : RV3D_VIEW_BOTTOM;
// Only enter this branch for the three newly added enum values.
next.axis(axis);
```

GUI 数值预期用 Blender 标准方向的独立字面四元数或原生 axis operator 的独立参考区域；不能调用待测函数生成自己的 expected。加上下/前后贡献缺失和恢复的 native zoom/pan 回归。
- [ ] **4. 写布局边界 RED，再实现。** 逻辑坐标；中心按钮围绕原始指针，其他行可独立内移，文字按测量宽度布置。主行放不下时保留原始顺序的滚动条/溢出入口；子菜单向内翻转，溢出叶项可滚动到达。深菜单优先命中，separator/disabled 不返回可执行 ID。

```cpp
TEST(axismeld_hotbox, SmallViewportRefusesMenus)
{
  MenuSnapshot snapshot{};
  EXPECT_FALSE(layout_menu(snapshot, 479, 320, 100, 100, {}, 0, {}).supported);
  EXPECT_FALSE(layout_menu(snapshot, 480, 319, 100, 100, {}, 0, {}).supported);
}
```

补充带实际默认树的 480×320、1920×1080，真实四角+中心测试；所有可操作行/叶项需存在可达路径，绘制/命中使用同一 MenuRect。不得把“屏外但算得到方向”视作可读菜单通过。
中央按钮边角处可向视口内扩展容纳文字，包含原始指针及原有可见命中部分；实际 Space/鼠标
捕获原点不变，不从新矩形中心反推方向。不得以安全内边距替代角点，也不把 12px 死区当按钮尺寸。
只有空间不足时中央 AxisMeld 按钮可与主行组分离；其余行连续保持 common/pane/(Recent,Controls)/modeling
纵序并避让该按钮，不重复中央入口。测试真实四角组序、矩形不重叠和原点命中；正常内区仍为完整中央三入口同行。
- [ ] **5. 运行/提交。** 原生测试与旧 13-case 行为兼容测试（替换旧对角预期）；新增 menu target 注册后先 `ctest -N -R axismeld` 确认目标名，再定向执行。构建 Blender 并安装独立 2B 目录，跑视图数值 GUI；不覆盖 2A stage。

## Task 3：提交桥和残留按键保护（先证明事件路由）

**Files:** 创建 `view3d_axismeld_hotbox_release.cc`、`view3d_axismeld_hotbox_internal.hh`；修改 `view3d_axismeld.hh`、`space_view3d.cc`、模块 CMake、`scripts/startup/bl_operators/axismeld.py`、`hotbox_runtime.py`；创建 `tests/python/axismeld_hotbox_release_events.py`。
**Consumes:** Task 1 dispatch/策略定义、Task 2 内部类型。
**Produces:** 内部语义 dispatch operator 和 `VIEW3D_OT_axismeld_hotbox_release_guard`；后者只有捕获键释放/重复与失焦处理，不绘制 UI。

本任务提前增加 runner 的固定 --suite 路由以执行 release 夹具，默认 hotbox 保持不变；
Task 4/5 在对应脚本存在后扩展枚举。将 Task 5 的 Recent 最小容器及纯行为测试一起前置到
本任务，使 dispatch 成功记录有实际消费者；Task 5 负责其产品显示、容量/重放与持久设置验证。

本任务也实现共享接口中的 AXISMELD_OT_hotbox_refresh、WindowManager 隐藏 JSON 属性及注册/注销，
以便 Task 4 不需要直接运行 Python 源码字符串来刷新菜单。

策略表：七视图方向、聚焦、显示为 `(false, true)`；单/四视图、选择模式、W/E/R 为 `(true, true)`；设置和 hotbox.open 不进入 Recent。未来交互/文件工具为 close_before=true 且 replayable=false，首批不启用对应目录。

- [ ] **1. 写真实释放 RED 探针。** 复用现有 runner 的私有配置/临时目录契约，注册仅测试进程的 modal probe，记录收到的 event.type/value。在模拟 Space/RMB 已按下后触发 probe，然后释放 RMB/Space；先证明无 guard 时 probe 收到这些 RELEASE。

```python
events = []
class AXISMELD_OT_release_probe(bpy.types.Operator):
    bl_idname = 'axismeld.release_probe'
    bl_label = 'Private release probe'
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def modal(self, context, event):
        events.append((event.type, event.value))
        return {'FINISHED'} if event.type == 'ESC' else {'RUNNING_MODAL'}
```

- [ ] **2. 实现专用 guard。** 参数：`trigger_type`（实际键）、`mouse_type`（实际鼠标键或 NONE）、`trigger_down`、`mouse_down`。只消费捕获键的 RELEASE/自动重复；有等待状态时其他事件仅返回 `OPERATOR_PASS_THROUGH`；全部释放 FINISHED；失焦取消；再次收到捕获键的新非重复 PRESS 表示旧 RELEASE 已丢失，清除此键的等待并放行新按下。不得长期吞新按键。
本版 WM 对精确 `RUNNING_MODAL | PASS_THROUGH` 返回组合会停止后续 modal 分发，故不能用于此 guard。
单独 PASS_THROUGH 保留已有 handler 并继续分发；终结分支仍按 FINISHED/CANCELLED 清理，实测最后
一个待释放键被新 PRESS 替代时同样到达子工具。此修正不改全局 WM。

```cpp
if (event->type == data.trigger && event->val == KM_RELEASE) {
  data.trigger_down = false;
  return data.mouse_down ? OPERATOR_RUNNING_MODAL : OPERATOR_FINISHED;
}
return OPERATOR_PASS_THROUGH;
```

guard 的默认状态只包括本热盒已经捕获的 DOWN；不猜整个键盘状态。无待释放键时不创建 handler。
命令导致原区域销毁时 guard 只依赖仍存活的窗口，不解引用旧 region。来源窗口失效由 WM 生命周期清理。

- [ ] **3. 按源码证据确定调用次序并测同窗口门禁。** `WM_event_add_modal_handler_ex` 走窗口 modal handler 插入逻辑；先去掉热盒 draw/timer、调用子命令，再添加 guard，使 guard 先看到残留释放。用实际普通及优先 modal probe 证明顺序，不仅检查列表名字。禁止修改 wm_event_system.cc；不以延迟执行到 Space 松开偷换命令时序。补测预设切换及同窗口 popup 正常后续输入；不扩大为跨窗口机制。
- [ ] **4. 保留无写入新窗口诊断。** 原 `fileselect_add` 真实新窗口接收探针保留为固定 `--suite release-cross-window` 独立诊断，仍以收到残留 RELEASE 判失败，不能改成假绿色。正常 `--suite release` 仅覆盖本轮同窗口及生命周期门禁，输出明确范围。execute/cancel 不写文件，Esc 清理测试窗口。产品目录和 dispatch 允许列表均不得启用新开窗口命令。
- [ ] **5. 同步与失败路径。** dispatch 重新 adapter.available；CANCELLED/异常不写 Recent；FINISHED 才 record。上下文变化类命令执行前关闭热盒；普通方向动作保留主热盒。guard 不要求 active preset 保持原值；否则用户切预设会导致释放穿透。
- [ ] **6. 运行并提交。** 保存无 guard RED、同窗口 guard GREEN、同步成功/失败和单列的跨窗口已知失败诊断；确认正常安装哈希未变。同窗口门禁失败不得进入 Task 4；跨窗口明确延期，不掩盖或宣称全门禁通过。

## Task 4：原生主菜单、中央七向与完整生命周期

**Files:** 创建 `view3d_axismeld_hotbox_model.cc`、`view3d_axismeld_hotbox_draw.cc`；修改原 hotbox.cc、内部头、模块 CMake、adapter.py；修改 `tests/python/axismeld_hotbox_events.py`；创建 `tests/python/axismeld_hotbox_menu_events.py`。
**Consumes:** Task 1 snapshot/目录，Task 2 layout/direction，Task 3 dispatch/guard。
**Produces:** 实际预设键位下运行的主菜单 UI；不再以测试临时键表作为完成证据。

- [ ] **1. 用实际产品入口取得 RED。** 旧 build 按 Space 截图并断言未出现主目录；Space+RMB NW 后数值不是 Left；保存截图和断言。使用 `window.event_simulate` 与现有 generator/timer harness；不操作用户进程。
- [ ] **2. 接入快照解析与错误测试。** `adapter.run(hotbox.open)` 传 `menu_json=hotbox_runtime.snapshot(context)`；原生 RNA StringProperty 接收，调用 BLI `JsonFormatter.deserialize(std::istream&)`，失败在安装 draw/timer 前返回 CANCELLED。解析树限定类型/容量，临时结果全部成功后才赋值 out。

```cpp
std::istringstream stream{std::string(json)};
blender::io::serialize::JsonFormatter formatter;
auto root = formatter.deserialize(stream);
if (!root) {
  error = "Invalid hotbox JSON";
  return false;
}
```

解析代码只放编辑器 model 文件；GTest 为 parser 加 malformed/超限测试，链接 bf_blenlib 的现有模块依赖，不引入第三方 JSON 库。
- [ ] **3. 替换原固定四向 draw 和 LMB 判断。** HotboxData 新增 snapshot、open_path、scroll_offsets、active_mouse、pending_leaf、menu_layout；绘制只消费布局矩形和候选，不调用 adapter。
状态为主热盒、下拉浏览、中央划选、关闭后 guard，短按资格单独单向清除。中心映射 null 只取消短按，不执行；普通菜单映射进入下拉而不是 marking。

```cpp
// On a mouse press when there is no active gesture:
data.tap_eligible = false;
data.active_mouse = event->type;
const std::string item = axismeld::hit_menu(data.menu_layout, x, y);
// Route the ID by node kind; a disabled/separator node cannot dispatch.
```

- [ ] **4. 实现点击和拖选两条路径。** 菜单标题按下展开；松开在标题/父项保持菜单；按住拖到叶项松开执行；点击浏览后需新按下+释放才能执行。子菜单 hover 打开，退回父菜单不丢失路径；切另一标题替换 open_path。另一个鼠标键不得提交当前候选。
- [ ] **5. 中央/边缘绘制与命中。** 主目录可见时不显示方向标签；中央鼠标按下才画七视图。按 Task 2 的中央边角扩展规则保留实际捕获原点，行与列表独立向内排布。按照 layout_menu 提供的所有可达菜单矩形画文字、禁用/候选与滚动提示，标签测量与点击矩形同一 UI scale。
滚动仅改变相应 owner 的 scroll_offsets；滚动祖先前收起其更深路径。保留子级滚动时父级标题位置；@scroll: 控件只导航、不交给语义派发器。原生解析器拒绝同前缀普通节点 ID。
- [ ] **6. 命令提交与重建。** C++ 用 `WM_operator_name_call` 调用 `AXISMELD_OT_hotbox_dispatch`，不执行任意字符串。close_before 策略由共享接口的 hotbox_command_closes 确定，不能由用户 JSON 指定；刷新快照仅在即时命令成功、设置改变或新 invoke 时发生。即时命令后通过 AXISMELD_OT_hotbox_refresh 和隐藏 RNA 返回通道刷新快照；设置通过 AXISMELD_OT_hotbox_setting 修改并刷新。区域改变后禁止回调原 draw。Space 先松取消未完成鼠标动作并启用只等待鼠标 RELEASE 的 guard。
- [ ] **7. 更新完整 GUI 回归并提交。** 覆盖 B1–B4/B6–B9；旧视图/BOXCLIP/生命周期用例保留。断言主目录截图、RMB 七向数值、click/drag 的调用次数、模式改变无 stale pointers、禁用项/NE 不执行、失焦后重新使用。不能只把旧 LMB 测试整体替换成 RMB 而丢掉其余基线。

## Task 5：设置/历史产品接入、完整验证与手测交付

**Files:** 修改 hotbox_runtime.py、runtime.py、bl_operators/axismeld.py、axismeld_input_blender.py、axismeld_hotbox_ui_runner.py；创建 `tests/python/axismeld_hotbox_profiles_blender.py`、`docs/compatibility/phase-2b-report.md`、`docs/compatibility/phase-2b-manual-test.md`；更新菜单清单及 README 的实际能力说明。
**Consumes:** 前四项全部接口及实际 UI。
**Produces:** 可重载/保存的个人设置、Recent、独立测试安装与可追溯报告。

- [ ] **1. 写设置和历史 RED。** `resolve_hotbox` 无 bpy 测试与安装态偏好测试分别执行；历史不依赖 current scene。下面测试加入 Task 1 的 unittest.TestCase 并带 self 参数，确保 discover 实际收集。

```python
from axismeld.hotbox_runtime import RecentCommands
def test_recent_success_only():
    history = RecentCommands()
    history.record('view.front', finished=False, replayable=True)
    history.record('view.top', finished=True, replayable=False)
    assert history.items() == ()
    history.record('view.front', finished=True, replayable=True)
    history.record('view.top', finished=True, replayable=True)
    history.record('view.front', finished=True, replayable=True)
    assert history.items() == ('view.front', 'view.top')
```

- [ ] **2. 实现 Recent 最小容器及上限。** 新增编号不同的 11 个已允许命令断言只保留最后 10 个；不得通过测试注册任意脚本作为正式命令。

```python
def record(self, command, *, finished, replayable):
    if not (finished and replayable):
        return
    self._items = [command] + [x for x in self._items if x != command]
    del self._items[10:]
```

每次 Recent 点击先重新 available，失败保持旧历史，不重新执行旧上下文。已启动但未完成的 modal 不算 FINISHED；首批不用监听全局命令历史。
- [ ] **3. 接入参数显示和持久化。** 样式/透明度/行显隐/中心三键设置在预设偏好和 Hotbox Controls 使用同一模型。Controls 更改是用户覆盖，写入 `hotbox_user.json` 时只保存差异，临时文件校验后 replace；已有文件读失败不得覆盖。`use_file_overrides=false` 忽略文件层，Controls 改动仅保存会话覆盖并在 UI 说明。公共目录不可变。reload_settings 在 runtime.load 和显式菜单重载调用；不在 slider motion 中重新生成全键表。
- [ ] **4. 安装态/GUI 测试。** 私有配置中写入有效/无效 studio、user、session；证明层原子回退、旧 schema 1、个人按键与菜单配置互不破坏。菜单活动时重载后当前快照仍安全；下次 invoke 使用新 generation。测试样式 rows/zones/center、中心键 null/映射另一已注册菜单；zones 的未接入周边不可执行，center 样式把整片非菜单区域解释为中央。
- [ ] **5. 完整本地验证。** 以下是执行时命令；本计划没有运行结果。CMake 程序使用本机 VS 附带路径，禁止误用配置好的 whole CTest 旧 install。

```powershell
$cmakeTool = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ctestTool = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'
& $cmakeTool --build D:/source/AxisMeld-build --config Release --target blender --parallel 8
& $cmakeTool --install D:/source/AxisMeld-build --config Release --prefix D:/source/AxisMeld-build/phase2b-test-install
& $ctestTool -N -C Release --test-dir D:/source/AxisMeld-build -R axismeld
```

先列出新增 GTest 对应 build target 再构建它们，不能对未构建的旧测试二进制取绿灯。
定向执行所有 AxisMeld 纯 native targets，Python pure/input、CLI identity、portable paths，安装态输入/菜单配置、release probe、完整热盒及操纵器 GUI。
所有依赖 Blender 的 Python 测试显式传 `D:/source/AxisMeld-build/phase2b-test-install/blender.exe`。
安装态后台测试必须在私有 TEMP/TMP/TMPDIR/BLENDER_USER_CONFIG 中运行并验证 bpy.app.tempdir；复用现有 runner，不直接用用户临时路径。

```powershell
& 'C:\Python314\python.exe' tests/python/axismeld_input_test.py
& 'C:\Python314\python.exe' -m unittest discover -s tests/python -p axismeld_hotbox_catalog_test.py -v
& 'C:\Python314\python.exe' tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-test-install/blender.exe
& 'C:\Python314\python.exe' tests/python/axismeld_manipulator_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-test-install/blender.exe
& 'C:\Python314\python.exe' tests/python/axismeld_navigation_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-test-install/blender.exe
```

扩展原 runner 支持 `--suite`，只接受固定枚举 `hotbox|menus|release|release-cross-window|profiles`（新增导航修复可有独立固定入口），映射到明确测试文件，不接受任意用户脚本路径。默认 hotbox 保留向后兼容。release-cross-window 是延期缺陷的独立诊断，不混入本轮成功汇总。
布局纯测试覆盖全部规定缩放；GUI 至少覆盖 1.0/2.0 与四角，保存并实际查看截图。低于尺寸下限的 short/hold 分开断言。
- [ ] **6. 文档和 handoff。** 报告记录源码/上游提交、真实命令、用例数、exe 哈希、已知警告、人工待验收和未接入目录。菜单表只按实际结果更新。人工表至少包括 Space 主目录、RMB 七向、点击式/划选式子菜单、边缘、快速手势、残留释放、三键覆盖、四视图和 W/E/R 回归。加入本次导航修复：右/下拉近、左/上拉远，双轴及透视/正交/四视图；明确指数灵敏度为 AxisMeld 适配而非 Maya 数值一致。清楚区分旧 phase2a-test-install 和新 phase2b-test-install，只提供已核对身份的新 exe。不得把独立跨窗口诊断的失败计入通过项。
- [ ] **7. 审查后提交交付。** 每项审查加最终整体审查；重大问题按开发技能门禁修复，不靠后续批次掩盖。保留分支和独立 stage，提供 exe 与人工表链接，不自动启动用户 GUI、不合并/推送。只有 B12 人工通过后才写体验验收通过。

## 计划自审覆盖矩阵

| 规格要求 | 承接任务 |
|---|---|
| B1 第一层/中央按键 | 1 默认数据、4 实际 UI、5 三键配置 |
| B2 时序/释放/取消 | 3 guard、4 modal、5 GUI 回归 |
| B3 七方向/边界 | 2 数学与视图、4 菜单优先命中 |
| B4 目录/子菜单 | 1 目录、2 布局、4 click/drag |
| B5 配置/隔离 | 1 原子层校验、5 安装态 |
| B6 生命周期 | 3 退出、4 上下文、5 文件/预设回归 |
| B7 缓存/裁剪 | 2 七方向回归、4/5 保留既有完整 GUI |
| B8 同窗口转交/新窗口禁用 | 3 同窗口门禁及独立跨窗口已知失败诊断、4 提交桥允许列表 |
| B9 UI scale/小视口 | 2 布局、4 绘制、5 截图 |
| B10 Recent | 1 策略、3 成功回报、5 历史 |
| B11 既有命令 | 2 adapter、5 全部相关回归 |
| B12 Maya 手感 | 5 人工交付；代码测试不能替代 |
| UV 边界/后续目录 | 1 禁用规划条目、5 说明；不在本轮实现算法 |

## 开始执行前检查点

- [ ] 用户选择任务逐项执行方式后，读取对应执行技能；不因计划含推荐项就提前派发代理。
- [ ] 核实工作树、未提交内容、构建 source、原安装/2A stage 哈希及当前用户进程，保留原件。
- [ ] 新基线回归先通过；若失败先区分既有问题与计划改动，不覆盖证据。
- [ ] 执行中发现新的全局事件修改需求或超出规格的交互取舍，先回到设计说明，不自扩范围。

本计划已完成静态范围和接口一致性检查；代码片段是待实现的测试/算法约束，未编译或运行，不构成成功证据。
