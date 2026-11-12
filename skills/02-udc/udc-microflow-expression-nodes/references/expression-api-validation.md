# 表达式后端校验：`/check` + `/transform`（LIVE PASS）

不需要打开编辑器就能判断表达式对不对，也能离线生成 `executableExpr`。
前提：请求必须在页面内发（带会话 cookie），且 `d.eval(..., await_promise=True)` ——
漏 `await_promise` 会拿到空字符串，看起来像「接口不可用」，实际是 Promise 没等。

## 1. 端点

```
POST /service/udc/expression/check
      → {"status":0,"code":"BOOT_0000","data":{"content":true}}
POST /service/udc/expression/transform
      → {"status":0,"code":"BOOT_0000","data":{"content":{
            "designData":{...},
            "runtimeData":{"executableExpr":"93gDaq3/..."}}}}
```

判成功：`code == BOOT_0000` **且** `data.content === true`（check）。
只判 `BOOT_0000` 不够——`content:false` 也是 `BOOT_0000`。

## 2. `schemas` 从哪来

不调 `/expression/schema`（`MICROFLOW` 域未注册，`BOOT_3000`）。直接取表达式里自带的
`designData.context`，逐层转换：

```python
SCHEMA_KEYS = ("name", "description", "type", "selectable",
               "enableDataI18n", "uniformityParams", "properties")

def context_to_schemas(context):
    def conv(node):
        out = {k: node[k] for k in SCHEMA_KEYS if k in node}
        out["skip"] = True                    # ★ 每层都要加
        if node.get("properties"):
            out["properties"] = [conv(c) for c in node["properties"]]
        return out
    return [conv(c) for c in context or []]
```

- `skip: true` **每层都加**，漏一层会被拒。
- `uniformityParams`（含 `paramId`）必须保留——`VariableCheckFilter` 靠它认变量；
  `pageNodeExtension: null` 保留即可，不需要删。
- 白名单外字段（如 `sort`）不带。

## 3. DTO 装配

```python
dto = {
    "resultTypeInfo": info["resultType"],          # BOOLEAN / STRING / INTEGER ...
    "schemas": context_to_schemas(info["context"]),
    "tokens": info["tokens"],                       # uid/type/value/desc 原样
    "isMultiSelect": False,
    "terminalSupportType": info["terminalType"],     # BACKEND / FRONTEND
}
```

`uid` 保留（服务端回包会回填）；值为 `None` 的键不提交。`paramType` 不在 DTO 里。

## 4. `executableExpr` 前缀不是签名

```
93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=+%28+_RETRIEVE_MSwqDF...%3E+0+%29+
```

对**已落库**的表达式调 `/transform`，返回的 `executableExpr` 与库中值**完全相同**。
⇒ 它是服务端固定产物，不是逐表达式签名，**可离线生成**，这是能脱离 UI 做批量写链的关键。

## 5. 四档判据

| 判据 | 可信度 | 说明 |
|---|---|---|
| 静态审计（变量根 / 恒等式 / token 五型） | 中 | 抓得到悬空与 `x > x`，抓不到类型不匹配 |
| `/check` = `content:true` | 高 | 走 5 段 Filter 链，与 UI「验证」同源 |
| `/transform` = `BOOT_0000` | 高 | 能产出运行态，说明结构完整 |
| `/transform` 产物 == 库中值 | 最高 | 证明库里的就是正确产物 |

静态审计与接口校验**互补**：静态抓语义无效（恒等式、悬空旧名），接口抓类型/结构不合法。
两者都跑才算收工；只跑一个方向的失败已在实战里出现过。

## 6. `verify_expression` 参考实现

```python
def verify_expression(d, expr):
    info = parse_expression(expr)
    dto  = build_save_dto(expr)
    chk  = check_expression_remote(d, dto)        # 失败即停，不调 transform
    if not chk["ok"]:
        return {"ok": False, "check": chk}
    tr = transform_expression_remote(d, dto)
    same = (info.get("executableExpr") or "") == (tr.get("executableExpr") or "")
    return {"ok": tr["ok"], "check": chk, "transform": tr, "roundtripSame": same}
```

check 失败必须短路——继续调 transform 只会拿到一堆无意义错误。

## 7. 与「暂存草稿」的关系

接口校验**只读**，不落库。判断对了之后写回仍要：

- 节点抽屉配置 → 「确定」即时写 L3；
- **画布内联配置（分支表达式 / 出入参 / 首节点）→ 必须点「暂存草稿」**；
- 顶栏「保存并提交」(`id=microflow_save`) 会把流程发成 RELEASE 并自锁只读，别用。

所以正常顺序是：**接口 check/transform 判对 → UI 或 GraphQL 写回 → 暂存草稿 → 后端回读 + 再 check**。

## 8. 陷阱

- 把 `/schema` 的 `BOOT_3000` 当成「整组表达式接口不可用」——只影响取变量面，`/check`、`/transform` 照常。
- `d.eval` 忘了 `await_promise=True`，返回空串，误判成接口坏了。
- 只判 `code == BOOT_0000` 不判 `content === true`，把校验失败当通过。
- `skip: true` 只加在根层，深层漏掉。
