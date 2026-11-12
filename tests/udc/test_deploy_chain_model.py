"""构建/部署链 op 目录测试（SETTINGS 附节 + DATADICT §5 证据）。"""
from components.udc.deploy_chain_model import (
    ASSEMBLY_SHAPES, DEPLOY_OPS, DEPLOY_STATE_ENUM, DEPLOY_TYPES,
    HARD_GATES, PROJECT_TYPES, SPECIAL_ERROR_CODES, TERMINAL_TYPES,
    DeployRequest, catalog,
)


def test_state_enum_literal():
    assert set(DEPLOY_STATE_ENUM) == {"NONE", "STOP", "RUNNING", "PENDING", "FAILED", "UNKNOWN"}


def test_deploy_types_literal():
    assert set(DEPLOY_TYPES) == {"TEST", "RELEASE", "ON_ONLINE", "DELTA"}


def test_deploy_normal_requires_deploydto_wrapper():
    """平铺 body → EL1007E（LIVE 教训）：body() 必须返回 deployDto 包裹形态。"""
    req = DeployRequest(app_id="8704", deploy_type="RELEASE")
    body = req.body()
    assert set(body.keys()) == {"deployDto"}
    assert body["deployDto"]["deployType"] == "RELEASE"


def test_deploy_normal_op_declared_write_true():
    op = DEPLOY_OPS["udcRuntimeDeployNormalPost"]
    assert op["write"] is True
    assert op["wrapper"] == "deployDto"
    assert op["loader"] == "queryLoader"   # 走 queryLoader 非 mutation（附节实证）


def test_bad_enums_fail_dry_run():
    req = DeployRequest(app_id="8704", deploy_type="FROB", project_type="MIDDLE",
                        terminal_type="WATCH")
    r = req.dry_run()
    assert r["status"] == "FAIL"
    assert len(r["errors"]) == 3


def test_dry_run_never_executable():
    req = DeployRequest(app_id="8704")
    assert req.dry_run()["can_execute"] is False
    # op 面标注写
    assert DEPLOY_OPS["udcDeploymentAppOnlineNewPost"]["write"] is True
    assert DEPLOY_OPS["udcDeploymentAppOnlineNewPost"]["extra"]["deployType"] == "ON_ONLINE"


def test_online_new_forces_on_online():
    assert DEPLOY_OPS["udcDeploymentAppOnlineNewPost"]["extra"]["deployType"] == "ON_ONLINE"


def test_assembly_shapes_match_chunk_literals():
    assert ASSEMBLY_SHAPES["release_full"]["deployType"] == "RELEASE"
    assert ASSEMBLY_SHAPES["delta_frontend"]["projectType"] == "FRONTEND"
    assert ASSEMBLY_SHAPES["page_debug"]["terminalType"] == "<PC|MOBILE>"


def test_special_error_codes_registered():
    assert "重新构建" in SPECIAL_ERROR_CODES["UDC_DEPLOY_0002"]
    assert "EL1007E" in SPECIAL_ERROR_CODES


def test_hard_gates_registered():
    blob = " ".join(HARD_GATES)
    assert "CdpDataDetectionTask" in blob
    assert "无部分成功" in blob


def test_catalog_roundtrip():
    import json
    cat = catalog()
    back = json.loads(json.dumps(cat, ensure_ascii=False))
    assert back["schema"].endswith("deploy-op-catalog.v1")
    assert len(back["ops"]) == 6
    assert "两形态活体一致 BOOT_0000" in back["url_forms"][-1]
