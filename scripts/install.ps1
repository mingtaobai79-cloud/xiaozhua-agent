# xiaozhua-agent one-line installer / upgrader for Windows PowerShell 5.1+
#
#   irm https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.ps1 | iex
#
#   with arguments (iex cannot pass params, so build a scriptblock):
#   & ([scriptblock]::Create((irm .../scripts/install.ps1))) -Hosts hermes
#
# NOTE: this file is deliberately ASCII-only and has NO UTF-8 BOM.
#   * A leading BOM breaks [CmdletBinding()] when the script arrives as a string via irm|iex
#     ("unexpected attribute CmdletBinding", verified on PS 5.1).
#   * Non-ASCII text without a BOM is decoded with the ANSI code page by PS 5.1,
#     which can produce stray punctuation and parse errors.
#   Chinese docs live in INSTALL.md; this script stays ASCII so every decode path works.
#
# Environment overrides:
#   XIAOZHUA_HOME   install root   (default %USERPROFILE%\.xiaozhua)
#   XIAOZHUA_HOSTS  hosts, comma separated or all (default all)
#   XIAOZHUA_REPO   git remote
#   XIAOZHUA_BRANCH branch (default main)

[CmdletBinding()]
param(
  [string]$Hosts  = $(if ($env:XIAOZHUA_HOSTS)  { $env:XIAOZHUA_HOSTS }  else { 'all' }),
  [string]$Root   = $(if ($env:XIAOZHUA_HOME)   { $env:XIAOZHUA_HOME }   else { Join-Path $env:USERPROFILE '.xiaozhua' }),
  [string]$Branch = $(if ($env:XIAOZHUA_BRANCH) { $env:XIAOZHUA_BRANCH } else { 'main' }),
  [string]$Repo   = $(if ($env:XIAOZHUA_REPO)   { $env:XIAOZHUA_REPO }   else { 'https://github.com/mingtaobai79-cloud/xiaozhua-agent.git' }),
  [switch]$NoPath
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

function Ok($m)   { Write-Host "[ok]   $m" -ForegroundColor Green }
function Info($m) { Write-Host "[..]   $m" -ForegroundColor DarkGray }
function Die($m)  { Write-Host "[fail] $m" -ForegroundColor Red; exit 1 }

$Src  = Join-Path $Root 'src'
$Venv = Join-Path $Root 'venv'
$Pkg  = Join-Path $Root 'pkg'
$Bin  = Join-Path $Root 'bin'

Write-Host ""
Write-Host "xiaozhua-agent installer - Windows $([Environment]::OSVersion.Version)"
Write-Host ""

# ---- 1. Python >= 3.12 (prefer the py launcher, which can pick a version)
$pyExe = $null
$candidates = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
  $candidates += ,@('py', @('-3.13'))
  $candidates += ,@('py', @('-3.12'))
  $candidates += ,@('py', @('-3'))
}
foreach ($c in @('python', 'python3')) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { $candidates += ,@($c, @()) }
}
foreach ($c in $candidates) {
  $exe = $c[0]
  $pre = @($c[1])
  try {
    $ver = & $exe @pre -c "import sys;print('%d.%d.%d'%sys.version_info[:3])" 2>$null
    if ($LASTEXITCODE -eq 0 -and $ver) {
      $parts = "$ver".Split('.')
      if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 12) {
        $pyExe = @($exe) + $pre
        Ok "Python $ver  ($exe $($pre -join ' '))"
        break
      }
    }
  } catch { }
}
if (-not $pyExe) {
  Die "Python 3.12+ is required. Install with: winget install Python.Python.3.12 (or python.org), reopen the terminal, then rerun."
}

# ---- 2. git + code
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Die "git is required. Install with: winget install Git.Git then reopen the terminal."
}
New-Item -ItemType Directory -Force -Path $Root | Out-Null
if (Test-Path (Join-Path $Src '.git')) {
  Info "updating code at $Src"
  git -C $Src fetch --prune --quiet origin
  if ($LASTEXITCODE -ne 0) { Die "git fetch failed (network or credentials)" }
  git -C $Src checkout --quiet $Branch
  git -C $Src merge --ff-only "origin/$Branch" --quiet
  if ($LASTEXITCODE -ne 0) { Die "local commits diverge from origin/$Branch; resolve manually in $Src" }
} else {
  Info "cloning into $Src"
  if (Test-Path $Src) { Remove-Item -Recurse -Force $Src }
  git clone --quiet --branch $Branch $Repo $Src
  if ($LASTEXITCODE -ne 0) { Die "git clone failed: $Repo" }
}
$sha = (git -C $Src rev-parse --short HEAD).Trim()
$ver = if (Test-Path (Join-Path $Src 'VERSION')) { (Get-Content (Join-Path $Src 'VERSION') -Raw).Trim() } else { '?' }
Ok "code $sha  version $ver"

# ---- 3. venv + deps
Info "preparing venv at $Venv"
$venvPy = Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path $venvPy)) {
  $pyArgs = @($pyExe | Select-Object -Skip 1)
  & $pyExe[0] @pyArgs -m venv $Venv
  if ($LASTEXITCODE -ne 0) { Die "venv creation failed: $Venv" }
}
if (-not (Test-Path $venvPy)) { Die "venv python not found: $venvPy" }

# Do NOT run "pip install --upgrade pip": on Windows it renames pip/ to ~ip/ before installing
# the new version, and a failure there leaves a venv with no pip at all. Self-heal only.
& $venvPy -m pip --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  Info "pip missing, repairing with ensurepip"
  & $venvPy -m ensurepip --upgrade 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { Die "pip repair failed: run $venvPy -m ensurepip --upgrade manually" }
}
& $venvPy -m pip install --quiet -e $Src
if ($LASTEXITCODE -ne 0) {
  Info "editable install failed, falling back to plain deps"
  & $venvPy -m pip install --quiet "pyyaml>=6.0" "websocket-client>=1.6"
  if ($LASTEXITCODE -ne 0) { Die "dependency install failed" }
}
Ok "dependencies ready"

# ---- 4. host configs (also records state.json for `xiaozhua update`)
Info "generating host configs -> $Pkg (host=$Hosts)"
& $venvPy (Join-Path $Src 'installer\selfupdate.py') install --host $Hosts --target $Pkg --write --force | Out-Null
if ($LASTEXITCODE -ne 0) { Die "host config generation failed" }
Ok "host configs written to $Pkg"

# ---- 5. xiaozhua command (cmd shim + ps1 shim, no execution-policy dependency)
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
$cmdShim = Join-Path $Bin 'xiaozhua.cmd'
@"
@echo off
"$venvPy" "$Src\installer\selfupdate.py" %*
"@ | Set-Content -Path $cmdShim -Encoding ASCII
$psShim = Join-Path $Bin 'xiaozhua.ps1'
@"
& "$venvPy" "$Src\installer\selfupdate.py" @args
exit `$LASTEXITCODE
"@ | Set-Content -Path $psShim -Encoding ASCII
Ok "command $cmdShim"

# ---- 6. PATH (user scope, idempotent)
if (-not $NoPath) {
  $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
  if ($null -eq $userPath) { $userPath = '' }
  $entries = $userPath.Split(';') | Where-Object { $_ }
  if ($entries -notcontains $Bin) {
    $newPath = (@($entries) + $Bin) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    Info "added $Bin to the user PATH (open a new terminal to pick it up)"
  }
}

# ---- 7. self-check: really start the MCP server once and count tools
Info "self-check (starting the MCP server once)"
$l1 = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"install","version":"1"}}}'
$l2 = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
$server = Join-Path $Src 'adapters\mcp\server.py'
$out = @($l1, $l2) | & $venvPy $server 2>$null
$tools = 0
foreach ($line in $out) {
  $t = "$line".Trim()
  if (-not $t.StartsWith('{')) { continue }
  try { $o = $t | ConvertFrom-Json } catch { continue }
  if ($o.result -and $o.result.PSObject.Properties.Name -contains 'tools') {
    $tools = @($o.result.tools).Count
  }
}
if ($tools -le 0) { Die "self-check failed: the MCP server reported no tools (run: $venvPy $server)" }
Ok "self-check tools=$tools"

Write-Host ""
Write-Host "installed $ver" -ForegroundColor Green
Write-Host ""
if (Get-Command xiaozhua -ErrorAction SilentlyContinue) {
  Write-Host "xiaozhua is on PATH. Try: xiaozhua doctor"
} else {
  Write-Host "For this window only: `$env:Path = `"$Bin;`$env:Path`""
}
Write-Host ""
Write-Host "next:"
Write-Host "  xiaozhua doctor      health check"
Write-Host "  xiaozhua update      upgrade later with this one command"
Write-Host ""
