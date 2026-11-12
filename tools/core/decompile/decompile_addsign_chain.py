# -*- coding: utf-8 -*-
"""拆 SimpleChangeProcessRequestDto（加签/会签 API 的入参）与 UDC 侧 ApproveFeatureService（加签/减签桥接）"""
import subprocess
import tempfile
import zipfile
from pathlib import Path

CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/bpm-addsign")

JOBS = [
    (r"<MAVEN_REPO>/com/seeyon/bpm-facade/5.3.374/bpm-facade-5.3.374.jar",
     "com/seeyon/bpm/dto/SimpleChangeProcessRequestDto.class"),
    (r"<MAVEN_REPO>/com/seeyon/bpm-facade/5.3.374/bpm-facade-5.3.374.jar",
     "com/seeyon/bpm/api/common/BpmAppService.class"),
    (r"<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.496/udc-starter-runtime-5.3.496.jar",
     "com/seeyon/boot/starter/udcrt/domain/service/ApproveFeatureService.class"),
    (r"<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar",
     "com/seeyon/boot/starter/udcrt/domain/service/ApproveFeatureService.class"),
]

for jar_path, entry in JOBS:
    jar = Path(jar_path)
    if not jar.exists():
        # 版本目录可能不同，找同 artifact 下最新版本
        base = jar.parent.parent
        cands = sorted(base.glob("*/" + jar.name.replace(jar.parent.name + "-", "").replace("-5.3.517", "")))
        print(f"[跳过] 不存在: {jar}")
        continue
    with zipfile.ZipFile(jar) as z:
        if entry not in z.namelist():
            print(f"[缺失条目] {entry} in {jar.name}")
            continue
        tmp = Path(tempfile.mkdtemp())
        z.extract(entry, tmp)
        r = subprocess.run(["java", "-jar", str(CFR), str(tmp / entry)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        ver = jar.parent.name
        name = f"{Path(entry).stem}.{ver}.java"
        (OUT / name).write_text(r.stdout, encoding="utf-8")
        print(f"[OK] {name}  {len(r.stdout)} 字符")
