# UI 验收判据 & 真跑一次（2026-10-31 实测）

## 1. 红色判据只能用 isCompleted，不能用颜色

颜色扫描在 6 条干净流程上报了 6 次假阳性：
- 默认分支（elseBranch）是编辑器固定珊瑚红 `rgb(255,120,117)`；
- `CUSTOM_ERROR` 节点本身就是红色标识；
- 高亮选中的列表项（`class=selected`）带强调色。

权威判据：

```js
appReduxStore.getState().appDesign.microflowEditorReducer.flowNodes
→ 递归 walk(node)：node.isCompleted === false 才是真未完成
→ conditions[] 里的 elseBranch 例外（isCompleted = None 是常态，941/941）
```

配合抽屉红字做文本判据（`所选数据已失效 / 请重新选择 / 不能为空 / 请选择 / 请填写`）。

## 2. verify_flow 的四个坑

函数：`components/udc/microflow/live/verify.py::verify_flow(app_id, mid, host, cookie)`

| 坑 | 现象 | 解 |
|---|---|---|
| `document.hidden=true` | innerText 恒空，读到 0 个节点 | 一律用 `textContent` |
| 拼 JS 调用 | `(i => {...})0` 不会执行 | 写成 `(() => {...})()`，idx 用字符串内联 |
| 点节点被连线层挡 | 鼠标事件不生效 | 直调 React fiber 的 `memoizedProps.onClick` |
| UI 编辑打回 DRAFT | 验完流程变草稿 | 验完必须重新 publish |

RELEASE 状态节点点不动，先点「编辑」转草稿；验收完重新发布。

## 3. 真跑链路：2026-10-31 已打通构建段（详见 seeyon-agent core/facts/udc/microflow/test-build-chain.md）

- 设计器右上「测试」= 应用测试弹窗 →「立即构建」调 `udcRuntimeDeployNormalPost`
  （deployType=RELEASE，返回 deployId）；状态轮询 `udcSandboxBuildInfoAppGet`
  （state/progress/logs，82%≈后端编译）；详细 javac 错误在 `backBuild.log`
  （`/service/udc/file/download?storageKey=compile-info/{appId}/{ts}/backBuild.log`）。
- **SCHEMA+UI+检测全绿 ≠ 能编译**：实测 DATA_MAPPING 单对象主实体上游（MASTER+parent）
  构建必炸（生成器按 List 处理），闸门 G29 拦截；数据映射只允许子表/列表形态。
- 构建成功 ≠ 有 HTTP 入口：`open_api=STOP` 的流程 `/service/{app}/microflow/{name}` 仍 404；
  RUNTIME 前置=开对外接口或绑定页面规则；运行记录在「更多→微流程运行日志」。
- 旧记录（本节下方）保留作历史：

- 设计器里**没有执行器**：「测试」弹「应用测试 / 本次发布预估 X 分 / 立即构建」；
  「页面调试(beta)」弹「会建构页面和页面规则，不适用后端服务更改」。两者都是构建入口，
  误点会触发构建，立刻点「取消」退出。
- 应用运行态网关通：`/service/{appName}/udc-runtime/data/query` 返回参数校验提示 JSON。
- 微流程不走 dynamic-rest：`/service/{app}/dynamic-rest/com-seeyon/{app}/{任意路径}`
  恒 `BOOT_4002 应用坐标数据不存在`（首段当页面坐标解析）。
- 微流程控制器不在本应用 runtime：`/service/{app}/udc-runtime/udc/{MicroFlowAppService|
  CustomMicroFlowAppService|MicroFlowController}/...` 全 404 Whitelabel；平台级
  `/service/udc-runtime/udc/CustomMicroFlowAppService/{name}` 返回「udc-runtime 服务不存在」。
- 推断（未证）：发布时 `restApi=DISABLED / openApi=STOP`，没对外暴露接口，故无 HTTP 入口。
- **不要再拼路径试**：十几种组合全被 4002/404 挡回，属于无效探测。要拿到真实 URL
  （服务定义/接口文档），或先开对外接口再构建后观察。
- 写路径同理受页面约束：`dynamic-rest/.../{pageUrl}/.../create` 需要 CRUD/DETAIL 页注册，
  无页面则 `BOOT_4002`；GraphQL 数据面 mutation 不存在（7 候选全 FieldUndefined）。
  读可用：`/service/{app}/udc-runtime/data/query {data:{appName, entityFullName, dataId}}`。

## 4. 子微流程（SUB_MICROFLOW，251 实例）

```json
{"actionType":"SUB_MICROFLOW","type":"ACTIVITY",
 "mfService":{"id","appId","caption","hasInput","hasOutput",
              "input":{DTO},"output":{出参},"method":"POST",
              "name":"MFSERVICE...","path":"/microflow/MFSERVICE...",
              "triggerType":"MANUAL","type":"SERVICE"}}
```

标品子微流程可被调用，生成侧无障碍；构造器未写（要拉目标流程的出入参 DTO 才能拼 mfService）。
`path=/microflow/{name}` 这个形态与「对外接口 URL」很可能是同一套命名，拿到真实 URL 后可互证。

## 5. 定时最小周期

`cycleType=SIMPLE` + `rotationType=MINUTE` + `value="1"` → 每分钟。可用于「让定时自己跑起来」
这类验证，但**不要在业务数据上跑会改数据的每分钟任务**。
