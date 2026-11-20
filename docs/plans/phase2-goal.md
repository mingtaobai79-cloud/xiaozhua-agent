# GOAL · 阶段2：平台接口面落到应用文档

**立此为目标，逐项验收。白明涛 2026-11-20 拍板。**

---

## 一句话目标

把 176 个构件、24,618 个类里的**可调用接口**，按 115 个应用整理成
「入参是什么 / 返回什么 / 干什么 / 落哪张表 / 怎么调」，让 Agent 拿到业务需求时
**不用读 jar、不用翻源码**，查文档就能直接写出调用代码。

---

## 交付物

对每个应用（或每个标品组件），产出 `core/facts/modules/{分组}/{应用}/README.md`，固定四段：

```
1. 构件清单      —— 这个应用由哪几个 jar 组成，各层职责
2. facade 层     —— AppService 接口逐个列：方法名 / 入参 DTO / 返回类型 / 干什么
3. biz 层        —— 实现最终做什么（校验/事务/落哪张表/发什么事件）
4. web 层        —— REST 路由 + 请求体 + 响应体
```

**biz / web 的要求按用户原话放宽**：

> 「biz web 你知道接口的入参以及做什么的就可以」

即 biz/web **不必逐方法穷举**，只要写清「这个入口的入参 + 它做什么」。

---

## 范围（全量，不挑不拣）

| 批次 | 应用 | 类数 | 理由 |
|---|---|---:|---|
| A | organization | 1,103 | 所有业务都要找人、找部门 |
| B | bpm | 3,415 | 流程发起/审批/事件 |
| C | ctp（affair 481 / user 1,069 / message 205） | 2,098 | 事项、用户中心、消息 |
| D | cip（connector 439 / capability 1,448） | 4,166 | 连接器、外部集成 |
| E | udc（microflow 368 / dataflow 112 / entity 185） | 3,345 | 自定义对象、微流程、数据流 |
| F | boot 组件（file 89 / enums 51 / extmetadata 102 / datasource 29 / mybatis 138 / dynamicsql 42） | 3,678 | 基础能力 |
| G | cdp 2,867 / portal 675 / m5 473 / app 1,539 | 5,554 | 数据、门户、移动、通用 |
| 合计 | | 24,618 | 全覆盖 |

---

## 关键约束（硬性）

1. **禁止编造**。每个方法的入参/返回必须来自字节码索引，标 `VERIFIED_STATIC_BYTECODE`。
2. **「干什么」允许推断，但必须标注**。方法名推不出业务语义时写 `UNVERIFIED`，不猜。
3. **落表必须来自真实证据**（mapper/SQL/实体注解），推不出就留空，不填「大概落 xxx 表」。
4. **不做客户诊断**。只写平台机制，客户数据一律不进来。
5. **每个批次必须跑自证脚本**，退出码 0 才算完成。
6. **不许用脚本返回值冒充验收**：自证要读回磁盘文件内容比对。

---

## 验收标准

### 单批次
- [ ] `README.md` 四段齐全
- [ ] facade 层方法数与索引中该应用 `*.api.*` + `*.appservice.*` 接口方法数一致
- [ ] 每个方法都有：入参类型 + 返回类型 + 「干什么」或 `UNVERIFIED`
- [ ] 文档里出现的每个类名都能在索引里查到（无拼写错误）
- [ ] 自证脚本 `sys.exit(1)` 闸门，实跑退出码 0

### 全量
- [ ] 115 个应用目录全部有 README
- [ ] 抽样 30 个方法，文档写的入参 == 字节码实际入参
- [ ] 文档里没有出现索引里不存在的类名（0 个孤儿引用）
- [ ] `verify_all_apps.py` 退出码 0

---

## 反例（这些做法算失败）

- ❌ 把域名当业务名写「组织管理」而不列具体方法
- ❌ facade 层写「提供人员和部门能力」——这不叫文档，叫废话
- ❌ 落表写「写入组织表」——要写真实表名
- ❌ 用 `TODO` / `待补充` 占位后宣称完成
- ❌ 自证脚本只 `print` 不 `sys.exit`
- ❌ 拿 jar 里不存在的方法名凑数

---

## 完成定义

Agent 拿到「给订单审批抄送部门负责人」这类需求时，能只查 `core/facts/modules/`
就写出：

```java
// 1. 找部门负责人 —— organization 文档给出确切方法和入参
// 2. 发起流程 —— bpm 文档给出 BpmAppService#send 的入参 DTO
// 3. 生成待办 —— ctp/affair 文档给出返回 id 的方法
```

**不需要打开任何 jar。**

---

## 进度

### 已完成（阶段2 主体）

22 个模块，479 个接口 / 3,078 个方法，0 个待定语义。
`verify_all_modules.py` 退出码 0，接口集合与索引完全一致。

| 批次 | 模块 | 接口 | 方法 | 状态 |
|---|---|---:|---:|---|
| A | organization | 55 | 421 | ✅ |
| B | bpm | 39 | 278 | ✅ |
| C | ctp-affair / ctp-user / ctp-message / ctp-other | 72 | 398 | ✅ |
| D | cip-connector / cip-capability / cip-provider / cip-other | 143 | 994 | ✅ |
| E | udc | 67 | 555 | ✅ |
| F | boot | 47 | 141 | ✅ |
| G | cdp / app / portal / m5 / ocip | 56 | 291 | ✅ |
| H | ai / devops / gateway / maven / mymojo | 0 | 0 | ✅（已说明无 facade 的原因）|

### 未完成（阶段3、4）

- **落表**：22 个模块全部标 `UNVERIFIED`。取证路径已写在每个 README，未执行。
- **REST 路径**：全部标 `UNVERIFIED`（除 udc 的 deploy-normal 有历史实测证据）。
- **93 个应用目录**：只有结构性 README，还没写接口表（这些应用本身没有 api/appservice 接口，
  或是 boot-starter 组件，接口面已包含在 boot 模块里）。

### 新增工具链

```
dump_facade.py         按域/子包抽 facade 签名
dump_facade_multi.py   多子包合并
gen_app_doc.py         生成 facade 表（名称拆词 + SPI 规则）
gen_module_readme.py   组装四段 README
gen_all_modules.py     批量生成 22 模块 + 汇总待定语义
verify_module.py       单模块自证（7 项）
verify_all_modules.py  全量自证（逐模块 + 跨模块对齐 + 域覆盖）
notes/*.json           678 条手工语义注记
notes/*.custom.md      手工补充片段（概念表/调用链/边界）