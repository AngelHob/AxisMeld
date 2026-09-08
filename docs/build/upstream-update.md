# Updating AxisMeld from Blender Upstream

This procedure merges Blender changes into AxisMeld without rewriting either
project's published history. Run all PowerShell commands from the maintained
checkout at `D:\source\AxisMeld`, not from a temporary worktree.

## Prepare the integration branch

Start with a clean `axismeld/integration` and keep Blender's upstream remote
read-only. The date is explicitly calculated in the project's Asia/Shanghai
time zone.

```powershell
Set-Location D:\source\AxisMeld
git status --short
git fetch origin axismeld/integration
git switch axismeld/integration
git pull --ff-only origin axismeld/integration

git remote add upstream https://projects.blender.org/blender/blender.git
git remote set-url --push upstream DISABLED
git fetch upstream main

$mergeDate = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow, 'China Standard Time').ToString('yyyy-MM-dd')
$upstreamCommit = git rev-parse upstream/main
git switch -c "integration/blender-main-$mergeDate" axismeld/integration
```

If `upstream` already exists, omit the `git remote add` line but still run
`git remote set-url --push upstream DISABLED`. Confirm `git status --short`
prints nothing before merging.

## Merge and recover Blender dependencies

Create a merge commit and include the exact Blender upstream commit in its
message. Resolve only direct conflicts; do not reformat unrelated Blender
files.

```powershell
git merge --no-ff upstream/main -m "Merge Blender upstream $upstreamCommit into AxisMeld"
git lfs fetch upstream HEAD
git lfs checkout
cmd /c make.bat update 2026b
```

After every upstream merge, fetch and check out main-repository LFS objects
from `upstream` for the new `HEAD` before the dependency update. Do not fetch
them from `origin`, because an AxisMeld GitHub fork does not host Blender's LFS
objects.

## Build and verify the merged result

Use the current verified Windows baseline. These commands preserve the standard
build and install locations and do not assume the shell's `PATH` has refreshed.

```powershell
$cmake = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ctest = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'

& $cmake -S D:\source\AxisMeld -B D:\source\AxisMeld-build -G 'Visual Studio 18 2026' -A x64 -C D:\source\AxisMeld\build_files\cmake\config\blender_developer.cmake -DWITH_GTESTS=ON -DWITH_TESTS_SINGLE_BINARY=OFF -DCMAKE_INSTALL_PREFIX=D:\source\AxisMeld-build\install
& $cmake --build D:\source\AxisMeld-build --target INSTALL --config Release --parallel 8
pwsh -NoProfile -File D:\source\AxisMeld\tools\axismeld\verify_windows_build.ps1 -InstallDir D:\source\AxisMeld-build\install
& $ctest --test-dir D:\source\AxisMeld-build -C Release -R '^(axismeld_identity|axismeld_cli_identity|axismeld_portable_paths)$' --output-on-failure
```

## Publish without rewriting history

Record the tested upstream revision in the merge commit (`$upstreamCommit`),
then publish the dated branch and integrate it through another merge commit:

```powershell
git push origin "integration/blender-main-$mergeDate"
git switch axismeld/integration
git merge --no-ff "integration/blender-main-$mergeDate" -m "Merge validated Blender upstream $upstreamCommit"
git push origin axismeld/integration
```

Never use `--force` when pushing `axismeld/integration` or `axismeld/stable`.
Do not push to `upstream`; its push URL must remain `DISABLED`.
