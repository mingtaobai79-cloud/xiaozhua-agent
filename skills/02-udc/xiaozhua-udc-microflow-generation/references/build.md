# 真构建 · 部署 · 一致性检测

> 由 SKILL.md 拆分而来，按需读取。

### 真构建验证（唯一能证明「生成的 Java 能编译」的手段）

#### ★★★ 构建产物 zip 是完整后端源码（最高优先级证据源）

**不用反编译 runtime，不用进 pod，不用 kubectl。** 每次成功构建都会把完整后端源码打进
一个 zip，`backBuild.log` 第一屏就写着地址：

```
构建元数据: http://<HOST>/service//udc/file/download?storageKey=metadata/udc/<appId>/<buildVersion>.zip
日志路径:   /A8C/base/autocode/<appId>/<buildVersion>/backBuild.log
```

```bash
CK=$(cat scratch/_ck.txt)          # 会话 cookie
curl -s -L -o meta.zip -H "Cookie: $CK" \
  "$HOST/service/udc/file/download?storageKey=metadata/udc/<appId>/<buildVersion>.zip"
```

实测一个应用 ~3.4MB / 3000+ 条目 / 250+ 个 java。里面有：

| 路径 | 能证明什么 |
|---|---|
| `…/domain/service/microflow/Rtv…Service.java` | **微流程编译出的 Java**：attrs 到底被翻成什么代码、节点顺序、变量传递 |
| `…/domain/service/<Entity>Service.java` | `preCreateBatch` / `executeExpression` → **哪些字段配了默认值表达式** |
| `…/api/<Entity>AppService.java` | 有没有 `create` / `update`（写节点可用性闸门） |
| `…/controller/Abstract<Entity>Controller.java` | 真实 REST 路由（`@PostMapping("create")` 等） |
| `…/dto/<Entity>Dto.java` | 字段类型、getter/setter 名 |

**什么时候用**：凡是出现「生成的东西运行时行为与预期不符」且 publish/build/UI 都绿时，
**第一件事就是拉这个 zip 看生成代码**，不要去黑盒试探、不要反编译 runtime、
不要反复改构造器猜。相关结论落 `core/facts/udc/microflow/`。

zip 是客户代码，**不进仓**，用完即删/收容到 `_attic_pending/`。

##### 从 zip 出实体可写性矩阵（写节点选实体前必跑）

写节点（`CREATE_ENTITY` / `CHANGE_ENTITY` 等）能不能用某个实体，由两件事决定，
都能从 zip 里读出来，**不要靠试跑**：

```bash
python scripts/entity_write_capability.py meta.zip --out entity-write-capability.json
```

| 判据 | 源码位置 | 不满足的后果 |
|---|---|---|
| `SingleResponse<Long> create(SingleRequest<Dto>)` 存在 | `*-facade/**/api/*AppService.java` | 构建 40 秒 FAIL：`找不到符号: 方法 create(SingleRequest<…Dto>)` |
| 字段的默认值表达式 `require_null` | `domain/service/*Service.java` 的 `preCreateBatch` | 传入值被无条件覆盖，写验证永远看不到效果 |

扫描三个实现坑（都踩过）：

- **不要写 `glob('**\facade\**')`** —— Windows 下多段 `**` 匹配不到，结果是「0 个实体有 create」的假结论。
  先粗匹配 `**/*AppService.java`，再按路径子串 `"-facade"` 过滤（模块目录名形如 `<app>-facade`）。
- **实体短名用 `basename[:-len("Service.java")]`**，不要用 `.replace("Service.java", "")` ——
  `*AppService.java` 也以 `Service.java` 结尾，replace 会把已经截好或用错的路径再咬一口。
- **表达式必须连 `requireNull` 一起取**：`executeExpressionXxx(list, <true|false>, XxxDto::getField, this::expNNN, …)`。
  只数 `executeExpression` 出现次数会把同一个字段的 get/set 两处算成两条，也分不出
  「仅空时填」和「无条件覆盖」这两种语义完全相反的情况。

实测某应用的分布（用来校准预期）：24 个实体里 18 个有 `create`、6 个没有（多为明细/子表）；
有一个实体 20 个字段全配了 `currentYear()` 表达式且约束 ≤100/≤999.99——**它永远插不进任何数据**，
拿它做写验证只能得到「值不生效」的错误结论。

#### UI 验收自动化（每次生成后必跑）
`components/udc/microflow/live/verify.py` 的 `verify_flow(app_id, mid, host, cookie)`：
打开编辑器 → 需要时点「编辑」转草稿 → 读 redux 里 `isCompleted=false` 的节点（**不要用颜色判**）→ 逐节点开抽屉读红字 → 取消关闭 → 重新发布。
返回 `{ok, nodes, issues[], state}`。

**判据用 `isCompleted`，不要用颜色。** 权威来源：
`appReduxStore.getState().appDesign.microflowEditorReducer.flowNodes` 里 `isCompleted === false`
（`elseBranch` 的 `null` 是常态，排除）。颜色判据会把设计态本来就红的元素全算成错误——
默认分支是珊瑚色、`CUSTOM_ERROR` 节点本身就是红色、选中项带强调色，一次扫出 6 条全误报。

- `document.hidden=true` 时 **innerText 恒空**（会读到 0 个节点），一律用 `textContent`；
- 节点点击要直调 React fiber 的 `memoizedProps.onClick`，且必须写成 `(() => {...})()`；
- 读完整后必点「取消」关闭抽屉，验收后必须重新 publish（UI 编辑会打回 DRAFT）。
- 判据细节、假阳性清单、执行入口探测结论、SUB_MICROFLOW 形态：见
  `references/execution-entry-and-ui-verify.md`。**`open_api=STOP`（默认）的流程没有 HTTP 执行入口，
  不要靠拼路径试（4002/404 无效探测）；RUNTIME 前置=流程开对外接口或绑定页面规则。**

#### 真跑一次：平台的真实入口（详见 `references/runtime-execution-reality.md`）

设计器里 **没有「用入参跑一条流程」的执行器**：

- 「测试」→ 「应用测试 / 本次发布预估时长 / 立即构建」= **构建测试版本**；
- 「页面调试(beta)」→ 「会建构页面和页面规则…不适用涉及调用后端服务的更改」= **构建对话框**。

两个都是构建入口，点错就白跑一次构建；验证完点「取消」退出。

#### 前端「测试」构建链（设计器抓包实测，与 deploy-normal 等价的前端通路）

| 步骤 | 接口 | 要点 |
|---|---|---|
| 触发构建 | GraphQL `udcRuntimeDeployNormalPost`（mutation） | body `{"deployDto":{appId,deployType:"RELEASE",projectType:"ALL",terminalType:"ALL"}}` → `deployId` |
| 状态轮询 | GraphQL `udcSandboxBuildInfoAppGet`（path: appId） | `{state: BUILDING/SUCCESS/FAIL, progress, buildVersion, logs[]}`；`logs` 即「展开沙箱日志」全文 |
| 详细日志 | `GET /service/udc/file/download?storageKey=compile-info/{appId}/{yyyymmddhhMMss}/backBuild.log` | maven+javac 全文，判 `BUILD SUCCESS/FAILURE` |

progress 82% ≈ 后端编译（FAIL 案例停在 82，SUCCESS 走 91→100）；构建产物 6 模块
（`-facade/-biz/-web/-ext/-assemble-resource`，微流程生成代码在 biz）。前端「测试」弹窗里
「运行中测试版本 V1.0.N」就是最近一次 SUCCESS 构建的运行态。
同一 app 并发构建限制、FAIL 后 5 分钟锁，与 deploy-normal 链相同（见下节）。

**progress 停在 91% 超过约十分钟 ≠ 卡死要重发**：实测同一轮构建长时间停在 91% 后，
服务端会自动重开新一轮（progress 回落到 18 再重新爬升），最终 SUCCESS。
轮询时先看 progress 是否回落再判卡死；回落即新一轮在跑，继续等，别再发 deploy-normal
（那只会挤进并发限制）。判卡死的依据是「长时间停且 progress 无任何变化」且轮询间隔已足够宽。
真跑的证据链只能从三处取：读接口回读、页面注册的写路由、定时任务按周期真触发。
具体路径、限制与验证脚本见 `references/runtime-execution-reality.md`。

#### 标准服务入参的「参数名称」
MANUAL + BASIC 的真实形态：`trigger.desc == output.desc == 业务显示名`，两处都要写。
只写 output.desc 不写 trigger.desc，设计器「参数名称」是空黄框（必填未填）。

#### 真跑一次（运行时验证）：先拿入口，别拼路径

发布 + 编译通过只证明「生成了正确的 Java」，不证明「跑出来是对的」。要真跑，先解决入口：

- 设计器里的「测试」和「页面调试(beta)」**都是构建对话框**（弹「应用测试 / 本次发布预估 N 分钟 /
  立即构建」或「页面调试会建构页面和页面规则」），点下去会触发一次构建，**都不是用入参跑一遍的入口**；
  误点必须点「取消」退出，别点「立即构建」。
- 运行态网关 `/service/{appName}/udc-runtime/...` 是通的（`data/query` 直接有响应）；
  但 `dynamic-rest/com-seeyon/{appName}/{x}` 的第一段被当**页面坐标**解析 —— 微流程没有页面坐标，
  **后缀怎么拼都是 `BOOT_4002 应用坐标数据不存在`**。
- 微流程服务控制器不保证注册在应用 runtime 下（`/service/{appName}/udc-runtime/udc/*AppService/{name}` → 404 Whitelabel）。
- **所以：不要靠枚举 URL 后缀找执行入口。** 合法来源只有两个：①服务定义里开对外接口（restApi/restPath）后取真实路径；
  ②直接问用户要那条接口的完整 URL。拼十几轮后缀是纯浪费，且容易被 `BOOT_4002` 伪装成「接口存在但参数错」。
- 现阶段可用的验证阶梯（不依赖写路径）：UI 验收（`isCompleted` + 抽屉红字）→ 发布 → delta 构建读 `backBuild.log`。
  触发方式、路由判读表、子微流程形态见 `references/runtime-invocation.md`。

#### 查询条件右值只有三种形态（塞错就 BOOT_1001）
```
变量引用 CONTEXT_VARIABLE  value = selectParam 的 JSON 字符串
expression?   EXPRESSION      value = designData 的 JSON 字符串
常量          CONSTANT        value = "10", desc = "10"        // 469/193/136 真实样本
```
右值是 `{type, value, desc}` 三键；直接把 selectParam 对象放进 rightParams → `BOOT_1001 Parameter Error`。

#### LIST_OPERATION 的 14 种操作（无 ADD）
FIRST_ONE / DISTINCT / FILTER / SORT / SUM / PICK_ONE / MAP / SIZE / LAST_ONE /
SUBTRACT / MIN / MAX / GROUP_AND_SUM / INTERSECT。
- 统计条数用 `SIZE`，出参 INTEGER/java.lang.Integer（`microflow_nodes_extra.list_size`）。
- 引实体列表时 selectParam 必带 `dtoType`，否则闸门拦（803/803 真实样本都有）。
- 往列表加元素只能 `CHANGE_LIST(action=ADD)`。

#### 列表复制（copy）组合模板 —— 用户口述的「写方法」七步
```
ids = 入参(BASIC BIGINTEGER[])                        # trigger.isArray=true, output.type=ARRAY
old = RETRIEVE_ARRAY(fetchType=IDS, value=SelectParam→ids)
new = CREATE_LIST(paramType=ENTITY_OBJECT, structure=实体, value=[])   # 空列表，不是 BASIC 型
for (o : old) {
    copy = CREATE_VARIABLE(paramType=ENTITY_OBJECT, structure, mappingType=attrs,
                           attrs=[{attrType: field_attr(f), value: SelectParam}])   # 字段对照
    CHANGE_LIST(action=ADD, selectParam=目标列表, dataSource=copy)      # 只能这么加元素
}
cnt = CREATE_BATCH_ENTITY(selectParam=目标列表)         # 出参 INTEGER
BRANCH(cnt > 0) else CUSTOM_ERROR(errorType=GLOBAL, error=Simple文案)
endNode BASIC INTEGER = cnt
```
★ `LIST_OPERATION` **没有 ADD**（643 条里只有 FILTER/SORT/MAP/SUM/FIRST_ONE 等 14 种），
往列表塞对象只能 `CHANGE_LIST(action=ADD)`（266/317 样本为 ADD）。
★ 标量表达式引用：token `value = "_NODE._NODE"`（两段，无字段），
context 条目 properties[0].name 也是该 NODE 名，paramCategory=该标量类型。
实现在 `microflow_nodes_extra.create_list_entity / change_list_add`。

#### 字段 attrType：真实 16 键（UI 字段映射能不能回显就靠这个）
`attrs[].attrType` 写成自造 19 键（validate/md5/caption/customs/refType…）时，
checkSchema 绿、发布绿、编译绿，但设计器「创建变量→字段映射」左列全部红字
「所选数据已失效，请重新选择」。真实键集（643 条语料）：
`name/id/fullName/javaType/dataType/type/desc/description/relationApp/refApp/`
`multiSelect/filterDataType/filterType/filterFullName/dataI18n/sort`，
关联字段（dataType=ENTITY）另加 `refId/relationEntity/relationEntityId/filterRelationEntity`。
缺 filter* 就是上面的红字。实现在 `microflow_fields.field_attr`。

#### UI 验证流程（RELEASE 状态点不动节点）
设计器里 RELEASE 的流程节点不可点（提示「正式状态，点击编辑转为草稿后才可编辑」）。
验证顺序：点「编辑」→ 点节点卡（直调 `.node-body` 的 React fiber `memoizedProps.onClick`，
鼠标点击会被连线层挡）→ 读 `.ant-drawer` 的 innerText 找红字 → **验完必须重新 publish**。
两个坑：`document.hidden` 为 true 时所有浮层宽 0（先 `Emulation.setFocusEmulationEnabled`）；
字段映射的右列值不在 innerText 里，要用 `input.value` 读（形如「原数据源.字段名 [类型]」）。

#### 监听 / 定时：两条铁律（都踩过）

**⓪ 触发节点必须带 `isCompleted: true`。**
BUSINESS_EVENT 61/61、SCHEDULE 24/24 真实样本都有。缺它设计器里「事件监听」节点是红的
（未完成态），但 publish/checkSchema 全绿——只有肉眼看得出。

**① 一致性检测未通过：先拉明细，别猜。**
`POST /service/udc/graphql?udcApplicationSearchDetectionPost`，GraphQL envelope + body `{appId}`
（`LiveRefs._gql` / `_content` 现成可用），返回 items[]：`{code, moduleType, interpolatedMessage, path}`。
两类别混在一起：节点空必填/空引用（我们造的）vs 应用既有问题（用户的循环内调服务警告、
生单规则 ID 映射、选项集缺项）——**后者也会拦构建，不要误归因到自己生成的流程**。

**② 监听流程直接从事件对象拿数据，不要按 id 回查。**
事件载荷里实体挂在子节点 `info`：
`name=info, id=<eventMfCustomDto>.info, path=<eventMfCustomDto 去点>.info, dataType=DTO, dtoType=MASTER_ENTITY`，
直接 `CHANGE_ENTITY(selectParam=该 info 引用, attrs=…)`。
选完事件前端会发 `udcMicroflowFindCustomDtoPost`（appId/appName/dtoFullName=eventMfCustomDtoName/
needChildren=true）做确认，可用 `LiveRefs.dto_attributes` 代替，不发设计器里事件节点显示异常。
★ 事件被监听后就不再出现在 `udcMicroflowFilterEventPost` 候选列表（消失 = 已被占用），
要复用就改现有流程，不要新建。★ 事件对象里没有 ids 列表，IDS 集合查询必然传空参数。

**③ 定时/事件与 publish body 的配套字段**
- 顶层 input：SCHEDULE 两处 null；BUSINESS_EVENT 的顶层 `input = trigger.output`（事件数据入参）。
- publish body 要带 `scheduleCaption` / `businessEventCaption`（真实抓包恒有，不适用填 "-"）。
- 事件监听无其它出入参；定时任务 `endNode.output=null`。

#### 构建不能并发
同一 app 同时只能跑一个构建：前一个卡在部署阶段（progress 停在 91%）会让后续 build
排队「沙箱全忙,等待中...」或直接 FAIL（msg="流水线回调:"）。
处理：`POST /service/udc/runtime/deploy/stop/{deployId}` 停掉卡住的构建释放沙箱，
排队的 build 会自动继续。编译结论看 backBuild.log，不看 deploy 的 state。

**★ 构建失败时 `wait()` 的 `problems` 可能是空的——真正错误在 `deploy_status()["msg"]`。**
`PlatformBuilder.wait()` 只解析 `state` / `validate` / `buildVersion`，拿不到编译错误；
`deploy_status(deploy_id)` 返回的 `msg` 里才有完整链路：

```
流水线回调:业务异常[后端失败:业务异常[后端失败:,详情链接:…/file/download?storageKey=compile-info/{appId}/{buildVersion}/backBuild.log
[ERROR] Failed to execute goal …maven-compiler-plugin…: Compilation failure
[ERROR] /…/biz/src/main/java/…/Rtv…Service.java:[172,189] 找不到符号
[ERROR]   符号:   类 _CREATE_VARIABLE_xxx
[ERROR]   位置: 类 …dto.YsFull6956Dto
```

所以**「构建 FAIL 但看不到原因」时，下一步一定是读 `msg`**，不要反复重发构建、也不要只看
`problems=[]` 就判「平台没给信息」。`msg` 里的 `XxxService.java:[行,列]` 直接指到生成的
Java 代码行，对照回节点配置能定位到具体字段。

**★★ 坏报错里的 `Rtv…Service` 可能根本不是你刚建的这条流程——`projectType:"ALL"` 是整个应用一起编。**
应用里只要残留任何一条编译不过的历史流程（哪怕已经删了节点、只是草稿），整包就 FAIL，
而报错里的类名是**旧流程**的。此时你会拿新代码对着一份与它无关的堆栈反复排查，
结论必然是「我的修复没生效」——这是个会直接带偏方向的假信号。

判据与处置：
- 把 `msg` 里的 `Rtv…Service` 类名与本次新建流程的 `name` 对一下，**对不上就不是你的问题**。
- 临时验收流程用完即删，不能留着；残留流程即使不跑也会被编译。
- 删完重跑构建，报错类名才会切到真正的那条。
- 删验证流后要触发一次构建收尾（见下文 backBuild.log 那节），否则验证期的生成代码留在沙箱。

**构建 FAIL 之后锁还在，约 5 分钟才放**：这期间 `deploy-normal` 一律回 `UDC_DEPLOY_0002 app publishing`
（`data.content=null`，看起来像「没触发」）。`deploy/stop` 对已 FAIL 的记录不释放这把锁，只能等。
做法：触发与轮询分离，每次调用只跑一轮、间隔 50–60s，不要在一个 `execute_code` 里循环 5 分钟以上——
撞上 300s 上限会连同这轮的输出一起丢，反而看不出到底触发没触发。

现成脚本：`python scripts/verify_build_compile.py --app <appId> [--expect-biz-sources N]`
（触发 DELTA、等 buildVersion、读 backBuild.log、判 biz 源文件数、查 app-ready-state，退出码 0/1/2）。
**删验证流后必须重建收尾**：临时验收流验完即删，但删除后要触发一次 DELTA 构建（成功收尾），
否则验证期间的生成代码留在沙箱里，下次构建的 biz 源文件数对不上账。手工步骤：
发布 REST 只写元数据，**不编译**。验证步骤：
1. `POST /service/udc/runtime/deploy-normal`，body 必须包裹 `{"deployDto": {"appId": …, "deployType": "DELTA", "projectType": "ALL", "terminalType": "ALL"}}`
   → 返 `deployId` + `buildVersion`（DELTA 也会重建后端镜像，约 5-10 分钟）。
2. 读编译日志（不必等部署完，编译先出）：
   `GET /service/app-sandbox/file/download?storageKey=compile-info/{appId}/{buildVersion}/backBuild.log`
   同目录还有 `frontBuild.log`。只看 `BUILD SUCCESS` / `BUILD FAILURE` 与 `XxxService.java:[行,列]`。
3. 部署状态：`POST /service/udc/runtime/search-deploy-status/{deployId}` body `{}`，
   ⚠ `data.content` 是**数组**（不是对象），取 `[0].state` / `[0].failReason`；
   PUBLISHING 会持续到镜像部署完，编译结论看 backBuild.log 即可。
4. 对照法（判断「真编译了」而不是「没编到所以没报错」）：
   - 失败日志里 `[app-…-biz] Compiling N source files` 后紧跟 `XxxService.java:[行,列]`；修完重跑
     同一 N 仍 SUCCESS 即同一批生成类通过。
   - **新增一条流程时 N 必须 +1**（115 → 116）。数字没变说明新流程没进本次生成，SUCCESS 不算证据。
5. 部署面收尾：`POST /service/udc/deployment/app-ready-state` body `{appId}` →
   `state:RUNNING` + `msg:DEPLOY_SUCCESS` 即部署真完成。常出现 sandbox `delta-build-info`
   卡在 progress 91、`udc_deploy_record` 仍 PUBLISHING，而实际已部署成功——以 app-ready-state 为准。

G15-G18 是 2026-10-30 从「v2 数据源校验流程」三轮真发布失败中提炼的：
它们全部是 **checkSchema 全绿、只有真发布或打开 UI 才暴露** 的坑。
双向校准：643 条真实语料 0 误报；注入 5 类缺陷 5/5 命中；test_composer 13/13
（commit 1ad47939）。改 gates.py 后必须跑这三样，缺一不可。

**G9 是本轮新增的关键闸门**，管的是「checkSchema 全绿但抽屉里空着」这一层：

- `MAP_OPERATION.basic` 是裸字符串 `"STRING"` → 抽屉「数据类型」空占位 + `structure` 被迭代成 `{"0":"S","1":"T",...}`
- `CREATE_LIST` BASIC 缺 `value` → 列表无初值（母版允许无 value，故 G9 只作提示不拦）
- `MAP_OPERATION.nullPromptMessage` 为空 —— **G9 故意不拦**：生产 24 个 MAP_OPERATION 全部为空仍正常运行，它是 UI 新增强校验，只对「新建节点点确定」有效，拦了会把存量业务流全判红。新建节点时仍要填（用户抽屉里看着是必填），但闸门不据此拒发布。
- `CREATE_ENTITY.value` 是 SelectParam 但指向不存在的 output 且无 `nodeInfo` → 运行时炸弹
- `END_NODE` 出现在 `nodes` 数组 → 画布渲染占位符

**误报基线的硬要求：`fixtures/microflow/backup/xzhAllNodesV16.schema.json`（生产母版）必须 0 问题。** 闸门一有误报就会挡住真实业务流，代价比漏检更大。本轮为此把两条过严判据改成可选/降级：

- `G4 DATA_MAPPING` 原来查 `mappingRule.name`，母版压根没这个字段 → 改查 `id`/`caption`
- `G5` 原来在没传 `dep_apps` 时把所有外部应用都报未依赖（dataSchema 顶层没有依赖字段，依赖在 create body 上）→ 改成 `if dep_apps and ...`
- `G8 run_order_gate` 原来强制「只能引用前面的节点」，但母版 `CHANGE_VARIABLE_sqv49j`(idx 9) 引用后序 `RETRIEVE_KNCEzh`(idx 10) 能正常发布 → 改成 `strict=False` 默认不报
- `G2/G10` 对实体引用 `_<relationEntityId>`（纯数字，无 nodeInfo）会误判悬空 → 只对带 `nodeInfo` 或形如 `_<ACTION>_<hex6>` 的名字判

**闸门改动的双向回归，缺一不可**：① 误报向——生产母版 `fixtures/microflow/backup/xzhAllNodesV16.schema.json` 必须 0 问题；② 漏报向——取当前 schema 深拷贝，注入 `basic:"STRING"` + `structure` 带字符下标 + `nullPromptMessage:""` + END 塞进 `nodes` + `endNode:{}`，必须全部命中。只跑一边会得到「闸门很干净但什么都抓不到」或「闸门报一堆但全是误报」。样本用完即弃，**不要依赖 `scratch/` 下的临时文件**——那里不进版本管理，下次会话根本没有。

## 存量草稿体检 / 修复阻断（读回→判→修→update→check）

用户问「这条草稿的节点是不是都有问题」时，按四层分级出结论：**BLOCKING**（前端 truthy 判空为真，零请求拦截）/ **QUALITY**（值只有空白字符，保存放行但运行时弹空白框）/ **RUNTIME**（能保存但语义跑不通，如子流程入参映射空）/ **EXPR**（表达式 tokens 引用失效变量或左右同源恒等式）。

四条防误报 / 防漏检铁律（存量体检最容易在这四处翻车）：

1. **扫悬空引用必须整棵跳过 `SUB_MICROFLOW.mfService`**。里面 `_FLOW_INPUT_xxx` / `_FLOW_OUTPUT_xxx` 是被调子流程**自己的形参名**，不是对本流程出参的引用。只收带 `nodeInfo` 或 `position:"parent"` 的真引用。**引用载体有两类，都要扫：值槽位里的 `selectParam`（`pageInfo.selectParam`、`attrs[].value.selectParam`）+ 节点顶层的引用字段（`selectParam`/`selectMap`/`dataSource`）**——`CHANGE_VARIABLE.selectParam`、`MAP_OPERATION.selectMap`、`CHANGE_LIST.dataSource` 都是节点顶层直接引用前序出参（`outputName`），悬空同样报 04004，只扫值槽位会整层漏。
2. **遍历要带祖先链**，不是单个父节点。`BREAK` 只在 `FOR_EACH`/`FOR` 内合法，链断了就误判成根级。
3. **`SAVE_REQUIRED_FIELDS` 是并集，条件必填要按实际配置判**（`SAVE_CONDITIONAL_FIELDS`），否则 `CREATE_VARIABLE.otherType`、`RETRIEVE.nullPromptMessage` 全报。
4. **表达式层必须单独扫——靠字段名找引用会整层空转。** `expression` 是 `{title, schema}` 对象（`schema` 又是 JSON 字符串，内含 `designData.tokens` / `runtimeData.executableExpr`），按 `outputName` / `name` 匹配的 `find_refs` 一条扫不到，于是报「全部健康」，而用户一开表达式面板就是红字。**这是最危险的漏检形态**：必用结构特征（dict 且 schema 含 `designData`/`expressionTranslation`）递归找，然后校验 `tokens` 里 VARIABLE 的根名是否命中本流程 `output.name`、是否左右同一变量（`x > x` 恒 false，分支永远不进去）。BRANCH 与它的 CONDITION 是同一个表达式对象，按 `nodeId` 去重后再报数。**tokens 遍历必须递归进 `FUNCTION.subOps`（二维数组，外层=参数位置），只遍历顶层 tokens 会漏掉函数参数表达式（如 `roundOffFloor(变量/999)`）里的悬空引用与 token 类型值域，报告假绿**——审计/闸门代码（`check_expression`、G2/G8）都改走递归遍历，写扫描器时不要只看顶层。
5. **判「用户这次改动行不行」要沿容器链看生效范围，不能只看节点配置本身。** 同一个 `CHANGE_VARIABLE`，挂在 `FOR_EACH` 循环体里又没前置分支保护，就是对每一条记录无条件执行；条件写宽（用「字段包含某关键词」代替「字段 == 某值」）会把本来正确的记录一起改写。核验顺序：定位节点 → 往上找最近的 `FOR_EACH`/`BRANCH` 容器（子节点在 `nodes` / `conditions[].nodes`，只读顶层 `nodes` 会把整段循环体看丢）→ 读条件表达式的 `expressionTranslation` 中文原文 → 判断覆盖面是否恰好等于用户想改的那批。只回「配置填对了」是半个答案，用户要的是「会不会误伤」。
6. **异常判据要选「不可能自然相等」的组合，不要选语义关键词。** 展示层做数据纠正时，`字段A == 字段B`（如节点名称 == 处理人姓名）零误伤；`字段A 包含 '加签'` 会命中平台本来正确生成的同形数据。判据写宽了，改完看起来生效了，实际把对的数据改错了，且回滚时已经分不清哪条是本来的、哪条是被改的。

**体检报告写「全部健康」之前，必须先跑一遍表达式扫描。** 节点必填都齐 ≠ 流程能跑：表达式引用一条失效变量，保存照样 200、画布照样显示完整表达式，只有运行时分支永远为假。

**标成 BLOCKING 前先真点一次保存**：有 `udcMicroflowCheckSchemaUpdatePost` 200 且 console 无 `firstErrorNode` 就是没拦。凭「字段看着空」断言会失败，会被用户一次点击拆穿。

只改差异点，state 保持原值（DRAFT 保持 DRAFT，别覆盖用户编辑态）；update + checkSchema + 检测收尾。工作区收敛时按用户指令保留点名流程、删其余，删后重新 Search 复核数量。

分级判据、truthy 与 `strip()` 的差异、`attrs:[]` 这类「保存能过运行会坏」的缺陷模式、**表达式层扫描函数与两类缺陷（变量根失效 / 左右同源恒等式）**、汇报口径，见 `references/draft-node-audit.md`。

**报告口径：漏检比误报更致命。** 体检第一版报「0 问题」而用户截图里是红字时，先承认漏了哪一层，再补扫描重报——不要拿「脚本没说有问题」当依据。

**看不到用户的截图时，第一句话就说看不到，不要拿后端反查冒充看图。** 用户贴图报「很多地方报错」而 `vision_analyze` 返回 `503 model_not_found` 时，正确动作：① 立刻声明「视觉模型不可用，我看不到图」；② 同时修视觉通道（`hermes config set auxiliary.vision.provider/model`，见 `hermes-model-provider-switching`）；③ 再用后端 `dataSchema` + CDP 取证自己找问题。跳过 ① 凭后端猜着回答，等用户发现你根本没看图，信任损失远大于慢一步。

**用户列点批评（「你没赋值 / 你没选 / 你写的什么」）时逐条取证、逐条认。** 每条落成「后端实测值 vs 应有值」两列，全部承认后再动手；改完回读同一组字段逐条对照回复。用户不接受「已修复」而不附值。

**用户问「这 N 个节点你到底明白了没 / 构造器都写好了吗」时，先建覆盖矩阵再回答，不要凭印象说「都明白了」。** 对每个 actionType 逐列取证：模板文件在不在、构造器函数在不在、facts 有记录、前端 bundle 命中、后端反编译命中；然后分成「证据链完整（已闭环）」「只有结构没有语义」「完全没碰」三档，缺的明确说缺什么、为什么缺。这类问题是在验收你的知识边界，把「已闭环」和「未验证」混在一起报等于自曝其短。

## 保存提交通过 ≠ 真通过（必须做一致性检查）

`checkSchema` 返回 `{check:true, errors:0}` 不代表流程对，可能是假通过。收尾必须再做：

1. `udcApplicationDoDetectionPost` 应用级检测，ERROR=0（sleep 3-4 秒再读）
2. 回读 `dataSchema`，逐节点比对前端 store 的 `flowNodes` 与后端保存结果是否一致
3. 检查每个节点 `output.name` 是否真能被后续节点引用到
4. 检查表达式 `executableExpr` 是否由 `/expression/transform` 生成（不是手写）
5. 页面点一次「检查」——前端绑定类错误只有前端认得出

**逐节点触发校验是定位错误最快的路径（用户指定的验收方法）。** 后端 `checkSchema` 全绿只证明结构合法；把画布上每个卡片点开、点「确定」走一遍前端校验，报错精确落在那个节点的那个字段上（`.ant-form-item-explain-error` 文本 + `.ant-form-item-has-error label`）。整条流程「保存并提交」只在 console 报 `firstErrorNode`，定位成本高得多。

逐节点跑完再判「流程可用」，判定口径：后端回读 `state=RELEASE` + UI 编辑器 `flowNodes` 逐节点 `isCompleted===true` + 画布卡片全部渲染 + **每个节点的抽屉点确定无红字**。四项缺一不可。

**「画布全部渲染」要用硬判据验，不能数卡片数：**
- 占位符计数必须为 0：遍历 `document.querySelectorAll('*')`，叶子节点文本含「节点开发中」的个数。
- 终点节点必须在：`document.querySelector('#MFEndNode')` 命中、`className` 含 `end-node`、文本为「结束」。
- 容器节点在画布上显示的是 `计数循环：<targetName>` / `循环列表：<targetName>`（**不是**「列表循环」）——按「列表循环」匹配 DOM 会把渲染正常的 FOR_EACH 判成「没渲染」。
- `.udc-microflow-editor-node-container` 数量天然少于 `flowNodes`（循环体/分支体内的子节点不各自成 container），少几个不是缺陷，别拿总数断言。

**★ 逐节点点「确定」有破坏性副作用：会把顶层 `endNode` 搬进 `nodes` 数组末尾并把顶层清成 `{}`。** 根因是前端保存时 `endNode = flowNodes[END]`、`nodes = flowFrame.slice(1)`，END 天然在数组之外；点开「结束」抽屉并确认会打乱这条布局关系。点过之后再发布就报 `[结束]:无效的数据 / MFEndNode.type DATA_INVALID`。所以：
- 点确定之前先 dump 一次顶层 `endNode` 的 key 数（正常 13 个键），点完复查；变 `{}` 就是被搬走了。
- 验收 END 节点只**只读打开抽屉看红字**，不点确定；控制节点（BRANCH / CONDITION / BREAK / FOR）本来没有独立确定抽屉，分支条件走画布内联面板。
- schema 一旦被点坏，不要在这份 schema 上继续修——用生成脚本按模板重建一条干净流程（endNode 由脚本生成），再发布。

**`BRANCH.isCompleted` 恒为 `None`，这是平台常态不是缺陷。** 仓库 `fixtures/microflow/node_templates/` 下的 BRANCH 模板本身就没有 `isCompleted` 字段（模板取自活体母版）。把 `isCompleted===true` 当唯一判据会把每个 BRANCH 都报成未完成；BRANCH 的完成度看它的 `conditions[].nodes` 和 `conditions[].expression` 是否齐全。

**节点计数要递归拍平后再比，不能直接拿 `len(flowNodes)` 比 `len(dataSchema.nodes)`。** UI 把 CONDITION / BREAK 也渲染成独立卡片，后端却嵌在 `BRANCH.conditions[].nodes` 里；顶层数会小于卡片数（实测顶层 19、递归 23、卡片 24），差值是嵌套节点 + `MFStartNode`/`MFEndNode` 这类不计入 `nodes` 的端点。判一致用「递归拍平后的 nodeId 集合」对比，不要用总数。

**报告要按「已点开通过 / 已点开有错 / 没点开」三类分别计数，不要合并成「验证完成」。** 没点开的一律单列为未覆盖，并说明原因（控制在循环体/分支体内、控制节点无独立抽屉、卡片落在视口外）。`BRANCH`/`CONDITION`/`BREAK`/`END` 这类控制节点本来就没有独立「确定」抽屉（分支条件走内联条件面板），把它们算进「失败」或「通过」都是假数据。

