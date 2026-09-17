# Windows 构建、验证与交付

更新：2026-09-17。本页用于新 Windows 机器和新的 Codex 会话，从源码接续工作；不要求复制维护者的旧磁盘、候选安装、偏好或临时审计目录。开发方向另见项目路线图与交接文档，本页不扩大功能范围。

## 1. 正确分支、Git LFS 与依赖

仓库：<https://github.com/AngelHob/AxisMeld>。**当前开发分支是 `axismeld/phase-2a`**。本页核验时，远端默认 HEAD 仍指向旧的 `axismeld/integration`。默认分支的 Download ZIP 会拿错代码，也不会准备 Git LFS 和子模块。

以下使用 PowerShell 7.3+（支持 `$PSNativeCommandUseErrorActionPreference`）；自行选择一个**没有空格**的新工作目录。路径只是示例，不是项目运行条件。`make.bat` 会拒绝含空格的源码路径。

```powershell
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$Work = 'D:\work\AxisMeld-dev'
$Repo = Join-Path $Work 'AxisMeld'
$Build = Join-Path $Work 'build-windows'
New-Item -ItemType Directory -Force $Work | Out-Null

# 分开取得普通 Git 内容和 LFS 内容，便于诊断下载失败。
$previousLfsSkip = $env:GIT_LFS_SKIP_SMUDGE
try {
    $env:GIT_LFS_SKIP_SMUDGE = '1'
    git clone --branch axismeld/phase-2a https://github.com/AngelHob/AxisMeld.git $Repo
} finally {
    $env:GIT_LFS_SKIP_SMUDGE = $previousLfsSkip
}
Set-Location $Repo
git branch --show-current
git rev-parse HEAD
git status --short
git ls-remote --symref origin HEAD
```

已有 checkout 先检查未提交改动，再 fetch、切换正确分支和 `git pull --ff-only`；不要 reset/clean 覆盖未提交工作。构建前阅读根目录 [AGENTS.md](../AGENTS.md)、[CHANGELOG.md](CHANGELOG.md) 和本轮设计/验收文档。

- 多数图片、字体、二进制和 `.blend` 仍走 LFS。上游原有对象可从 Blender 官方 upstream 下载。
- **`release/datafiles/startup.blend` 是指定的普通 Git 二进制例外**，其 filter/diff/merge/text 均 unset。另有一张明确列出的参考 PNG 例外；不要取消整体 LFS 规则。
- 当前 startup SHA-256：`07ecbc61e9b9853ab0c81f84c628dc84d6ebebfc0be55d793bfe48f9fbe35382`。它是含 Rigging 的真实压缩 blend，不是 LFS pointer 文本。未来批准修改资产后，应同步更新验收与版本记录。
- `lib/windows_x64` 是独立 Git 子模块，里面的依赖也使用 LFS；根仓库 LFS 下载不能代替子模块下载。

```powershell
git lfs install --local
git remote add upstream https://projects.blender.org/blender/blender.git
git remote set-url --push upstream DISABLED
# 已有 upstream 时先核对 URL，省略 remote add，不覆盖个人远端。
git lfs pull upstream
git lfs fsck --objects
git check-attr filter diff merge text -- release/datafiles/startup.blend
Get-FileHash release/datafiles/startup.blend -Algorithm SHA256

# .gitmodules 的 update=none 需要显式启用，与 check_libraries.cmd 一致。
git config --local submodule.lib/windows_x64.update checkout
git submodule update --init --progress lib/windows_x64
git -C lib/windows_x64 lfs pull
git -C lib/windows_x64 lfs fsck --objects
git submodule status -- lib/windows_x64
```

完整 LFS/依赖下载可能较大。遇到 404、配额、代理或认证错误，保存具体 URL/OID 并处理下载问题；不要把 pointer 文本交给 CMake，不要上传凭据。当前 Windows 子模块 pin 是 `60d6e96b917568278d400a4024c98da0fb777338`；未来以 checkout 的 gitlink 为准，**不要自行切到子模块 main 最新版**。

`make.bat update` 会经 `update_sources.cmd` 调用 `make_update.py` 更新源码与依赖，不是“仅补齐当前提交依赖”的命令。重现固定提交使用上述显式下载流程。

## 2. 工具链与验证边界

安装 Git for Windows + Git LFS、Visual Studio Build Tools 的 **Desktop development with C++** 工作负载（x64 MSVC、Windows SDK、CMake 工具）、PowerShell 7。独立测试需要普通 Python，站点逻辑测试另需 Node.js。新机器正常安装这些工具，不复制旧 Visual Studio 安装目录或认证配置。

| 项目 | 本机核验值，非所有受支持组合的声明 |
| --- | --- |
| 系统 | Windows 10 19045 x64 |
| 生成器 | Visual Studio 18 2026，Build Tools |
| MSVC | 编译器 19.51.36248.0；工具目录 14.51.36231 |
| Windows SDK | 10.0.26100.0 |
| CMake | 4.3.1-msvc1 |
| Git / Git LFS | 2.55.0.windows.3 / 3.7.1 |
| 普通 Python / Blender Python | 3.14.4 / 3.13 |
| PowerShell / Node.js | 7.6.5 / 24.15.0 |

仓库 CMake 最低版本为 3.21，但选择 VS 2026 时仍需认识该生成器的 CMake，不能据此推断 3.21 可用。`make.bat` 也识别 2022/2022b 等参数；本页没有在新机器重新验证这些组合。

把所选 cmake/ctest 加入当前终端 PATH，检查 `cmake --version` 和 `cmake --help` 的生成器列表。VS 检测使用 `vswhere`、`vcvarsall.bat`；Build Tools 参数是 **`2026b`**，不是 `2026`。依赖 Python 由 `find_dependencies.cmd` 从 `lib/windows_x64/python/313`（回退 311）检测，普通 Python 不参与编译链接。

## 3. 新 build、新 install

以下参数来自 `build_files/windows/parse_arguments.cmd`，采用现有开发构建的 `full + developer + with_tests` 路线：Release 配置、断言和测试启用。它不是官方 release preset，也不声称包含预编译 CUDA/HIP/oneAPI kernels。

```powershell
Set-Location $Repo
# 切换编译器/生成器不要复用旧 CMakeCache。
.\make.bat 2026b x64 full developer with_tests builddir $Build nobuild
cmake --build $Build --config Release --parallel 2

$Revision = (git rev-parse --short=12 HEAD).Trim()
$Candidate = Join-Path $Work "candidate-$Revision"
if (Test-Path -LiteralPath $Candidate) { throw '选择全新候选目录，不覆盖旧安装或偏好' }
cmake --install $Build --config Release --prefix $Candidate
$Blender = Join-Path $Candidate 'blender.exe'
& $Blender --version
```

`nobuild` 仅配置。随后显式 build/install 可分别记录退出码；省略 nobuild 时，现有 `build_msbuild.cmd` 自己也会构建 INSTALL 项目。

已按 CMake 源码核实：

- `source/creator/CMakeLists.txt` 整体安装 scripts，因此 `scripts/modules/rigify`、`scripts/startup/rigify_builtin.py` 和 AxisMeld 菜单/键位会随源码安装，不需要 `addon_enable`。
- 源码已无 `scripts/addons_core/rigify`；**全新**安装不会有旧插件。CMake 不主动清除旧前缀遗留文件，故不能把覆盖安装当作迁移验证。
- Windows 规则安装 `portable/README.txt`。新候选保留标记，但不带个人 userpref、startup 或 profile。
- startup 由 `source/blender/editors/datafiles/CMakeLists.txt` 的 `data_to_c_simple` 编入 exe。修改资产必须重编 native，仅复制 Python/磁盘 startup 无法更新内嵌工作区。

现有本机 native 构建与候选验收通过；**本页从零安装配方尚未在第二台机器完整执行**。历史 stage/package 编排曾依赖维护者旧候选与临时 receipt，不能当作跨机工具，本页不要求那些文件存在。

## 4. 可移植的轻量验证

先确认当前终端没有残留的个人 `BLENDER_USER_CONFIG` / `BLENDER_USER_RESOURCES` 覆盖。品牌/portable 检查在设置隔离配置前运行：

```powershell
& "$Repo/tools/axismeld/verify_windows_build.ps1" -InstallDir $Candidate -SourceDir $Repo
python "$Repo/tests/python/axismeld_cli_identity.py" --blender $Blender
python "$Repo/tests/python/axismeld_portable_paths.py" --blender $Blender
$Audit = Join-Path $Work "audit-$Revision"
New-Item -ItemType Directory -Force $Audit | Out-Null
python "$Repo/tests/python/axismeld_rigging_catalog_test.py"
python "$Repo/tests/python/axismeld_rigging_ui_test.py"
python "$Repo/tests/python/axismeld_native_rigging_test.py"
python "$Repo/tests/python/axismeld_input_test.py"
```

不要用 `unittest discover axismeld_*.py` 把全部文件混跑：仓库包含纯 Python、Blender 内脚本、GUI runner、历史布局和依赖前置 fixture 的用例。`workspace-bar` suite 仅适用于已废弃的双排顶部栏候选，当前建模菜单使用 `modeling-viewport`。

### 默认资产与后台启动

raw-asset 使用仓库 blend parser；普通 Python 3.14 自带 `compression.zstd`，较早 Python 需在独立测试环境安装 zstandard。

```powershell
python "$Repo/tests/python/axismeld_rigging_workspace_test.py" --case raw-asset `
    --asset "$Repo/release/datafiles/startup.blend" --artifacts "$Audit/raw-asset"
$env:BLENDER_USER_CONFIG = Join-Path $Audit 'isolated-config'
$env:BLENDER_USER_SCRIPTS = Join-Path $Audit 'isolated-scripts'
New-Item -ItemType Directory -Force $env:BLENDER_USER_CONFIG, $env:BLENDER_USER_SCRIPTS | Out-Null
& $Blender --background --factory-startup --python-exit-code 1 `
    --python "$Repo/tests/python/axismeld_rigging_workspace_test.py" -- `
    --case factory --artifacts "$Audit/factory"
& $Blender --background --factory-startup --python-exit-code 1 `
    --python "$Repo/tests/python/axismeld_rigging_workspace_test.py" -- `
    --case factory-reset --artifacts "$Audit/factory-reset"
```

通过标准包括退出码、PASS 标记和 receipt。资产需保留原 11 页/场景，新 Rigging 为 OBJECT，默认活动页 Layout，每个 Workspace 有有效窗口布局关系；普通 blend 能打开不等于内嵌 factory 能启动。

| 高级 case | 实际参数与前置条件 |
| --- | --- |
| `asset` | `--asset <待查blend>`，普通文件读入 |
| `embedded-append` | `--original <无Rigging的旧startup fixture>`，内部使用原生 `<startup.blend>` sentinel |
| `append-save` | 同时提供 `--original`、`--asset` |
| `reopen` | 与前一 append-save/embedded-append 使用同一 artifacts |
| `old-file` / `no-ui` | `--original`，分别检查 Load UI true/false |
| `user-startup` | 不带 factory-startup，只在隔离 config 放旧 fixture 的 startup.blend |
| `gui-reopen` | GUI runner 自动另起后台进程，依赖刚保存的场景与 JSON |

旧 fixture 不在普通工作树中；可以取得指定历史提交 pointer 对应的原 LFS 对象，或用独立旧 Blender 制作无 Rigging 默认文件。未准备 fixture 就记录跳过，不能使用个人 startup，也不能用当前含 Rigging 的资产冒充旧文件。历史完整矩阵通过不等于换机后已复测。

### 原生 Rigify

```powershell
$RigifyAudit = Join-Path $Audit 'rigify'
foreach ($Case in 'factory', 'generate', 'reopen', 'lifecycle') {
    python "$Repo/tests/python/axismeld_rigify_builtin_test.py" `
        --blender $Blender --artifacts $RigifyAudit --case $Case
}
```

runner 自建隔离进程；generate/reopen 通过同一 artifacts 交换文件。默认 case=all **必须提供 `--legacy-blender`** 来制造真正旧版偏好，所以新机器不要直接省略 case。旧偏好迁移需另备已核验旧二进制，不是新 build 的隐式依赖。

## 5. GUI 与当前候选资源清单

`axismeld_rigging_workspace_events.py`、`axismeld_rigify_builtin_events.py` 均接收 `--blender`、`--artifacts`、`--verification`。verification 至少包含当前 exe 的 `binary_sha256` 和 `resources: [{path, sha256}]`，资源 path 以版本目录中的 scripts 开始。旧发布 exe SHA 不能验证一次新编译。

下面先比较源码/安装文件，再为**当前**候选生成清单。覆盖现有 AxisMeld/Rigify 模块及 14 个接入文件；未来增加接入点应扩展清单，不以缩小清单掩盖缺文件。

```powershell
$Verification = Join-Path $Audit 'candidate-resources.json'
@'
import hashlib, json, pathlib, sys
repo, install, output = map(pathlib.Path, sys.argv[1:])
versions = [p for p in install.iterdir() if (p / 'scripts/modules').is_dir()]
assert len(versions) == 1, 'Require one fresh versioned install'
version = versions[0]
paths = set()
for folder in ('scripts/modules/axismeld', 'scripts/modules/rigify'):
    files = list((repo / folder).rglob('*.py'))
    assert files, folder
    paths.update(p.relative_to(repo).as_posix() for p in files)
paths.update('''scripts/addons_core/bl_pkg/bl_extension_ui.py
scripts/modules/addon_utils.py
scripts/presets/keyconfig/AxisMeld_Maya_2026.py
scripts/startup/bl_operators/axismeld.py
scripts/startup/bl_ui/__init__.py
scripts/startup/bl_ui/properties_data_mesh.py
scripts/startup/bl_ui/space_axismeld_menubar.py
scripts/startup/bl_ui/space_axismeld_native_modeling.py
scripts/startup/bl_ui/space_axismeld_native_rigging.py
scripts/startup/bl_ui/space_image.py
scripts/startup/bl_ui/space_topbar.py
scripts/startup/bl_ui/space_userpref.py
scripts/startup/bl_ui/space_view3d.py
scripts/startup/rigify_builtin.py'''.splitlines())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
rows = []
for path in sorted(paths):
    assert (version / path).is_file(), path
    assert sha(repo / path) == sha(version / path), ('Stale installed resource', path)
    rows.append({'path': path, 'sha256': sha(repo / path)})
assert not (version / 'scripts/addons_core/rigify').exists(), 'Old add-on survived'
output.write_text(json.dumps({'binary_sha256': sha(install / 'blender.exe'),
                              'resources': rows}, indent=2), encoding='utf-8')
print('RESOURCE_VERIFICATION_PASS', len(rows), output)
'@ | python - $Repo $Candidate $Verification

python "$Repo/tests/python/axismeld_rigging_workspace_events.py" `
    --blender $Blender --artifacts "$Audit/rigging-gui" --verification $Verification
python "$Repo/tests/python/axismeld_rigify_builtin_events.py" `
    --blender $Blender --artifacts "$Audit/rigify-gui" --verification $Verification
python "$Repo/tests/python/axismeld_hotbox_ui_runner.py" `
    --blender $Blender --suite modeling-viewport --artifacts "$Audit/modeling-gui"
```

runner 自己另起工厂 GUI，模拟事件并隔离配置，不连接用户编辑中的窗口。需要真实图形桌面/GPU；不能给 GUI 用例加 background。既有截图回归主要在 1920×1017、默认缩放运行；其他尺寸/DPI 的失败需区分观察器与产品问题。

Rigging GUI 覆盖 metarig 创建、原生绑定/Undo、Normalize/Undo、插件菜单宿主、工作区添加/重命名/删除、保存和独立重开；不证明生产蒙皮质量、第三方 Feature Set 或 Maya 专有算法完成。

## 6. 默认资产仅在批准改布局时再生成

正常编译直接用已提交 startup，不重新生成。维护工具实际入口：

```powershell
python "$Repo/tools/utils/axismeld_rigging_workspace_asset.py" `
    --blender $KnownGoodBlender --input $OriginalStartup `
    --output $NewStartup --manifest $AssetManifest
```

这些路径由本次资产任务明确选择。input 必须是无 Rigging 的原始 11 页资产，output 不存在且不同于输入。工具执行后台基线、真实 GUI 激活 Rigging→Layout、后台重开、raw DNA 审计，拒绝改变原场景/工作区。GUI 需匹配原资产 1920×1080 drawable area，会拒绝静默缩放后的输入。

不要用通用 Workspace `.copy()` 或后台仅设置 window.workspace 代替原生切换：前者有 real-user 陷阱，后者不会完成窗口布局关联。合格资产仍必须重编并实际 factory 启动验收，不能用 C++ 空指针绕过不完整数据。

## 7. 新包与既有公开包分别核验

目前没有已在另一机器验证的一键 build→stage→publish 工具。历史本机编排不作为依赖；从完整**新 install**开始。

现有开发缓存为 `WITH_WINDOWS_BUNDLE_CRT=OFF`、`WITH_CYCLES_NATIVE_ONLY=ON`、`WITH_BUILDINFO=OFF`。面向其他机器发布时，应在独立发布 build 审查这些设置、运行时依赖、CPU/GPU支持和许可证，不能自动称为官方 Blender 等价发行版。full/release 区别以仓库 preset 为准，后者涉及额外 GPU 内核配置，不可未经验证替换。

ZIP 使用未经过个人交互的新候选，保留 DLL、blender.shared、Python、数据及 portable 标记；不能只打包 exe。去除 PDB/测试符号应在独立 staging 副本逐项记录，不改已验收原目录。

```powershell
$Zip = Join-Path $Work "AxisMeld-$Revision-windows-x64.zip"
if (Test-Path -LiteralPath $Zip) { throw '选择新的 ZIP 文件名' }
# 先确认 Windows tar --version 可用；-a 按 .zip 后缀选择格式。
$CandidateParent = Split-Path -Parent $Candidate
$CandidateLeaf = Split-Path -Leaf $Candidate
tar.exe -a -c -f $Zip -C $CandidateParent $CandidateLeaf
Get-FileHash $Zip -Algorithm SHA256
$Extracted = Join-Path $Work "extract-$Revision"
if (Test-Path -LiteralPath $Extracted) { throw '解压验收目录必须是新的' }
New-Item -ItemType Directory $Extracted | Out-Null
tar.exe -x -f $Zip -C $Extracted
$ExtractedInstall = Join-Path $Extracted $CandidateLeaf
& "$Repo/tools/axismeld/verify_windows_build.ps1" -InstallDir $ExtractedInstall -SourceDir $Repo
```

对解压目录重做源资源比较、factory 和相关行为检查，记录源码完整 SHA、子模块 pin、配置/构建日志、exe/ZIP hash 及未测项；不能仅验证压缩前候选。WITH_BUILDINFO=OFF 时 version 输出不足以追溯，须依赖外部清单。

**既有 2026.09.17 Rigging 包**的公开 pins/hash 见 [交接快照](compatibility/2026-09-17-handoff-snapshot.json)。固定发布包的只读审计：

```powershell
python "$Repo/tools/utils/axismeld_release_audit.py" `
    --archive $DownloadedReleaseZip --report "$Audit/published-release-audit.json" --repo $Repo
```

此审计需要普通 Python 3.11+。ZIP 旁必须同时放置 `<完整ZIP文件名>.sha256`（例如 `preview.zip.sha256`，下载发布资产提供的 sidecar），checkout 需保留该发布提交的 Git 历史。该工具验证固定历史包，不用于批准新编译的不同 exe。公开下载入口在 `tools/testing_site/config.json` 的 releaseUrl；不要把本机路径放进公开配置。tag 必须指向实际验收源码，Release 列明限制。新机器自行正常登录 GitHub，不复用旧聊天中的凭据。

## 8. 公开测试网页与发布顺序

门户源目录是 `tools/testing_site/`，运行时无 npm 构建依赖。访客状态在各自浏览器 localStorage，**不跨设备自动同步**。页面可导出 JSON 供自行转移、备份或反馈；目前没有导入功能，不能承诺换机后恢复网页勾选。私人 Sites 数据库和备注不进入公开 catalog。

```powershell
Set-Location $Repo
python tools/utils/axismeld_public_test_catalog.py --check
python tools/testing_site/tests/validate_site.py
node tools/testing_site/tests/state_check.mjs
python -m http.server 8765 --bind 127.0.0.1 --directory tools/testing_site
```

浏览器验收需独立 Playwright 开发依赖，按 [站点 README](../tools/testing_site/README.md) 设置 PLAYWRIGHT_MODULE/BROWSER_EXECUTABLE；实际入口是 `node tools/testing_site/tests/browser_check.mjs <审计目录>`。部署只需 index.html、app.mjs、styles.css、config.json、catalog.json、favicon.svg，不包含测试脚本、私人数据和安装包。

当前 checkout 没有 `.github/workflows` 自动部署流水线。Pages 分支/设置需在维护者仓库核对，不能把 push 当作网页已更新。独立 Pages 分支应使用独立工作树准备这六个文件，核对差异再提交，勿在源码工作树覆盖根目录或 force-push。

1. 完成源码/安装/解压/行为验证，更新设计、CHANGELOG、待测项，保留稳定编号和已有结果。
2. 提交并推送 `axismeld/phase-2a`，用 `git ls-remote origin refs/heads/axismeld/phase-2a` 核对远端 SHA。
3. 按本次授权发布明确源码指向的 Release、ZIP 与校验信息，成功后才更新真实 buildId/releaseUrl。
4. 发布 Pages 资源，核对公开 config/catalog/buildId、下载链接；源码、包、网页分别验证。

不要上传个人 portable、用户名路径、令牌、认证文件、私人测试站或 Autodesk/Maya 安装目录。仓库保留公开基线投影与兼容实现，参考菜单不构成分发专有安装资源的理由。

## 9. 换机仍需确认

已按当前源码核对命令参数、安装规则、测试入口及本机版本。尚未在第二台 Windows 从空目录完成下载、全量编译、干净安装与 GPU GUI 回归，也未把历史本机打包编排变成跨机流水线。新机器必须记录实际工具链、LFS访问、显卡驱动、缩放和运行时依赖。

接续时让 Codex 先读 AGENTS、交接/路线图、本页和 CHANGELOG，确认分支、远端 SHA 与未提交改动，再选择本批需求的验证。以仓库文件和新 receipt 为依据，不依赖旧聊天记忆或维护者磁盘路径。
