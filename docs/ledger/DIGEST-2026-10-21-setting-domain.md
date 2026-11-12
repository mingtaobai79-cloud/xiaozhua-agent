# 会话续接摘要 · 设置域推进（2026-10-21）

> 用途：上一个长会话（上下文 886k，LCM 压缩被 store_id 交错卡死）的续接件。
> 只记「下一轮开局必须知道的东西」——目标、规矩、已完成、缺口、下一步。
> 细节一律指向仓内事实格/契约/skill，本文件不复制它们。

## 一、当前任务线

**目标**：让 AI 以用户身份、通过真实前后端协议操作UDC 设计器，
把「应用设计 → 设置」域各 tab 全部打通并沉淀回 `xiaozhua-agent`。

**本轮范围**：设置域。已完成 8 个 tab：

```
枚举 / 自定义对象 / 选项集 / 参数 / 流水号 / 导入导出模板 / 二维码 / 字段集 / 扩展实体
页面模板、外框模板 = 明确不在本域处理（页面/外框建完后自动同步过来）
```

## 二、用户订下的规矩（跨会话有效）

| 规矩 | 内容 |
|---|---|
| 协议优先 | 前台接口基本是 **GraphQL**。后台能通就不必前台一个个点；**以后台 JSON 为先**，实在不行再反编译 jar 读 DTO |
| 抓包工具 | 要抓接口就用 **rea**（`capture_browser_scenario` / 前端点击后抓）；rea 在字段集面板会 timeout，改用 CDP `performance.getEntriesByType('resource')` + 页面内 fetch 拦截 |
| 类型必须全覆盖 | 「任何数据类型的格式、和类别你都得试一下，你看看他是怎么组装的」——不许验通一条就报打通 |
| 换样本复验 | 对象/选项集要**换一个来源**（例如都选 bpm 引擎下的）再验一遍，防止只在一个上下文里碰对 |
| 控件不能一刀切 | 除文本外其他类型的字段不一定是单行文本，**不能全用 `Input`** |
| 沉淀去处 | 结论 → `core/facts/`；构造/校验器 → `components/`；契约 → `registry.py`；使用说明 → Hermes skill `xiaozhua-udc-setting`。**只写进 skill 不写进仓库 = 没沉淀** |
| 汇报口径 | 分清 LIVE PASS / LIVE / VERIFIED_STATIC_BYTECODE / UNVERIFIED / VACUUM；`BOOT_0000` 不等于成功，必须 DB 或接口回读 |
| 客户信息 | 客户实体/页面/微流程明细不进长期事实库；证据在仓外 `xiaozhua-customer-evidence/` |

## 三、本轮已完成（全部有 commit + 事实格 + 落位测试）

```
ee4b153b  widgetConfig 必须按 dataType 给，不能全用 Input
d7e60e34  表达式组件链路全抓到；sysvar 纯文本导致白屏已修
7859ef45  表达式三段链打通 —— design 可写，runtime 服务端生成
5538a343  字段集演示集 —— 1 枚举 + 1 实体 + 6 文本（表达式/函数/校验各异）
0a9822b2  CTPENUM 字段必须传三个关联槽位（用户抓包纠正）
eddb68a2  字段集 18 种类型 + 20 项字段配置、扩展实体 10 种类型全量实测
fc12affa  字段集/扩展实体全打通 —— 发现「父 REST + 子 GraphQL」混合协议
28e85d9f  二维码/流水号按落位规范固化（九段式事实格 + 契约 + 强校验）
84566521  二维码三种类型全部实测通过
9b6152d9  导入导出模板支持关联实体字段展开（levelPath 两层）
b74ee3d6  导入导出模板 + 二维码打通（REST，反编译定字段）
4e43ff41  流水号打通 —— 反编译 SerialSchemeDto 拿到真实字段名
f8229782  清空选项集/参数旧数据，重建两套验收样本
ade6a152  选项集/参数打通，流水号读面 LIVE 写面 PARTIAL
```

验收基线：`pytest tests -q` → **1716 passed / 22 skipped**（2026-10-21 实测）。

## 四、★ 本轮最重要的一条结构发现（下个 tab 开局先看）

**同一域内「父」和「子」可能是两种协议**：

```
父（壳）  REST     create/update 只改壳自身，不处理子集合
子（明细）GraphQL  真正的子项写入入口
```

| 域 | 父 REST | 子 GraphQL |
|---|---|---|
| 字段集 | `POST /service/udc/attributeSet`（驼峰） | `udcEntityAttributePost` / 改 `udcEntityAttributeUpdatePost` |
| 扩展实体 | `POST /service/udc/scalability-option`（连字符） | `udcScalabilityPost` |
| 自定义对象 | `udcDataTransferObjectUpdatePost` | `udcDataTransferObjectUpdateDtoPost` |

父 DTO 里带了子集合字段 **不等于** 该接口消费它 —— 4+2 种变体全回 `BOOT_0000`
但子表零行（静默忽略）。判据只能是**回读子表行数**，不是 `code=BOOT_0000`。

## 五、本轮新发现的三个坑（已写进事实格）

1. **`defaultValueSystemVariable` 传纯文本 → 整个字段集面板白屏**
   前端对它 `JSON.parse`。合法形态是 ExpressionSaveDto：
   `{"resultTypeInfo":"ENTITY","schemas":[],"tokens":[{"value":"system.currentUserId",...}],"isMultiSelect":false,"terminalSupportType":"BACKEND"}`
   提交前必须过 `validate_sysvar()`。

2. **`expressionRuntimeData` 客户端写不进去**（7 种形态全试，只有 null/`""` 被接受）
   runtime 由**代码生成阶段服务端写入**，客户端只写 `expressionDesignData` + `calculate=COMPUTE`。

3. **`udc_attribute` 没有 `attribute_set_id` 列** —— 字段挂父靠 `source_id` + `source_type=1`（ATTRIBUTESET）。
   照 `attribute_set_id` 查会 `Unknown column`。

## 六、本轮订正掉的错误口径（2026-10-21 复核）

| 旧说法 | 实测 |
|---|---|
| 「本 app 参数总数（is_delete=0）：40」 | `is_delete=0` 只 **3** 条，`is_delete=1` 40 条（`zxjParamProbe` 自己也已删） |
| 「选项集批量删除 = 逻辑删除 `udc_enum.is_delete=1`」 | `udc_enum` **无 `is_delete` 列**，删除语义 UNVERIFIED |
| 契约里 `widgetConfig` 示例统一 `Input/Input` | 只对 STRING 成立；其余按 `DEFAULT_WIDGETS` |

## 七、缺口与下一步

**设置域内还剩**：

```
页面模板 / 外框模板   不在本域处理（页面建完自动同步过来）
选项集：更新/删除接口、批量删 content=0 语义        UNVERIFIED
参数：删除接口、paramGroup/type 语义、各类型约束值域  UNVERIFIED
二维码：update 系列                                UNVERIFIED
导入导出模板：update 系列                           UNVERIFIED
表达式：paramType=ENTITY 的 schema、函数 token 组装、
        「验证」按钮行为、对话框确认后落库字段        UNVERIFIED
```

**设置域外**（`capability_report.py --check` 报的缺口）：
菜单 / 规则 / 流程 / BI / 栏目 / 角色 六个域**缺事实格**；应用域「有契约无事实格」。

**设置域落位补完项（本轮已做）**：选项集/参数/导入导出模板/表达式组件
四份事实格此前**没在 `core/facts/INDEX.md` 登记**（= 检索不到 = 等于没写），
2026-10-21 已补登；四者仍缺 `docs/operation-contracts/udc/setting/*-contracts.md`
独立契约件（operation 已在 `registry.py`，契约件可后补）。

## 八、开局命令

```bash
cd <XIAOZHUA_AGENT_ROOT>
.venv/Scripts/python.exe -m pytest tests -q --tb=no        # 基线 1716 passed
.venv/Scripts/python.exe tools/core/capability_report.py    # 九域落位 + 契约数（116 条/写面 32）
.venv/Scripts/python.exe tools/core/capability_report.py --check   # 缺口 → 退出码非 0

# 只读 DB（凭据从 skill .env 读，不入库）
# .env 路径：skills/seeyon/01-platform/xiaozhua-low-code-environment/.env
# 关键 schema：udc_test2（元数据）/ ctp_user_test2 / organization_test2
```

CDP：Edge 9222 起不来时用 9231（当前设计器标签页 `BCD2D805…`，appId=8704025620829192834）。
