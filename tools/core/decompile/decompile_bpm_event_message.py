# -*- coding: utf-8 -*-
"""按 basename 定位并反编译 Message 类 + MessageInfo 注解全文，确认 MQ 信封与 payload。"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/bpm-addsign")
ESC = re.compile(r"\\u([0-9a-fA-F]{4})")
u = lambda s: ESC.sub(lambda m: chr(int(m.group(1), 16)), s)
FAC = Path(r"<MAVEN_REPO>/com/seeyon/bpm-facade/5.3.374/bpm-facade-5.3.374.jar")
BOOT = Path(r"<MAVEN_REPO>/com/seeyon/boot-core/5.3.358/boot-core-5.3.358.jar")

with zipfile.ZipFile(FAC) as z:
    ent = z.namelist()
    msgs = [n for n in ent if Path(n).name.endswith("Message.class")]
    print("=== bpm-facade 里 *Message.class 的包分布 ===")
    from collections import Counter
    for p, c in Counter(str(Path(n).parent) for n in msgs).most_common():
        print(f"   {p}: {c}")
    print("   示例:", [n for n in msgs if "Submit" in n][:4])
    # Message 类与 Event 类的配对关系：看是否同名成对
    evs = {Path(n).name for n in ent if "/event/" in n and n.endswith("Event.class")}
    print("\n=== Event 类总数:", len(evs))

    want = ["BpmSubmitEventMessage.class", "BpmStepBackEventMessage.class", "BpmTransferEventMessage.class"]
    for w in want:
        hit = [n for n in msgs if Path(n).name == w]
        if not hit:
            print(f"!! 未找到 {w}")
            continue
        p = Path(tempfile.mkdtemp()) / w
        p.write_bytes(z.read(hit[0]))
        r = subprocess.run(["java", "-jar", str(CFR), str(p)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=240)
        src = u(r.stdout)
        (OUT / w.replace(".class", ".java")).write_text(src, encoding="utf-8")
        print("=" * 78)
        print(f"### {w}  ← {hit[0]}")
        for line in src.splitlines():
            s = line.strip()
            if s.startswith(("@MessageInfo", "@Message", "@DtoInfo", "public class", "public abstract class",
                             "private ", "protected ")) or "extends" in s and "class" in s:
                print("   ", s[:220])

# MessageInfo 注解属性
with zipfile.ZipFile(BOOT) as zb:
    p = Path(tempfile.mkdtemp()) / "MessageInfo.class"
    p.write_bytes(zb.read("com/seeyon/boot/annotation/MessageInfo.class"))
r = subprocess.run(["java", "-jar", str(CFR), str(p)], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=240)
src = u(r.stdout)
(OUT / "MessageInfo.annotation.java").write_text(src, encoding="utf-8")
print("=" * 78)
print("### @MessageInfo 注解定义全文")
print(src.strip()[:2200])
