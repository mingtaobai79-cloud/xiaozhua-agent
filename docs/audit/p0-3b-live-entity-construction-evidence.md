# P0-3B Entity Construction Live Artifact Evidence

更新时间：2026-09-04

## 范围

- 环境：`test2`
- 访问路径：SSH `root@10.0.0.1` → `kubectl --kubeconfig=configtest2`
- Namespace：`lowcode-test`
- UDC Pod：`udc-7cbfc587f5-kwjdd`
- UDC 镜像：`chit-acr-registry.客户方.com/chjh-external/udc:5.3.517`
- 证据类型：真实运行 Pod 中的 JAR 清单与 `javap` 字节码；只读

## 1. 运行入口

UDC Pod 日志观察到真实设计器请求：

```text
request url:/udc/graphql
```

这证明 test2 UDC 运行实例实际接收 GraphQL 请求，但日志没有暴露每次请求的 GraphQL field，因此不能单独证明某次请求就是 `udcEntityPost`。

## 2. EntityController

真实 Artifact：

```text
/root/appdata/udc/local/backend/jarpath/udc-web-5.3.517.jar
```

真实类：

```text
com.seeyon.udc.controller.EntityController
```

类级别注解常量：

```text
@RestController
@RequestMapping("udc/entity")
@RestApi("实体管理接口")
@HasRole("udcAppDesigner", "udcSystemAdmin")
```

创建方法字节码/注解：

```text
public SingleResponse<Long> create(EntityDto dto)
@RestApiOperation("1.1:创建实体")
@PostMapping
@RequestBody EntityDto
```

调用关系：

```text
EntityController.create(EntityDto)
  → SingleRequest.from(dto)
  → EntityAppService.create(SingleRequest<EntityDto>)
```

## 3. EntityAppServiceImpl

真实 Artifact：

```text
/root/appdata/udc/local/backend/jarpath/udc-biz-5.3.517.jar
```

真实类：

```text
com.seeyon.udc.appservice.EntityAppServiceImpl
```

创建方法调用：

```text
EntityAppServiceImpl.create(SingleRequest<EntityDto>)
  → request.getData()
  → EntityService.create(EntityDto)
  → SingleResponse.from(Long)
```

## 4. EntityService.create

真实类：

```text
com.seeyon.udc.entity.domain.service.EntityService
```

已从 `javap -p -c` 确认的顺序：

```text
ApplicationService.selectById(dto.appId)
ApplicationService.checkApplicationNull(...)
生成或保留 dto.guid
DbUtils.getDbTableName(...)（tableName 为空时）
checkEntityLevel(...)
validationEntityDto(...)
validateRelation(...)
Stereotypes.applyStereotype(dto)
new Entity()
Entity.from(dto)
Entity.setGuid(guid)
EntityDao.create(entity)
EntityDto.setId(entity.getId())
Stereotypes.apply(dto)
createChildAttribute(dto)
AttributeSetService.createAttributeFromAttributeSet(...)
new EntityCreateEvent(...)
EventBus.publish(event)
ConsistenceDetectionService.createDetection4Dto(...)
OperationLogService.logCreate(...)
return entity.getId()
```

关键落库字节码：

```text
Entity.from(Object)
EntityDao.create(Object)
Entity.getId()
EntityDto.setId(Long)
```

因此以下边界已由真实 5.3.517 字节码闭合：

```text
EntityDto → Entity → EntityDao.create(Entity)
```

## 5. Metadata / Generator 边界

UDC 运行包中确认存在：

```text
udc-starter-autocode-5.3.517.jar
boot-starter-metadata-5.3.358.jar
udc-common-5.3.517.jar
udc-starter-lowcode-5.3.517.jar
```

AutoCode 类：

```text
com.seeyon.boot.starter.autocode.engine.CodeEngine
com.seeyon.boot.starter.autocode.engine.SimpleCodeEngine
com.seeyon.boot.starter.autocode.handler.CodeHandler
com.seeyon.boot.starter.autocode.handler.MetaDataHandler
com.seeyon.boot.starter.autocode.handler.LazyCacheableAutoCodeTask
com.seeyon.boot.starter.autocode.context.AutoCodeContext
```

`SimpleCodeEngine.execute(AbstractLazyCacheableContext)` 的字节码确认：

```text
创建 CompletionExecutor("代码生成", 30000)
遍历 LazyCacheableAutoCodeTask
为每个 task 创建 NamedFutureTask
调用 task.code(context)
等待 CompletionExecutor.waitTimeout()
```

但在本轮已取得的字节码中，尚未出现以下直接调用边：

```text
EntityCreateEvent → MetadataCreateAppService
EntityService.create → MetadataService.createMetadata
MetadataService → AutoCodeContext
某个 EntityCreateEvent listener → SimpleCodeEngine.execute
```

因此不能把 AutoCode 类存在升级成 Entity 创建后的 Generator 因果证据。

## 6. 当前状态

```text
Frontend createEntity → udcEntityPost          VERIFIED_STATIC_SOURCE
真实 UDC GraphQL 入口 /udc/graphql             VERIFIED_LIVE_RUNTIME_LOG
EntityController.create                         VERIFIED_STATIC_BYTECODE
EntityController → EntityAppService.create     VERIFIED_STATIC_BYTECODE
EntityAppServiceImpl → EntityService.create    VERIFIED_STATIC_BYTECODE
EntityService → EntityDao.create                VERIFIED_STATIC_BYTECODE
EntityCreateEvent / consistency / audit log      VERIFIED_STATIC_BYTECODE
Metadata generic storage contract                VERIFIED_STATIC_BYTECODE
Entity create → Metadata                       UNVERIFIED
Metadata → AutoCodeContext                     UNVERIFIED
AutoCodeContext → generated source              UNVERIFIED
GraphQL field udcEntityPost → Java binding       UNVERIFIED
```

## 7. 安全边界

本轮只读查询真实 Pod、JAR 清单和字节码，没有执行：

- 创建实体
- 修改实体
- 数据库写入
- Redis 写入
- Nacos 修改
- Kubernetes apply/patch/delete/restart

私密配置、token、密码和 kubeconfig 内容不写入本证据文件。
