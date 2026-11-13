#!/usr/bin/env python3
"""盘点分发仓库「带什么 / 不带什么」，生成 docs/audit/ASSET-INVENTORY.md。

为什么需要：这个仓库对外分发，但证据树有 390 MB。哪些资产必须随仓库走、哪些
可以重建、哪些因为含客户痕迹不能走，过去散落在对话里。本脚本把它们落成一份
可复现的表——数字从磁盘现算，理由来自 EXPORT_POLICY，未判定的会显式标出来。

判据三档：
  随仓库  已打进 docs/audit/reference/*.tar.gz 或已索引（signatures / svc / ui）
  可重建  不随仓库，但 tools/ 下有一句话重建入口
  不收录  含客户痕迹（客户名/环境域名/appId/内网 IP/真人名），或纯中间产物

用法：
    python tools/inventory_assets.py            # 生成 md + json
    python tools/inventory_assets.py --check    # 只打印未判定项，非零退出即需人工裁决
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "docs" / "audit" / "artifacts"
MD_OUT = ROOT / "docs" / "audit" / "ASSET-INVENTORY.md"
JSON_OUT = ROOT / "docs" / "audit" / "asset-inventory.json"

SAMPLE_BYTES = 2 * 1024 * 1024

# 客户痕迹检测（拼接写法，避免守卫自触发）
FORBIDDEN = {
    "客户组织": re.compile("chang" + "hong", re.I),
    "客户名(中文)": re.compile("\u957f\u8679"),
    "环境域名": re.compile("lowcode-" + "test" + "2"),
    "appId": re.compile(r"163126498398523384|8704025620829192834|6419954374508955097"),
    "内网IP": re.compile(r"\b(?:10\.\d{1,3}|192\.168)\.\d{1,3}\.\d{1,3}\b"),
    "真人名": re.compile("\u767d\u660e\u6d9b"),
}

# 人工裁决过的资产（键 = 相对 docs/audit/artifacts 的路径）
EXPORT_POLICY: dict[str, tuple[str, str]] = {
    "extension-surface-20261029": ("可重建", "原始反编译面 293 MB；签名已由 signatures.txt.gz 覆盖，"
                                            "契约/字段/实现类已由 surface-index.tar.gz + udc-platform 包覆盖"),
    "decompiled": ("不收录", "50 个临时 CFR 目录、版本重复，混 101 处客户组织名 / 218 处环境域名 / "
                            "178 处真实 appId / 11 处真人名；需要源码用 cfr-0.152.jar 重跑"),
    "scratch-migrated": ("不收录", "迁移过程草稿，无稳定结构，无代码引用"),
    "service-flow-20261103": ("不收录", "文件名即含真实 appId 与手机号，客户业务流证据"),
    "api-usage": ("不收录", "含内网 IP 与客户侧字段示例，可重跑 emit_api_usage.py 得到"),
    "frontend-surface-20261102": ("不收录", "客户应用自己的前端快照（appId + @seeyon 依赖版本）"),
    "udc-node-evidence": ("不收录", "含客户组织名、环境域名、29 处真实 appId"),
    "udc-bi-5.3.517": ("不收录", "含 CDP 抓包原文与客户组织名"),
    "udc-bi-5.3.260": ("不收录", "含环境域名与 17 处真实 appId"),
    "udc-menu-5.3.517": ("不收录", "含客户组织名；且菜单域按既定边界不推进"),
    "udc-entity-5.3.517": ("不收录", "含环境域名；实体域已有 core/facts/udc/entity 事实"),
    "udc-entity-customplan-5.3.517": ("不收录", "含环境域名"),
    "udc-page-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中，仅排除 2 个 LIVE-* 运行记录"),
    "udc-frontend-5.3.496": ("不收录", "单个 2.4 MB 压缩后的 redux store chunk，噪声大于信息"),
    "udc-frontend-ops": ("不收录", "含真实 appId 与客户组织名"),
    "udc-app-deploy-info-5.3.496": ("不收录", "20 处真实 appId + 真人名"),
    "udc-assemble-5.3.517-deployed": ("不收录", "含客户组织名与环境域名"),
    "u4-gateway": ("不收录", "含客户组织名 + 内网 IP"),
    "u5-storage": ("不收录", "含环境域名 + 5 处内网 IP"),
    "u6-nacos-config": ("不收录", "含客户组织名、环境域名、内网 IP"),
    "udc-web-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中：全部 Controller javap 单文件"),
    "udc-web-5.3.517-contracts": ("随仓库", "在 udc-platform-*.tar.gz 中：54 Controller / 674 端点的端点表"),
    "udc-web-5.3.517-methods": ("随仓库", "在 udc-platform-*.tar.gz 中：方法索引"),
    "udc-web-5.3.517-javap": ("不收录", "与 udc-web-5.3.517-contracts 内的 javap 同源重复，且含 1 处内网 IP"),
    "udc-runtime-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中：UdcBaseGeneralController / UdcRestPathParse"),
    "udc-runtime-5.3.517-javap": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "udc-resource-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "udc-publish-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中：页面/应用发布入口"),
    "udc-biz-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "udc-flow-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "udc-app-basic": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "udc-common-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "udc-user-5.3.517-contracts": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "extmetadata-5.3.318": ("随仓库", "在 udc-platform-*.tar.gz 中：UdcEntityMetaDataService 元数据契约"),
    "metadata-5.3.358": ("随仓库", "在 udc-platform-*.tar.gz 中：MetadataService / MetadataController"),
    "runtime-lowcode-5.3.517": ("随仓库", "在 udc-platform-*.tar.gz 中"),
    "udc-expression-functions.json": ("随仓库", "在 udc-platform-*.tar.gz 中：表达式函数树"),
    "udc-expression-system-variables.json": ("随仓库", "在 udc-platform-*.tar.gz 中：系统变量"),
    "udc-expression-samples.json": ("随仓库", "在 udc-platform-*.tar.gz 中：真实样本"),
    "udc-expression-schema-full.json": ("随仓库", "在 udc-platform-*.tar.gz 中：ENTITY / CONFIG_PARAM 结构"),
    "udc-expression-schema-paramtypes.json": ("随仓库", "在 udc-platform-*.tar.gz 中：参数类型"),
    "udc-expression-contracts.json": ("随仓库", "在 udc-platform-*.tar.gz 中：token 类型与可执行判定"),
    "udc-expression-functions-raw.json": ("不收录", "函数树原始中间件，已由 functions.json 结构化版本覆盖"),
    "mf_realdataschema.json": ("随仓库", "在 udc-platform-*.tar.gz 中：微流程节点真实 io schema"),
    "udc-entity-to-ctpenum-mechanism-20261013.md": ("随仓库", "在 udc-platform-*.tar.gz 中：关联字段→枚举切换机制"),
    "s7_w1_result.json": ("不收录", "一次性实测返回（建单结果 id），结论已入 core/facts"),
    "s7_w3_result.json": ("不收录", "一次性实测返回（建页结果 id），结论已入 core/facts"),
    "README.md": ("不收录", "描述的是完整 409 MB 证据根，与分发形态不符；分发说明见 REGENERATE-EVIDENCE.md"),
}


def _scan(path: Path) -> dict:
    """统计体积/文件数并做客户痕迹扫描（大文件只抽样头部）。"""
    files = [p for p in (path.rglob("*") if path.is_dir() else [path]) if p.is_file()]
    size = sum(f.stat().st_size for f in files)
    hits: dict[str, int] = {}
    for f in files:
        try:
            with f.open("rb") as fh:
                raw = fh.read(SAMPLE_BYTES)
        except OSError:
            continue
        text = raw.decode("utf-8", errors="ignore")
        for label, rx in FORBIDDEN.items():
            if rx.search(text):
                hits[label] = hits.get(label, 0) + 1
    return {"files": len(files), "size_mb": round(size / 1024 / 1024, 2), "hits": hits}


def collect() -> list[dict]:
    rows: list[dict] = []
    if not ARTIFACTS.exists():
        return rows
    for p in sorted(ARTIFACTS.iterdir()):
        rel = p.name
        stat = _scan(p)
        policy, reason = EXPORT_POLICY.get(rel, ("未判定", "需要人工裁决"))
        rows.append({"name": rel, "kind": "dir" if p.is_dir() else "file",
                     **stat, "policy": policy, "reason": reason})
    return rows


def render(rows: list[dict], extra: list[dict]) -> str:
    total_mb = sum(r["size_mb"] for r in rows)
    by: dict[str, list[dict]] = {}
    for r in rows + extra:
        by.setdefault(r["policy"], []).append(r)

    lines = [
        "# 资产清单（哪些进仓库、哪些不进）",
        "",
        "> 自动生成，勿手改。`python tools/inventory_assets.py` 重跑。",
        "> 体积与客户痕迹计数从磁盘现算；判定口径见脚本 `EXPORT_POLICY`。",
        "",
        f"- `docs/audit/artifacts` 合计 **{total_mb:.1f} MB** / {len(rows)} 项",
        f"- 随仓库 **{len(by.get('随仓库', []))}** 项 · 可重建 **{len(by.get('可重建', []))}** 项 · "
        f"不收录 **{len(by.get('不收录', []))}** 项 · 未判定 **{len(by.get('未判定', []))}** 项",
        "",
        "## 一、随仓库（clone 就有）",
        "",
        "| 资产 | 体积 | 文件 | 说明 |",
        "|---|---|---|---|",
    ]
    for r in sorted(by.get("随仓库", []), key=lambda x: -x["size_mb"]):
        lines.append(f"| `{r['name']}` | {r['size_mb']:.2f} MB | {r['files']} | {r['reason']} |")

    lines += ["", "## 二、可重建（不随仓库，一条命令重造）", "",
              "| 资产 | 原体积 | 文件 | 重建方式 |", "|---|---|---|---|"]
    for r in sorted(by.get("可重建", []), key=lambda x: -x["size_mb"]):
        lines.append(f"| `{r['name']}` | {r['size_mb']:.2f} MB | {r['files']} | {r['reason']} |")

    lines += ["", "## 三、不收录（含客户痕迹或纯噪声）", "",
              "| 资产 | 体积 | 文件 | 客户痕迹 | 原因 |", "|---|---|---|---|---|"]
    for r in sorted(by.get("不收录", []), key=lambda x: -x["size_mb"]):
        hits = "、".join(f"{k}×{v}" for k, v in r["hits"].items()) or "—"
        lines.append(f"| `{r['name']}` | {r['size_mb']:.2f} MB | {r['files']} | {hits} | {r['reason']} |")

    if by.get("未判定"):
        lines += ["", "## 四、未判定（要人工裁决）", ""]
        for r in sorted(by["未判定"], key=lambda x: -x["size_mb"]):
            hits = "、".join(f"{k}×{v}" for k, v in r["hits"].items()) or "—"
            lines.append(f"- `{r['name']}` — {r['size_mb']:.2f} MB / {r['files']} 文件 / 痕迹 {hits}")

    lines += ["", "## 五、仓库外的排除项", "",
              "| 位置 | 原因 |", "|---|---|"]
    for r in extra:
        lines.append(f"| `{r['name']}` | {r['reason']} |")

    lines += ["", "## 六、一句话重建全部证据", "", "```bash",
              "python tools/regen_evidence.py          # 抽取 + 聚合 + 签名索引",
              "python tools/build_reference_bundle.py --profile core",
              "python tools/build_reference_bundle.py --profile surface",
              "python tools/build_app_service_index.py",
              "python tools/build_component_index.py --modules <pc/node_modules>",
              "```", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="盘点分发资产")
    ap.add_argument("--check", action="store_true", help="存在未判定项则非零退出")
    a = ap.parse_args(argv)

    rows = collect()
    if not rows and not a.check:
        # 分发树里没有 docs/audit/artifacts（按设计排除），此时不许把清单覆盖成空表：
        # 那份清单描述的是「完整证据根怎么取舍」，只能在有证据的开发仓生成。
        print("[x] 本仓库没有 docs/audit/artifacts，拒绝覆盖现有清单。\n"
              "    这份清单需在带完整证据的仓里生成，见 REGENERATE-EVIDENCE.md。")
        return 2
    extra = [
        {"name": "docs/audit/evidence/", "policy": "不收录", "files": 0, "size_mb": 0.0, "hits": {},
         "reason": "客户业务证据（截图/回读记录），脱敏后也失去证据价值"},
        {"name": "core/facts/**/evidence/（已脱敏的部分除外）", "policy": "随仓库", "files": 0,
         "size_mb": 0.0, "hits": {}, "reason": "305 个事实依据文件已脱敏入仓"},
        {"name": "tools/core/feishu/", "policy": "不收录", "files": 0, "size_mb": 0.0, "hits": {},
         "reason": "一次性排障脚本，硬编码真实飞书 TOKEN，运行时 0 引用"},
        {"name": "skills/06-delivery/<客户项目>-pmp/", "policy": "不收录", "files": 0, "size_mb": 0.0,
         "hits": {}, "reason": "客户项目专属 skill"},
        {"name": "docs/audit/column-discovery/raw-nav-capture-*.json", "policy": "不收录", "files": 0,
         "size_mb": 0.0, "hits": {}, "reason": "页面导航抓包含 42 处真实操作人姓名"},
    ]
    md = render(rows, extra)
    MD_OUT.write_text(md, encoding="utf-8")
    JSON_OUT.write_text(json.dumps({"artifacts": rows, "outside": extra}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    undecided = [r for r in rows if r["policy"] == "未判定"]
    print(f"[ok] {MD_OUT}  ({len(rows)} 项 / {sum(r['size_mb'] for r in rows):.1f} MB)")
    print(f"[ok] {JSON_OUT}")
    if undecided:
        print(f"[!] {len(undecided)} 项未判定：")
        for r in undecided:
            print("    -", r["name"], f"{r['size_mb']:.2f} MB")
        if a.check:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
