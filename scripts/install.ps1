# xiaozhua-agent 一键安装 / 升级（Windows PowerShell 5.1+ / PowerShell 7）
#
#   irm https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.ps1 | iex
#
# 只装一个宿主（iex 传参写法）：
#   & ([scriptblock]::Create((irm .../install.ps1))) -Hosts hermes
#
# 可选环境变量：
#   XIAOZHUA_HOME   安装根目录（默认 %USERPROFILE%\.xiaozhua）
#   XIAOZHUA_HOSTS  宿主，逗号分隔或 all（默认 all）
#   XIAOZHUA_REPO   仓库地址
#   XIAOZHUA_BRANCH 分支（默认 main）
#
# 说明：不装进系统 Python，全部落在 XIAOZHUA_HOME 下的 venv，卸载=删目录。

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

function Ok($m)   { Write-Host "✓ $m" -ForegroundColor Green }
function Info($m) { Write-Host $m -ForegroundColor DarkGray }
function Die($m)  { Write-Host "✗ $m" -ForegroundColor Red; exit 1 }

$Src  = Join-Path $Root 'src'
$Venv = Join-Path $Root 'venv'
$Pkg  = Join-Path $Root 'pkg'
$Bin  = Join-Path $Root 'bin'

Write-Host ""
Write-Host "xiaozhua-agent 安装器 · Windows $([Environment]::OSVersion.Version)"
Write-Host ""

# ---- 1. Python >= 3.12（优先 py 启动器，能挑版本）
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
  $exe = $c[0]; $pre = $c[1]
  try {
    $ver = & $exe @pre -c "import sys;print('%d.%d.%d'%sys.version_info[:3])" 2>$null
    if ($LASTEXITCODE -eq 0 -and $ver) {
      $parts = $ver.Split('.')
      if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 12) {
        $pyExe = @($exe) + $pre
        Ok "Python $ver  ($exe $($pre -join ' '))"
        break
      }
    }
  } catch { }
}
if (-not $pyExe) {
  Die @"
需要 Python 3.12+（当前机器没有）。
  装法一：winget install Python.Python.3.12
  装法二：https://www.python.org/downloads/  （勾选 Add python.exe to PATH）
装完重开终端，再跑本命令。
"@
}

# ---- 2. git + 代码
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Die "缺 git：winget install Git.Git（装完重开终端）"
}
New-Item -ItemType Directory -Force -Path $Root | Out-Null
if (Test-Path (Join-Path $Src '.git')) {
  Info "更新代码 $Src"
  git -C $Src fetch --prune --quiet origin
  if ($LASTEXITCODE -ne 0) { Die "git fetch 失败（检查网络/凭据）" }
  git -C $Src checkout --quiet $Branch
  git -C $Src merge --ff-only "origin/$Branch" --quiet
  if ($LASTEXITCODE -ne 0) { Die "本地有分叉提交，无法快进：先到 $Src 手动处理" }
} else {
  Info "拉取代码 → $Src"
  if (Test-Path $Src) { Remove-Item -Recurse -Force $Src }
  git clone --quiet --branch $Branch $Repo $Src
  if ($LASTEXITCODE -ne 0) { Die "git clone 失败：$Repo" }
}
$sha = (git -C $Src rev-parse --short HEAD).Trim()
$ver = if (Test-Path (Join-Path $Src 'VERSION')) { (Get-Content (Join-Path $Src 'VERSION') -Raw).Trim() } else { '?' }
Ok "代码 $sha  版本 $ver"

# ---- 3. venv + 依赖
Info "准备虚拟环境 $Venv"
if (-not (Test-Path (Join-Path $Venv 'Scripts\python.exe'))) {
  $pyArgs = @($pyExe | Select-Object -Skip 1)
  & $pyExe[0] @pyArgs -m venv $Venv
  if ($LASTEXITCODE -ne 0) { Die "venv 创建失败：$Venv" }
}
$venvPy = Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path $venvPy)) { Die "找不到 $venvPy" }
# 同 install.sh：不主动升级 pip（Windows 上会把 pip 改名成 ~ip 后失败），只在坏掉时 ensurepip 自愈
& $venvPy -m pip --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  Info "pip 不可用，用 ensurepip 修复"
  & $venvPy -m ensurepip --upgrade 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { Die "pip 修复失败：手动跑 $venvPy -m ensurepip --upgrade" }
}
& $venvPy -m pip install --quiet -e $Src
if ($LASTEXITCODE -ne 0) {
  Info "-e 安装失败，退回单包安装"
  & $venvPy -m pip install --quiet "pyyaml>=6.0" "websocket-client>=1.6"
  if ($LASTEXITCODE -ne 0) { Die "依赖安装失败" }
}
Ok "依赖就绪"

# ---- 4. 宿主配置
Info "生成宿主配置 → $Pkg (host=$Hosts)"
& $venvPy (Join-Path $Src 'installer\selfupdate.py') install --host $Hosts --target $Pkg --write --force | Out-Null
if ($LASTEXITCODE -ne 0) { Die "宿主配置生成失败" }
Ok "宿主配置已写入 $Pkg"

# ---- 5. xiaozhua 命令（cmd 批处理 shim，不依赖 PowerShell 执行策略）
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
"@ | Set-Content -Path $psShim -Encoding UTF8
Ok "命令 $cmdShim"

# ---- 6. PATH（用户级，幂等）
if (-not $NoPath) {
  $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
  if ($null -eq $userPath) { $userPath = '' }
  $entries = $userPath.Split(';') | Where-Object { $_ }
  if ($entries -notcontains $Bin) {
    $newPath = (@($entries) + $Bin) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    Info "已把 $Bin 加进用户 PATH（新开终端生效）"
  }
}

# ---- 7. 自检：真起一次 MCP 数工具
Info "自检（真起一次 MCP 服务）"
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
if ($tools -le 0) { Die "自检失败：MCP 没数到工具（手动跑：$venvPy $server）" }
Ok "自检 tools=$tools"

Write-Host ""
Write-Host "装好了  $ver" -ForegroundColor Green
Write-Host ""
if (Get-Command xiaozhua -ErrorAction SilentlyContinue) {
  Write-Host "xiaozhua 已可用：xiaozhua doctor"
} else {
  Write-Host "当前窗口临时用：`$env:Path = `"$Bin;`$env:Path`""
}
Write-Host ""
Write-Host "下一步："
Write-Host "  xiaozhua doctor      体检"
Write-Host "  xiaozhua update      以后升级用这一条"
Write-Host ""
