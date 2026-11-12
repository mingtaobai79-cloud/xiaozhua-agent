# -*- coding: utf-8 -*-
"""在多个 maven 仓库根中搜索中文文案"违反主键约束/主键约束"及其 \\uXXXX 转义形式。
输出 jar::entry，用于判定报错组件来源。"""
import pathlib
import sys
import zipfile

ROOTS = [pathlib.Path(p) for p in sys.argv[1:]] or [
    pathlib.Path("D:/repo-seeyon"),
    pathlib.Path("D:/maven"),
]
TEXT_EXT = (".class", ".properties", ".json", ".js", ".xml", ".sql", ".txt", ".vm", ".html",
            ".ftl", ".yaml", ".yml", ".jsp", ".tag")
NEEDLES = ["主键","违反","重复数据","唯一校验","唯一约束",



    "\\u8fdd\\u53cd\\u4e3b\\u952e",
    "\\u8FDD\\u53CD\\u4E3B\\u952E",
    "Duplicate entry",
]


def main():
    total = 0
    hits = {}
    for R in ROOTS:
        if not R.exists():
            print("skip (not found):", R)
            continue
        for j in R.rglob("*.jar"):
            if "-sources" in j.name or "-javadoc" in j.name:
                continue
            total += 1
            try:
                with zipfile.ZipFile(j) as z:
                    for i in z.infolist():
                        if i.file_size > 6_000_000:
                            continue
                        if not i.filename.lower().endswith(TEXT_EXT):
                            continue
                        try:
                            b = z.read(i)
                        except Exception:
                            continue
                        for nd in NEEDLES:
                            if nd.encode("utf-8") in b:
                                hits.setdefault(nd, []).append("%s :: %s" % (j, i.filename))
                                break
            except Exception:
                continue
    print("scanned_jars=", total)
    for nd, lst in hits.items():
        print("### needle=%r  hits=%d" % (nd, len(lst)))
        for h in lst[:25]:
            print("   ", h)


if __name__ == "__main__":
    main()
