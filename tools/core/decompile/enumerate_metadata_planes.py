# Mechanical enumerator of the three PARALLEL metadata planes that all live under the
# /udc prefix, plus the frontend op-family usage of each plane.
#
# Why this exists: the repo "platform operation surface" was for many rounds read as a
# SINGLE-artifact view (udc-web -> 674 endpoints). LIVE evidence (RUNTIME-URL-SURFACE.md
# finding A) then showed that /udc/metadata/** is served by a *different* component
# (ctp MetadataController). On top of that, udc-web itself registers TWO metadata
# prefixes one hyphen apart: udc/meta-data (MetaDataController, designer uses it) and
# udc/design-metadata (UdcDesignMetadataController, LIVE 0 calls in window). The ctp
# provider registers a THIRD one with no hyphen: metadata (ctp MetadataController).
# The leaf vocabularies of the latter two overlap heavily (43 shared leaves), so a path
# that reads correct can address a plane nobody calls.
#
# Everything here is read from DURABLE in-repo sources (no scratch, no network):
#   - docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json   (udc-web contract)
#   - docs/audit/artifacts/metadata-5.3.358/MetadataController.class  (ctp bytecode)
#   - docs/audit/artifacts/udc-frontend-5.3.496/chunks/*.js           (designer chunk)
#   - docs/audit/udc-semantics/RUNTIME-URL-SURFACE.json               (LIVE counts)
#
# Evidence level: VERIFIED_STATIC_BYTECODE + LIVE (for the cross-checks).
# Read-only and offline. Usage: python tools/enumerate_metadata_planes.py [--json]
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

CONTRACT = ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts" / "_api_full.json"
CTP_CLASS = ROOT / "docs" / "audit" / "artifacts" / "metadata-5.3.358" / "MetadataController.class"
ENUMERATOR = ROOT / "tools" / "core" / "decompile" / "enumerate_class_http_mappings.py"
DESIGNER_CHUNK = (ROOT / "docs" / "audit" / "artifacts" / "udc-frontend-5.3.496"
                  / "chunks" / "src_redux_store_ts.14dc061e.js")
LIVE_SURFACE = ROOT / "docs" / "audit" / "udc-semantics" / "RUNTIME-URL-SURFACE.json"

PLANE_META_DATA = ("meta-data-udcweb", "/udc/meta-data/", "udc-web-5.3.517", "MetaDataController")
PLANE_DESIGN_METADATA = ("design-metadata-udcweb", "/udc/design-metadata/",
                         "udc-web-5.3.517", "UdcDesignMetadataController")
PLANE_METADATA_CTP = ("metadata-ctp", "/udc/metadata/", "metadata-5.3.358",
                      "com.seeyon.ctp.metadata.controller.MetadataController")


def _load_enumerator():
    spec = importlib.util.spec_from_file_location("enumerate_class_http_mappings", ENUMERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _contract_plane(contract, controller):
    entry = contract[controller]
    full = [m["full_path"] for m in entry["methods"]]
    leaves = [p.rsplit("/", 1)[-1] for p in full]
    return {
        "controller": controller,
        "class_mapping": entry["class_mapping"],
        "endpoints": len(entry["methods"]),
        "contract_api_count": entry["api_count"],
        "distinct_full_paths": len(set(full)),
        "distinct_leaves": len(set(leaves)),
        "leaves": sorted(set(leaves)),
        "full_paths": sorted(set(full)),
    }


def _ctp_plane():
    mod = _load_enumerator()
    res = mod.enumerate_routes(str(CTP_CLASS))
    endpoints = res["endpoints"]
    leaves = sorted({e["sub_path"].strip("/") for e in endpoints})
    no_op = sorted(e["sub_path"] for e in endpoints if not e["op_code"])
    return {
        "controller": PLANE_METADATA_CTP[3],
        "class_mapping": res["class_mapping"],
        "endpoints": len(endpoints),
        "op_surface": sum(1 for e in endpoints if e["op_code"]),
        "no_op_subs": no_op,
        "distinct_leaves": len(leaves),
        "leaves": leaves,
    }


def enumerate_planes():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    p1 = _contract_plane(contract, PLANE_META_DATA[3])
    p2 = _contract_plane(contract, PLANE_DESIGN_METADATA[3])
    p3 = _ctp_plane()
    p1["id"], p1["external_prefix"] = PLANE_META_DATA[0], PLANE_META_DATA[1]
    p2["id"], p2["external_prefix"] = PLANE_DESIGN_METADATA[0], PLANE_DESIGN_METADATA[1]
    p3["id"], p3["external_prefix"] = PLANE_METADATA_CTP[0], PLANE_METADATA_CTP[1]

    l1, l2, l3 = set(p1["leaves"]), set(p2["leaves"]), set(p3["leaves"])
    udcweb_total = sum(len(v["methods"]) for v in contract.values())

    chunk = DESIGNER_CHUNK.read_text(encoding="utf-8", errors="replace")
    fam = {
        "udcMetaData": chunk.count("udcMetaData"),
        "udcDesignMetadata": chunk.count("udcDesignMetadata"),
    }

    live = json.loads(LIVE_SURFACE.read_text(encoding="utf-8"))
    usage = live["control_plane"]["route_family_usage_in_window"]

    return {
        "schema": "metadata-planes.v1",
        "evidence": "STATIC (udc-web contract + ctp bytecode) + LIVE (RUNTIME-URL-SURFACE.json)",
        "question": "平台操作面里有几个并行的 metadata 面？按单构件（udc-web 674）口径理解会漏什么？",
        "answer": ("三个并行面：udc-web 自身注册两个（udc/meta-data 32 / udc/design-metadata 47，"
                   "相差一个连字符），ctp 另注册一个无连字符的 metadata（105 mapping / 99 op 面）。"
                   "故平台操作面 = 全构件并集；单构件 674 口径漏掉 ctp 面 105 条。"),
        "planes": [p1, p2, p3],
        "cross_plane": {
            "leafs_meta_data_and_design_metadata_shared": len(l1.intersection(l2)),
            "leafs_meta_data_and_metadata_shared": len(l1.intersection(l3)),
            "leafs_design_metadata_and_metadata_shared": len(l2.intersection(l3)),
            "leafs_shared_by_all_three": sorted(l1.intersection(l2).intersection(l3)),
            "shared_leaves_design_metadata_vs_metadata": sorted(l2.intersection(l3)),
        },
        "surface_arithmetic": {
            "udc_web_contract_endpoints": udcweb_total,
            "udc_web_controllers": len(contract),
            "ctp_metadata_endpoints": p3["endpoints"],
            "platform_union_endpoints": udcweb_total + p3["endpoints"],
            "note": ("674（udc-web 单构件）与 779（含 ctp metadata 面）是两个不同口径，不可混用；"
                     "779 仍不是运行期全量（其它非 udc-web 提供者未纳入）。"),
        },
        "frontend_op_family_usage": {
            "chunk": "docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js",
            "hits": fam,
            "reading": ("设计器 trunk chunk 只出现 udcMetaData 族（udc/meta-data 面），"
                        "udcDesignMetadata 族命中 0 说明 design-metadata 面不是设计器在用。"),
        },
        "live_cross_check": {
            "family_calls_in_window": usage,
            "reading": ("运行期窗口 /udc/metadata/ 20 次调用 vs /udc/design-metadata/ 0 次；"
                        "被真实调用的是 ctp 无连字符面，而与它 43 个同名字面量的 "
                        "udc-web design-metadata 面 0 调用，即该面在本窗口是死面。"),
        },
        "why_it_matters": ("(1) 平台操作面必须按全构件并集理解（674 是单构件视图）；"
                           "(2) meta-data 与 metadata 相差一个连字符、leaf 词表大面积重叠，"
                           "按读起来像拼路径会打到无人调用的面（design-metadata）；"
                           "(3) GraphQL op 名由全路径派生，三面同名 leaf 会派生三个不同 op。"),
        "limitations": [
            "设计器 chunk 为 5.3.496 快照，部署 udc 为 5.3.517（版本差未消除）。",
            "LIVE 计数是单窗口事实，只证明该窗口的调用分布，不证明 design-metadata 面永不使用。",
            "779 只是 udc-web 加 ctp metadata，不是运行期全量端点面。",
            "ctp 面证据为 5.3.358 静态样本 + LIVE 同线程日志，未取 5.3.517 部署态该 class 字节。",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="enumerate parallel metadata planes")
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    ap.add_argument("--emit", help="把证据件写到该路径（与 --json 同字节）")
    args = ap.parse_args(argv)
    data = enumerate_planes()
    # ★ 字节级契约：换行显式固定为 CRLF，不走宿主文本模式转换。
    # 此前 print() 在 Windows 隐式转 CRLF、Linux 出 LF ⇒ 复算字节随宿主变化，
    # 而证据件是复算产物（字节即契约）⇒ 必须显式钉死。
    txt = json.dumps(data, ensure_ascii=False, indent=2)
    txt = txt.replace(chr(10), chr(13) + chr(10)) + chr(13) + chr(10)
    if args.emit:
        Path(args.emit).write_bytes(txt.encode("utf-8"))
        print("WROTE", args.emit)
    if args.json:
        sys.stdout.buffer.write(txt.encode("utf-8"))
        sys.stdout.buffer.flush()
        return 0
    for p in data["planes"]:
        print("%-26s %-22s endpoints=%4d leaves=%4d (%s)" % (
            p["id"], p["external_prefix"], p["endpoints"], p["distinct_leaves"], p["controller"]))
    c = data["cross_plane"]
    print("shared design-metadata-to-metadata = %d | all three = %s" % (
        c["leafs_design_metadata_and_metadata_shared"], c["leafs_shared_by_all_three"]))
    print("surface arithmetic = %s" % (data["surface_arithmetic"],))
    print("frontend family hits = %s" % (data["frontend_op_family_usage"]["hits"],))
    return 0


if __name__ == "__main__":
    sys.exit(main())
