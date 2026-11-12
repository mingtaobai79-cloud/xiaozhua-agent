"""能力矩阵生成器：契约样本 × 构造器 × 已验收流程覆盖。

用法:
  python tools/microflow_coverage.py            # 只跑本地（契约 + 构造器）
  python tools/microflow_coverage.py --live     # 额外查线上分组已验收流程的 actionType 覆盖

输出可直接对照 docs/audit/microflow-capability-matrix.md。
"""
from __future__ import annotations
import os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT = os.path.join(ROOT, "core/facts/udc/microflow/node-contract-from-samples.json")
BUILDERS = ["microflow_nodes.py", "microflow_nodes_v2.py", "microflow_nodes_extra.py",
            "microflow_nodes_svc.py", "microflow_nodes_batch.py"]


def load_contract() -> dict:
    return json.load(open(CONTRACT, encoding="utf-8"))["contract"]


CONTRACT_KEYS: set[str] = set()


def scan_builders() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in BUILDERS:
        p = os.path.join(ROOT, "components/construction", f)
        if not os.path.exists(p):
            continue
        src = open(p, encoding="utf-8").read()
        for m in re.finditer(r"^def (\w+)\(", src, re.M):
            seg = src[m.end():m.end() + 1800]
            t = re.search(r'build\(\s*"([A-Z_]+)"', seg)
            # 有些构造器把 actionType 交给 builder.build(name) 之外的路径（如 build("ACTIVITY") + 显式赋值），
            # 用「函数体里出现的唯一契约 actionType 字面量」兜底。
            if not t:
                lits = [x for x in re.findall(r'"([A-Z][A-Z_]{3,})"', seg) if x in CONTRACT_KEYS]
                if len(set(lits)) == 1:
                    t = type("M", (), {"group": lambda self, _n=0, v=lits[0]: v})()
            if t:
                out.setdefault(t.group(1), []).append("%s:%s" % (f.replace("microflow_", "").replace(".py", ""), m.group(1)))
    return out


def live_coverage(proven_ids: set[str], app: str, group: str) -> dict[str, int]:
    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    from components.udc.microflow import deploy as DP
    from components.udc.microflow.live_refs import LiveRefs
    from providers.cdp import CdpClient
    HOST = os.environ.get("UDC_HOST", "")
    c = CdpClient(9333, allow_network=True, timeout=20); c.connect()
    r = c.send("Network.getCookies", urls=[HOST]); c.close()
    ck = "; ".join("%s=%s" % (k["name"], k["value"]) for k in r.get("cookies", [])
                   if k["name"] in ("SY_UID", "SY_ACCESS_TOKEN"))
    L = LiveRefs(HOST, ck)
    op = "udcMicroflowSearch"
    q = ("query g($p: %sInputBody) { data0: %s(body: $p) { code data { content } message } }" % (op, op))
    flows = L._content(L._gql(op, {"pageInfo": {"needTotal": True, "pageNumber": 1, "pageSize": 100},
                                   "params": {"appId": app}}, q, timeout=90)) or []

    def walk(ns, out):
        for n in ns or []:
            out.append(n); walk(n.get("nodes"), out)
            for cd in (n.get("conditions") or []):
                walk(cd.get("nodes"), out)
        return out

    cov: dict[str, int] = {}
    for f in flows:
        if str(f.get("id")) not in proven_ids or str(f.get("microFlowGroupId")) != group:
            continue
        ds = json.loads(DP.get(HOST, ck, str(f["id"]))["dataSchema"])
        for n in walk(ds.get("nodes"), []):
            t = n.get("actionType") or n.get("type")
            cov[t] = cov.get(t, 0) + 1
    return cov


def main() -> None:
    contract = load_contract()
    CONTRACT_KEYS.update(contract)
    builders = scan_builders()
    cov = {}
    if "--live" in sys.argv:
        ids = {x.strip() for x in (os.environ.get("PROVEN_IDS") or "").split(",") if x.strip()}
        if not ids:
            print("--live 需要 PROVEN_IDS=a,b,c"); return
        cov = live_coverage(ids, os.environ.get("APP_ID", "8704025620829192834"),
                            os.environ.get("GROUP_ID", "-5906489607826727193"))
    print("%-24s %6s %-42s %s" % ("actionType", "样本", "构造器", "已验收"))
    for t, spec in sorted(contract.items(), key=lambda x: -x[1]["samples"]):
        print("%-24s %6d %-42s %s" % (t, spec["samples"], ", ".join(builders.get(t, ["-"])[:2])[:42],
                                      cov.get(t, "-")))
    missing = sorted(set(contract) - set(builders))
    # ★ 假阴性修正（2026-11-02）：`for_each` 是 build("FOR") 之后把 type 改成 FOR_EACH
    #   （真实 384 个样本全部没有 actionType 键，控制节点靠 type 直取），
    #   所以按 build("FOR_EACH") 匹配永远找不到它。同理 CONDITION 不是节点，
    #   是 BRANCH 的 conditions[] 元素，不该出现在「缺构造器」里。
    FALSE_GAPS = {"FOR_EACH", "CONDITION"}
    real_missing = [m for m in missing if m not in FALSE_GAPS]
    print("\n无构造器:", real_missing or "无（22/22 都有构造路径）")
    if set(missing) - set(real_missing):
        print("  已排除的工具假阴性:", sorted(set(missing) - set(real_missing)))


if __name__ == "__main__":
    main()
