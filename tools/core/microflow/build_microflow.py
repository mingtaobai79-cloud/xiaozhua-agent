"""微流程生成 CLI：声明式 spec → dataSchema → checkSchema → create → 发布。

用法：
    python tools/core/microflow/build_microflow.py \
        --app-id <appId> --caption "我的微流程" --name myFlow \
        --spec spec.json [--dry-run] [--draft-only]

spec.json：
    {
      "trigger_type": "MANUAL",
      "input":  {"desc": "入参", "dataType": "STRING"},
      "output": null,
      "nodes": [
        {"actionType": "CUSTOM_ERROR", "caption": "错误",
         "error": "文案", "errorType": "ERROR"},
        {"actionType": "BRANCH", "caption": "分支(1)",
         "cases": [{"expr": null, "nodes": [ ... ]}]}
      ]
    }

★ 分支用 `cases`，其余节点字段直接摊在对象上（与 settings 声明一致）。
★ 所有 id / 域名一律从参数或运行期取，不写死（脱敏闸门会拦）。

★★ 发布态（LIVE 已证，见 core/facts/udc/microflow/state-lifecycle.md）：
   `type=SERVICE` 的 create 会被后端**强制改成 state=DRAFT(10)**，传 20 无效；
   发布必须再发一次 update（完整 DTO + state=20）。
   所以本 CLI 默认 create 完立刻发布，`--draft-only` 才停在草稿。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.platform_operations.graphql_call import call_rest  # noqa: E402
from components.udc.microflow.build import (  # noqa: E402
    branch, build_schema, make_node, param, validate_for_submit, validate_schema,
)

BASE = "/service/udc/microflow"
RELEASE_STATE = 20


def _live_tab(client, need: str = "app-design"):
    """连一个**能真正执行 JS** 的 tab。

    ★ 教训：`connect(url_substr="app-design")` 会匹配到列表里第一个，
      而那个 tab 可能已经卡死（evaluate 超时），此时所有调用都会挂。
      必须逐个试，用 `1+1` 探活后再用。
    ★ 探活必须用**短超时**：卡死 tab 每次要等满 client.timeout，
      4 个 tab 就是几分钟。这里临时压到 5s。
    ★ 优先匹配 `need`，匹配不到就试全部（实测常活的往往是
      entity-rule/editor，URL 里不含 app-design）。
    """
    import urllib.request

    with urllib.request.urlopen("http://127.0.0.1:9250/json/list", timeout=8) as r:
        tabs = [t for t in json.load(r) if t.get("type") == "page"]
    cands = [t for t in tabs if need in (t.get("url") or "")]
    if not cands:
        cands = tabs
    if not cands:
        raise RuntimeError("没有可用页面 tab")
    old_to = getattr(client, "timeout", None)
    for t in cands:
        try:
            if old_to:
                client.timeout = 5
            client.connect(target=t)
            ok = client.evaluate("1+1", await_promise=False) == 2
            if old_to:
                client.timeout = old_to
            if ok:
                return t.get("url", "")
        except Exception:
            if old_to:
                client.timeout = old_to
            continue
    raise RuntimeError("%d 个候选 tab 全部无响应（evaluate 超时），请重开页面" % len(cands))


def spec_to_nodes(items: list[dict]) -> list[dict]:
    """把声明式节点列表转成真实节点。"""
    out = []
    for it in items:
        it = dict(it)
        # ★ 已经是完整节点（带 nodeId）就原样透传 ——
        #   FOR / BRANCH 这类结构节点是手写完整形态的，再走构造器会被拆坏
        if it.get("nodeId") and it.get("type") in ("FOR", "BRANCH", "CUSTOM_ERROR") \
                and it.get("actionType") is None:
            out.append(it)
            continue
        at = it.pop("actionType", None) or it.get("type")
        if at == "BRANCH":
            cases = it.pop("cases", [])
            conv = [{"expr": c.get("expr"),
                     "nodes": spec_to_nodes(c.get("nodes") or [])} for c in cases]
            out.append(branch(conv, caption=it.pop("caption", "分支(1)")))
            continue
        cap = it.pop("caption", None)
        out_decl = it.pop("output", None)
        node = make_node(at, caption=cap, **it)
        if isinstance(out_decl, dict):
            # 出参名必须与节点 id 同源：_<TYPE>_<6位>
            suffix = node["nodeId"].rsplit("_", 1)[-1]
            if any(k in out_decl for k in ("id", "javaType", "dtoType", "udcApp", "relationEntity")):
                # ★ 调用方给了**完整出参形态**（实体 DTO 需要 id/javaType/dtoType/relationEntity），
                #   不能压成 param()，否则 checkSchema 报 output.id 必填
                o = dict(out_decl)
                o.setdefault("name", "_%s_%s" % (at, suffix))
                node["output"] = o
            else:
                node["output"] = param(
                    "_%s_%s" % (at, suffix),
                    out_decl.get("dataType", "STRING"),
                    out_decl.get("desc", ""),
                )
        out.append(node)
    return out


def _resume(a) -> int:
    """对已有草稿继续走「发布 → 接口读回」。

    用途：spec 迭代时不想每次重建（重建会换 id、留垃圾），
    直接拿现有 id 改 dataSchema 再发布。

    ★ body 必须完全按 create 的形态拼（type/triggerType/creationMethod 用枚举名），
      少字段或传数字都会 BOOT_3000。
    """
    if not a.db_env:
        print("--resume 需要 --db-env（要读 DB 里的 dataSchema）")
        return 1
    from tools.core._env import connect_db, load_env, query  # noqa: E402

    db = connect_db(load_env(a.db_env), a.db_name)
    try:
        rows = query(db, """SELECT id, app_id, name, caption, type, trigger_type,
                                   state, service_interface, creation_method, data_schema
                            FROM udc_microflow_info WHERE id=%s""", (int(a.resume),))
    finally:
        db.close()
    if not rows:
        print("DB 里没有 id=%s" % a.resume)
        return 4
    r = rows[0]
    TYPE = {0: "SERVICE", 1: "FRONTEND", 2: "ENTITY_RULE", 3: "CUSTOM", 4: "FUNCTION"}
    TRIG = {0: "BUSINESS_EVENT", 1: "SCHEDULE", 2: "MANUAL", 3: "FRONTEND_PARAM"}
    CREA = {0: "MANUAL", 1: "FROM_TEMPLATE", 2: "PAGE_LAYOUT"}
    # ★ 关键修复：--resume 以前直接用 DB 里的 data_schema 提交，
    #   --spec 被完全忽略 → 「原地更新」实际是空转（节点/出入参改动全丢）。
    schema_json = r["data_schema"]
    if getattr(a, "spec", None):
        from pathlib import Path  # noqa: E402
        from components.udc.microflow.build import build_schema  # noqa: E402
        _spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
        schema_json = json.dumps(build_schema(_spec, app_id=str(r["app_id"])),
                                 ensure_ascii=False)
        print("使用 --spec 重建 dataSchema（%d 节点）" % len(_spec.get("nodes") or []))
    body = {
        "appId": str(r["app_id"]), "id": str(r["id"]),
        "name": r["name"], "caption": r["caption"],
        "type": TYPE.get(int(r["type"]), "SERVICE"),
        "triggerType": TRIG.get(int(r["trigger_type"]), "MANUAL"),
        "state": RELEASE_STATE,
        "creationMethod": CREA.get(int(r["creation_method"] or 0), "MANUAL"),
        "description": "",
        "serviceInterface": r["service_interface"],
        "dataSchema": schema_json,
    }
    from providers.cdp import CdpClient  # noqa: E402

    c = CdpClient(9250, allow_network=True, timeout=180)
    try:
        print("连接 tab：", _live_tab(c))
        if a.check_only:
            ck = call_rest(c, BASE + "/checkSchema/update", body)
            print("checkSchema/update：", ck.get("code"))
            print("  content:", str(ck.get("content"))[:1500])
            return 0 if ck.get("code") == "BOOT_0000" else 4

        pub = dict(body)
        u = call_rest(c, BASE + "/update", pub)
        print("publish(update)：", u.get("code"), str(u.get("message"))[:80])
        if u.get("code") != "BOOT_0000":
            print("★ 发布失败（校验不过时后端会静默丢弃改动）")
            ck = call_rest(c, BASE + "/checkSchema/update", body)
            print("checkSchema/update：", ck.get("code"))
            print("  content:", str(ck.get("content"))[:2000])
            return 3
        ck = call_rest(c, BASE + "/checkSchema/update", body)
        print("checkSchema/update：", ck.get("code"), str(ck.get("content"))[:160])
        return _verify(a, r["id"], c)
    finally:
        c.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--caption")
    ap.add_argument("--name")
    ap.add_argument("--spec")
    ap.add_argument("--resume", help="对已有草稿 id 继续发布（读 DB 的 dataSchema，需 --db-env）")
    ap.add_argument("--check-only", action="store_true", help="配合 --resume：只跑 checkSchema/update")
    ap.add_argument("--trigger-type", default="MANUAL")
    ap.add_argument("--service-interface", default="CustomMicroFlowAppService")
    ap.add_argument("--dry-run", action="store_true", help="只生成+校验，不提交")
    ap.add_argument("--draft-only", action="store_true",
                    help="只创建为草稿，不发布（默认 create 后自动发布）")
    ap.add_argument("--out-json", help="把生成结果写到文件")
    ap.add_argument("--db-env", help="发布后回读用的环境名（如 test2）；不填则跳过 DB 回读")
    ap.add_argument("--db-name", default="udc_test2", help="回读用的库名")
    a = ap.parse_args()

    if a.resume:
        return _resume(a)

    if not (a.spec and a.name and a.caption):
        ap.error("除 --resume 外必须给 --spec/--name/--caption")

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    spec["nodes"] = spec_to_nodes(spec.get("nodes") or [])
    schema = build_schema(spec, app_id=a.app_id)

    errs = validate_schema(schema)
    print("生成校验：", "通过" if not errs else "失败 %d 条" % len(errs))
    for e in errs:
        print("  -", e)
    if errs:
        return 1

    sins = validate_for_submit(schema, app_id=a.app_id, flow_name=a.name,
                               state=RELEASE_STATE)
    if sins:
        print("提交门禁：失败 %d 条" % len(sins))
        for e in sins:
            print("  -", e)
        return 1
    print("提交门禁：通过")

    if a.out_json:
        Path(a.out_json).write_text(json.dumps(schema, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
        print("已写出：", a.out_json)

    if a.dry_run:
        print("dry-run，未提交")
        return 0

    from providers.cdp import CdpClient  # noqa: E402

    c = CdpClient(9250, allow_network=True, timeout=180)
    try:
        print("连接 tab：", _live_tab(c))
        chk = call_rest(c, BASE + "/checkSchema", schema)
        print("checkSchema：", chk.get("code"), str(chk.get("content"))[:120])

        body = {
            "appId": a.app_id, "name": a.name, "caption": a.caption,
            "type": "SERVICE", "triggerType": a.trigger_type,
            "state": RELEASE_STATE, "creationMethod": "MANUAL", "description": "",
            "serviceInterface": a.service_interface,
            "dataSchema": json.dumps(schema, ensure_ascii=False),
        }
        r = call_rest(c, BASE + "/create", body)
        print("create：", r.get("code"), r.get("content"), str(r.get("message"))[:80])
        if r.get("code") != "BOOT_0000":
            return 2
        mid = r.get("content")
        print("已创建 id =", mid)

        if a.draft_only:
            print("（--draft-only）停在草稿态 state=10")
            return 0

        # ---- 发布：必须再发一次 update（create 的 state 会被后端覆盖成 DRAFT）
        pub = dict(body, id=str(mid), state=RELEASE_STATE)
        u = call_rest(c, BASE + "/update", pub)
        print("publish(update)：", u.get("code"), str(u.get("message"))[:60])
        if u.get("code") != "BOOT_0000":
            print("★ 发布失败，流程停在草稿态，运行期不会生效")
            return 3
        ck = call_rest(c, BASE + "/checkSchema/update", pub)
        print("checkSchema/update：", ck.get("code"), str(ck.get("content"))[:100])
        return _verify(a, mid, c)
    finally:
        c.close()


def _verify(a, mid, client) -> int:
    """发布后**用接口**读回确认 —— 接口写成功必须由接口读闭环。

    ★ 不用 DB 当常规验证通道：DB 只是取证工具，客户环境通常没有 DB 权限；
      而且「接口 0000 + DB 对」验证的是存储层，不是平台契约。
    ★ `--verify-db` 才额外做一次 DB 交叉校验（需要 --db-env）。
    """
    from components.udc.microflow.read import find_service, is_release, state_of

    try:
        svc = find_service(client, a.app_id, mid)
    except Exception as e:
        print("★ 接口读回失败：%s" % str(e)[:160])
        print("  标记 BLOCKED，不要当作成功")
        return 5
    if svc is None:
        print("★ 接口读回：列表里找不到 id=%s —— 标记 BLOCKED" % mid)
        return 4
    st = state_of(svc)
    print("接口读回：state=%s caption=%s type=%s"
          % (st, str(svc.get("caption"))[:24], svc.get("type")))
    if not is_release(svc):
        print("★ 接口读回 state=%s ≠ RELEASE，发布未生效" % st)
        return 4
    print("✓ 已发布，运行期生效（接口读回）")

    if getattr(a, "verify_db", False) and a.db_env:
        from tools.core._env import connect_db, load_env, query  # noqa: E402

        db = connect_db(load_env(a.db_env), a.db_name)
        try:
            rows = query(db, "SELECT state, publish_state FROM udc_microflow_info WHERE id=%s",
                         (int(mid),))
        finally:
            db.close()
        print("DB 交叉校验：", rows[0] if rows else "查不到")
        if not rows or int(rows[0].get("state") or 0) != RELEASE_STATE:
            print("★ DB 与接口不一致 —— 以接口为准但需排查")
            return 4
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
