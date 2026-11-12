# CALL_APP_SERVICE（自定义服务）节点契约

取证：CDP 真实建节点 → 9 个服务逐个切换抓入参联动 → 无入参服务完整提交 → 后端 dataSchema 回读 → 前端 bundle `es={group:"base",name:"自定义服务",type:"CALL_APP_SERVICE"}` 权威定义交叉验证。
证据目录：`scratch/call_app_service-evidence/`。

## 1. 固定字段

| key | 标签 | 类型 | 必填 | 默认值 |
|---|---|---|---|---|
| `app` | 选择应用 | applicationSelector | ✅ | 当前应用 |
| `selectMethod` | 选择服务 | serviceMetadataMethodSelector | ✅ | — |
| `outputName` | 节点出参名称 | outputName | ✅ | — |

空提交实测报错：
```
selectMethod  请输入选择服务
outputName    请输入节点出参名称
```

## 2. 入参三形态（由服务签名决定，实测 9 个服务）

| 服务 | 触发字段 | 说明 |
|---|---|---|
| 获取当前应用文件中心配置 | 无参数字段 | 服务无入参，直接配出参名 |
| 文件复制 / 获取时效性下载url / 获取后端模式下载地址 / 获取下载地址 | `参数`（valueComponent，必填） | 单个非 DTO 入参 |
| 获取缩略图地址 / 修改文件名称 / 保存文件信息 | `赋值方式`（radio，必填）+ `参数映射`（选填） | DTO 入参，走字段映射 |
| 批量保存文件信息 | `赋值方式` + `参数`（选填） | 列表入参 |

联动规则（权威定义）：
```javascript
// 无入参
ishidden: (0,L.fI)(e.selectMethod?.parameter)
// DTO / MAP 入参
ishidden: [X.dataType === Dto, X.dataType === Map]
// 赋值方式选项
options: X.type === Array
  ? [{label:"对象引用", value:"value"}]
  : [{label:"字段映射", value:"attrs"},
     {label:"对象引用", value:"value"},
     {label:"自动映射", value:"mapping"}]
defaultval: X.type === Array ? "value" : "attrs"
```

## 3. 后端数据结构（无入参服务，已回读证实）

```json
{
  "nodeId": "CALL_APP_SERVICE_KsewfV",
  "type": "ACTIVITY",
  "actionType": "CALL_APP_SERVICE",
  "caption": "自定义服务(1)",
  "input": null,
  "output": {
    "id": "com.seeyon.boot.starter.file.dto.response.FileConfigDto",
    "javaType": "com.seeyon.boot.starter.file.dto.response.FileConfigDto",
    "dataType": "DTO",
    "type": "OBJECT",
    "desc": "服务调用结果",
    "appName": "datamigration9000000000000000001",
    "name": "_CALL_APP_SERVICE_5QT6V9"
  },
  "isCompleted": true,
  "app": {
    "appId": "9000000000000000001",
    "appName": "datamigration9000000000000000001",
    "caption": "数据迁移",
    "inApp": true,
    "udcApp": true,
    "dynamicDependency": "NONE"
  },
  "selectMethod": {
    "caption": "获取当前应用文件中心配置",
    "customs": null,
    "description": "获取当前应用文件中心配置",
    "dubbo": false,
    "dubboVersion": null,
    "fullName": "com.seeyon.boot.starter.file.appservice.FileAppService.getFileConfig",
    "group": null,
    "implClass": "com.seeyon.boot.starter.file.appservice.FileAppService",
    "interfaceClass": null,
    "md5": "1f4973e74fbd2b971fd83f98da988090",
    "parameter": null,
    "returnValue": {
      "caption": "文件中心配置",
      "type": "com.seeyon.boot.transport.SingleResponse",
      "item": {
        "enums": null,
        "itemType": "com.seeyon.boot.starter.file.dto.response.FileConfigDto",
        "item": null
      }
    },
    "isCondition": false
  },
  "outPutDesc": null,
  "outputName": "服务调用结果"
}
```

## 4. 关键认知

1. **`selectMethod` 存的是完整方法元数据**，不是简单引用：
   `fullName`（接口全名）、`implClass`、`md5`、`parameter`、`returnValue`、`isCondition`。
   回读时可直接拿到接口签名，无需再查 API 手册。
2. **`returnValue` 是 `SingleResponse<T>` 包装**：
   `item.itemType` 才是真实返回 DTO（此处 `FileConfigDto`），
   `output` 的 `javaType` 就是解包后的 `itemType`。
3. **出参名字段是 `outputName`**（不是其他节点常用的 `title`）。
4. **可选应用范围**：当前应用 + 所有依赖应用。实测当前环境可选项：
   `数据迁移 (当前应用) / 基础设置 / BPM引擎 / 报表中心 / 基础能力接入 / 连接器 / 集成平台 / 事项中心 / 消息中心`。
5. **`type` 恒为 `ACTIVITY`**，回读用 `actionType == 'CALL_APP_SERVICE'`。
6. **`outPutDesc` 大小写陷阱**：是 `outPutDesc`（P 大写），不是 `outputDesc`。
