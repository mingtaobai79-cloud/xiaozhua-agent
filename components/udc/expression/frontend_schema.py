"""前端侧的扩展机制 —— 各模块"不一样"在客户端怎么实现的。

证据：CFR/bundle `udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`
（关键词实测：expression 312 / schema 202 / paramType 291 / uniformityParams 37 /
  FRONT_NODE 20 / BACK_NODE 0 / ENTITY_NODE 0 / MICRO_FLOW_NODE 0）

结论：后端靠 `@ParamLoadService(paramType)` 给标准变量面；
      前端靠**注入 customSchema** 给模块自己的变量面。
两者叠加才是你在面板里看到的那个树。

## 1. customSchema —— 前端扩展点

模块把自己的变量包成一个节点塞进表达式组件：

```js
initialState: {
  customSchema: (() => {
    if (P?.type === "FUNCTION") {
      // 微流程里 type=FUNCTION 的节点 → 公共页面规则
      return [{type:"FRONT_NODE", name:"udc", description:"公共页面规则",
               schemas: [...uiModelSchemas, ...pageSchemas]}]
    }
    return a ? [{type:"FRONT_NODE", name:"udc", description:"页面规则",
                 schemas: pageSchemas}] : defaultSchemas
  })(),
  resultType: String
}
```

`type` 只有 **FRONT_NODE** 一种（bundle 里 BACK_NODE / ENTITY_NODE /
MICRO_FLOW_NODE 计数全为 0）—— 别臆造节点类型。

## 2. terminal 由谁决定

```js
{mode} = useXxx(
  ["FRONTEND","FUNCTION"].includes(flowBasicInfo?.type) ? "FRONTEND" : "BACKEND"
)
```

⇒ **微流程节点 type 决定 terminal**：
    type ∈ {FRONTEND, FUNCTION} → terminal=FRONTEND
    其余（SERVICE 等）           → terminal=BACKEND

这解释了「同一模块能力不同」：不是模块等级，是该节点跑在前端还是后端。

## 3. unLoadPresetSchema —— 默认不加载的 schema

```js
serverParams: { appId, unLoadPresetSchema: ["APP_PARAM"] }
```

`APP_PARAM`（应用参数）**默认不加载**；需要时才显式放出来。
所以 schema 面板上「应用参数」分组有时在、有时不在，不是 bug。

## 4. resultType 归一化（容易漏的一条）

```js
N = e => (e === Enum || e === CtpEnum) ? Long : e
```

⇒ **枚举 / 选项集的结果类型一律按 Long 处理**，再交给引擎。
自己拼 resultTypeInfo 时不要直接写 `Enum`，要写 `LONG`，否则类型兼容检查会拒。

## 5. mode 字符串形态

另一处代码里 `mode` 是拼接串：

```js
mode: "DESIIGN | ".concat(y, " | BACKEND")   // ← 注意 bundle 原文拼写就是 DESIIGN
```

这是**已知的 bundle 拼写**（不是本层笔误）。见到 `DESIIGN` 不要当发现 bug 去改，
它是平台前端自己的字符串。
"""
from __future__ import annotations

# 前端注入的变量节点类型（实测只有这一种）
FRONT_NODE = "FRONT_NODE"

# customSchema 里的固定字段
FRONT_NODE_SERVER_NAME = "udc"

# description 取值 = 模块标签（实测 3 种）
MODULE_LABEL_PUBLIC_PAGE_RULE = "公共页面规则"
MODULE_LABEL_PAGE_RULE = "页面规则"
MODULE_LABEL_PAGE_DESIGN = "页面设计"

MODULE_LABELS: tuple[str, ...] = (
    MODULE_LABEL_PUBLIC_PAGE_RULE,
    MODULE_LABEL_PAGE_RULE,
    MODULE_LABEL_PAGE_DESIGN,
)

# 微流程节点 type → terminal
FRONTEND_FLOW_TYPES: tuple[str, ...] = ("FRONTEND", "FUNCTION")

# 默认不加载的 preset schema（需要时显式放开）
DEFAULT_UNLOADED_SCHEMAS: tuple[str, ...] = ("APP_PARAM",)

# resultType 归一化：枚举 / 选项集按 Long
ENUM_RESULT_TYPE_CAST: dict[str, str] = {
    "Enum": "LONG",
    "CtpEnum": "LONG",
}


def terminal_for_flow_type(flow_type: str | None) -> str:
    """按微流程节点 type 推 terminal（前端真实判据）。"""
    return "FRONTEND" if flow_type in FRONTEND_FLOW_TYPES else "BACKEND"


def build_front_node(description: str, schemas: list,
                     name: str = FRONT_NODE_SERVER_NAME) -> dict:
    """构造前端注入的 customSchema 节点。

    description 必须取 MODULE_LABELS 之一，便于按模块反查。
    """
    if not isinstance(schemas, list):
        raise TypeError("schemas 必须是 list")
    return {"type": FRONT_NODE, "name": name,
            "description": description, "schemas": schemas}


def normalize_result_type(result_type: str) -> str:
    """枚举/选项集 → LONG；其余原样。"""
    return ENUM_RESULT_TYPE_CAST.get(result_type, result_type)


def should_load_schema(schema_name: str,
                       unload: tuple[str, ...] = DEFAULT_UNLOADED_SCHEMAS) -> bool:
    """该 preset schema 是否默认加载。"""
    return schema_name not in unload
