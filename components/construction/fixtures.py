"""Golden Sample fixture loading for the Construction Engine.

v0.2: the Golden Sample is the real audited output of one application
(见 docs/audit/artifacts/customer-{facade,biz,web}-1.0.11029)。本 loader 直接解析
那些审计产物，让 golden 期望不会相对证据悄悄漂移。

⚠ 脱敏约束（2026-10-20）：本常量必须是**数字形式**的 app 标识——
   `platform_operations.deployment` 要从它提取尾号段作为数字 appId
   （见 _numeric_app_id）。用非数字代号会破坏这个契约。
   客户真实标识一律不进仓库，这里用保留段 app9000000000000000001。
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

# 客户应用标识是**仓外事实**：仓库内不硬编码（客户明细只进 seeyon-customer-evidence）。
# 下面这个常量仅作"未解析时的占位"，真实值由 golden_application_id() 在运行时从
# 仓外 golden 目录结构解析得到。
GOLDEN_APPLICATION_ID = "app9000000000000000001"


def _customer_evidence_root_from_config() -> str | None:
    """从 config/environments.yaml 读客户证据根（仓外路径；仓库内只存路径不存数据）。

    这是**仓库内的权威配置**——不能只靠环境变量，否则 shell 与 pytest 行为不一致，
    会导致"构造器用占位、loader 读真名"的两侧不一致。
    """
    try:
        import yaml as _yaml
        cfg_path = Path(__file__).resolve().parents[2] / "config" / "environments.yaml"
        cfg = _yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        envs = cfg.get("environments") or {}
        for env in ("test2", "uat", "default"):
            node = envs.get(env) or {}
            for key in ("customer_evidence_root", "customer_evidence"):
                if node.get(key):
                    return str(node[key])
        for key in ("customer_evidence_root", "customer_evidence"):
            if cfg.get(key):
                return str(cfg[key])
    except Exception:
        pass
    return None


def golden_application_id(evidence_root=None) -> str:
    """从仓外 golden 证据解析真实 application_id。

    仓外布局：<evidence_root>/fixtures-golden/<appId>/<entity>/entity.json
    解析顺序：环境变量 → config/environments.yaml 的 customer_evidence_root
    解析不到时回退到 GOLDEN_APPLICATION_ID（占位）。
    """
    import os as _os
    # 顺序：显式参数 → 环境变量（覆盖）→ config/environments.yaml（仓库内权威配置）
    root = evidence_root or _os.environ.get("SEEYON_CUSTOMER_EVIDENCE_ROOT")
    if not root:
        root = _customer_evidence_root_from_config()
    if root:
        base = Path(root)
        for pat in ("fixtures-golden/*/*", "*/*"):
            for cand in sorted(base.glob(pat)):
                if (cand / "entity.json").is_file():
                    try:
                        import json as _json
                        data = _json.loads((cand / "entity.json").read_text(encoding="utf-8-sig"))
                        aid = data.get("application_id")
                        if aid:
                            return str(aid)
                    except Exception:
                        continue
    return GOLDEN_APPLICATION_ID
GOLDEN_ENTITY = "Hetongdangan"

_FACADE_MODULE = "customer-facade-1.0.11029"
_BIZ_MODULE = "customer-biz-1.0.11029"
_WEB_MODULE = "customer-web-1.0.11029"

# Core Hetongdangan artifacts per module (javap dump basenames).
_CORE_ARTIFACT_FILES = {
    _FACADE_MODULE: (
        "HetongdanganDto.javap.txt",
        "HetongdanganAppService.javap.txt",
    ),
    _BIZ_MODULE: (
        "Hetongdangan.javap.txt",
        "HetongdanganService.javap.txt",
        "HetongdanganAppServiceImpl.javap.txt",
        "App9000000000000000001HetongdanganDao.javap.txt",
    ),
    _WEB_MODULE: (
        "AbstractHetongdanganController.javap.txt",
        "HetongdanganController.javap.txt",
    ),
}

# javap prints the resolved FQN on the class/interface declaration line.
_DECLARATION = re.compile(r"(?:class|interface)\s+((?:\w+\.)+\w+)")


@dataclass
class GoldenSample:
    application_id: str
    entity_name: str
    package_root: str
    fully_qualified_names: frozenset
    sources: dict

    def __post_init__(self):
        self.fully_qualified_names = frozenset(self.fully_qualified_names)


def load_golden_sample(artifacts_root) -> GoldenSample:
    """Load the checked-in Golden Fixture for Hetongdangan.

    ``artifacts_root`` may be the repository root, ``fixtures/golden`` or
    the legacy audit-artifacts directory. The canonical source is
    fixtures/golden/<application>/<entity>/{entity,artifacts}.json; audit
    javap files are retained as provenance and are only used as a fallback.
    """
    supplied = Path(artifacts_root)
    _app_id = golden_application_id()   # 运行时从仓外解析，仓库内不存客户 app 名
    candidates = [
        supplied / "fixtures" / "golden" / _app_id / GOLDEN_ENTITY,
        supplied / _app_id / GOLDEN_ENTITY,
        supplied,
    ]
    # 客户 golden 样本已迁出仓库（见 config/environments.yaml customer_evidence_root），
    # 仅当显式传入仓库外证据根或环境变量指向时可用；仓库内不再携带客户场景数据。
    import os as _os
    _ev_root = _os.environ.get("SEEYON_CUSTOMER_EVIDENCE_ROOT")
    if _ev_root:
        candidates.extend([
            Path(_ev_root) / "fixtures-golden" / _app_id / GOLDEN_ENTITY,
            Path(_ev_root),
        ])
    # 仓外证据根：在其下按结构找 golden 目录
    # 仓外布局：<evidence_root>/fixtures-golden/<appId>/<entity>/{entity,artifacts}.json
    #           <evidence_root>/<appId>/<entity>/{entity,artifacts}.json（另一历史布局）
    # 不依赖仓库内硬编码的客户 app 名（客户标识只存仓外，仓库内不留）。
    for base in (Path(_ev_root) if _ev_root else None, supplied):
        if base is None or not base.exists():
            continue
        found_dirs = []
        for pat in ("fixtures-golden/*/" + GOLDEN_ENTITY, "*/" + GOLDEN_ENTITY):
            found_dirs.extend(sorted(base.glob(pat)))
        for cand in found_dirs:
            if (cand / "entity.json").is_file() and (cand / "artifacts.json").is_file():
                candidates.insert(0, cand)
    fixture = next((p for p in candidates if (p / "entity.json").is_file() and (p / "artifacts.json").is_file()), None)
    if fixture is None:
        raise FileNotFoundError(f"golden fixture not found below: {supplied}")
    entity = json.loads((fixture / "entity.json").read_text(encoding="utf-8-sig"))
    payload = json.loads((fixture / "artifacts.json").read_text(encoding="utf-8-sig"))
    required = {"application_id", "entity_name", "package_root"}
    if not required.issubset(entity) or not isinstance(payload.get("artifacts"), list):
        raise ValueError("golden fixture schema is incomplete")
    observed = frozenset(str(x) for x in payload["artifacts"])
    expected_root = f"com.seeyon.{entity['application_id']}"
    if entity["package_root"] != expected_root:
        raise ValueError(f"golden fixture uses invalid package root: {entity['package_root']}")
    if not observed or any(not x.startswith(expected_root + ".") for x in observed):
        raise ValueError("golden fixture artifacts disagree with package root")
    return GoldenSample(entity["application_id"], entity["entity_name"], entity["package_root"], observed, {
        "entity": str(fixture / "entity.json"), "artifacts": str(fixture / "artifacts.json")
    })

