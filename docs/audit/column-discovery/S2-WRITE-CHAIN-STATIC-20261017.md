# S2 写链静态取证｜建/删真实语义与回读预期校准

> 角色：implementer ｜ 切片：S2（WAF 403 待命期间的**零网络探测**离线补证）
> 时间：2026-10-17 18:0x +08 ｜ 环境：test2（`udc_test2`）
> 证据等级：**VERIFIED_STATIC_BYTECODE（CFR 0.152 反编译 udc 5.3.517）+ LIVE（只读 SQL）**
> 性质：**不改 ROUTE、不改验收标准、不写业务数据**。本文只把 S2 恢复后会踩的坑提前钉死。
> 触发原因：ROUTE §S2 回读预期写的是「157 → 159 / `udc_portlet_group` 期望仍 0 行」，本轮核验发现该预期
> 有 3 处与实际代码语义不符，若不校准，恢复后**必被误判为取证失败**。
> **裁定结果（2026-10-17 18:04）**：main 已裁定 **H 采纳 + I 采纳**（`column-s2-writechain-static-ruling-hi-v1`），
> 本文件 §5/§6 已按裁定同步为**生效口径**；ROUTE 恢复判定标准第 6/7 条同步登记。

---

## 零、一句话结论

S2 的建删链路本身**不会留孤儿行**（删除有级联，见 §3），但 ROUTE 的**回读计数预期需要改**：
`udc_page_info` 全库总数今天已被其它域改动（1568 → 1574），**全库绝对计数不能作为判定依据**，
必须改用「本应用 + 本次新建 id 白名单」的增量判定（**main 已裁定 I 采纳，生效**）。另有两处新增必抓项（§4、§5）。
**本文件已同步裁定 H（H1-H5）与裁定 I（I1-I6），§5/§6 为生效口径。**

---

## 一、端点与控制器（STATIC，权威）

反编译：`udc-web-5.3.517.jar` → `com.seeyon.udc.controller.PortletController`
源码：`<HERMES_HOME>/cache/scratch/cfr-web/com/seeyon/udc/controller/PortletController.java`

| 方法级 path | HTTP | 入参 | 语义（`@RestApiOperation` 常量池原文） |
|---|---|---|---|
| `/create` | POST | `PortletDto` | **创建栏目分组** |
| `/create-portlet` | POST | `PageDefinitionDto` | **创建栏目** |
| `/update` | POST | `PortletDto` | 修改栏目分组 |
| `/update-portlet` | POST | `PageDefinitionDto` | 修改栏目 |
| `/select-by-appId/{appId}` | GET | Long | 查询应用下栏目分组以及栏目 |
| `/delete/{id}` | POST | Long | 删除指定栏目分组/栏目 |
| `sort` | POST | `List<PortletDto>` | 栏目拖拽排序 |

类级：`@RequestMapping("udc/portlet")`、`@RestApi(value="栏目接口", group="页面")`、
`@HasRole({"OrgAdmin","udcAppDesigner","udcSystemAdmin"})`。

→ **这是 S2 的两条创建链闭合点**：分组走 `/create`，栏目走 `/create-portlet`。
`/delete/{id}` 是**同一个**端点，靠 id 指向的行自带 type 区分，无独立 delete-portlet。

---

## 二、`/create`（建分组）实际做了什么 —— 含一个 ROUTE 未登记的跨服务调用

反编译：`udc-biz-5.3.517.jar` → `com.seeyon.udc.page.domain.service.PortletService#create`
源码：`<HERMES_HOME>/cache/docs/audit/artifacts/decompiled/cfr-r31b/com/seeyon/udc/page/domain/service/PortletService.java` L120-131

```java
public PortletDto create(PortletDto portletDto) {
    PortletEntity pageEntity = new PortletEntity();
    pageEntity.from(portletDto);
    this.checkDuplicateName(pageEntity);                                   // L123 重名校验
    pageEntity.setOrderNo(this.getMaxOrder(portletDto.getAppId()) + 1);    // L124 服务端算 orderNo
    this.portletDao.create(pageEntity);                                    // L125 落 udc_portlet
    ... operationLog ...                                                   // L126-127
    portletDto.setId(pageEntity.getId());
    this.syncPortletCategory(pageEntity, true);                            // L129 ★门户侧同步
    return portletDto;
}
```

### 2.1 `orderNo` 不是前端给的

`getMaxOrder(appId)` = 该应用 `udc_portlet` 里 `orderNo` 最大值 + 1（L458-466）。
→ **回读断言不要写死 `order_no` 期望值**，只能断言「等于建前该应用 max+1」。

### 2.2 `syncPortletCategory` 会向门户（Dubbo）写分类 —— GROUP 专属

`PortletService.java` L419-441：

```java
private void syncPortletCategory(PortletEntity portlet, boolean isCreate) {
    if (portlet.getType() != PortletTypeEnum.GROUP) return;     // 仅 type=0 才会走
    ...
    ctyDto.setCategoryCode(String.valueOf(portlet.getId()));
    ctyDto.setParentCategoryCode("-1");
    ctyDto.setSortNo(portlet.getOrderNo());
    response = isCreate ? ...createCategory(...) : ...updateCategory(...);
    if (Objects.isNull(result)) throw new BusinessException("栏目分类发送至门户，失败！");
}
```

链路：`PortletService#syncPortletCategory`
→ `PageInfoService#getUdcPortalPortletAppService()`（L364-366）
→ `UdcPortalPortletAppServiceImpl#createCategory`（`udc-portal-5.3.517.jar`，`@DubboReference` 至 `PortalPortletAppService`）
→ 门户侧 `createCategory`。

**这条在 ROUTE 里完全没有登记。** 其证据价值与风险：

1. **证据价值（正面）**：建分组会在门户侧留下分类实体，S2 可以顺手抓这条
   「设计态 → 门户态」的同步链，这是 P0 域定位里「栏目在门户侧是什么」的第一个 LIVE 支点。
   此前 `PC_PORTAL` 族被登记为未触达（S1 边界），这条同步调用正好是入口。
2. **风险（必须登记）**：若门户侧 create 成功而后续步骤失败，会留下**门户侧脏分类**，
   而本域 DB 里看不到它。判定方式：删除后必须复查门户侧分类是否同步消失（见 §3.3）。

### 2.3 `/create` 对 type=0 不写 `page_info`

`create()` 只写 `udc_portlet` 一行 + op-log + 门户分类，**不碰 `udc_page_info`**。
→ 建分组后 `udc_page_info` 计数**不应变化**。若变了，说明命中的不是 `/create`。

---

## 三、`/create-portlet`（建栏目）与 `/delete/{id}`（删除）的级联语义

### 3.1 建栏目 = 先 page_info 后 portlet

`PortletService#createPortlet(PageDefinitionDto)` L133-149：

```java
if (PageTypeEnum.PORTLET.name().equals(dto.getPageType())) {
    this.pageInfoService.baseCreate(dto);          // L135 先写 udc_page_info
    PortletDto portlet = new PortletDto();
    portlet.setName(dto.getCaption());
    portlet.setGroupId(dto.getGroupId());
    portlet.setAppId(dto.getAppId());
    portlet.setTerminalType(this.getTerminalTypeEnum(dto));   // L140
    portlet.setType(PortletTypeEnum.PORTLET);
    portlet.setPageRelationId(dto.getRelationGroupId());      // L143 关联键
    portlet.setCategory(dto.getCategory());
    return this.create(portlet);                   // L145 再写 udc_portlet
}
```

`terminalType` 由 **pageItems 条数**推导（L469-479），不是前端指定：

```java
if (pageItems.size() > 1) tmt = TerminalTypeEnum.ALL;         // 0
if (pageItems.size() == 1) tmt = urlType == PC ? PC : MOBILE; // 1 / 2
```

→ **回读断言只能写成「与本次提交的 pageItems 条数/urlType 一致」**，不能写死。
（与既有 DB 分布自洽：type=0 的 6 行中 5 行是 `1,2` 双页、1 行单页 url_type=2 —— 见 §6 校准表。）

`baseCreate` → `createPages`：`relationGroupId = Ids.gidLong()`（新建 64 位 id），
每条 pageItem 派生一行 `udc_page_info`（L511-532）。`sortNo = getMaxOrder(appId)+1`（L522）。

### 3.2 删除有级联，不会留孤儿（这是好消息，也是 S2 可行性的关键）

`PortletService#deleteById(Long)` L293-332：

```java
delIds.add(id);
if (entity.getType() == GROUP) {
    List portletList = portletDao.selectListByCondition(GROUP_ID, id, null);   // L303 找出子栏目
    if (isNotEmpty) {
        delIds.addAll(子栏目 ids);                       // L308 连子栏目一起删
        relationIds.addAll(子栏目 page_relation_id);      // L309-310
    }
} else if (entity.getType() == PORTLET) {
    relationIds.add(entity.getPageRelationId());          // L313
}
...
count = portletDao.deleteByIds(delIds);                    // L320
if (isNotEmpty(relationIds)) {
    conds.put("appId", entity.getAppId());
    conds.put("IN_relationGroupId", relationIds);
    pageInfoService.deleteByConditions(conds, false);      // L326 删 page_info + 下游
}
if (entity.getType() == GROUP) {
    pageInfoService.syncDelete(Arrays.asList(id));          // L329 门户侧删分类
}
```

`PageInfoService#deleteByConditions`（L969-997）会顺手做完：
`deleteDetection4Dto`（L984）→ `deleteSchemaByPageIds`（L993）→ 删 page_info（L994）
→ `syncDeleteToPortal`（L995，删门户侧 portlet 实体）。

**结论（LIVE 侧证，见 §4）**：

- 删 **栏目**（type=1）→ 删 `udc_portlet` 1 行 + 其 `page_info`（**可能多行**，136/131 说明一个 portlet 最多挂 2 行）+ 其 schema + 门户侧 portlet 实体。
- 删 **分组**（type=0）→ **连该分组下所有子栏目一起删**（L303-310），再删门户侧分类（L329）。
- `syncDelete`（PageInfoService L368-375）内部是 `deleteCategoryByIds`，**有错误抛出**，不是静默。

→ 所以裁定 F 的「先删栏目后删分组」不是仅为避孤儿，而是：**若先删分组，子栏目会被连带删除，
S2 就拿不到「删栏目」这一独立动作的证据了**。这是顺序的真正理由，建议登记。

### 3.3 事务边界（决定失败时的残留形态）

`PortletAppService`（`udc-biz`）：`create` / `createPortlet` / `deleteById` 均为 `@Transactional`（L47/55/69/76/82 区段）。
`UdcPortalPortletAppServiceImpl` 各方法亦 `@Transactional`，但走 `@DubboReference` **跨进程**。

→ **本地 DB 有事务，跨门户 Dubbo 调用不在同一本地事务内**（跨服务）。
失败残留形态：本域 DB 回滚，但门户侧分类/portlet 实体可能已建成 → **门户侧脏数据**。
S2 取证必须包含一条「门户侧残留复查」，证据等级记 LIVE 或 UNVERIFIED，不得默认干净。

---

## 四、现有 LIVE 先例：zzprobe 应用已做过一次完整建删

这是本轮**唯一可直接引用的建删闭环先例**，不来自我的推断：

`udc_operation_log`（module=4 PORTLET）实测：

| create_time | app_id | module | sub_module | action_type | domain_caption |
|---|---|---|---|---|---|
| 2026-09-30 22:42:23 | 6419954374508955097 | 4 | 40 (PORTLET_PAGE) | 1 (CREATE) | zzprobe栏目 |
| 2026-10-01 00:42:04 | 6419954374508955097 | 4 | 40 (PORTLET_PAGE) | 2 (DELETE) | zzprobe栏目 |

当前该应用实测：`udc_portlet` **0 行**、`udc_page_info`（含 PORTLET）**0 行**。

→ 建 → 删 → **归零，无残留**（LIVE 佐证 §3.2 的级联结论）。
→ 但注意：该记录 `sub_module=40 (PORTLET_PAGE)`，而 `createPortlet` 的 op-log 走的是
`PortletService#create` 内 `SubModuleEnum.PORTLET(5)`，`baseCreate` 走 `PORTLET_PAGE(40)`。
**一次建栏目会产生两条 op-log（40 CREATE + 5 CREATE）**，S2 抓 op-log 时不要当成两次操作。

其余 6 条 `sub_module=6 (PORTLET_GROUP) action_type=2` 是 2026-10-12 17:25-17:26 对
本应用 6 个分组（平台门户/本部总门户/客开自定义栏目-勿删/事总门户/分总门户/销售员门户）的删除记录。

枚举权威码（`udc-plugin-api-5.3.517.jar`）：
`ModuleEnum.PORTLET=4`；`SubModuleEnum.PORTLET=5 / PORTLET_GROUP=6 / PORTLET_PAGE=40`；
`LogOperationType.CREATE=1 / DELETE=2 / UPDATE=3 / RECOVER=7`。

---

## 五、回读预期校准（**main 已裁定 I 采纳，白名单增量口径生效**）

> 2026-10-17 18:04 DECISION `column-s2-writechain-static-ruling-hi-v1`：
> 裁定 H（H1-H5 并入 ROUTE 恢复判定标准第 6 条）与裁定 I（回读口径白名单化）**全部采纳**。
> 本节由「建议」升级为「生效口径」；§6 已按裁定 H 重写。

### 5.1 全库绝对计数已失效（LIVE 实测漂移）

| 项 | S1 基线（15:15） | 本轮实测（18:00） | 差 |
|---|---|---|---|
| `udc_portlet` 全库 | 157 | **157** | 0 |
| ├ type=0 | 26 | **26** | 0 |
| └ type=1 | 131 | **131** | 0 |
| `udc_page_info` 全库 | 1568 | **1574** | **+6** |
| `udc_page_schema` 全库 | 1555 | **1561** | **+6** |
| `udc_page_info` 本应用 | — | 31 | （含 15:18/15:41 新增 6 行） |
| `udc_portlet` 本应用 | 0 | **0** | 0 |
| `udc_portlet_group` 全库 | 0 | **0** | 0 |

`udc_page_info` 的 +6 来源明确（LIVE，按 create_time 倒序）：

```
15:18:49 / 15:18:50 / 15:41:03  app_id=8704025620829192834
  caption: 迁移方案配置列表_副本 / 迁移方案配置详情_副本 / 数据源配置信息列表弹窗选择页面_副本
  page_type: SEARCH_LIST / DETAIL
```

→ **这 6 行是另一个域（页面/实体域）在本会话期间通过 UI 建「副本页」产生的**，
与本域无关，但会让任何「全库 1568→1570」式断言当场失败。

**生效判定口径（裁定 I，白名单增量版）**：

- **禁用**：全库 `udc_page_info` / `udc_page_schema` 绝对计数断言（I1）。
- **改用**：**本应用 + 本次新建 id 白名单**（I2）。S2 抓到的创建响应里有 `id` / `relationGroupId`，
  回读时按这些 id 精确 SELECT；断言「命中 1 行」「字段与响应一致」「删除后该 id 0 行」。
- `udc_portlet` 全库计数（157 / 26+131）今日未漂移，**可继续断言**，但以本应用计数为准者优先（I3）。
- `udc_page_info` 的 PORTLET 增量 +1/+2 分叉，恢复后**先记录表单端类型默认勾选再定期望**，不写死（I5）。

### 5.1b 白名单回读的精确 SQL 模板（恢复后直接套用，替换 `<...>`）

基线已在本轮复核（2026-10-17 18:06，LIVE，只读）：

| 基线项 | 值 |
|---|---|
| `udc_portlet` 本应用 `8704025620829192834` | **0 行**（`t0`/`t1` 均 NULL） |
| `udc_portlet` 本应用 `MAX(order_no)` | **0**（空表，`COALESCE` 后） |
| `udc_portlet` 全库 / type=0 / type=1 | **157 / 26 / 131** |
| `udc_portlet_group` 全库 | **0** |

```sql
-- W1 分组白名单（<group_id> = 建分组响应 id）
SELECT id,name,type,group_id,terminal_type,template_type,page_relation_id,publish_state,order_no,create_time
FROM udc_portlet WHERE app_id=8704025620829192834 AND id=<group_id>;
--   断言：命中 1 行；type=0；order_no = 建前该应用 max+1（H5，实测基线 max=0 → 期望 1）
--   group_id / page_relation_id / terminal_type 按响应原值断言；template_type 必为 NULL（平台不写）

-- W2 栏目白名单（<portlet_id> = 建栏目响应 id）
SELECT id,name,type,group_id,terminal_type,template_type,page_relation_id,publish_state,order_no,create_time
FROM udc_portlet WHERE app_id=8704025620829192834 AND id=<portlet_id>;
--   断言：命中 1 行；type=1；group_id = <group_id>（S1 强制更正交叉验证）
--   order_no = 建前（含刚建分组）该应用 max+1（基线 max=1 → 期望 2）

-- W3 page_info 白名单（<relation_group_id> = 建栏目响应的 relationGroupId）
SELECT id,caption,page_type,relation_group_id,group_id,url_type,layout_id,schema_state,hand_written
FROM udc_page_info WHERE app_id=8704025620829192834 AND relation_group_id=<relation_group_id>;
--   断言：命中行数 = 表单端勾选数（+1 或 +2，I5 现场定）；page_type 全 'PORTLET'
--   url_type 组合与勾选端一致；group_id = <group_id>（交叉一致性断言，136/136 全库校验支持）
--   layout_id 全 0、hand_written 非 1、default_open_type NULL —— 不设强期望（§5.4）

-- W4 schema 白名单（page_id 取 W3 的 id 集合）
SELECT COUNT(*) FROM udc_page_schema WHERE page_id IN (<W3_ids>);
--   断言：命中行数 = pageItems 条数（不用全库计数）

-- W5 删除后归零（白名单三张表逐条断言 0 行）
SELECT COUNT(*) FROM udc_portlet WHERE app_id=8704025620829192834;   -- 期望 0
SELECT COUNT(*) FROM udc_page_info WHERE app_id=8704025620829192834 AND relation_group_id IN (<rg_ids>);  -- 期望 0
SELECT COUNT(*) FROM udc_portlet_group;                              -- 期望仍 0（I4）
```

### 5.2 `udc_portlet_group` 期望 0 行 —— 依据已按裁定 I4 更正

静态证据 §2.2 已证：`syncPortletCategory` 走的是**门户 Dubbo 分类**，
**不写 `udc_portlet_group`**（该表由 `PortletGroupController` / `PortletGroupDto` 独立使用）。
→ 「建分组后 `udc_portlet_group` 仍 0 行」这个预期**成立**，
依据是「**建分组不碰该表（走门户 Dubbo 分类）**」，**不是**「该表无人用」（I4）。

裁定 I4 原文依据即此。若建分组后该表增长 → 说明命中的是「栏目分类」链（`portlet-group/create`），
那是另一个结论，须单独判定，**不得与「栏目分组」混为一谈**（同时也触发了 ROUTE 恢复判定标准第 4 条的现场改判条件）。

### 5.3 建 1 分组 + 1 栏目后的**预期增量（精确版，裁定 I 后口径）**

| 表 | 增量 | 依据 | 断言方式（裁定 I） |
|---|---|---|---|
| `udc_portlet` type=0 | **+1** | `/create` L125 | id 白名单 W1 + 本应用计数 |
| `udc_portlet` type=1 | **+1** | `createPortlet` L145 → `create` L125 | id 白名单 W2 + 本应用计数 |
| `udc_page_info` page_type='PORTLET' | **+1 或 +2** | `createPages` 按 pageItems 条数派生（§3.1） | **仅 id 白名单 W3**，禁全库计数 |
| `udc_page_schema` | **+pageItems 条数** | `deleteSchemaByPageIds` 反向印证有 schema 写入 | **仅 page_id 白名单 W4**，禁全库计数 |
| `udc_portlet_group` | **0** | §5.2（建分组不碰该表） | 全库 0 仍可断言（I4） |
| `udc_operation_log` module=4 | **+3（分组 1 条 + 栏目 2 条）** | §4（H4） | 按 app_id + 时间窗白名单 |

**`order_no` 不写死**（H5）：只断言「等于建前该应用 `max+1`」。本轮实测基线：
本应用 `udc_portlet` 0 行、`MAX(order_no)=0` → 分组期望 **1**；建完分组后 max=1 → 栏目期望 **2**。
若现场 `max` 与基线不同（例如恢复前有人动过），**以现场建前实测 max 为准**，不得用本文数字强判。

**「+1 或 +2」是 S2 恢复后必须现场判定的分叉点**（I5）：
若提交表单只勾 1 个端 → 1 行（`terminal_type` = 1 或 2）；若勾 2 个端 → 2 行（`terminal_type`=0）。
静态机制（PortletService L469-479）：`terminalType` 由 `pageItems.size()` 推导 —— >1 → ALL(0)，==1 → PC(1)/MOBILE(2)，非前端指定。
现状 DB 里 6 个 type=0 分组中 5 个是双端（11 行 page_info / 6 portlet），说明**表单默认可双端**。
→ 恢复后**先记录表单端类型选项的实际默认勾选**，再决定回读期望是 +1 还是 +2，**不写死**。

### 5.4 `page_info.group_id` 的语义（S1 未覆盖，本轮补）

LIVE 全库校验（136 行 PORTLET 页）：

| 断言 | 结果 |
|---|---|
| `page_info.group_id` 能解析到 `udc_portlet` 行 | **136 / 136** |
| 其中指向 `type=0`（分组） | **136 / 136** |
| `page_info.group_id = portlet.group_id` 一致 | **136 / 136** |

→ `udc_page_info.group_id` 与 `udc_portlet.group_id` **同源同值**，都指向 type=0 分组行。
S2 回读时可作交叉一致性断言：`page_info.group_id == 新建分组 id`。

另：`udc_page_info` 的 PORTLET 页 `layout_id` **全为 0**（136/136），
`hand_written=1` 仅 4 行，`schema_state` 以 2 为主（1 有 3 行），`default_open_type` 全 NULL。
→ 回读不要对这几个字段设强期望。

---

## 六、S2 恢复后**必抓项清单（裁定 H 生效版）**

> 2026-10-17 18:04 DECISION：H1-H5 **全部采纳**，并入 ROUTE 恢复判定标准第 6 条。
> 本节按裁定重写，编号与 ROUTE 对齐；原「新增 3 条」表述废止。

原有必抓项（ROUTE 恢复判定标准 §4）不变：`portlet/create` vs `portlet-group/create` 命中判定、
`udc_portlet_group` 增长单独判定、命名避 `-`、枚举取值。

### H1 门户侧同步链取证（本域 P0，第一个「门户侧是什么」的 LIVE 支点）

建分组请求返回后，必抓**门户侧分类是否真的生成**。链路（STATIC 已证）：

```
POST /service/udc/portlet/create (PortletDto, type=GROUP)
  → PortletController#create
  → PortletService#create L125 落 udc_portlet
  → L129 syncPortletCategory(entity, true)        [仅 type=GROUP]
  → L419-441 组 UdcPortalPortletCategoryDto{
        categoryCode = portlet.getId()            ← 门户侧 code = 本地 udc_portlet.id
        categoryName = portlet.getName()
        parentCategoryCode = PARENT_CATEGORY_CODE ("-1")
        sortNo = portlet.getOrderNo()
        appCode / originalAppId = 应用 name / id }
  → PageInfoService#getUdcPortalPortletAppService()
  → UdcPortalPortletAppServiceImpl#createCategory (@DubboReference PortalPortletAppService)
  → 门户侧 createCategory
```

**取证要求**：拿到「门户侧分类已生成」的可核对证据。可接受路径（按可得性优先）：
- 门户侧分类表/缓存回读（categoryCode 应等于本地新建分组 id）
- 门户侧设计器 UI 回读（分类树出现该 name）
- 本地 op-log / 应用日志中出现 createCategory 成功痕迹（**弱证据，单独立记，不单独判 PASS**）

抓不到 → 记 **UNVERIFIED**，**不得**默认成功，也不得因本地 `udc_portlet` 有行就判门户侧同步成功。

### H2 门户侧残留复查（删除后必做）

Dubbo 调用**不在本地事务内**（`PortletAppService` 的 `@Transactional` 管不到 Dubbo 对端）。
删除链的门户侧出口（STATIC 已证）：

```
deleteById(GROUP) L328-330 → PageInfoService#syncDelete(ids)
  → UdcPortalPortletAppServiceImpl#deleteCategoryByIds
  → portalPortletAppService.deleteCategoryByCodes
```

**取证要求**：删除完成后复查门户侧分类（及 portlet 实体）同步消失。
取不到 → 记 **UNVERIFIED**，**不得默认干净**。本地 DB 归零**不能**代替门户侧复查。

### H3 删除顺序理由（更正，原文已废止）

「先删栏目后删分组」的依据 = **`deleteById(GROUP)` 会连带删除子栏目（L300-311）**，
先删分组将使 S2 失去「删栏目」这一独立证据。
~~原「避免孤儿行」表述废止~~（级联删除已证不留孤儿，见 §3.2）。

### H4 op-log 判读

一次建栏目产生**两条** op-log：`PORTLET_PAGE(40) baseCreate` + `PORTLET(5) create`。
S2 不得误判为两次操作。分组创建为 `PORTLET_GROUP(6) DELETE/CREATE` 单条（deleteById L302）。

### H5 `order_no` 不写死期望

只断言「等于建前该应用 `max+1`」（服务端 L124 `getMaxOrder+1` 计算，非前端给值）。

### 另两条（原「新增 3 条」中的 2、3 项，保留）

2. **双端还是单端**（§5.3 / I5）：提交前记录表单端类型默认勾选，据此决定 `udc_page_info` 期望 +1 还是 +2。
3. **门户侧残留复查** = H2（已上移，此处不重复）。

### 本轮复核补充（STATIC，2026-10-17 18:0x，供 H1/H2 判读用）

复核 cfr 产物（同一批 5.3.517 字节码），确认两条 ROUTE 尚未写明的细节：

- **门户侧 `categoryCode` 就是本地 `udc_portlet.id`**（L424 `String.valueOf(portlet.getId())`），
  `parentCategoryCode` 恒为常量 `-1`（L114 `PARENT_CATEGORY_CODE`，L426 使用），`sortNo` 取本地 `orderNo`（L432）。
  → H1 的门户侧核对有了**精确比对键**：拿到门户侧分类后，`code == 新建分组 id` 即可交叉证实，
  不必依赖 name 模糊匹配。
- **建栏目（type=1）不会触发分类同步**（L420 早退 `type != GROUP` return），
  但会经另一路径同步门户 portlet 定义：`PageInfoService#syncPortal` L1990-2033
  （保存页面时 `syncPortalToPortal` → L2000 `categoryCode = pageItem.getGroupId()`）。
  → 即：**栏目 → 门户的出口是「保存页面」而非「建栏目」**。
  S2 若只建栏目不保存页面，门户侧 portlet 定义可能不存在；这是 **H1/H2 之外的新增观察点**，
  取证时不得把「门户侧无该 portlet」误判为删除残留。

---

## 附：级联删除 LIVE 佐证（裁定 I 补充登记，恢复后随 S2 产物一并核实引用）

`zzprobe` 应用 `6419954374508955097`：建（2026-09-30 22:42）→ 删（2026-10-01 00:42）
→ 当前该应用 `udc_portlet` 0 行 / `udc_page_info` 0 行（归零，无残留）。
`udc_operation_log` 有对应 CREATE/DELETE 记录（`sub_module=40 PORTLET_PAGE`）。
→ 作为「级联删除 + 无残留」的 LIVE 先例，支撑 §3.2 结论。

---

## 七、边界遵守自述

- 写操作：**0**（无 create/update/delete/sort；SQL 全部 SELECT / SHOW）
- 网络探测：**0**（本轮为纯离线静态取证 + DB 只读）
- 未改 `main/ROUTE.md`、未改验收标准、未扩范围、未跨域
- 未打印 secret；凭据仅路径引用
- 反编译产物落 scratch（`cfr-portlet` / `cfr-pageinfo` / `cfr-portal` / `cfr-web` / `cfr-enums`），不进仓库
- 本文与原始数据落 `docs/audit/column-discovery/`，本地 commit，不 push

## 八、复现命令

```bash
CDP=  # 本切片不使用 CDP
J=/d/software/hermes/cache/scratch/djars
CFR=<HERMES_HOME>/skills/seeyon/03-v8-extension/seeyon-v8-spi/references/contract-index/tools/cfr.jar

# 控制器（端点 + 语义原文）
java -jar $CFR --jarfilter "com.seeyon.udc.controller.PortletController" \
  --outputdir <HERMES_HOME>/cache/scratch/cfr-web $J/udc-web-5.3.517.jar

# 服务层（create / createPortlet / deleteById / syncPortletCategory）
java -jar $CFR --jarfilter "com.seeyon.udc.page.domain.service.PortletService" \
  --outputdir <HERMES_HOME>/cache/scratch/cfr-portlet $J/udc-biz-5.3.517.jar

# page_info 级联删除
java -jar $CFR --jarfilter "com.seeyon.udc.page.domain.service.PageInfoService" \
  --outputdir <HERMES_HOME>/cache/scratch/cfr-pageinfo $J/udc-biz-5.3.517.jar

# 门户侧 Dubbo 桥
java -jar $CFR --jarfilter "com.seeyon.udc.portal.appservice.UdcPortalPortletAppServiceImpl" \
  --outputdir <HERMES_HOME>/cache/scratch/cfr-portal $J/udc-portal-5.3.517.jar

# 枚举
java -jar $CFR --jarfilter "com.seeyon.udc.operationlog.enums.*" \
  --outputdir <HERMES_HOME>/cache/scratch/cfr-enums $J/udc-plugin-api-5.3.517.jar

# DB 只读
cd /d/software/hermes/skills/seeyon/01-platform/seeyon-low-code-environment/scripts
python conn.py db "SELECT type,COUNT(*) c FROM udc_portlet GROUP BY type" --db=udc_test2 --env=test2
python conn.py db "SELECT COUNT(*) c FROM udc_page_info WHERE page_type='PORTLET'" --db=udc_test2 --env=test2
python conn.py db "SELECT module,sub_module,action_type,COUNT(*) c FROM udc_operation_log WHERE module=4 GROUP BY module,sub_module,action_type" --db=udc_test2 --env=test2
```
