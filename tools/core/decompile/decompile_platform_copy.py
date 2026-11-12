# -*- coding: utf-8 -*-
"""反编译平台侧 BaseEntityCurdService / UdcMethod2ActionUtil，看复制时主键与 ActionType 处理。"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
ROOT = Path(r"<MAVEN_REPO>/com/seeyon")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/platform-copy")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ("udc-starter-lowcode/5.3.517/udc-starter-lowcode-5.3.517.jar",
     "com/seeyon/boot/starter/lowcode/service/BaseEntityCurdService.class"),
    ("boot-starter-extmetadata/5.3.318/boot-starter-extmetadata-5.3.318.jar",
     "com/seeyon/boot/starter/extmetadata/utils/UdcMethod2ActionUtil.class"),
]

for rel, entry in TARGETS:
    jar = ROOT / rel
    if not jar.exists():
        print("缺 jar:", jar)
        continue
    with zipfile.ZipFile(jar) as z:
        data = z.read(entry)
    p = Path(tempfile.mkdtemp()) / Path(entry).name
    p.write_bytes(data)
    r = subprocess.run(["java", "-jar", str(CFR), str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=420)
    src = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), r.stdout)
    out = OUT / (Path(entry).stem + ".java")
    out.write_text(src, encoding="utf-8")
    print("=" * 96)
    print("### %s  (%d 字符) -> %s" % (entry, len(src), out))
    for i, l in enumerate(src.splitlines(), 1):
        if re.search(r"runtimeCopy|copyAndInsert|setId\(|IdGenerator|snowflake|Snowflake|序列|主键|ActionType|INSERT|copy", l):
            print("  %5d| %s" % (i, l.strip()[:210]))
