# VERDICT｜门1-C 反编译批复执行：四问逐条答

> auditor　｜　2026-10-18 02:40 (GMT+8)　｜　STATIC（CFR 0.152）+ Redis/DB 只读
> 触发：main DECISION「授权反编译，重点改四个具体问题」
> 版本锚：**udc 5.3.517**（`udc-cicd-5.3.517` / `udc-biz-5.3.517` / `udc-plugin-api-5.3.517` 全解包）

## ⚠ 本报告内有 1 处自我纠错（必读）

**我在 02:10 的 VERDICT 报「184 个一致性检测项」——这个数字是错的，正确是 1074 个。**
错因：我从实现类 grep 字面量，只抓到写死的码；权威全集在
`ConsistenceDetectionCodeEnum`(997) + `ConsistenceErrorCode`(1032)，并集 1074。
本报告 §3 已修正，**§4 已在 1074 全集下重做复核，结论不变**。

---
## 类 sha256（main 要求）

| 类 | sha256 |
|---|---|
| `AbstractDeployService.class` | `3afef84e693590fdf9cd2a68980fe2614bb46c3fece0a7a6cdc977bfb68c6855` |
| `NormalDeployService.class` | `0440dae9f752395437340d0ec32923cb16ee85d8628f95ecc63dbf0f29f0cf2a` |
| `PipeLineManager.class` | `62322dbf428a3535f9371c9f43b75d73032dc79b5007c0c99a3465a807effdeb` |
| `DetectionManager.class` | `09ff6907e6bebf495cbeb2e7d6181858719ec22518a52ae7305dc222cf5e0a67` |
| `DetectionExecuteImpl.class` | `4cab3f1e5a0cddf0a6746a6e7d8815de00e28895b06de960d9b715f33a7fd325` |
| `PageDetectionTask.class` | `0a2c31576806561b8c73aa00c53d418682cf7942f3eb9a319e7ce5fbab65c607` |
| `EntityFileTemplate.class` | `7fc5c9fa0f19f5308e9319389ab050d8cfd83a2f50fe121ebf3a34f63acd73c2` |

---

# 第 1 问（最高优先）：NFE 在流水线里的位置 —— **在一致性检测之后，检测门已绿**

## 1.1 答案

> **`NumberFormatException` 发生在 `doGenerateCode`（代码生成）阶段，在一致性检测 `doCheck` 之后。**
> **23:43 那次失败时，一致性检测已经返回 true（门是绿的）。**
>
> **推论（强）：NFE 是当前唯一有实证的阻断，且它不是一致性检测的问题。**

## 1.2 证据 A：`doParallel` 内部 get 顺序（STATIC）

`AbstractDeployService.doParallel()`（反编译 268 行起，原始行号 242 在此段内）：

```java
CompletableFuture<Boolean> checkFuture = CompletableFuture.supplyAsync(() -> this.doCheck(context), this.executorService);
CompletableFuture<Boolean> codeFuture  = CompletableFuture.supplyAsync(() -> this.doGenerateCode(context), this.executorService);
try {
    boolean flag = checkFuture.get(10L, TimeUnit.MINUTES);     // ← 先阻塞等 check
    if (!flag) {
        throw new BusinessException("BOOT_1000").addError("一致性检测未通过");   // ★ 原第 242 行
    }
    flag = codeFuture.get(10L, TimeUnit.MINUTES);              // ← check 绿了才等 code
    if (!flag) {
        throw new BusinessException("BOOT_1000").addError("后端代码生成错误");
    }
}
```

**两个 Future 并行启动，但 get 是串行的：先 `checkFuture.get()`，`!flag` 就抛「一致性检测未通过」并结束；
只有 check 为 true 才会走到 `codeFuture.get()`。**

**所以：若 NFE 从 `doGenerateCode` 里抛出，必然是 `checkFuture.get()` 已返回 true 之后。**

## 1.3 证据 B：串行路径顺序相同（STATIC）

`PipeLineManager.startPipeline`（反编译 362-368 行）：

```java
if (context.isParallel()) {
    deployService.doParallel(context);
} else {
    deployService.doCheck(context);          // ← 先
    deployService.doGenerateCode(context);   // ← 后
}
deployService.doDeploy(context);
```

**两条路径（parallel / serial）都是 check 先于 code。顺序结论与配置无关。**

## 1.4 证据 C：报错位置差异（LIVE，决定性）

`udc_deploy_record.msg` 原文（`app_name=datamigration9000000000000000001, state=2`）：

**一致性检测失败（多次）**：
```
发布失败: 业务异常[一致性检测未通过],报错位置:com.seeyon.udc.pipeline.AbstractDeployService.doParallel(AbstractDeployService.java:242)
发布失败: Business Error[一致性检测未通过],报错位置:com.seeyon.udc.pipeline.AbstractDeployService.doParallel(AbstractDeployService.java:242)
```

**NFE 失败（23:43:05 一次）**：
```
发布失败: java.lang.NumberFormatException: For input string: "com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp795",
报错位置:java.lang.NumberFormatException.forInputString(NumberFormatException.java:65)
```

**两处「报错位置」完全不同：**
- 一致性失败 → `doParallel:242`（**我们自己抛的那行**）
- NFE 失败 → `NumberFormatException.forInputString:65`（**JDK 内部**）

**若 NFE 发生在 `doCheck` 内部**，它会被 `checkFuture.get()` 包装成 `ExecutionException`，
再由 `catch (ExecutionException) → ExceptionUtils.rethrow` 重抛，
**报错位置应指向 `doParallel` 的 `catch` 行，而不该穿透到 JDK 的 `forInputString:65`。**

**NFE 报错位置直达 JDK 内部，说明它是 `codeFuture.get()` 抛出的 `ExecutionException` 被 rethrow 后保留的原始栈顶**
——即 **`doGenerateCode` 内部**。

## 1.5 第 1 问结论 + 对 main 因果链的修正

| main 的原假设 | 修正后 |
|---|---|
| 「NFE 与一致性检测可能同源」 | ❌ 不同阶段。NFE 在检测**之后** |
| 「0 ERROR 快照可能不代表门绿（若 NFE 在检测前）」 | ✅ **这个担心不成立**。NFE 在检测后，检测确实跑完了且返回 true |
| 「当前唯一有实证的阻断 = NFE」 | ✅ **成立，且现在有代码级+记录级双重支撑** |

**⚠ 一个必须说清的例外**：以上成立的前提是 **23:43 那次 check 返回 true**。
如果 check 返回 **false**，`doParallel` 会在第 242 行抛「一致性检测未通过」，**根本走不到 `doGenerateCode`**，
也就不会有 NFE。**NFE 的存在本身就是「check 通过」的证明。**

---

# 第 2 问：`doParallel:242` 的判定条件是不是 `errorCount > 0`？

## 2.1 答案：**不是在第 242 行判，第 242 行只判 `boolean flag`**

**准确回答分两层：**

| 层 | 位置 | 判据 |
|---|---|---|
| `doParallel:242` | `AbstractDeployService` | `if (!flag)`，`flag = checkFuture.get()` 的返回值 |
| **真正的 `errorCount > 0`** | **`DetectionManager.java:384`** | `if (dto.getErrorCount() > 0L) return false;` |

## 2.2 完整链路（每层已反编译确认）

```
doParallel:242                      抛 "一致性检测未通过"（只判 boolean）
 └ doCheck                          NormalDeployService:149 → 仅包装
    └ doDefaultCheck                AbstractDeployService:182
       ├ DeployBeforeService 链     并行 handle()（DeployPageCheckService 等）
       └ detectionExecute.detectionExecute()
          └ DetectionExecuteImpl    只 catch 记日志，不改返回值
             └ detectionManager.execute()
                └ DetectionManager.execute():384  ★ 判据在此
```

`DetectionManager.execute()`（反编译 349 行起）关键段：

```java
if (!this.deployProperties.isOpenCheck()) {
    return true;                                    // ← 开关关闭直接放行
}
...
boolean result = this.doExecute(applicationDto, parentContext);   // 跑 184 个检测项，写 Redis
...
// 加锁失败分支（等别人跑完）：
Set consistenceDetectionDtoSet = RedisDetectionUtils.selectDetectionSetByAppId(appId);
DetectionMessageDto dto = RedisDetectionUtils.getDetectionCount(consistenceDetectionDtoSet);
if (dto.getErrorCount() > 0L) {
    log.info("应用[{}]一致性检测结果阻断条数:{},严重条数:{}", appId, dto.getErrorCount(), dto.getSeriouCount());
    return false;                                   // ★ 唯一的 false 出口（计数路径）
}
return true;
```

## 2.3 「WARN 不阻断」验证结果

| 判据 | 是否阻断 |
|---|---|
| `errorCount > 0` | ✅ **阻断**（唯一） |
| `seriouCount > 0` | ❌ 不阻断（只打日志） |
| `warnCount > 0` | ❌ 不阻断 |

**→ 「WARN 不阻断」成立，有字节码依据。**

**⚠ 一处 UNVERIFIED**：`doExecute()` 内部若有检测项直接 `throw`（而非写入 dto），也会导致失败，
那条路径不经过 `errorCount`。我未逐项确认 184 项中是否全部「只记录不抛出」。
**但 23:43 实际是 NFE 而非检测异常，说明那次没走这条路径。**

## 2.4 一处与 main 快照的交叉验证

main 实测 `DetectionError:Count` 里 6 个域全部 `errorCount=0 / seriouCount=0 / warnCount=1`。
**按 384 行判据 → `return true` → 门绿。** 与第 1 问「检测已通过」**互相印证**。

---

# 第 3 问：一致性检测项清单 —— **修正：权威全集 1074 个（我 02:10 报的 184 是错的）**

## 3.0 ⚠ 先修正我的错误

我 02:10 那条 VERDICT 说「184 个检测项」。**这个数字是错的。**

错因：我从**实现类**（`PageCommonDetection` 等）里 grep `UDC_CE_*` 字面量，
只抓到这些类**自己写死**的码。而权威全集在**枚举 + 常量类**里：

| 来源 | 类 | 数量 |
|---|---|---|
| 枚举 | `com.seeyon.udc.detection.enums.ConsistenceDetectionCodeEnum` | **997** |
| 常量 | `com.seeyon.udc.detection.constant.ConsistenceErrorCode` | **1032** |
| **并集（权威全集）** | | **1074** |
| 其中 `UDC_CE_*` 检测项 | | **631** |

**验证**：实测 WARN 的三个码（`UDC_CE_FUNCTION_NODE_08100` / `UDC_CE_MICRO_FLOW_04003` / `UDC_MICRO_FLOW_04009`）
**全部在 1074 里，但只有 1 个在我的 184 里**。
→ **我的 184 漏了大部分，用它做「某类校验不存在」的推论是不可靠的。§4 已按新全集重做。**

## 3.1 你列的历史 ERROR 码——**全部精确命中**

| 你的码 | 权威全集中的码 | 状态 |
|---|---|---|
| `03103` | **`UDC_CE_PAGE_03103`**（另有 `UDC_CE_PAGE_031034`，不同项） | ✅ 命中 |
| `03108` | **`UDC_CE_PAGE_03108`** | ✅ 命中 |
| `03907` | **`UDC_CE_PAGE_03907`** | ✅ 命中 |
| `04003` | **`UDC_CE_MICRO_FLOW_04003`** | ✅ 命中（且实测在 Redis 里） |
| `04004` | **`UDC_MICRO_FLOW_04004`**（注意无 `CE`） | ✅ 命中 |
| `02104` | **`UDC_CE_ENTITY_02104`** | ✅ 命中 |
| `08100` | **`UDC_CE_FUNCTION_NODE_08100`** | ✅ 命中（实测在 Redis 里） |

**→ 7/7 精确对齐。你的历史码都在权威全集内，码号体系正确。**

## 3.2 `UDC_CE_*` 631 项的族分布

| 族 | 数量 | 族 | 数量 |
|---|---|---|---|
| `PAGE` | 232 | `DTO` | 12 |
| `ENTITY` | 109 | `APP` | 11 |
| `LAYOUT` | 108 | `MICRO` | 7 |
| `DATA*` | 50 | `BASIC` | 4 |
| `DEDUCTION` | 28 | `EVENT` | 3 |
| `FUNCTION` | 16 | `UNIQUE` | **1** |
| | | 其他（URL/SUB/SIZE/等） | 各 1-2 |

`*DATA` 前缀来自 `DATA_GRID` / `DATA_SOURCE` / `DATAFLOW` 等复合前缀，不是单一族。

## 3.3 完整清单路径

```
<HERMES_HOME>\cache\scratch\drift-p3\cfr-codes  com/seeyon/udc/detection/enums/ConsistenceDetectionCodeEnum.java   (997)
  com/seeyon/udc/detection/constant/ConsistenceErrorCode.java        (1032)
  all.txt                                                            (并集 1074)
```

一键复现：
```
java -jar cfr.jar udc-plugin-api-5.3.517/com/seeyon/udc/detection/enums/ConsistenceDetectionCodeEnum.class
java -jar cfr.jar udc-plugin-api-5.3.517/com/seeyon/udc/detection/constant/ConsistenceErrorCode.class
```

# 第 4 问：rg 是否在任何检测项里被唯一性校验？—— **没有（已在权威 1074 全集下复核）**

## 4.1 答案

> **在权威全集 1074 个错误码中，唯一带 `UNIQUE` 的是 `UDC_CE_UNIQUE_ELEMENTS`，
> 且它在全 22 模块内零调用者（死码）。没有任何检测项校验 `relationGroupId` 唯一性。**
> **你的「3 页共用 rg」假设没有代码依据。**

## 4.2 证据 A：权威全集搜索（修正后）

```
grep -iE "GROUP|UNIQUE|DUPLICAT|REPEAT|CONFLICT|SAME"  all.txt(1074)
→ 仅 1 条命中：UDC_CE_UNIQUE_ELEMENTS
```

**穷举搜索 `RELATION_GROUP|RELATIONGROUP|_RG_` → 零命中。**

`UDC_CE_UNIQUE_ELEMENTS` 的调用者：
```
全 22 模块 grep -rl "UNIQUE_ELEMENTS" --include=*.class
→ 只有 udc-plugin-api/.../constant/ConsistenceErrorCode.class（定义处自身）
```
**→ 定义但从未使用 = 死码，不构成本应用的真实检测项。**

## 4.3 证据 B：rg 在检测链只有 3 处引用，全非唯一性校验

| # | 位置 | 代码 | 真实用途 |
|---|---|---|---|
| 1 | `DeployPageCheckService:119-126` | `groupingBy(getRelationGroupId)` 后查手工 portlet | **找出写了手工 portlet 的页面，从检测中剔除**。共用 rg 只让剔除范围变大，不报错 |
| 2 | `PageDetectionService:248` `comparedPcAndMobile` | `map.get(rg)` 找同组 MOBILE 页 | **PC/Mobile 配对**。组内无移动页 → `return`，静默不报错 |
| 3 | `PageCommonDetection:2782` `MENU_PAGE` 分支 | `.filter(rg.equals(navPageId) && MOBILE).findAny()` | **底部导航反查移动页**。共用时 `findAny()` 随机取一个 → **功能歧义，非阻断** |

**关键**：三处读的 `pageInfoItemMap` 均来自 `context.getMetadata("...PageInfoEntity")`
→ **`udc_page_info.relation_group_id` 列**（31 页全唯一），
**不是 `page_schema` JSON 残留值。**

`relationGroupPageInfoMap` 的唯一调用点已全量确认：
```
grep -rn "getRelationGroupPageInfoMap" --include=*.java
→ 仅 PageDetectionService.java:249（comparedPcAndMobile 内）
```

## 4.4 证据 C：后端永不生成共用 rg（STATIC）

```java
// PageInfoService.java:511  createPages（复制与新建共用）
Long relationGroupId = Ids.gidLong();

// PageInfoService.java:832  batchCreate
Long relationGroupId = Ids.gidLong();
```

→ **`udc_page_info.relation_group_id` 设计上永远唯一。**

## 4.5 与实测数据交叉

```
udc_page_info WHERE app_id=8704... GROUP BY relation_group_id HAVING COUNT(*)>1  →  空（31页，0 共用组）
page_schema.page_schema JSON 里 relationGroupId → 3组×3页 + 1组×2页共用（17/17 行都有）
```

→ **残留只在 JSON 内层，平台索引层干净。**

## 4.6 结论

**「3 页共用 rg」= 未证实的相关性，且与检测输出不符，无代码依据。**
main 在 `GATE1C-DETECTION-SNAPSHOT-UPDATE.md` 里的自我削弱判断**成立**。

# 补充：NFE 的代码位置（第 1 问的下游，仍 UNVERIFIED）

**已证实**：NFE 在 `doGenerateCode` 阶段。
**未证实**：具体哪个类抛出。

已排除的候选（经反编译确认有 `NumberUtil.isNumber()` 守卫，不会抛 NFE）：

```java
// EntityFileTemplate.java:752 / 799
if (NumberUtil.isNumber(field.getRelationEntity())) {
    CtpEnumDto dto = this.ctpEnumMetadata.get(Long.parseLong(field.getRelationEntity()));   // 有守卫
}
```

**唯一无守卫的一处**（候选，未证实是本应用触发）：

```java
// EntityFileTemplate.java:426-430
if (DataType.ENUM.name().equals(field.getDataType())) {
    if (StringUtils.isNotBlank(field.getRelationApp()) && !NumberUtil.isNumber(field.getRelationApp())) {
        return field.getRelationEntity();                     // ← relationApp 非数字则直接返回
    }
    UdcEnumDto udcEnumDto = this.udcEnumMetadata.get(Long.parseLong(field.getRelationEntity()));  // ★ 无守卫
}
```

**但**：本应用 7 个 ENUM 类字段的 `relation_entity` 实测**全部是数字**（`expEnum=4456389269786582653` 等），
且 NFE 的字符串是**实体全名** `com.seeyon.datamigration...domain.entity.XzhExp795`，
**不是字段的 relation_entity**。

→ **NFE 的输入是「实体全名」，不是「字段的 relationEntity」。所以我找的这条不是它。**
→ **NFE 具体抛出点 = UNVERIFIED。** 需要完整堆栈（`udc_deploy_record.msg` 只有栈顶）。

**建议**：取 23:43 那次的完整 build 日志（`compile-info/.../backBuild.log` 或服务端 app.log），
里面有完整堆栈，能直接看到调用方。

---

# 边界

| 项 | 边界 |
|---|---|
| STATIC | CFR 0.152 反编译 `udc-cicd-5.3.517` / `udc-biz-5.3.517` / `udc-plugin-api-5.3.517` |
| LIVE | DB 仅 SELECT（`udc_deploy_record` / `udc_page_info` / `udc_page_schema` / `udc_attribute` / `udc_entity`）；Redis 仅 SCAN/HGETALL/SCARD/TTL |
| 未做 | **零写、零浏览器、零凭据、零网络**；未触发发布、未上架、未改配置 |
| 产物 | `<HERMES_HOME>\cache\scratch\drift-p3\cfr-line242\`、`cfr-gate1c\`、`cfr-nfe\` |

---

# 四问汇总卡

| # | 问题 | 答案 | 等级 |
|---|---|---|---|
| 1 | NFE 在检测前还是后？ | **之后**。NFE 存在本身就证明 check 已返回 true | ✅ STATIC+LIVE |
| 2 | 242 判定是不是 `errorCount>0`？ | **242 只判 boolean**；`errorCount>0` 在 `DetectionManager:384` | ✅ STATIC |
| 3 | 检测项清单？ | **权威全集 1074 个**（`UDC_CE_*` 631 个）。**我先前报的 184 是错的，已修正** | ✅ STATIC（历史码 7/7 精确命中） |
| 4 | rg 有唯一性校验吗？ | **没有**。1074 全集下唯一 `UNIQUE` 项是死码；3 处引用全非唯一性 | ✅ STATIC+LIVE |

**唯一 UNVERIFIED：NFE 的具体抛出类**（需完整堆栈）。
