# udc.metadata.storage｜UDC 设计态元数据存储机制（九段式机制格）

> 基线：udc-biz/udc-web/boot-starter-metadata/boot-starter-file 5.3.517（CFR 反编译，逐条行号锚定）。
> 本件只写机制（存储载体/读写链/预制物），客户业务 0 入件，凭据 0 入仓。
> 反编译源存 scratch（不进仓库），本格只留结论+类名:行号索引。

---

## 1. 结论一句话

**设计态权威存储 = MySQL 业务表（udc_entity / udc_attribute / …）；运行态读取 = CTP 元数据中心的
Redis Hash（权威缓存，180h TTL）+ OSS JSON 文件（持久镜像）；
"发布"= 把 DB 设计态数据导出为元数据写入 Redis+OSS（LastVersionMetadata 快照落 udc_last_version_metadata）。**
不存在"元数据只存 JSON 预制"的情况——JSON 预制仅用于**子实体的系统属性模板**（见 §6）。

## 2. 读写链（反编译实证）

### 写链（设计态，如 POST /service/udc/entity）
```
EntityController.create                        (udc-web, javap #4)
  → EntityAppServiceImpl.create                (udc-biz, EntityAppServiceImpl.java:111, @Transactional)
    → EntityService.create                     (udc-biz, EntityService.java:320)
        ├ applicationService.selectById        校验应用
        ├ Ids.gidLong()                        guid 雪花（:326）
        ├ DbUtils.getDbTableName               tableName={name}_{gid}（:329）
        ├ dao.create(entity)                   ★ MyBatis 落 MySQL udc_entity（:345）
        ├ createChildAttribute                 子实体系统属性（:351，预制 JSON 见 §6）
        ├ eventBus.publish(EntityCreateEvent)  （:356）
        └ detectionService.createDetection4Dto 局部一致性检测（:360）
```
- 表：`Entity.java @Table(name="udc_entity")`（唯一键 app_id+name+tenant_id）；
  `Attribute.java @Table(name="udc_attribute")`；快照表 `udc_last_version_metadata`。
- dao = `BaseMybatisDao<Entity>`（EntityDao）。**雪花 id 由 BaseMybatisDao 侧生成**（MyBatis-Plus 雪花，EntityService 未手动 setId——entity.getId() 在 create 后回填 :346）。

### 读链（运行态）
```
UdcEntityMetadata4OssService.selectEntityItemByAppName     (udc-common, javap)
  → MetadataQueryAppService.selectJsonMetadata             (boot-starter-metadata, MetadataQueryAppService.java:1056)
    → MetadataService.selectJsonMetadata                   (:640)
        storageKey = {env}:Metadata:JSON:{appName}:{jsonFileName}   (MetadataRedisKeyUtils)
        Redis 版本号(md5) 比对 → JSON_CACHE(guava) → miss 则 fileService.download(OSS)
```

### 存储（MetadataService 反编译，boot-starter-metadata 5.3.358）
| 载体 | 角色 | 证据 |
|---|---|---|
| Redis Hash `{env}:Metadata:{Type}:{appName}` | **运行态权威读缓存**（180h TTL），`createMetadata` 直写（:552-555） | MetadataService.java |
| MD5 key `{env}:Metadata:MD5:{Type}:{appName}` | 版本比对（变更检测） | :538-547 |
| OSS（file.storage-type: oss，bucket seeyon-private-test2，nacos raw-02:578/590-597） | **持久镜像**：`syncSave2Storage→fileService.uploadForPublicNoDB`（:1450）；读 miss 时 `loadMetadataFromStorage` 回灌 Redis（:1716-1733） | MetadataService.java + nacos 配置证据 |
| MySQL udc_* 表 | **设计态权威源**（udc_entity/udc_attribute/udc_page_info/...） | @Table 注解逐字 |

### 元数据写入触发（createMetadata :533 / createJsonMetadata :473）
- 元数据"入库"= 写 Redis Hash + 异步镜像 OSS（`asyncSave2Storage` :637/:1354/:1408）。
- 触发方 = 应用**构建/发布**流水线（udc_last_version_metadata 快照 + LastVersionMetadata*Service.prepareLastVersionAfterDeployed，
  EntityLastVersionMetadataService.java:31-56：UNPUBLISH→PUBLISHED 翻转 + schema JSON 序列化）。
- 这解释了已知事实"C2b 运行态元数据面只回读已发布页"——**发布前设计态写只在 MySQL，运行态面看不见**。

## 3. JSON 预制物（唯一一处，修正点）

`EntityService.createChildAttribute`（:371-375）：
```java
List attributeList = FileUtils.jsonToBeanList("presetData/attribute.json", Attribute.class);
// 子实体(bill detail)创建时，从 classpath 预制 JSON 读出 parentId/orderNo 系统属性模板，
// 按 multiplicity 设 One2Many/One2OneAggregation 后落 udc_attribute
```
- **预制 JSON 只是"系统属性模板"**（parentId/orderNo 两条），不是实体/属性元数据的主存储。
- 用户在 deployment.py 看到的"平台自动补单据族系统属性"即此通道。

## 4. 对 agent 能力面的推论

1. 设计态写（entity/attribute.create）**只动 MySQL** → 写后立刻走 C2b 运行态读面查不到 = 预期，不是 bug。
2. 运行态元数据不一致排查顺序：Redis Hash（实时）→ OSS JSON（发布镜像）→ MySQL udc_*（设计态真源）。
3. `selectJsonMetadata` 的 jsonFileName=`udc@<实体全名>.json` 是**发布产物**，随构建生成——它的内容源头仍在 MySQL。
4. 之前 build-chain 已证的"检测明细只在 Redis"与本机制同构：Redis 是过程态，OSS/MySQL 是持久态。

## 5. Verified（逐项）

| 项 | 等级 | 依据 |
|---|---|---|
| 建实体落 udc_entity（MyBatis） | **VERIFIED_STATIC_SOURCE**（CFR 反编译） | EntityService.java:320-370；Entity.java @Table |
| udc_attribute 表 + 唯一键 | VERIFIED_STATIC_SOURCE | Attribute.java @Table 逐字 |
| 运行态读 = Redis→OSS→回灌 | VERIFIED_STATIC_SOURCE | MetadataService.java:640-661/1716-1740 |
| 元数据写入 = Redis+OSS 镜像 | VERIFIED_STATIC_SOURCE | MetadataService.java:533-586/1450 |
| test2 存储后端=OSS（非 NFS） | OBSERVED_LIVE（nacos 实配） | u6-nacos raw-02:578 `file.storage-type: oss` |
| publishState 翻转在发布时 | VERIFIED_STATIC_SOURCE | EntityLastVersionMetadataService.java:37-39 |
| 子实体系统属性来自 presetData/attribute.json | VERIFIED_STATIC_SOURCE | EntityService.java:371-375 |
| 雪花 id 生成点（BaseMybatisDao 内部） | UNVERIFIED（未反编译 boot 基类，只锚定回填点 :346） | 推断非断言 |

## 6. 溯源索引

| 件 | 位置 |
|---|---|
| MetadataService.java / MetadataRedisKeyUtils.java（CFR） | scratch md561（不进仓），类名:行号已锚 |
| EntityService/EntityAppServiceImpl（CFR） | 同上；jar=Artifactory udc-biz/udc-web 5.3.517 |
| nacos test2 file.storage-type | docs/audit/artifacts/u6-nacos-config/raw-02-nacos-configs.md:578 |
| CTP 读面 AppService | boot-starter-metadata MetadataQueryAppService.java:1056 |
