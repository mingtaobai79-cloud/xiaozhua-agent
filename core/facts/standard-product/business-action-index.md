# 业务动作索引：要做什么 → 调哪个方法

## 1. Capability

写扩展时第一个问题永远是「**我要做的这件事，平台有现成方法吗？叫啥？传什么？**」。

2258 个 AppService 方法散在 91 个构件、11 个域里，靠翻签名表找等于大海捞针。
本格按**业务动作**（创建/修改/删除/流程/发布/导入导出/校验/查询）归类，
一行给全：动作方法 → 接口 → 入参 DTO → 实现类 → 流转第一步。

## 2. Version

同 `BASELINE.md`。

## 3. Input

```
interfaces.json           → 322 个 AppService / 2258 个方法 / 入参 DTO / 实现类
service-flow-20261103/    → 实现类方法体的调用链（反编译）
```

## 4. Required

无（查表）。

## 5. Execution

```
① 我要做某件事 → action-index.md 找对应动作分组
② 找到入口方法 → 记下接口名 + 入参 DTO
③ DTO 有什么字段 → dto-fields/<域>.md
④ 背后发生什么 → service-flow-20261103/<构件>.md 搜那个实现类
⑤ 完整签名 → packages/<构件>.md 或 domains/<域>.md
```

## 6. Side Effects

无。但注意：表里「流转（第一步）」只给**第一步**调用，不是完整链路。
写扩展前要看 flow 文件的完整那一节，否则会漏掉事件发布、多线程、配置开关这些副作用。

## 7. Known Constraints

### 7.1 覆盖现实（先看这个，别指望全部能追）

| 项 | 数量 |
|---|---|
| AppService 方法总数 | **2258**（322 个接口） |
| 有实现类 | **2127**（269 个接口） |
| 能追到方法体流转 | **1884** |

**关键事实**：322 个 AppService 里 **269 个已拿到实现类**。

实现 jar 不在本机 Maven 仓库（`<MAVEN_REPO>` 只有 facade/api），
从 Artifactory `libs-release` 下载了 21 个 `*-biz` 构件（40 MB / 15869 类）到
`<MAVEN_REPO>-extra`：bpm-biz、organization-biz、ctp-{affair,user,message,media}-biz、
cip-{capability,connector,convert,manager,openapi-gateway}-biz、app-{approval,common,doc}-biz、
cdp-{data,schedule}-biz、m5-biz、portal-biz、ai-biz、udc-biz。

⇒ **BPM / 组织架构 / 事项 / 连接器 / 连接器能力 的流转现在都能追**。
剩下 53 个接口的实现确实不在这些 jar 里（多为纯接口或平台运行时装配）。

⚠️ 仓库**没有 `-sources.jar`**（Artifactory 搜索 `*-sources.jar` 返回空），
只有 class jar，所以是反编译方法体，不是读源码。

### 7.2 动作分布

| 动作 | 方法数 | 有实现 | 有流转 |
|---|---|---|---|
| 查询 | 1197 | 少量 | 少量 |
| 其他（batch/dynamic/process 前缀） | 390 | — | — |
| 创建 | 237 | 多 | 多 |
| 修改 | 159 | 多 | 多 |
| 删除 | 137 | 多 | 多 |
| 校验 | 41 | — | — |
| 导入导出 | 35 | — | — |
| 发布 | 29 | 多 | 多 |
| 流程 | 22 | 0（BPM 在服务端） | 0 |
| 启用禁用 | 11 | — | — |

查询类 1197 个太碎，索引里**按接口聚合**（只列接口 + 方法名，签名去 `packages/` 查）。

### 7.3 典型动作速查

**发布应用**（这组最常用，因为 ext 代码最终要靠发布生效）：

| 方法 | 接口 | DTO | 流转 |
|---|---|---|---|
| `deployNormal` | `ApplicationAppService` | `DeployNormalDto` | → `ApplicationService.deploy` |
| `deployForm` | `ApplicationAppService` | `DeployFormDto` | → `ApplicationService.deploy` |
| `deployNormal` | `ApplicationManagerAppService` | `DeployNormalDto` | → `ApplicationService.deploy` |
| `shelfCompatibilityLock` | `ApplicationManagerAppService` | `ShelfCompatibilityLockRequestDto` | → `ApplicationService.lockCompatibility` |
| `upgradeOnlyPageApplication` | `ApplicationManagerAppService` | `OnlyPageApplicationUpgradeDto` | → `CustomPageInfoService.upgradeSchema` |
| `upgradeCallExtendAppService` | `MicroFlowUpgradeAppService` | `Long` | → `MicroFlowService.selectListByConditions` |

⚠️ `DeployNormalDto` 的字段就是部署请求体（appId / deployType / projectType / terminalType），
字段表在 `dto-fields/udc.md`。

**流程类**（22 个方法全是 BPM，实现不在仓库）：

`send` / `submit` / `saveDraft` / `stepBack` / `repeal` / `stop` / `takeBack` /
`replace` / `pause` / `cancelPause` / `counterSignNode` / `addNode` —— 全在 `BpmAppService`，
实现是 **`BpmApiAppServiceImpl`**（不是 `BpmAppServiceImpl`，命名不规则，靠猜会漏）。

`send()` 的真实流转（反编译 `bpm-biz-appservice.md`）：

```
BpmUserTemplateService.selectCanSendTemplateByCode   ← 查可用模板
BpmTemplateService.selectEntityById                   ← 查模板实体
UserAppServiceProxy.getBpmMemberPost                  ← 跨服务取人员岗位
BpmOperationService.send                              ← 真正的发送
MessageRepository.getMessage                          ← 消息
BpmCommonUtil.isLongNull / ExceptionUtil.isTrue       ← 参数校验与异常
BeanCopier.copy                                        ← DTO 拷贝
```

入参 DTO 在 `dto-fields/bpm.md`（`BpmSendDto` 10 字段）。

**导入导出**（35 个）：

`import` / `export` / `transfer` / `transport` / `copy` / `saveAs` 前缀。
这组和 `TransportHandler` / `Importable` / `SaveAsHandler` 扩展点直接对应——
要自定义导入逻辑，实现那些接口，不是调这些方法。

### 7.4 「其他」390 个是什么

`batch*`（批量）、`dynamic*`（动态查询）、`process*`（流程处理）、`push*`、`sync*` 等前缀，
未归入八类动作。要查具体某个，直接搜 action-index.md。

### 7.5 缺口

- 53 个 AppService 仍未找到实现类 → 流转 UNVERIFIED
- 「流转」列只给第一步，完整链路看 flow 文件
- 实现是**反编译**不是源码（仓库无 sources jar），注释和局部变量名已丢失

## 8. Evidence

```
docs/audit/artifacts/extension-surface-20261029/
  action-index.md   124 KB（覆盖现实 → 动作分布 → 八类动作逐条 → 查询类聚合 → 用法 → 缺口）
  impl-map.json      51 KB（269 个接口 → 实现类，读字节码 implements 子句）

实现 jar：<MAVEN_REPO>-extra/（21 个 *-biz / 40 MB / 15869 类）
  来源 http://10.0.0.1/artifactory/libs-release/com/seeyon（只读 GET）

生成器
  tools/core/platform/fetch_biz_jars.py      下实现 jar
  tools/core/platform/build_impl_map.py      扫 implements 关系（命名不规则，必须读字节码）
  tools/core/platform/emit_action_index.py   --impl-map 合并两路映射
  闸门：能追流转的方法 < 100 则 WARN
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 2258 个方法的动作归类、入参 DTO、实现类 | `VERIFIED_STATIC_BYTECODE` |
| 370 个方法的流转第一步 | `VERIFIED_STATIC_BYTECODE`（反编译方法体） |
| 269 个接口 → 实现类映射 | `VERIFIED_STATIC_BYTECODE`（javap 读 implements） |
| 1884 个方法的流转第一步 | `VERIFIED_STATIC_BYTECODE`（反编译方法体） |
| 53 个接口仍无实现 | **推断**（21 个 biz jar 里都没有），未核实是否在其他构件 |
