# MCP 工具真机验证（第二批）

> 日期：2026-11-11
> 环境：test2，`appId=app9000000000000000001`，`appGuid=appGuid0000000000000001`
> 传输：CDP 页面代发（`PageFetch`，cookie 不出浏览器）
> 结论：**11 个新增通过 + 4 个真 bug 修复 + 1 个路径不符 + 1 次误删事故（已补回）**
> 测试数据：全部清零（serial `content: []`；scalability 只剩真实 `dsa`；事件列表 `content: []`；索引二次删除报不存在）

## 1. 通过（新增 3 个）

| 工具 | 入口 | 建成 id | 回读 | 删除 |
|---|---|---|---|---|
| `serial_scheme_body` + `serial_section` | `udcSerialSchemeCreatePost` | 2021379478200684424 | `udcSerialSchemeSearchPagePost` 查到 | `udcSerialSchemeDeletePost` content=1 |
| `dto_body` | `udcDataTransferObjectPost` | -1040424636770033314 | — | `udcDataTransferObjectDeletePost` content=1，再删 content=0 |
| `scalability_field_body` | `udcScalabilityPost` | 6921585768522308613 | — | 随父方案 `udcScalabilityOptionDeletePost` content=1 |
| `index_body` | `udcIndexPost` | 144990080312625299 | — | `udcIndexDeleteBatchPost` content=1；再删报 `UDC_INDEX_0001 索引不存在` |
| `refer_config_body` | `udcReferConfigCreateConfigInfoPost` | 5388640036410513956（groupId） | — | `udcReferConfigDeleteByGroupIdPost` content=1；再删 content=0 |
| `event_body` | `udcEventPost` | -5445124548271606368 | — | `udcEventDeletePost` content=1 |
| `event_data_body` | `udcEventCreateWithDataPost` | 815500718291899191 | — | `udcEventDeletePost` content=1 |
| `app_version_list` | `ctp-application/appcenter/search-app-edition` | — | 回读到真实版本行 | 只读 |
| `app_build_info` | `udcSandboxBuildInfoAppGet` | — | state=SUCCESS / progress=100 / logs[] 全文 | 只读 |
| `app_dependency_body` | `udcApplicationDependentApplicationCreateBatchPost` | -3207627913631809273（cip-convert） | 列表 44→45 行 | `udcApplicationDependentApplicationDeleteByIdPost` → 回到 44 行 |

**serial 的关键**：`serialSectionDtoList` 里必须是 `CONSTANT` + `SERIAL` 各一个（`SERIAL` 恰好 1 个）。
`totalSize` = 各段 `size` 之和（4+6=10）。上传 `INCREASE` 会 `BOOT_3002`，枚举里没这个值。

**dto 佐证了 `notNull` 修复**：建出的 body 里属性是 `"notNull": false`，平台接受。
（旧版写 `isNotNull`，平台静默忽略不报错。）

## 2. 真 bug #8：`scalability_field_body` 的 `dataTypeProperties` 空串

```
dataTypeProperties=""    → BOOT_3000, message=null, data=null    ← 什么都没说
dataTypeProperties="{}"  → BOOT_0000 SUCCESS
```

做的最小对照（同一个 option，只改 props）：

```
A 工具原样(id=0 + appId + 空 props)   FAIL  BOOT_3000
B 补 props（保留 id=0/appId）          PASS
C' 删 id/appId + 空 props + 新 prefix  FAIL  BOOT_3000
D  有 id/appId + 空 props + 新 prefix  FAIL  BOOT_3000
```

⇒ **与 `id:0` / `appId` 无关，就是空字符串**。

再按类型验 `"{}"` 通用性：

```
LONG   + "{}"  PASS      LONG   + ""  FAIL
STRING + "{}"  PASS
DATE   + "{}"  PASS
DOUBLE + "{}"  PASS
```

⇒ 不用按类型分支，统一缺省 `"{}"` 即可。

已修：空/None/空白 → `"{}"`；显式传值原样保留（dict 转 JSON 字符串）。
回归守卫 `test_scalability_field_props_never_empty_string`，反向验证注入回空串 → 红。

## 2.5 真 bug #9 / #10：`event_data_body` 两处

修前提交 `udcEventCreateWithDataPost` 连挂两次，报错都不指向真因：

```
① eventDataList 传单对象
   → BOOT_3002 属性 eventDataList 的值反序列化为 ArrayList 类型时失败
② 包成数组后
   → BOOT_1001 属性名称 不能为空
```

**① 不是 DTO 声明问题，是真的要数组。**
上一轮曾据"前端 bundle 提交单对象"判定单对象正确 —— 实测推翻：GraphQL 层不负责包装，
DTO 声明 `List<DataTransferObjectDto>` 就是字面意思。已改成 `[event_data_list]`。

**② "属性名称"指的是 `caption`（显示名），不是 `name`。**
构造器只从 `sp["outputName"]` 取 name，直接传 `{"name":"f1"}` 落成 `name: null`；
而真正卡住的是 `caption` 取 `sp["description"]`，没给就空 → 报"属性名称不能为空"。
已加 `outputName or name` 回退。

修后建成功（id 815500718291899191），删除 content=1，事件列表 `content: []`。

**另一个反例**：`event_body`（裸事件，`udcEventPost`）的 `eventDataType: 0` 是**对的**，
平台接受。LIVE 记录里要求 `"OBJECT"` 的是 `udcEventCreateWithDataPost` 那条链 ——
两个接口不是一套枚举，别互推。

## 2.6 真 bug #11 / #12

### #11 `app_build_info` 的参数类型声明错了

```python
"query graphqlLoader ($params0: udcSandboxBuildInfoAppGetInputBody) { ... }"
→ GraphQL-3001 Unknown type udcSandboxBuildInfoAppGetInputBody
```

按惯例猜 `InputBody` 在这里不成立 —— 这个 operation 是 `path:` 入参，
平台没给它生成 InputBody 类型。实测候选：

```
udcSandboxBuildInfoAppGetInputBody   → Unknown type
udcSandboxBuildInfoAppGetInput       → Unknown type
udcSandboxBuildInfoGetInputBody      → Unknown type
Map                                  → BOOT_0000，content 正常返回
```

改成 `Map` 后拿到真实数据：`state=SUCCESS, progress=100, totalTime=267, logs[]` 全文。

### #12 `app_version_list` 的 `IN_appId` 必须传 appName

```
传数字 appId    → BOOT_0000，content: []
传 appName      → BOOT_0000，content 有真实版本行
```

注：代码注释里本来就写了「传 appName 而不是数字 appId」，是我调用时传错 —— 这条不算代码 bug，
但要记下来，因为**空数组不报错**，很容易被当成"这应用没版本"。

## 2.7 ⚠ 事故：误删平台内置依赖 cip-manager

验证删除接口时，我拿列表里现成的 `cip-manager` 行去试，`content: 1` 真的删掉了。
已用 create 补回，44 行不变、11 SERVICE / 33 FRONTEND 不变，但**依赖行 id 和版本变了**。

详见 `docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md`。

连带纠正一条错误认知：**`enableDelete` 不是安全闸**。
`cip-manager` / `app-common` / `cip-capability` 三条内置依赖的 `enableDelete` 都是 `true`，
平台照样删。契约和 docstring 里「内置依赖删不掉」的说法已改掉。

## 3. 契约与现实不符：excel 模板 create 404

`excel-template-contracts.md` 写 `setting.excel.template.create` 是 **LIVE PASS**，
路径 `POST /service/udc/excel/template/create`。实测：

```
/service/udc/excel/template/create  → Whitelabel 404（Spring 层无 mapping）
/udc/excel/template/create          → MethodNotAllowed（OSS 层，RequestId/HostId 是阿里云格式）
search 两个路径同样结果
```

⇒ **test2 上这条链现在不通**。可能是环境差异或路径变更，未查明。
标 **BLOCKED**，不当作工具问题。

## 4. 调用姿势（写给下一个跑的人）

- **REST 父级不处理子集合**：`scalability-option` 的 `update` 带 `attributeDtoList` 会被静默忽略，
  子项必须走 GraphQL `udcScalabilityPost`（契约 §★ 早就写了）。
- **`with-detail` 是 GET**，`PageFetch` 只支持 POST → 405。查方案用
  `POST /service/udc/scalability-option/select-all-optionName {appId}`。
- **GraphQL `params` 要 Map**：`query ($body: Map)` + variables 传对象，
  直接内联 `{IN_appId:[...]}` 会报 `Expected AST type 'MapValue' but was 'ObjectValue'`。
- **`SerialSchemeDto` 没有 `caption` 字段**（只有 `name`），查询带 `caption` 报 `FieldUndefined`。

## 5. 未验证（剩余 13 个）

```
application  1   app_deploy_body（会覆盖沙箱态，实施需授权）
                 app_dependency_remove 的 GraphQL 单删路径（REST 批删已验证）
entity       1   deploy_plan
setting      2   excel_template_body / excel_template_column（create 404，链不通）
flow         7   microflow_* 全套
page         4   list_page_schema / detail_page_schema / custom_page_scaffold / filter_plan_body
expression   1   expression_catalog
```

其中 5 个是只出 body 不发请求的（`app_dependency_*` / `app_deploy_body` / `app_version_list`
/ `app_build_info` / `deploy_plan`），要验证得自己发，成本高于收益，暂列未跑。
