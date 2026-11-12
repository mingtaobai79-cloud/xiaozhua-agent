#!/usr/bin/env bash
# 一条命令装好并自检。
#
#   bash quickstart.sh                    # 装到 ~/xiaozhua-pkg，宿主 all
#   bash quickstart.sh ~/my-pkg hermes    # 指定目录 + 只装 hermes
#   bash quickstart.sh "" all --portable  # 生成 <XIAOZHUA_AGENT_ROOT> 占位符，跨机分发用
#
# 做的事：装依赖 → 生成宿主配置 → 起一次 MCP 服务数工具数。
# 不改任何全局配置，产物全在你指定的目录里。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$HOME/xiaozhua-pkg}"
HOST="${2:-all}"
PORTABLE="${3:-}"
PY="${PYTHON:-python}"

cd "$ROOT"

echo "[1/3] 依赖"
"$PY" - <<'PYEOF' || "$PY" -m pip install -q "pyyaml>=6.0" "websocket-client>=1.6"
import yaml, websocket  # noqa: F401
PYEOF

echo "[2/3] 生成宿主配置 → $TARGET (host=$HOST)"
ARGS=(--host "$HOST" --target "$TARGET" --write)
[ "$PORTABLE" = "--portable" ] && ARGS+=(--portable)
"$PY" installer/install.py "${ARGS[@]}"

echo "[3/3] 自检：真起一次 MCP 服务"
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"qs","version":"1"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | "$PY" adapters/mcp/server.py \
  | "$PY" -c '
import sys, json
n = name = None
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        o = json.loads(line)
    except json.JSONDecodeError:
        continue
    res = o.get("result") or {}
    if "serverInfo" in res:
        name = res["serverInfo"].get("name")
    if "tools" in res:
        n = len(res["tools"])
print(f"[ok] serverInfo={name}  tools={n}")
raise SystemExit(0 if n else 1)
'

echo
echo "装好了。宿主配置在这个目录里："
echo "  $TARGET"
find "$TARGET" -maxdepth 2 -type f \( -name '*.yaml' -o -name '*.toml' -o -name '*.json' -o -name '*.md' \) | sed 's/^/  /'
