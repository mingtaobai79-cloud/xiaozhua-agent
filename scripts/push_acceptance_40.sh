#!/usr/bin/env bash
# 批量把 验收/*.spec.json 推到 test2（创建 + 发布 + checkSchema + DB 回读）
set -u
cd "$(dirname "$0")/.." || exit 1
OUT=验收/PUSH-RESULT.md
: > "$OUT"
echo "# 40 条验收微流程推送结果" >> "$OUT"
echo "" >> "$OUT"
echo "| 业务 | 创建 | 发布 | checkSchema | 接口读回 |" >> "$OUT"
echo "|---|---|---|---|---|" >> "$OUT"
for f in 验收/*.spec.json; do
  base=$(basename "$f" .spec.json)
  cap="验收-${base}"
  nm=$(echo "$base" | awk -F- '{printf "%s", $1; for(i=2;i<=NF;i++) printf "%s%s", toupper(substr($i,1,1)), substr($i,2)}')
  log=$(mktemp)
  ./.venv/Scripts/python.exe tools/core/microflow/build_microflow.py \
     --app-id 8704025620829192834 \
     --caption "$cap" --name "$nm" \
     --spec "$f" > "$log" 2>&1
  create=$(grep -o "已创建 id = [0-9]*" "$log" | head -1)
  pub=$(grep -o "publish(update)：[^ ]* [A-Z]*" "$log" | head -1)
  chk=$(grep -o "checkSchema/update： [^ ]* {'check': [A-Za-z]*" "$log" | head -1)
  read=$(grep -o "接口读回：state=[A-Z]*" "$log" | head -1)
  [ -z "$chk" ] && chk=$(grep -o "checkSchema：[^|]*" "$log" | head -1)
  echo "| $base | ${create:-FAIL} | ${pub:-FAIL} | ${chk:-FAIL} | ${read:-FAIL} |" >> "$OUT"
  echo "[$base] ${create:-FAIL} | ${chk:-?}"
  rm -f "$log"
done
echo "DONE" >> "$OUT"
