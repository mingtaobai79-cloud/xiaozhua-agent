# standard-product｜扩展工程骨架：模块划分与包职责（后端）

> 本格回答**「我要写的类放哪个模块、哪个包」**。
> 只记录模块划分、包路径形态与职责，不含具体应用名/组织/环境与版本。
> 扩展点接口本体见 `udc-microflow-extend-interfaces.md`；接口×平台实现见
> `docs/audit/artifacts/extension-surface-20261029/extension-points.md`。

分级：`VERIFIED_STATIC`（读平台生成的后端工程实际文件树 + 各模块 pom 依赖）。

## 1. Capability

平台给一个 UDC 应用生成的后端工程固定是**五个 Maven 模块**，根包统一为
`com.seeyon.<应用标识>`（应用标识 = 平台给的应用目录名，通常带 appId）。

拿到工程后第一件事不是写代码，是认清**哪个模块能写**——只有 ext 能写，其余四个是生成物：

- `-facade` / `-biz` / `-web` / `-assemble`：平台按设计态元数据整包生成，**重新构建即整体覆盖** → 只读
- `-ext` 的 `extend/` 包：客开唯一落笔处

在这套工程里手改生成模块的代码，下一次构建就没了，而且不会有任何提示。

## 2. Version

不含。模块清单与应用版本无关，平台固定生成这五个。

## 3. Input

平台「沙箱构建 / 代码生成」产出的 backend 目录，典型形态：

```
backend/
├── pom.xml                              ← <modules> 列下面五个
├── README.md
├── <应用标识>-facade/
├── <应用标识>-biz/
├── <应用标识>-web/
├── <应用标识>-ext/
└── <应用标识>-assemble/
```

## 4. Required

模块间依赖是**单向链**，逆着写必然循环：

```
facade  ←  biz  ←  web
  ↑        ↑       ↑
  └────────┴───────┴──  ext（依赖 biz + web + facade 三者）
                        assemble（依赖 web + ext）
```

- `facade` 依赖标品 facade（`cip-connector-facade` / `portal-facade` / `ctp-user-facade` …），不依赖本项目其它模块
- `biz` 依赖 `facade` + `boot-starter-web`
- `web` 依赖 `biz`
- `ext` 依赖 `biz` + `web` + `facade`
- `assemble` 依赖 `web` + `ext`，含唯一启动类

## 5. Execution

改代码只有一步：判断要改的行为对应哪个扩展点 → 在 `-ext/extend/` 新建实现类 → 自行注册。
facade / biz / web / assemble 一律不碰（读了可以，写了会被覆盖）。

## 6. Side Effects

- 在 `ext` 里新增扩展点实现类，需要**自己保证注册**：平台没有 META-INF/services、
  也没有 spring.factories 自动装配（见 `udc-microflow-extend-interfaces.md` §7.9）。
- 往生成模块（facade / biz / web / assemble）里手改的任何代码，下次构建都会整包覆盖，
  改动直接丢失、无提示、无告警。这是最容易白干半天的地方。

## 7. Known Constraints

### 7.1 五模块职责表（照这个放，不要自创模块）

| 模块 | 包（根包之下） | 放什么 | 典型文件 |
|---|---|---|---|
| `-facade` | `api/` | 应用内服务**接口**。微流程「自定义服务」节点能选到的候选就是这里 | `XxxAppService.java` |
| | `api/dataflow/` | 数据流运行时接口 | `XxxDataFlowRuntimeAppService.java` |
| | `api/microflow/` | 微流程可调服务接口 | `MicroFlowAppService.java` |
| | `custom/service/`、`custom/service/microflow/` | 自定义服务接口 | — |
| | `dto/`、`dto/microflow/event/` | 请求/响应 DTO、事件体 | `XxxDto.java` |
| | `enums/` | 本应用枚举 | — |
| | `domain/message/` | 消息体 | — |
| `-biz` | `appservice/` | 上面 `api/*AppService` 的**实现** | `XxxAppServiceImpl.java` |
| | `appservice/dataflow/`、`appservice/microflow/` | 数据流/微流程服务实现 | — |
| | `custom/appservice/` | 自定义服务实现 | — |
| | `custom/config/`、`custom/processor/` | 客开配置、处理器 | — |
| | `beanname/` | Bean 名生成（对应 `CodeTask` 族） | — |
| | `context/` | 上下文持有 | — |
| | `domain/entity/`、`domain/dao/` | 实体与 Mapper/Dao | `Xxx.java` / `XxxDao.java` |
| | `domain/service/`（含 `entityrule/` `microflow/` `dataflow/`） | 领域服务 | `XxxDomainService.java` |
| | `registry/` | 注册表 | — |
| | `schedule/` | 定时任务 | — |
| `-web` | `controller/` | REST 层。平台生成的是 `Abstract` 前缀，可继承覆盖 | `AbstractXxxController.java` |
| `-ext` | `extend/` | **扩展点实现**：`Importable` / `SaveAsHandler` / `TransportHandler` / `AppMetaDataContextPostProcess` / `CodeTask` 等 | 自己新建 |
| `-assemble` | 根 | 唯一启动类 | `Application.java` |

### 7.2 唯一可写层：ext（其余全是生成物）

**硬边界**：facade / biz / web / assemble 四个模块都是平台按设计态元数据整包生成的，
重新构建一次就整体覆盖，手改代码不会保留。这四个模块只能**读**——拿来查契约长什么样、
查生成出来的 AppService 有哪些方法、查 DTO 字段——不能写。

可写的只有 `<应用标识>-ext` 一个模块的 `extend/` 包。

由此推三条：

1. **要改生成层的行为，只能在 ext 里 implements 扩展点**（151 个可选，见
   `extension-points.md`）。改 biz 的 `XxxAppServiceImpl` 或 web 的 Controller 都是白改。
2. **ext 里也不要拿生成的 `Abstract*Controller` 当继承抓手**——它随元数据变、每次重生成
   都可能换形态。要拦请求、改输出口径，走钩子：`DeployBeforeService`（部署前校验，能拦发布）、
   `AppMetaDataContextPostProcess`（元数据后处理）、`TransportHandler`（导出内容）、
   `Importable`（导入）这类。
3. **facade 里的 `api/*AppService` 是读的对象不是写的对象**：它告诉你这个应用暴露了哪些
   服务、微流程「自定义服务」节点能选到什么，但你要加接口不能在这加。

### 7.3 ext 模块的现状

平台生成的 ext 模块默认只有 `extend/package-info.java` 一个文件（占位说明）。
也就是说扩展点是**空的**——平台一个钩子都不预置，所有扩展行为都要自己写。

反过来这也确认了边界：ext 里没有生成物，所以这个模块整体归客开，构建不会覆盖它。

## 8. Evidence

```
① 样本   平台生成的后端工程（UDC 沙箱构建产物 backend/），五模块实际文件树
② 规模   facade 71 java / biz 146 java / web 39 java / ext 1 java / assemble 1 java
③ 依赖   <modules> 顺序 = facade → biz → web → assemble → ext
         （ext 在 assemble 之前声明，但 assemble 同时依赖 web 与 ext）
④ 抽验   各模块 artifactId 与根包 com.seeyon.<应用标识> 逐字核对
⑤ 复现   同一应用重新触发构建，对照 backend/ 目录结构是否一致
```

不含：具体应用名、appId、组织标识、版本号、本机路径（均在证据件中，不入本格）。

## 9. Verified


- 模块清单与依赖链：读实际生成的 `backend/pom.xml` 的 `<modules>` 与各模块 `pom.xml` 的依赖
- 包职责表：逐模块 `find <模块>/src/main/java -type d` 与实际文件分布比对
- 命名规范：`api/XxxAppService.java` 与 `appservice/XxxAppServiceImpl.java` 一比一对应
- ext 为空：`find <应用标识>-ext -name "*.java"` 只返回 `extend/package-info.java`
- 生成物会覆盖：对比两次构建产物的同路径文件，facade/biz/web/assemble 内容随元数据变；
  ext 目录两次构建后保持不变（客开代码不被触碰）
