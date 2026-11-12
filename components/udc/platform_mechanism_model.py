"""平台机制模型 —— 版型/特征/权限/openAPI 的权威配置固化（udc-biz 5.3.517 jar 资源）。

证据基线：`docs/audit/artifacts/udc-biz-5.3.517/resources/`（jar 内打包资源原文，
STATIC_BYTECODE；提取脚本 tools/core/extract_udc_biz_resources.py）。这些是**平台自身配置**，
不是从既有实体反推——比"照标品回读"高一级的证据。

三块机制：
1. **版型→特征→字段集**（stereotype/*/config.json + feature/*/config.json）：
   建实体时 `stereotype` 决定 `necessaryFeatures`（必须带）+ `availableFeatures`（可选）；
   每个 feature 的 `attributeSet` 决定预置字段集（basic/approve/billBasic/...）。
   这直接回答"建 bill 实体要带哪些 features"（此前只能从既有实体反推）。
2. **设计态 vs 部署态权限**（auth/{draft,deploy}-auth.json）：
   设计态（草稿）entity/attribute 全 create/update/delete 允许；
   部署态 entity.update/delete=false、attribute.update/delete=false（仅 create 允许）
   —— 用户"已上架版本无法添加/复制/转移"的机制根因。
3. **openAPI 四操作**（openApi/entityOpenApi.json）：创建/删除/更新/查询 → 方法名清单（权威）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.platform.mechanism.v1"

_RES_ROOT = (Path(__file__).resolve().parents[2]
             / "docs" / "audit" / "artifacts" / "udc-biz-5.3.517" / "resources")


def _load(name: str) -> Any:
    p = _RES_ROOT / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _load_all(pattern_dir: str, field_probe: str | None = None) -> dict[str, Any]:
    d = _RES_ROOT / pattern_dir
    out: dict[str, Any] = {}
    if not d.is_dir():
        return out
    for sub in sorted(d.iterdir()):
        cfg = sub / "config.json"
        if cfg.exists():
            data = json.loads(cfg.read_text(encoding="utf-8"))
            key = data.get(field_probe) if field_probe else sub.name
            out[key or sub.name] = data
    return out


# ---------------------------------------------------------------- 1. 版型 / 特征
def load_stereotypes() -> dict[str, dict[str, Any]]:
    """版型定义（name → {caption, order, dataFlowEnabled, necessaryFeatures, availableFeatures}）。"""
    return _load_all("stereotype", field_probe="name")


def load_features() -> dict[str, dict[str, Any]]:
    """特征定义（name → {caption, attributeSet, order, configurable, ...}）。"""
    return _load_all("feature", field_probe="name")


def features_for_stereotype(stereotype: str) -> dict[str, Any]:
    """建该版型实体应带的 features（necessary 必带 + available 可选），附 attributeSet。

    这是建实体 body 的 `features` 字段的权威来源——此前靠既有实体反推，现为平台配置原文。
    """
    st = load_stereotypes().get(stereotype)
    if not st:
        return {"stereotype": stereotype, "found": False,
                "unknowns": [f"版型 {stereotype!r} 不在平台配置（{sorted(load_stereotypes())}）"]}
    feats = load_features()
    necessary = list(st.get("necessaryFeatures", []))
    available = list(st.get("availableFeatures", []))
    all_names = necessary + [a for a in available if a not in necessary]
    return {
        "stereotype": stereotype, "caption": st.get("caption"),
        "dataFlowEnabled": st.get("dataFlowEnabled"),
        "necessary_features": necessary, "available_features": available,
        "attribute_sets": {f: feats.get(f, {}).get("attributeSet", "") for f in all_names},
        "features_csv": ",".join(necessary),   # 建实体 features 字段（necessaryFeatures 逗号拼接）
        "found": True,
    }


# ---------------------------------------------------------------- 2. 权限（设计态 vs 部署态）
def load_auth(mode: str) -> dict[str, Any]:
    """mode ∈ {draft（设计态允许改）, deploy（部署态禁改）}。"""
    name = {"draft": "auth/draft-auth.json", "deploy": "auth/deploy-auth.json"}.get(mode)
    if not name:
        return {"unknowns": [f"mode={mode!r} 不合法（draft/deploy）"]}
    data = _load(name) or {}
    return {"mode": mode, "rules": data}


def permission_boundary() -> dict[str, Any]:
    """设计态 vs 部署态权限对照 —— 解释「已上架版本无法增删改」的机制。"""
    draft = (_load("auth/draft-auth.json") or {})
    deploy = (_load("auth/deploy-auth.json") or {})
    frozen: list[str] = []
    for obj in ("entity", "attribute"):
        for act in ("create", "update", "delete"):
            d_ok = draft.get(obj, {}).get(act)
            p_ok = deploy.get(obj, {}).get(act)
            if d_ok and not p_ok:
                frozen.append(f"{obj}.{act}: 设计态允许 / 部署态禁止")
    return {
        "draft_auth": draft, "deploy_auth": deploy,
        "frozen_on_publish": frozen,
        "rule": "已部署应用 entity.update/delete 与 attribute.update/delete=false —— "
                "「已上架版本无法 添加/复制/转移 实体/字段/字段集/索引」的服务端机制"
                "（对应 ENTITY-PAGE-INVENTORY §2.8.1 VERSION_CONSTRAINT 文案）",
    }


# ---------------------------------------------------------------- 3. openAPI 四操作
def load_openapi_operations() -> list[dict[str, Any]]:
    return _load("openApi/entityOpenApi.json") or []


def openapi_operation_map() -> dict[str, list[str]]:
    """{中文操作名: [方法名...]}，如 {'创建': ['create','createBatch','create4bpm'], ...}。"""
    return {e["caption"]: e["name"].split(",") for e in load_openapi_operations() if e.get("name")}


# ---------------------------------------------------------------- 4. 实体事件白名单
def load_entity_event_whitelist() -> list[str]:
    """标准生命周期事件全类名（触发微流程可选事件）。"""
    return _load("microflow/entityEventWhiteList.json") or []


# ---------------------------------------------------------------- catalog 导出
def catalog() -> dict[str, Any]:
    st = load_stereotypes()
    return {
        "schema": SCHEMA_ID,
        "evidence": "docs/audit/artifacts/udc-biz-5.3.517/resources/（jar 原文）",
        "evidence_level": "STATIC_BYTECODE",
        "stereotypes": {k: {"caption": v.get("caption"),
                            "necessaryFeatures": v.get("necessaryFeatures"),
                            "availableFeatures": v.get("availableFeatures"),
                            "dataFlowEnabled": v.get("dataFlowEnabled")}
                        for k, v in st.items()},
        "features": {k: {"caption": v.get("caption"), "attributeSet": v.get("attributeSet")}
                     for k, v in load_features().items()},
        "openapi_operations": openapi_operation_map(),
        "permission_boundary": permission_boundary()["frozen_on_publish"],
        "entity_event_whitelist": load_entity_event_whitelist(),
    }


__all__ = [
    "SCHEMA_ID", "load_stereotypes", "load_features", "features_for_stereotype",
    "load_auth", "permission_boundary", "load_openapi_operations",
    "openapi_operation_map", "load_entity_event_whitelist", "catalog",
]
