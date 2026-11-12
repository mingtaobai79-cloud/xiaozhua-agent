# -*- coding: utf-8 -*-
"""反编译加签识别相关的枚举/常量/DTO + 检查事件基类是否携带加签信息。"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

JAR = Path(r"<MAVEN_REPO>/com/seeyon/bpm-facade/5.3.374/bpm-facade-5.3.374.jar")
CFR = Path(r"<HERMES_HOME>/skills/software-development/seeyon-v8-spi/seeyon-v8-spi/references/contract-index/tools/cfr.jar")
OUT = Path(r"<SEEYON_AGENT_ROOT>/docs/audit/modules/decompiled/bpm-addsign")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    "com/seeyon/bpm/enums/ChangeTypeEnum.class",
    "com/seeyon/bpm/dto/OperateTypeEnum.class",
    "com/seeyon/bpm/dto/BpmConstants.class",
    "com/seeyon/bpm/constants/BpmConstants.class",
    "com/seeyon/bpm/dto/LogActionDetailOperationConstants.class",
    "com/seeyon/bpm/dto/BpmSendUdcDto.class",
    "com/seeyon/bpm/dto/BpmOperationNodeDto.class",
    "com/seeyon/bpm/dto/BpmNodePermissionResponseDto.class",
    "com/seeyon/bpm/dto/ChangeNodeRequestDto.class",
    "com/seeyon/bpm/dto/message/event/BpmBaseEvent.class",
]

ESC = re.compile(r"\\u([0-9a-fA-F]{4})")
def unesc(s):
    return ESC.sub(lambda m: chr(int(m.group(1), 16)), s)

with zipfile.ZipFile(JAR) as z:
    names = set(z.namelist())
    tmp = Path(tempfile.mkdtemp())
    for t in TARGETS:
        if t not in names:
            # 容错：按类名模糊找
            stem = Path(t).stem
            cands = [n for n in names if n.endswith(f"/{stem}.class")]
            if not cands:
                print(f"[未找到] {t}")
                continue
            t = cands[0]
        z.extract(t, tmp)
        r = subprocess.run(["java", "-jar", str(CFR), str(tmp / t)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        src = unesc(r.stdout)
        f = OUT / (Path(t).stem + ".java")
        f.write_text(r.stdout, encoding="utf-8")          # 存原始（保留转义）
        (OUT / (Path(t).stem + ".unescaped.java")).write_text(src, encoding="utf-8")
        print(f"\n{'='*72}\n### {Path(t).stem}   ({len(src)} 字符)\n{'='*72}")
        # 只打印与加签/常量/枚举值相关的行
        keep = []
        for line in src.splitlines():
            if re.search(r"加签|减签|会签|ADD_NODE|NODE_ADD|OPERATE_|ChangeTypeEnum|^\s+[A-Z_]+\(|public |static final|enum ", line):
                keep.append(line.rstrip())
        print("\n".join(keep[:60]) if keep else "（无匹配行，完整文件已存盘）")
