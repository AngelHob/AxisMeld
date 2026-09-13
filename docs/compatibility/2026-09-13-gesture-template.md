# 热盒共用划选模板与QWER重复唤出

用户反馈两项：其他热盒离开按钮后划选失效；QWER一直按住时，松LMB再按无法重新唤出。基线129373b45c6，2026-09-13。

## 结果与范围

方向热盒共用Views的五行几何函数，水平中心留白由32收紧到8逻辑像素，保留每项完整label和既有方向。QWER、其radial子菜单、Space路径的同一工具树及组件RMB支持显示行列向外延续选中与释放提交。原生列表、分页和radio组保持实际行命中；禁用与缺席方向阻挡邻项，真实按下点/当前环中心保护取消与退一级。

QWER持键为会话，LMB为一次划选：松LMB后收起，继续持QWER可在新的鼠标位置再次按LMB开环。成功、空中心和禁用项释放均能重新唤出。18个经adapter确认的同步工具叶子动作保留会话；模式/视区改变或原生模态仍沿close-before-dispatch规则。Esc、先松工具键、失焦和新工具交接沿原所有权规则结束，RMB组件仍一次一会话。

## 根因与审查修复

只有Views专用路径调用外延helper；工具与普通Space路径只查矩形。原helper又只认识Views中心、缺少工具空方向阻挡。本批限定当前活动radial层，并保护未等宽标签的行外延。原LMB释放会close_guard，后续LMB没有重新开环的处理器；本批只回到隐藏armed状态，下次鼠标按下刷新快照。

审查补齐：隐藏armed态不调用空path布局；普通Space采用真实press_position死区；当前子环外延不再被隐藏祖先中心先行返回吞掉。只允许先向外后回当前中心退一级，普通native列表祖先返回保留。

## 验证与证据

- 旧radio预览程序实际RED：Q一次持键内第一笔Lasso成功，第二笔移位LMB不能再开Paint；退出1。日志D:/source/AxisMeld-build/rearm-old-red-tools.log，截图rearm-old-red-artifacts/rearm-select-second-stroke.png。
- Native先有4组针对性RED，后52项布局/命中测试全部通过；模型记录见../superpowers/reviews/2026-09-13-gesture-model.md。完整5个native目标与57项Python单测均通过，日志gesture-native.log / gesture-python.log。
- 首版工具GUI通过多次唤出、空/灰取消、新原点、外64px实际提交、Space实际按下点取消、先松触发键、Esc/失焦/切工具、Edit与四视图、F13个人改键。最终祖先中心修正后再次通过完整tools；W/R经隐藏根中心角点后继续选择三级View的实际动作也通过，日志gesture-tools-final-green.log。
- 最终组件GUI已通过，包括新增四向外延、缺席NW与禁用方向不误触，以及M2b目标拾取/提交/取消回归。

最终Views菜单suite与native-style已通过。menus测试原先沿用M2a之前的Select条目，将首项误认为Object / Component；当前首项已是Active Mesh Components。仅更新fixture标签和目标index，保留原本“松Space前已进入EDIT”的状态断言，回归通过。最终release与tools同样通过。五套最终candidate GUI日志为gesture-final-components.log、gesture-final-menus.log、gesture-final-native-style.log、gesture-final-release.log、gesture-tools-final-green.log；每套退出0且PASS marker匹配，保留既有libpng ICC提示。

## 人工验收

集中清单新增G-01至G-10，累计57项仍待人工测试。新增重点：实体鼠标快划/远划、同次QWER持键多次LMB、边缘/不同DPI、嵌套返回、原生列表外不选中。本批自动输入与截图不代表真实手感或跨OS窗口验收，已有极窄Tool Header遮挡仍保留。

## 安装与回退

测试使用factory/temp独立配置。备份D:/source/AxisMeld-build/gesture-20260913-before保留原blender.exe（M2b）和blender-radio-preview.exe（radio版）；portable6份文件哈希见gesture-install-before.json。最终安装时再次确认待替换exe未运行，仅更新native exe，无配置迁移或Python资源修改。

## 最终安装

已确认原入口未运行后更新 `D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`，同时更新原 `blender-radio-preview.exe` 别名，保留前述两份旧版备份。未修改个人配置。

最终SHA256：`E8674E2E653C0819C469CC8FAA91AE870B28FE16EC950F29B5D526812391AB49`。build/candidate/installed/preview四份exe一致；12份Python资源与源码匹配，6份portable配置与安装前哈希一致。核验记录D:/source/AxisMeld-build/gesture-install-verification.json。

原入口安装态hotbox smoke已退出0且具备AXISMELD_HOTBOX_EVENTS_PASS，日志gesture-installed-hotbox.log；测试后再次核验四份exe、12份资源和6份portable文件一致。代码只在本地提交，不推送。
