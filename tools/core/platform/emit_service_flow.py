#!/usr/bin/env python3
"""抽 Service 的业务流转：反编译方法体，提取每个方法调了谁。

为什么需要：AppService 只是门面（`XxxAppServiceImpl` 一行转发给业务 Service），
真正的业务流转在下一层。写 ext 时要接进平台流程，必须知道
「这个方法背后实际动了哪些业务组件、哪些 Dao」。

做法：javap -p -c 每个 Impl 类 → 按方法切块 → 提 `// Method a.b.C.m:(...)` 行
→ 过滤框架噪音（java.* / org.springframework / slf4j / apache）→ 按 Dao/Service/Util 分类。

用法：
  python tools/core/platform/emit_service_flow.py \
      --repo <MAVEN_REPO>/com/seeyon --pkg udc-biz --emit-dir <dir>
"""
from __future__ import annotations

import argparse
import re
import subprocess
import zipfile
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"
RE_METHOD_LINE = re.compile(r"^  (?:public|protected|private|static|final|synchronized|\s)+[\w.$<>\[\], ?]+\s+([\w$]+)\(")
RE_CALL = re.compile(r"//\s*(?:Method|InterfaceMethod)\s+([\w.$/]+)\.([\w$<>]+):")
NOISE = ("java.", "javax.", "org.springframework", "org.slf4j", "org.apache",
         "com.fasterxml", "io.netty", "lombok.", "sun.", "jdk.")


def resolve_jar(repo: Path, pkg: str) -> Path | None:
    d = repo / pkg
    if not d.is_dir():
        return None
    js = sorted(d.rglob("*.jar"))
    return js[-1] if js else None


def classify(fq: str) -> str:
    low = fq.lower()
    if "dao" in low or "mapper" in low or "repository" in low:
        return "Dao"
    if "service" in low or "appservice" in low:
        return "Service"
    if "util" in low or "utils" in low or "helper" in low or "tool" in low:
        return "Util"
    if "event" in low or "listener" in low or "publisher" in low:
        return "Event"
    return "Other"


def parse_class(text: str) -> list[dict]:
    """按方法块切，提取每个方法的调用目标。"""
    methods: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        if line.startswith("  ") and not line.startswith("    ") and "(" in line and "Code:" not in line:
            m = RE_METHOD_LINE.match(line)
            if m:
                cur = {"name": m.group(1), "sig": " ".join(line.split())[:220], "calls": []}
                methods.append(cur)
                continue
        if cur is not None:
            for cm in RE_CALL.finditer(line):
                fq, meth = cm.group(1).replace("/", "."), cm.group(2)
                if fq.startswith(NOISE):
                    continue
                cur["calls"].append((fq, meth))
    return methods


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pkg", required=True, nargs="+", help="构件名，如 udc-biz")
    ap.add_argument("--emit-dir", required=True)
    ap.add_argument("--only-impl", action="store_true", default=True)
    ap.add_argument("--suffix", default="", help="输出文件名后缀，如 -appservice / -domain")
    ap.add_argument("--paths", nargs="*", default=None,
                    help="只抽路径含这些片段的类（如 domain/service domain/dao autocode/task）。"
                         "平台的业务 Service 常是具体类（domain/service/XxxService），不是 XxxServiceImpl。")
    a = ap.parse_args()

    repo = Path(a.repo)
    outdir = Path(a.emit_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    for pkg in a.pkg:
        jar = resolve_jar(repo, pkg)
        if not jar:
            print(f"WARN: 找不到 {pkg} 的 jar")
            continue
        with zipfile.ZipFile(jar) as z:
            names = [n for n in z.namelist() if n.endswith(".class")]
        if a.paths:
            names = [n for n in names if any(p in n for p in a.paths) and "$" not in n]
        elif a.only_impl:
            names = [n for n in names if n.endswith("Impl.class")]
        print(f"{pkg}: {len(names)} 个目标类", flush=True)

        lines = [f"# {pkg}：Service 业务流转", "",
                 f"> 自动生成。jar = `{jar.name}`。反编译方法体，提每个方法调了谁。",
                 "> 过滤掉了 java.*/spring/slf4j/apache 等框架噪音；`Dao`=落库，`Service`=业务委托，",
                 "> `Util`=工具，`Event`=事件发布，`Other`=其他。", ""]
        stats = {"Dao": 0, "Service": 0, "Util": 0, "Event": 0, "Other": 0}
        done = 0
        for name in sorted(names):
            fq = name[:-6].replace("/", ".")
            try:
                r = subprocess.run([JAVAP, "-p", "-c", "-cp", str(jar), fq],
                                   capture_output=True, text=True, timeout=90,
                                   encoding="utf-8", errors="replace")
            except subprocess.TimeoutExpired:
                continue
            if r.returncode != 0:
                continue
            methods = parse_class(r.stdout)
            # 只保留有调用的方法
            methods = [m for m in methods if m["calls"]]
            if not methods:
                continue
            done += 1
            lines += [f"## `{fq.split('.')[-1]}`", "", f"`{fq}`", ""]
            for m in methods:
                targets: dict[str, list[str]] = {}
                for cfq, cmeth in m["calls"]:
                    k = classify(cfq)
                    stats[k] += 1
                    targets.setdefault(f"{k}|{cfq}", [])
                    if cmeth not in targets[f"{k}|{cfq}"]:
                        targets[f"{k}|{cfq}"].append(cmeth)
                lines.append(f"### `{m['name']}()`")
                lines.append("")
                order = {"Service": 0, "Dao": 1, "Event": 2, "Util": 3, "Other": 4}
                for key in sorted(targets, key=lambda x: order[x.split("|")[0]]):
                    kind, cfq = key.split("|", 1)
                    meths = ", ".join(targets[key][:8]) + (" …" if len(targets[key]) > 8 else "")
                    lines.append(f"- **{kind}** `{cfq.split('.')[-1]}` → {meths}")
                lines.append("")
        p = outdir / f"{pkg}{a.suffix}.md"
        p.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {done} 个类有调用 → {p.name}（{p.stat().st_size//1024} KB）"
              f"  Dao {stats['Dao']} / Service {stats['Service']} / Util {stats['Util']}"
              f" / Event {stats['Event']}", flush=True)
        if done < 5:
            print(f"  WARN: {pkg} 只有 {done} 个类有调用，跳过", flush=True)
            p.unlink(missing_ok=True)
            continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
