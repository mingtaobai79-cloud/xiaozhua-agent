# 踩过的坑 / 错误教训

> 由 SKILL.md 拆分而来，按需读取。

## 生成节奏验证清单（每批完成后逐项过）

- [ ] 每个节点在业务上有存在理由，节点顺序能跑通（不是「查询完立刻删除」这类拼装）
- [ ] 出参引用的变量/对象确实被前序节点赋值过，不是空壳
- [ ] 6 组合矩阵匹配：CUSTOM 无节点链、事件/定时无出入参、nodeId 前缀跟类型走
- [ ] CUSTOM + MANUAL 的 trigger.nodeId=MFStartNode、nodes=[]、有 input/output
- [ ] SERVICE + MANUAL 才有节点链，trigger.nodeId=MFStartNode
- [ ] trigger.output 含 inApp:true + hasPagination:false
- [ ] 节点内 CONTEXT_VARIABLE/selectParam 的 outputName == 回读后的前序节点输出名
- [ ] MQ 监听 eventDataFullName 不带 UDC_..._MQ 前缀
- [ ] checkSchema errors=0
- [ ] SearchDetection ERROR=0（sleep 3-4 秒再读）
- [ ] 用户前端抽检红点

**全节点闸门回归测试在 `tests/test_microflow_all_nodes.py`**：24 类节点（26 个节点）+ 真实出入参（前序输出→后序引用）+ 表达式（FOR.forEnd 用 `roundOffFloor` 函数、BRANCH 条件比较、CHANGE_VARIABLE 算术）+ 业务逻辑（RETRIEVE 查单条→CHANGE_ENTITY 更新、FOR 套 BREAK/CUSTOM_ERROR、BRANCH 分流），断言 validate_schema/validate_for_submit/run_gates 三道闸门全 0 错误。改生成器（build/expression_fill/gates/constraints）后跑它回归：`python tests/test_microflow_all_nodes.py`。

## 错误教训（v8 为何全错，别再犯）

v8 把 CUSTOM 当 SERVICE 用，给它加了节点链 + 出入参，也给事件/定时加了出入参——三个致命错误全来自**忽略反编译权威事实** `trigger-and-type-mapping.md`，只凭上一轮拼 JSON 的经验。正确做法：生成前必读 `facts/udc/microflow/trigger-and-type-mapping.md` 的 6 组合矩阵，逐条对照 nodeId/节点链/出入参。

- **SERVICE+MANUAL 的 endNode 必带 `value`（SelectParam 引用最后一个节点出参）+ `mappingType:"value"`**：无节点链时 endNode 不需要 value（CUSTOM 无节点链就是这样）。有节点链但 endNode 缺 value → check 报 `root.endNode.value.value` PROPERTY_IS_REQUIRED。结构照原生样本 MFSERVICEHbICrp 的 endNode。
- **本地 dev（localhost:3000）cookie 过期（TK_EXP 过期）时**：浏览器会跳 `/login/`，接口返回 403（不是 401）。CDP `Network.getAllCookies` 重拿无效（还是旧 token），刷新页面也不续期。必须让用户在浏览器重新登录 `/login/`，登录后再 `Network.getAllCookies` 导出。test2 的 `shared-credentials/ctp-user-login.json` 只适用 test2 环境（lowcode-test2.<客户组织>.com），对 localhost:3000 无效。

## 坑

- **响应体不能在 CDP 回调线程里取**：`Network.loadingFinished` 在 WebSocket 回调线程分发，在该回调里同步调 `Network.getResponseBody` 会**死锁**（命令等自己所在的事件循环返回）。回调里只登记 `n["_needBody"]=True`，主线程事后 `fetch_bodies()` 批量补取。另：`Network.responseReceived` 只给 status，不给 body；要 body 必须等 `loadingFinished` 再取。
- **网络过滤不要只收 `/service/udc/`**：保存链路里还有别的 service 接口会被漏掉。收 `/service/` 或 `graphql`，再排除静态资源扩展名（`.js/.css/.png/.jpg/.svg/.woff*/.ttf/.ico`）。
- **业务事件 DTO 字段先查再映射**：`udcMicroflowSearchEventListPost` 只给 fullName，不查 SelectDtoWithAttrsGet 就拼映射必类型不匹配。事件对象字段名是**英文驼峰**（如 `eventCode`/`bizKey`/`remark`），不是中文拼音（`beizhu`/`shiwubianma`）——猜拼音字段名 check 能过（结构对）但前端显示成完整路径/失效。字段用 `udcMicroflowFindCustomDtoPost`（body `{appId,appName,dtoFullName,needChildren:false}`）查 `content.attributes`（dict，key=真实字段名，value 带 caption/dataType/javaType/customs.id）。
- **`udcMicroflowFindByIdGet` 的变量类型是 `udcMicroflowFindByIdGetInputPath`，参数名是 `path:` 不是 `body:`**：写成 `udcMicroflowFindByIdGet(body:$p)` 不会报错，只会返回空——于是误判成「流程不存在」。正确形态 `query g($p: udcMicroflowFindByIdGetInputPath){ data0: udcMicroflowFindByIdGet(path:$p){ code message data { content } } }`，`variables={"p":{"id":"<mid>"}}`。同理 `udcMicroflowSearch` 用 `body:`，两者别混。
- **页内 `fetch('/service/udc/graphql')` 常返回 `{}`（被拦截或未带完整头）**：要读 dataSchema 就在 `CdpClient` 上 `Network.getCookies` 取 cookie，再本机 `urllib` 直发同一个 endpoint（带 `Cookie` 头）。比在 tab 里跑 async fetch 稳定，也不受 DevTools 占用 tab 的影响。
- **checkSchema 过 ≠ 前端合法**：前端绑定字段错（title/simple）检测根本不报；生成后必须抽查前端回显。
- **CDP 9250 断连时**：9222 主调试口仍可用；tab 内 `awaitPromise` fetch 可能整体挂起（DevTools 占用 tab、promise 不回），改走 CDP `Network.getCookies` 取 SY_ACCESS_TOKEN 后本机直发请求（带 Cookie 头过 SSO 校验，BOOT_1006=未带 cookie）。多 tab 时先逐个 `Runtime.evaluate("1+1")` 探活（被 DevTools 占用的 tab connect 成功但 recv 挂起）。
- **403 Forbidden 先查 token 是否过期，别误判为接口错误**：读 cookie 的 `TK_EXP`（秒级时间戳）和当前 `time.time()` 比，过期了浏览器会跳 `/login/`。本地 localhost:3000 dev 环境过期只能用户在浏览器重登（test2 的 shared-credentials 是 lowcode-test2.<客户组织>.com 另一套环境，token 不通用，别拿它续本地）。刷新页面不会续期，token 未变。批量生成前先探活 cookie 再跑，避免跑到一半 403 中断留下半批。
- **MQ 的 eventDataFullName/javaType 必须是 DTO 表的真实 fullName**（`com.seeyon.<app>.dto.YsEvtData2`）——用 `udcDataTransferObjectSearchListPost` 查。手拼 `8704025620829192834.dto.YsEvtData2`（漏 `com.seeyon.`）同样报「消息的参数已被删除」。带 `UDC_..._MQ.` topic 前缀也报。
- **事件唯一占用会串场**：同一事件只能一个微流程订阅。批量生成时先用 FilterEventPost 拉空闲事件池，分配时去重（已占用事件会从返回里消失，但检测仍会报 EVENT_USED）。
- **批量删旧用 `name` 前缀匹配后复核**：删除循环后必须重新 Search 复核数量与分组计数，删多/删漏（正则分组写错）都发生过。清理「我做过的测试数据」时，用户点名的保留项要按 **id 精确排除**，待删项也写成**显式 name 黑名单**而非宽泛前缀（`gen*` 前缀会连带删掉用户手工建的同类流程，删前把全量清单打给用户确认）。业务正式流程（带 `1.0/1.1/1.4…` 版本号的那批）一律不动。
- **trigger.output 必含 `inApp:true` 和 `hasPagination:false`**：前端「选择参数」树按这两个字段构建入参对象子节点，缺失时过滤条件右值下拉展不开「ID」等字段（用户只能手填文本）。对照原生流程（如 SyncNowData）的 output 补齐。
- **节点引用必须随 trigger 重建同步**：RETRIEVE 过滤条件的 CONTEXT_VARIABLE 内嵌 JSON 里的 `outputName/key/id/path` 指向入参节点名；重造 schema 时 trigger.output.name 会变，节点引用不同步 → 前端一致检测报「前序节点发生变更请重新选择(ID)」（checkSchema 不报）。重建后必须重写所有 `_FLOW_IN*` 引用为当前 output.name 及配套 path（DTO fullName 去点+字段名）。
- **字段级 SelectParam 结构（attrs 映射/条件右值引字段时）**：`{id:"<DtoFullName>.<field>", javaType:同型, dataType:同型, field:字段名, dto:"_<field>", position:"children", path:<DtoFullName去点><field>, outputName:<节点出参名>}`——对象级引用（javaType=DTO 全名）对 STRING 字段必报「不是文本类型」（CheckUtils NOT_STRING 判定链反编译实证）。
- **事件/MQ 监听 trigger.output 的 id 用真实数据 DTO**：EVENT=`messageInfo.eventDataFullName`，MQ=FilterMqPost `contentDto.type`；javaType 用 `eventMfCustomDtoName`/MQ 别名。output.id 写错（如复制了实体 DTO）→ 报「消息的参数已被删除」。MQ 的 messageInfo 还须补 `eventMfCustomDtoName/currentId/topic`（接口现值）。
- **checkSchema 报「订阅的业务事件已被其他微流程使用」= 事件唯一占用**：换未占用事件重建，不要反复重试同一事件。
- **删除单个节点不是 CDP 点 X 按钮**：节点 X 按钮（hover 显示的 `span.remove-btn`，antd Tooltip「删除」）的 onClick 是 antd fireEvents 多层包装，CDP 点击和直调都进不到删除逻辑，后端也没有删单个节点的接口（删除本质是前端把节点移出 dataSchema 再整包保存）。正确做法是 dispatch Redux action `udc-microflow-edit/removeNode`（payload `{nodeId}`）。清理测试节点时直接 `udcMicroflowDeletePost`（参数 `{id}`）删整条测试流程更省事。
- **模板基座残留键会把校验器带进错误分支**：`fixtures/microflow/node_templates/*.json` 的骨架键是前端新建态形态，残留 `otherType`/`nodeRemark` 会让校验器按 OTHER 分支校验，value/mapping 等合法形态全被 DATA_INVALID 误杀。给模板补形态前先核对它的键集；构造器分支显式设置的键（如 OTHER 形态的 otherType）由分支负责，模板不该预置。
- **checkSchema 错误 path 的段名是校验模板的槽位名，不是节点上的键**：`创建变量.mapping.value.type` 里的 `mapping` 指「赋值方式」这个槽位（value/mapping 形态都报它），不等于节点上真有 `mapping` 键。按字面去节点上找同名键会白找。
- **DATA_INVALID 定位用嫁接二分，别逐键猜**：把语料真节点原样嫁接进最小流（把 RETRIEVE 节点的 nodeId/outputName/id/javaType 改成语料引用的目标），checkSchema——过了就证明校验器与形态没问题，是我的节点有差异；然后递归 diff 两节点（跳过值本该不同的键：nodeId/caption/title/desc/output/app/structure 的值），跳过项的**键集**单独 diff。这比盯着错误信息猜字段快一个量级。
- **实体型「赋值方式」键位纪律**：value（对象引用）/mapping（自动映射）形态连 `attrs=None` 都不能带（键存在即触发另一分支校验）；`otherType` 仅 OTHER 形态可带。构造器分支里用 `pop` 删键而不是赋 None。
- **流程 name/caption 的 API 规则**：name 必须字母开头纯字母数字（`UDC_ENTITY_0001`），caption 全应用唯一（`UDC_MICROFLOW_0002`）——调试脚本统一 name/caption 带时间戳，且失败路径要自动删流程，否则下次重跑撞唯一键。
- **后台 tab 画布不渲染 ≠ 验证失败**：浏览器窗口在后台时设计器画布懒渲染（`.node-body=0`），prove 的 UI 层会误报「页面未渲染出节点」。检查按钮真点（`run_check`）+ 应用检测明细（`detection_mine=[]`）是等价证据；要目检抽屉就把 tab 激活到前台或截图确认。
- **构建进度 91% 可长期停留（Java 编译段），进度回落到 18/82 = 服务端自动重开新一轮**，不是失败。判失败只认最终 `state=FAIL`，轮询用后台进程别占前台（300s 超时会杀掉轮询现场）。
- **调试探针脚本不带真实 app/组织字面量**：`scratch/*.py` 硬编码 `datamigration<真实id>`/`<客户组织>` 会被脱敏测试拦死（它扫一切入库路径）。验证流的 dataSchema 归档前把真实字面量替换成标准假 app（`datamigration9000000000000000001`），探针要么收容 `_attic_pending/` 要么用 env 变量注入。

