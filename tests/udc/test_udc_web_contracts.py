"""udc-web controller 契约测试 —— 类级路径 + @HasRole 角色（javap -v 机器提取）。

证据：docs/audit/artifacts/udc-web-5.3.517-contracts/_contracts.json（STATIC_BYTECODE）。
与人工审计 ENTITY-PAGE-INVENTORY §3 交叉核对。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

_C = ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts" / "_contracts.json"


def _load():
    return json.loads(_C.read_text(encoding="utf-8"))


def test_54_controllers():
    assert len(_load()) == 54


def test_entity_domain_controllers_paths():
    d = _load()
    assert d["EntityController"]["class_mapping"] == "udc/entity"
    assert d["EntityController"]["roles"] == ["udcAppDesigner", "udcSystemAdmin"]
    assert d["ReferConfigController"]["class_mapping"] == "udc/refer-config"
    assert "OrgAdmin" in d["ReferConfigController"]["roles"]   # 参照额外含 OrgAdmin
    assert d["EventController"]["class_mapping"] == "udc/event"
    assert d["IndexController"]["class_mapping"] == "udc/index"


def test_deploy_family_paths_and_roles():
    d = _load()
    # DeployController 类级 udc/runtime 无 HasRole（方法与 skill 记录一致）
    assert d["DeployController"]["class_mapping"] == "udc/runtime"
    assert d["DeployController"]["roles"] == []
    # DeploymentController 类级 udc/deployment + 4 角色
    assert d["DeploymentController"]["class_mapping"] == "udc/deployment"
    assert set(d["DeploymentController"]["roles"]) == {
        "BpmSystemManager", "OpsAdmin", "udcAppDesigner", "udcSystemAdmin"}


def test_hasrole_absent_five():
    """类级无 @HasRole 的 5 个（与审计 §第1层一致）。"""
    d = _load()
    absent = sorted(k for k, v in d.items() if not v["class_hasrole_annotation"])
    assert absent == ["MetaDataController", "OperationLogController", "ParameterController",
                      "UdcDesignMetadataController", "UdcFileController"]


def test_main_role_gate_is_appdesigner_systemadmin():
    d = _load()
    with_app = sum(1 for v in d.values() if "udcAppDesigner" in v["roles"])
    with_sys = sum(1 for v in d.values() if "udcSystemAdmin" in v["roles"])
    # udcAppDesigner/udcSystemAdmin 是主门（覆盖绝大多数 controller）
    assert with_app >= 45 and with_sys >= 44
    assert with_app >= with_sys  # appDesigner 覆盖 ≥ systemAdmin
