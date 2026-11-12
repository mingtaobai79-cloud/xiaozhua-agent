# -*- coding: utf-8 -*-
"""在本地 Maven 仓库中定位中文错误文案的产出 jar/资源（判定报错组件来源）。
用法: python scan_jar_text.py "违反主键约束"
"""
import sys, zipfile, pathlib, io

ROOT = pathlib.Path("<MAVEN_REPO>/com/seeyon")
NEEDLES = [n.encode("utf-8") for n in (sys.argv[1:] or ["违反主键约束"])]
EXT_OK = (".class", ".properties", ".json", ".js", ".xml", ".txt", ".sql", ".yaml", ".yml", ".vue")


def main():
    hits, scanned, entries = [], 0, 0
    for jar in sorted(ROOT.rglob("*.jar")):
        if "-sources" in jar.name or "-javadoc" in jar.name:
            continue
        scanned += 1
        try:
            with zipfile.ZipFile(jar) as z:
                for info in z.infolist():
                    if info.file_size > 3_000_000 or not info.filename.lower().endswith(EXT_OK):
                        continue
                    entries += 1
                    try:
                        data = z.read(info)
                    except Exception:
                        continue
                    for n in NEEDLES:
                        if n in data:
                            hits.append((str(jar.relative_to(ROOT)), info.filename, n.decode("utf-8")))
                            break
        except Exception as e:
            print("SKIP", jar, e)
    print(f"scanned_jars={scanned} entries={entries} hits={len(hits)}")
    for h in hits[:80]:
        print("HIT", h[0], "::", h[1], "->", h[2])


if __name__ == "__main__":
    main()
