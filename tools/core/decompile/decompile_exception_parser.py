# -*- coding: utf-8 -*-
"""反编译 appservice 异常解析链：谁把 SQL 1062 翻译成 error.code.PRIMARY("违反主键约束")。"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
ROOT = Path(r"<MAVEN_REPO>/com/seeyon")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/platform-appservice-ex")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = ["MysqlExceptionParser", "DBExceptionParser", "ExceptionTransfer"]
jars = sorted((ROOT / "boot-starter-appservice").rglob("5.3.358/*.jar")) or list((ROOT / "boot-starter-appservice").rglob("*.jar"))
print("jars:", [j.name for j in jars])

found = {}
for j in jars:
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
                       encoding="utf-8", errors="replace", timeout=600)
    src = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), r.stdout)
    (OUT / (stem + ".java")).write_text(src, encoding="utf-8")
    print("=" * 96)
    print("### %s  (%d chars)  <- %s" % (stem, len(src), j.name))
    for i, l in enumerate(src.splitlines(), 1):
        if re.search(r"PRIMARY|1062|Duplicate|Constraint|error\.code|ErrorCode|parse|return ", l):
            print("  %5d| %s" % (i, l.strip()[:190]))
