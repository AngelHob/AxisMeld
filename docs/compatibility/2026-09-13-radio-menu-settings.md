# 热盒单选菜单显示修复

状态：实现、构建、独立复审与安装回归完成。基线af3f5d86428。

已定位：现有互斥设置目录本来就是原生纵向菜单，绘制时把图标固定为空，缺少当前值标记。修复Transparency、Hotbox Style和三组中心按钮映射的左圆圈+右label；选中状态取自现有快照，不改配置格式。

实际Maya来源、适配边界及尚未接入的Pivot/选择约束等radio组，见[对照与缺口](../maya-mapping/2026-09-13-radio-menu-groups.md)。不把Rows独立开关变成单选，不改QWER布局和现有设置的提交/取消语义。

## 验证

Release构建成功；57项Python单测和5个native目标通过。真实截图像素检查验证1x/2x下Style双入口、Transparency点击前/悬停/点击后重开，以及三个按钮映射独立重载。Disabled的JSON null在C++解析为空串，已修复其选中态并保留修复前失败证据。独立静态复审无剩余阻断问题。非法非预设透明度由现有配置校验拒绝；内部helper另有全空防御单测；悬停不改变选中圈；左右中三个映射组独立。

## 交付与回退

原测试入口D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe正在由用户运行，窗口有未保存场景。本批先使用同目录独立预览exe验证，不关闭用户进程、不改其配置。最终入口为 `D:/source/AxisMeld-build/phase2b-ui-test-install/blender-radio-preview.exe`；原blender.exe保持M2b版本。预览复用同目录资源和个人配置，测试过程使用factory/temp隔离配置。

更新前备份D:/source/AxisMeld-build/radio-20260913-before；原exe SHA256 3FCEBEBD3C141B01F9A0D091E37DE1DF0D97CCE15B2E7A6F3B3A0CB66BCBFEDF。6份portable配置哈希见radio-install-before.json。若以后更新原入口，退出程序后可用此备份回退。

预览exe SHA256：`6C8C1A064E360B795F24EF1A95B989FD7088DDC9E3906CBEF06866879DD490BE`。build/candidate/preview三份一致；12份Python资源与源码一致，6份portable文件与备份哈希一致；原exe哈希未变。证据：D:/source/AxisMeld-build/radio-install-verification.json。

人工清单新增S-01至S-07，总计47项仍待人工测试；自动验证不替代人工反馈。真实Maya尚缺Pivot/持续选择约束/重置枢轴组，详见RG-P01至RG-P03。

最终独立预览入口串行通过native-style、release、tools、components四套GUI回归，日志为D:/source/AxisMeld-build/radio-installed-<suite>.log；mappings专项由最终同哈希candidate通过，日志radio-mappings-final.log。release只覆盖同窗口合成事件，不代表跨窗口或真实鼠标人工验收。截图目录radio-installed-native-style和radio-mappings-final。
