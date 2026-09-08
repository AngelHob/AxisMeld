# AxisMeld Phase 0 Build and Product Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a Windows-first AxisMeld source baseline that retains Blender upstream ancestry, builds reproducibly, identifies itself as AxisMeld in user-visible surfaces, and keeps its development preferences isolated from an installed Blender.

**Architecture:** Add a small `bf::axismeld` identity library under the dedicated AxisMeld namespace, then connect it through narrow build-system seams to the creator and window-manager modules. Preserve Blender's file-format version, command-line compatibility, executable filename, and runtime dependencies; use a portable profile directory for Phase 0 isolation and verify the installed build with an independent PowerShell smoke test.

**Tech Stack:** Blender 5.3 alpha C/C++, CMake, GoogleTest, Python 3, PowerShell 7, Visual Studio 2022 Build Tools, Git.

**Spec:** `docs/design/2026-09-08-axismeld-architecture.md`

## Global Constraints

- Work on `axismeld/integration`; keep `upstream` fetch-only with its push URL set to `DISABLED`.
- The bootstrap Blender commit is `18d84097b4f859582afdec57eece2ae880371adc`; record a newer upstream commit explicitly if Task 1 updates it.
- Keep `BLENDER_VERSION`, `BLENDER_FILE_VERSION`, `.blend` compatibility, Blender Python module names, and `blender.exe` unchanged in Phase 0.
- AxisMeld product version starts at `0.1.0-dev` and must always be displayed together with the underlying Blender version.
- New AxisMeld source files use `SPDX-FileCopyrightText: 2026 AxisMeld contributors` and `SPDX-License-Identifier: GPL-2.0-or-later`.
- Add no external runtime dependency and do not copy Maya code, visual assets, icons, or proprietary algorithms.
- Except for inherited Blender code and third-party dependencies, all implementation, tests, build scripts, and project documents are produced by AI; humans define goals, make decisions, and perform final acceptance.
- Official AxisMeld operation remains completely non-profit; GPL rights, including commercial production use, remain unchanged.
- Build outside the source tree at `D:\source\AxisMeld-build`; install to `D:\source\AxisMeld-build\install`.
- Phase 0 supports Windows x64 first. Cross-platform product paths and packaging receive separate plans after the Windows baseline passes.

## Scope Boundary

This plan covers the design specification's project identity, non-profit and AI-authorship disclosures, upstream ancestry, thin-core module boundary, compatibility failure behavior, verification gates, and Phase 0 build baseline. It deliberately defers first-party workflow modules, third-party extension integration, semantic commands, Maya input, hotbox, viewport behavior, profile layering, modeling tools, and UV functionality. Each deferred subsystem requires its own plan after this installed build passes; Phase 0 must not advertise any of them as implemented.

## Planned File Structure

```text
source/blender/axismeld/
├─ AXM_identity.hh                # Stable product identity API.
├─ CMakeLists.txt                 # bf::axismeld library and its test target.
├─ intern/identity.cc             # Identity/version formatting implementation.
└─ tests/identity_test.cc         # Pure C++ identity unit tests.

tests/python/
├─ axismeld_cli_identity.py       # Black-box --version contract test.
└─ axismeld_portable_paths.py     # Black-box user-config isolation test.

release/datafiles/axismeld/portable/
├─ .gitignore                     # Keeps generated user state out of Git.
└─ README.txt                     # Explains Phase 0 portable preferences.

tools/axismeld/
└─ verify_windows_build.ps1       # Independent installed-build acceptance test.

docs/build/
├─ windows.md                     # Reproducible Windows build instructions.
└─ upstream-update.md             # Merge and validation procedure.
```

The following existing files receive narrow edits:

- `source/blender/CMakeLists.txt`: register the AxisMeld library directory.
- `source/blender/windowmanager/CMakeLists.txt`: link `bf::axismeld`.
- `source/blender/windowmanager/intern/wm_window.cc`: show AxisMeld in main and temporary window titles.
- `source/blender/windowmanager/intern/wm_splash_screen.cc`: show both AxisMeld and Blender versions.
- `source/creator/CMakeLists.txt`: link `bf::axismeld` and create/copy the portable directory after build.
- `source/creator/creator_args.cc`: expose the combined product/upstream version on `--version` and help output.
- `tests/python/CMakeLists.txt`: register two black-box tests.
- `CMakeLists.txt`: assign an AxisMeld Windows AppUserModel ID and friendly name.
- `release/windows/icons/winblender.rc`: change Windows product metadata without replacing Blender's inherited icons yet.

---

### Task 1: Expand the Upstream Checkout and Establish the Windows Toolchain

**Files:**
- No tracked files change.
- Populate: Blender source worktree, submodules, precompiled libraries, and test data used by the current branch.

**Interfaces:**
- Consumes: clean `axismeld/integration` at commit `5df195d` or its direct successor.
- Produces: a complete non-sparse checkout, full Git history, Blender dependencies, and a configured build directory at `D:\source\AxisMeld-build`.

- [x] **Step 1: Verify the repository safety boundary**

Run:

```powershell
git status --short --branch
git remote -v
git rev-parse --is-shallow-repository
git sparse-checkout list
```

Expected: the worktree is clean; `origin` is `https://github.com/AngelHob/AxisMeld.git`; `upstream` fetches from `https://projects.blender.org/blender/blender.git` and pushes to `DISABLED`; the repository reports `true`; sparse paths contain `docs/design`.

- [x] **Step 2: Expand history and the worktree**

Run:

```powershell
git fetch --unshallow upstream main
git sparse-checkout disable
git submodule update --init --recursive
git rev-parse --is-shallow-repository
git status --short
```

Expected: `false` followed by no status lines. Do not merge `upstream/main` in this step; expanding history must not change `HEAD`.

- [x] **Step 3: Recheck the required Windows tools**

Run:

```powershell
Get-Command git,cmake,python -ErrorAction SilentlyContinue | Select-Object Name,Source
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path -LiteralPath $vswhere) {
  & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
}
```

Expected: Git, CMake, Python, and a Visual Studio 2022 installation path. The 2026-09-09 preflight found Git and Python but did not find CMake, `vswhere`, MSBuild, or the Visual C++ compiler. If still missing, stop and obtain explicit permission before installing system software.

- [x] **Step 4: Install missing prerequisites only after permission**

Run from an elevated terminal only when Step 3 confirms they are absent and the user has approved installation:

```powershell
winget install --exact --id Kitware.CMake --accept-package-agreements --accept-source-agreements
winget install --exact --id Microsoft.VisualStudio.2022.BuildTools --accept-package-agreements --accept-source-agreements --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Expected: both installers exit with code `0`; a new terminal resolves `cmake`, and `vswhere` returns Visual Studio 2022 Build Tools.

- [x] **Step 5: Download branch-matched Blender libraries and test data**

Run from `cmd.exe`, as required by Blender's Windows build wrapper:

```bat
cd /d D:\source\AxisMeld
make.bat update
```

Expected: exit code `0`; the command reports current libraries, add-ons, and tests without switching away from `axismeld/integration`.

- [x] **Step 6: Configure the developer build**

Run:

```powershell
cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build -G "Visual Studio 17 2022" -A x64 -C D:\source\AxisMeld\build_files\cmake\config\blender_developer.cmake -DWITH_GTESTS=ON -DWITH_TESTS_SINGLE_BINARY=OFF -DCMAKE_INSTALL_PREFIX=D:\source\AxisMeld-build\install
```

Expected: CMake exits `0`, reports Visual Studio 2022 x64, and writes `D:\source\AxisMeld-build\Blender.sln` without modifying tracked files.

- [x] **Step 7: Build the unmodified baseline before AxisMeld code changes**

Run:

```powershell
cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8
& 'D:\source\AxisMeld-build\install\blender.exe' --version
```

Expected: build exit code `0`; the executable currently prints `Blender 5.3.0 Alpha` (the numeric version may be newer only if the recorded upstream base changed in Step 2).

---

### Task 2: Add the Isolated AxisMeld Identity Library

**Files:**
- Create: `source/blender/axismeld/AXM_identity.hh`
- Create: `source/blender/axismeld/intern/identity.cc`
- Create: `source/blender/axismeld/tests/identity_test.cc`
- Create: `source/blender/axismeld/CMakeLists.txt`
- Modify: `source/blender/CMakeLists.txt`

**Interfaces:**
- Consumes: a C++17 standard library and Blender's existing test framework.
- Produces: `blender::axismeld::product_name() -> std::string_view`, `project_version() -> std::string_view`, and `version_line(std::string_view) -> std::string` through target `bf::axismeld`.

- [x] **Step 1: Write the failing identity test**

Create `source/blender/axismeld/tests/identity_test.cc`:

```cpp
/* SPDX-FileCopyrightText: 2026 AxisMeld contributors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "AXM_identity.hh"
#include "testing/testing.h"

namespace blender::axismeld::tests {

TEST(axismeld_identity, ProductConstants)
{
  EXPECT_EQ(product_name(), "AxisMeld");
  EXPECT_EQ(project_version(), "0.1.0-dev");
}

TEST(axismeld_identity, CombinedVersionLine)
{
  EXPECT_EQ(version_line("5.3.0 Alpha"), "AxisMeld 0.1.0-dev (based on Blender 5.3.0 Alpha)");
}

}  // namespace blender::axismeld::tests
```

- [x] **Step 2: Register the module and confirm the test cannot build yet**

Add `add_subdirectory(axismeld)` immediately before `add_subdirectory(windowmanager)` in `source/blender/CMakeLists.txt`.

Create `source/blender/axismeld/CMakeLists.txt`:

```cmake
# SPDX-FileCopyrightText: 2026 AxisMeld contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(INC
  PUBLIC .
)
set(INC_SYS
)
set(SRC
  intern/identity.cc
  AXM_identity.hh
)
set(LIB
)

blender_add_lib(bf_axismeld "${SRC}" "${INC}" "${INC_SYS}" "${LIB}")
add_library(bf::axismeld ALIAS bf_axismeld)

if(WITH_GTESTS)
  set(TEST_SRC
    tests/identity_test.cc
  )
  blender_add_test_suite_lib(axismeld "${TEST_SRC}" "${INC}" "${INC_SYS}" "bf::axismeld")
endif()
```

Reconfigure and build:

```powershell
cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build
cmake --build D:\source\AxisMeld-build --target axismeld_identity_test --config Release --parallel 8
```

Expected: build fails because `AXM_identity.hh` and `intern/identity.cc` do not exist.

- [x] **Step 3: Implement the minimal public identity API**

Create `source/blender/axismeld/AXM_identity.hh`:

```cpp
/* SPDX-FileCopyrightText: 2026 AxisMeld contributors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <string>
#include <string_view>

namespace blender::axismeld {

std::string_view product_name();
std::string_view project_version();
std::string version_line(std::string_view blender_version);

}  // namespace blender::axismeld
```

Create `source/blender/axismeld/intern/identity.cc`:

```cpp
/* SPDX-FileCopyrightText: 2026 AxisMeld contributors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "AXM_identity.hh"

namespace blender::axismeld {

std::string_view product_name()
{
  return "AxisMeld";
}

std::string_view project_version()
{
  return "0.1.0-dev";
}

std::string version_line(const std::string_view blender_version)
{
  return std::string(product_name()) + " " + std::string(project_version()) +
         " (based on Blender " + std::string(blender_version) + ")";
}

}  // namespace blender::axismeld
```

- [x] **Step 4: Build and run the identity unit tests**

Run:

```powershell
cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build
cmake --build D:\source\AxisMeld-build --target axismeld_identity_test --config Release --parallel 8
ctest --test-dir D:\source\AxisMeld-build -C Release -R "^axismeld_identity$" --output-on-failure
```

Expected: build exits `0`; CTest reports one matching test and zero failures.

- [x] **Step 5: Commit the isolated identity module**

Run:

```powershell
git add source/blender/CMakeLists.txt source/blender/axismeld
git commit -m "Add AxisMeld product identity module"
```

Expected: one commit containing only the new module and its single registration line.

---

### Task 3: Expose AxisMeld Identity in CLI, Window Titles, and Splash

**Files:**
- Modify: `source/creator/CMakeLists.txt`
- Modify: `source/creator/creator_args.cc`
- Modify: `source/blender/windowmanager/CMakeLists.txt`
- Modify: `source/blender/windowmanager/intern/wm_window.cc`
- Modify: `source/blender/windowmanager/intern/wm_splash_screen.cc`
- Create: `tests/python/axismeld_cli_identity.py`
- Modify: `tests/python/CMakeLists.txt`

**Interfaces:**
- Consumes: `bf::axismeld` and `blender::axismeld::version_line(std::string_view)` from Task 2.
- Produces: a stable first line for `blender.exe --version`, `AxisMeld 0.1.0-dev (based on Blender <version>)`, plus equivalent title and splash labels.

- [x] **Step 1: Write the failing black-box CLI test**

Create `tests/python/axismeld_cli_identity.py`:

```python
# SPDX-FileCopyrightText: 2026 AxisMeld contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import re
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("--blender", required=True)
args = parser.parse_args()

result = subprocess.run(
    [args.blender, "--version"],
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
first_line = result.stdout.splitlines()[0]
assert re.fullmatch(
    r"AxisMeld 0\.1\.0-dev \(based on Blender \d+\.\d+\.\d+(?: [A-Za-z]+)?\)",
    first_line,
), first_line
```

Register it near the general correctness tests in `tests/python/CMakeLists.txt`:

```cmake
add_python_test(
  axismeld_cli_identity
  ${CMAKE_CURRENT_LIST_DIR}/axismeld_cli_identity.py
  --blender ${TEST_BLENDER_EXE}
)
```

Build and run:

```powershell
cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build
cmake --build D:\source\AxisMeld-build --target blender --config Release --parallel 8
ctest --test-dir D:\source\AxisMeld-build -C Release -R "^axismeld_cli_identity$" --output-on-failure
```

Expected: the test fails because the first line still starts with `Blender`.

- [x] **Step 2: Link the identity module into creator and window manager**

In `source/creator/CMakeLists.txt`, add this entry to `LIB`:

```cmake
  PRIVATE bf::axismeld
```

In `source/blender/windowmanager/CMakeLists.txt`, add the same entry to `LIB`:

```cmake
  PRIVATE bf::axismeld
```

Expected: no new include-directory path is added because `bf::axismeld` publishes only its module root.

- [x] **Step 3: Change creator version output without changing Blender build metadata**

Add this include to `source/creator/creator_args.cc`:

```cpp
#include "AXM_identity.hh"
```

In `print_version_full()`, `print_version_short()`, and `print_help()`, replace only the user-visible leading `Blender <version>` line with:

```cpp
const std::string version = axismeld::version_line(BKE_blender_version_string());
printf("%s\n", version.c_str());
```

Use `PRINT("%s\n", version.c_str());` inside `print_help()`. Keep build date, build hash, branch, platform, compiler flags, the `Usage: blender` command, and Blender's internal version macros unchanged. Change the `--version` help text to `Print AxisMeld and Blender versions and exit.`

- [x] **Step 4: Change the main-window and temporary-window titles**

Add `#include "AXM_identity.hh"` to `source/blender/windowmanager/intern/wm_window.cc`.

Replace the temporary-window fallback `return "Blender";` with:

```cpp
return std::string(axismeld::product_name());
```

Replace the final Blender suffix append with:

```cpp
win_title.append(fmt::format(" — {}", axismeld::version_line(BKE_blender_version_string())));
```

Expected title example: `(Unsaved) — AxisMeld 0.1.0-dev (based on Blender 5.3.0 Alpha)`.

- [x] **Step 5: Change the splash text while retaining Blender attribution**

Add `#include "AXM_identity.hh"` to `source/blender/windowmanager/intern/wm_splash_screen.cc`.

Before `wm_block_splash_add_label`, create the combined string and pass it to the existing label helper:

```cpp
const std::string version = axismeld::version_line(BKE_blender_version_string());
wm_block_splash_add_label(block,
                          version.c_str(),
                          splash_width - 8.0 * UI_SCALE_FAC,
                          splash_height - 13.0 * UI_SCALE_FAC);
```

Keep Blender's inherited splash artwork for Phase 0; the combined text prevents the image from being presented as an unmodified official build.

- [x] **Step 6: Run unit and CLI tests**

Run:

```powershell
cmake --build D:\source\AxisMeld-build --target blender axismeld_identity_test --config Release --parallel 8
ctest --test-dir D:\source\AxisMeld-build -C Release -R "^(axismeld_identity|axismeld_cli_identity)$" --output-on-failure
```

Expected: two matching tests, zero failures, and the CLI test observes both AxisMeld and Blender versions.

- [x] **Step 7: Commit the visible product identity**

Run:

```powershell
git add source/creator/CMakeLists.txt source/creator/creator_args.cc source/blender/windowmanager/CMakeLists.txt source/blender/windowmanager/intern/wm_window.cc source/blender/windowmanager/intern/wm_splash_screen.cc tests/python/CMakeLists.txt tests/python/axismeld_cli_identity.py
git commit -m "Show AxisMeld identity in the application"
```

---

### Task 4: Isolate Phase 0 Preferences with a Portable Profile

**Files:**
- Create: `release/datafiles/axismeld/portable/README.txt`
- Modify: `source/creator/CMakeLists.txt`
- Create: `tests/python/axismeld_portable_paths.py`
- Modify: `tests/python/CMakeLists.txt`

**Interfaces:**
- Consumes: Blender's existing `portable` directory lookup in `BKE_appdir_folder_id_ex`.
- Produces: a `portable` directory beside every built and installed Phase 0 executable; `bpy.utils.user_resource('CONFIG')` resolves beneath that directory.

- [x] **Step 1: Write the failing portable-path test**

Create `tests/python/axismeld_portable_paths.py`:

```python
# SPDX-FileCopyrightText: 2026 AxisMeld contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import pathlib
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("--blender", required=True)
args = parser.parse_args()

expression = "import bpy; print('AXISMELD_CONFIG=' + bpy.utils.user_resource('CONFIG'))"
result = subprocess.run(
    [args.blender, "--background", "--factory-startup", "--python-expr", expression],
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
line = next(line for line in result.stdout.splitlines() if line.startswith("AXISMELD_CONFIG="))
config_path = pathlib.Path(line.split("=", 1)[1]).resolve()
expected_root = (pathlib.Path(args.blender).resolve().parent / "portable").resolve()
assert config_path.is_relative_to(expected_root), (config_path, expected_root)
```

Register it in `tests/python/CMakeLists.txt`:

```cmake
add_python_test(
  axismeld_portable_paths
  ${CMAKE_CURRENT_LIST_DIR}/axismeld_portable_paths.py
  --blender ${TEST_BLENDER_EXE}
)
```

Run:

```powershell
cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build
cmake --build D:\source\AxisMeld-build --target blender --config Release --parallel 8
ctest --test-dir D:\source\AxisMeld-build -C Release -R "^axismeld_portable_paths$" --output-on-failure
```

Expected: failure because no `portable` directory exists beside the executable.

- [x] **Step 2: Add the tracked portable-profile notice**

Create `release/datafiles/axismeld/portable/README.txt` with:

```text
AxisMeld Phase 0 portable profile

Preferences, extensions, startup files, and user scripts for this build are stored under this
directory so that testing AxisMeld does not modify an installed Blender profile.

This directory contains user-generated state after AxisMeld runs. Do not commit that state.
```

Add `release/datafiles/axismeld/portable/.gitignore`:

```gitignore
*
!.gitignore
!README.txt
```

- [x] **Step 3: Create the portable directory beside build and install executables**

In the Windows, non-Python-module branch of `source/creator/CMakeLists.txt`, add:

```cmake
add_custom_command(
  TARGET blender
  POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:blender>/portable"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
          "${CMAKE_SOURCE_DIR}/release/datafiles/axismeld/portable/README.txt"
          "$<TARGET_FILE_DIR:blender>/portable/README.txt"
)
install(
  DIRECTORY "${CMAKE_SOURCE_DIR}/release/datafiles/axismeld/portable/"
  DESTINATION "${TARGETDIR_EXE}/portable"
)
```

The condition must be `WIN32 AND NOT WITH_PYTHON_MODULE`; do not create a portable directory for the `bpy` module build.

- [x] **Step 4: Build and verify isolation**

Run:

```powershell
cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build
cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8
ctest --test-dir D:\source\AxisMeld-build -C Release -R "^axismeld_portable_paths$" --output-on-failure
```

Expected: one matching test, zero failures, and both the build executable directory and `D:\source\AxisMeld-build\install` contain `portable\README.txt`.

- [x] **Step 5: Commit portable profile isolation**

Run:

```powershell
git add release/datafiles/axismeld/portable source/creator/CMakeLists.txt tests/python/CMakeLists.txt tests/python/axismeld_portable_paths.py
git commit -m "Isolate AxisMeld development preferences"
```

---

### Task 5: Apply Windows Product Metadata Without Renaming the Binary

**Files:**
- Modify: `CMakeLists.txt`
- Modify: `release/windows/icons/winblender.rc`
- Create: `tools/axismeld/verify_windows_build.ps1`

**Interfaces:**
- Consumes: installed `blender.exe`, CLI identity from Task 3, and portable directory from Task 4.
- Produces: Windows AppUserModel ID `axismeld.<major>.<minor>`, friendly name `AxisMeld <major>.<minor>`, AxisMeld file metadata, and an independent acceptance command.

- [x] **Step 1: Write the build verifier before changing metadata**

Create `tools/axismeld/verify_windows_build.ps1`:

```powershell
param(
  [Parameter(Mandatory = $true)]
  [string]$InstallDir
)

$ErrorActionPreference = 'Stop'
$exe = Join-Path $InstallDir 'blender.exe'
if (-not (Test-Path -LiteralPath $exe)) {
  throw "Missing executable: $exe"
}

$versionOutput = @(& $exe --version 2>&1)
if ($LASTEXITCODE -ne 0) {
  throw "--version failed with exit code $LASTEXITCODE"
}
$firstLine = [string]$versionOutput[0]
if ($firstLine -notmatch '^AxisMeld 0\.1\.0-dev \(based on Blender \d+\.\d+\.\d+( [A-Za-z]+)?\)$') {
  throw "Unexpected version line: $firstLine"
}

$versionInfo = (Get-Item -LiteralPath $exe).VersionInfo
if ($versionInfo.ProductName -ne 'AxisMeld') {
  throw "Unexpected ProductName: $($versionInfo.ProductName)"
}
if ($versionInfo.CompanyName -ne 'AxisMeld Project') {
  throw "Unexpected CompanyName: $($versionInfo.CompanyName)"
}

$portableReadme = Join-Path $InstallDir 'portable\README.txt'
if (-not (Test-Path -LiteralPath $portableReadme)) {
  throw "Missing portable profile marker: $portableReadme"
}

[pscustomobject]@{
  Result = 'PASS'
  Executable = $exe
  Version = $firstLine
  ProductName = $versionInfo.ProductName
  CompanyName = $versionInfo.CompanyName
  PortableProfile = $portableReadme
}
```

Run it against the Task 4 install:

```powershell
pwsh -NoProfile -File D:\source\AxisMeld\tools\axismeld\verify_windows_build.ps1 -InstallDir D:\source\AxisMeld-build\install
```

Expected: failure on `ProductName`, which still reports `Blender`.

- [x] **Step 2: Change the Windows AppUserModel identity**

In the Windows definition block in root `CMakeLists.txt`, change only the string values:

```cmake
-DBLENDER_WIN_APPID="axismeld.${BLENDER_VERSION_MAJOR}.${BLENDER_VERSION_MINOR}"
-DBLENDER_WIN_APPID_FRIENDLY_NAME="AxisMeld ${BLENDER_VERSION_MAJOR}.${BLENDER_VERSION_MINOR}"
```

Keep the existing macro names so downstream Blender modules require no additional edits.

- [x] **Step 3: Change Windows executable metadata**

In `release/windows/icons/winblender.rc`, set:

```rc
VALUE "CompanyName", "AxisMeld Project"
VALUE "FileDescription", "AxisMeld — Maya-style workflow built on Blender"
VALUE "LegalCopyright", "GPLv3; Blender Authors and AxisMeld contributors"
VALUE "OriginalFilename", "blender.exe"
VALUE "ProductName", "AxisMeld"
```

Keep `OriginalFilename` as `blender.exe`, retain the inherited icons for Phase 0, and do not remove Blender copyright notices elsewhere.

- [x] **Step 4: Rebuild and run the independent verifier**

Run:

```powershell
cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build
cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8
pwsh -NoProfile -File D:\source\AxisMeld\tools\axismeld\verify_windows_build.ps1 -InstallDir D:\source\AxisMeld-build\install
```

Expected: the verifier prints one object with `Result : PASS`, the combined AxisMeld/Blender version, AxisMeld product metadata, and the portable marker path.

- [x] **Step 5: Run the focused automated suite**

Run:

```powershell
ctest --test-dir D:\source\AxisMeld-build -C Release -R "^(axismeld_identity|axismeld_cli_identity|axismeld_portable_paths)$" --output-on-failure
```

Expected: three matching tests and zero failures.

- [x] **Step 6: Commit Windows identity and verification**

Run:

```powershell
git add CMakeLists.txt release/windows/icons/winblender.rc tools/axismeld/verify_windows_build.ps1
git commit -m "Brand and verify the AxisMeld Windows build"
```

---

### Task 6: Document Reproducible Builds and Upstream Merges

**Files:**
- Create: `docs/build/windows.md`
- Create: `docs/build/upstream-update.md`

**Interfaces:**
- Consumes: exact build and verification commands from Tasks 1–5.
- Produces: maintainer procedures that another worker can execute without relying on conversation history.

- [x] **Step 1: Write the Windows build guide**

Create `docs/build/windows.md` with these sections and exact commands:

```markdown
# Building AxisMeld on Windows

## Requirements

- Windows 11 x64
- Git for Windows
- CMake in `PATH`
- Visual Studio 2022 Build Tools with `Microsoft.VisualStudio.Workload.VCTools`
- At least 40 GB free on `D:` before downloading Blender libraries and build outputs

## Prepare

    git clone https://github.com/AngelHob/AxisMeld.git D:\source\AxisMeld
    cd /d D:\source\AxisMeld
    git switch axismeld/integration
    make.bat update

## Configure and build

    cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build -G "Visual Studio 17 2022" -A x64 -C D:\source\AxisMeld\build_files\cmake\config\blender_developer.cmake -DWITH_GTESTS=ON -DWITH_TESTS_SINGLE_BINARY=OFF -DCMAKE_INSTALL_PREFIX=D:\source\AxisMeld-build\install
    cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8

## Verify

    pwsh -NoProfile -File D:\source\AxisMeld\tools\axismeld\verify_windows_build.ps1 -InstallDir D:\source\AxisMeld-build\install
    ctest --test-dir D:\source\AxisMeld-build -C Release -R "^(axismeld_identity|axismeld_cli_identity|axismeld_portable_paths)$" --output-on-failure

The Phase 0 executable remains named `blender.exe` for compatibility. Its window, version output,
Windows metadata, and portable profile identify it as AxisMeld. Do not distribute a build until both
verification commands pass.
```

- [x] **Step 2: Write the upstream update guide**

Create `docs/build/upstream-update.md`:

```markdown
# Updating AxisMeld from Blender Upstream

1. Start from a clean `axismeld/integration` branch.
2. Fetch without pushing to Blender:

       git fetch upstream main

3. Create a dated integration branch:

       $mergeDate = Get-Date -Format yyyy-MM-dd
       git switch -c "integration/blender-main-$mergeDate" axismeld/integration

4. Merge without rewriting Blender history:

       git merge --no-ff upstream/main

5. Resolve only direct conflicts. Do not reformat unrelated Blender files.
6. Run the Windows installed-build verifier and all three focused tests.
7. Record the upstream commit in the merge commit message and push the integration branch to `origin`.
8. Merge the validated integration branch into `axismeld/integration` with a merge commit.

`upstream` must keep push URL `DISABLED`. Never force-push `axismeld/integration` or
`axismeld/stable`. Run the date command in the Asia/Shanghai time zone used by the project.
```

- [x] **Step 3: Verify that documentation matches executable commands**

Run:

```powershell
rg -n "AxisMeld-build|verify_windows_build|axismeld_identity|axismeld_cli_identity|axismeld_portable_paths" docs/build tools/axismeld
git diff --check
```

Expected: both documents use the same source, build, install, verifier, and test names; `git diff --check` emits no errors.

- [x] **Step 4: Commit the maintainer procedures**

Run:

```powershell
git add docs/build/windows.md docs/build/upstream-update.md
git commit -m "Document AxisMeld build and upstream update workflow"
```

---

### Task 7: Phase 0 Acceptance and Publication

**Files:**
- Modify only if evidence differs: `README.md`
- Update checklist status in this plan as each task completes.

**Interfaces:**
- Consumes: all Phase 0 commits and the installed Release build.
- Produces: a verified `axismeld/integration` commit published to GitHub and ready for the separate Maya 2026 input-system plan.

- [x] **Step 1: Run the complete focused verification from a clean shell**

Run:

```powershell
cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8
ctest --test-dir D:\source\AxisMeld-build -C Release -R "^(axismeld_identity|axismeld_cli_identity|axismeld_portable_paths)$" --output-on-failure
pwsh -NoProfile -File D:\source\AxisMeld\tools\axismeld\verify_windows_build.ps1 -InstallDir D:\source\AxisMeld-build\install
git status --short --branch
```

Expected: build exit code `0`; three tests, zero failures; verifier `PASS`; clean `axismeld/integration` worktree.

- [x] **Step 2: Verify upstream ancestry and the protected remote direction**

Run:

```powershell
git merge-base --is-ancestor upstream/main HEAD
git remote get-url origin
git remote get-url upstream
git remote get-url --push upstream
```

Expected: the ancestry command exits `0`; URLs are AxisMeld GitHub for `origin`, Blender Projects for upstream fetch, and `DISABLED` for upstream push.

- [ ] **Step 3: Launch the installed UI once**

Run:

```powershell
Start-Process -FilePath 'D:\source\AxisMeld-build\install\blender.exe'
```

Verify visibly that the main window and splash show `AxisMeld 0.1.0-dev` together with the Blender version. Close the application normally and confirm that new preferences were written only under `D:\source\AxisMeld-build\install\portable`.

- [ ] **Step 4: Push the validated branch**

Run:

```powershell
git push origin axismeld/integration
git ls-remote origin refs/heads/axismeld/integration
git rev-parse HEAD
```

Expected: push succeeds and the two printed commit hashes are identical.

- [ ] **Step 5: Record the Phase 0 boundary**

Add this section to `README.md` only after Steps 1–4 pass:

```markdown
## Phase 0 status

AxisMeld `0.1.0-dev` has a verified Windows 11 x64 Release build based on Blender commit
`18d84097b4f859582afdec57eece2ae880371adc`. Phase 0 retains the compatibility filename
`blender.exe`, identifies the running product as AxisMeld, and stores development preferences under
the adjacent `portable` directory. The three focused identity and isolation tests pass.

Maya-style shortcuts, hotbox behavior, viewport interaction, modeling additions, and the UV overhaul
remain planned work and are not part of the Phase 0 build.
```

Run:

```powershell
git add README.md docs/superpowers/plans/2026-09-09-phase-0-build-identity.md
git commit -m "Record verified AxisMeld Phase 0 baseline"
git push origin axismeld/integration
```

Expected: GitHub default branch shows only verified Phase 0 capability and still states the non-profit, AI-authored, Blender-based project boundaries.
