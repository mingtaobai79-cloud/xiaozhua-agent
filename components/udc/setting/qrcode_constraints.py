"""设置域 · 二维码（QR Code Rule）实现与校验。

## 接口形态：REST，路径 `/service/udc/qrcode-rule/*`

（反编译 `boot-starter-qrcode-5.3.262.jar` 的 `CtpQrCodeRuleController`）

```
POST /service/udc/qrcode-rule/create              新建（@RequestBody CtpQrCodeRuleDesignDto）
POST /service/udc/qrcode-rule/update              更新
POST /service/udc/qrcode-rule/delete              删除（body {"id": ...}）
POST /service/udc/qrcode-rule/batch-delete        批量删（body {"ids": [...]}）
POST /service/udc/qrcode-rule/physical-delete     物理删除
POST /service/udc/qrcode-rule/deactivate          停用
POST /service/udc/qrcode-rule/start-using         启用
POST /service/udc/qrcode-rule/search              分页（PageInfo + ParamsDto + Sort）
POST /service/udc/qrcode-rule/search-no-page      不分页
GET  /service/udc/qrcode-rule/{id}                按 id 查
GET  /service/udc/qrcode-rule/detail/{guid}       按 guid 查
POST /service/udc/qrcode-rule/search-for-design-drop-down-list
```

## CtpQrCodeRuleDesignDto（反编译原文）

```java
Long    id
String  name                 // @NotBlank @Size(max=50)「个数必须在1到50之间」
CtpQrCodeTypeEnum type
CtpQrCodeLinkTypeEnum linkType
Long    appGuid = null
Long    appId = null
String  entityFullName
String  valueFieldCode       // ★ 二维码取哪个字段的值
String  pcPagePath
String  mobilePagePath
```

## 两个枚举（字符串传参）

```java
CtpQrCodeTypeEnum     BARCODE(0) / LINKQRCODE(1) / FIELDQRCODE(2) / QRCODE(3)
CtpQrCodeLinkTypeEnum APP(0) / CUSTOM(1)
```

含义（结合表字段推断 + 真实样本）：
- `type=BARCODE`   一维条码
- `type=LINKQRCODE` 链接二维码（配合 `linkType` + `pcPagePath`/`mobilePagePath`）
- `type=FIELDQRCODE` 字段值二维码（`valueFieldCode` 决定内容）
- `type=QRCODE`     普通二维码

`linkType=APP` 走应用内页面（`pcPagePath`）；`linkType=CUSTOM` 走自定义路径。

## 落库表 ctp_qr_code_rule

```
id / create_time / update_time / version / guid
is_active / app_guid / app_id / code / create_id / is_delete
entity_full_name / field_code / mobile_page_path / name / pc_page_path
release_state / type / update_id / value_field_code / logo_file_id
original_id / link_type
```

## CtpQrCodeRuleParamsDto（查询条件，反编译）

```java
String  name                 // @Size(1,50)
Boolean active = null
Long    appGuid = null
Long    appId = null
String  entityFullName
Boolean deleteFlag = null
Long    originalId
```
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------- 枚举（照抄反编译）
QR_TYPE = {"BARCODE": 0, "LINKQRCODE": 1, "FIELDQRCODE": 2, "QRCODE": 3}
LINK_TYPE = {"APP": 0, "CUSTOM": 1}

NAME_MAX = 50


def build_qr_rule_body(app_id: str | int, app_guid: str | int, *,
                       name: str, entity_full_name: str,
                       type_: str = "FIELDQRCODE",
                       link_type: str = "APP",
                       value_field_code: str = "",
                       pc_page_path: str | None = None,
                       mobile_page_path: str | None = None) -> dict[str, Any]:
    """构造二维码规则 body（CtpQrCodeRuleDesignDto）。

    `type_` 与 `link_type` 都传字符串枚举。
    `value_field_code` 只在 FIELDQRCODE / BARCODE 类需要（取哪个字段的值）。
    """
    return {
        "name": name,
        "type": type_,
        "linkType": link_type,
        "appGuid": str(app_guid),
        "appId": str(app_id),
        "entityFullName": entity_full_name,
        "valueFieldCode": value_field_code,
        "pcPagePath": pc_page_path,
        "mobilePagePath": mobile_page_path,
    }


def validate_qr_rule_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["二维码规则 body 必须是对象"]

    name = str(body.get("name") or "")
    if not name:
        errs.append("缺 name（DTO @NotBlank）")
    elif len(name) > NAME_MAX:
        errs.append(f"name 超长 {len(name)} > {NAME_MAX}（DTO @Size(max=50)）")

    if body.get("type") not in QR_TYPE:
        errs.append(f"type 必须是 {tuple(QR_TYPE)} 之一，实际 {body.get('type')!r}"
                    "（字符串枚举，不是数字）")
    if body.get("linkType") not in LINK_TYPE:
        errs.append(f"linkType 必须是 {tuple(LINK_TYPE)} 之一，实际 {body.get('linkType')!r}")

    for k in ("appId", "appGuid", "entityFullName"):
        if not body.get(k):
            errs.append(f"缺 {k}")

    ef = str(body.get("entityFullName") or "")
    if ef and not ef.startswith("com.seeyon."):
        errs.append("entityFullName 应是实体全类名（com.seeyon.<app>.domain.entity.Xxx）")

    t = body.get("type")
    if t in ("FIELDQRCODE", "BARCODE") and not body.get("valueFieldCode"):
        errs.append(f"type={t} 必须给 valueFieldCode（二维码取哪个字段的值）")
    # 链接二维码的页面值校验（禁止自编 URL）
    errs.extend(validate_link_page_path(body))
    return errs


def build_search_body(*, app_id: str | int, name: str | None = None,
                      entity_full_name: str | None = None,
                      active: bool | None = None,
                      page_number: int = 1, page_size: int = 50) -> dict[str, Any]:
    """构造 search body。

    Controller 签名是三个 @MultiRequestBody：
      selectPageByConditions(@MultiRequestBody PageInfo pageInfo,
                             @MultiRequestBody CtpQrCodeRuleParamsDto paramsDto,
                             @MultiRequestBody Sort sort)

    body 是三个平铺 key：pageInfo / paramsDto / sort。

    ⚠ **`sort` 必须是 `null`，不能是 `{}`**。
      传 `{}` 报 `BOOT_3000 message:null`（平台反序列化空对象失败）；
      传 `null` 正常。`search-no-page` 同理：只传 `{"paramsDto":{...}}` 即可。
    """
    params: dict[str, Any] = {"appId": str(app_id), "deleteFlag": False}
    if name:
        params["name"] = name
    if entity_full_name:
        params["entityFullName"] = entity_full_name
    if active is not None:
        params["active"] = bool(active)
    return {
        "pageInfo": {"pageNumber": int(page_number), "pageSize": int(page_size)},
        "paramsDto": params,
        "sort": None,
    }


def build_search_no_page_body(*, app_id: str | int,
                              entity_full_name: str | None = None,
                              name: str | None = None) -> dict[str, Any]:
    """search-no-page body —— 只传 paramsDto（不要 sort key）。"""
    params: dict[str, Any] = {"appId": str(app_id), "deleteFlag": False}
    if name:
        params["name"] = name
    if entity_full_name:
        params["entityFullName"] = entity_full_name
    return {"paramsDto": params}


# ---------------------------------------------------------------- 页面候选（链接二维码）
# ★ 2026-10-21 用户现场纠正：pcPagePath 不能自己编，必须先选实体、由平台按实体过滤
#   出候选页面，再取页面资源的 code 提交。
#
# 候选来源（DB 权威）：
#   udc_resource WHERE app_id=? AND type=1 AND is_delete=0
#   AND entity_full_name=<选中实体全类名>
#   → 取 code 作为 pcPagePath / mobilePagePath
#
# 实测：页面上"数据源配置信息列表页" → 落库 pc_page_path = "sjypzxxListPage"
#      （就是该页面资源行的 code，不是 URL 路由）

PAGE_RESOURCE_TYPE = 1   # udc_resource.type=1 = 页面


def build_page_candidate_query(app_id: str | int,
                               entity_full_name: str) -> tuple[str, tuple]:
    """返回查「该实体可用页面」的 SQL 与参数（权威表：`udc_page_info`）。

    ★ `pcPagePath` 存的是 **`udc_page_info.page_url`**，不是 `udc_resource.code`。
      实测：页面上选「数据源配置信息列表页」→ 落库 pc_page_path = "sjypzxxListPage"
      = `udc_page_info.page_url` 的值。

    注意 `udc_page_info` **没有 `is_deleted` 列**（和 udc_resource 不同）。
    """
    sql = ("SELECT id, page_url, caption, page_type, url_type "
           "FROM udc_test2.udc_page_info "
           "WHERE app_id=%s "
           "AND (master_entity_ids LIKE %s OR include_entity_ids LIKE %s) "
           "ORDER BY sort_no")
    like = f"%{entity_full_name}%"
    return sql, (str(app_id), like, like)


def build_page_candidate_query_by_url(app_id: str | int,
                                      url_prefix: str) -> tuple[str, tuple]:
    """备用查法：页面 url 以某前缀开头（实体名拼音缩写，如 sjypzxx）。"""
    sql = ("SELECT id, page_url, caption, page_type, url_type "
           "FROM udc_test2.udc_page_info WHERE app_id=%s AND page_url LIKE %s "
           "ORDER BY sort_no")
    return sql, (str(app_id), f"%{url_prefix}%")


def validate_link_page_path(body: dict[str, Any],
                            allowed_codes: set[str] | None = None) -> list[str]:
    """链接二维码的页面值校验 —— 必须是页面资源的 code，不是自编 URL。

    `allowed_codes`：该实体下真实存在的页面 code 集合（从
    `build_page_candidate_query` 查出来）。传 None 只做形态校验。
    """
    errs: list[str] = []
    t = body.get("type")
    if t != "LINKQRCODE":
        return errs
    if body.get("linkType") != "APP":
        return errs   # CUSTOM 分支未验证，不在此校验

    pc = body.get("pcPagePath")
    mob = body.get("mobilePagePath")

    if not pc and not mob:
        errs.append("type=LINKQRCODE 至少给 pcPagePath 或 mobilePagePath")
        return errs

    for label, val in (("pcPagePath", pc), ("mobilePagePath", mob)):
        if not val:
            continue
        if not isinstance(val, str):
            errs.append(f"{label} 必须是字符串")
            continue
        # 形态：不能是 URL / 路由（含 / 或 ://）
        if "://" in val or val.startswith("/"):
            errs.append(
                f"{label}={val!r} 看着是自编 URL —— 必须填页面资源的 code"
                "（如 sjypzxxListPage），由「选实体 → 平台过滤候选」得到，不能手写路由")
            continue
        if allowed_codes is not None and val not in allowed_codes:
            errs.append(
                f"{label}={val!r} 不在该实体的可用页面里（候选 {sorted(allowed_codes)[:8]}）"
                " —— 页面候选按实体过滤，必须先选实体")
    return errs


__all__ = [
    "QR_TYPE", "LINK_TYPE", "NAME_MAX",
    "build_qr_rule_body", "validate_qr_rule_body", "build_search_body",
    "build_search_no_page_body", "build_page_candidate_query",
    "build_page_candidate_query_by_url",
    "validate_link_page_path", "PAGE_RESOURCE_TYPE",
]
