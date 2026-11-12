#!/usr/bin/env python3
"""从 Artifactory libs-release 下载 com.seeyon 的实现 jar（*-biz 等）。

为什么：仓库里 <MAVEN_REPO> 只有 facade/api jar（接口），业务实现在 *-biz 构件里。
没有实现 jar 就追不到业务流转（322 个 AppService 只有 68 个能追）。

仓库实测：无 -sources.jar（搜索返回空），只有 class jar → 下 class jar 反编译。

用法：
  python tools/core/platform/fetch_biz_jars.py --base http://10.0.0.1/artifactory/libs-release/com/seeyon \
      --out <MAVEN_REPO>-extra [--pkgs bpm-biz organization-biz ...]
"""
from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

UA = {"User-Agent": "xiaozhua-agent/0.1 (audit)"}
RE_VER = re.compile(r'href="(\d+\.\d+(?:\.\d+)*)/"')


def get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def latest_version(base: str, pkg: str) -> str | None:
    try:
        html = get(f"{base}/{pkg}/").decode("utf-8", "replace")
    except Exception as e:
        print(f"  ERR {pkg}: {e}")
        return None
    vs = RE_VER.findall(html)
    if not vs:
        return None
    return sorted(vs, key=lambda v: [int(x) for x in v.split(".")])[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pkgs", nargs="*", default=None)
    a = ap.parse_args()

    pkgs = a.pkgs or [
        "bpm-biz", "organization-biz", "ctp-affair-biz", "ctp-user-biz", "ctp-message-biz",
        "ctp-media-biz", "cip-capability-biz", "cip-connector-biz", "cip-convert-biz",
        "cip-manager-biz", "cip-openapi-gateway-biz", "app-approval-biz", "app-common-biz",
        "app-doc-biz", "cdp-data-biz", "cdp-schedule-biz", "m5-biz", "portal-biz",
        "ai-biz", "udc-biz", "ctp-webapi-gateway-biz",
    ]
    out = Path(a.out)
    ok, fail = [], []
    for pkg in pkgs:
        ver = latest_version(a.base, pkg)
        if not ver:
            print(f"  跳过 {pkg}（无版本）")
            fail.append((pkg, "无版本"))
            continue
        d = out / pkg / ver
        d.mkdir(parents=True, exist_ok=True)
        jar = d / f"{pkg}-{ver}.jar"
        if jar.exists() and jar.stat().st_size > 1000:
            print(f"  已有 {pkg}-{ver}.jar（{jar.stat().st_size//1024} KB）")
            ok.append((pkg, ver, jar.stat().st_size))
            continue
        url = f"{a.base}/{pkg}/{ver}/{pkg}-{ver}.jar"
        try:
            data = get(url, timeout=300)
        except Exception as e:
            print(f"  ERR {pkg}-{ver}: {e}")
            fail.append((pkg, str(e)))
            continue
        jar.write_bytes(data)
        print(f"  下载 {pkg}-{ver}.jar（{len(data)//1024} KB）")
        ok.append((pkg, ver, len(data)))

    print(f"\n成功 {len(ok)} / 失败 {len(fail)}")
    total = sum(s for _, _, s in ok)
    print(f"合计 {total//1024//1024} MB → {out}")
    if fail:
        for p, why in fail:
            print(f"  失败 {p}: {why}")
    if len(ok) < 10:
        print("ERR: 下载成功的过少")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
