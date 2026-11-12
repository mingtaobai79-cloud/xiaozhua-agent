# -*- coding: utf-8 -*-
"""反编译 DtoFieldHelper / DtoConvertUtil / handlerCaseId，判定插入时主键如何生成。"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
ROOT = Path(r"<MAVEN_REPO>/com/seeyon")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/platform-copy")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = ["DtoFieldHelper", "DtoConvertUtil"]
JARS = [j for j in (ROOT / "udc-starter-lowcode").rglob("5.3.517/*.jar")]
if not JARS:
    JARS = list((ROOT / "udc-starter-lowcode").rglob("*.jar"))
print("jar:", [j.name for j in JARS])

found = {}
for j in JARS:
    with zipfile.ZipFile(j) as z:
        for n in z.namelist():
            if n.endswith(".class") and Path(n).stem in TARGETS:
                found.setdefault(Path(n).stem, (j, n))

for stem, (j, n) in found.items():
    with zipfile.ZipFile(j) as z:
        data = z.read(n)
    p = Path(tempfile.mkdtemp()) / Path(n).name
    p.write_bytes(data)
    r = subprocess.run(["java", "-jar", str(CFR), str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=420)
    src = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), r.stdout)
    (OUT / (stem + ".java")).write_text(src, encoding="utf-8")
    print("=" * 94)
    print("### %s (%d 字符) from %s" % (stem, len(src), j.name))
    for i, l in enumerate(src.splitlines(), 1):
        if re.search(r"resetId|resetInsert|resetChildNormal|setId\(|gidLong|Ids\.|id\b", l):
            print("  %5d| %s" % (i, l.strip()[:200]))
