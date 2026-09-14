# Maya实际菜单层级与完整展开验收

更新：2026-09-15。以本机隔离Maya 2026实际树重建22个主菜单，纠正能力注册表被直接用作展示树的问题。Display由错误的56项平铺恢复为16个主条目，Polygons、NURBS、Animation、Rendering等回到各自子层。当前层完整显示；不使用折叠、滚动、分页箭头或人工Back页。真实子菜单保留原层级。

## 来源与内容

- 22个主菜单：Common 7、Current Pane 6、Modeling 9。原始2007槽位按明确动态清单归一化为1949节点，包含369个附属Options。Options计数不是额外可执行功能数。
- Maya的dividerLabel按非交互标题显示，不转换成菜单分组；正文与带字标题24逻辑像素，普通分隔6像素。Undo/Redo/Repeat的会话历史名称不固化到菜单。
- 全部现有热盒的静态内容复核见 `../development/2026-09-14-maya-marking-hierarchy-audit.md`。Snap的Relative Mode移至真实下方列表；Mapping两标签修正；Style三个项不显示Maya不存在的单选圆圈，Transparency保留真实radio。
- 已有564个注册命令ID和核心选择、创建、视图入口保留。剩余Blender能力放入独立Blender Extensions，并沿原生功能分组；Marking Menus内部根独立可达，不混入Maya Modify/Select/Controls。通过键位偏好的中心鼠标按钮映射访问这些扩展。
- 精确语义审查禁用16个错误或歧义RTC绑定，保留原Maya条目与原因，原Blender能力仍在扩展目录。其中6个唯一候选同样不等价：选择约束、两种改名、成员编辑工具、从曲面复制曲线、通用相似选择。

## 布局与输入

组合菜单在下方空间不足、源pane仍可容纳完整UI时整体上移并对齐安全底边，伴随列表仍位于环下。小pane不足时使用同一窗口可见区域；真实当前层仍过高才按原顺序分列。标题不会孤悬列尾，图标、状态列、正文与参数格不相互覆盖。整窗也无法容纳固定尺寸布局时安全拒绝，不隐藏不可见条目。

显示可以跨pane，动作仍归捕获的源上下文。环、列表、参数格、子菜单和命中同步平移；实际按下点保留取消语义。滚轮不分页且不传递到视口缩放；窗口、区域或缩放变化安全取消。四视图Views仍为五行热盒内缘与取消区域标杆。

## 最终候选与验证

- 独立安装：`D:\source\AxisMeld-build\maya-hierarchy-test-install\blender.exe`。
- 程序SHA-256：`7BE40DAFC8735F6B8485F49A49ABC509395B47772CE4D8D0D0E93CA50AA695CF`。
- 30份脚本资源指纹：`B1370714D2945389D535ADFE6EF415CC19FF6A4A41BCE074007CE0618954B324`，逐文件与源码一致；4份配置完整复制，228份前批保护文件哈希不变。
- 当前快照3180节点、20根、深度7、642519 UTF-8字节；严格限制4096节点、1MiB，未知或不完整根结构、越界与状态伪造仍原子拒绝。
- Python：22文件179项通过；原生：6组127项通过，其中布局81、解析23。
- GUI：19套均在上述程序和资源指纹通过。包括22主菜单及Display→Polygons真实像素顺序、创建/选择与单次Undo、原生样式、完整菜单、生命周期、原位释放、全部现有热盒、图标及菜单状态回归。证据索引为 `D:/source/AxisMeld-build/maya-hierarchy-install-verification.json`。

旧56行目录只保留为显式合成布局压力数据，不再作为产品Display或Maya内容证据。观察器误匹配顶栏Object Mode的问题已定位到具体像素坐标；采用实际完整按钮组定位后，各热盒逐项对照同次实测Views内缘，原容差保留，不以固定旧截图数值替代实际测量。

## 明确边界与人工测试

静态菜单内容对齐不等于所有Maya算法已实现。未适配正文/参数仍灰显；动态DG、材质、UV/颜色集、历史节点、Scene Assembly及插件分支按记录的条件保留边界。Show→Isolate Select→Bookmarks的Maya原生回调在隔离场景仍出错，只确认固定Bookmark Current Objects入口和Options，未伪造动态子项。View→Bookmarks相机分支已另行核对，二者不混算。

人工目录共253项：历史已测试47项、目录初始待测206项，本轮新增MT-01～MT-32；FM-01～FM-10布局项一并待测。自动回归不代替人工手感与个人场景结果。私人测试网页第8版已更新目录且保留个人记录：https://axismeld-test-ledger.zwb285638030.chatgpt.site。
