# 微流程的草稿态与发布态（state 生命周期）

> 状态：LIVE（2026-10-24，反编译 + DB 全量分布 + 一次 LIVE 改态验证）

## 铁律

- `state` 只有两个值：**`DRAFT(10)` 草稿** / **`RELEASE(20)` 发布**
- **`type=SERVICE` 的微流程，create 时后端强制把 state 改成 DRAFT**，入参传 20 无效
- **发布 = 再调一次 `update` 并把 `state` 传 20**，没有单独的"发布"按钮接口
- `state=RELEASE` 才会触发 `checkSchema` 深度解析；草稿态的 checkSchema 是浅校验，过了不代表能用
- 运行时到处按 `RELEASE` 过滤 —— 草稿流程**不执行、不能被引用、不进上架包、定时任务不跑**
- `publish_state` 是**另一个维度**，与 `state` 不是非此即彼的关系（见 §5）

## 1. 枚举（反编译权威）

```java
// com.seeyon.udc.common.enums.MicroFlowDataStateEnum
DRAFT(10), RELEASE(20)
```

`publish_state` 参考值：`PublishStateEnum { PUBLISHED(0), UNPUBLISH(1) }`，
但微流程表里 4758/4779 条是 `1`，与"UNPUBLISH 占 99%"矛盾 ⇒
**微流程的 `publish_state` 大概率不是这个枚举**，语义未定（§5）。

## 2. create 强制 DRAFT（根因）

`MicroFlowAppService` 里有一段在 create 前跑的修正：

```java
private void ...(MicroFlowDefinitionDto dto) {
    if (MicroFlowTypeEnum.SERVICE.equals(dto.getType())) {
        dto.setState(MicroFlowDataStateEnum.DRAFT);      // ← 传什么都覆盖成草稿
    }
}
```

⇒ 所以 `POST /service/udc/microflow/create` 传 `state:20`，
  DB 落的是 `state=10`。这不是接口 bug，是设计。

只有 `type` 非 SERVICE 的（实体规则/页面规则等）可能保留传入值。

## 3. 发布 = update 传 state=20（LIVE 证）

```
DB 前      state=10  publish_state=1
POST update {完整 DTO, state:20}
           → BOOT_0000, content=1
POST checkSchema/update
           → BOOT_0000, {check:true, errors:0}
DB 后      state=20  publish_state=1
```

要点：

- `update` 要**完整 DTO**（id/appId/name/caption/type/triggerType/state/
  creationMethod/description/serviceInterface/dataSchema），只传 id+state 不行
- REST 侧只有这些路径可用：`/create` `/update` `/delete` `/checkSchema`
  `/checkSchema/update`；`getMicroFlowDefinition` 这类读接口是 **GraphQL**
  （`udcMicroflow*Post`），REST 上打会 404
- `create` 对 `dataSchema` **不做结构校验**（传 `"{}"` 也能建成草稿），
  真正的门禁在 RELEASE 那一步

## 4. 运行时按 RELEASE 过滤的位置

| 位置 | 条件 | 后果 |
|---|---|---|
| `MicroFlowService` | 11 处 `.andEqualTo("state", RELEASE)` | 草稿查不到 |
| `CtpJobTask` / `CtpJobTaskV27` | 定时任务查 `state=RELEASE` | 草稿定时任务不跑 |
| `MicroFlowComponentUtils` | `DRAFT == dto.getState()` → 报错 | 草稿不能被 `SUB_MICROFLOW` 引用 |
| `ApplicationShelf4UdcServiceImpl` | `.andNotEqualTo("state", DRAFT)` | 草稿不进上架包 |
| `MicroFlowMetaDataPostProcessor` | `RELEASE.equals(state)` 才处理 | 草稿不生成元数据 |
| `AbstractMicroFlowFrontDeployDetectionTask` | `predicate = RELEASE` | 部署检测跳过草稿 |
| `CheckUtils` | `RELEASE == state` 才进 switch | 草稿不做完整解析 |
| `MicroFlowFrontEndService` | 子流程 `DRAFT` → 报错 | 前端规则引用草稿子流程失败 |

⇒ **草稿 = 设计态草稿，运行期完全不参与**。

## 5. publishState 的语义（已闭合，2026-10-24）

**`publishState` = 元数据产物是否已重新生成，不是"流程是否启用"。**

反编译证据 `PublishStateAddMetadataInterceptor`：

```java
boolean notMicroFlowDraftData = !(udcBaseEntity instanceof MicroFlowEntity)
    || ((MicroFlowEntity) udcBaseEntity).getState().equals(MicroFlowDataStateEnum.RELEASE);
if (notMicroFlowDraftData) {
    entityList.forEach(e -> e.setPublishState(PublishStateEnum.PUBLISHED));
}
```

⇒ **`state=RELEASE` 是前置条件；元数据生成后 `publishState` 自动转 `PUBLISHED(0)`。**

而任何更新都会把它打回待生成：

```java
// MicroFlowService
definitionDto.setPublishState(PublishStateEnum.UNPUBLISH);   // 更新即置为待生成
// MicroFlowUpgradeAppServiceImpl
dto.setState(MicroFlowDataStateEnum.RELEASE);
dto.setPublishState(PublishStateEnum.UNPUBLISH);             // 升级后同样待生成
```

**这解释了 DB 分布**：

```
state=10 + publish_state=1   271 条   ← 草稿（元数据不会生成）
state=20 + publish_state=1  4487 条   ← 已发布但元数据还没重新生成（常态，99.5%）
state=20 + publish_state=0    21 条   ← 发布且元数据已生成
```

★ 结论：**判断流程是否生效只看 `state`**；`publishState=1` 不代表没发布，
  只代表"元数据待刷新"，这是绝大多数流程的常态。
  之前把它按 `PUBLISHED(0)/UNPUBLISH(1)` 直译成"99.5% 未发布"是错的。

## 6. 对生成器/CLI 的含义

```
create  → 必然得到 DRAFT（type=SERVICE）
         → 若要"建完就能用"，必须紧跟一次 update(state=20)
         → 但 update 需要完整 DTO，所以 create 时要把完整字段都存下来
```

`tools/core/microflow/build_microflow.py` 目前只做 create，产出的是草稿。
若要一步到位，需在 create 成功后用返回 id 拼完整 DTO 再 update —— 尚未实现（待办）。
