#!/usr/bin/env python3
"""构建 UDC 平台参考包（docs/audit/reference/udc-platform-*.tar.gz）。

为什么要有这个脚本，而不是手工 tar：参考包是对外分发物，必须能复现、能审。
每次重建都走同一套「收录清单 + 排除规则 + 脱敏表」，避免下一次手工打包把
客户域名/appId 又带进去。

收录判据：
  1. 对 UDC 自定义页面 / 微流程 / 扩展开发有直接作用（Controller javap、
     端点表、元数据契约、表达式函数与系统变量）
  2. 不含客户痕迹；有则先脱敏，脱不干净就整文件排除

用法：
    python tools/build_reference_bundle.py                     # 构建并打印清单
    python tools/build_reference_bundle.py --check             # 只报告哪些文件会被排除
"""
from __future__ import annotations

import argparse
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "docs" / "audit" / "artifacts"
OUT = ROOT / "docs" / "audit" / "reference" / "udc-platform-5.3.517.tar.gz"
OUT_SURFACE = ROOT / "docs" / "audit" / "reference" / "surface-index.tar.gz"

# 整目录收录（机器生成的 javap / 端点表，无客户数据）
DIRS = [
    "udc-web-5.3.517",              # 全部 Controller javap
    "udc-web-5.3.517-contracts",    # 端点表 _api_full.json（54 Controller / 674 端点）
    "udc-web-5.3.517-methods",
    "udc-runtime-5.3.517",
    "udc-runtime-5.3.517-javap",
    "udc-resource-5.3.517",
    "udc-publish-5.3.517",
    "udc-biz-5.3.517",
    "udc-flow-5.3.517",
    "udc-app-basic",
    "udc-common-5.3.517",
    "udc-user-5.3.517-contracts",
    "extmetadata-5.3.318",          # UdcEntityMetaDataService
    "metadata-5.3.358",             # MetadataService / MetadataController
    "runtime-lowcode-5.3.517",
    "udc-page-5.3.517",             # 自定义页面：UdcBaseGeneralController 等
]

# 单文件收录（表达式：微流程表达式绑定要用）
FILES = [
    "udc-expression-functions.json",
    "udc-expression-system-variables.json",
    "udc-expression-schema-full.json",
    "udc-expression-schema-paramtypes.json",
    "udc-expression-contracts.json",
    "udc-expression-samples.json",
]

# ---------------------------------------------------------------- 第二份：查具体东西
# 「这个 DTO 有哪些字段」「这个接口的实现类是哪个」「UDC 能扩展哪些点」
# —— 这些是 agent 干活时真正要落地的东西，体积小（7.6MB），必须随仓库走。
SURFACE_ROOT = "extension-surface-20261029"
SURFACE_DIRS = ["domains", "dto-fields", "packages"]
SURFACE_FILES = [
    "action-index.md",          # 接口 → 实现类 + 入参 DTO
    "annotations.md",
    "constants.md",
    "consumers.json",           # 谁在消费这些接口
    "dto-meta.json",            # DTO 元数据（含字段示例）
    "dto-validations.json",
    "extension-points.md",      # 扩展点清单
    "impl-map.json",            # 接口 → 实现映射
    "interface-inventory.md",   # 1457 个接口人读清单
    "registration-scan.json",
    "subtype-discovery.json",
    "symbols-udc-extend.json",      # UDC 扩展 API 符号
    "symbols-udc-plugin-api.json",  # UDC 插件 API 符号
]

# 整文件排除：LIVE-* 是真实环境跑批记录，含客户域名 / app_id / 凭据路径，
# 脱敏后也失去证据价值（记的是「哪个环境哪次跑」），直接不收。
EXCLUDE_NAME_RX = re.compile(r"^LIVE-", re.I)

# 脱敏表：命中的文本文件先替换再入包
SCRUBS = [
    (re.compile("lowcode-" + "test" + "2." + "chang" + "hong" + "it\\.com", re.I), "lowcode.example.com"),
    (re.compile(r"8704025620829192834"), "app0000000000000000"),
    (re.compile(r"163126498398523384"), "app0000000000000001"),
    (re.compile(r"6419954374508955097"), "app0000000000000002"),
    (re.compile("chang" + "hong", re.I), "customer"),
    (re.compile(r"10\.3\.4\.157"), "10.0.0.1"),
    (re.compile("\u957f\u8679"), "客户"),
    (re.compile("\u767d\u660e\u6d9b"), "zhangsan"),
    (re.compile(r"test2"), "测试环境"),
]

TEXT_EXT = {".json", ".md", ".txt", ".javap", ".csv", ".yaml", ".yml", ".properties"}


def _scrub_bytes(data: bytes, name: str) -> tuple[bytes, int]:
    if Path(name).suffix.lower() not in TEXT_EXT:
        return data, 0
    try:
        t = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, 0
    hits = 0
    for rx, rep in SCRUBS:
        t, n = rx.subn(rep, t)
        hits += n
    return t.encode("utf-8"), hits


def collect(profile: str = "core") -> tuple[list[tuple[Path, str]], dict]:
    items: list[tuple[Path, str]] = []
    stats = {"files": 0, "skipped": [], "scrubbed": 0, "raw": 0}

    if profile == "surface":
        base = ART / SURFACE_ROOT
        for d in SURFACE_DIRS:
            root = base / d
            if not root.exists():
                stats["skipped"].append(f"{d}（不存在）")
                continue
            for f in sorted(root.rglob("*")):
                if f.is_file():
                    items.append((f, f"{d}/{f.relative_to(root).as_posix()}"))
        for name in SURFACE_FILES:
            f = base / name
            if not f.exists():
                stats["skipped"].append(f"{name}（不存在）")
                continue
            items.append((f, name))
        stats["files"] = len(items)
        return items, stats

    for d in DIRS:
        root = ART / d
        if not root.exists():
            stats["skipped"].append(f"{d}（不存在）")
            continue
        for f in sorted(root.rglob("*")):
            if not f.is_file():
                continue
            if EXCLUDE_NAME_RX.match(f.name):
                stats["skipped"].append(f"{d}/{f.name}")
                continue
            items.append((f, f"{d}/{f.relative_to(root).as_posix()}"))
    for name in FILES:
        f = ART / name
        if not f.exists():
            stats["skipped"].append(f"{name}（不存在）")
            continue
        items.append((f, name))
    stats["files"] = len(items)
    return items, stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="构建 UDC 平台参考包")
    ap.add_argument("--out", default="")
    ap.add_argument("--profile", default="core", choices=["core", "surface"],
                    help="core=平台契约包；surface=DTO字段/实现类/扩展点")
    ap.add_argument("--check", action="store_true", help="只报告收录/排除清单，不写包")
    a = ap.parse_args(argv)

    items, stats = collect(a.profile)
    raw = sum(p.stat().st_size for p, _ in items) / 1024 / 1024
    print(f"[*] 收录 {stats['files']} 个文件 / 原始 {raw:.1f} MB")
    if stats["skipped"]:
        print(f"[*] 排除 {len(stats['skipped'])} 个：")
        for s in stats["skipped"][:10]:
            print("    -", s)
    if a.check:
        return 0

    out = Path(a.out) if a.out else (OUT_SURFACE if a.profile == "surface" else OUT)
    out.parent.mkdir(parents=True, exist_ok=True)
    scrubbed = 0
    with tarfile.open(out, "w:gz", compresslevel=9) as tf:
        for src, arcname in items:
            data = src.read_bytes()
            data, n = _scrub_bytes(data, src.name)
            scrubbed += n
            info = tarfile.TarInfo(arcname)
            info.size = len(data)
            info.mtime = int(src.stat().st_mtime)
            import io
            tf.addfile(info, io.BytesIO(data))
    print(f"[ok] {out}  {out.stat().st_size/1024/1024:.2f} MB "
          f"(压缩比 {100*out.stat().st_size/(raw*1024*1024):.0f}%) / 脱敏 {scrubbed} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
