"""故障注入自检：验证 business_readiness_audit 的门禁真能拦住错误。

铁律 4b：一条从没失败过的测试，很可能什么都没断言。
这里构造 3 个「应当被拦住」的 draft，逐个跑 audit，必须变红；
再跑一个「应当通过」的 draft，必须变绿。
"""
import sys, os, subprocess, json, tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "business_readiness_audit.py")

CASES = {
    # ① 编码字段硬编码（必须拦）
    "bad_code_const": {
        "expect_blocker": "编码类字段",
        "draft": '''def build_draft():
    return {"nodes": [
        {"id": "po", "kind": "create_entity", "entity": "采购订单",
         "fields": {"poCode": {"const": "PO-001"}, "bizStatus": {"const": "待收货"}}},
    ], "end": {"from": "po", "desc": "id", "basic_out": "BIGINTEGER"}}
''',
    },
    # ② 循环里逐条 create_entity（用户明确禁止，必须出现在警告里）
    "warn_loop_create": {
        "expect_warning": "循环内逐条 create_entity",
        "draft": '''def build_draft():
    return {"nodes": [
        {"id": "loop", "kind": "for_each", "list": "items", "body": [
            {"id": "one", "kind": "create_entity", "entity": "明细", "fields": {}},
        ]},
    ], "end": {"from": "loop", "desc": "x", "basic_out": "INTEGER"}}
''',
    },
    # ③ 正常 draft（应当无阻碍，仅警告）
    "good": {
        "expect_blocker": None,
        "draft": '''def build_draft():
    return {"nodes": [
        {"id": "r", "kind": "retrieve", "entity": "采购订单", "by_id_from": "$input",
         "caption": "查询-采购订单"},
        {"id": "v", "kind": "create_variable", "title": "poId", "data_type": "BIGINTEGER",
         "value": {"field": "r.id"}},
        {"id": "u", "kind": "change_entity", "entity": "采购订单", "from_node": "r",
         "fields": {"bizStatus": {"const": "已收货"}}},
    ], "end": {"from": "u", "desc": "行数", "basic_out": "INTEGER"}}
''',
    },
}


def run_case(name, case):
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, f"{name}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(case["draft"])
    r = subprocess.run([sys.executable, SCRIPT, "--draft", path, "--json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        out = json.loads(r.stdout)
    except Exception:
        return {"case": name, "ok": False, "why": f"输出非 JSON: {r.stdout[:200]} {r.stderr[:200]}"}

    blockers = out.get("blockers") or []
    warns = out.get("warnings") or []
    expect = case.get("expect_blocker")
    expect_w = case.get("expect_warning")

    if expect:
        hit = any(expect in b for b in blockers)
        return {"case": name, "ok": hit, "why": ("已拦住" if hit else f"未拦住！blockers={blockers}")}
    if expect_w:
        hit = any(expect_w in w for w in warns)
        return {"case": name, "ok": hit, "why": ("已警告" if hit else f"未警告！warnings={warns}")}
    return {"case": name, "ok": r.returncode in (0, 2), "why": f"blockers={len(blockers)} warns={len(warns)}"}


if __name__ == "__main__":
    results = [run_case(n, c) for n, c in CASES.items()]
    allok = True
    for r in results:
        mark = "PASS" if r["ok"] else "FAIL"
        if not r["ok"]:
            allok = False
        print(f"[{mark}] {r['case']}: {r['why']}")

    print()
    if allok:
        print("SELFTEST_OK 门禁有效（能拦住错误、放行正常）")
        sys.exit(0)
    else:
        print("SELFTEST_FAILED 门禁失效")
        sys.exit(1)
