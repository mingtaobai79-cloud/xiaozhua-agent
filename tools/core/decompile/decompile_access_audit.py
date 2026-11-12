# -*- coding: utf-8 -*-
"""查 boot-starter-web 的 AccessAuditLg 里"加签"是干什么的（访问审计日志是否记录加签操作）"""
import io
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/bpm-addsign")
ESC = re.compile(r"\\u([0-9a-fA-F]{4})")
u = lambda s: ESC.sub(lambda m: chr(int(m.group(1), 16)), s)

JAR = Path(r"<MAVEN_REPO>/com/seeyon/boot-starter-web/5.3.358/boot-starter-web-5.3.358.jar")
with zipfile.ZipFile(JAR) as z:
    ent = [n for n in z.namelist() if Path(n).name == "AccessAuditLg.class"]
    print("条目:", ent)
    if ent:
        tmp = Path(tempfile.mkdtemp())
        z.extract(ent[0], tmp)
        r = subprocess.run(["java", "-jar", str(CFR), str(tmp / ent[0])],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        src = u(r.stdout)
        (OUT / "AccessAuditLg.java").write_text(src, encoding="utf-8")
        print(f"反编译 {len(src)} 字符\n")
        # 找含"加签"的位置及其上下文
        for m in re.finditer("加签", src):
            i = m.start()
            print("…", src[max(0, i - 260):i + 160].replace("\r", "").replace("\n", " ")[-420:])
            print("-" * 60)
        # 顺带看有哪些操作类型的常量
        print("\n=== 常量/枚举相关行 ===")
        for line in src.splitlines():
            if re.search(r"static final|enum |OPERATION|Operation|OPERATE|String [A-Z_]+ =", line):
                print("   ", line.strip()[:150])
