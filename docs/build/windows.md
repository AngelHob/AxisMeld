# Building AxisMeld on Windows

This procedure uses the verified Phase 0 Windows baseline: Visual Studio Build
Tools 2026 (18.8), its bundled CMake 4.3.1, the `2026b` Blender dependency
wrapper, and the `Visual Studio 18 2026` generator. Earlier toolchain plans
are superseded by this verified baseline.

## Requirements

- Windows 11 x64.
- Git for Windows and Git LFS.
- Visual Studio Build Tools 2026 (18.8) with
  `Microsoft.VisualStudio.Workload.VCTools`.
- At least 40 GB free on `D:` before downloading Blender libraries and build
  outputs.

The commands below use the maintained checkout at `D:\source\AxisMeld`, an
out-of-tree build at `D:\source\AxisMeld-build`, and an install directory at
`D:\source\AxisMeld-build\install`. Do not substitute a temporary worktree
path for those locations.

## Clone and prepare

GitHub forks do not store Blender's LFS objects. In PowerShell, skip LFS smudge
while cloning the required integration branch, then obtain the objects from
Blender upstream. The `finally` block removes the temporary setting after the
upstream checkout and also removes it if a preparation command fails.

```powershell
try {
  $env:GIT_LFS_SKIP_SMUDGE = '1'
  git clone --branch axismeld/integration https://github.com/AngelHob/AxisMeld.git D:\source\AxisMeld

  Set-Location D:\source\AxisMeld
  git remote add upstream https://projects.blender.org/blender/blender.git
  git remote set-url --push upstream DISABLED
  git lfs fetch upstream HEAD
  git lfs checkout
}
finally {
  Remove-Item Env:GIT_LFS_SKIP_SMUDGE -ErrorAction SilentlyContinue
}

cmd /c make.bat update 2026b
```

If `upstream` already exists, do not add it again. Check and enforce its safe
push configuration before continuing:

```powershell
git remote -v
git remote set-url --push upstream DISABLED
```

## Configure and build

Use the bundled CMake and CTest explicitly; this does not rely on a newly
installed Visual Studio path already being present in the current shell.

```powershell
$cmake = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ctest = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'

& $cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build -G 'Visual Studio 18 2026' -A x64 -C D:\source\AxisMeld\build_files\cmake\config\blender_developer.cmake -DWITH_GTESTS=ON -DWITH_TESTS_SINGLE_BINARY=OFF -DCMAKE_INSTALL_PREFIX=D:\source\AxisMeld-build\install
& $cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8
```

A successful configure creates `D:\source\AxisMeld-build\Blender.slnx`.

## Verify

Run the installed-build verifier and all three focused tests before distributing
the build:

```powershell
$ctest = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'
pwsh -NoProfile -File D:\source\AxisMeld\tools\axismeld\verify_windows_build.ps1 -InstallDir D:\source\AxisMeld-build\install
& $ctest --test-dir D:\source\AxisMeld-build -C Release -R '^(axismeld_identity|axismeld_cli_identity|axismeld_portable_paths)$' --output-on-failure
```

The Phase 0 executable remains named `blender.exe` for compatibility. Its
window, version output, Windows metadata, and portable profile identify it as
AxisMeld. Do not distribute a build until both verification commands pass.
