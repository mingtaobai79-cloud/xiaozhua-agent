# -*- coding: utf-8 -*-
"""反编译 bpm-facade 里加签相关的关键类，回答"怎么识别 / 有没有发消息 / 哪个字段能读到"。

输出目录：docs/audit/modules/decompiled/bpm-addsign/
"""
import subprocess
import tempfile
import zipfile
from pathlib import Path

JAR = Path(r"<MAVEN_REPO>/com/seeyon/bpm-facade/5.3.374/bpm-facade-5.3.374.jar")
CFR = Path(r"<HERMES_HOME>/skills/software-development/xiaozhua-v8-spi/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar")
OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/modules/decompiled/bpm-addsign")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    "com/seeyon/bpm/dto/message/BpmMqDataType.class",
    "com/seeyon/bpm/dto/message/BpmMqData.class",
    "com/seeyon/bpm/api/ext/activity/BpmSupportOperation.class",
    "com/seeyon/bpm/dto/ChangeNodeRequestDto.class",
    "com/seeyon/bpm/dto/ChangeNodeResponseDto.class",
    "com/seeyon/bpm/dto/ChangeNodeLogDto.class",
    "com/seeyon/bpm/dto/AddNodeParameterDto.class",
    "com/seeyon/bpm/dto/AddNodePerson.class",
    "com/seeyon/bpm/dto/AddNodeOrgInfoDto.class",
    "com/seeyon/bpm/dto/AddNodeProcessTermParameterDto.class",
    "com/seeyon/bpm/dto/SimpleChangeNodeParameterDto.class",
    "com/seeyon/bpm/api/common/BpmActionAppService.class",
    "com/seeyon/bpm/dto/message/event/BpmBaseEvent.class",
    "com/seeyon/bpm/dto/message/event/BpmStepbackEvent.class",
    "com/seeyon/bpm/api/udc/BpmUdcApiService.class",
]

with zipfile.ZipFile(JAR) as z:
    present = set(z.namelist())
    tmp = Path(tempfile.mkdtemp())
    for t in TARGETS:
        if t not in present:
            print(f"[缺失] {t}")
            continue
        z.extract(t, tmp)
        cls = tmp / t
        r = subprocess.run(["java", "-jar", str(CFR), str(cls)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        out_file = OUT / (Path(t).stem + ".java")
        out_file.write_text(r.stdout, encoding="utf-8")
        print(f"[OK] {Path(t).stem}.java  {len(r.stdout)} 字符  {out_file}")
