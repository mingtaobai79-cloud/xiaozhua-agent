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
#   XIAOZHUA_PYTHON exact python.exe to use (skips detection)
#   XIAOZHUA_HOME   install root   (default %USERPROFILE%\.xiaozhua)
#   XIAOZHUA_HOSTS  hosts, comma separated or all (default all)
#   XIAOZHUA_REPO   git remote
#   XIAOZHUA_BRANCH branch (default main)
#
# Python: needs 3.11+. Detection order = XIAOZHUA_PYTHON, py launcher (3.13/3.12/3.11/3),
#   `py -0p` registry list, PATH python/python3, then the usual install dirs
#   (LocalAppData\Programs\Python, Program Files, C:\Python3*, uv-managed pythons).
#   Microsoft Store stubs under WindowsApps are skipped - they are 0-byte aliases.

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

function Invoke-Native($exe, [string[]]$arguments) {
  # PS 5.1 turns a native command's stderr into a terminating NativeCommandError when
  # $ErrorActionPreference is Stop. pip writes its "[notice] A new release of pip" line to
  # stderr, which aborted the whole installer. Run native tools with EAP=Continue and
  # decide success from $LASTEXITCODE only.
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $lines = & $exe @arguments 2>&1 | ForEach-Object { "$_" }
    return @{ Exit = $LASTEXITCODE; Lines = @($lines) }
  } finally {
    $ErrorActionPreference = $prev
  }
}

function Ok($m)   { Write-Host "[ok]   $m" -ForegroundColor Green }
function Info($m) { Write-Host "[..]   $m" -ForegroundColor DarkGray }
function Die($m)  { Write-Host "[fail] $m" -ForegroundColor Red; exit 1 }

$MinMajor = 3
$MinMinor = 11

function Test-PythonExe($exe, $pre) {
  # Returns "3.11.16" or $null. Skips the Microsoft Store alias stub.
  if (-not $exe) { return $null }
  if ("$exe" -like '*\WindowsApps\*') { return $null }
  try {
    $out = & $exe @pre -c "import sys;print('%d.%d.%d'%sys.version_info[:3])" 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    $line = @($out | Where-Object { "$_" -match '^\d+\.\d+\.\d+$' })[0]
    if ($line) { return "$line" }
  } catch { }
  return $null
}

function Get-PythonCandidates {
  $list = New-Object System.Collections.ArrayList
  if ($env:XIAOZHUA_PYTHON) { [void]$list.Add(@($env:XIAOZHUA_PYTHON, @())) }

  if (Get-Command py -ErrorAction SilentlyContinue) {
    # `py -0p` lists every registered interpreter. Prefer 64-bit paths, then higher versions:
    # a 32-bit 3.11 must not win over a 64-bit uv-managed 3.11.
    try {
      $reg = @()
      foreach ($line in (& py -0p 2>$null)) {
        if ("$line" -match '([A-Za-z]:\\[^ ]*python\.exe)') {
          $path = $Matches[1]
          $bits = if ($path -match '(?i)(-32|x86)') { 1 } else { 0 }
          $rank = 0
          if ($path -match '(?i)cpython-(\d+)\.(\d+)') { $rank = [int]$Matches[1] * 100 + [int]$Matches[2] }
          elseif ($path -match '(?i)python(\d)(\d+)') { $rank = [int]$Matches[1] * 100 + [int]$Matches[2] }
          $reg += ,@($bits, (-1 * $rank), $path)
        }
      }
      foreach ($r in ($reg | Sort-Object { $_[0] }, { $_[1] })) { [void]$list.Add(@($r[2], @())) }
    } catch { }
    foreach ($v in @('-3.13', '-3.12', '-3.11', '-3')) { [void]$list.Add(@('py', @($v))) }
  }

  foreach ($n in @('python', 'python3')) {
    if (Get-Command $n -ErrorAction SilentlyContinue) { [void]$list.Add(@($n, @())) }
  }

  $globs = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python3*\python.exe'),
    (Join-Path $env:APPDATA 'uv\python\cpython-3*\python.exe'),
    (Join-Path $env:USERPROFILE '.local\share\uv\python\cpython-3*\python.exe'),
    'C:\Python3*\python.exe'
  )
  if ($env:ProgramFiles) { $globs += (Join-Path $env:ProgramFiles 'Python3*\python.exe') }
  if (${env:ProgramFiles(x86)}) { $globs += (Join-Path ${env:ProgramFiles(x86)} 'Python3*\python.exe') }

  foreach ($g in $globs) {
    try {
      $hits = Get-ChildItem -Path $g -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
      foreach ($h in $hits) { [void]$list.Add(@($h.FullName, @())) }
    } catch { }
  }
  return $list
}

Write-Host ""
Write-Host "xiaozhua-agent installer - Windows $([Environment]::OSVersion.Version)"
Write-Host ""

# ---- 1. Python 3.11+
Info "looking for Python $MinMajor.$MinMinor+"
$pyExe = $null
$pyVer = $null
$seen = @{}
$tried = @()
foreach ($c in (Get-PythonCandidates)) {
  $exe = "$($c[0])"
  $pre = @($c[1])
  $key = "$exe $($pre -join ' ')"
  if ($seen.ContainsKey($key)) { continue }
  $seen[$key] = $true
  $v = Test-PythonExe $exe $pre
  if ($v) {
    $parts = $v.Split('.')
    $tried += ("{0} -> {1}" -f $key, $v)
    if ([int]$parts[0] -eq $MinMajor -and [int]$parts[1] -ge $MinMinor) {
      $pyExe = @($exe) + $pre
      $pyVer = $v
      break
    }
  }
}
if (-not $pyExe) {
  Write-Host ""
  Write-Host "Candidates checked:" -ForegroundColor Yellow
  if ($tried.Count -eq 0) { Write-Host "  (no python interpreter found on PATH or in the usual install dirs)" }
  foreach ($t in $tried) { Write-Host "  $t" }
  Write-Host ""
  Die ("Python {0}.{1}+ is required. Install it with:  winget install Python.Python.3.12   (or python.org, tick 'Add python.exe to PATH'), reopen the terminal, then rerun. Or point at an existing interpreter: `$env:XIAOZHUA_PYTHON='C:\path\to\python.exe'" -f $MinMajor, $MinMinor)
}
Ok "Python $pyVer  ($($pyExe -join ' '))"

# ---- 2. git + code
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  $gitDirs = @("$env:ProgramFiles\Git\cmd", "$env:LOCALAPPDATA\Programs\Git\cmd", 'D:\software\Git\cmd')
  foreach ($d in $gitDirs) {
    if ((Test-Path (Join-Path $d 'git.exe')) -and ($env:Path -notlike "*$d*")) { $env:Path = "$d;$env:Path" }
  }
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Die "git is required (it fetches and updates the code). Install with:  winget install Git.Git  then reopen the terminal."
}
$gitExe = if ($env:XIAOZHUA_GIT) { $env:XIAOZHUA_GIT } else { 'git' }
$Src  = Join-Path $Root 'src'
$Venv = Join-Path $Root 'venv'
$Pkg  = Join-Path $Root 'pkg'
$Bin  = Join-Path $Root 'bin'

New-Item -ItemType Directory -Force -Path $Root | Out-Null
if (Test-Path (Join-Path $Src '.git')) {
  Info "updating code at $Src"
  & $gitExe -C $Src fetch --prune --quiet origin
  if ($LASTEXITCODE -ne 0) { Die "git fetch failed (network or credentials)" }
  & $gitExe -C $Src checkout --quiet $Branch
  & $gitExe -C $Src merge --ff-only "origin/$Branch" --quiet
  if ($LASTEXITCODE -ne 0) { Die "local commits diverge from origin/$Branch; resolve manually in $Src" }
} else {
  Info "cloning into $Src"
  if (Test-Path $Src) { Remove-Item -Recurse -Force $Src }
  & $gitExe clone --quiet --branch $Branch $Repo $Src
  if ($LASTEXITCODE -ne 0) { Die "git clone failed: $Repo" }
}
$sha = (& $gitExe -C $Src rev-parse --short HEAD).Trim()
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
$pipProbe = Invoke-Native $venvPy @('-m', 'pip', '--version')
if ($pipProbe.Exit -ne 0) {
  Info "pip missing, repairing with ensurepip"
  $repair = Invoke-Native $venvPy @('-m', 'ensurepip', '--upgrade')
  if ($repair.Exit -ne 0) { Die "pip repair failed: run $venvPy -m ensurepip --upgrade manually" }
}
$editable = Invoke-Native $venvPy @('-m', 'pip', 'install', '--quiet', '-e', $Src)
if ($editable.Exit -ne 0) {
  $why = @($editable.Lines | Where-Object { $_ -match 'ERROR|error:' })[-1]
  if ($why) { Info ("editable install failed: " + $why) } else { Info "editable install failed, falling back to plain deps" }
  $plain = Invoke-Native $venvPy @('-m', 'pip', 'install', '--quiet', 'pyyaml>=6.0', 'websocket-client>=1.6')
  if ($plain.Exit -ne 0) { Die "dependency install failed" }
}
Ok "dependencies ready"

# ---- 4. host configs (also records state.json for `xiaozhua update`)
Info "generating host configs -> $Pkg (host=$Hosts)"
$hostCfg = Invoke-Native $venvPy @((Join-Path $Src 'installer\selfupdate.py'), 'install', '--host', $Hosts, '--target', $Pkg, '--write', '--force')
if ($hostCfg.Exit -ne 0) {
  Die ("host config generation failed: " + (@($hostCfg.Lines) -join ' | '))
}
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
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$out = @($l1, $l2) | & $venvPy $server 2>$null
$ErrorActionPreference = $prevEap
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
Write-Host "For this window only: `$env:Path = `"$Bin;`$env:Path`""
Write-Host "(a new terminal picks up the user PATH change automatically)"
Write-Host ""
Write-Host "next:"
Write-Host "  xiaozhua doctor      health check"
Write-Host "  xiaozhua update      upgrade later with this one command"
Write-Host ""
