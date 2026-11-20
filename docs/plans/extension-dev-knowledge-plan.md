# 扩展开发知识方案：从需求到上线只解决一条链

> 制定日期：2026-11-21
> 适用范围：xiaozhua Agent 的 UDC 扩展开发知识重建
> 边界：**只解决我怎么建、怎么调、怎么编、怎么测、怎么排错。** 别人怎么调我的流程，不写。

---

## 0. 结论先行

这套知识不按“平台有什么”组织，而按 Agent 干活时的判断顺序组织：

```text
需求
  -> 先判路线：标准微流程 / 自定义微流程 / 扩展代码 / 自有 REST
  -> 再判合法性：我能用哪个层的东西
  -> 再查抓手：开放接口 / 基础能力 / 注解 / utils
  -> 再写代码：接口、签名、DTO、注入、事务
  -> 再编译构建：拉码 -> 本地编译 -> 平台构建 -> 部署
  -> 再验证：Controller / 微流程 / 构建日志 / 运行日志
  -> 最后清理：测试数据、临时脚本、循环依赖
```

每篇统一判据：

```text
L0 先看权限与副作用
L1 先看 classpath 与公开 API
L2 只走开放面
L3 看依赖声明
L4 本应用生成物优先 Service/AppService；直接 Dao 先核写链
```

原稿的“L0/L1 直接用；L4 随便用”不准确，本方案以此判据取代。

---

## 1. 范围与非目标

### 1.1 覆盖

| 类别 | 覆盖内容 |
|---|---|
| 微流程 | 标准 / 自定义微流程；MANUAL / BUSINESS_EVENT / SCHEDULE 三类触发 |
| Java 侧 | 实现接口、方法签名、出入参、DTO、Dao / Service / AppService、事件监听 |
| 平台能力 | 标品 AppService、Dubbo 代理、泛化调用、基础组件、注解、工具类 |
| 工程动作 | 拉码、提交、本地编译、构建、部署、接口测试、日志、K8s、清理 |
| 排错 | 构建报错、循环依赖、监听不触发、配置缺失、测试残留 |

### 1.2 不覆盖

- 别人如何从页面、菜单、外部系统调用我的流程；
- 页面搭建、菜单配置、前端组件细节；
- 平台内部实现原理，除非它决定“我写的东西会不会被调用”；
- 具体客户业务规则、组织权限方案和上线审批流程。

---

## 2. 知识分层：这一层决定“我能不能用那个东西”

### 2.1 修正后的 L0–L4

```text
L4  本应用生成物 / 本应用扩展代码
      本应用 Dao / Service / AppService / DTO / Event / Controller
      ↑ 可用；写入口优先 Service/AppService，直接 Dao 前先核写链

L3  其他业务应用（依赖坐标声明）
      依赖应用的 -facade / 明确允许的 -biz
      ↑ 只在 pom 已声明、classpath 能解析、包公开时可用；不能用传递依赖碰运气

L2  标品应用 / 基础应用
      org / bpm / affair / message / connector / file / enum / cache ...
      ↑ 只走 AppService + Dubbo 契约 + 明确扩展点；禁止拿内部实现类

L1  基础组件 Jar（应用内）
      file / enum / cache / 线程池 / 变量 / 函数 / mybatis / util
      ↑ 先确认工程已引入、类在 classpath、API 公开；不是“无条件直接使用”

L0  运行底座
      Spring / Nacos / 日志 / MQ / EventBus / K8s
      ↑ 受权限、环境和副作用约束；发消息、改配置、清数据必须有授权与回滚
```

### 2.2 每层判据

| 层 | 问什么 | 能用条件 | 不能怎么做 |
|---|---|---|---|
| L4 | 本应用生成物能不能调 | 包路径、类名、方法签名可从生成物或模板核实 | 不直接改 facade / biz / web / assemble 生成模块 |
| L3 | 别的业务应用能不能调 | `pom.xml` 已声明依赖，编译能过，且只依赖公开 facade | 不靠传递依赖、不注入对方内部 Service |
| L2 | 标品能力能不能调 | 有 AppService / Dubbo 契约 / 明确扩展点 | 不 new 内部类、不反射私有实现 |
| L1 | 基础组件能不能用 | 工程已有依赖、类是公开 API、行为已核或有兜底 | 不把“jar 里存在”当成“我能用” |
| L0 | 底座能力能不能动 | 有环境权限、知道写副作用、有回滚或幂等 | 不擅改 Nacos、不盲发 MQ、不随手清库 |

### 2.3 写进每篇开头

```text
L0 先看权限与副作用；L1 先看 classpath 与公开 API；
L2 只走开放面；L3 看依赖声明；
L4 本应用生成物优先 Service/AppService，直接 Dao 先核写链。
```

---

## 3. 先把“两类微流程”和“三类触发方式”分开

这是原稿最需要纠正的地方。`type` 和 `triggerType` 是两个正交维度。

### 3.1 type：标准还是自定义

| type | 含义 | 是否有节点 | Java 侧 |
|---|---|---|---|
| `SERVICE(0)` | 标准微流程 | 有节点链 | 不写实现；平台按节点生成 |
| `CUSTOM(3)` | 自定义微流程 | 无节点链，必须写 Java 实现 | 实现 `{App}CustomMicroFlowService` 等生成接口 |

所以“标准”不等于“MANUAL”。标准微流程也可以是事件监听、定时任务。

### 3.2 triggerType：怎么触发

| triggerType | 含义 | 出入口 | 设计态重点 |
|---|---|---|---|
| `MANUAL(2)` | 服务定义 | 有出入参，`paramType` 四值 | trigger / endNode 参数定义 |
| `BUSINESS_EVENT(0)` | 事件监听 | 自身无调用入参，只有 `messageInfo` 事件数据 | `messageSource` / `eventName` / `eventDataFullName` |
| `SCHEDULE(1)` | 定时任务 | 自身无出入参 | `jobCaption` / `jobCode` / `scheduleCronRule` |

### 3.3 六种组合与覆盖

| 组合 | 设计器叫法 | 是否覆盖 | Java 侧现状 |
|---|---|---|---|
| `SERVICE + MANUAL` | 服务定义 / 标准微流程 | 覆盖 | 画节点，不写实现 |
| `SERVICE + BUSINESS_EVENT` | 事件监听 / 标准微流程 | 覆盖 | 画节点，不写实现 |
| `SERVICE + SCHEDULE` | 定时任务 / 标准微流程 | 覆盖 | 画节点，不写实现 |
| `CUSTOM + MANUAL` | 自定义微流程 | 覆盖 | **已有模板级证据**：生成 `{App}CustomMicroFlowService` |
| `CUSTOM + BUSINESS_EVENT` | 自定义事件监听 | 覆盖，但需验证 | **Java 方法签名 / 骨架 / 运行调用 UNVERIFIED** |
| `CUSTOM + SCHEDULE` | 自定义定时任务 | 覆盖，但需验证 | **Java 方法签名 / 骨架 / 运行调用 UNVERIFIED** |

> 设计器/前端创建模型的唯一权威出处：
> `docs/audit/udc-semantics/MICROFLOW-BUSINESS-EVENT-TRIGGERS.md` §1。

`CUSTOM + BUSINESS_EVENT` / `CUSTOM + SCHEDULE` 在设计器创建模型里确实存在，但“平台会生成哪个 Java 接口、方法签名是否与 MANUAL 相同、运行时是否走同一 custom service 调用链”当前没有完整生成类或真实运行证据。方案必须把它们列为 P0 验证项，不能照 `CustomMicroFlowService.java.ftl` 直接推。

### 3.4 监听来源不是只有“应用内 / 应用间”

| messageSource | 含义 | 关键字段 |
|---|---|---|
| `EVENT` | 应用内实体事件 | `eventFullName`、`eventMfCustomDtoName` |
| `MESSAGE` | MQ / 跨应用消息 | `topic`、`eventDataFullName` |
| `CONNECTOR` | 连接器事件 | `connectorMessageInfo` |
| `MICRO_FLOW_EVENT` | 微流程事件 | 事件 DTO / 事件名 |

因此不要把“应用间监听”统称为“别的应用实体事件”。应用间通常是 `MESSAGE`，不是 `EVENT`。

### 3.5 写链事件监听不是自定义微流程

`@EventHandler` + `@EventSubscribe` 是**实体写链事件监听**，用于 `BeforeUpdateEvent<T>` 一类钩子。它和“自定义微流程 trigger=BUSINESS_EVENT”不是同一条路线。

---

## 4. 扩展路线决策矩阵

### 4.1 先选落地方式

| 需求形态 | 首选 | 次选 | 不该做 |
|---|---|---|---|
| 纯配置编排、节点能表达 | 标准微流程 | 子微流程拆分 | 为每个分支写 Java |
| 算法 / 外部系统 / 平台节点表达不了 | 自定义微流程 Java | 明确扩展点实现 | 硬塞进标准节点 |
| 拦平台行为、改元数据、导入导出 | 明确扩展点 | 自定义微流程调用 | 改生成模块源码 |
| 只给外部系统一个 HTTP 接口 | 自有 REST Controller | 自定义微流程 + 开放 | 为了一个 API 硬造微流程 |
| 监听实体写前 / 写后改数据 | `@EventHandler` / `@EventSubscribe` 或 Service 钩子 | 自定义微流程 | 改 `getOldInfo()` 后指望落库 |
| 跨进程调标品 | `DubboFactory.getProxy` | AppService 注入 | 手写 `@DubboReference` 绕过平台 |

### 4.2 选型后必须回答六个问题

```text
1. 触发是谁：人工、事件、定时、HTTP？
2. 入口是哪个接口：标准节点 / 自定义实现 / Controller？
3. 出入参是什么：paramType 四值、DTO 字段、分页与否？
4. 数据落在哪：本应用实体、外部 REST、MQ、缓存？
5. 失败怎么处理：事务、重试、幂等、死信、人工补偿？
6. 怎么验证：构建日志、运行日志、接口响应、库回读？
```

一个需求可能多点落地。例如“定时拉取外部数据并生成单据”：`SCHEDULE` 负责触发，`SUB_MICROFLOW` 负责传时间范围，业务子流程负责 `CALL_APP_SERVICE` + `CREATE_ENTITY`；外部协议复杂时再落一个自定义微流程或自有 REST。

---

## 5. 标准微流程怎么建：只讲我要做的事

### 5.1 服务定义 `SERVICE + MANUAL`

| 字段 | 说明 |
|---|---|
| `type` | `SERVICE` |
| `triggerType` | `MANUAL` |
| `serviceInterface` | 标准微流程不需要 |
| `trigger.output` / `endNode.input` | 入参，`paramType` 四值 |
| `endNode.output` | 出参 |

`paramType` 四值：

```text
NONE            无参数
BASIC           基本类型；标量入参用 9 键 desc
ENTITY_OBJECT   实体对象，配 entityObject
DEFAULT_OBJECT  自定义对象，配 defaultObject
```

判据：标量业务名放 `desc`；DTO 入参才用 `description` 12 键。读回时 `desc` / `description` 双兼容。

### 5.2 事件监听 `SERVICE + BUSINESS_EVENT`

```json
{
  "trigger": {
    "type": "BUSINESS_EVENT",
    "messageInfo": {
      "messageSource": "EVENT | MESSAGE | CONNECTOR | MICRO_FLOW_EVENT",
      "eventName": "<事件名>",
      "eventDataFullName": "<事件数据 DTO 全名>",
      "caption": "<标题>"
    },
    "expression": {}
  }
}
```

`EVENT` 额外要 `eventFullName` + `eventMfCustomDtoName`；`MESSAGE` 额外要 `topic`；`CONNECTOR` 额外要 `connectorMessageInfo`。

> 结构出处：`core/facts/udc/microflow/trigger-and-type-mapping.md`；
> 前端选择器与 LIVE 回读交叉证据：`docs/audit/udc-semantics/MICROFLOW-BUSINESS-EVENT-TRIGGERS.md`。

特别记住：`MESSAGE` 源若根 `input` 为空或缺 `javaType` / `name`，构建会在 `BusinessEventListener.java.ftl` 第 117 行左右抛 `InvalidReferenceException`。这是模板层真实坑，平台 `checkSchema` 兜不住。

### 5.3 定时任务 `SERVICE + SCHEDULE`

```json
{
  "trigger": {
    "type": "SCHEDULE",
    "jobCaption": "<任务名>",
    "jobCode": "<任务编码>",
    "scheduleCronRule": {
      "cronRules": [{
        "cycleType": "SIMPLE",
        "rotationType": "MINUTE",
        "startTime": "<毫秒时间戳字符串>",
        "endTime": null,
        "type": "FIRST",
        "value": "5"
      }]
    }
  }
}
```

“SCHEDULE 无出入参”只说明定时节点自身不声明参数。典型形态是定时触发 -> `SUB_MICROFLOW`，时间范围必须放在 `SUB_MICROFLOW.attrs` 里传给子流程；`attrs: []` 能保存、能发布，但运行会空参。

> 设计态结构出处：`core/facts/udc/microflow/schedule-structure.md`。

---

## 6. 自定义微流程怎么建、怎么写

### 6.1 `CUSTOM + MANUAL`：当前可落地的模板事实

平台生成 7 个类，只有一个是我写的：

| 类 | 谁写 | 作用 |
|---|---|---|
| `{App}CustomMicroFlowService` | 我实现 | 业务逻辑 |
| `{App}CustomMicroFlowAppService` | 平台生成 | 对外契约接口 |
| `Default{App}CustomMicroFlowAppServiceImpl` | 平台生成 | 调我的实现 |
| `CustomMicroFlow{Page}Controller` | 平台生成 | REST 入口 |
| `DefaultCustomMicroFlowConfig` | 平台生成 | Dubbo 导出 |
| `DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor` | 平台生成 | 我的实现生效后移除默认实现 |
| `MicroFlowDubboExportBeanPostProcessor` | 平台生成 | Dubbo 导出工具 |

接口形态（来自 `CustomMicroFlowService.java.ftl`）：

```java
package com.seeyon.{app}.custom.service.microflow;

public interface {App}CustomMicroFlowService {

    // 有分页：入参是整个 Request，没有 getData()
    default {OutDto} {flowName}({Req}<{InDto}> request) {
        throw new UnsupportedOperationException();
    }

    // 无分页：入参是裸 DTO
    default {OutDto} {flowName}({InDto} {inputName}) {
        throw new UnsupportedOperationException();
    }
}
```

三条硬规则：

```text
1. 方法名 = 微流程编码 name 首字母小写。
2. 生成方法带 default；不实现也能编译，运行时抛 UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED。
3. hasPagination=true -> Request<Dto>；false -> 裸 Dto；hasOutput=false -> void。
```

> 事实出处：`core/facts/platform-dev-system/01-custom-microflow-implement.md`、
> `core/facts/platform-dev-system/03-io-params-and-custom-object.md`。

平台如何找到我的实现：

```text
@Autowired(required = false) 注入 {App}CustomMicroFlowService
  -> 没有实现时字段为 null，平台抛 UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED
  -> 有实现时默认实现被 BeanDefinitionRegistryPostProcessor 移除
```

最小实现：

```java
package com.seeyon.zzprobe.custom.service.microflow;

import com.seeyon.zzprobe.api.OrderAppService;
import com.seeyon.zzprobe.domain.service.OrderService;
import com.seeyon.zzprobe.dto.OrderDto;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class OrderCustomMicroFlowServiceImpl implements OrderCustomMicroFlowService {

    @Autowired private OrderService orderService;
    @Autowired private OrderAppService orderAppService;

    @Override
    public OrderDto createOrder(OrderDto input) {
        orderService.create(input);
        SingleResponse<OrderDto> resp = orderAppService.selectById(
            SingleRequest.from(input.getId()));
        return resp.getData().getContent();
    }
}
```

### 6.2 `CUSTOM + BUSINESS_EVENT` / `CUSTOM + SCHEDULE`：先验证，不写死

当前只证实：

```text
- 设计器能创建 CUSTOM + BUSINESS_EVENT
- 设计器能创建 CUSTOM + SCHEDULE
- 事件监听模板 BusinessEventListener.java.ftl 存在
- 定时模板 MicroFlowSchedule.java.ftl 存在
```

**未证实：**

```text
- 自定义监听是否仍生成 {App}CustomMicroFlowService 方法
- 自定义监听的方法签名是否带 messageInfo / 事件 DTO
- 自定义定时是否生成不同接口或 schedule 类
- 运行时是否走同一 custom service 调用链
```

处理策略：先做 P0 真实验证，拿到生成产物和运行日志后再写成“可复制代码”。验证前只写设计态字段和 `UNVERIFIED` 占位，不给假 Java 签名。

验证单固定四步：

```text
1. 在设计器建 CUSTOM + BUSINESS_EVENT / CUSTOM + SCHEDULE 各一条。
2. 触发平台构建，拉后端生成工程，记录新增/变化的接口与类文件。
3. 部署后触发一次，拉运行日志、traceId、业务回读。
4. 把生成物、签名、日志和失败态写回对应事实格；仍缺证据的部分保留 UNVERIFIED。
```

### 6.3 自定义微流程验收闭环

```text
设计器建 MANUAL 自定义流程
  -> 拉取后端扩展工程
  -> 识别生成接口与签名
  -> 在 ext 内实现
  -> 本地 mvn compile
  -> 平台构建 / 部署
  -> 触发流程
  -> 看运行日志与业务回读
```

---

## 7. Dao / Service / AppService / DTO：谁负责什么

### 7.1 分层

```text
DTO          契约数据，字段名就是 REST / GraphQL / 微流程参数名
AppService   对外契约层，入参包 SingleRequest/ListRequest/PageRequest，有平台 AOP/事务/权限
Service      业务实现层，直接传 DTO；校验、规则、组合写这里
Dao          数据访问层，负责 SQL/Mapper；优先用平台 CRUD，不手搓 SQL
```

### 7.2 生成物包路径

```text
{appPackagePath}.api                 {E}AppService
{appPackagePath}.dto                 {E}Dto
{appPackagePath}.appservice          {E}AppServiceImpl
{appPackagePath}.domain.entity       {E}
{appPackagePath}.domain.service      {E}Service
{appPackagePath}.domain.dao          {appName}{E}Dao   ← 带应用名前缀
{appPackagePath}.domain.event        {E}Event
{appPackagePath}.controller          Abstract{E}Controller
```

### 7.3 什么时候用哪个

| 我要做的事 | 用 | 原因 |
|---|---|---|
| 本应用业务组合、批量、事务内逻辑 | `{E}Service` | 直接传 DTO，钩子在这里 |
| 对外契约 / 需要平台 AOP / 跨模块 | `{E}AppService` | Request 包装、权限、日志、事务 |
| 明确需要自定义 SQL / 平台 CRUD 覆盖不了 | `{E}Dao` 或自研 Mapper | 最后手段，先查平台 Dao |
| 参数结构 / 返回值 | DTO | 字段有 `@DtoAttribute` 元信息，别自造同义 DTO |

### 7.4 调用铁律

```java
// Service：直接传 DTO
OrderDto created = orderService.create(orderDto);

// AppService：必须包 Request，取值两层
SingleResponse<OrderDto> resp = orderAppService.create(SingleRequest.from(orderDto));
OrderDto data = resp.getData().getContent();

// 分页：PageRequest 没有 getData()
Map<String,Object> params = request.getParams();
PageInfo pageInfo = request.getPageInfo();
Sort sort = request.getSort();   // com.seeyon.boot.transport.Sort
```

---

## 8. 索引是主形态

### 8.1 三本索引

| 索引 | 回答什么 | 条目判据 |
|---|---|---|
| 可调用索引 | 我要做的事有没有现成接口 | 全名 + 方法签名 + 入参 DTO 字段 + 一行可复制代码 |
| 能力索引 | 文件/枚举/cache/线程池/变量/函数/mybatis/util 怎么用 | 全名 + 场景 + 一行代码 + 副作用 |
| 注解索引 | 这个注解贴哪、谁读、什么时候生效 | 全名 + @Target/@Retention + 一行示例 + 证据 |

每条必须至少包含：

```text
我要做什么 -> 去哪 -> 抓手（全名） -> 入参 DTO 字段 -> 一行可复制代码 -> 判据 / Evidence
```

给不出可复制代码或 DTO 字段的，只能是“目录”，不能叫索引。

### 8.2 可调用索引：三条通路

| 通路 | 适用 | 入口 | 关键约束 |
|---|---|---|---|
| Spring 注入 AppService | 编译期已知接口 | `@Autowired XxxAppService` | Request/Response 包装，取值两层 |
| Dubbo 代理 | 跨进程标品服务 | `DubboFactory.getProxy(Class[, group[, version[, timeout]]])` | 不手写 `@DubboReference` 绕过注册中心 |
| 泛化调用 | 只有接口名 / 动态模块 | `AppServiceProxy.invokeAppService(SingleRequest<AppServiceInvokeDto>)` | 本地 Spring BeanFactory 反射，不是 Dubbo |

泛化调用五值：

```java
AppServiceInvokeDto d = new AppServiceInvokeDto();
d.setInterfaceName("com.seeyon.bpm.api.common.BpmAppService");
d.setMethodName("send");
d.setParamType("com.seeyon.boot.transport.SingleRequest");
d.setGenericType("com.seeyon.bpm.dto.operation.openapi.BpmSendDto");
d.setParamJson("{\"templateCode\":\"xxx\",\"currentUserId\":123}");
d.setReturnJson(Boolean.TRUE);
SingleResponse<Object> r = appServiceProxy.invokeAppService(SingleRequest.from(d));
```

`AppServiceProxy` 四个入口按目标返回类型选：

```text
invokeAppService             单对象
invokeAppServiceForList      列表
invokeAppServiceForPage      分页
reliableInvokeAppService     可靠送达 + 回调
```

### 8.3 基础能力索引：六件

| 能力 | 抓手 | 典型用途 | 证据 |
|---|---|---|---|
| 文件 | `com.seeyon.boot.starter.file.FileService` | 附件、临时文件、构建日志下载 | 类已确认；方法/入参待逐条落格 |
| 枚举 | UDC 枚举 / 选项集 AppService + 枚举常量 | 选项读写、枚举翻译 | 已有 setting 域事实 |
| cache | `com.seeyon.boot.util.cache.SeeyonCache` + cache starter | 本地缓存、去重、短期状态 | `boot-core` 字节码；语义待测 |
| 线程池 | `boot-starter-threadpool` 的公开 executor API | 异步任务、回调、批处理 | 构件存在；公开入口待查 |
| 系统变量 / 函数 | `com.seeyon.boot.starter.systemvariable.util.SystemVariableUtils` | 当前用户、日期、上下文 | `boot-starter-systemvariable` |
| MyBatis | `AllInOneBaseDao` / Mapper | CRUD、条件查询、分页 | `dao-and-mybatis.md` |

“基础组件”不能只写六个名词。每件至少给：类全名、依赖坐标、一次真实调用、失败形态。

这里有一个必须诚实的分界：模块 README 只证明“构件有 N 类/M 方法”，不证明“这 M 个方法都该由业务代码调”。把公开入口写成索引前，必须逐个核接口面、入参和副作用。

### 8.4 注解索引

先记最常用组合：

```java
// 暴露 AppService
@AppService(value = "OrderAppService", description = "订单契约")

// 暴露单个操作到 OpenAPI
@AppServiceOperation(
    value = "创建订单",
    openApi = @OpenApi(isOpenApi = true, url = "/order/create")
)

// 实体元数据 / 字段说明
@EntityInfo(value = "订单", entityType = EntityType.BILL)
@DtoAttribute(value = "订单号", description = "业务唯一号")

// 安全：加密 / 脱敏 / 审计
@Safety(encryption = EncryptionEnum.NONE, auditLog = true)
@Maskable(type = MaskType.MOBILE, start = 3, end = 7)
```

查三件事：

```text
1. @Target：能不能贴在这个位置
2. 元注解：是否自带 @Service/@Component，贴了就会被 Spring 扫到
3. 消费方：平台在启动时、请求时还是导出时读取
```

### 8.5 Utils 索引：不要重复造轮子

| 场景 | 首选 | 一行示例 |
|---|---|---|
| JSON | `com.seeyon.boot.util.JsonUtils` | `String s = JsonUtils.toJsonNotIncludeNull(dto);` |
| JSON 转 Map | 同上 | `Map<String,Object> m = JsonUtils.toMap(s);` |
| 日期 | `com.seeyon.boot.util.DateUtils` | `String d = DateUtils.format(new Date(), "yyyy-MM-dd");` |
| 字符串 / 脱敏 | `com.seeyon.boot.util.StringUtils` | `String m = StringUtils.mask("13812345678", 3, 4);` |
| ID | `com.seeyon.boot.util.id.IdentifierGenerator` | `Long id = identifierGenerator.generateLong();` |
| UDC JSON | `com.seeyon.boot.starter.udcrt.util.UdcJsonUtils` | `String s = UdcJsonUtils.toJson(dto);` |
| 反射 | `com.seeyon.boot.starter.udcrt.util.UdcReflectUtil` | `Object v = UdcReflectUtil.getFieldValue(dto, "name");` |
| 当前用户 | `com.seeyon.boot.starter.systemvariable.util.SystemVariableUtils` | `Long uid = SystemVariableUtils.currentUserId();` |
| 运行日志 | `com.seeyon.boot.starter.udcrt.util.UdcAppLogHelper` | `UdcAppLogHelper.buildEndLog(result, traceId);` |

最终索引必须逐条核对方法真实重载与参数顺序；上表只给首选抓手，不作为最终可复制索引成品。

D8 的“导出 / HTTP / 加密”先落已确认类，不硬编示例：

```text
Excel       com.seeyon.boot.starter.excel.*（构件存在，导出模板/服务类待逐条筛公开入口）
HTTP        com.seeyon.boot.util.http.HttpClientUtil（类存在，重载待核）
加密/脱敏   @Safety / @Maskable + boot-spi EntityEncryption / SensitiveSpi（优先走 SPI，不在业务硬编码）
```

---

## 9. 工程动作：拉码、提交、编译、构建、部署

### 9.1 先探工程形态

```text
backend/
  pom.xml
    -> 有 <modules>     = 五模块生成工程
    -> 无 <modules>     = 单模块客开工程
```

五模块形态：

```text
<app>-facade/
<app>-biz/
<app>-web/
<app>-ext/         ← 唯一可写
<app>-assemble/
```

单模块形态：

```text
backend/
  src/main/java/com/seeyon/<app>/extend/   ← 客开代码
```

### 9.1.1 拉取与提交代码

```bash
# 从 Nacos repo.gitlab 推出 git-base 后
git clone <git-base>/backend/<appName>.git
cd <appName>
git checkout -b feature/<task>

# 只提交客开代码与必要配置
git add <changed-files>
git commit -m "feat: <task>"
git push origin feature/<task>
```

提交前必须核对：

```text
1. 没有改 facade/biz/web/assemble 生成模块。
2. 没有提交本地调试配置、cookie、token、真实密钥。
3. 没有把测试数据文件、临时脚本塞进业务目录。
4. diff 只含本次任务相关文件。
```

铁律：

```text
五模块工程只写 -ext；facade/biz/web/assemble 下一次构建会被整包覆盖。
单模块工程写 extend/；不要把生成物当长期手写代码。
```

### 9.2 Git 地址

路径规则固定：

```text
<git-base>/backend/<appName>.git
<git-base>/frontend/<appName>.git
```

`<git-base>` 不是常量，来自 Nacos `repo.gitlab`：

```yaml
repo:
  gitlab:
    apiUrl: <gitlab 地址>
    parentExtendGroupPath: <客开组>
    parentGroupPath: <标品组>
```

推导：

```text
客开工程 git-base = {apiUrl}/{parentExtendGroupPath}
标品工程 git-base = {apiUrl}/{parentGroupPath}
```

没有配置、没有已有 clone 反推 -> 报“需要 git-base”，不要猜域名。

### 9.3 本地编译

```bash
cd backend
mvn -q -DskipTests compile
```

判据：

```text
编译失败 -> 先修本地类型 / 依赖 / 签名，不要带病构建
编译成功 -> 再走平台构建
```

本地编译只证明“代码和 classpath 对”，不证明平台生成链路能通过；平台构建还会重生成 facade/biz/web。

> 工程形态出处：`core/facts/standard-product/code-repo-and-targets.md`、
> `core/facts/standard-product/extension-project-skeleton.md`。

### 9.4 平台构建与部署

```http
POST /service/udc/runtime/deploy-normal
Content-Type: application/json

{
  "deployDto": {
    "appId": "<APP_ID>",
    "deployType": "RELEASE",
    "projectType": "ALL",
    "terminalType": "ALL"
  }
}
```

关键点：

```text
1. 必须包 deployDto；平铺 body 会拿到 null。
2. deployType ∈ TEST / RELEASE / ON_ONLINE / DELTA。
3. 返回 deployId 只表示“任务已受理”，不表示构建成功。
```

前端真实轮询链（设计器“测试”同款）：

```text
POST /service/udc/graphql?udcRuntimeDeployNormalPost
  body: { "variables": { "params0": { "deployDto": {...} } } }

POST /service/udc/graphql?udcSandboxBuildInfoAppGet
  body: { "variables": { "params0": { "appId": "<appId>" } } }
  约每 6s 一次，直到 state=SUCCESS/FAIL
  返回: state, progress, buildVersion, buildTime, totalTime, logs[]
```

后端 REST 只读探测：

```http
GET /service/udc/sandbox/build-info/{appId}
GET /service/udc/sandbox/delta-build-info/{appId}
```

详细日志：

```text
GET /service/udc/file/download?storageKey=compile-info/{appId}/{yyyymmddhhMMss}/backBuild.log
```

> 构建/部署出处：`core/facts/deploy/build-chain.md`、
> `core/facts/udc/write-chain/sandbox-build-deploy-chain.md`、
> `docs/operation-contracts/udc/application/udc-app-inner-readonly-2026-10-22.md`。

### 9.5 部署历史与版本

```text
查询面：POST /service/udc/application/appVersion/{appGuid}
运行态：Redis + sandbox + K8s Deployment
```

不要把“appVersion 查得到”当成“服务已经运行”。运行证据要看：

```text
sandbox 状态
deployment / pod 状态
微流程运行日志
业务接口回读
```

---

## 10. Controller 与接口测试

### 10.1 什么时候需要自建 Controller

平台 `@AppService` 不是 HTTP 暴露机制，`@AppServiceOperation` 的方法不会自动变成 REST 端点。

准入：

```text
- 对方只要 HTTP / REST，不需要微流程
- 需要明确的自定义路径、请求体、响应格式
- 接口有鉴权、限流、幂等、审计要求
```

### 10.2 暴露机制

```text
Spring: @RestController + @RequestMapping + @PostMapping/@GetMapping
元数据: 类级 @RestApi + 方法级 @RestApiOperation 才进 op/GraphQL 面
```

只写 `@RestController` 能注册 Spring 路由，但不会自动进平台 GraphQL op 面。

### 10.3 最小 Controller

```java
package com.seeyon.zzprobe.extend.web;

import com.seeyon.zzprobe.api.OrderAppService;
import com.seeyon.zzprobe.dto.OrderDto;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("ext/order")
public class OrderExtController {

    private final OrderAppService orderAppService;

    public OrderExtController(OrderAppService orderAppService) {
        this.orderAppService = orderAppService;
    }

    @PostMapping("select-by-id")
    public SingleResponse<OrderDto> selectById(@RequestBody Long id) {
        return orderAppService.selectById(SingleRequest.from(id));
    }
}
```

实际包名前缀和网关路由需按工程规则核对；Controller 不能写在会被构建覆盖的生成模块里。

> 暴露机制出处：`docs/audit/udc-semantics/REST-EXPOSURE-MECHANISM.md`。

### 10.4 接口测试清单

```text
1. 路由：类级 + 方法级映射，是否带网关 / 应用前缀。
2. 鉴权：session cookie / token / 角色注解。
3. 请求体：包装形态、JSON 字段名、Long 精度、日期格式。
4. 成功：code=BOOT_0000 或预期信封；data.content 非空。
5. 失败：缺字段、错类型、无权限、业务异常。
6. 副作用：库回读或下游日志。
7. 清理：删除测试数据或明确标记。
```

请求形态示例：

```http
POST {gateway_base}/service/{appName}/ext/order/select-by-id
Content-Type: application/json

123456789012345
```

平台 REST 常见信封是 `SingleResponse<T>`：`status` / `code` / `data.content`；GraphQL 结果在 alias 下。以实际接口为准，不套错判据。

### 10.4.1 接口测试请求怎么取

```text
1. 从 Controller 类级 + 方法级注解拼出真实路径。
2. 从网关 / 应用入口补 service 前缀，不猜完整域名。
3. 从方法签名确定是 @RequestBody、@PathVariable 还是表单。
4. 从 DTO 的 @DtoAttribute 读字段名、示例、说明。
5. 用最小请求先打通路由，再补业务字段。
6. 保存 curl、响应码、响应体、traceId、库回读。
```

### 10.5 什么时候不走微流程

直接用自有 REST 的条件：

```text
- 不需要画布编排；
- 请求/响应契约属于外部系统；
- 延迟、重试、幂等要直接控制；
- 把流程包一层只会增加调用链。
```

仍应使用微流程的条件：

```text
- 需要编排、规则、事件触发或设计器复用；
- 需要被页面规则、子流程、定时任务组合；
- 需要平台运行日志与画布回读。
```

### 10.6 自有 REST 的测试与清理

```text
1. 使用专用测试应用或测试租户。
2. 先测幂等查询，再做一次带唯一标记的创建。
3. 断言响应码，并按唯一标记回读数据库。
4. 通过批准过的 API 或清理脚本删除测试数据。
5. 把 curl 和结果写入 evidence，而不是只写“测过了”。
```

---

## 11. Nacos、日志、K8s 与构建进度

### 11.1 Nacos

取值顺序：

```text
1. 已有 Nacos 配置（只读，值脱敏）
2. 已有 clone 的 remote URL 反推
3. 用户显式给出的环境参数
4. 缺失 -> 停下要 git-base / namespace / dataId，不猜
```

相关键：

```text
repo.gitlab.apiUrl
repo.gitlab.parentExtendGroupPath
repo.gitlab.parentGroupPath
seeyon.sandbox.repositoryPath
seeyon.sandbox.udcYamlConfigDataId
seeyon.sandbox.ciCdTaskTimeOut
seeyon.sandbox.deployTimeOut
```

应用 YAML 先取 `{appName}-yaml`，空则回落 `udc-app-yaml`。

缺配置时的动作：

```text
1. 先判断业务是否真的需要这个键。
2. 需要就产出明确的 key/value 方案。
3. 由用户或环境负责人授权写入。
4. 写入后回读验证。
5. 不把密钥写进文档和日志。
```

### 11.2 日志

| 日志 | 位置 | 用途 |
|---|---|---|
| 构建进度 | `udcSandboxBuildInfo` 的 `state/progress/logs` | 看构建卡在哪一步 |
| Maven 详细日志 | `compile-info/{appId}/{timestamp}/backBuild.log` | javac 报错、依赖失败 |
| 微流程运行日志 | `/service/{appName}/udc-runtime/app-log/search/microflow` | 看 flow 是否执行、入参、异常 |
| 设计日志 | `/service/udc/graphql?udcOperationLogSearch` | 看元数据变更和操作记录 |
| Pod 日志 | `kubectl logs` / `kubectl exec` | 看启动、运行时异常、GC、连接池 |

微流程日志请求体：

```json
{
  "params": {"appName": "<appName>", "appId": "<appId>", "logType": "MICRO_FLOW"},
  "pageInfo": {"pageNumber": 1, "pageSize": 10, "needTotal": true, "total": 0}
}
```

判据：`success=true` 才算运行成功，HTTP 200 / `BOOT_0000` 不是充分条件。

> 日志出处：`core/facts/udc/application/applog-family.md`、
> `core/facts/udc/microflow/runtime-log.md`、`core/facts/udc/application/app-inner-pages.md`。

### 11.3 K8s

```bash
kubectl --kubeconfig <config> -n <namespace> get pods
kubectl --kubeconfig <config> -n <namespace> logs <pod> --tail=200
kubectl --kubeconfig <config> -n <namespace> logs <pod> -f
kubectl --kubeconfig <config> -n <namespace> describe pod <pod>
```

看四层：

```text
1. Deployment/Pod Ready？
2. 启动日志是否加载到应用？
3. 环境变量 / Nacos dataId / namespace 是否对？
4. 构建出的 image tag 是否是本次版本？
```

不要把“Pod Running”当成“业务可用”。还要看接口和微流程日志。

> K8s 执行链出处：`core/facts/udc/write-chain/sandbox-build-deploy-chain.md`、
> `core/facts/modules/01-platform/boot-starter-k8s/README.md`。

### 11.4 构建进度接口的轮询规则

```text
1. 发起构建，拿 deployId / appId。
2. 每 5-10s 查 build-info；不要 1s 刷。
3. state=BUILDING 继续；SUCCESS 停止；FAIL 停止并拉日志。
4. progress 只作参考，不以 100% 单独判成功。
5. 超时按 seeyon.sandbox.ciCdTaskTimeOut / deployTimeOut 判。
6. 页面真实轮询是 `udcSandboxBuildInfoAppGet`，约 6s 一次。
```

---

## 12. MQ、EventBus 与事件监听

### 12.1 三条不同路线

| 路线 | 用途 | 入口 | 事务/重试 |
|---|---|---|---|
| EventBus | 应用内事件，进程内 | `PublishBusinessEvent` 节点 / `@EventHandler` | 节点在事务提交后投递；无订阅者无痕 |
| MQ | 跨应用/异步消息 | `AMONG_APP` `selectMq` + topic | 跨进程，需自己处理幂等与重试 |
| 写链事件 | 实体写前/写后钩子 | `@EventHandler` + `@EventSubscribe` | 改 `getInfo()` 在写库前生效 |

### 12.2 发 EventBus

```json
{
  "actionType": "PUBLISH_BUSINESS_EVENT",
  "eventType": "IN_APP",
  "selectEvent": {"type": "<event DTO full name>"},
  "mappingType": "attrs"
}
```

事实：`IN_APP` 走进程内 EventBus，不写 `ctp_mq`；事务提交成功后投递。没有订阅者时投递成功也看不到任何记录。

> 出处：`core/facts/udc/microflow/node-publish-event.md`。

### 12.3 发 MQ

```json
{
  "actionType": "PUBLISH_BUSINESS_EVENT",
  "eventType": "AMONG_APP",
  "selectMq": {
    "key": "UDC_<APPNAME>_MQ.<dto>",
    "topic": "UDC_<APPNAME>_MQ",
    "contentDto": {"type": "<dto full name>"}
  }
}
```

跨应用 MQ 形态当前证据等级较低：结构可构造，运行投递与消费闭环尚未完整验证。正式落地前必须做发送 -> 消费 -> 日志 -> 库回读四步。

> MQ 结构出处：`core/facts/udc/microflow/three-nodes-live-evidence.md`；
> 应用间投递/消费闭环：`UNVERIFIED`。

### 12.4 写链监听

```java
@EventHandler
public class OrderAuditListener {

    @EventSubscribe
    public void onBeforeUpdate(BeforeUpdateEvent<OrderDto> event) {
        OrderDto current = event.getInfo();
        current.setAuditFlag("Y");
    }
}
```

铁律：

```text
1. 类上 @EventHandler、方法上 @EventSubscribe，缺一不可。
2. @EventSubscribe 没有 value，订阅靠方法参数类型。
3. 不要用 Object 作参数，否则收所有事件。
4. 改 getInfo() 生效；改 getOldInfo() 不落库。
5. 不要改完再调 update，可能二次写和死循环。
6. 单条和批量事件都会发，两个都挂会执行两次，选一个。
```

> 写链监听出处：`core/facts/platform-dev-system/06-beforeupdate-listener-code.md`。

---

## 13. 自建实体与建表

### 13.1 实体创建链路

```http
POST /service/udc/entity
Content-Type: application/json

{
  "appId": "<APP_ID>",
  "name": "Order",
  "caption": "订单",
  "stereotype": "bill",
  "entityNature": "MAIN",
  "features": "basic,approve,organization,billBasic,termination,suspend,nullify",
  "multiplicity": "ONE2MANY",
  "category": "ENTITY",
  "parentEntityId": "0",
  "superior": "0",
  "validate": true
}
```

必填：`appId`、`name`、`entityNature`、`stereotype`。缺失会报 `UDC_ENTITY_0010` / `BOOT_1001`。

### 13.2 实体属性

```text
1. 字段走 udcDataTransferObjectUpdateDtoPost（自定义对象），实体属性走实体属性接口。
2. attributes 通常是全量替换语义，先读后写。
3. 字段名、类型、长度、是否必填、索引都要在设计态定清楚。
4. 平台不用 javax.validation；必填只能从描述或实测判断。
```

### 13.3 建表发生在构建时

```text
建实体本身不直接落物理表
  -> RELEASE 构建触发 DDL
  -> 物理表落应用自己的库 {app}_{env}
  -> 不是 udc_xxx 元数据库
```

实证：test2 单据实体表落 `{app}_test2`，带业务列和单据系统列。

### 13.4 什么时候允许自建表

```text
允许：
- 平台实体承载不了的中间表、日志表、外部同步表；
- 需要明确索引和批处理；
- 有清理策略和容量评估。

不允许：
- 绕过平台实体写链去直写业务表；
- 重复建平台已有字段；
- 没有租户/应用隔离的表；
- 没有迁移和回滚的表。
```

### 13.5 索引与约束

```text
- 唯一键：业务编码、外部系统唯一 ID；
- 普通索引：查询条件、状态 + 时间；
- 联合索引：应用 ID + 状态 + 创建时间；
- 外键：平台通常不用数据库外键，靠实体和代码约束；
- 所有索引必须有对应查询场景，不为“以后可能”乱加。
```

> 实体创建与建表出处：`core/facts/udc/entity/create.md`；
> 字段语义与写面：`core/facts/udc/entity/attribute-create.md`、
> `core/facts/udc/setting/custom-object/create.md`。

---

## 14. 构建报错、循环依赖、清理

### 14.1 构建报错拉取顺序

```text
1. 发起 deploy-normal，拿 deployId / appId。
2. 查 build-info 的 state / progress / logs。
3. FAIL 后拉 backBuild.log，定位 javac / maven / 依赖错误。
4. 区分：生成代码错误 / 手写代码错误 / 依赖缺失 / 一致性检测失败。
5. 修完先本地 compile，再重新构建。
```

常见映射：

| 现象 | 根因 | 修法 |
|---|---|---|
| 找不到符号 `getName()` on `List<Dto>` | DATA_MAPPING 单对象/列表形态错 | 改 `selectParam.type=ARRAY` 或加承接节点 |
| 循环依赖 / bean 初始化失败 | ext 注入链成环 | 构造函数改 setter / 延迟依赖 / 拆服务 |
| `InvalidReferenceException` at BusinessEventListener 117 | MESSAGE 根 input 为空或缺 javaType/name | 补 trigger.input |
| 一致性检测未通过 | 页面/实体/微流程引用悬空 | 先修检测明细，构建不会越过 |
| 找不到类 | 依赖未声明或 scope 错 | 补 pom / 核对 classpath |
| 生成物覆盖手写 | 写到了 facade/biz/web/assemble | 迁到 ext |

### 14.2 循环依赖定位

```text
1. 看启动日志的 BeanCurrentlyInCreationException / circular reference。
2. 顺着 bean 名找 A -> B -> C -> A。
3. 优先删业务循环：抽共同依赖、抽接口、下沉共享服务。
4. 仍不能删再延迟注入：@Lazy / setter / ObjectProvider。
5. 不用 @Lazy 掩盖真正的领域循环。
```

### 14.3 清理脚本

清理范围：

```text
- 测试创建的业务数据（按唯一标记）；
- 临时实体/页面/微流程；
- 构建失败留下的临时脚本；
- 本地 test fixture 临时文件；
- 缓存/静态单例；
- 测试生成的 MQ / EventBus 订阅。
```

脚本要求：

```text
1. 先 dry-run，打印将删的 id / 表和数量。
2. 只删本次任务创建的对象，不按时间范围全删。
3. 每步有回读确认。
4. 失败可重试，不重复删。
5. 清理结果写 evidence。
```

---

## 15. 16 篇呈现 + 1 个合并主题

### 15.1 P0：先证明未知契约（不计入 17 篇，但必须先做）

| # | 缺口 | 为什么先做 |
|---|---|---|
| V1 | `CUSTOM + BUSINESS_EVENT` Java 生成物与运行调用 | 当前不能给可复制代码 |
| V2 | `CUSTOM + SCHEDULE` Java 生成物与运行调用 | 同上 |
| V3 | 沙箱构建轮询精确接口契约 | 页面抓包已有一部分，需补 API 与失败态 |
| V4 | 生成物完整渲染样本 | `{E}Service` 头部、Dao、Controller 仍缺完整 LIVE |

### 15.2 P1：能建能跑

| # | 文章 | 输出 |
|---|---|---|
| D1 | 三类怎么建 | 设计态字段 + Java 接口对照 + 监听应用内/间 |
| D2 | Dao / Service / AppService 区别 | 谁负责什么 + 选择表 + 错误用法 |
| D3 | 拉码 -> 编译 -> 构建 -> 部署 | 工程形态 + Git 地址 + 命令 |
| D15 | Nacos / 日志 / K8s / 构建进度 | 配置来源 + 日志路径 + 轮询 |
| D4 | Controller 与接口测试 | 怎么写 + 测什么 + 请求怎么构造 |

### 15.3 P2：能查能调

| # | 文章 | 输出 |
|---|---|---|
| D5 | 标品开放面索引 | Dubbo 契约 + 泛化五值 + DTO |
| D6 | 基础组件六件 | file / enum / cache / 线程池 / 变量 / 函数 |
| D7 | 注解索引 | Target / Retention / 消费方 |
| D8 | Utils 索引 | JSON / 导出 / 日期 / ID / 加密 / HTTP |
| D14 | 直接给人 REST 接口 | 什么时候写、怎么写、怎么测 |
| D16 | 业务 -> 选哪个微流程 | 一需求多点落地 |

### 15.4 P3：能排能收

| # | 文章 | 输出 |
|---|---|---|
| D9 | MQ / EventBus | 发送、接收、事务后发、重试语义 |
| D10 | 自建实体 / 建表 | 允许条件、落库、索引 |
| D11 | 构建报错通过接口拉 | 接口、结构、常见错误 -> 修法 |
| D12 | 循环依赖 | 定位、四类修法 |
| D13 | 收尾清理 test 脚本 | 删什么、别留脏数据 |
> D17 不单独成篇，内容固定放在 D16 的「一次需求多点落地」小节；这样总共仍是原编号 D1-D17。

---

## 16. 执行顺序

```text
P0  验证未知契约（CUSTOM 监听/定时、轮询、完整生成物）
P1  能建能跑：D1 -> D2 -> D3 -> D15 -> D4；每篇完成即跑该篇验收
P2  能查能调：D5 -> D6 -> D7 -> D8 -> D14 -> D16
P3  能排能收：D9 -> D10 -> D11 -> D12 -> D13
```

每篇不是“写完就算”，必须按下面顺序收口：

```text
写正文
  -> 代码块用真实 jar / 真实工程编译一次
  -> 涉及接口的用真实请求调一次
  -> 涉及构建的跑一次构建并回读状态
  -> 涉及运行的看日志并回读业务
  -> 记录 evidence 与证据等级
  -> 未验证项保留 UNVERIFIED，不伪装完成
```

每一篇固定模板：

```text
1. Capability：一句话，我要做什么。
2. 前置条件：工程形态、依赖、权限、环境。
3. 操作步骤：设计态 / 代码 / 构建 / 部署 / 测试，分步编号。
4. 可复制代码：真实全名、真实字段、真实签名；没有就标 UNVERIFIED。
5. 判据：成功返回、日志、库回读、页面/接口表现。
6. Evidence：文件路径 / 命令 / 时间 / 证据等级。
7. Verified：LIVE / VERIFIED_STATIC_BYTECODE / STATIC_RULE / UNVERIFIED。
```

---

## 17. 验收：每批真跑

### 17.1 P0 验收

```text
1. 在测试应用各建一个 CUSTOM + BUSINESS_EVENT 和 CUSTOM + SCHEDULE。
2. 构建并拉生成物，确认接口名、方法名、签名。
3. 部署并真实触发，确认运行日志和业务回读。
4. 把结果写回 D1，未验证前不得给代码模板。
```

### 17.2 P1 验收

```text
在测试应用建 MANUAL 自定义流程
  -> 拉代码
  -> 实现接口
  -> 本地 mvn compile
  -> deploy-normal
  -> build-info 到 SUCCESS
  -> 触发
  -> 运行日志 success=true
  -> 库/接口回读
```

### 17.3 P2 验收

```text
从索引挑 5 个接口，不看源码直接调通：
- 至少 1 个 Spring 注入 AppService
- 至少 1 个 DubboFactory 代理
- 至少 1 个泛化 AppServiceProxy
- 至少 1 个工具类/基础组件
- 至少 1 个自有 REST Controller
```

### 17.4 P3 验收

```text
故意造一个循环依赖 + 一个构建报错
  -> 按 D11/D12 定位修好
  -> 跑清理脚本 dry-run
  -> 真清理
  -> 回读确认无残留
```

---

## 18. 现有资产复用

| 已有资产 | 覆盖 | 用法 |
|---|---|---|
| `platform-dev-system/` 6 格 | 自定义微流程实现 / 生成物 / 出入参 / 方法 / 平台能力 / beforeUpdate | 写代码主入口 |
| `standard-product/` 32 篇 | 开放面、DTO、Dubbo、泛化、Dao、注解、枚举、工具、扩展点 | 查抓手 |
| `udc/microflow/` 66 篇 | 建、节点、触发、表达式、数据流 | 设计态 |
| `udc/write-chain/` 39 篇 | 实体写链、构建部署链 | 写链与部署 |
| `docs/audit/artifacts/` | jar 签名、方法表、DTO 字段、service flow | 证据底账，不进 Agent 默认路由 |
| `modules/` | 平台模块清单 | L2 底账，查证用 |

原则：

```text
不重写已有事实格；新文章引用它们并补缺口。
证据件只用于查证和重跑，不复制成第二份事实。
Agent 默认路由 = platform-dev-system + standard-product + 本方案 17 篇。
```

---

## 19. 风险与阻塞

| 风险 | 影响 | 处理 |
|---|---|---|
| CUSTOM 监听/定时 Java 契约未证 | 不能写代码模板 | P0 真实验证 |
| 完整生成物未 LIVE | 包路径/签名可能错 | 拉真实生成工程核验 |
| 构建轮询前端契约未完全等价 REST | 实现可能错 | 同时保留 GraphQL 页面契约 + REST 探测 |
| K8s 权限不足 | 看不了 Pod 日志 | 由环境负责人提供只读访问 |
| 索引字段过多 | 维护成本 | 按域分批，每条带证据 |
| 旧 modules 口径漂移 | 误用过期模块 | 只作底账，不作默认索引 |

---

## 20. 首个可执行任务

从 D1 开始，先落“已证实部分”：

```text
1. 写 MANUAL 自定义微流程：create/update/checkSchema + 生成接口 + Java 实现 + 调用。
2. 写 SERVICE + BUSINESS_EVENT：EVENT / MESSAGE 的 messageInfo 与构建坑。
3. 写 SERVICE + SCHEDULE：trigger + SUB_MICROFLOW.attrs。
4. 单独列 CUSTOM + BUSINESS_EVENT / CUSTOM + SCHEDULE 的 UNVERIFIED 验证单。
5. 用测试应用真建一个 MANUAL 自定义流程，走构建 -> 部署 -> 触发 -> 日志 -> 回读。
```

完成标准：

```text
- 每段有仓库路径证据；
- 每个代码块能编译；
- 每个接口测试有请求和响应；
- 未验证内容全部标 UNVERIFIED；
- 不把“平台能保存”写成“运行已通过”。
```

---

## 21. 证据索引

本方案不复制事实正文，只引用以下底账。Agent 干活前先读事实格，证据件只在需要核签名/字段/重跑时打开。

### 21.1 微流程与 Java 契约

```text
core/facts/udc/microflow/trigger-and-type-mapping.md
core/facts/udc/microflow/event-listener-structure.md
core/facts/udc/microflow/schedule-structure.md
core/facts/udc/microflow/node-publish-event.md
core/facts/platform-dev-system/01-custom-microflow-implement.md
core/facts/platform-dev-system/03-io-params-and-custom-object.md
core/facts/platform-dev-system/04-generated-service-methods.md
core/facts/platform-dev-system/06-beforeupdate-listener-code.md
docs/audit/udc-semantics/MICROFLOW-BUSINESS-EVENT-TRIGGERS.md
```

### 21.2 平台能力与调用

```text
core/facts/standard-product/appservice-invocation.md
core/facts/standard-product/dubbo-cross-service.md
core/facts/standard-product/dao-and-mybatis.md
core/facts/standard-product/platform-annotations.md
core/facts/standard-product/boot-core-utils-and-annotations.md
core/facts/standard-product/api-usage-cards.md
core/facts/standard-product/code-repo-and-targets.md
core/facts/standard-product/extension-project-skeleton.md
```

### 21.3 构建、部署、日志

```text
core/facts/deploy/build-chain.md
core/facts/udc/write-chain/sandbox-build-deploy-chain.md
core/facts/udc/microflow/test-build-chain.md
core/facts/udc/application/applog-family.md
core/facts/udc/microflow/runtime-log.md
docs/operation-contracts/udc/application/udc-app-inner-readonly-2026-10-22.md
docs/audit/udc-semantics/REST-EXPOSURE-MECHANISM.md
```

### 21.4 实体与设置

```text
core/facts/udc/entity/create.md
core/facts/udc/entity/attribute-create.md
core/facts/udc/entity/entity-update-payload.md
core/facts/udc/setting/custom-object/create.md
```

### 21.5 证据等级

| 等级 | 含义 | 能写到什么程度 |
|---|---|---|
| `LIVE` | 真环境真实请求/运行 | 可写“已验证” |
| `VERIFIED_STATIC_BYTECODE` | javap/cfr 逐类逐方法核对 | 可写签名和属性，不写运行行为 |
| `STATIC_RULE` | 模板/生成器原文规则 | 可写生成规则，运行前仍需构建 |
| `UNVERIFIED` | 未跑或证据不足 | 只能写验证单，不写可复制成品 |

Agent 交付前必须能回答：

```text
这条结论来自哪个文件？
等级是什么？
有没有真实构建或运行证据？
如果没有，下一步怎么验证？
```
