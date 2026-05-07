param(
  [string]$RepoRoot = (Resolve-Path ".").Path,
  [string]$Python = "python",
  [string]$ReleaseDir = "code_Release_BudsFCT_R",
  [string]$Version = "",
  [switch]$SkipPyInstaller,
  [string]$PrebuiltExe = ""
)

$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$Path) {
  if (!(Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function Sync-Dir([string]$Source, [string]$Dest) {
  Ensure-Dir $Dest
  # Exclude build outputs and VCS metadata to keep release clean/small
  $excludeDirs = @(
    ".git",
    ".github",
    "__pycache__",
    "build",
    "dist",
    "OSENSTester"
  )
  $xd = @()
  foreach ($d in $excludeDirs) { $xd += @("/XD", (Join-Path $Source $d)) }

  robocopy $Source $Dest /MIR /R:2 /W:2 /NFL /NDL /NJH /NJS /NP @xd | Out-Null
  if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed syncing '$Source' -> '$Dest' (exit=$LASTEXITCODE)"
  }
}

$repo = (Resolve-Path $RepoRoot).Path
$common = Join-Path $repo "CommonPlatform"
$engine = Join-Path $repo "engine"
$release = Join-Path $repo $ReleaseDir
$sitePkgs = Join-Path $release "site-packages"

if (!(Test-Path -LiteralPath $common)) { throw "Missing CommonPlatform at $common" }
if (!(Test-Path -LiteralPath $engine)) { throw "Missing engine at $engine" }
if (!(Test-Path -LiteralPath $release)) { throw "Missing release dir at $release" }

if ([string]::IsNullOrWhiteSpace($Version)) {
  $tag = $env:GITHUB_REF_NAME
  if (![string]::IsNullOrWhiteSpace($tag)) {
    $Version = $tag.TrimStart("v")
  }
}
if ([string]::IsNullOrWhiteSpace($Version)) {
  $Version = "0.0.0-dev"
}

Write-Host "RepoRoot: $repo"
Write-Host "ReleaseDir: $release"
Write-Host "Version: $Version"
if ($SkipPyInstaller) { Write-Host "Mode: SkipPyInstaller (prebuilt UI exe + sign/package only)" }

#
# Ensure release site-packages includes runtime deps (bundled to C:\site-packages)
#
Ensure-Dir $sitePkgs
& $Python -m pip install --upgrade pip | Out-Null
& $Python -m pip install --target $sitePkgs --upgrade "pywinpty" "pyzmq"

#
# Step 1: Build OSENSTester (PyInstaller) or package prebuilt exe
#
Push-Location $common
try {
  if (Test-Path -LiteralPath ".\dist") { Remove-Item -Recurse -Force ".\dist" }
  if (Test-Path -LiteralPath ".\build") { Remove-Item -Recurse -Force ".\build" }
  if (Test-Path -LiteralPath ".\OSENSTester") { Remove-Item -Recurse -Force ".\OSENSTester" }

  if (-not $SkipPyInstaller) {
    & $Python -m pip install -r ".\requirements-build.txt"

    # Prefer venv site-packages first so pip-installed pyzmq wins over any vendored
    # incomplete `zmq` tree under release site-packages (which would shadow imports).
    $venvSite = & $Python -c "import site; print(site.getsitepackages()[0])"
    if (Test-Path -LiteralPath $sitePkgs) {
      if ($env:PYTHONPATH) {
        $env:PYTHONPATH = "$venvSite;$sitePkgs;$env:PYTHONPATH"
      }
      else {
        $env:PYTHONPATH = "$venvSite;$sitePkgs"
      }
      Write-Host "PYTHONPATH: venv=`"$venvSite`" then release=`"$sitePkgs`""
    }
    else {
      $env:PYTHONPATH = "$venvSite;$env:PYTHONPATH".TrimEnd(';')
    }

    & $Python -m PyInstaller ".\src\spec\Tester_windows.spec"
  }
  else {
    $srcExe = $PrebuiltExe
    if ([string]::IsNullOrWhiteSpace($srcExe)) {
      $candidates = @(
        (Join-Path $common "UI.exe"),
        (Join-Path $common "OSENSTester.exe"),
        (Join-Path $release "Overlay\OSENSTester.exe"),
        (Join-Path $release "Overlay\CommonPlatform\UI.exe")
      )
      foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) {
          $srcExe = $c
          break
        }
      }
    }
    if ([string]::IsNullOrWhiteSpace($srcExe) -or !(Test-Path -LiteralPath $srcExe)) {
      throw "SkipPyInstaller: missing prebuilt exe. Commit one of: CommonPlatform/UI.exe, Overlay/OSENSTester.exe under ReleaseDir, or pass -PrebuiltExe"
    }
    Write-Host "Using prebuilt exe: $srcExe"
    Ensure-Dir ".\dist"
    Copy-Item -LiteralPath $srcExe ".\dist\OSENSTester.exe" -Force
  }

  Ensure-Dir ".\dist\configure"
  Ensure-Dir ".\dist\profile"
  Ensure-Dir ".\dist\engine"

  Copy-Item ".\src\configure\*.json" ".\dist\configure\" -Force
  Copy-Item (Join-Path $engine "*") ".\dist\engine\" -Recurse -Force
  Copy-Item (Join-Path $engine "profile\*.csv") ".\dist\profile\" -Force -ErrorAction SilentlyContinue

  & ".\src\signer\signer_win.exe" -d ".\dist"
  if (-not $?) { throw "signer_win.exe failed signing dist (exit=$LASTEXITCODE)" }

  Move-Item ".\dist" ".\OSENSTester"
  Copy-Item ".\killport.bat" ".\OSENSTester\" -Force
  Copy-Item ".\__init__.py" ".\OSENSTester\" -Force
}
finally {
  Pop-Location
}

#
# Step 1 output: sync OSENSTester into release dir
#
$releaseOsens = Join-Path $release "OSENSTester"
if (Test-Path -LiteralPath $releaseOsens) { Remove-Item -Recurse -Force $releaseOsens }
Copy-Item (Join-Path $common "OSENSTester") $releaseOsens -Recurse -Force
if (Test-Path -LiteralPath (Join-Path $common "OSENSTester")) {
  Remove-Item -Recurse -Force (Join-Path $common "OSENSTester")
}

#
# Step 2: Sync Overlay sources into release dir Overlay/
#
$releaseOverlay = Join-Path $release "Overlay"
Ensure-Dir $releaseOverlay
Sync-Dir $common (Join-Path $releaseOverlay "CommonPlatform")
Sync-Dir $engine (Join-Path $releaseOverlay "engine")

#
# Step 2: Build installer via Inno Setup (expects iscc.exe in PATH)
#
Push-Location $release
try {
  Ensure-Dir ".\Output"
  & iscc.exe "/DMyAppVersion=$Version" ".\CodeExample_code_testplan.iss"

  # Sign installer output so Windows shows trusted (green lock).
  $signer = Join-Path $common "src\\signer\\signer_win.exe"
  if (Test-Path -LiteralPath $signer) {
    & $signer -d ".\\Output"
    if (-not $?) { throw "signer_win.exe failed signing installer Output (exit=$LASTEXITCODE)" }
  }
  else {
    Write-Warning "signer_win.exe not found at $signer (skipping installer signing)"
  }
}
finally {
  Pop-Location
}

Write-Host "Done. Outputs:"
Write-Host " - $release\\Output\\SetupBudsFCT_R_Code_$Version.exe (or similar)"
Write-Host " - $release (folder to zip for code release)"
