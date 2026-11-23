#!/usr/bin/env bash
# xiaozhua-agent 一键安装 / 升级（macOS · Linux）
#
#   curl -fsSL https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --host hermes      # 只装一个宿主
#
# 可选环境变量：
#   XIAOZHUA_HOME   安装根目录（默认 ~/.xiaozhua）
#   XIAOZHUA_HOSTS  宿主，逗号分隔或 all（默认 all）
#   XIAOZHUA_REPO   仓库地址（默认官方）
#   XIAOZHUA_BRANCH 分支（默认 main）
#   PYTHON          指定解释器
#
# 兼容性：macOS 自带 bash 3.2 / 无 readlink -f / 系统 python 是 3.9 —— 本脚本都避开了。
set -euo pipefail

XIAOZHUA_HOME="${XIAOZHUA_HOME:-$HOME/.xiaozhua}"
HOSTS="${XIAOZHUA_HOSTS:-all}"
REPO="${XIAOZHUA_REPO:-https://github.com/mingtaobai79-cloud/xiaozhua-agent.git}"
BRANCH="${XIAOZHUA_BRANCH:-main}"
SRC="$XIAOZHUA_HOME/src"
VENV="$XIAOZHUA_HOME/venv"
PKG="$XIAOZHUA_HOME/pkg"
BIN="$XIAOZHUA_HOME/bin"

info() { printf '\033[2m%s\033[0m\n' "$*"; }
ok()   { printf '\033[32m✓\033[0m %s\n' "$*"; }
die()  { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# ---- 参数（curl | bash -s -- --host hermes）
while [ $# -gt 0 ]; do
  case "$1" in
    --host)   HOSTS="$2"; shift 2 ;;
    --host=*) HOSTS="${1#*=}"; shift ;;
    --home)   XIAOZHUA_HOME="$2"; SRC="$XIAOZHUA_HOME/src"; VENV="$XIAOZHUA_HOME/venv"
              PKG="$XIAOZHUA_HOME/pkg"; BIN="$XIAOZHUA_HOME/bin"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0" 2>/dev/null || true; exit 0 ;;
    *) die "未知参数：$1" ;;
  esac
done

printf '\nxiaozhua-agent 安装器 · %s %s\n\n' "$(uname -s)" "$(uname -m)"

# ---- 1. Python ≥ 3.12（macOS 系统 python 是 3.9，必须自己找）
need_py=""
for cand in "${PYTHON:-}" python3.13 python3.12 python3 python; do
  [ -n "$cand" ] || continue
  command -v "$cand" >/dev/null 2>&1 || continue
  if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3,12) else 1)' 2>/dev/null; then
    need_py="$(command -v "$cand")"; break
  fi
done
if [ -z "$need_py" ]; then
  printf '\033[31m✗ 需要 Python 3.12+，当前只有：\033[0m\n' >&2
  for c in python3 python; do command -v "$c" >/dev/null 2>&1 && "$c" --version >&2; done
  cat >&2 <<EOF

macOS：  brew install python@3.12
Debian： sudo apt install python3.12 python3.12-venv
然后重跑本命令，或 PYTHON=/opt/homebrew/bin/python3.12 curl ... | bash
EOF
  exit 1
fi
ok "Python $("$need_py" -c 'import platform;print(platform.python_version())')  ($need_py)"

# ---- 2. git + 代码
command -v git >/dev/null 2>&1 || die "缺 git：macOS 跑 xcode-select --install；Debian 跑 sudo apt install git"
mkdir -p "$XIAOZHUA_HOME"
if [ -d "$SRC/.git" ]; then
  info "更新代码 $SRC"
  git -C "$SRC" fetch --prune --quiet origin
  git -C "$SRC" checkout --quiet "$BRANCH"
  git -C "$SRC" merge --ff-only "origin/$BRANCH" --quiet || die "本地有分叉提交，无法快进：先到 $SRC 手动处理"
else
  info "拉取代码 → $SRC"
  [ -e "$SRC" ] && rm -rf "$SRC"        # 残留的非 git 目录
  git clone --quiet --branch "$BRANCH" "$REPO" "$SRC"
fi
ok "代码 $(git -C "$SRC" rev-parse --short HEAD)  版本 $(cat "$SRC/VERSION" 2>/dev/null || echo '?')"

# ---- 3. venv + 依赖（用 venv 的 python，不污染系统）
info "准备虚拟环境 $VENV"
[ -d "$VENV" ] || "$need_py" -m venv "$VENV"
# POSIX 用 venv/bin/python；在 Windows 的 git-bash 里跑会落在 venv/Scripts/python.exe，两种都认
VENV_PY="$VENV/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="$VENV/Scripts/python.exe"
[ -x "$VENV_PY" ] || die "虚拟环境创建失败：$VENV 下没有 python（bin/ 与 Scripts/ 都不存在）"
"$VENV_PY" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
"$VENV_PY" -m pip install --quiet -e "$SRC" || "$VENV_PY" -m pip install --quiet "pyyaml>=6.0" "websocket-client>=1.6"
ok "依赖就绪"

# ---- 4. 宿主配置
info "生成宿主配置 → $PKG (host=$HOSTS)"
"$VENV_PY" "$SRC/installer/selfupdate.py" install --host "$HOSTS" --target "$PKG" --write --force >/dev/null
ok "宿主配置已写入 $PKG"

# ---- 5. xiaozhua 命令
mkdir -p "$BIN"
cat > "$BIN/xiaozhua" <<EOF
#!/usr/bin/env bash
exec "$VENV_PY" "$SRC/installer/selfupdate.py" "\$@"
EOF
chmod +x "$BIN/xiaozhua"
ok "命令 $BIN/xiaozhua"

# ---- 6. 自检：真起一次 MCP 数工具
info "自检（真起一次 MCP 服务）"
L1='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"install","version":"1"}}}'
L2='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
resp="$(printf '%s\n%s\n' "$L1" "$L2" | "$VENV_PY" "$SRC/adapters/mcp/server.py" 2>/dev/null || true)"
tools="$(printf '%s' "$resp" | "$VENV_PY" -c '
import json, sys
n = 0
for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    res = obj.get("result") or {}
    if "tools" in res:
        n = len(res["tools"])
print(n)')"
[ "${tools:-0}" -gt 0 ] || die "自检失败：MCP 没数到工具（手动跑：$VENV_PY $SRC/adapters/mcp/server.py）"
ok "自检 tools=$tools"

# ---- 7. PATH 提示（macOS 默认 zsh）
printf '\n\033[32m装好了\033[0m  %s\n\n' "$(cat "$SRC/VERSION" 2>/dev/null || echo '?')"
case ":$PATH:" in
  *":$BIN:"*) printf 'xiaozhua 已可用：xiaozhua doctor\n\n' ;;
  *)
    printf '把下面一行加进 %s，然后重开终端：\n' "${ZDOTDIR:-$HOME}/.zshrc"
    printf '\n  export PATH="%s:$PATH"\n\n' "$BIN"
    printf '当前窗口先临时用：export PATH="%s:$PATH"\n\n' "$BIN"
    ;;
esac
printf '下一步：\n  xiaozhua doctor      体检\n  xiaozhua update      以后升级用这一条\n\n'
