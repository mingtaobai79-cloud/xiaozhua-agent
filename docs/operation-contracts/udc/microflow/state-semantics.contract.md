# 微流程 `state` 语义（B-7）—— `MicroFlowDataStateEnum` 字节码实证

结论来源：`udc-common-5.3.517.jar` 字节码反编译（javap -c）+ `udc-biz-5.3.517.jar` 调用侧反编译
+ LIVE 交叉验证（test2，app=8704025620829192834）。
状态：**FOCUSED VERIFIED（字节码实证 + LIVE 一致）**。0 次 `/service`。

---

## 0. TL;DR

| 问题 | 答案 | 证据等级 |
|---|---|---|
| `state` 是什么 | `MicroFlowDataStateEnum` 枚举，只有 2 个常量 | **字节码实证** |
| `10` / `20` 分别是什么 | **10 = DRAFT，20 = RELEASE** | **字节码实证** |
| DB 存的是 code 还是 ordinal | 存 **`code()`**（10/20），非 ordinal（0/1） | **字节码实证**（`Messageable.codeOf` 按 `code()` 反查） |
| `state` 是不是发布标志 | **不是**。发布标志是 `publish_state`(0/1) | **字节码 + LIVE 交叉** |
| state=10 是否进代码生成 | **不进**。`CtpJobTask` / `selectEntity4Code` 硬过滤 `RELEASE(20)` | **字节码实证** |
| 本应用 7 个 state=10 映射节点 | 宿主 4 个 state=10 + 2 个 state=20（按微流程计 6 个宿主） | LIVE |

**一句话**：`state` 是「微流程数据行的生命周期态」（草稿 / 发布），`publish_state` 是「应用发布态」，两者正交。代码生成只吃 RELEASE(20)，前端路由不吃过滤。

---

## 1. 枚举定义（字节码铁证）

来源：`<MAVEN_REPO>/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar`
类：`com.seeyon.udc.common.enums.MicroFlowDataStateEnum`
（与 biz 侧 `udc-biz-5.3.517.jar` **版本完全对齐**，均 2026-06-17 构建，相差 3 分钟）

### 1.1 类签名

```java
public final class MicroFlowDataStateEnum extends Enum<MicroFlowDataStateEnum>
        implements com.seeyon.boot.enums.Messageable {
    public static final MicroFlowDataStateEnum DRAFT;
    public static final MicroFlowDataStateEnum RELEASE;
    private int code;
    public int code();
}
```

### 1.2 `<clinit>` 原始字节码（关键 16 行）

> **证据形式说明（auditor 2026-10-18 建议，已采纳）**：
> 本节给的是 **`javap -c` 的原始字节码指令流**，不是 CFR 反编译源码。
> 区别很重要：**反编译是二次加工**，可能受常量池顺序或反编译器重排影响，错了看不出来；
> **原始字节码错了会直接崩**（栈不配对、描述符不匹配）。
> 本切片是 B-7 的**单点依赖**（搞反则整片结论全反），故必须用原始字节。

```
  0: new  #4   // class MicroFlowDataStateEnum
  4: ldc  #8   // String DRAFT
  6: iconst_0  // ordinal = 0
  7: bipush 10 // ★ code = 10
  9: invokespecial <init>(String,int,int)
 12: putstatic #10 // DRAFT

 15: new  #4
 19: ldc  #11  // String RELEASE
 21: iconst_1  // ordinal = 1
 22: bipush 20 // ★ code = 20
 24: invokespecial <init>(String,int,int)
 27: putstatic #12 // RELEASE
```

> **判定关键是「配对」而不是「先后」**（auditor 原话，本切片采纳）：
> `putstatic DRAFT` 之前，栈上依次压入 `"DRAFT" → 0 → 10`，三者正是 `<init>(String,int,int)` 的三个实参。
> 所以 `DRAFT` 的 `(ordinal, code) = (0, 10)` —— 不是「10 恰好出现在 DRAFT 附近」这种位置推断。
>
> **附带确认**：`methods_count = 5`，枚举常量只有 `DRAFT` / `RELEASE`，**无第三个**，与 LIVE `state ∈ {10, 20}` 吻合。
>
> 复现：`javap -p -c com/seeyon/udc/common/enums/MicroFlowDataStateEnum.class`
> （本机 JRE 无 `javap`，需用 `<USER_HOME>/...

**等价 Java 源码**：

```java
public enum MicroFlowDataStateEnum implements Messageable {
    DRAFT(10),
    RELEASE(20);
    private final int code;
    MicroFlowDataStateEnum(int code) { this.code = code; }
    public int code() { return code; }
}
```

→ **`10 = DRAFT`，`20 = RELEASE`，无第三个常量。** 这与 LIVE 中 `state` 只有 {10, 20} 两个值完全吻合。

### 1.3 DB 存 code 不存 ordinal（关键，否则 10/20 无法解释）

`com.seeyon.boot.enums.Messageable`（`boot-core-5.3.358.jar`）字节码：

```java
public static <E extends Messageable> E codeOf(Class<E> clazz, int code) {
    for (E e : clazz.getEnumConstants())
        if (e.code() == code) return e;   // ★ 按 code() 匹配
    return null;
}
```

调用侧亦为 `.code()`：

```
MicroFlowService.selectEntity4Code:
  101: getstatic  MicroFlowDataStateEnum.RELEASE
  104: invokevirtual MicroFlowDataStateEnum.code()I     // → 20
  107: invokestatic  Integer.valueOf
  110: invokevirtual Criteria.andEqualTo("state", 20)
```

→ **DB 里 `state=20` 反序列化回 `RELEASE`，`state=10` 反序列化回 `DRAFT`。**

### 1.4 写 / 读 / 注册 三端闭环（auditor 2026-10-18 补证，已不再依赖间接推断）

上一版此节只有「读端 + 反向推理」。auditor 找到了 **TypeHandler 本体**，三端现在是闭环：

| 端 | 证据 | 位置 |
|---|---|---|
| **写** | `ps.setInt(i, parameter.code())` —— **写入用 `code()`，不是 `ordinal()`** | `boot-starter-mybatis` `com/seeyon/boot/starter/mybatis/type/EnumCodeTypeHandler#setNonNullParameter` |
| **注册** | `factory.setDefaultEnumTypeHandler(EnumCodeTypeHandler.class)` —— 设为**默认**枚举处理器 | `MybatisAutoConfiguration` L155 |
| **读** | `getNullableResult → codeOf(type, s) → 按 code 匹配` | 同 §1.3 |

→ **「DB 存 code」由间接推断升级为写读注册三端闭环的直接证据。**
→ 原反向推理「若是 ordinal，DB 会是 0/1 而非 10/20」**降为辅助论据**（它依然成立，但已非主证）。
→ 上一版曾写「有没有可能 MyBatis 层按 ordinal 写？我没直接证到写入端」——**该保留已可撤销。**
→ 教训：`TypeHandler` 不在 `udc-*` 系列 jar，而在 `boot-starter-mybatis`。**找框架层组件时不要只扫业务 jar。**

---

## 2. `state` 与 `publish_state` 正交（否证「草稿」误读）

### 2.1 LIVE 全库交叉（4755 行）

| state | publish_state | 行数 | 说明 |
|---|---|---|---|
| 10 (DRAFT) | 1 | **289** | 全部已发布 |
| 10 (DRAFT) | 0 | **0** | **不存在** |
| 20 (RELEASE) | 1 | 4445 | |
| 20 (RELEASE) | 0 | 21 | 未发布只在 RELEASE |

→ `state=10` 的 289 行 **100% 是 `publish_state=1`**。
→ 「state=10 是草稿所以未生效」这个推断**没有数据支持**（B-6 UNVERIFIED#11 原表述已由 main 在 `3a6b757` 撤回）。

### 2.2 为什么 DRAFT 行也会 publish=1

`state` 是**行级**生命周期态，`publish_state` 是**应用级**发布态。两者不在同一维度：

- 一个已发布应用里，某些微流程行仍可停留在 DRAFT（例如：从旧版本迁移过来、模板预设、被 `copy()` 复制出的新行）
- 代码生成**只挑 RELEASE**，但那只影响"是否进入代码产物"，不影响"应用是否已发布"

**字节码佐证**（javap -c 逐条复核，10 处调用点全量清单见 §8.10.4）：

> ⚠️ **订正记录（B-7 事实性订正，auditor D59 报 + main 常量池复核）**
> 本表旧版 5 行中 **3 行与字节码不符**，已按下述字节码事实重写。
> 旧版错在两处：(a) `MicroFlowService.create/update` 被写成写 DRAFT，实际这两个方法**全类 0 次 setState**；
> (b) `ApplicationShelf4UdcServiceImpl` 被写成下架置 DRAFT，实际该类**全类 0 次 setState**，
> 它调的是 `setPublishState(PUBLISHED)`（应用级发布态），与行级 `state` 不是同一个字段。

| 方法 | 对 `state` 的实际动作（javap 复核） | DRAFT 来源 / 条件 |
|---|---|---|
| `MicroFlowAppService.create` | **本方法不写 state**；调私有 `setServiceMfToDraft(dto)` | `setServiceMfToDraft` 只判 `type == SERVICE`：相等才 `setState(DRAFT)`，否则直接 return |
| `MicroFlowAppService.update` | **同上**，调 `setServiceMfToDraft(dto)` | 同一条 `type == SERVICE` 判定 |
| `MicroFlowService.create` | **0 次 setState**（方法体 94 行/91 指令内无 state 赋值；javap -c -p 签名边界口径，D63） | 走 `MicroFlowEntity.<init>` 字段默认值 DRAFT（路径 B） |
| `MicroFlowService.update` | **0 次 setState** | 不产生 DRAFT；只改非 state 字段 |
| `MicroFlowService.copy` | `setState(DRAFT)` | **`type != FRONTEND` 才置**（`if_acmpeq` 跳过 FRONTEND） |
| `MicroFlowService.recover` | `setState(DRAFT)` | **无条件**（恢复即回 DRAFT，写路径） |
| `OriginalMicroFlowReferenceDataReplaceResolver.resolve` | `setState(DRAFT)` | **无条件**（引用替换后） |
| `ApplicationShelf4UdcServiceImpl.buildChangePublishStateWrapper` | **本类全类 0 次 setState** | 调 `setPublishState(PUBLISHED)`；下架是**应用级发布态**路径，非行级 state 写路径 |

→ **DRAFT 是"`type=SERVICE` 被强制置 DRAFT / 新建走默认值 / copy(非 FRONTEND) / recover"的产物**，
与"应用是否发布"无关。**下架不写 `state`**（旧版此处为事实性错误）。

---

## 3. 生产口径判定：state=10 不进代码生成（本切片核心结论）

### 3.1 代码生成路径硬过滤 `RELEASE(20)`

**证据 1 —— `CtpJobTask.code()`（代码生成定时任务）**

```
CtpJobTask.code:
   93: ldc        String state
   95: getstatic  MicroFlowDataStateEnum.RELEASE
   98: invokevirtual MicroFlowDataStateEnum.code()I      // → 20
  104: invokevirtual Criteria.andEqualTo("state", 20)
```

`CtpJobTaskV27` 同构（同样 `andEqualTo("state", RELEASE.code())`）。

**证据 2 —— `MicroFlowService.selectEntity4Code`**

```
  99: ldc        String state
 101: getstatic  MicroFlowDataStateEnum.RELEASE
 104: invokevirtual code()I
 110: invokevirtual Criteria.andEqualTo("state", 20)
```

### 3.2 但前端路径不过滤 —— 这是 state=10 仍有产物的原因

> **调用方声明（铁律 30）**：`selectFrontendEntity4Code` 的调用方是**前端页面取流程定义**的链路
> （UI 侧按 appId 拉取可运行流程列表），**不是**代码生成链路（后者走 `selectEntity4Code`）。
> 「不过滤 state」这件事只在「前端可见性」这个场景下成立，**不能外推为「运行时执行不看 state」**。
> 运行时执行引擎不在 `udc-biz-5.3.517.jar`（无 runtime/exec/engine 包，2312 class 已核），
> 故「运行时是否执行 state=10」仍是 UNVERIFIED，且**证据不在此处**，需转向 ctp-* / microflow-runtime-* 或部署产物。


`MicroFlowService.selectFrontendEntity4Code(Long appId)` 的 Wrapper 构造：

```
 10: and()
 14: ldc  String appId
 16: andEqualTo("appId", appId)
 21: and()
 25: ldc  String type
 27: andNotEqualTo("type", ENTITY_RULE.code())
 40: and()
 44: andNotEqualTo("type", SERVICE.code())
 59: and()
 63: andNotEqualTo("type", CUSTOM.code())
 78: selectListByWrapper(wrapper)
```

→ **整段无 `state` 条件。**
→ 前端类微流程（`type=FRONTEND`）在生成时**不按 state 过滤**。

**证据强度：已证（不是「未能 LIVE 验证的推论」）**

上一版我在这条上留了「这是我唯一没能用 LIVE 直接验证的推论」的尾巴。auditor 指出该尾巴多余，判断正确：

> 字节码层「同文件、相邻方法逐行 diff」已是最高强度静态证据。

| 方法 | 条件序列 |
|---|---|
| `selectEntity4Code` | `appId` + 排除 3 类 type + **`andEqualTo("state", RELEASE.code())`** |
| `selectFrontendEntity4Code` | `appId` + 排除 3 类 type |

→ 同文件、同封装、同 `selectListByWrapper` 调用，**唯一实质差异就是 state 过滤这一行**。
→ 其余条件逐条相同，可排除「换个等价写法实现同样过滤」的可能。
→ **本条按「已证」记，不留保留语气。**（LIVE 只能观察结果，反而更弱）

### 3.3 结论：分类型判定，不能一刀切

| 微流程 type | 生成路径 | 是否按 state 过滤 | state=10 是否生效 |
|---|---|---|---|
| `type=0`（服务/事件/定时等） | `selectEntity4Code` / `CtpJobTask` | **是**（只取 20） | **否** |
| `type=1`（FRONTEND） | `selectFrontendEntity4Code` | **否** | **是** |
| `type=3` | 见 `selectEntity4Code`（排除 ENTITY_RULE/FRONTEND/FUNCTION） | 是 | 否 |
| `type=2`（ENTITY_RULE） | 被 `selectEntity4Code` 排除 | 不适用 | 不适用 |

**→ 这是本切片对 B-6 UNVERIFIED#11 的实质回答：不能只问"是不是 state=10"，必须同时问"是哪个 type"。**

---

## 4. 本应用实测（app=8704025620829192834）

### 4.1 9 个映射节点的宿主（6 个微流程）

> **口径声明（铁律 7 三层教训必须并存，不得只留本应用）**：
> - **第 0 层 · 应用范围**：本应用 `8704025620829192834` → **9 个**映射节点（本节分母）
> - **第 1 层 · 遍历位置**：全库 R1（仅顶层 nodes）= **42 个** ← 漏掉分支内嵌套
> - **第 1 层 · 遍历位置**：全库 R3（递归 node 容器 + 跳 REF_SLOTS）= **131 个** ← 权威全库值
>
> 本应用 R1=R3=9（无分支内嵌套），**但不得因此删除 42/131 两层教训** —— 将来做全库统计会重犯。
> 本节只回答「本应用哪 6 个宿主承载这 9 个映射节点」，不做全库统计。

| 微流程 id | name | state | publish | type | 映射节点数 | 代码生成是否取 |
|---|---|---|---|---|---|---|
| 1524985498115296151 | xzhSvcEvtBpDA | **10 DRAFT** | 1 | 0 | 1 | **否** |
| -3790333238868911627 | xzhStdReal31046 | **10 DRAFT** | 1 | 0 | 2 | **否** |
| -1014184770817921434 | xzhFinalAllNodes | **10 DRAFT** | 1 | 0 | 3 | **否** |
| 862673936068342178 | xzhSvcDefK4Ge | **10 DRAFT** | 1 | 0 | 1 | **否** |
| -8675485534859429311 | xzhSvcSchcHXa | 20 RELEASE | 1 | **0** | 1 | **是**（state=20 已满足过滤） |
| -5161505652062878096 | xzhRestMf | 20 RELEASE | 1 | 3 | 1 | **是** |

**三个数量必须分清（D52 §四 铁律 28）：**

```
① 节点数        按 state = {10: 7, 20: 2}   合计 9
② 宿主行数      按 state = {10: 4, 20: 2}   合计 6
③ 宿主总行数                 = 6
④ 每宿主节点数直方图 = {1: 4, 2: 1, 3: 1}   ← 实测，用于核对「N 行各含 M 个」
```

> 直方图 `{1: 4, 2: 1, 3: 1}` 的含义：4 个宿主各含 1 个节点、1 个宿主含 2 个、1 个宿主含 3 个。
> 校验：`4×1 + 1×2 + 1×3 = 9` ✅ 与节点总数一致。
> **和校验只保证总量，不保证分布**（铁律 28）—— 9 可以拆成 4+1+1，也可以拆成 3+3+3，
> 所以凡「N 行各含 M 个」必须附实测直方图，不能只报总和。

> **订正记录（本切片自查）**：本表初稿把 `xzhSvcSchcHXa` 的 `type` 写成 1（FRONTEND），
> 据此解释"它为何仍有产物"。实测其 `type=0`。**该归因是错的** —— 它能进代码生成的真正原因是
> `state=20 RELEASE` 已满足 `CtpJobTask` 的过滤条件，与 type 无关。
> 教训：不能拿"未验证的类型假设"去解释一个已观察到的现象；先查字段值，再写机制。

### 4.2 业务回答（验收标准 3）

> **问：本应用 state=10 的宿主在生产运行时是否生效？**
>
> **答：分两条路，不能一句话答。**
>
> **口径先分清（这是本节的第 0 层）**：
> ```
> 本应用 state=10 的「行（微流程）」= 5 行      ← 分母用于「生效与否」
> 本应用 state=10 的「映射节点宿主」= 4 行      ← 分母用于「9 个映射节点」
> 本应用 state=10 的「映射节点」  = 7 个
> ```
> 初稿把「7 个 state=10 宿主」写错了——7 是**节点数**，宿主只有 4 行。分母混用会让人以为还有 3 行没讨论。
>
**① 9 个映射节点的 4 个 state=10 宿主 → 代码生成不取**
4 个宿主全为 `type=0`，被 `CtpJobTask` 的 `state=20` 硬过滤排除（§3.1 字节码已证）。

**运行时是否执行 → UNVERIFIED，但理由是"证据不在此处"，不是"我还没查"**
（本条按 auditor 2026-10-18 补证重写，替换原「可能走 Redis/OSS 绕过」的推测）

```
udc-biz-5.3.517.jar 内 .class 文件数 = 2312（unzip -l | grep -c '\.class$'，含 $ 内部类 456、顶层 1856）
顶层包只两个：cn/hutool、com/seeyon
无 exec / engine 包；deployment/ 只含 DeploymentManager / DeploymentService / MigrationManager（部署动作，非执行引擎）
含 "runtime" 字样的仅 2 个类，均非执行引擎：
  MicroFlowRuntimeMetadataQueryService            → 元数据查询（依赖 ctp-metadata-api）
  MicroFlowRuntimeEntityDataSourceDtoConstructor  → 数据源 DTO 构造器
```
→ **微流程执行引擎根本不在这个 jar 里。无论怎么读 udc-biz，都不可能证到「运行时不执行 state=10」——
   不是没查到，是证据不在此处。**

> **⚠️ 一个差点踩的陷阱（auditor 自述，本切片记录）**：
> `MicroflowRepository.selectById(id) → microFlowService.getEntityById(id) → dao.selectById(id)` 纯主键、**无 state 过滤**，
> 看起来能支持「运行时不看 state」。但其消费方是
> `model/parser/AbstractReferenceParser`、`model/parser/ReferenceChecker`、`model/RelationService` 等 ——
> 全是**设计态模型解析 / 引用检查 / 关系维护**，不是运行时执行。
> → 它只能证明「运行时**可以**按 id 加载 state=10」，**不能**证明「运行时执行时**会**走这条路」。
> → 只报前半句就会得出「state=10 运行时生效」的错误结论。**这正是 UNVERIFIED 要防的错。**

**下一步证据源（不是「继续读 udc-biz」）**：
1. 查 `ctp-*` / `microflow-runtime-*` 类 jar 是否存在执行引擎
2. 或直接看部署产物：Redis / OSS 里编译后的流程定义**是否带 state 字段**
>
> **② 但本应用 state=10 共 5 行，第 5 行生效**
> ```
> xzhFront27390   state=10  type=1 (FRONTEND)  maps=0  publish=1
> ```
> 按 §3.3 分类型表：`type=1` → `selectFrontendEntity4Code` **不过滤 state** → **该行 state=10 生效**。
> （调用方：前端页面取流程定义链路；**不代表运行时执行不看 state** —— 引擎不在 udc-biz，铁律 30）。
> 它无映射节点，**不影响 9 个映射节点的判定**，但读者不能把本节读成「本应用整片 state=10 都不生效」。
>
> **⚠️ 铁律 16 的变体：报「4 个不生效」必须同时报「全片 5 个里 1 个生效」。**
> 只报分子不报分母，等于用口径收窄制造了一个看起来完整的答案。

> **订正记录（auditor D51 §四② 抓出）**：本节原问句写「7 个 state=10 宿主」，把**节点数 7** 当成**宿主行数**；
> 且只讨论 4 个 type=0 宿主，遗漏了第 5 行 `xzhFront27390`（type=1，state=10 生效）。
> 两个问题叠加的效果是：读者会以为「本应用 state=10 全不生效」，而真相是 4/5 不生效、1/5 生效。
> 这正是铁律 17（报分布先声明分母）在「生效判定」上的实例。

### 4.3 本应用 47 行 state 分布（复核 main D48）

```
本应用 47 行：state {10: 5, 20: 42}
  · state=10 的 5 行中，4 行含映射节点（共 7 个）
  · 第 5 行 4774717078364917047 xzhFront27390 是 type=1 FRONTEND（无映射节点）
全库 4755 行：state {10: 289, 20: 4466}
```

> 注：B-6 契约 L252 曾写作 `{10: 45, 20: 2}`，系数字拆反（45/2 ↔ 5/42），已在 main `3a6b757` 与 B-7 本轮复核确认。

---

## 5. 第三个状态列：`last_version_metadata_state`

`udc_microflow_info` 共有 3 个含 `state` 的列：

| 列 | 类型 | 取值 | 语义 | 证据 |
|---|---|---|---|---|
| `state` | smallint(6) | {10, 20} | `MicroFlowDataStateEnum` DRAFT/RELEASE | 字节码 |
| `publish_state` | smallint(6) | {0, 1} | 应用发布态 | B-6 + LIVE |
| `last_version_metadata_state` | smallint(6) | {0, NULL} | 旧版本元数据态 | LIVE（**语义 UNVERIFIED**） |

### 5.1 `last_version_metadata_state` 全库分布

```
NULL : 453
0    : 4302
```

**不是二值 0/1，而是 {0, NULL}** —— 与 `publish_state` 的 {0,1} 结构不同。
枚举类 `MicroFlowLastVersionMetadataStateEnum` 在 `MicroFlowEntity` 中定义，默认值 `DISABLED`（字节码），
但本机 jar 中**未找到该枚举定义**（属外部依赖），故只能给出 LIVE 分布，**语义标 UNVERIFIED**。

### 5.2 三列完整交叉（全库）

| state | publish_state | last_version_metadata_state | 行数 |
|---|---|---|---|
| 10 | 1 | NULL | 18 |
| 10 | 1 | 0 | 271 |
| 20 | 0 | NULL | 12 |
| 20 | 0 | 0 | 9 |
| 20 | 1 | NULL | 423 |
| 20 | 1 | 0 | 4022 |

→ 三列**互相独立**，无任何组合缺失或强制约束。

---

## 6. 稳定区分特征：无

对全库 32 列逐一做「state=10 集合 vs state=20 集合」的不相交检验：

- **唯一完全互斥的列是 `id`**（主键，必然互斥）→ **假阳性，无业务含义**
- `creation_method`：全库 100% 为 0（4755/4755）→ **零区分力**
- `type`：state=10 有 type∈{0,1,2,3}，state=20 也有 {0,1,2,3} → **不可区分**（仅比例不同）
- `trigger_type`、`group_type`、`version`、`version_code`、`owner_code` 等：**均不可区分**

**结论：`state` 不由任何其他业务字段派生，是一个独立写入的生命周期列。**

这与「state 是枚举而非计算字段」的字节码证据一致。

---

## 7. 为什么 state 不可能是「版本/草稿状态」

> **本节已按 main D51（commit d283b99）重写。** 原论据「289 行 state=10 无同名 state=20 兄弟行」**已作废** ——
> 按 `name` 跨应用分组确实存在 32 组同名同时含 state=10 与 20（涉 36 行 state=10），但那 32 组是
> 「同租户·不同应用」的同名流程（32/32 组内 `tenant_id` 相同、`app_id` 全不同；`original_id` 32/32 为 None 且组内无交叉），
> 不是同一流程的两个版本。**决定性证据见 §7.1。**

### 7.1 结构性证据（不依赖统计相关性）

```
按 (app_id, name) 分组 → 多行组数 = 0
```

→ **每个应用内每个名字只有一行，数据库中根本不存在「同一流程的多个版本行」。**
→ 既然不存在版本行，`state` 就不可能是「版本/草稿状态」——这是**结构性结论**，不是相关性推断。

本轮实跑复核（`tools/core/b7b_causal.py`（**已移入 `_attic_pending/legacy-audit/b7b_causal.py`**，仓库内已无此路径））：
```
(app_id,name) 多行组数        = 0      ← 结构性
name 跨应用同名组数           = 847
  其中同时含 state=10 与 20   = 32     ← 这就是 D51 说的 32 组，跨应用同名，非版本对
```

### 7.2 机制解释（DRAFT 的产生路径）

`MicroFlowEntity` 的 `state` 默认值为 `DRAFT`（字节码 `<init>` 中 `putfield state = DRAFT`）。
DRAFT 的产生路径见 §2.2（字节码复核后为 4 条 DRAFT 写路径 / 10 处调用点中的 4 处），其中：
- `setServiceMfToDraft`（被 `MicroFlowAppService.create/update` 调用）：**只判 `type == SERVICE`**
- `MicroFlowService.copy`：产生**新 id**，且仅 `type != FRONTEND` 才置 DRAFT
- `MicroFlowService.create`：**不写 state**，走字段默认值（同样产生新 id）
- `OriginalMicroFlowReferenceDataReplaceResolver.resolve` / `MicroFlowService.recover`：无条件置 DRAFT
- **下架路径不写行级 `state`**：`ApplicationShelf4UdcServiceImpl` 全类 0 次 `setState`，
  下架走 `setPublishState(PUBLISHED)`（应用级发布态）——旧版此处为事实性错误，已订正

→ **DRAFT 是新行或原地改态的产物，天然不产生「同 id 双 state 行」。**
→ 所以"同名兄弟行"这个检测维度本身就不适用于 `state`（它适用于 `name` 重复，见 B-6 §1.4）。

---

## 8. 对 B-6 UNVERIFIED#11 的更新

**原表述（B-6，已由 main `3a6b757` 部分撤回）**：
> 本应用 7/9 映射节点宿主 state=10；若业务只认已发布态，本应用实际应用面只有 2 个。

**B-7 更新为**：

> `state` = `MicroFlowDataStateEnum`{DRAFT=10, RELEASE=20}，与 `publish_state`(0/1) 正交。
> 本应用 7 个映射节点宿主（4 个微流程）全部 `state=10 DRAFT` + `publish_state=1`，
> **其 `type` 全部为 0**，因此**不被代码生成任务 `CtpJobTask` 获取**（该任务硬过滤 `state=RELEASE.code()==20`）。
> 
> 已确定：**代码生成口径下这 4 个微流程的映射节点不产出代码。**
> 仍 UNVERIFIED：**运行时是否实际执行这 4 个 state=10 宿主** —— 理由是**执行引擎不在本 jar 内**（§4.2：2312 class、无 exec/engine 包），
> 不是「可能走 Redis/OSS 绕过」这种推测。需换证据源（`ctp-*`/`microflow-runtime-*` jar，或部署产物里流程定义是否带 state）。
> 
> 已否证：**"state=10 是草稿态所以整个应用只有 2 个生效"** —— 该推断混淆了 `state` 与 `publish_state`。

---

## 9. 复现

```bash
# 枚举字节码（DRAFT=10 / RELEASE=20）
python tools/core/b7_enum.py

# LIVE 交叉（三状态列 + 区分度）
python tools/core/b7_state_x.py
python tools/core/b7_tristate.py

# 类型/路径分析
python tools/core/b7_type_path.py

# 闸门（GATE-STRICT：路径断言 + 字节码断言 + 文档口径断言）
python tools/core/b7_gate.py     # EXIT=0 PASS / EXIT=1 FAIL
```

---

## 8.10 因果方向：三级报告，样本不足 → 无法定论（按 D52 重写）

> **本节已按 main D52（commit 0badd4d）重写。**
> 上一版我把「16.8×」与「控 type 后 6.0×」当作判定依据，**两处引用均已被 D52 作废，本版已删除**。

### 8.10.1 三级报告（必须三级都报，缺一即误导）

**本应用（47 行样本，带映射的只有 6 行）**

| 级别 | state=10 含映射 | state=20 含映射 | 倍数 | 可否作结论 |
|---|---|---|---|---|
| **级1 粗相关** | 80.0% (4/5) | 4.8% (2/42) | 16.8× | ❌ 含 `type` 混杂，**不是效应量** |
| **级2 控 type=SERVICE** | 100% (4/4) | 16.7% (1/6) | 6.0× | ❌ n=4/6，**样本不足以支撑估计** |
| **级3 双重分层**（type=SERVICE × trigger_type） | tt=0: 1/1；tt=2: 3/3 | tt=0: 0/1；tt=2: 0/2 | — | ❌ 每格 n=1~3，**无法定论** |

> **级3 的陷阱（D52 §二 明确指出，本切片认同并记录）**：
> 双重分层后看起来「100% vs 0%，效应更强」，但这**恰恰是分层分析最经典的陷阱** ——
> 分到样本不足时效应会放大，看起来更有说服力，实际上一无所知。
> **正确结论是「无法定论」，不是「效应更强」。**

**全库（换数据源，289 行 state=10，样本足够）**

| 级别 | state=10 含映射 | state=20 含映射 | 倍数 | Fisher 精确 p |
|---|---|---|---|---|
| 级1 粗相关 | 3.1% (9/289) | 1.0% (44/4466) | 3.16× | **p=0.0041（显著）** |
| 级2 控 type=SERVICE | 5.9% (9/152) | 3.4% (43/1249) | 1.72× | **p=0.1668（不显著）** |
| 级3 再控 trigger_type=0 | 1.8% (1/56) | 2.6% (5/196) | 0.70× | **p=1.0000 无差异** |
| 级3 再控 trigger_type=1 | 0.0% (0/31) | 1.0% (1/102) | 0.00× | **p=1.0000 无差异** |
| **级3 再控 trigger_type=2** | **12.3% (8/65)** | **3.9% (37/951)** | **3.16×** | **p=0.0059 显著** |
> 三档倍数齐报：0.70× / 0.00× / 3.16×（必须三级都报，缺一即误导）——少报任一层即隐藏「仅 tt=2 显著」的结构；三档 p=1.0000/1.0000/0.0059 必须同表出现

> **★ 三级表的正确读法（`49f0293` 首版读错，`D54` 用 Fisher 纠正）**：
> **不能只看倍数判方向 —— 0.70× 和 0.00× 的 Fisher p 都是 1.0000，那是「无差异」，不是「反向」。**
> 小样本下 0/31 vs 1/102 的倍数可以是任意值，但没有统计含义。
>
> → 0.70×/0.00× 两层「反向」表述**超出数据**（p=1.0000 是无差异）；但「效应条件化」同样**超出数据**（aud_b7_n1n2.py 两项检验）：
>   ① Woolf OR 同质性检验：tt∈{0,1} OR=0.566 vs tt=2 OR=3.467，Q=2.430 df=1 **p=0.1191 不显著**——层间异质性未达显著，不支持「条件化」这一异质性断言；
>   ② leave-one-app-out：剔除本应用后 tt=2 层 5/62 (8.1%) vs 37/949 (3.9%) = 2.07×，**p=0.1746 不显著**——本应用在 tt=2 的 state=10 组贡献 3/8 行（37.5%）、state=20 组贡献 0/37 行。同一份数据：粗相关阶段把本应用当离群点剔除，分层阶段却把它留在格子里叫显著——两阶段口径相反（铁律 1）。
> → 合并层（控 type 后 p=0.1668）不显著 ≠ 子层不存在（铁律 26 反向版）；但子层显著也 **不能升级为「条件化效应」**——显著性对单个应用敏感且层间异质性不显著。
> → **唯一可支持的表述**：「合并层不显著（p=0.1668）；分层仅 tt=2 显著（p=0.0059），但层间异质性不显著（Woolf Q p=0.1191）且该显著性对单个应用敏感（剔除后 p=0.1746）→ **整体 UNVERIFIED，无法定论**」。
> → 错误表述（四个，均超出数据）：「方向会翻转」「存在 Simpson 交互」「state 无任何效力」「效应条件化于 trigger_type」。
>
> 复现：`python tools/core/b7c_main_fisher_recheck.py`（Fisher 四分支，EXIT=0）+ `python tools/core/b7_n1n2_check.py`（Woolf Q + leave-one-app-out，EXIT=0）

→ **换到足够样本的数据源后，控制 `type` 即不显著。**
→ **铁律 1**：以上为**全库口径**，不可回流为本应用结论。

### 8.10.2 `type` 不是「混杂变量」，而是「唯一有意义的比较域」

这一点上一版说错了。`type` 不只是统计上的混杂——它**在语义上限定映射节点能出现在哪里**。

**`MicroFlowTypeEnum` 字节码实证**（`udc-common-5.3.477.jar`，`<clinit>`）：

```
SERVICE      = (0)   // iconst_0 / iconst_0
FRONTEND     = (1)
ENTITY_RULE  = (2)
CUSTOM       = (3)
FUNCTION     = (4)

BACKEND_TYPES  = {SERVICE, CUSTOM}          // #21
FRONTEND_TYPES = {FRONTEND, FUNCTION}       // #22
CALL_CHAIN_TYPES = {SERVICE, CUSTOM, FRONTEND, FUNCTION}  // #20（D52 订正：原漏 SERVICE，<clinit> 字节码四成员实测）
```

**映射节点宿主的 type 分布（全库实测）：**
```
映射节点出现在:  SERVICE 130 个 / CUSTOM 1 个
```

→ **映射节点只在 SERVICE（和极少量 CUSTOM）里出现，FRONTEND 里 0 个。**
→ 所以「state=10 含映射率更高」的粗相关，**大部分来自 state=10 组里 SERVICE 占比更高**
   （本应用：SERVICE 在 state=10 组占 80%，在 state=20 组只占 14.3%）。
→ 正确表述不是「控制混杂变量」，而是：**只有在 SERVICE（或 CUSTOM）内部比较才有意义**，
   因为其它 type 结构上就不可能有映射节点。

### 8.10.3 三种假设的判定

**假设 1：`state=10` 标记「含数据加工/映射能力」→ 映射集中**
→ **否证。** state=10 的 289 行里只有 9 行含映射（3.1%），**96.9% 不含映射**。
   state 不可能是"含映射能力"的标记。

**假设 2：含映射的流程在保存/发布时被置为 `state=10`（结果非原因）**
→ **无代码路径支撑，且时间序方向不符。**
- 字节码：`MicroFlowService.update` 的状态转换分支只判 `type`（SERVICE/CUSTOM）与原 `state`，
  **不读任何节点内容**；`setServiceMfToDraft` 同样只判 `type==SERVICE`。
- 时间序：`state=10` 组「从未修改过」比例 37.7%，`state=20` 组 39.8% —— **方向与假设 2 相反**（差异极小，不足以定论）。
→ 若 state 是「含映射之后才变 10」，state=10 组应更多是「修改过的」，实测不是。

**假设 3：两者都受第三字段决定 → 相关非因果**
→ **成立，且第三字段就是 `type`（见 8.10.2）。**

### 8.10.4 `state=10` 的真实成因（字节码，这是本轮最硬的发现）

穷举全部 **10 处** `setState(MicroFlowDataStateEnum.X)` 调用点（auditor D52 L1/L3 双口径复核 + main D55 独立字节码复核一致；原写 17 处系笔误，无法以任何口径复现），
**B-7 订正轮已用脚本对全 22 个 udc-*-5.3.517 jar 独立重扫确认恰为 10 处**（`tools/core/b7_gate.py`（**已移入 `_attic_pending/legacy-audit/b7_gate.py`**，仓库内已无此路径） 的 10 处清单断言即绑此结果）：

| # | 类.方法 | 赋的常量 | 条件 |
|---|---|---|---|
| 1 | `MicroFlowAppService.setServiceMfToDraft` | DRAFT | `type == SERVICE` 才置，否则 return（被 `MicroFlowAppService.create`/`update` 调用） |
| 2 | `MicroFlowService.copy` | DRAFT | `type != FRONTEND` 才置（`if_acmpeq` 跳过 FRONTEND） |
| 3 | `MicroFlowService.recover` | DRAFT | **无条件**（恢复即回 DRAFT） |
| 4 | `OriginalMicroFlowReferenceDataReplaceResolver.resolve` | DRAFT | **无条件**（引用替换后） |
| 5 | `MicroFlowUpgradeAppServiceImpl.generateCustomMfFromExtendAppService` | RELEASE | 无条件（升级期生成自定义 MF 即发布态） |
| 6 | `Application4PageMetaDataService.getMicroFlowDefinitionList` | RELEASE | **查询 DTO 上的 state**（`MicroFlowQueryDto.setState`），非实体写 |
| 7 | `AbstractPresetTemplateHandler.generateByName` | RELEASE | **查询 DTO 上的 state**，非实体写 |
| 8 | `AbstractPresetTemplateHandler.buildMicroFlowDefinitionDto` | RELEASE | 无条件（模板预设建出来就是 RELEASE） |
| 9 | `SubMicroFlowGenerateParamDto.to` | RELEASE | 无条件（子流程生成参数） |
| 10 | `SubMicroFlowReferenceDataReplaceResolver.resolve` | RELEASE | 无条件（引用替换后置 RELEASE） |

→ **DRAFT 写路径 4 处 / RELEASE 写路径 4 处 / 读侧过滤 2 处**（#6 `getMicroFlowDefinitionList`、#7 `generateByName`，接收者 `MicroFlowQueryDto`；其余 8 处接收者为 `MicroFlowDefinitionDto`/`MicroFlowEntity`，属实体写）；**合计 10 处**。
→ `ApplicationShelf4UdcServiceImpl` **不在此清单内**：该类全类 0 次 `setState`，下架走 `setPublishState`。

由此得到两条主路径：

**路径 A —— `MicroFlowAppService.setServiceMfToDraft`（显式，只看 type）**
```java
0: getstatic MicroFlowTypeEnum.SERVICE
7: equals(dto.getType())
10: ifeq 20                        // 不是 SERVICE → 直接返回
13: getstatic MicroFlowDataStateEnum.DRAFT
17: dto.setState(DRAFT)            // 是 SERVICE → 置 DRAFT
```

**路径 B —— 实体默认值（隐式）**
```java
MicroFlowEntity.<init>:
  getstatic MicroFlowDataStateEnum.DRAFT
  putfield  state                    // 字段默认值就是 DRAFT
```
且 `MicroFlowService.create` 的 **94 行**（91 指令，javap -c -p 方法签名边界口径）字节码里**完全没有任何 `setState`**；`update` 162 行内同样 0 次。**订正史**：初版 94 → 上一订正误改 321/3710（未按签名边界切分，把后续 8 个方法并入 create 段），D63 再订正回 94/162 →
新建时若不显式指定，就走默认值 DRAFT。

**数据侧验证（全库 state=10 的 289 行按 type 分）：**
```
SERVICE     152 (52.6%)   ← 路径 A 可解释
FRONTEND    135 (46.7%)   ← 路径 B（默认值）可解释；代码里无任何类同时含 FRONTEND 与 DRAFT
ENTITY_RULE   1 ( 0.3%)
CUSTOM        1 ( 0.3%)
```
→ **`state=10` 的成因是「type=SERVICE 被强制置 DRAFT」+「新建走默认值 DRAFT」，与节点内容完全无关。**

### 8.10.5 最终判定

| 问题 | 判定 | 依据 |
|---|---|---|
| 现象是否真实 | **是** | 本应用粗 16.8×（不可引用为效应量，仅现象存在）；全库粗 3.16× 显著、控 type 后 1.72× 不显著——分层不改变「本应用现象存在」，但全库效应方向无法定论（UNVERIFIED） |
| 粗倍数 16.8× 能否引用 | **不能** | 含 type 构成差异，虚报效应 |
| 净 6.0× 能否引用 | **不能** | n=4/6，分层后样本不足 |
| 因果方向 | **UNVERIFIED，且无代码路径支持 state 由映射决定** | `update`/`setServiceMfToDraft` 分支均只看 type |
| 已排除字段 | `creation_method`（全 0）、`group_type`（全 0） | LIVE |
| `trigger_type` | **与 state 相关的混杂变量；分层后 tt=2 子层显著，但该显著性对剔除本应用敏感（2.07×, p=0.1746），整体 UNVERIFIED** | state=20 里 trigger=2 占 36/42；aud_b7_n1n2.py |
| 剩余 1.7×（全库）是否有独立含义 | **UNVERIFIED**（p=0.1668 不显著；tt=2 子层 p=0.0059 但 Woolf Q p=0.1191 异质性不显著、剔本应用后 p=0.1746） | aud_b7_n1n2.py |

### 8.10.6 对 B-6 §8.10 的更新建议

> B-6 §8.10 曾写「16.7 倍」（main 已在 `0badd4d` 重写为三级报告）。
> B-7 附议 D52 的处理，并补一条**机制侧**的限定：
>
> **`state=10` 不是「含映射」的结果或标记，而是 `type` 与「新建默认值」的产物。**
> 因此「映射节点集中在 state=10 流程」这个现象，**不应解读为 state 与映射存在因果**，
> 而应解读为：**SERVICE 类流程既是唯一能承载映射节点的类型，又更容易停在 DRAFT 状态**（路径 A 强制 + 新建默认）。
> 两者共享同一个上游原因（`type`），不是彼此的原因。

### 8.10.7 复现

```bash
python tools/core/b7c_threelevel.py   # 三级报告 + 全库 Fisher 检验
python tools/core/b7c_mechanism.py    # type 枚举 / state x type 交叉
python tools/core/b7c_mechanism2.py   # 映射节点宿主 type + 分层比较
```

---

## 10. 未解决问题（移交下一片）

| # | 问题 | 为什么没解 | 下一步 |
|---|---|---|---|
| 1 | 运行时是否实际执行 state=10 宿主 | **证据不在此处**：udc-biz 2312 class 无 exec/engine 包，执行引擎不在该 jar | 查 `ctp-*`/`microflow-runtime-*` jar；或看部署产物（Redis/OSS 编译后流程定义是否带 state） |
| 2 | `last_version_metadata_state` 语义 | 枚举类属外部依赖，本机 3 个 udc jar 均无定义 | 找 `udc-api` jar 或从 `MicroFlowLastVersionMetadataStateEnum` 的调用点反推 |
| 3 | `type=3` 是什么 | `MicroFlowTypeEnum` 未反编译 | 反编译 `MicroFlowTypeEnum` 补全 0/1/2/3 语义 |
| 4 | 为何本应用 47 行里 5 行 DRAFT（10.6%），但全库只有 6.1%（289/4755） | 样本小，无统计意义 | 不追 |

---

## 附：本切片方法论增量

**铁律 9 的应用（本轮特别适用）**：
「说 jar 里没有 state 枚举之前，先证明搜索位置对」——
本轮实际遇到：`udc-biz.jar` 里**确实没有** `MicroFlowDataStateEnum.class`（13 个 common/enums 类不含它），
但它被 36 个类引用。此时**不能**下"代码里无枚举"的结论 —— 它是**外部依赖**。
最终在 `<MAVEN_REPO>/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar` 找到，且版本与 biz 完全对齐。
→ **"在这个 jar 里没有" ≠ "在代码里没有"。必须先枚举依赖，再下否定结论。**

**新增（建议 ROUTE 铁律 15）**：
**枚举语义必须从 `<clinit>` 字节码取 `bipush`/`sipush` 常量，不能从 DB 值反推。**
本切片若只看 DB（state ∈ {10,20}），无法判定 10=DRAFT 还是 10=RELEASE；
只有 `<clinit>` 的 `bipush 10 / bipush 20` 与 `ldc "DRAFT"/"RELEASE"` 配对，才能定死方向。
→ 这是"否定/命名结论必须先证明位置"在**常量取值维度**的应用。
