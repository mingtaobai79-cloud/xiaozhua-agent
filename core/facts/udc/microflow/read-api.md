# 微流程的接口读取（不靠数据库）

> 状态：LIVE（2026-10-24，接口实测 + 后端 DTO 反编译交叉）

## 铁律

- **DB 只是取证工具，不是验证通道**。客户环境通常没有 DB 权限，接口才是通用路径。
- **接口写成功必须由接口读闭环**；用 DB 回读验证的是存储层，不是平台契约。
- 列表接口 `udcMicroflowServiceListPost` **不过滤草稿**，`state` 原样返回。
- **`state` 在接口里是字符串枚举名 `DRAFT` / `RELEASE`**，DB 里才是数字 `10` / `20`。
- GraphQL 的 `pageInfo` 在 **`data{}` 层**，不在 `content{}` 里（放错会报「pageInfo 不在 MicroFlowSubMfDto 中」）。
- **`data.content` 是数组**，不是对象；每组里挂 `microFlowServiceInfoDtos[]`。

## 1. 列表接口契约（已 LIVE 验证）

```
op    : udcMicroflowServiceListPost
body  : {pageInfo:{needTotal,pageNumber,pageSize,pages,total},
         params:{appId},
         sort:{orders:[{direction,property}]}}

queryFields:
  code
  data {
    content {                       ← 数组，元素类型 = MicroFlowSubMfDto
      appId
      caption
      groupId
      microFlowServiceInfoDtos {    ← 真正的微流程条目
        id appId name caption description type triggerType state
        path method hostPath hasInput hasOutput
      }
    }
    pageInfo { needTotal pageNumber pageSize pages total }   ← ★在 data 层
  }
  message
  status
```

实测返回（本应用）：

```
state 分布: {'DRAFT': 1, 'RELEASE': 9}     ← 草稿也在列表里
-5581540218594804639  RELEASE  SERVICE  xzhApiProbe
-7241102129168964356  DRAFT    SERVICE  xzhStateProbe
```

⇒ 所以「出现在列表里」**不等于**「已发布」，必须看 `state`。
  （对比：`udcMicroflowSearchEntityRulePost` 只返 RELEASE，两个接口语义不同。）

## 2. 返回 DTO 的权威字段

`MicroFlowServiceInfoDto`（17 字段，反编译）：

```
id appId appName appCaption name path hostPath method
caption description groupId
type(MicroFlowTypeEnum) triggerType(MicroFlowTriggerTypeEnum)
input(MicroFlowParameterDefDto) output(MicroFlowParameterDefDto)
outputDetail(MicroFlowOutputDetailDto) state(MicroFlowDataStateEnum)
```

★ **这个 DTO 没有 `dataSchema`** ⇒ 列表/详情接口读不到节点内容。
  读 schema 只有 `MicroFlowDefinitionDto`（`getMicroFlowDefinition` /
  `selectDetailsBySourceId`），而它们的 GraphQL op 名尚未定位（见 §4）。

## 3. GraphQL 类型名 = 包路径去点 + 类名

报错里出现：

```
Field 'pageInfo' in type 'UdccomseeyonudcmicroflowdtodefinitionMicroFlowSubMfDto' is undefined
```

⇒ 类型名规则：`Udc` + 包路径去掉点 + 类名。
  排查 FieldUndefined 时可以直接从类型名反推是哪个 DTO。

## 4. op 名 ≠ 方法名（规则已定位，见 graphql-op-naming.md）

后端 `@AppServiceOperation` **只有中文 `value`，没有 op 名**：

```java
@AppServiceOperation(value="跟据ID查询微流程")
public SingleResponse<MicroFlowDefinitionDto> getMicroFlowDefinition(SingleRequest<Long> r)
```

op 名由元数据的 `path + httpMethod` 算出（`GraphQLProvider.pathToCamel`）：

```
op = pathToCamel(path + "/" + httpMethod.toLowerCase())
   去 {} → toCamelCase(首字母小写, '-','/','_') → 去非字母数字
   → 去尾 "Id" → "IdGet$"→"Get" → "SearchPost$"→"Search"
```

例：`/udc/microflow/serviceList` + `post` → `udcMicroflowServiceListPost` ✓（实测一致）

对比已知配对：

| GraphQL op | 后端方法 | 结果 |
|---|---|---|
| `udcMicroflowSearchAppsPost` | `searchApps` | 名字一致（path 恰好同名） |
| `udcMicroflowSearchAppServiceByAppNamePost` | `searchAppServiceByAppName` | 名字一致 |
| `udcMicroflowServiceListPost` | 无同名方法 | **对不上**（path 叫 serviceList） |
| `udcMicroflowDisableNodePost` | 无同名方法 | **对不上** |

⇒ 想读 `dataSchema`，需要 `MicroFlowDefinitionDto` 那两个方法的元数据 path；
  而元数据在 ctp-metadata 服务，本环境 DB 里没有 RestApi 元数据表。
  另：这些 AppService 方法**只注册 GraphQL，不暴露 REST**（探 9 条路径全 404）。

## 5. 读 vs 写 的分工

| 用途 | 通道 | 说明 |
|---|---|---|
| 验证是否已发布 | `udcMicroflowServiceListPost` 读 `state` | **常规验证走这条** |
| 判断运行期是否生效 | 同上，`state == "RELEASE"` | 运行期按 RELEASE 过滤（见 state-lifecycle.md） |
| 读节点内容 | 暂无接口 | 需要 `MicroFlowDefinitionDto` 的 op 名 |
| 内部取证/分布统计 | DB | 仅调试用，不作为交付路径 |

## 6. 代码入口

```
components/udc/microflow/read.py
  list_services(client, app_id, page_size=200) -> list[dict]
  find_service(client, app_id, service_id)     -> dict | None
  is_release(svc) / state_of(svc)
```

`tools/core/microflow/build_microflow.py` 的 `_verify` 默认用它读回；
`--verify-db` 才额外做一次 DB 交叉校验。
