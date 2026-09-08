# SPDX-FileCopyrightText: 2026 AxisMeld contributors
# SPDX-License-Identifier: GPL-2.0-or-later

param(
  [Parameter(Mandatory = $true)]
  [string]$InstallDir,

  [string]$SourceDir = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
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
$versionPattern = '^AxisMeld 0\.1\.0-dev \(based on Blender (?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)(?: (?:Alpha|Beta|Release Candidate|LTS))?\)$'
$validVersionLines = @(
  'AxisMeld 0.1.0-dev (based on Blender 5.3.0)',
  'AxisMeld 0.1.0-dev (based on Blender 5.3.0 Alpha)',
  'AxisMeld 0.1.0-dev (based on Blender 5.3.0 Beta)',
  'AxisMeld 0.1.0-dev (based on Blender 5.3.0 Release Candidate)',
  'AxisMeld 0.1.0-dev (based on Blender 4.5.1 LTS)'
)
$invalidVersionLines = @(
  'AxisMeld 0.1.0-dev (based on Blender 5.3)',
  'AxisMeld 0.1.0-dev (based on Blender 5.3.0 Preview)',
  'AxisMeld 0.1.0-dev (based on Blender 5.3.0 Release)',
  'AxisMeld 0.1.0-dev (based on Blender 5.3.0 LTS extra)'
)
foreach ($line in $validVersionLines) {
  if ($line -notmatch $versionPattern) {
    throw "Version parser rejected supported Blender lifecycle: $line"
  }
}
foreach ($line in $invalidVersionLines) {
  if ($line -match $versionPattern) {
    throw "Version parser accepted malformed Blender lifecycle: $line"
  }
}

$firstLine = [string]$versionOutput[0]
if ($firstLine -notmatch $versionPattern) {
  throw "Unexpected version line: $firstLine"
}

$versionInfo = (Get-Item -LiteralPath $exe).VersionInfo
$expectedVersionInfo = [ordered]@{
  CompanyName = 'AxisMeld Project'
  FileDescription = 'AxisMeld - Maya-style workflow built on Blender'
  InternalName = 'blender.exe'
  LegalCopyright = 'GPLv3; Blender Authors and AxisMeld contributors'
  OriginalFilename = 'blender.exe'
  ProductName = 'AxisMeld'
}
foreach ($field in $expectedVersionInfo.Keys) {
  if ($versionInfo.$field -ne $expectedVersionInfo[$field]) {
    throw "Unexpected ${field}: $($versionInfo.$field)"
  }
}

$expectedVersion = [Version]::new(
  [int]$Matches.major,
  [int]$Matches.minor,
  [int]$Matches.patch,
  0
)
$appUserModelId = "axismeld.$($expectedVersion.Major).$($expectedVersion.Minor)"
if ($versionInfo.FileVersionRaw -ne $expectedVersion) {
  throw "Unexpected FileVersion: $($versionInfo.FileVersionRaw)"
}
if ($versionInfo.ProductVersionRaw -ne $expectedVersion) {
  throw "Unexpected ProductVersion: $($versionInfo.ProductVersionRaw)"
}

$cmakeSource = Get-Content -Raw -LiteralPath (Join-Path $SourceDir 'CMakeLists.txt')
$expectedAppId = '-DBLENDER_WIN_APPID="axismeld.${BLENDER_VERSION_MAJOR}.${BLENDER_VERSION_MINOR}"'
$expectedFriendlyName = '-DBLENDER_WIN_APPID_FRIENDLY_NAME="AxisMeld ${BLENDER_VERSION_MAJOR}.${BLENDER_VERSION_MINOR}"'
if (-not $cmakeSource.Contains($expectedAppId)) {
  throw "Missing AxisMeld AppUserModel ID definition: $expectedAppId"
}
if (-not $cmakeSource.Contains($expectedFriendlyName)) {
  throw "Missing AxisMeld AppUserModel friendly-name definition: $expectedFriendlyName"
}

$resourceSource = Get-Content -Raw -LiteralPath (
  Join-Path $SourceDir 'release\windows\icons\winblender.rc'
)
foreach ($field in $expectedVersionInfo.Keys) {
  $expectedResource = 'VALUE "{0}", "{1}"' -f $field, $expectedVersionInfo[$field]
  if (-not $resourceSource.Contains($expectedResource)) {
    throw "Missing Windows resource definition: $expectedResource"
  }
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
  FileDescription = $versionInfo.FileDescription
  AppUserModelId = $appUserModelId
  PortableProfile = $portableReadme
}
