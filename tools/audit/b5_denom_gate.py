# -*- coding: utf-8 -*-
"""B-5 分母一致性闸门（可执行版判据）

把 §5 里「三脚本必须输出一致，不一致即可复现性失效」从文字承诺变成可执行断言：
依次运行三个独立实现，解析各自的 total / with_mi / without，
若任一脚本非 exit=0 或三者数字不全相同 → exit 1（可复现性失效）。

用法:  python aud/b5_denom_gate.py
期望:  GATE PASS (total=254 / with_mi=244 / without=10)   exit=0
"""
import subprocess, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["b5_scan7.py", "b5_verify_254.py", "b5_recon_independent.py"]

# 各脚本输出格式不同，用容错正则抓三组数字
PATTERNS = [
    (r"total\s*=\s*(\d+)", "total"),
    (r"with_mi\s*=\s*(\d+)", "with_mi"),
    (r"without\s*=\s*(\d+)", "without"),
    (r"含\s*messageInfo\s*:\s*(\d+)", "with_mi"),
    (r"空壳\(无\s*messageInfo\)\s*:\s*(\d+)", "without"),
]

def parse(out):
    r = {}
    for pat, key in PATTERNS:
        if key in r: continue
        m = re.search(pat, out)
        if m: r[key] = int(m.group(1))
    return r

def main():
    results = {}
    failed = []
    for s in SCRIPTS:
        p = os.path.join(HERE, s)
        if not os.path.exists(p):
            print("MISSING %s" % s); failed.append((s, "file not found")); continue
        cp = subprocess.run([sys.executable, p], capture_output=True, text=True, encoding="utf-8", errors="replace")
        d = parse(cp.stdout)
        results[s] = d
        ok = (cp.returncode == 0) and all(k in d for k in ("total","with_mi","without"))
        print("%-26s exit=%-3d total=%-4s with_mi=%-4s without=%-4s %s"
              % (s, cp.returncode, d.get("total"), d.get("with_mi"), d.get("without"), "" if ok else "  <-- 解析/执行失败"))
        if not ok: failed.append((s, "exit=%d parsed=%s" % (cp.returncode, d)))

    print()
    if failed:
        print("GATE FAIL —— 可复现性失效（有脚本执行失败或关键数字缺失，须先修脚本再引用本文结论）")
        for f in failed: print("   ", f)
        return 1

    triples = {(d["total"], d["with_mi"], d["without"]) for d in results.values()}
    if len(triples) != 1:
        print("GATE FAIL —— 可复现性失效（三脚本输出不一致，须先查口径再谈数字）")
        for s, d in results.items():
            print("    %-26s %s" % (s, (d["total"], d["with_mi"], d["without"])))
        return 1

    t, wm, wo = triples.pop()
    # 额外断言：total = with_mi + without
    if t != wm + wo:
        print("GATE FAIL —— 内部不自洽: total(%d) != with_mi(%d) + without(%d)" % (t, wm, wo))
        return 1

    print("GATE PASS (total=%d / with_mi=%d / without=%d) —— 三脚本一致且有 trigger 微流程数可核" % (t, wm, wo))
    return 0

if __name__ == "__main__":
    sys.exit(main())
