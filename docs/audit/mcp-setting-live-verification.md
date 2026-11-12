# MCP 工具面 LIVE 验证记录（setting + rule 域）

> 目的：证明「能出 body」的工具在真实平台上也**能落库**，而不只是参数拼得对。
> 执行日期：2026-11-10　环境：test2（`<host>`）　应用：`<appId>`

## 一、为什么要做这次

之前的工具面里，`setting` 域 18 个工具只验证过「返回结构正确」，
从未有一次真实提交。这类**假阳性**最危险：工具返回 `{ok: true, body: {...}}`，
用户以为成功了，实际平台可能整条拒掉。

本次挑最简单的一条（选项集分组）跑完整闭环：**建 → 回读 → 删**。

## 二、执行路径

用 CDP 让页面自己发请求（`fetch(url, {credentials:'include'})`），
不导出 cookie、不重放 token —— 页面自带身份。

```
浏览器   Chrome/157，独立调试端口 + 独立数据目录
页面     <host>/main/portal（用户已登录）
脚本     scratch/page_api.py::PageApi
```

## 三、五步实测结果

### ① 只读探针：取 appGuid

```
POST /service/udc/graphql?udcApplicationDetailGet
variables: {"p0": {"id": "<appId>"}}
```

响应 `status=200`，`code=BOOT_0000`，`message=SUCCESS`
→ `guid = <appGuid>`，`name = <appName>`，`caption = 数据迁移`

**结论**：cookie 有效，网关前缀对，GraphQL 封装对。

### ② 只读探针：选项集全树

```
POST /service/udc/graphql?udcUdcEnumCategorySelectCategoryAndEnumPost
variables: {"p0": {"appId": "<appId>"}}
```

`status=200`，`len=2384`（已有 1 个分组 + 1 个枚举）。

**结论**：读面通，可作为回读判据。

### ③ 创建（真写）

```
工具   seeyon_option_set_category_body(appId, appGuid, "ZzTestCat", "探针测试分组")
接口   POST /service/udc/graphql?udcUdcEnumCategoryPost
```

生成的 body：

```json
{"appId":"<appId>","appGuid":"<appGuid>","name":"ZzTestCat",
 "caption":"探针测试分组","orderNo":1,"parentId":"0","description":""}
```

响应 `BOOT_0000 / SUCCESS`，`content = -7006800889046832071`（新行 id）。

### ④ 回读（关键判据，不认上一步返回值）

再调 ②，在返回树里定位新 id，逐字段比对：

| 字段 | body 传入 | 回读值 | |
|---|---|---|---|
| id | — | `-7006800889046832071` | ✓ 与创建返回一致 |
| name | ZzTestCat | ZzTestCat | ✓ |
| parentId | 0 | 0 | ✓ |
| orderNo | 1 | 1 | ✓ |
| appId | `<appId>` | `<appId>` | ✓ |
| description | `""` | `""` | ✓ |
| createTime | — | `1794300830000` | ✓ 真实落库时间戳 |
| enums | — | null | ✓ 无子枚举 |

**结论**：`seeyon_option_set_category_body` 产出的 body 平台接受且字段无失真。**LIVE PASS**。

### ⑤ 删除（清理 + 顺带验删除面）

```
接口   POST /service/udc/graphql?udcUdcEnumCategoryDeletePost
入参   {"id": "-7006800889046832071"}       ← 只要 id，不需要 appId
响应   BOOT_0000 / SUCCESS，content = 1
```

回读确认：`ZzTestCat` 与 id 均消失，树 `len` 由 2384 → 2061。

**结论**：删除真生效。测试数据已清理，环境与测试前一致。

## 四、这次证实了什么

```
① setting 域 body 构造器（至少选项集分组一支）产出的结构，平台接受
② appGuid ≠ appId，且 appGuid 取法 udcApplicationDetailGet → content.guid 正确
③ BOOT_0000 + content 非零仍不等于落库成功 —— 必须回读
④ udcUdcEnumCategoryDeletePost 入参只需 id，不需要 appId
```

## 五、还没证实的

- `setting` 域另外 17 个工具仍只验证到「结构正确」一层
- `entity` / `application` / `rule` 三个域**一次真提交都没跑过**
- `rule` 域的 `entity_rule_publish` 有完整判据（checkSchema 通过才 create），但从未真跑

## 六、复现方法

```python
import page_api                          # scratch/page_api.py
p = page_api.PageApi(9333)               # 已登录的调试实例
r = p.api("<host>/service/udc/graphql?udcApplicationDetailGet",
          {"method": "POST",
           "headers": {"Content-Type": "application/json"},
           "body": json.dumps({"query": q, "variables": {"p0": {"id": app_id}}})})
```

★ 不要让脚本自己发 HTTP 带 cookie —— 用页面 fetch，浏览器自己带身份。
★ 判据永远是**回读**，不是返回值。

---

# 第二部分：rule 域（实体规则）

## 起因：这里抓到一个真 bug

`seeyon_entity_rule_body` 生成的 body 里 `type` 写的是 `"ENTITY"`，
平台直接回：

```
BOOT_3002  No enum constant
com.seeyon.udc.common.enums.MicroFlowTypeEnum.ENTITY
```

真值是 `core/facts/udc/microflow/all-nodes-coverage.md` 第 11 条：

```
MicroFlowTypeEnum   SERVICE(0) FRONTEND(1) ENTITY_RULE(2) CUSTOM(3) FUNCTION(4)
```

**正确答案是 `ENTITY_RULE`。**

为什么一直没被发现：旧测试只断言 `type` 这个字段**存在**，没断言值。
字段在、值为错 → 测试绿、平台拒。这正是「假阳性」的教科书形态。

已修，并加回归守卫 `test_entity_rule_type_is_entity_rule_not_entity`。
反向验证：把 `ENTITY` 注入回去，该测试立刻红（1 failed / 117 passed），还原后绿。

## 修复后的实测

### checkSchema

```
POST /service/udc/microflow/checkSchema      body = dto 本体（不走 GraphQL 封装）
→ status=200  BOOT_0000  content={check:true, errors:0, errorMessage:null}
```

### create

```
POST /service/udc/microflow/create
→ BOOT_0000  content = -4544658532880917930
```

### 回读（判据）

```
接口  udcMicroflowSearchEntityRulePost
入参  {"pageInfo":{"pageNum":1,"pageSize":20},"params":{"sourceId":"<entityId>"}}
```

★ 入参形态是 `{pageInfo, params:{sourceId}}`，不是 `{appId, sourceId}` 也不是
`{appId, entityId}` —— 后两种都回 `BOOT_1001 参数错误`。

回读到的行：

```json
{"id":"-4544658532880917930","name":"ZzTestRule","appId":"<appId>",
 "caption":"探针规则","creationMethod":"MANUAL","type":"ENTITY_RULE",
 "triggerType":"MANUAL","groupType":"VALIDATE","description":"",
 "orderNum":161,"state":"RELEASE..."}
```

`groupType=1` → 回读 `VALIDATE`，映射正确。

### 删除

```
接口  udcMicroflowDeletePost
入参  {"id":"-4544658532880917930"}      ← 只要 id
→ BOOT_0000  content=true
```

二次删除同一 id 回 `BOOT_4002 数据不存在或无权限查看` —— 这本身就是删掉了的旁证。
回读列表 `len` 545 → 124，名字与 id 均消失。

## rule 域结论

```
entity_rule_body    body 结构正确（type 修好后）     LIVE PASS
checkSchema 判据     content.check==true && errors==0  正确
create              BOOT_0000 + 回读一致            LIVE PASS
delete              BOOT_0000 + 回读消失            LIVE PASS
```

## 顺带暴露的设计问题

`seeyon_entity_rule_publish(host, cookie, dto)` 要求调用方把 **cookie 字符串**传进来。

但按红线，token/cookie 不应该被导出到本地再重放 —— 它就是这个用户的身份。
本次验证全程用的是「页面自己 `fetch(credentials:'include')`」，cookie 从未离开浏览器。

也就是说：**这个工具在遵守红线的前提下用不了。**

修法有两条：
- 让它接受一个「由宿主提供的发送回调」，而不是 cookie
- 或者提供 `via_cdp(port)` 模式，内部走页面 fetch

目前未改，先记录。

