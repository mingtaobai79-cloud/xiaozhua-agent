# UDC Entity Operation Contract Evidence

结论：STATIC FACTS 部分闭合；HTTP method/path 已由目标 test2 UDC 5.3.517 字节码常量池与方法注解证实。实际网络调用、认证 header、响应 envelope 和应用映射仍为 UNVERIFIED。

## Scope

- Parent component: Seeyon Agent
- Component: UDC
- Environment: test2 via SSH 10.0.0.1 → `kubectl --kubeconfig=configtest2`
- Namespace: `lowcode-test`
- Pod: `udc-7cbfc587f5-kwjdd`
- Artifact: `udc-web-5.3.517.jar` inside `/app/udc-assemble.jar`
- Controller: `com.seeyon.udc.controller.EntityController`

## Controller boundary

Class facts:

```text
@RestApi("实体管理接口")
@RequestMapping("udc/entity")
@HasRole({"udcAppDesigner", "udcSystemAdmin"})
```

## Verified operation table

| operation | HTTP | relative path | Java method | request | response | status |
|---|---|---|---|---|---|---|
| entity.create | POST | `udc/entity` | `create(EntityDto)` | `@RequestBody EntityDto` | `SingleResponse<Long>` | VERIFIED_STATIC_BYTECODE |
| entity.update | POST | `udc/entity/update` | `update(EntityDto)` | `@RequestBody EntityDto` | `SingleResponse<Integer>` | VERIFIED_STATIC_BYTECODE |
| entity.select_by_id | GET | `udc/entity/{id}` | `selectById(Long)` | `@PathVariable id` | `SingleResponse<EntityDto>` | VERIFIED_STATIC_BYTECODE |
| entity.search | POST | `udc/entity/search-list` | `selectListByConditions(Map, Sort)` | request body / framework binding | `ListResponse<EntityDto>` | VERIFIED_STATIC_BYTECODE |
| entity.search_term | GET | `udc/entity/search/term` | `selectListByTerm(Long, String, Sort)` | `appId`, `term` | `ListResponse<EntityDto>` | VERIFIED_STATIC_BYTECODE |
| entity.primary_by_app | GET | `udc/entity/primary/select-by-appid/{appId}` | `selectPrimaryEntityByAppId(Long)` | `@PathVariable appId` | `ListResponse<EntityDto>` | VERIFIED_STATIC_BYTECODE |
| entity.tree_by_app | GET | `udc/entity/select-by-appid/tree/{appId}` | `selectEntitiesByAppId4Tree(Long)` | `@PathVariable appId` | `ListResponse<EntityDto>` | VERIFIED_STATIC_BYTECODE |
| entity.all_by_app | GET | `udc/entity/select-all-by-appid/{appId}` | `selectAllEntitiesByAppId(Long)` | `@PathVariable appId` | `ListResponse<EntityDto>` | VERIFIED_STATIC_BYTECODE |
| entity.root_id | GET | `udc/entity/primary/select-root/{id}` | `selectRootId(Long)` | `@PathVariable id` | `SingleResponse<Long>` | VERIFIED_STATIC_BYTECODE |
| entity.all_by_entity | GET | `udc/entity/select-all-by-entityId/{id}` | `selectAllEntitiesByEntityId(Long)` | `@PathVariable id` | `ListResponse<EntityDto>` | VERIFIED_STATIC_BYTECODE |
| attribute.create | POST | `udc/entity/attribute` | `createAttribute(AttributeDto)` | `@RequestBody AttributeDto` | `SingleResponse<Long>` | VERIFIED_STATIC_BYTECODE |
| attribute.create_batch | POST | `udc/entity/attribute-batch` | `createAttributionBatch(List<AttributeDto>)` | `@RequestBody List` | `SingleResponse<Integer>` | VERIFIED_STATIC_BYTECODE |
| attribute.update | POST | `udc/entity/attribute/update` | `updateAttribute(AttributeDto)` | `@RequestBody AttributeDto` | `SingleResponse<Integer>` | VERIFIED_STATIC_BYTECODE |
| attribute.delete | POST | `udc/entity/attribute/delete` | `deleteAttributeById(Long)` | framework parameter binding | `SingleResponse<Integer>` | VERIFIED_STATIC_BYTECODE |
| attribute.select_by_id | GET | `udc/entity/attribute/{id}` | `selectAttributeById(Long)` | `@PathVariable id` | `SingleResponse<AttributeDto>` | VERIFIED_STATIC_BYTECODE |
| attribute.search | POST | `udc/entity/attribute/search-list` | `selectEntityAttributeListByCondition(Map, Sort)` | request body / framework binding | `ListResponse<AttributeDto>` | VERIFIED_STATIC_BYTECODE |
| attribute.search_term | GET | `udc/entity/attribute/search/term` | `selectAttributeListByTerm(Long, String, Sort)` | `appId`, `term` | `ListResponse<AttributeDto>` | VERIFIED_STATIC_BYTECODE |
| attribute.by_primary | GET | `udc/entity/attribute/select-by-primary/{id}` | `selectByPrimaryEntityId(Long)` | `@PathVariable id` | `ListResponse<AttributeDto>` | VERIFIED_STATIC_BYTECODE |
| attribute.all_by_entity | GET | `udc/entity/attribute/select-all-by-entity-id/{entityId}` | `selectAllAttributeByEntityId(Long)` | `@PathVariable entityId` | `ListResponse<AttributeDto>` | VERIFIED_STATIC_BYTECODE |

## DTO facts

`EntityDto` extends `EntityBaseDto`; create input must be modeled separately from readback output. Relevant fields include `appId: Long`, `name`, `caption`, `description`, `entityType`, `parentEntityId`, `attributes`, `children`, `indexes`, and generation flags.

`AttributeDto` extends `BaseUdcAttributeDto`; relevant fields include `appId: Long`, `entityId: Long`, `name`, `caption`, `dataType`, `notNull`, `description`, `searchable`, `defaultValue`, `relation*`, `orderNo`, and source/security/display fields.

The minimum accepted create payload is NOT yet asserted. Do not infer required fields from Java field presence.

## Call-chain facts

```text
EntityController.create(EntityDto)
  → SingleRequest.from(dto)
  → EntityAppService.create(SingleRequest<EntityDto>)

EntityController.createAttribute(AttributeDto)
  → SingleRequest.from(dto)
  → AttributeAppService.create(SingleRequest<AttributeDto>)

EntityController.selectById(Long)
  → SingleRequest.from(id)
  → EntityAppService.selectById(SingleRequest<Long>)

EntityController.selectAllAttributeByEntityId(Long)
  → SingleRequest.from(entityId)
  → AttributeAppService.selectAllAttributeByEntityId(SingleRequest<Long>)
```

## Explicit non-claims

- No real write was executed.
- No authentication/header contract has been verified.
- No GraphQL operation has been mapped to these REST-style controller methods.
- No application string ID → numeric `appId` mapping has been verified.
- No response JSON envelope has been observed.
- No publish/build/readback execution has been verified.
- Controller annotations prove route facts, not successful external accessibility.

## Evidence command

Targeted `javap -v -p` on the target pod's `udc-web-5.3.517.jar`; method descriptors, annotation constants, class mapping and bytecode invocation were inspected.
