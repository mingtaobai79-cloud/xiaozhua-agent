"""自定义对象（DataTransferObject）域的本地校验与构造。

域归属：UDC 九域之「设置」→ 自定义对象 tab。

业务定位（2026-10-20 设计器原文）：
  「支持自定义对象，用于微流程/页面规则之间的相互调用数据传递」
  落库表 ``udc_data_transfer_object``

平台接口（2026-10-20 GraphQL 探测 + LIVE 证实）：
  创建  udcDataTransferObjectPost        （Mutation）
  更新  udcDataTransferObjectUpdatePost   （Mutation）
  删除  udcDataTransferObjectDeletePost   （Mutation）
  查询  **无 GraphQL 查询 operation**（探测 40+ 候选全为 FieldUndefined）
        → 列表读取走 DB（udc_data_transfer_object），这是事实不是缺失

必填槽位（BOOT_1001 逐条探针实测得出，非推断）：
  appId     应用Id 不能为null
  appGuid   应用 guid（取自 udc_application.guid，不是 appId）
  caption   对象显示名称 不能为空
  name      对象名称 不能为空
  source    source不能为空（实测 1 可过）

错误码实测：
  BOOT_1001  缺必填（消息逐字段点名，可直接据此补齐）
  BOOT_4101  source 不能为空

范围纪律：
  · 删除用 ``udcDataTransferObjectDeletePost``，不是批量删（批量删 operation 不存在）
  · 查询面不存在 → 事实记录为「平台无查询 operation，列表走 DB 读」
  · 不臆造 operation 名（探测判据见 enum-write-chain 同款：FieldUndefined ⇒ 不存在）
"""
from __future__ import annotations

import json
from typing import Any

# 平台必填字段（BOOT_1001 / BOOT_4101 实测）
REQUIRED_FIELDS = ("appId", "appGuid", "caption", "name", "source")

# source 取值域：实测 1 可过；其它取值的语义未取证 → 不做值域断言
KNOWN_SOURCE = 1


def build_custom_object_body(app_id: str | int,
                             app_guid: str,
                             caption: str,
                             name: str,
                             source: int = KNOWN_SOURCE,
                             *,
                             description: str = "",
                             order_no: int = 100,
                             host_app_name: str | None = None,
                             data_status: bool = False) -> dict[str, Any]:
    """构造自定义对象 body（与 udcDataTransferObjectPost 逐字段对齐）。

    ⚠ ``name`` 是对象编码（英文），``caption`` 是显示名（中文）——平台报错文案
      分别叫「对象名称」与「对象显示名称」，别对调。
    """
    if not str(name).strip():
        raise ValueError("自定义对象 name（对象编码）不能为空（平台 BOOT_1001：对象名称 不能为空）")
    if not str(caption).strip():
        raise ValueError("自定义对象 caption（显示名）不能为空（平台 BOOT_1001：对象显示名称 不能为空）")
    if not str(app_guid).strip():
        raise ValueError("自定义对象 appGuid 不能为空（取自 udc_application.guid，不是 appId）")
    body: dict[str, Any] = {
        "appId": str(app_id),
        "appGuid": str(app_guid),
        "name": str(name).strip(),
        "caption": str(caption).strip(),
        "source": source,
        "orderNo": order_no,
        "hostAppName": host_app_name,
        "dataStatus": data_status,
    }
    if description:
        body["description"] = description
    return body


def validate_custom_object_body(body: dict[str, Any]) -> list[str]:
    """校验自定义对象 body —— 把平台 BOOT_1001/4101 前移到本地。"""
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["自定义对象 body 必须是对象"]
    if body.get("appId") in (None, ""):
        errs.append("自定义对象缺 appId（平台 BOOT_1001：应用Id 不能为null）")
    if body.get("appGuid") in (None, ""):
        errs.append("自定义对象缺 appGuid（取自 udc_application.guid，不是 appId）")
    if body.get("caption") in (None, ""):
        errs.append("自定义对象缺 caption（对象显示名称；平台 BOOT_1001）")
    if body.get("name") in (None, ""):
        errs.append("自定义对象缺 name（对象编码；平台 BOOT_1001：对象名称 不能为空）")
    if body.get("source") in (None, ""):
        errs.append("自定义对象缺 source（平台 BOOT_4101：source不能为空）")
    return errs


def build_custom_object_delete_body(app_id: str | int,
                                    object_id: str | int) -> dict[str, Any]:
    """删除 body（udcDataTransferObjectDeletePost）。

    实测：body 缺 id 时返回 BOOT_0000 但 content=0（删了 0 条）——
    **成功码不代表删掉了**，必须回读核对。
    """
    return {"appId": str(app_id), "id": str(object_id)}


def validate_custom_object_delete_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["自定义对象删除 body 必须是对象"]
    if body.get("id") in (None, ""):
        errs.append("自定义对象删除缺 id（实测：缺 id 时平台仍返回 BOOT_0000 但 content=0，"
                    "成功码不代表删掉了）")
    if body.get("appId") in (None, ""):
        errs.append("自定义对象删除缺 appId")
    return errs


__all__ = [
    "build_custom_object_body",
    "validate_custom_object_body",
    "build_custom_object_delete_body",
    "validate_custom_object_delete_body",
    "REQUIRED_FIELDS",
    "KNOWN_SOURCE",
]
