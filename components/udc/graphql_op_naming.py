"""GraphQL op 命名规则（后端权威，反编译字节码实证）。

证据（VERIFIED_STATIC_BYTECODE）：
- `boot-starter-graphql-5.3.358.jar`
  `com.seeyon.boot.starter.graphql.GraphQLProvider#pathToCamel(String)` +
  `#queryBuild(...)`：GraphQL 字段名 = `pathToCamel(restPath + "/" + httpMethod.toLowerCase())`。
- `GraphQLObjectTypeParamsService#addMethodParamList`：
  - path 参数  → 入参类型 `<op>InputPath`，GraphQL 参数名 `path`
  - body 参数  → 入参类型 `<op>InputBody`，GraphQL 参数名 `body`
  - query 参数 → 入参类型 `<op>InputQuery`，GraphQL 参数名 `query`
- `GraphQLObjectTypeNReturnService#getContentType` → 出参类型 `<op>ResponseContent`。
- `GraphQLProvider#addMethod`：`get` → Query；其余 → Query + Mutation（同名双挂）。

**结论**：GraphQL op 不是独立接口面，而是 **udc-web REST 端点的镜像**——
"页面按钮 → op" 的右端就是"Controller 方法 + @RequestMapping 路径 + HTTP 动词"。
因此前端 op 与后端 REST 的对账可以**按规则精确推导**，不必逐个反查 Resolver。

规则逐步（与字节码逐行对应）：
1. `pathToCamel`: replaceAll("\{","") + replaceAll("\}","")   去掉 path 变量花括号
2. `p = toCamelCase(p + "/" + httpMethod.toLowerCase(), false, '-','/','_')`
3. `p = p.replaceAll("[^A-Za-z0-9]","")`
4. `p = p.replaceAll("IdGet$","Get")`  5. `p = p.replaceAll("Id$","")`
6. `p = p.replaceAll("SearchPost$","Search")`

第 4~6 步是**唯一的三条业务缩写改写**，顺序不可交换（`IdGet$` 必须先于 `Id$`）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.platform.graphql-op-naming.v1"
EVIDENCE_LEVEL = "VERIFIED_STATIC_BYTECODE"
EVIDENCE_ARTIFACT = "boot-starter-graphql-5.3.358.jar (GraphQLProvider/GraphQLObjectTypeParamsService)"

DELIMITERS: tuple[str, ...] = ("-", "/", "_")

# 三条业务缩写改写（顺序敏感，与字节码一致）
OP_SUFFIX_REWRITES: tuple[tuple[str, str], ...] = (
    ("IdGet$", "Get"),
    ("Id$", ""),
    ("SearchPost$", "Search"),
)

# 入参/出参类型后缀（GraphQLObjectTypeParamsService / NReturnService）
ARG_TYPE_SUFFIX: dict[str, str] = {
    "path": "InputPath",
    "body": "InputBody",
    "query": "InputQuery",
}
ARG_NAME: dict[str, str] = {"path": "path", "body": "body", "query": "query"}
RESPONSE_TYPE_SUFFIX = "ResponseContent"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")


def to_camel_case(value: str, capitalize_first: bool = False,
                  delimiters: tuple[str, ...] = DELIMITERS) -> str:
    """`GraphQLProvider.toCamelCase` 的等价实现（含 outOffset==0 守卫）。

    与字节码逐行一致的两处关键细节：
    1. 分隔符集合**恒含空格**（generateDelimiterSet 先加 ' '）；
    2. 分隔符置 capitalizeNext=true，但**当 outOffset==0（尚未输出任何字符）时复位为
       false** —— 这正是 `/udc/application/...` 保持首字母小写（udc...）的原因，
       也是 `apache-commons CaseUtils` 与本实现行为的差异点。
    """
    if not value:
        return value
    delim_set = set(" ") | set(delimiters)
    out: list[str] = []
    capitalize_next = capitalize_first
    for ch in value:
        if ch in delim_set:
            capitalize_next = True
            if not out:
                capitalize_next = False
            continue
        if capitalize_next or (not out and capitalize_first):
            out.append(ch.title())
            capitalize_next = False
        else:
            out.append(ch)
    return "".join(out) if out else value


def path_to_op(path: str, http_method: str) -> str:
    """`GraphQLProvider.pathToCamel(path + "/" + httpMethod.toLowerCase())` 等价实现。"""
    p = path.replace("{", "").replace("}", "")
    p = to_camel_case(p + "/" + (http_method or "").lower(), False, DELIMITERS)
    p = re.sub(r"[^A-Za-z0-9]", "", p)
    for pattern, repl in OP_SUFFIX_REWRITES:
        p = re.sub(pattern, repl, p)
    return p


def arg_type_name(op: str, kind: str) -> str:
    """op 的入参类型名（kind ∈ path|body|query）。"""
    return op + ARG_TYPE_SUFFIX[kind]


def response_type_name(op: str) -> str:
    """op 的出参类型名。"""
    return op + RESPONSE_TYPE_SUFFIX


def _load_api() -> dict[str, Any]:
    with open(_API, encoding="utf-8") as fh:
        return json.load(fh)


def derive_ops(api: dict[str, Any] | None = None) -> dict[str, list[dict[str, str]]]:
    """REST 端点 → GraphQL op 映射（op → [{ctrl, method, http, path}]）。

    path 唯一取 `full_path`（= class_mapping + 方法级 value，见
    tools/core/merge_udc_web_api.py）。**不再**并列试算 "class_mapping + 方法 path"：
    那种双候选写法是在 full_path 拼接缺陷（方法级 value 以 "/" 开头被误当绝对路径）
    存在期间用来兜底的，实测掩盖了该缺陷；缺陷修复后两条拼法产出完全相同的 op 集合
    （655 vs 655，差异 0），双候选已是死代码，保留只会掩盖未来同类回归。
    """
    api = api if api is not None else _load_api()
    out: dict[str, list[dict[str, str]]] = {}
    for ctrl, info in api.items():
        for m in info.get("methods") or ():
            http = m.get("http") or ("POST" if m.get("is_write") else "GET")
            full_path = (m.get("full_path") or "").strip("/")
            if not full_path:
                continue
            op = path_to_op("/" + full_path, http)
            entry = {"ctrl": ctrl, "method": m.get("method", ""),
                     "http": http, "path": full_path}
            bucket = out.setdefault(op, [])
            if entry not in bucket:
                bucket.append(entry)
    return out


def explain(op: str, api: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """反查一个 op 的 REST 来源（空 = 该 op 非 udc-web REST 镜像）。"""
    return derive_ops(api).get(op, [])


__all__ = ["SCHEMA_ID", "EVIDENCE_LEVEL", "EVIDENCE_ARTIFACT", "DELIMITERS",
           "OP_SUFFIX_REWRITES", "ARG_TYPE_SUFFIX", "ARG_NAME", "RESPONSE_TYPE_SUFFIX",
           "to_camel_case", "path_to_op", "arg_type_name", "response_type_name",
           "derive_ops", "explain"]
