# -*- coding: utf-8 -*-
"""从 web jar 的 Controller 字节码提取真实 REST 路由（javap -v 注解）。

javap 输出结构：
  类级注解在文件末尾的 RuntimeVisibleAnnotations（缩进 4）：@RequestMapping(value=[基础路径])、@RestApi
  方法级注解在方法体内（缩进 8）：@PostMapping/@GetMapping(...)
据此用缩进区分，避免把类级路径算到最后一个方法上。

输出: docs/audit/artifacts/rest/<artifact>.json
用法: python extract_rest_routes.py [artifact ...]   # 缺省 = 全部 *-web
"""
import json, io, os, re, subprocess, sys, zipfile
from concurrent.futures import ThreadPoolExecutor

REPO = r"C:/Users/白明涛/xiaozhua-agent"
TARGETS = r"D:/software/hermes/cache/scratch/rebuild/targets_full.json"
OUT = os.path.join(REPO, "docs/audit/artifacts/rest")
JAVAP = r"D:/software/java/bin/javap.exe"

MAP_TYPES = ("RequestMapping", "PostMapping", "GetMapping", "PutMapping",
             "DeleteMapping", "PatchMapping")
METHOD_SIG = re.compile(r"^  (?:public|protected|private)[^;]*?(\w+)\((.*)\);\s*$")


def controllers(jar):
    zf = zipfile.ZipFile(jar)
    out = [n[:-6].replace("/", ".") for n in zf.namelist()
           if n.endswith(".class") and ("/controller/" in n or n.endswith("Controller.class"))]
    zf.close()
    return out


def run_javap(jar, fqcn):
    try:
        r = subprocess.run([JAVAP, "-v", "-p", "-cp", jar, fqcn],
                           capture_output=True, timeout=90)
    except Exception:
        return ""
    b = r.stdout or b""
    for enc in ("gbk", "utf-8"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("utf-8", "ignore")


def parse(jar, fqcn):
    txt = run_javap(jar, fqcn)
    if "Mapping(" not in txt:
        return None

    base, rest_api, routes = "", "", []
    cur_method, pending, plines = None, None, []

    for line in txt.splitlines():
        stripped = line.strip()

        m = METHOD_SIG.match(line)
        if m:
            cur_method = m.group(1)
            continue

        indent = len(line) - len(line.lstrip())
        mt = next((t for t in MAP_TYPES if (t + "(") in stripped), None)
        if stripped.startswith("com.seeyon.boot.annotation.RestApi("):
            pending, plines = "RestApi", []
            continue
        if mt:
            pending, plines = mt, []
            continue
        if pending and stripped.startswith("value"):
            if pending == "RestApi":
                mm = re.findall(r'"([^"]*)"', stripped)
                rest_api = mm[0] if mm else ""
                pending = None
                continue
            plines.append(stripped)
            if stripped.endswith("]") or stripped.endswith('"'):
                paths = re.findall(r'"([^"]*)"', " ".join(plines))
                path = paths[0] if paths else ""
                if indent >= 8 and cur_method:
                    routes.append({"java_method": cur_method, "mapping": pending,
                                   "path": path, "paths": paths})
                elif base == "":
                    base = path
                pending = None
            continue
        if stripped.startswith("com.seeyon.boot.annotation.RestApi("):
            pending, plines = "RestApi", []
            continue
        if pending == "RestApi" and stripped.startswith("value="):
            mm = re.findall(r'"([^"]*)"', stripped)
            if mm:
                rest_api = mm[0]
            pending = None

    if not routes and not base:
        return None
    return {"base": base, "rest_api": rest_api, "routes": routes}


def scan(artifact, jarpath, workers=8):
    cs = controllers(jarpath)
    res = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [(c, ex.submit(parse, jarpath, c)) for c in cs]
        for c, f in futs:
            try:
                d = f.result()
            except Exception:
                d = None
            if d:
                res[c] = d
    return res, len(cs)


def main():
    targets = json.load(io.open(TARGETS, encoding="utf-8"))
    arts = sys.argv[1:] or sorted(k for k in targets if k.endswith("-web"))
    os.makedirs(OUT, exist_ok=True)
    tot = 0
    for a in arts:
        if a not in targets:
            print(f"  ? {a}")
            continue
        p = targets[a][1]
        if not os.path.exists(p):
            print(f"  ✗ {a}: jar 缺")
            continue
        res, n = scan(a, p)
        routes = sum(len(v["routes"]) for v in res.values())
        if not res:
            print(f"  - {a}: {n} controller，0 路由")
            continue
        io.open(os.path.join(OUT, f"{a}.json"), "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        tot += routes
        print(f"  ✓ {a}: {len(res)}/{n} controller，{routes} 路由")
    print(f"\n合计 {tot} 条路由")
    return 0


if __name__ == "__main__":
    sys.exit(main())
