# 一致性检测面的读源机制（LIVE 取证 + 定论）

> 结论先行：**`udcApplicationSearchDetectionPost` 读的是「当前应用未发布元数据的工作副本」，其载体是 MySQL `udc_*` 设计态表；
> Redis `Metadata:JSON:MD5:*` 只是失效戳（值形如 `1.0.7-20261013113125`），不含元数据正文；正文在发布镜像/OSS。**
> 因此"检测面落后于 DB"不是缓存，而是**未重新生成工作副本/未重新拉取**导致。

## 1. 直接证据链

| # | 观测 | 值 |
|---|---|---|
| 1 | 属性 `expEnum`（CTPENUM）三列 `relation_entity_name/relation_code/relation_app` | 修复前全 **NULL** |
| 2 | 同一应用其它 6 个 CTPENUM 字段 | 三列**齐备**（如 `syncMode` → `同步模式`/`SyncMode`/`8704...834`） |
| 3 | 平台真实 CTPENUM 字段（跨应用样本，如 `OAlcspzt`） | 三列齐备 |
| 4 | REST 修复（`POST /udc/entity/attribute/update`）→ 回读 | ✅ 三列已写入，`relationEntityName=小爪实验枚举953322`、`relationCode=XzhEnum953322`、`relationApp=8704025620829192834` |
| 5 | 检测面（检测 `UDC_CE_ENTITY_02104`） | **仍报**「Attr relation ctpEnum not exist」 |
| 6 | Redis `Metadata:JSON:MD5:{app}:udc@...Attribute.json` | 值 = `"1.0.7-20261013113125"`（**纯版本戳**，TTL ~450k s） |
| 7 | Redis `Metadata:JSON:MD5:{app}:udc@...MicroFlowEntity@FRONTEND@{id}.json` | **存在**（前端页面规则类） |
| 8 | Redis 中 `MicroFlowEntity@SERVICE@*` / 具体微流程 id 键 | **不存在**（应用内 scan 仅得 FRONTEND 族 + 无 id 的族根） |

## 2. 机制判定

```
设计态 MySQL udc_*  ←(权威源, REST 直写落此)
       │
       ├── 检测面（doParallel 阶段）读 = 【应用工作副本】（本轮实证：不随单表 UPDATE 立即变）
       │
       └── 发布 → 生成发布镜像 + 写 Redis Metadata:JSON:MD5:*（仅失效戳）
                        → 运行态读 OSS/镜像
```

- **Redis 不是检测面的读源**（值只是戳，没有正文可读）。
- **单表 REST 写不刷新检测面**：属性表已改、检测面不变 ⇒ 检测面消费的是**另一份快照**（工作副本），
  该快照在**应用级元数据重新生成**（发布/重新打开设计器/`disable-last-version-metadata` 一类动作）时重建。
- 这解释了历史现象：**页面 schema 修改后 `03108` 消失**——页面族走了会重建工作副本的路径；
  **属性/微流程族**在本轮动作下没走。

## 3. 操作含义（写作链时的硬规则）

1. **REST 写成功 ≠ 检测面立刻反映**；判定修复是否生效要**同时**看：(a) 目标表/接口回读，(b) 检测面（可能需触发重建）。
2. 想让检测面刷新，**不要**去等 Redis TTL；走**应用级重建**（发布链路 / 设计器重载 / 相关 rebuild 端点）。
3. 检测面 **同一应用内不同校验器读源不统一**（页面族 vs 属性/微流程族行为不同）——此点仍需单测确认，
   本轮标 **UNVERIFIED-读源分族**，不要一概而论。

## 4. CTPENUM 字段的权威字段契约（LIVE 定论）

CTPENUM（`data_type='CTPENUM'`）字段在 `udc_attribute` 的**必填四件套**：

| 列 | 值 | 例 |
|---|---|---|
| `relation_entity` | 目标枚举 id | `3934748939202274853` |
| `relation_entity_name` | 枚举 **caption** | `小爪实验枚举953322` |
| `relation_code` | 枚举 **name** | `XzhEnum953322` |
| `relation_app` | 归属 appId | `8704025620829192834` |

- `relation_type=1`（Many2OneAssociation）、`relation_entity_category=0`（ENTITY）
- **缺 `relation_entity_name` 即被检出 `UDC_CE_ENTITY_02104`**（"Attr relation ctpEnum not exist"）
  ——即使 `relation_entity`（枚举 id）本身完全正确。
- REST 面：`GET /udc/entity/attribute/{id}` → `POST /udc/entity/attribute/update`（body = 完整属性 DTO）。
- 该字段的 DTO 读面还带 `dataTypeDisplayName/relationType` 等**枚举字符串**（`CTPENUM`/`Many2OneAssociation`），
  而 DB 存 `relation_type=1` 数字 ⇒ 读写面做了值映射，**回传必须用读面返回的字符串形式**。
