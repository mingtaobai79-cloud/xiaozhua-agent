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
#   XIAOZHUA_SRC    local checkout to install from (skips clone/zip entirely)
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
  [string]$Source = $(if ($env:XIAOZHUA_SRC) { $env:XIAOZHUA_SRC } else { '' }),
  [switch]$NoPath,
  [switch]$NoLink
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

# ---- 2. source code: local dir > existing git checkout > clone (180s timeout) > zip
$gitExe = $null
if (Get-Command git -ErrorAction SilentlyContinue) { $gitExe = 'git' }
if ($env:XIAOZHUA_GIT -and (Test-Path $env:XIAOZHUA_GIT)) { $gitExe = $env:XIAOZHUA_GIT }
foreach ($d in @("$env:ProgramFiles\Git\cmd", "$env:LOCALAPPDATA\Programs\Git\cmd", 'D:\software\Git\cmd')) {
  if (-not $gitExe -and (Test-Path (Join-Path $d 'git.exe'))) { $gitExe = (Join-Path $d 'git.exe') }
}
$Src  = Join-Path $Root 'src'
$Venv = Join-Path $Root 'venv'
$Pkg  = Join-Path $Root 'pkg'
$Bin  = Join-Path $Root 'bin'
New-Item -ItemType Directory -Force -Path $Root | Out-Null

function Remove-Tree($path) {
  # Locked by git / antivirus -> IOException: retry, then empty it with robocopy /MIR
  for ($i = 0; $i -lt 3; $i++) {
    if (-not (Test-Path $path)) { return }
    try { Remove-Item -Recurse -Force $path -ErrorAction Stop; return } catch { Start-Sleep -Milliseconds 800 }
  }
  if (Test-Path $path) {
    $empty = Join-Path $env:TEMP ("xz-empty-" + [guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Force -Path $empty
    & robocopy $empty $path /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
    Remove-Item $empty -Recurse -Force -ErrorAction SilentlyContinue
  }
}

function Copy-Tree($from, $to) {
  Remove-Tree $to
  $null = New-Item -ItemType Directory -Force -Path $to
  & robocopy $from $to /E /XD .git .venv __pycache__ .pytest_cache /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
  $code = $LASTEXITCODE
  # robocopy: 0-7 = success with various copies, >=8 = real failure
  if ($code -ge 8) { Die "copying $from -> $to failed (robocopy exit $code)" }
}

if ($Source) {
  if (-not (Test-Path (Join-Path $Source 'pyproject.toml'))) { Die "XIAOZHUA_SRC=$Source does not look like the repo (no pyproject.toml)" }
  Info "using local source $Source"
  Copy-Tree $Source $Src
  Ok "code copied  version $(if (Test-Path (Join-Path $Src 'VERSION')) { (Get-Content (Join-Path $Src 'VERSION') -Raw).Trim() } else { '?' })"
}
elseif (Test-Path (Join-Path $Src '.git')) {
  if (-not $gitExe) { Die "git not found but $Src is a git checkout; install git or set XIAOZHUA_SRC" }
  Info "updating code at $Src"
  $shallow = ((& $gitExe -C $Src rev-parse --is-shallow-repository 2>$null | Select-Object -First 1) -eq 'true')
  if ($shallow) {
    # depth-1 checkout: fetch just the tip again instead of unshallowing the whole history
    & $gitExe -C $Src fetch --depth 1 --quiet origin "+refs/heads/$Branch`:refs/remotes/origin/$Branch"
    if ($LASTEXITCODE -ne 0) { & $gitExe -C $Src fetch --depth 1 --quiet origin }
  } else {
    & $gitExe -C $Src fetch --prune --quiet origin
  }
  if ($LASTEXITCODE -ne 0) { Die "git fetch failed (network or credentials)" }
  & $gitExe -C $Src checkout --quiet $Branch
  & $gitExe -C $Src merge --ff-only "origin/$Branch" --quiet
  if ($LASTEXITCODE -ne 0) { Die "local commits diverge from origin/$Branch; resolve manually in $Src" }
}
else {
  $got = $false
  if ($gitExe) {
    Info "cloning into $Src (depth 1, ~50 MB; 180s timeout, falls back to a zip download)"
    if (Test-Path $Src) { Remove-Item -Recurse -Force $Src }
    $job = Start-Job -ScriptBlock {
      param($g, $r, $b, $d)
      & $g clone --depth 1 --single-branch --branch $b $r $d 2>&1
    } -ArgumentList $gitExe, $Repo, $Branch, $Src
    $null = Wait-Job $job -Timeout 180
    if ($job.State -eq 'Completed') {
      $null = Receive-Job $job
      if ((Test-Path (Join-Path $Src 'pyproject.toml'))) { $got = $true }
    } else {
      Stop-Job $job -ErrorAction SilentlyContinue
      # Stop-Job only ends the PowerShell job: the native git / git-remote-https /
      # index-pack children keep running and lock the src dir, so the next install
      # or update cannot delete it. Match them by command line and terminate.
      try {
        Get-CimInstance Win32_Process -Filter "Name='git.exe'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -and $_.CommandLine -like "*$Root*" } |
          ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
      } catch {}
      Start-Sleep -Milliseconds 500
      Info "git clone did not finish in 180s (slow or blocked); switching to zip download"
    }
    Remove-Job $job -Force -ErrorAction SilentlyContinue
    if (-not $got -and (Test-Path $Src)) { Remove-Tree $Src }
  }
  if (-not $got) {
    $slug = ($Repo -replace '^.*github\.com[:/]', '') -replace '\.git$', ''
    $zipUrl = "https://codeload.github.com/$slug/zip/refs/heads/$Branch"
    $zip = Join-Path $Root 'src.zip'
    $tmp = Join-Path $Root 'src-unzip'
    Info "downloading $zipUrl"
    try {
      Invoke-WebRequest -Uri $zipUrl -OutFile $zip -UseBasicParsing -TimeoutSec 600
      if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
      Expand-Archive -Path $zip -DestinationPath $tmp -Force
      $inner = @(Get-ChildItem $tmp -Directory)[0]
      if (-not $inner) { Die "zip archive looks empty" }
      Copy-Tree $inner.FullName $Src
      $got = $true
      Info "installed from zip (no .git: `xiaozhua update` will re-download the zip instead of pulling)"
    } catch {
      Die ("could not fetch the code: " + $_.Exception.Message + "`n  Options: set `$env:XIAOZHUA_SRC='C:\path\to\a\local\checkout', or check proxy/VPN, then rerun.")
    } finally {
      Remove-Item $zip -Force -ErrorAction SilentlyContinue
      Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}
$sha = if ((Test-Path (Join-Path $Src '.git')) -and $gitExe) { (& $gitExe -C $Src rev-parse --short HEAD).Trim() } else { 'zip' }
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
$installArgs = @((Join-Path $Src 'installer\selfupdate.py'), 'install', '--host', $Hosts, '--target', $Pkg, '--write', '--force')
if ($Source) { $installArgs += @('--source', $Source) }
$linkReport = Join-Path $Root 'link-report.json'
if (-not $NoLink) { $installArgs += @('--link', '--link-report', $linkReport) }
$hostCfg = Invoke-Native $venvPy $installArgs
if ($hostCfg.Exit -ne 0) {
  Die ("host config generation failed: " + (@($hostCfg.Lines) -join ' | '))
}
Ok "host configs written to $Pkg"

# ---- 5. xiaozhua command (cmd shim + ps1 shim, no execution-policy dependency)
# Shims are ASCII-only on purpose and locate the install relative to themselves
# (%~dp0 / $PSScriptRoot). Writing the real absolute path here breaks on
# non-ASCII user names: the shim is written in ANSI/ASCII, so a CJK user name
# turns into "???" and cmd then cannot find the interpreter.
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
$cmdShim = Join-Path $Bin 'xiaozhua.cmd'
@"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0xiaozhua.ps1" %*
exit /b %ERRORLEVEL%
"@ | Set-Content -Path $cmdShim -Encoding ASCII
$psShim = Join-Path $Bin 'xiaozhua.ps1'
@"
# ASCII-only shim: resolve the install dir from this file's own location so a
# non-ASCII username (or a moved install) does not break the launcher.
`$ErrorActionPreference = 'Stop'
`$XzHome = Split-Path -Parent `$PSScriptRoot
`$py = Join-Path `$XzHome 'venv\Scripts\python.exe'
`$entry = Join-Path `$XzHome 'src\installer\selfupdate.py'
if (-not (Test-Path `$py)) { Write-Error "xiaozhua-agent: venv missing at `$XzHome\venv (rerun the installer)"; exit 1 }
& `$py `$entry @args
exit `$LASTEXITCODE
"@ | Set-Content -Path $psShim -Encoding ASCII
Ok "command $cmdShim"

# ---- 5b. surface the MCP link result (child's own stdout is UTF-8, PS 5.1 mangles it)
if (-not $NoLink -and (Test-Path $linkReport)) {
  try {
    $rep = Get-Content $linkReport -Raw -Encoding UTF8 | ConvertFrom-Json
    $okHosts = @($rep | Where-Object { $_.ok } | ForEach-Object { $_.host })
    $badHosts = @($rep | Where-Object { -not $_.ok -and $_.action -eq 'linked' } | ForEach-Object { $_.host })
    if ($okHosts.Count) { Ok ("MCP linked -> " + ($okHosts -join ', ')) }
    if ($badHosts.Count) { Info ("MCP link FAILED -> " + ($badHosts -join ', ') + " (run: xiaozhua link)") }
  } catch {}
  Remove-Item $linkReport -Force -ErrorAction SilentlyContinue
}

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
