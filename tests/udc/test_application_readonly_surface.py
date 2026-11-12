"""应用域只读面契约 + 探针白名单的自证测试（离线可跑，不触网）。

覆盖：
  1. registry 里 8 条应用域只读契约的方法/路径逐字正确、write=False；
  2. 探针脚本白名单与 registry 路径一致（路径归一：去网关 /service、去前导 #?），
     且白名单里不允许出现任何写端点关键字；
  3. 落盘证据文件存在、结构完整、summary 与探针条数自洽；
  4. 证据文件不含会话 cookie 值（SY_ACCESS_TOKEN= 之类）。
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PY = ROOT / "components/platform_operations/registry.py"
PROBE_PY = ROOT / "tools/core/application/gateway_readonly_probe.py"
EVIDENCE = ROOT / "core/facts/udc/application/evidence/live-app-readonly-2026-10-22.json"

NEW_OPS = {
    "udc.application.user_role": ("GET", "udc/application/user-role?appName={appName}"),
    "udc.application.role_resource": ("GET", "udc/application/role-resource?appName={appName}"),
    "udc.deployment.latest_test_info": ("POST", "udc/deployment/latest-test-info"),
    "udc.application.front_detection": ("POST", "udc/application/search/front-detection"),
    "udc.sandbox.delta_build_info": ("GET", "udc/sandbox/delta-build-info/{appId}"),
    "udc.sandbox.is_deploy_war": ("GET", "udc/sandbox/system/config/is-deploy-war"),
    "udc.sandbox.app_search": ("POST", "udc/sandbox/app/search"),
    "sandbox.flexible.test_status": ("POST", "sandbox/flexible/test-status"),
}


def _registry():
    from components.platform_operations.registry import UdcOperationRegistry

    return UdcOperationRegistry.default()


@pytest.mark.parametrize("op,expected", sorted(NEW_OPS.items()))
def test_contract_registered_with_exact_method_and_path(op, expected):
    reg = _registry()
    assert reg.has(op), f"{op} 未登记"
    c = reg.get(op)
    assert (c.method, c.path) == expected
    assert c.write is False, f"{op} 必须是只读契约"


def _norm(path: str) -> str:
    p = path.replace("/service/", "", 1).lstrip("/").split("?", 1)[0]
    p = re.sub(r"\{[^}]*\}", "{}", p)
    return p


def _qkeys(path: str) -> list[str]:
    if "?" not in path:
        return []
    q = path.split("?", 1)[1]
    return [kv.split("=", 1)[0] for kv in q.split("&") if kv]


def test_probe_allowlist_has_no_write_endpoint():
    spec = importlib.util.spec_from_file_location("probe_mod", PROBE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    paths = [p for _op, _m, p, _b, _e in mod.ALLOWLIST]
    for p in paths:
        assert not any(w in p for w in mod.WRITE_LIKE), f"写端点混入白名单: {p}"

    # 白名单里的每条路径都必须能在 registry 找到同 method 同路径的契约
    # 例外：sandbox.flexible.test_status 的探针故意打 udc 前缀做负向验证（证明 udc 无映射）
    reg = _registry()
    by_key = {(c.method, _norm(c.path)) for c in reg.all().values()}
    for op, method, path, _b, _e in mod.ALLOWLIST:
        normalized = _norm(path)
        if op == "sandbox.flexible.test_status":
            assert normalized.endswith(_norm(reg.get(op).path)), (
                f"负向探针必须指向 udc 下的同名路径: {path}")
            continue
        assert (method, normalized) in by_key, f"探针 {op} 的 {method} {path} 在 registry 无对应契约"
        c = reg.get(op)
        for k in _qkeys(path):
            assert k in c.path, f"探针 {op} 的查询参数 {k} 未出现在契约路径 {c.path}"


def test_sandbox_flexible_belongs_to_sandbox_service():
    reg = _registry()
    c = reg.get("sandbox.flexible.test_status")
    assert c.path.startswith("sandbox/"), "弹性部署面必须挂在 sandbox 服务，不能拼 udc 前缀"
    assert c.status.value == "BLOCKED"
    assert "sandbox 服务不存在" in json.dumps(c.evidence, ensure_ascii=False)


def test_sandbox_flexible_family_is_denied_and_never_udc_prefixed():
    reg = _registry()
    writes = {
        "sandbox.flexible.create_deployment": True,
        "sandbox.flexible.delete_deployment": True,
        "sandbox.flexible.restart_deployment": True,
        "sandbox.flexible.select_deployment_page": False,
    }
    for op, is_write in writes.items():
        assert reg.has(op), f"{op} 未登记"
        c = reg.get(op)
        assert c.path.startswith("sandbox/"), f"{op} 必须挂 sandbox 服务"
        assert c.write is is_write, f"{op} 的 write 标记错误"
        assert c.status.value == "DENIED", f"{op} 在服务缺席下必须是 DENIED"
        assert "sandbox" in json.dumps(c.evidence, ensure_ascii=False)


def test_live_evidence_shape_and_summary():
    assert EVIDENCE.exists(), f"缺证据文件 {EVIDENCE}"
    doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert doc["app_id"] == "8704025620829192834"
    probes = doc["probes"]
    assert len(probes) == doc["summary"]["total"] == 9
    assert doc["summary"]["live_pass"] == 8
    assert doc["summary"]["fail"] == 1
    verdicts = {p["op"]: p["verdict"] for p in probes}
    assert verdicts["sandbox.flexible.test_status"] == "FAIL"
    for p in probes:
        assert p.get("traceId") or p["verdict"] != "LIVE_PASS"


def test_live_evidence_has_no_cookie_values():
    raw = EVIDENCE.read_text(encoding="utf-8")
    assert "SY_ACCESS_TOKEN=" not in raw
    assert "SY_UID=" not in raw
    assert "TK_EXP=" not in raw
    assert not re.search(r"cookie\s*[:=]\s*\S{10,}", raw, re.I), "证据文件疑似写入 cookie 值"


# ---------------------------------------------------------------- 应用内功能页

INNER_EVIDENCE = (ROOT / "core/facts/udc/application/evidence"
                  / "app-inner-pages-2026-10-22/replay-probe.json")

INNER_OPS = {
    # op_id: (method, path, write, status)
    "udc.applog.search.microflow": ("POST", "{app_name}/udc-runtime/app-log/search/microflow", False, "OBSERVED"),
    "udc.applog.search.dataflow": ("POST", "{app_name}/udc-runtime/app-log/search/dataflow", False, "OBSERVED"),
    "udc.applog.search.deduction": ("POST", "{app_name}/udc-runtime/app-log/search/deduction", False, "OBSERVED"),
    "udc.operation_log.init_data": ("POST", "udc/graphql?udcOperationLogSearchInitDataAppGet", False, "OBSERVED"),
    "udc.operation_log.search": ("POST", "udc/graphql?udcOperationLogSearch", False, "UNVERIFIED"),
    "udc.collaboration.app_get": ("POST", "udc/graphql?udcCollaborationAppGet", False, "OBSERVED"),
    "udc.deployment.app_ready_state": ("POST", "udc/graphql?udcDeploymentAppReadyStatePost", False, "OBSERVED"),
    "app_common.theme.select_default_brand": (
        "POST", "app-common/graphql?appCommonThemeSelectDefaultBrandPost", True, "DENIED"),
}


@pytest.mark.parametrize("op,expected", sorted(INNER_OPS.items()))
def test_inner_page_contract_shape(op, expected):
    reg = _registry()
    assert reg.has(op), f"{op} 未登记"
    c = reg.get(op)
    method, path, write, status = expected
    assert (c.method, c.path) == (method, path)
    assert c.write is write, f"{op} 的 write 标记错误"
    assert c.status.value == status, f"{op} 状态应为 {status}，实际 {c.status.value}"


def test_applog_family_prefix_is_app_name_not_udc():
    """运行态日志按应用隔离：前缀必须是 {app_name}/udc-runtime/，拼 udc 前缀会 404。"""
    reg = _registry()
    for op in ("udc.applog.search.microflow", "udc.applog.search.dataflow",
               "udc.applog.search.deduction"):
        c = reg.get(op)
        assert c.path.startswith("{app_name}/udc-runtime/app-log/search/"), c.path
        assert not c.path.startswith("udc/"), "日志族不能拼 udc 前缀"


def test_applog_only_three_kinds_are_known():
    """design/page/bizrule/sandbox/build/compile/deployment 已用 7 次 404 证伪。"""
    reg = _registry()
    known = {reg.get(op).path.rsplit("/", 1)[-1]
             for op in ("udc.applog.search.microflow", "udc.applog.search.dataflow",
                        "udc.applog.search.deduction")}
    assert known == {"microflow", "dataflow", "deduction"}
    absent = reg.get("udc.applog.search.absent_kinds")
    assert absent.status.value == "DENIED"
    for bad in ("design", "page", "bizrule", "sandbox", "build", "compile", "deployment"):
        assert bad in absent.path, f"{bad} 必须登记在证伪契约里"


def test_inner_graphql_ops_are_readonly_except_theme_mutation():
    """应用内功能页几乎全走 /graphql?<op>；只有主题页那条是 mutation 且已 DENIED。"""
    reg = _registry()
    gql_ops = [op for op, spec in INNER_OPS.items() if "/graphql?" in spec[1]]
    assert len(gql_ops) == 5, "graphql 族应登记 5 条（init_data/search/app_get/ready_state/theme）"
    for op in gql_ops:
        c = reg.get(op)
        denied = c.write is False and c.status.value in ("OBSERVED", "UNVERIFIED", "PASS")
        assert c.write is False and c.status.value != "DENIED" or c.status.value == "DENIED", op
        if op == "app_common.theme.select_default_brand":
            assert c.write is True and c.status.value == "DENIED"
        else:
            assert denied, f"{op} 只读契约不得标 DENIED"


def test_inner_evidence_replay_summary():
    assert INNER_EVIDENCE.exists(), f"缺证据文件 {INNER_EVIDENCE}"
    doc = json.loads(INNER_EVIDENCE.read_text(encoding="utf-8"))
    s = doc["summary"]
    assert s["LIVE_PASS"] == 5, s
    assert s["CALLED_EMPTY"] == 2, "dataflow/deduction 应是存活空结果"
    assert s["SKIPPED"] == 1, "udcOperationLogSearch 声明为 mutation，必须被跳过"
    assert s["FAIL"] == 3, "design/page/bizrule 三个证伪候选"
    skipped = [p for p in doc["probes"] if p["verdict"] == "SKIPPED"]
    assert all("MUTATION_NOT_REPLAYED" == p.get("skipped") for p in skipped)


def test_inner_evidence_has_no_cookie_values():
    raw = INNER_EVIDENCE.read_text(encoding="utf-8")
    for name in ("SY_ACCESS_TOKEN=", "SY_UID=", "TK_EXP="):
        assert name not in raw, f"证据文件写入 {name}"
    assert not re.search(r"cookie\s*[:=]\s*\S{10,}", raw, re.I)
    doc = json.loads(raw)
    assert "not persisted" in doc["auth"], "证据必须声明 cookie 未落盘"


def test_inner_capture_probes_never_send_mutations():
    """重放器必须对 mutation 硬跳过（源码级断言，防后人放宽）。"""
    src = (ROOT / "tools/core/application/replay_read_probe.py").read_text(encoding="utf-8")
    assert "MUTATION_NOT_REPLAYED" in src
    assert '"mutation " in pd' in src, "跳过条件必须基于 postData 里的 mutation 声明"


# ---------------------------------------------------------------- 依赖设置全链路

DEP_EVIDENCE = ROOT / "core/facts/udc/application/evidence/app-inner-pages-2026-10-22"

DEP_OPS = {
    "udc.dependency.available_apps": (
        "udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost", False, "OBSERVED"),
    "udc.dependency.list": (
        "udc/graphql?udcApplicationDependentApplicationSelectByConditionPost", False, "OBSERVED"),
    "udc.dependency.create_batch": (
        "udc/graphql?udcApplicationDependentApplicationCreateBatchPost", True, "DENIED"),
    "udc.dependency.delete_by_id": (
        "udc/graphql?udcApplicationDependentApplicationDeleteByIdPost", True, "DENIED"),
    "udc.application.detection": (
        "udc/graphql?udcApplicationSearchDetectionPost", True, "DENIED"),
}


@pytest.mark.parametrize("op,expected", sorted(DEP_OPS.items()))
def test_dependency_contract_shape(op, expected):
    c = _registry().get(op)
    path, write, status = expected
    assert c.path == path, c.path
    assert c.write is write, f"{op} write 标记错误"
    assert c.status.value == status, f"{op} 状态应为 {status}"


def test_dependency_write_ops_are_captured_from_real_recording():
    """写面形状必须来自真实录制：create 的 params0 是数组且带六个字段。"""
    raw = (DEP_EVIDENCE / "dep-write-create.json").read_text(encoding="utf-8")
    items = json.loads(raw)
    create = [x for x in items if "CreateBatchPost" in x["url"]]
    assert create, "缺 create 录制"
    body = json.loads(create[0]["postData"])
    params0 = body["variables"]["params0"]
    assert isinstance(params0, list), "params0 必须是数组"
    row = params0[0]
    for k in ("appId", "depAppName", "depAppCaption", "depAppVersion",
              "depAppBasePackage", "dependentAppType"):
        assert k in row, f"create 请求缺字段 {k}"
    assert row["dependentAppType"] == "SERVICE"
    # 列表重拉与写在同一批事件里
    assert any("SelectByCondition" in x["url"] for x in items), "确认后应自动重拉依赖列表"


def test_dependency_delete_uses_row_id_not_app_id():
    items = json.loads((DEP_EVIDENCE / "dep-write-remove.json").read_text(encoding="utf-8"))
    remove = [x for x in items["confirm"] if "DeleteByIdPost" in x["url"]]
    assert remove, "缺 delete 录制"
    body = json.loads(remove[0]["postData"])
    assert set(body["variables"]["params0"].keys()) == {"id"}, "delete 只带依赖行 id"


def test_dependency_list_replay_is_live_pass():
    doc = json.loads((DEP_EVIDENCE / "dep-select-replay.json").read_text(encoding="utf-8"))
    assert doc["replay"]["verdict"] == "LIVE_PASS"
    assert doc["replay"]["gql_keys"] == ["data0"]
    assert '"code": "BOOT_0000"' in doc["replay"]["content_head"]
    assert "depAppName" in doc["replay"]["content_head"]


def test_available_apps_payload_explains_disabled_checkbox():
    """enableDependent=false ⇔ 行 checkbox disabled（后端许可位，非前端 bug）。"""
    doc = json.loads((DEP_EVIDENCE / "dep-available-apps.json").read_text(encoding="utf-8"))
    assert '"enableDependent"' in doc["response"]
    assert '"code":"BOOT_0000"' in doc["response"]
    assert "SearchAvailableAppMultiVersionPost" in doc["url"]


def test_dependency_evidence_has_no_cookie_values():
    for p in DEP_EVIDENCE.glob("dep-*.json"):
        raw = p.read_text(encoding="utf-8")
        for name in ("SY_ACCESS_TOKEN=", "SY_UID=", "TK_EXP="):
            assert name not in raw, f"{p.name} 写入 {name}"


# ---------------------------------------------------------------- 沙箱构建 / 组件依赖

BUILD_EVIDENCE = ROOT / "core/facts/udc/application/evidence/app-inner-build-2026-10-22"

BUILD_OPS = {
    "udc.deploy.deploy_normal": ("udc/graphql?udcRuntimeDeployNormalPost", True, "DENIED"),
    "udc.sandbox.build_info": ("udc/graphql?udcSandboxBuildInfoAppGet", False, "OBSERVED"),
    "ctp.version.list": ("ctp-application/appcenter/search-app-edition", False, "OBSERVED"),
    "udc.ws.business_channels": ("业务消息服务", False, "OBSERVED"),
    "udc.dependency.component_create": (
        "udc/graphql?udcApplicationDependentApplicationCreateBatchPost", True, "DENIED"),
    "udc.dependency.delete_by_ids": (
        "udc/application/dependent-application/delete-by-ids", True, "DENIED"),
}


@pytest.mark.parametrize("op,expected", sorted(BUILD_OPS.items()))
def test_build_contract_shape(op, expected):
    path, write, status = expected
    c = _registry().get(op)
    assert path in c.path, c.path
    assert c.write is write, f"{op} write 标记错误"
    assert c.status.value == status, f"{op} 状态应为 {status}"


def test_build_info_returns_full_log_array():
    """构建日志靠一把取全量，不需要在构建窗口内抓流。"""
    doc = json.loads((BUILD_EVIDENCE / "build-info-live.json").read_text(encoding="utf-8"))
    assert doc["code"] == "BOOT_0000"
    c = doc["content"]
    assert c["state"] == "SUCCESS"
    assert c["progress"] == "100"
    assert int(c["totalTime"]) > 0
    logs = c["logs"]
    assert len(logs) >= 20, "logs 应包含完整构建阶段"
    assert any("任务开始" in x for x in logs)
    assert any("后端编译" in x or "前端" in x for x in logs)
    # 别名是 path:，不是 body:
    assert "(path:" in doc["request"]["query"]


def test_build_capture_shows_http_poll_and_ws_push():
    cap = json.loads((BUILD_EVIDENCE / "sandbox-build-capture.json").read_text(encoding="utf-8"))
    paths = [x["path"] for x in cap["http"]]
    poll = [p for p in paths if "BuildInfoAppGet" in p]
    assert len(poll) >= 10, "构建期间应轮询 build_info"
    assert any("udcRuntimeDeployNormalPost" in p for p in paths)
    assert any("udcApplicationSearchDetectionPost" in p for p in paths)
    assert any("search-app-edition" in p for p in paths)
    # 进度走 WS，不是 HTTP 推送
    ws = cap["ws"]
    ops = {json.loads(w["data"]).get("operate") for w in ws
           if w.get("dir") == "in" and (w.get("data") or "").startswith("{")}
    assert "udc_detection_channel" in ops
    assert "udc_deploy_channel" in ops
    assert "common-message" in ops


def test_deploy_normal_body_is_release_build():
    cap = json.loads((BUILD_EVIDENCE / "sandbox-build-capture.json").read_text(encoding="utf-8"))
    row = [x for x in cap["http"] if "udcRuntimeDeployNormalPost" in x["path"]][0]
    body = json.loads(row["postData"])
    dto = body["variables"]["params0"]["deployDto"]
    assert dto["projectType"] == "ALL" and dto["terminalType"] == "ALL"
    assert dto["deployType"] == "RELEASE"
    assert dto["generateLog"] is True
    # 声明成 query，实际是写
    assert body["query"].lstrip().startswith("query ")


def test_component_dependency_delete_is_rest_batch():
    rows = json.loads((BUILD_EVIDENCE / "cmp-dep-page-hook.json").read_text(encoding="utf-8"))
    dels = [x for x in rows if "delete-by-ids" in x["url"]]
    assert dels, "缺批量删除录制"
    body = json.loads(dels[0]["body"])
    assert list(body) == ["ids"] and isinstance(body["ids"], list)
    assert body["ids"][0].lstrip("-").isdigit(), "ids 应是依赖行 id"


def test_component_dependency_create_carries_frontend_fields():
    rows = json.loads((BUILD_EVIDENCE / "cmp-dep-create-full.json").read_text(encoding="utf-8"))
    create = [x for x in rows if "CreateBatchPost" in x["url"]][0]
    row = json.loads(create["postData"])["variables"]["params0"][0]
    assert row["dependentAppType"] == "FRONTEND"
    for k in ("description", "dynamicModuleGroup", "dynamicService", "enableDelete",
              "needGenerate", "sort", "supportUpgrade", "terminalType", "sourceType",
              "packageType"):
        assert k in row, f"组件依赖缺字段 {k}"
    assert row["packageType"] == "CONTROL" and row["terminalType"] == "PC"


def test_build_evidence_has_no_cookie_values():
    for p in BUILD_EVIDENCE.glob("*.json"):
        raw = p.read_text(encoding="utf-8")
        for name in ("SY_ACCESS_TOKEN=", "SY_UID=", "TK_EXP="):
            assert name not in raw, f"{p.name} 写入 {name}"
