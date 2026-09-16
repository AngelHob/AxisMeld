# Rigging 工作区：人工验收设计

日期：2026-09-17。依据 [Rigging 工作区设计](2026-09-17-rigging-workspace.md) 编写。以下验收项已同步到统一清单与公开目录，全部待人工测试；目录收录不表示人工测试已通过。

已发布 [`axismeld-2026.09.17-rigging-preview`](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.17-rigging-preview)，对应源码 `617986ac1841`。使用该包验收新增工作区；公开下载和反馈版本已同步，旧 Rigify 预览版不包含本轮工作区。

## 清单与结果保留

本轮追加 RG-07 至 RG-14，共 8 项。统一清单和公开目录保留此前 300 项的编号、步骤、预期和 47 条已测试状态，不修改访客本地记录。现共 308 项：47 项历史已测试、261 项初始未测；12 项已替代历史方案继续保留，当前验收清单为 296 项。

RG-01 至 RG-06 继续作为内置 Rigify 的回归项目，本次只取消其“最近新增”标记，不修改状态。全部新增项目初始为待测；自动注册、脚本与GUI检查不能代替人工结果。

## RG-07 至 RG-14 人工验收

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| RG-07 | 使用本轮Rigging预览构建的隔离工厂配置启动，查看Layout、Modeling、Rigging；在三者之间往返，并分别使用Blender和Maya键位检查Rigging视窗 | 默认仍进入Layout，原有工作区保留；Rigging具有参考Modeling的3D视窗、Outliner和Properties布局，两种键位均有Skeleton/Skin；切工作区不隐式绑定、切Weight Paint、改选择、姿态或权重，原生全局栏与其他工作区正常 | 待测 |
| RG-08 | 在临时配置用顶部+→General→Rigging添加工作区；再打开一个不含Rigging的旧测试blend，分别检查Load UI开启与关闭的行为 | 原生+入口添加同一默认Rigging布局；旧文件按原生Load UI选项载入或保留布局，不被自动注入页面，不改写旧用户startup或删除其他工作区；仍可通过原生+入口自行添加 | 待测 |
| RG-09 | 对照Maya参考逐层查看Skeleton的Joints/IK/Joint Labelling和Skin的Bind/Weight Maps/Normalize Weights/Edit Influences；在常用缩放及较矮窗口检查末项、灰正文与独立Options | 原始名称、章节、顺序、子层和Options保留，缺失算法仍灰占位；统一左侧Blender图标及右对齐参数齿轮；固定目录完整展示，下方不足时底部对齐，不新增折叠或滚动；灰正文及灰齿轮不执行场景操作 | 待测 |
| RG-10 | 在Rigging的Skeleton原生入口添加Single Bone并执行一次骨骼Extrude，再Undo；另建Rigify metarig并从原有Rigify面板生成控制骨架 | 真实Blender骨骼创建与编辑可用，取消及一次Undo符合原生行为，不重复执行；Rigify无需安装或启用，实际生成控制骨架，原生骨骼命名、集合、IK和Pose子目录仍可找到 | 待测 |
| RG-11 | 临时网格与骨架按Blender要求选择，以骨架为活动对象从Skin原生Armature Deform入口用Automatic Weights绑定，移动骨骼观察变形并在副本中撤销；另用可编辑的本地Object引用链接只读Armature数据，以它为活动目标用Empty Groups绑定本地网格；再检查空选择、只有网格、只有骨架及错误活动对象 | 自动权重产生真实父子关系、Armature修改器和相应权重，姿态影响网格，Undo恢复上一步；链接只读Armature数据仍可作为本地对象的绑定目标，Empty Groups创建父关系、修改器和对应空组；无效上下文禁用或给出原生提示，不偷换活动对象、扩选、跨窗口找目标或切模式，不把原生绑定标成已实现Maya Bind Skin | 待测 |
| RG-12 | 在已绑定的临时网格明确进入Weight Paint，从Skin的原生权重目录执行Normalize或Clean，比较顶点组/权重并Undo；切回Object、Edit Mesh以及无对象上下文查看目录 | 权重操作作用于当前网格和正确顶点组，参数与原生Blender一致，撤销恢复可观察的权重变化；对应Weights入口只收纳一份，模式不匹配时安全灰显，不因打开菜单修改权重或自动改变选择 | 待测 |
| RG-13 | Pose下从Skeleton原生Pose目录执行Clear Transform或Copy/Paste并撤销；再用本地Object引用链接只读Armature数据，检查Pose与IK目录并执行可用的姿态清除、添加或清除IK；使用已安装兼容扩展对照原生Armature/Pose/Weights及Add Armature菜单，再检查Pose Asset入口 | 本地对象的Pose与IK不因Armature数据只读而整组误禁用，操作遵循各原生poll并产生可观察结果；姿态、资产、原生复杂子目录及参数保留；原生宿主插件条目显示且不重复，移除后消失，不将插件回调整包复制到平行菜单，缺少第三方样本时注明仍待测 | 待测 |
| RG-14 | 在临时文件中将Rigging重命名并复制，分别检查Skeleton/Skin；保存、退出并以新进程重开；在Object、Edit Armature、Pose、Weight Paint及非骨架编辑模式间切换；分别删除含用途标记的活动与非活动工作区副本 | 改名、复制和保存重开后用途保持，Skeleton/Skin仍各一份；Armature/Pose/Weights在对应领域目录中保留，非骨架模式原菜单仍可用，不串入Modeling；无对象或从Window→Maya Menu Sets访问时不报错，也不使用另一窗口的编辑对象；删除副本后剩余工作区及其布局保留且可切换，无用户计数递减错误或崩溃 | 待测 |

## 人工边界与准备

使用测试副本和简单可还原的网格/骨架，不直接修改生产角色。绑定质量需要观察真实变形，不能只凭出现修改器或报告成功就认定符合预期；本轮没有实现缺席的Maya专有蒙皮算法。复杂生产拓扑、多骨架权重与第三方Feature Set仍须按实际场景补充备注。

原生绑定有活动对象与选择要求。人工验证无效上下文时，不能先手动修正后把原无效状态记为通过。Weight Paint的模式切换须是明确点击操作，不能由进入工作区或打开菜单隐式触发。

插件条目检查优先使用已安装且兼容的样本。没有第三方样本时记录缺口，不因自动测试探针通过而声称所有插件兼容；动态资产或插件造成超长目录的情况另附窗口高度、缩放和截图。固定目录通过不代表动态内容的所有高度已验证。

工作区保存与Load UI测试只使用自建临时文件，按Blender原生文件信任机制处理生成脚本，不全局降低脚本安全设置。旧文件未自动新增Rigging是本轮明确的兼容行为，原生+添加入口仍应可用。

## 静态审查基线

从现有Maya来源独立计数：Skeleton为54条正文、8个Options；Skin为28条正文、25个Options，总计82条正文与33个Options。原始Skeleton/Skin根分别23/28行；最长已有子层Add Joint Labels为35行。新原生内容应按用途进入已有章节或合理子目录，不能把内部复杂菜单整体摊成更长根层。

静态检查要核对原ID恰好出现一次、完整payload、原父子层级与顺序、独立Options，以及未适配条目没有新增执行绑定。真实Menu宿主回调、按模式可用性、底部对齐和实际绑定/权重/姿态结果则由独立候选GUI及以上人工项验证，不能用目录数量代替。
