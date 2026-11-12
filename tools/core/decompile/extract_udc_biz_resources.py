"""从 udc-biz JAR 提取关键资源 JSON（权限/版型/特征/预设/白名单）到 audit 产物。

udc-biz 携带 1063 个非 class 资源，其中多份是**平台机制的权威配置**（不是推断）：
  auth/{deploy,draft}-auth.json      设计态 vs 部署态权限（entity/attribute 的 create/update/delete）
  openApi/entityOpenApi.json         openAPI 四操作 → 方法清单（创建/删除/更新/查询）
  stereotype/<name>/config.json      版型：necessaryFeatures / availableFeatures / dataFlowEnabled
  feature/<name>/config.json         特征（密级/扩展/停用/终止/…）
  presetData/*.json                  预置数据（属性能力矩阵/枚举/字段集/事件）
  microflow/*WhiteList.json          事件/服务白名单
  upgrade/componentMapping.json      组件映射

用法：
    python tools/extract_udc_biz_resources.py <jar> [--out <dir>]

证据边界：STATIC_BYTECODE（jar 打包资源原文），不证明运行态行为。
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

# 关键资源白名单（按目录前缀）
KEY_PREFIXES = (
    "auth/", "openApi/", "stereotype/", "feature/", "presetData/",
    "microflow/", "upgrade/", "formula-functions.xml", "generator.properties",
)


def is_key(name: str) -> bool:
    return any(name.startswith(p) for p in KEY_PREFIXES)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jar")
    ap.add_argument("--out", default="docs/audit/artifacts/udc-biz-5.3.517/resources")
    ns = ap.parse_args()
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(ns.jar)
    written = 0
    index: dict[str, dict] = {}
    for name in z.namelist():
        if name.endswith("/") or not name or ".class" in name:
            continue
        if not is_key(name):
            continue
        raw = z.read(name)
        txt = raw.decode("utf-8", errors="replace")
        # 原样落盘（保留目录结构）
        dest = out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(txt, encoding="utf-8")
        # 索引（JSON 则记摘要）
        entry = {"bytes": len(raw)}
        if name.endswith(".json"):
            try:
                data = json.loads(txt)
                if isinstance(data, dict):
                    entry["json_keys"] = list(data)[:20]
                elif isinstance(data, list):
                    entry["json_len"] = len(data)
            except Exception as e:
                entry["json_err"] = str(e)[:60]
        index[name] = entry
        written += 1
    (out / "_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"提取 {written} 个资源 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
