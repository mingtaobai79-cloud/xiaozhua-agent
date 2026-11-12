# -*- coding: utf-8 -*-
"""把 bpm-facade 里所有 api/ 接口反编译，找出哪个方法接收 AddNode*/ChangeNode* 参数。

这一步回答"加签走哪条 API 链"，并给出可监听/可校验的接口落点。
"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

JAR = Path(r"<MAVEN_REPO>/com/seeyon/bpm-facade/5.3.374/bpm-facade-5.3.374.jar")
CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/bpm-addsign/api")
OUT.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(JAR) as z:
    apis = [n for n in z.namelist() if n.startswith("com/seeyon/bpm/api/") and n.endswith(".class")]
    print(f"api 接口/类: {len(apis)} 个，开始反编译…")
    tmp = Path(tempfile.mkdtemp())
    found = []
    for n in apis:
        z.extract(n, tmp)
        r = subprocess.run(["java", "-jar", str(CFR), str(tmp / n)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        src = r.stdout
        (OUT / (Path(n).stem + ".java")).write_text(src, encoding="utf-8")
        for m in re.finditer(r"^\s*(?:public\s+)?[\w<>,\[\]\. ]+\s+(\w*(?:AddNode|ChangeNode|Node)\w*)\s*\(([^)]*)\)",
                             src, re.M):
            found.append((Path(n).stem, m.group(1), " ".join(m.group(2).split())[:120]))

print(f"\n=== 与节点变更/加签相关的方法签名（{len(found)} 条）===")
for cls, method, params in found:
    print(f"  {cls}.{method}({params})")
