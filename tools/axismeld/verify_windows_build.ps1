# SPDX-FileCopyrightText: 2026 AxisMeld contributors
# SPDX-License-Identifier: GPL-2.0-or-later

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
