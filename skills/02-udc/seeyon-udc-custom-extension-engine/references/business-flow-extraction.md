# 抽 Service 业务流转（方法 → Dao/Service/事件）

目的：回答「我调这个方法，它实际会动哪些业务组件、落哪些表、发什么事件」。
方法签名只给传参和返回；DTO 字段给内容形状；**「之后会发生什么」只能反编译方法体**。

## 先认清两层结构（认错就抽空）

| 层 | 类形态 | 内容 |
|---|---|---|
| 门面 | `XxxAppServiceImpl implements XxxAppService` | 几乎全是**一行转发**：`return ListResponse.from(xxxService.select((Dto) checkAndGetParam(req)))` |
| 业务 | `domain/service/XxxService` | 真业务：查库、发事件、多线程、配置判断 |

**业务 Service 是具体类，不叫 `XxxServiceImpl`。** 按 `*Impl.class` 过滤只拿到门面层，
实测同一构件：只扫 Impl = 83 类 151 KB（全是转发），加扫 `domain/service` = 265 类 646 KB（真业务）。
两份都留着有用：门面层告诉你「哪个 AppService 方法对应哪个业务 Service」。

## 实现 jar 不在本地仓库，必须单独下（漏了这步整个平台都「追不到」）

`<MAVEN_REPO>/com/seeyon/` 里只有 **facade / api** 构件——纯接口 jar，没有实现类。
照它跑，322 个 AppService 只有 68 个能匹配到实现，于是把 BPM / 组织 / 事项 / 连接器
全判成「实现在平台服务端」。**那个结论是错的，只是没下实现 jar。**

实现类在独立的 `*-biz` 构件里，从 Artifactory 取（只读 GET，匿名可访问）：

```bash
# 列全量 biz 构件
curl -s "http://<内网IP>/artifactory/libs-release/com/seeyon/" \
  | grep -oE 'href="[a-z0-9.-]+"/>' | sed 's/href="//; s/\/"//' | grep -E "biz$"

# 批量下最新版（脚本在 seeyon-agent）
python tools/core/platform/fetch_biz_jars.py \
    --base http://<内网IP>/artifactory/libs-release/com/seeyon \
    --out <MAVEN_REPO>-extra
```

实测 21 个 `*-biz` / 40 MB / 15869 类 / 284 个 AppServiceImpl：
bpm-biz、organization-biz、ctp-{affair,user,message,media}-biz、
cip-{capability,connector,convert,manager,openapi-gateway}-biz、
app-{approval,common,doc}-biz、cdp-{data,schedule}-biz、m5-biz、portal-biz、ai-biz、udc-biz。

**该仓库没有 `-sources.jar`**：`/api/search/artifact?name=*-sources.jar&repos=libs-release`
返回 `{"results":[]}`，每个版本目录只有 `.jar` + `.pom`。只能反编译 class，拿不到注释和
局部变量名——不要再去翻源码 jar。

下完把 `--repo` 指到 `<MAVEN_REPO>-extra`：有实现 517 → **2127**，有流转 370 → **1884**。
同一批 jar 也覆盖 udc-biz 的更新版本（5.3.605 对本地 5.3.517），优先用新的。

## 接口 → 实现不能按名字猜（命名不规则）

`com.seeyon.bpm.api.common.BpmAppService` 的实现是 **`BpmApiAppServiceImpl`**，不是
`BpmAppServiceImpl`。按 `XxxAppService → XxxAppServiceImpl` 兜底会漏掉整个 BPM 核心接口，
而 flow 文件里明明有它的方法体——症状是「接口在、流转空」，看起来像平台没实现。

必须读字节码的 `implements` 子句建映射：

```bash
python tools/core/platform/build_impl_map.py \
    --repo <MAVEN_REPO>-extra \
    --emit docs/audit/artifacts/extension-surface-*/impl-map.json
# → 269 个接口 → 实现类
```

消费侧（`emit_action_index.py --impl-map`）的规则：先查字节码映射，命名规则只作最后兜底，
且必须 `(候选实现类, 方法名) in flow` 才算命中——**不许凭名字直接写实现类**，
否则会把不存在的方法标成有流转。

## 命令

工具在 seeyon-agent：`tools/core/platform/emit_service_flow.py`。

```bash
# ① 门面层（看转发关系）
python tools/core/platform/emit_service_flow.py \
    --repo <MAVEN_REPO>/com/seeyon --pkg udc-biz \
    --only-impl --suffix=-appservice --emit-dir <out>

# ② 业务层（按路径片段选目标类）
python tools/core/platform/emit_service_flow.py \
    --repo <MAVEN_REPO>/com/seeyon --pkg udc-biz \
    --paths "udc/collaboration/domain" "udc/page/domain" "udc/metadata/" \
            "udc/autocode/task" "udc/detection/" \
    --suffix=-domain --emit-dir <out>

# ③ 客户应用 biz（平台生成的 ServiceImpl，业务骨架最好的样本）
python tools/core/platform/emit_service_flow.py \
    --repo <MAVEN_REPO>/com/seeyon \
    --pkg <客户appId>-biz --emit-dir <out>
```

输出每个方法一节，按 `Service` → `Dao` → `Event` → `Util` 排序，每条给「类 → 方法名」。

## 三个必踩的坑

1. **`// Method com/seeyon/x.Y.m:` 的全限定名含 `/`**。字符集写成 `[\w.$]+` 就一条都匹配不到，
   结果是「0 个类有调用」而 exit 0。要写 `[\w.$/]+` 再 `.replace("/", ".")`。
2. **`--suffix -appservice` 会被 argparse 当成新选项**（以 `-` 开头），报 `expected one argument`。
   用等号形式 `--suffix=-appservice`。
3. **业务层类名不带 Impl**。写 `--paths` 时按**包路径片段**选，不要按类名后缀选。

## 读出来的三种典型流转

**① 查询组装**
```
Wrapper.and / Example$Criteria.andEqualTo          拼条件
XxxEntityDao.selectListByWrapper                    落库查
MultiThreadTransaction.executeSplit                 分批并发
Apps.getRequestContext / RequestContext.getUserId   取上下文
```

**② 事件驱动**
```
XxxProperties.isDeleteFirst          先看配置开关
XxxEvent.builder(...)                构造事件
EventBus.publishAfterTransaction     事务提交后才发
```
`publishAfterTransaction` 是关键：监听方看到的一定是已提交数据。要挂这条流程就监听那个事件，
不用改业务代码。

**③ 客户应用的生成式骨架**（平台按元数据生成，几百个 ServiceImpl 几乎同一个形状）
```
校验(EntityRuleUtil / EntityAuthHelper) → Dto转Entity → XxxEntityDao.insert/update → 触发特性/事件
```
说明平台业务骨架固定，客开不用重写，挂对应扩展点即可。

## 拿不到的（不要指望从字节码里得到）

| 项 | 为什么 |
|---|---|
| 业务规则语义 | 字节码只有调用没有「为什么」；规则要从 `if` 常量和配置项反推，不保证完整 |
| 真实 SQL | 实测 109 个 jar 只有 8 个 mapper XML——平台走 `boot-starter-dynamicsql` 动态拼 + MyBatis-Plus Wrapper。「查哪张表」只能从 `XxxEntityDao` 类名推断 |
| 参数实际取值 | `parameterData` 是 `Map<String,Object>`，键与值来源字节码里没有 |
| 分支走哪条 | 需真实请求 |

## 和其他两份事实配合

```
签名  packages/<构件>.md / domains/<域>.md     传什么类型
字段  dto-fields/<域>.md                       类型里有什么
流转  service-flow-*/<构件>.md                 调了之后发生什么
```
三份合起来才够写一段能跑的扩展代码。
