# 05 · 在自定义微流程里调用平台能力：可复制的调用片段

## Capability

**回答「我在自定义微流程里，要查组织 / 发流程 / 写枚举 / 读文件，代码到底怎么写」。**

给 Agent 用：接到跨域需求时，**先来本格拿可复制的片段**，不要凭经验拼方法名。
每个片段都标了权威事实格 —— 细节去那里查，本格只保证「调用形态对」。

**本格与 01/02/04 的分工：**
- 01 = 自定义微流程**怎么实现**（改哪个类）
- 02 = **怎么注入** UDC 生成物（包路径 / Request 包装）
- 04 = UDC 生成物**有哪些方法**（CRUD 速查）
- **05 = 怎么调标品 / 平台组件**（本格）

## Version

| 域 | 权威事实格 |
|---|---|
| 组织 / 人员 | `standard-product/organization-ctpuser-method-index.md` |
| 流程 / 事项 | `bpm/appservice-method-index.md` |
| 微流程引擎 | `standard-product/udc-biz-microflow-method-index.md` |
| 工具类 | `standard-product/boot-core-utils-and-annotations.md` |
| 扩展点 | `standard-product/extension-point-decision-table.md` |

---

## 一、先判断：这个能力是哪种形态（决定注解）

```
① 标品业务服务（org / bpm / affair / message / connector）
     → @DubboReference   ← 跨进程，必须包 SingleRequest

② 平台组件 Service（file / enum / cache / excel / i18n / metadata）
     → @Autowired        ← 同 JVM

③ 工具类（JsonUtils / HttpClientUtil / AES / Ids / BeanCopier）
     → 静态调用          ← 无状态
```

**★★★★★ 判据：类名以 `AppService` 结尾 → ①；以 `Service` 结尾且不在你应用包下 → ②；
在 `com.seeyon.boot.util` 下 → ③。**

---

## 二、组织 / 人员（@DubboReference）

```java
import com.seeyon.organization.api.common.OrgCommonAppService;
import com.seeyon.ctp.user.api.core.CtpUserCoreAppService;
import com.seeyon.boot.transport.*;

@DubboReference private OrgCommonAppService orgCommonAppService;
@DubboReference private CtpUserCoreAppService ctpUserCoreAppService;
```

### 2.1 ★★★★★ 先看返回类型：大多数查人方法返回 `Long` / `Map`，不是 DTO

**这是最容易踩的坑 —— 我最初按「强类型 DTO」写，核对字节码后全部推翻。**

| 方法 | 真实返回 |
|---|---|
| `selectMemberInfoById(SingleRequest<Long>)` | `SingleResponse<Map<String,Object>>` |
| `selectMemberExtendInfoById` | `SingleResponse<Map<String,Object>>` |
| `selectMemberMultiDimOrgInfo` | `SingleResponse<Map<String,Object>>` |
| `selectMemberDepartmentInfoById` | `SingleResponse<Map<Long, Map<String, List>>>` |
| **`selectMemberByOrgId(SingleRequest<Map<String,?>>)`** | **`ListResponse<Long>`** ← 只给 id |
| **`selectPageMemberByOrgId(PageRequest)`** | **`PageResponse<Long>`** ← 只给 id |
| `selectMemberByPostId` / `ByJobId` / `ByLevelId` | `ListResponse<Long>` |
| **`selectMemberBySelectPeopleData`** | `ListResponse<OrgMemberCoreDto>` ← ★ 真正的 DTO |
| `selectPageMemberBySelectPeopleData` | `PageResponse<OrgMemberCoreDto>` |
| **`selectMemberByUserId`** | `SingleResponse<OrgMemberCoreDto>` ← ★ 真正的 DTO |
| `selectPageMemberBySelectPeopleIdData(PageDtoRequest<..>)` | `PageResponse<Long>` ← 只给 id |

**⇒ 只有三个方法能直接拿到 `OrgMemberCoreDto`：**
```
selectMemberBySelectPeopleData(...)     → ListResponse<OrgMemberCoreDto>
selectPageMemberBySelectPeopleData(...) → PageResponse<OrgMemberCoreDto>
selectMemberByUserId(...)               → SingleResponse<OrgMemberCoreDto>
```

### 2.2 按 id 查人（返回 Map）

```java
// 单个人 —— 注意返回是 Map，不是 DTO
SingleResponse<Map<String,Object>> resp = orgCommonAppService
        .selectMemberInfoById(SingleRequest.from(memberId));
Map<String,Object> member = resp.getData().getContent();
String name = (String) member.get("name");
Long   dept = (Long)   member.get("orgId");

// 扩展信息（另一个 Map）
SingleResponse<Map<String,Object>> ext = orgCommonAppService
        .selectMemberExtendInfoById(SingleRequest.from(memberId));
```

**★★★ 没有 `selectMemberInfoByIds`（批量按 id 查人**。要批量，用：
```java
// 用选人器形态批量拿 DTO
ListResponse<OrgMemberCoreDto> list = orgCommonAppService
        .selectMemberBySelectPeopleData(SingleRequest.from(selectPeopleDataObj));
```

### 2.3 按组织查人（只有 id）

```java
// 组织下的人 —— 返回 List<Long>，只有 id
SingleRequest<Map<String,?>> req = SingleRequest.from(Map.of("orgId", orgId));
ListResponse<Long> ids = orgCommonAppService.selectMemberByOrgId(req);

// 分页版 —— PageRequest（裸的，不是 PageRequest<Dto>）
PageResponse<Long> page = orgCommonAppService
        .selectPageMemberByOrgId(PageRequest.from(pageInfo, Map.of("orgId", orgId)));
```

**★★★★★ 要到人员详情，得两步：先拿 id，再逐个 `selectMemberInfoById`。
或者改用选人器形态 `selectMemberBySelectPeopleData` 直接拿 DTO —— 推荐后者。**

### 2.4 选人器（★ 拿 DTO 的正确方式）

```java
// 选人器结果 → 人员 DTO（强类型，推荐）
ListResponse<OrgMemberCoreDto> members = orgCommonAppService
        .selectMemberBySelectPeopleData(SingleRequest.from(selectPeopleData));

// 选人器 JSON 字符串版
ListResponse<OrgMemberCoreDto> members2 = orgCommonAppService
        .selectMemberBySelectPeopleDataJson(SingleRequest.from(json));

// 只要 id
PageResponse<Long> idPage = orgCommonAppService
        .selectPageMemberBySelectPeopleIdData(
            PageDtoRequest.from(pageInfo, selectPeopleIdData));
```

**⚠️ 注意 `selectPageMemberBySelectPeopleIdData` 的入参是 `PageDtoRequest`，不是 `PageRequest`** ——
`PageDtoRequest` 是「分页 + 列表参数」合一（微流程选人器的形态）。

### 2.5 按用户 id 查（唯一直接给 DTO 的单查）

```java
SingleResponse<OrgMemberCoreDto> resp = orgCommonAppService
        .selectMemberByUserId(SingleRequest.from(userId));
OrgMemberCoreDto member = resp.getData().getContent();
// member.getName() / member.getId() / member.getOrgId() ...
```

### 2.4 建人 / 改人

```java
// 普通建人
SingleResponse<Integer> r = ctpUserCoreAppService
        .create(SingleRequest.from(userDto));

// 外部同步建人（逐条校验消息）
ListResponse<SyncUserMessageDto> msgs = ctpUserCoreAppService
        .syncCreateBatchCheck(ListRequest.from(userDtoList));
// msgs 里逐条告诉你哪条失败

// 写前校验（避免脏写）
ctpUserCoreAppService.beforeCreateCheck(SingleRequest.from(userDto));
```

**★★★ `create` vs `syncCreateBatchCheck`：普通业务用 `create`；外部系统同步用 sync 版（能定位哪条失败）。**

**⇒ 45 个 `OrgCommonAppService` 方法全表见 `organization-ctpuser-method-index.md` §6.2。
   ★ 返回类型全部按字节码核对过，别假设是 DTO。**

---

## 三、流程 / 事项（@DubboReference）

```java
import com.seeyon.bpm.api.common.BpmAppService;
import com.seeyon.bpm.api.common.BpmTemplateAppService;
import com.seeyon.ctp.affair.api.microflow.AffairMicroflowAppService;

@DubboReference private BpmAppService bpmAppService;
@DubboReference private BpmTemplateAppService bpmTemplateAppService;
@DubboReference private AffairMicroflowAppService affairMicroflowAppService;
```

### 3.1 发起流程（两种路）

```java
// 路 A：完整 DTO（能带表单数据、选人）
SingleResponse<BpmSendResultDto> r = bpmAppService
        .send(SingleRequest.from(sendDto));
BpmSendResultDto result = r.getData().getContent();

// 路 B：按模板 id 发起
ListResponse<BpmTemplateDto> list = bpmTemplateAppService
        .startByTemplateId(SingleRequest.from(startDto));
```

**★★★★★ 发起是 `send` 或 `startByTemplateId`，不是 `activitySubmit`。**

### 3.2 流转五动作（语义不同，别混）

```java
bpmAppService.submit(SingleRequest.from(submitDto));      // 提交到下一节点
bpmAppService.stepBack(SingleRequest.from(stepBackDto));  // 退回上一节点
bpmAppService.repeal(SingleRequest.from(repealDto));      // 撤销（回发起人）
bpmAppService.stop(SingleRequest.from(stopDto));          // 终止（不可继续）
bpmAppService.takeBack(SingleRequest.from(takeBackDto));  // 取回（追回已发出）
```

| 动作 | 谁做 | 效果 |
|---|---|---|
| `submit` | 当前处理人 | 往下走 |
| `stepBack` | 当前处理人 | 往回退一步 |
| `repeal` | 发起人 | 整单回到发起人 |
| `stop` | 有权限者 | 终结，不能再继续 |
| `takeBack` | 发起人 | 追回已发出的 |

### 3.3 微流程里发事项（要拿 id 用 ReturnIds）

```java
// 不要 id
affairMicroflowAppService.createAffairByMicroflow(
        SingleRequest.from(infoDto));

// ★ 要 id
ListResponse<Long> ids = affairMicroflowAppService
        .createAffairByMicroflowReturnIds(SingleRequest.from(infoDto));
```

### 3.4 查「这个实体配了流程吗」

```java
SingleResponse<Boolean> r = bpmTemplateAppService
        .hasDesignTemplateByEntityName(SingleRequest.from("Order"));
```

**⇒ 26 个 `BpmAppService` 方法全表见 `bpm/appservice-method-index.md` §6.1。**

---

## 四、平台组件（@Autowired，同 JVM）

### 4.1 枚举

```java
import com.seeyon.boot.starter.enums.domain.service.*;

@Autowired private CtpEnumItemService ctpEnumItemService;

// 按枚举编码 + 项编码取项
CtpEnumItemDto item = ctpEnumItemService.selectByEnumCodeAndItemCode(enumCode, itemCode);
```

**⚠️ 枚举（`ctp_enum*`）和选项集（`udc_enum*`）是两套表，别混用 —— 见 `udc/setting/option-set/create.md`。**

### 4.2 文件

```java
@Autowired private FileService fileService;
// 上传/下载/取 URL —— 具体方法见 standard-product/ 下 file 相关格
```

### 4.3 i18n

```java
@Autowired private MessageRepository messageRepository;
String text = messageRepository.getMessage("key", args);
```

### 4.4 缓存

```java
import com.seeyon.boot.starter.cache.util.CacheUtils;
import com.seeyon.boot.starter.cache.util.RedisUtils;

CacheUtils.put(key, value);       // 本地缓存
RedisUtils.set(key, value);       // Redis
```

---

## 五、工具类（静态，`com.seeyon.boot.util`）

```java
import com.seeyon.boot.util.JsonUtils;
import com.seeyon.boot.util.StringUtils;
import com.seeyon.boot.util.bean.BeanCopier;
import com.seeyon.boot.util.id.Ids;

String json   = JsonUtils.toJson(obj);
MyDto dto     = JsonUtils.fromJson(json, MyDto.class);      // ★ fromJson，没有 toBean
Map<String,Object> m = JsonUtils.toMap(json);               // 转 Map
List<MyDto> l = JsonUtils.toList(json, MyDto.class);        // 转 List

Long   id     = Ids.gidLong();                              // ★ 平台长 id
String idStr  = Ids.gidString();                            // 字符串形态
String uuid   = Ids.uuidString();                           // UUID 形态
Date   fromId = Ids.analyzeDate(id);                        // 从 id 反解时间

MyDto copy    = BeanCopier.copy(source, MyDto.class);       // ★ 比 BeanUtils 快
```

**★★★★★ 四条（全部按字节码核对）：**

| # | 事实 |
|---|---|
| 1 | **`JsonUtils.fromJson(json, Class)` 反序列化** —— **没有 `toBean`**（我最初写错） |
| 2 | **`Ids.gidLong()` / `gidString()` / `uuidString()`** —— **没有 `newId()`**（我最初写错） |
| 3 | **对象拷贝用 `BeanCopier.copy`** —— 平台自己就用它（`updateBase` 偏移 768） |
| 4 | **`Ids.analyzeDate(id)` 能从 id 反解生成时间** —— 排查数据来源时好用 |

**`JsonUtils` 全表（18 个方法，选几个常用的）：**
```
toJson / toJsonThrowError / toJsonNotIncludeNull / toJsonLongToString / toJsonDecimalToString
fromJson / fromJsonThrowError
toMap / toStringMap / toList / toStringList
```

**⇒ 177 个工具类全表见 `boot-core-utils-and-annotations.md`。**

---

## 六、一个跨域完整示例

**需求**：自定义微流程「提交订单后派人审批」。

```java
@Service
public class OrderCustomMicroFlowServiceImpl implements OrderCustomMicroFlowService {

    @Autowired private OrderService orderService;                    // 本应用
    @DubboReference private OrgCommonAppService orgCommonAppService;  // 组织
    @DubboReference private AffairMicroflowAppService affairService;  // 事项
    @DubboReference private BpmAppService bpmAppService;              // 流程

    @Override
    public OrderDto submitOrder(OrderDto orderDto) {

        // ① 本应用：更新订单状态
        orderDto.setStatus("SUBMITTED");
        orderService.update(orderDto);

        // ② 组织：查订单负责人
        //    注意 selectMemberInfoById 返回 Map，不是 DTO
        SingleResponse<Map<String,Object>> m = orgCommonAppService
                .selectMemberInfoById(SingleRequest.from(orderDto.getOwnerId()));
        Map<String,Object> owner = m.getData().getContent();
        Long ownerMemberId = (Long) owner.get("id");

        // ③ 事项：生成待办（要 id）
        AffairMicroflowInfoDto info = new AffairMicroflowInfoDto();
        info.setSubject("订单待审批：" + orderDto.getOrderNo());
        info.setMemberId(ownerMemberId);
        ListResponse<Long> affairIds = affairService
                .createAffairByMicroflowReturnIds(SingleRequest.from(info));

        // ④ 流程：发起
        BpmSendDto send = new BpmSendDto();
        // ... 填 send（见 bpm/appservice-method-index.md）
        bpmAppService.send(SingleRequest.from(send));

        return orderService.selectById(orderDto.getId());
    }
}
```

---

## 七、Side Effects

| 调用 | 副作用 |
|---|---|
| `BpmAppService.send` / `startByTemplateId` | 建流程实例、生成待办、发消息、触发事件 |
| `BpmAppService.submit/stepBack/repeal/stop/takeBack` | 流转、写日志、改待办状态 |
| `createAffairByMicroflow*` | 建事项、发消息、进待办箱 |
| `CtpUserCoreAppService.create` | 建人员、触发同步 |
| 组件 `@Autowired` 调用 | 各自副作用（文件落盘 / 缓存写 / DB 写） |
| 工具类静态调用 | 无 |

**⇒ 跨域调用几乎都有外部可见效果。事务边界要想清楚：Dubbo 调用不在你的本地事务里。**

## 八、Known Constraints

| # | 约束 |
|---|---|
| 1 | **标品一律 `@DubboReference`，且入参必须包 `SingleRequest.from(...)`** |
| 2 | **取值两层：`resp.getData().getContent()`** |
| 3 | **摘掉 `@DubboReference` 直接 `@Autowired` 标品会注入失败** |
| 4 | **Dubbo 跨进程调用不在本地事务内** —— 本地回滚不会回滚远端 |
| 5 | **`createAffairByMicroflow` 不返回 id**，要 id 用 `...ReturnIds` |
| 6 | **发起流程用 `send` / `startByTemplateId`**，不是 `activitySubmit`（那是活动级） |
| 7 | **枚举 `ctp_enum*` 与选项集 `udc_enum*` 是两套表，id 不互通** |
| 8 | **id 用 `Ids.gidLong()`；JSON 反序列化用 `JsonUtils.fromJson`**（无 `newId` / 无 `toBean`） |
| 9 | **组织域查人返回类型不统一** —— `selectMemberByOrgId` 只给 `Long`，要 DTO 用 `selectMemberBySelectPeopleData` |
| 10 | **不存在 `selectMemberInfoByIds`** —— 批量查人用选人器形态 |

## 九、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 组织 45 方法 / 用户 18 方法 | `javap` 全量重建索引 + 逐个枚举 | **VERIFIED_STATIC_BYTECODE** |
| BPM 26 方法（含 send/submit/stepBack/repeal/stop/takeBack） | 同索引 `bpm/appservice-method-index.md` | **VERIFIED_STATIC_BYTECODE** |
| `createAffairByMicroflowReturnIds` | `ctp-affair-facade-5.3.600.jar` javap | **VERIFIED_STATIC_BYTECODE** |
| `BeanCopier.copy` 被平台自己使用 | `BaseEntityCurdService.updateBase` 偏移 768 | **VERIFIED_STATIC_BYTECODE** |
| 工具类清单 | `boot-core-utils-and-annotations.md` | **VERIFIED_STATIC_BYTECODE** |
| 真实跨域调用成功 | 未实测 | **UNVERIFIED** |

## 十、Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：所有方法名与签名（javap 逐个枚举）
- ✅ **引用既有 LIVE 格**：枚举/选项集两套表、自定义对象字段坑（不重复求证）
- ⚠️ **UNVERIFIED**：上面跨域示例的真实运行（需环境 + 实际 DTO 字段）
- ⚠️ **UNVERIFIED**：各标品 DTO 的必填字段（见 `appservice-dto-fields.md`）

## 十一、给 Agent 的判据

```
问「我要查组织里的人」
  → @DubboReference OrgCommonAppService
  → ★ 返回类型不统一，先看表：
     selectMemberInfoById          → SingleResponse<Map<String,Object>>
     selectMemberByOrgId           → ListResponse<Long>        （只有 id）
     selectMemberBySelectPeopleData → ListResponse<OrgMemberCoreDto>  ★ 要 DTO 用这个
     selectMemberByUserId          → SingleResponse<OrgMemberCoreDto>
  → 没有 selectMemberInfoByIds（不存在，别写）
  → 全表：organization-ctpuser-method-index.md

问「我要建人」
  → @DubboReference CtpUserCoreAppService.create
  → 外部同步用 syncCreateBatchCheck（能定位哪条失败）

问「我要发流程」
  → BpmAppService.send（完整 DTO）或 BpmTemplateAppService.startByTemplateId
  → 不是 activitySubmit

问「我要在微流程里生成待办并拿 id」
  → AffairMicroflowAppService.createAffairByMicroflowReturnIds

问「我要写枚举」
  → CtpEnumItemService（@Autowired，同 JVM）
  → ★ 枚举和选项集是两套表

问「我要生成 id」
  → Ids.gidLong() / Ids.gidString() / Ids.uuidString()
  → 没有 newId()（我最初写错，已按字节码更正）

问「我要拷贝对象」
  → BeanCopier.copy(source, Target.class)

问「跨域事务能回滚吗」
  → 不能。Dubbo 调用不在本地事务内，要自己做补偿
```