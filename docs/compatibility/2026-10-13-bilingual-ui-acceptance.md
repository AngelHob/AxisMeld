# 中英文界面本批验收记录

日期：2026-10-13。目标标签：`axismeld-2026.10.12-bilingual-ui-preview`。**本地必要门禁通过，公开交付仍待收齐。** 本页记录实际范围，不代表完整 Maya 能力、全部原生/第三方界面或人工手感已验收；当前公开旧包不含本批双语修改。

## 实现边界

- 仅英文 `en_US`（ID 1）和简体中文 `zh_HANS`（ID 13），默认英文；沿用原生简中 MO 和专属补词，覆盖固定热盒/伴随列表、Modeling/Rigging、Options、灰项说明、偏好、内置 Rigify 及已审计的原生按钮。专名/数字/格式/快捷键保持项显式记录。
- 原生热盒普通与 Views 紧凑文字、Python 菜单及说明的测量/绘制使用对应上下文的同一实际译文；保留独立界面/工具提示翻译开关及注册/注销/重载生命周期。
- 工作区实际名称、对象/骨骼/材质等用户数据和路径不改写；内置工作区只翻译显示标签，旧“建模”识别保留。默认 Blender 键位、Layout、命令 ID/绑定、菜单层级、灰能力和 Options 默认参数保持。
- 伴随列表仍为 18 逻辑像素；100%/150% 为 18/27px。Views 间隔、方向按钮、不折叠/不滚动、底部对齐和说明无完整空白时隐藏的规则保持。新算法继续暂停。
- 只安装简中 MO 与两项语言清单，完整字体栈保留。旧 Automatic、法语、繁中回退英文；旧简中、英文保留。设计见[双语界面](../development/2026-10-12-bilingual-ui.md)。

## 当前身份与实际证据

运行 EXE SHA256：`e85cc631490981c0a4893ffd6fe60b4bc70c2534108c21c181219c86772a74a4`。本批基于既有 Blender 5.4 Alpha 固定上游，没有再次合并主干。最终发布源码 SHA 和完整包指纹由最终发布快照绑定；本页不将构建时尚未提交的工作树误写为旧源码已包含双语修改。

下列名称是本批审计回执入口，不要求新机器复制维护者审计目录。新机器应从仓库及已发布快照重建各自证据；旧失败记录保留，成功记录不覆盖失败。

| 检查 | 实际结果 | 回执入口与边界 |
|---|---|---|
| 原生构建 | PASS | `build-attempt-03/build-receipt.json`；前序失败保留 |
| 全新候选安装 | PASS，6,529 个安装文件 | `install/receipt.json`；两项语言、仅简中资源及字体栈核对，运行缓存与安装清单分别记账 |
| 候选资源审计/工厂启动 | PASS，153 项选定资源 | `candidate-audit.json`、`candidate-factory/run.json`；静态资源和实际启动分别核验 |
| 原生针对性回归 | PASS，2 组 114 项 | `native/receipt.json`；不冒称全部 Blender 测试 |
| Python 针对性回归 | PASS，7 组 90 项 | `python-final/receipt.json`；词库最终补词与门禁已复核 |
| 固定词库真实运行时 | PASS，3,737 个源词 | `translation-runtime-01/observed.json`；含英文往返、界面/工具提示开关、数据名保护和注册重载 |
| 原生按钮/上下文 | PASS，129/129，英文往返通过 | `final-native-candidate-01/observed.json`；使用已安装模块，未插入源码路径 |
| 旧偏好与中文持久化 | PASS，5 种旧种子、7 次新进程 | `language-migration/baseline-05/summary.json`、`verify-04/summary.json`；配置隔离、实际保存/重启，前后源码/EXE/资源哈希稳定 |
| 既有交互与最终双语 GUI | PASS，三套既有回归及 52 条双语记录 | `gui-final/receipt.json`；真实 Modeling/Rigging 切换、固定代表入口与英文往返，非逐按钮人工验收 |
| 中文低窗口说明 | PASS，全长 3 行 | `reason-low-150-03/bilingual-events.json`；840×480，150%，实际说明与背板不遮挡菜单 |
| 中文无空白隐藏/恢复 | PASS，无新增说明 ink，真实全屏恢复显示 | `reason-no-fit-04/bilingual-events.json`；840×480，200%，隐藏说明而保留菜单 |
| 英文列表几何 | PASS，100%/150% 为 18/27px | `geometry-green-01`；方向按钮相对不可变既有基线保持，未复制旧 PASS |
| 本地测试网页 | PASS，14 项浏览器检查 | `site-browser-01/browser-report.json`；394 项目录、分类/分页、旧记录、390px 窄屏与反馈 URL；未提交真实 Issue，未证明 Pages 已部署 |

## 迁移观察器与工厂启动重载的边界

旧完整 18px 包在五个全新隔离配置中实际保存 Automatic、`fr_FR`、`zh_HANT`、`zh_HANS`、`en_US`。新候选分别启动验证前三种回退英文、后两种保留；第六进程保存中文，第七进程独立重启并重载工厂启动布局保留已保存 prefs。全部通过；旧种子、旧失败及保存文件哈希链保留。

重载的真实调用是 `wm.read_homefile(use_factory_startup=True)`，`preferencesReset=False`。它保留中文偏好并重载工厂启动布局，**不等于执行 Reset Preferences 后仍保留中文**。语言/数据名翻译开关开启时，工作区仍保留 12 个实际英文名称，Modeling 识别通过。

后台没有 GUI 事件循环，`window.workspace` setter 的异步 notifier 不能用来假称工作区已切换。测试在现有真实窗口/VIEW_3D/WINDOW、OBJECT 模式下用真实 Modeling 数据块做 context override，报告明确 `guiWorkspaceSwitchVerified=False`；名称、predicate、活动 Maya keyconfig、七根菜单和恢复原 Blender keyconfig 的断言均保留。实际 GUI 切换由最终双语 52 条记录单独验证。测试观察器及过期 API 的失败证据均未删除。

## 待人工测试与公开交付

仓库待发布目录为 394 项（当前 380、历史 14），保留 47 项历史已测标记；当前初始未测 333、全表初始未测 347。本批新增 49 项 BI 验收，新增标记共 50 项（含保留 GU-28）。既有编号与人工结果保持，自动化不替用户勾选。 49 项按入口归类：BI-H01～BI-H14（14 个热盒）、BI-M01～BI-M29（29 个菜单）、BI-C01～BI-C06（6 项跨入口/语言/数据/原生/Rigify）。具体步骤见[按入口清单](2026-10-12-tests-by-entry.md)和[统一人工总表](2026-09-14-manual-test-ledger.md)。

逐入口人工检查中文术语、长文字/灰项原因、右侧齿轮、100%/150% 与窄视窗可读性、方向/滑选/取消/重复唤出和实际鼠标手感。生产 Rigify、第三方 Feature Sets、任意资产/插件规模与真实变形结果独立验收；自动化通过不改人的测试状态。

**待公开交付**：最终源码 SHA 与本页证据绑定、完整双语 ZIP/校验、独立干净解压/启动、匿名下载重核验、GitHub 远端确认和 Pages 六个资源逐字节核验尚未收齐。发布后再更新公开 buildId/下载链接及发布快照；源码 push、本地网页检查和包生成不能互相替代。
