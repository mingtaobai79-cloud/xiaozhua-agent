# -*- coding: utf-8 -*-
"""在本地平台 jar 中定位 error.code.PRIMARY / 主键冲突 的使用点（抛出方）。"""
import pathlib
import sys
import zipfile

ROOTS = [pathlib.Path(p) for p in sys.argv[1:]] or [pathlib.Path("<MAVEN_REPO>")]
TEXT_EXT = (".class", ".properties", ".xml", ".json", ".js", ".txt")
NEEDLES = ["error.code.PRIMARY", "error.code.PK_", "主键冲突", "违反主键约束",
           "SQLIntegrityConstraintViolationException", "DuplicateKeyException", "uk_u_c"]


def main():
    total = 0
    hits = {}
    for R in ROOTS:
        for j in R.rglob("*.jar"):
            if "-sources" in j.name or "-javadoc" in j.name:
                continue
            total += 1
            try:
                with zipfile.ZipFile(j) as z:
                    for i in z.infolist():
                        if i.file_size > 8_000_000 or not i.filename.lower().endswith(TEXT_EXT):
                            continue
                        try:
                            b = z.read(i)
                        except Exception:
                            continue
                        for nd in NEEDLES:
                            if nd.encode("utf-8") in b:
                                hits.setdefault(nd, []).append("%s :: %s" % (j.name, i.filename))
                                break
            except Exception:
                continue
    print("scanned_jars=", total)
    for nd, lst in hits.items():
        print("### %r  hits=%d" % (nd, len(lst)))
        for h in lst[:20]:
            print("   ", h)


if __name__ == "__main__":
    main()
