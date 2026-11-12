# 零硬编码地探测 UDC 环境

用户明确要求：**不要写死或客户信息等固定内容，要的是事实和可复用工具，而不是固定生成工具。**

本文是从活体环境反推所有标识的方法，适用于任何应用、任何实体。

## 从哪拿什么

| 需要 | 来源 | 备注 |
|---|---|---|
| `appId` | 编辑器 URL 的 `?appId=` | 备选：`flowBasicInfo.appId` |
| `mid` | URL `/microflow/editor/<mid>` 末段 | 负数；备选 `flowBasicInfo.id` |
| `appName` | 流程 dataSchema 里的 `com.seeyon.<appName>.<...>` 正则 | 没有稳定的 application 查询 operation，别去找 |
| 实体清单 | `udcMicroflowSearchTreeEntityPost` | 返回键 `caption` / `dtoFullName` / `fullName`(domain) / `relationEntity` |
| 实体字段 | `udcMicroflowFindDtoByEntityPost` | `content.attributes`（dict，key=字段名） |
| 节点结构 | `udcMicroflowFindByIdGet` → `dataSchema` | 唯一「是否真落库」的判据 |
| cookie | CDP `Network.getAllCookies` | 必须按 host 过滤，见下 |

`appName` 推导：平台所有 UDC 类全名都是 `com.seeyon.<appName>.<...>`，所以从任意一个 DTO/domain 全名反推即可，不需要额外接口：

```python
m = re.search(r"com\.seeyon\.([A-Za-z0-9_]+)\.", json.dumps(schema, ensure_ascii=False))
app_name = m.group(1)
```

## GraphQL 调用形状（不要凭接口名猜）

后端 operation 的 query 形状由前端 `udcMutationLoader.load` 的 `paramsType` / `paramsKey` 决定：

| paramsType 后缀 | HTTP 类型 | 顶层字段 |
|---|---|---|
| `InputBody` | `mutation` | `body: $p` |
| `InputPath` | `query` | `path: $p` |

变量类型名 = 接口名 + 后缀。例：

```
mutation graphqlLoader ($p: udcMicroflowSearchTreeEntityPostInputBody)
  { data0: udcMicroflowSearchTreeEntityPost(body: $p) { code data { content } } }

query graphqlLoader ($p: udcMicroflowFindByIdGetInputPath)
  { data0: udcMicroflowFindByIdGet(path: $p) { code data { content { id dataSchema } } } }
```

把 `InputBody` 写成 `query`、或把 `InputPath` 写成 `mutation`，都会得到 HTTP 400 / `BOOT_*` 错误，看起来像参数问题，实际是形状错。

## cookie：`Network.getAllCookies` 必须按 host 过滤

它返回**整个浏览器**所有域名的 cookie（实测 89 个）。不分域全部塞进请求头会让服务端直接返回 **HTTP 400**——很容易误判成 token 过期或接口坏了。

```python
host = re.sub(r"^https?://", "", base_url()).split(":")[0]
out = {}
for ck in cookies:
    dom = (ck.get("domain") or "").lstrip(".")
    if dom == host or dom.endswith("." + host) or host.endswith(dom):
        out[ck["name"]] = ck["value"]
# localhost:3000 过滤后只剩 4 个：SY_ACCESS_TOKEN / SY_UID / SameSite / TK_EXP
```

直接用 CDP 现取的好处：不用维护外部 cookie 文件，也不会拿到过期 token。

## 实体树解析

`udcMicroflowSearchTreeEntityPost` 返回的是**嵌套树**（应用 → 实体 / 分组 → 实体），要拍平。实体项的特征键是 `dtoFullName` + `caption`：

```python
def walk(node):
    if isinstance(node, list):
        for x in node: yield from walk(x); 
        return
    if not isinstance(node, dict): return
    if node.get("dtoFullName") and node.get("caption"):
        yield node; return
    for k in ("children", "entities", "data"):
        if k in node: yield from walk(node[k])
```

实体对象字段映射：

```
label      = caption
 domain     = fullName
dto        = dtoFullName
entity_id  = relationEntity    (数字 id，字符串化)
```

`appName` 未知时这个接口会报 `UDC_MICROFLOW_0024` —— 所以必须先解析出 appName 再调。

## 环境变量约定

机器相关的（不能进代码常量，但每个环境不同）：

```
UDC_BASE       默认 http://localhost:3000
UDC_CDP        默认 http://127.0.0.1:9222
UDC_COOKIE_FILE  可选；CDP 取不到时的退回路径
```

## 探测脚本的写法

- 命令行只传**语义参数**（中文实体标题、字段标题），不传 id。
- 实体从节点已有配置反查：节点 `structure.label` / `structure.fullName` / `structure.id` 任一个都能 `ctx.entity()` 命中。
- 字段优先取 `source_type == "ENTITY"` 的业务字段，不写死字段名。
- 报告里写「本环境实测值」，不把值编回代码。
