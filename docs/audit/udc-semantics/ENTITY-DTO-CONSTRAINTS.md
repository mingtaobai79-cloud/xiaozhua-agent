# UDC 实体域 DTO 字段约束（后端权威，反编译 udc-common 5.3.517）

**证据源**：`udc-common-5.3.517.jar` 反编译
- `com.seeyon.udc.common.dto.EntityDto` / `EntityBaseDto`
- `com.seeyon.udc.common.dto.AttributeDto` / `BaseUdcAttributeDto`
- 约束来自 `javax.validation` 注解（`@NotNull` / `@NotBlank` / `@Length(max=...)` / `@Min(0)`）

**LIVE 回读验证**（test2 app=8704025620829192834）：**8 实体 + 190 属性全部满足必填约束，零误报**。

---

## 1. 实体创建/更新（EntityBaseDto + EntityDto）

| 字段 | 类型 | 必填 | 限制 | 说明 |
| --- | --- | --- | --- | --- |
| `appId` | Long | ★ | — | 实体所属应用Id |
| `name` | String | ★ | ≤21 (`UDC_ENTITY_0024`) | 实体编码（首字母大写） |
| `caption` | String | ★ | ≤50 (`UDC_ENTITY_0027`) | 实体名称 |
| `stereotype` | String | ★ | — | 业务版型 archive/standard/bill/archiveTree/form |
| `features` | String | ★ | — | 业务标签 basic/disable/treeEntity |
| `description` | String | | ≤200 | 描述 |
| `tableName` | String | | ≤100 | 运行态表名 |
| `searchable` | Boolean | | — | 启用全文检索（默认 true） |
| `parentEntityId` | Long | | — | 父实体Id（默认 NULL_ID） |
| `entityType` | String | | — | MASTER_ENTITY / SUB_ENTITY |
| `multiplicity` | EntityRelationMultiplicityEnum | | — | 关系基数（默认 ONE2MANY） |
| `category` | EntityCategoryEnum | | — | 实体类别（默认 ENTITY） |
| `fullName` / `dtoFullName` | String | | — | 实体/DTO fullName |
| `attributes` | List\<AttributeDto\> | | — | 属性列表 |

## 2. 实体属性创建/更新（BaseUdcAttributeDto + AttributeDto）

| 字段 | 类型 | 必填 | 限制 | 说明 |
| --- | --- | --- | --- | --- |
| `appId` | Long | ★ | — | 所属应用ID |
| `entityId` | Long | ★ | — | 实体主键ID |
| `name` | String | ★ | — | 属性编码 |
| `caption` | String | ★ | ≤255 | 属性名称 |
| `dataType` | String | ★ | — | 数据类型（ENTITY_DATA_TYPES 22 种） |
| `notNull` | Boolean | | — | 是否必填 |
| `minLength`/`maxLength`/`decimalDigits` | Integer | | ≥0 | 长度/小数位 |
| `multiSelect` | Boolean | | — | 是否多选 |
| `relationEntity`/`relationType`/`relationApp` | — | | — | 关联实体配置 |
| `dataFormat` | String | | ≤60 | 显示格式（DecimalFormat/DateFormat pattern） |
| `attributeGroup` | String | | ≤50 | 属性分组 |
| `inCondition` | Boolean | | — | 是否参与条件（默认 true） |
| `uniqueness`/`permission`/`auditLog` | Boolean | | — | 唯一/权限/审计 |
| `enableEncryption`/`encryption` | — | | — | 加密（默认 NOT_ENCRYPTION） |
| `enableDesensitization`/`desensitization` | — | | — | 脱敏（默认 None） |
| `system`/`hidden`/`edit`/`orderNo` | — | | — | 系统属性/隐藏/可编辑/排序 |
| `calculate` | AttributeCalculateEnum | | — | NORMAL/计算/聚合（默认 NORMAL） |
| `expressionDesignData`/`expressionRuntimeData` | String | | — | 表达式设计/运行态 schema |
| `defaultValueSystemVariable`/`defaultValueIsChange` | — | | — | 默认值系统变量/是否可改 |

## 3. 枚举
- **AttributeActionType**：ADD(0) / UPDATE(1) / DELETE(2) / DEFAULT(3)
- **stereotype**：archive / standard / bill / archiveTree / form
- **features**：basic / disable / treeEntity
- **multiplicity**：ONE2ONE / ONE2MANY

## 4. 机器可读模型
`components/udc/entity_constraints.py`：`ENTITY_FIELDS` / `ENTITY_REQUIRED` / `ATTRIBUTE_FIELDS` /
`ATTRIBUTE_REQUIRED` / `ENTITY_STEREOTYPES` / `ENTITY_FEATURES` / `ATTRIBUTE_ACTIONS` +
`validate_entity(body)` / `validate_attribute(body)`。

## 5. 属性列表接口真实 body（LIVE 修正）
`POST /service/udc/entity/attribute/search-list` 需 **`{"params":{"appId":...,"entityId":...}}`**
（裸 `{appId,entityId}` 返回 `BOOT_3000`）；方法签名 `@MultiRequestBody Map params, @MultiRequestBody Sort sort`。
