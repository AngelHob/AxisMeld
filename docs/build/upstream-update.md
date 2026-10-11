# 从固定 Blender 提交更新 AxisMeld

更新：2026-10-11。本文用于已经批准的上游合并；新机器重现当前发布版请从 [HANDOFF](../HANDOFF.md) 和 [BUILD_AND_DELIVERY](../BUILD_AND_DELIVERY.md) 开始。

当前开发分支是 **`axismeld/phase-2a`**。`axismeld/integration` 只同步公开首页，不作为本轮合并目标。合并保留双方历史，不 rebase、不 force-push，不执行会更新源码分支的 `make.bat update` / `make_update.py`。

## 本轮固定边界

| 项目 | 本轮值 |
| --- | --- |
| 阶段一交付检查点 | `bbce9d3483432f30eff1cc94b61d08838eba25eb`；其中 short-window 包的功能/native 源码为 `665cb38b123d89d273d6f68e2c748a258abfff47` |
| 合并前 Blender 基线 | `18d84097b4f859582afdec57eece2ae880371adc`，5.3.0 Alpha |
| 本轮官方目标 | `754ebe3c4b4e1402a159df6e1e58823cc93ef887`，5.4.0 Alpha |
| Windows x64 gitlink | `aa0c5db72fa9488bb685bdddbede780d19f483f5`，以目标和合并索引中的 gitlink 复核 |
| 过程设计 | [极低窗口修复与主干同步](../development/2026-10-11-short-window-and-upstream.md) |

这些值固定本轮来源，不表示合并构建或发布已经通过。源码、依赖、构建、实际运行和公开包分别记录证据；旧 5.3 short-window 包继续保持原发布身份，不能用它证明 5.4 兼容。

## 1. 固定来源后合并

示例使用本机开发工作树 `D:\source\AxisMeld-phase0`；其他机器改为自己的无空格路径。已有合并正在进行时从冲突处理继续，不重复执行本节。

```powershell
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true # PowerShell 7.3+
$Repo = 'D:\source\AxisMeld-phase0'
$UpstreamCommit = '754ebe3c4b4e1402a159df6e1e58823cc93ef887'
$LibPin = 'aa0c5db72fa9488bb685bdddbede780d19f483f5'
Set-Location $Repo
if ((git branch --show-current).Trim() -ne 'axismeld/phase-2a') { throw '不是当前开发分支' }
if (git status --porcelain) { throw '先交付或明确保存现有工作，不覆盖未提交改动' }
git rev-parse HEAD
git remote get-url upstream
```

`upstream` 必须是 `https://projects.blender.org/blender/blender.git`。没有该 remote 时添加；若已有不同 URL，先核实用途，不覆盖个人配置。禁用它的推送 URL，窄范围取得本轮明确提交；不自动换成随后移动的 main，也不递归拉取其他平台库。

```powershell
# 仅当 upstream 尚不存在：
# git remote add upstream https://projects.blender.org/blender/blender.git
git remote set-url --push upstream DISABLED
git -c fetch.recurseSubmodules=false fetch --no-tags --no-recurse-submodules upstream $UpstreamCommit
if ((git rev-parse FETCH_HEAD).Trim() -ne $UpstreamCommit) { throw '上游提交不符' }
git lfs fetch upstream $UpstreamCommit
git merge --no-ff --no-commit $UpstreamCommit
```

冲突时 merge 的非零退出码不等于可以继续构建；先查看 `git status`、`git diff --name-only --diff-filter=U` 和 `MERGE_HEAD`，逐项解决并暂存。结束时应无 unmerged 文件，`MERGE_HEAD` 仍为固定目标；不要用整文件 ours/theirs 丢弃另一方修改。保留 AxisMeld 品牌、Rigging 内嵌资产、七根 Modeling、独立灰 Options、原生菜单 provider 和精确 File 松键 token，同时接受上游 API、Project 菜单、原生导入器条件与 UI 所有权变化。

合并可能带入上游既有空白格式告警；只修本批新增的问题，不重格式化上游全文。若需取消尚未提交的合并，先检查合并后是否新增了必须保留的工作，再使用 `git merge --abort`；不使用 reset/clean 清场。

## 2. 仅检出精确 Windows 依赖

主仓库 LFS 和 Windows 库 LFS 是两个独立来源。主仓库先取官方目标的 LFS；AxisMeld 的 startup 保持当前 `.gitattributes` 的普通 Git 例外。源码冲突解决后执行 `git lfs checkout` / `git lfs fsck --objects`，检查真实资产，不能把 pointer 文本交给 CMake。

库更新使用**合并索引**的 gitlink，因此适用于 merge 尚未提交的阶段；提交后索引与 HEAD 应一致。先停止依赖旧库的构建，保留旧 pin，检查库工作树干净。

```powershell
$Lib = Join-Path $Repo 'lib/windows_x64'
$RecordedPin = (git rev-parse ':lib/windows_x64').Trim()
if ($RecordedPin -ne $LibPin) { throw '合并索引的 Windows gitlink 不符' }
if (Test-Path -LiteralPath "$Lib/.git") {
    if (git -C $Lib status --porcelain) { throw 'Windows 库有本地修改' }
    git -C $Lib rev-parse HEAD
    git -C $Lib fetch --no-tags origin $LibPin
}
$PreviousSmudge = $env:GIT_LFS_SKIP_SMUDGE
try {
    $env:GIT_LFS_SKIP_SMUDGE = '1'
    git submodule update --init --checkout --progress -- lib/windows_x64
} finally {
    $env:GIT_LFS_SKIP_SMUDGE = $PreviousSmudge
}
if ((git -C $Lib rev-parse HEAD).Trim() -ne $LibPin) { throw 'Windows 库检出不是精确 pin' }
git -C $Lib lfs fetch origin $LibPin
git -C $Lib lfs checkout
git -C $Lib lfs fsck --objects
git submodule status -- lib/windows_x64
git -C $Lib status --short
```

`--checkout` 明确覆盖 `.gitmodules` 的 `update=none`。已初始化且精确提交预取完成时可添加 `--no-fetch`，避免检出时继续下载。只处理 Windows x64；不使用 `--remote`、递归更新所有平台或切到子模块 main 最新版。`make.bat update` 经 `update_sources.cmd` 调用 `make_update.py`，其中包含源码更新与 `pull --rebase`，不是固定依赖恢复工具。

## 3. 独立配置、构建和安装 5.4

选用本机已安装且支持该生成器的工具链。以下 VS 2026 Build Tools 路径是本机示例；其他机器按实际安装设置，不能混用旧生成器缓存。新 build、新 candidate 与旧 5.3 验收包分开。

```powershell
$CMake = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$CTest = Join-Path (Split-Path $CMake) 'ctest.exe'
$MergeBuild = 'D:\source\AxisMeld-build-main-754ebe3c4b4e'
$Candidate = 'D:\source\AxisMeld-candidate-main-754ebe3c4b4e'
if (Test-Path -LiteralPath $MergeBuild) { throw '首次配置选择新 build；失败重试保留该缓存和日志' }
if (Test-Path -LiteralPath $Candidate) { throw '选择新的 candidate 目录' }
& $CMake -S $Repo -B $MergeBuild -G 'Visual Studio 18 2026' -A x64 `
    -C "$Repo/build_files/cmake/config/blender_full.cmake" `
    -C "$Repo/build_files/cmake/config/blender_developer.cmake" `
    -DWITH_GTESTS=ON -DWITH_TESTS_SINGLE_BINARY=OFF -DWITH_WINDOWS_BUNDLE_CRT=ON `
    "-DCMAKE_INSTALL_PREFIX=$MergeBuild/bin/Release"
& $CMake --build $MergeBuild --config Release --target blender bf_intern_draco_bridge bf_intern_meshopt_bridge blender-launcher BlendThumb cycles_osl_shaders axismeld_identity_test axismeld_transform_axis_test axismeld_hotbox_state_test axismeld_hotbox_menu_test editor_hotbox_hotbox_model_test editor_hotbox_icons_hotbox_icons_test transform_axismeld_snap_test windowmanager_wm_operator_completion_test -- /m:8 /p:CL_MPCount=2 /nologo
& $CMake --install $MergeBuild --config Release --prefix "$MergeBuild/bin/Release"
& $CMake --install $MergeBuild --config Release --prefix $Candidate
& "$Candidate/blender.exe" --version
```

每一步成功后再继续，日志分别保存。检查 cache 中 GTests ON、single binary OFF、CRT ON、Python 和 Windows 库路径；新 full preset 的 Jolt 不应为绕过缺库而关闭。developer preset 会设 CRT OFF，故末尾明确覆盖 ON。BUILDINFO OFF 时须另外记录源码/merge parents、未提交差异和库 pin，不从版本字符串推断来源。

CTest 使用配置时记录的 `$MergeBuild/bin/Release`，单独安装 candidate 不会改变其运行目录。新安装必须完整拥有 5.4 脚本、Python、DLL、Rigify builtin、内嵌 startup 和 portable 标记；不要混入旧 5.3 安装。源码或库变化后重新构建相应目标，不能沿用之前的成功日志。

## 4. 先保留失败，再更新派生物与验证

先运行当前输入、菜单路由和公开目录生成器的 `--check`，保留合并后的首次结果。输入继承或 source hash 改变时，用对应 generator 更新派生文件并审查差异，不改冻结的 Maya 来源来迎合新 Blender。检查七根、原生 provider/alias 和 Maya 参考数量是否保持；上游 provider 自然带入的新原生叶子不计为新的 Maya 等价实现。

```powershell
python -B tools/utils/axismeld_input_audit.py --check
python -B tools/utils/axismeld_workspace_menu_routes.py --check
python -B tools/utils/axismeld_public_test_catalog.py --check
```

运行当前全部普通 Python 的 AxisMeld 纯测试；需要 `bpy`、`--blender` 或 GUI 的脚本另行运行，不能把缺少运行环境当作产品通过或跳过。原生测试先用新 build 的 `ctest -N` 核对名字，再实际执行 AxisMeld、热盒 model/icons、临时吸附及 WM completion 等已配置组；枚举不算通过，记录实际组数与 case 数，不沿用 5.3 的数字。

真实运行至少核对：factory/保存打开、Rigging/Rigify、Modeling 七根和新 Transform 原生条目、Project 条件菜单、原生导入器、Options 与插件回调、QWER/重复唤出、File 确认链/跨窗释放、短窗口全文零交叠及无空间隐藏后恢复。界面测试使用隔离配置与实际 5.4 candidate，记录窗口/缩放，串行占用 GUI。自动化不替人工验收。

## 5. 提交与发布独立取证

更新本批设计、CHANGELOG、当前基线和新增人工待测项，保留所有旧编号/结果。创建包含两个父提交的 merge commit，消息写明固定上游 SHA；发布包只接受最终已提交且与验证源码一致的内容。推送 `axismeld/phase-2a`，再用 `git ls-remote origin refs/heads/axismeld/phase-2a` 核对，禁止推送 upstream。默认 integration 仍按当前规则只同步首页，不自动合并开发分支。

新包从完整新 install 独立 staging，核对源码、gitlink、资源/文件清单、5.4 的精确白名单、许可证与运行库。随后干净解压、factory、实际 GUI、发布、匿名下载重验；全部成功后才更新公开 config 的下载入口，并逐字节验证 Pages 的精确 Git blob。详见 [构建与交付](../BUILD_AND_DELIVERY.md)。旧包和历史验证数字保持；未完成的合并构建、GUI 或发布步骤明确记为待完成。
