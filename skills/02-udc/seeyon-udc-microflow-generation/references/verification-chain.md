# 生成→交付的自证链（prove）

`components/udc/microflow/live/verify.py`

## ⛔ 先确认 CDP 端口：9222 有登录态，9333 没有

`BOOT_1006 token黑名单` 出现时，**先查端口，别判登录过期**：

```
port 9222: cookies=88  SY_ACCESS_TOKEN 有（.<客户组织>.com / test2 / localhost）
port 9333: cookies=75  SY_ACCESS_TOKEN 无    ← 页面能开，API 全 1006
```

9333 上页面 title 显示「数据迁移」看起来正常，但 API 全挂。
**「页面能打开」不能证明「登录有效」**。

取 cookie（`document.cookie` 读不到 httpOnly，返回空串）：

```python
from providers.cdp import CdpClient
c = CdpClient(9222, allow_network=True, timeout=20); c.connect()
cs = (c.send('Network.getAllCookies') or {}).get('cookies') or []
ck = '; '.join('%s=%s' % (x['name'], x['value'])
               for x in cs if str(x.get('domain') or '').endswith('<客户组织>.com'))
```

## prove(app_id, mid, host, cookie)
一条命令跑完四道校验，返回 `{publish, ui, param_names, detection_mine, ok}`：

| # | 检查 | 取数位置 | 拦什么 |
|---|---|---|---|
| 1 | 发布 checkSchema | publish 返回 `errors[]` | 结构/必填/类型（单流程） |
| 2 | UI 红节点 | redux `microflowEditorReducer.flowNodes[].isCompleted === false` | 设计器才认的未完成态 |
| 3 | UI 必填红字 | 逐节点开抽屉读 `textContent`，匹配「所选数据已失效/请重新选择/不能为空/请选择」 | 字段标识、必填下拉 |
| 4 | 入参显示名称 | PARAM 页签 `input[placeholder=请输入显示名称]` 的 value | trigger.desc 缺失（G21） |
| 5 | 应用级检查 | `udcApplicationSearchDetectionPost`，按流程名/id 过滤 | 循环内调服务、选项集缺项、生单规则映射 |

## 关键区别
- 设计器「检查」按钮 = **应用级**一致性检测（`udcApplicationDoDetectionPost` → `udcApplicationSearchDetectionPost`），
  会把用户自己的存量问题一起报出来，**不要归因到刚生成的流程**。
- 单流程 schema 校验在 publish 的 `checkSchema` 里，两者口径不同。

## UI 三个数字 ↔ detectionType（汇报两边都要取）

设计器底部面板显示「N 阻断 / N 严重 / N 警告」，
`udcApplicationSearchDetectionPost` 返回的是 `detectionType`，同一批数据的两种口径：

| UI 显示 | detectionType | 阻塞发布 |
|---|---|---|
| 阻断（红锁） | `ERROR` | **是**，构建必失败 |
| 严重（紫 ×） | 更高等级 | 否 |
| 警告（黄三角） | `WARN` | 否 |

同一时刻实测：UI `2 阻断 / 0 严重 / 13 警告` = API `2 ERROR / 13 WARN` = 15 条。

只看 API 的 ERROR 数可等价判断阻断，但**汇报时两边都取一次**——用户看的是 UI。
只报 API 数字等于替用户做了一次翻译，他没法核对。

## 阻断的典型成因：旧流程引用了失效的实体属性

```
[ERROR] 查询数据源:实体属性已更改(ID)
```

实体属性改名/删除后，旧流程里存的字段引用悬空，平台判成**阻断**，
整个应用的构建被挡（构建日志：`一致性检测未通过`）。

★ **测试流程不要发布成 RELEASE。** 字段一失效就变阻断，把整个应用的构建链拖死，
而报错只写流程名、不写「这是测试残留」，排查得从流程名反推。
验收完就删；要留就留 DRAFT。

## UI 取数的三个坑
- `document.hidden=true` 时 `innerText` 恒为空（读到 0 个节点）→ 一律用 `textContent`；
- 节点点击直调 React fiber `memoizedProps.onClick`，且写 `(() => {...})()`，否则不执行；
- 颜色判据不可用：默认分支是珊瑚红、自定义错误节点本身红色、selected 项带强调色；
  红节点只认 `isCompleted === false`（elseBranch 的 None 除外）。

## 参数名称（反复被用户指出的那条）
MANUAL 带参的真实形态：`trigger.desc == output.desc == 业务显示名`。
PARAM 页签「参数名称」绑的是 **trigger.desc**；只写 output.desc → 空黄框，
而 checkSchema / 发布 / 编译全绿。闸门 G21 已拦。

## 闸门侧同源规则
- G21 MANUAL 带参必须 trigger.desc 非空且 == output.desc；
- G22 每个节点 caption 非空、`isCompleted` 不为 False。
