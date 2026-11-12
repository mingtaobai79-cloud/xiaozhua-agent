# 生成器重写方案（链路顺序 + 定义驱动）

## 现状盘点

| 资产 | 状态 | 复用 |
|---|---|---|
| build.py（spec→dataSchema 骨架） | 顶层6键/node_id/param/make_node/branch 实测正确 | ✅ 复用骨架 |
| gates.py（G1-G8 生成前闸门） | 校验 Expression/悬空引用/类型/顺序 | ✅ 复用+补 |
| construction/microflow_nodes.py | 样本克隆（SAMPLE_PATH=create_entity_node.sample.json） | ❌ 弃用，换成定义驱动 |
| node_templates/（23类平台真实模板） | 从真实流程抽取，取字段最全者 | ✅ 作骨架 |
| node_modals/（24类 modal 契约） | 本次会话完成 | ✅ 作校验闸门输入 |
| api-catalog.md（30接口） | 入参+返回 | ✅ 定义抓取指引 |
| frontend-validation.md（前端校验清单） | 本次会话完成 | ✅ 校验闸门 |
| entity_attrs.json / skeleton_110.json 等 | 部分真实定义缓存 | ⚠️ 需补全成「定义库」 |

## 核心架构：定义驱动 + 链路顺序

旧做法（否定）：整包 JSON 手写 → 写进去算完成 → 事后脚本补。
新做法：**按节点顺序，每节点从「定义库」取真实字段/参数，过校验，保存，读回验证。**

```
spec（声明式，节点序列）
  │
  ▼ 按 nodes 顺序逐个生成
节点 N：
  1. 确定依赖（选实体/选服务/选选项集/选事件）
  2. 从「定义库」取真实定义（attributes/parameter/枚举项/事件字段，含 md5）
  3. 构造节点 JSON（结构来自 node_templates 骨架，字段来自定义库）
  4. 引用解析（前序出参 → 本节点引用，链路 G8）
  5. 过闸门（frontend-validation 清单 + gates G1-G8）
  │
  ▼ 产出 dataSchema
  │
  ▼ 提交：UpdatePost 保存 → FindByIdGet 读回 → 校验 state/节点完整性
```

## 定义库（definitions/）

从接口抓取的真实定义缓存，生成时离线取用（不实时调接口）：

```
definitions/
  entities/{entityFullName}.json     ← SearchTreeEntity + FindCustomDto 的 attributes(含 md5)
  services/{app}/{methodFullName}.json ← SearchMethodByName 的 parameter/returnValue(含 md5)
  enums/{enumId}.json                ← SearchEnumByAppName + SelectJavaEnumItem 的枚举项
  events/{app}.json                  ← SearchEventList / SearchSendMqList 的事件字段
  dtos/{dtoFullName}.json            ← FindCustomDto 的 attributes
  dataflows/{sourceEntityId}.json    ← DataFlowListManuallyMapping 的生单规则
```

定义库由独立脚本 `scripts/harvest_definitions.py` 抓取（走接口，CDP 或直连），生成器只读。

## 关键决策

1. **结构来自 node_templates，字段来自定义库**——不新增键，只替换三类（entity 引用/字段引用/表达式），替换后跑校验。
2. **引用按链路顺序**——前序节点先生成，出参名 `_<actionType>_<6位>` 注册进「符号表」，后序引用从符号表解析。
3. **字段必须来自所选实体的 attributes**（含 md5）——拿不到就报错，不编造。
4. **保存后 FindByIdGet 读回**——验证 dataSchema 完整 + state 正确，不只是 UpdatePost 返回。
5. **先 1 条最小流程端到端跑通**（minV1 式：建变量→查询→修改变量），零异常再上 40 条真实业务。

## 实施步骤

1. ✅ 前端校验清单（frontend-validation.md）
2. 写 scripts/harvest_definitions.py —— 抓真实定义落 definitions/
3. 重写 construction/microflow_nodes.py —— 定义驱动的节点构造器（弃用样本克隆）
4. 补 build.py 的符号表 + 链路顺序
5. 写 1 条最小流程 spec + 端到端验证（生成→校验→保存→读回）
6. 上 40 条真实业务（采购到付款 P2P + 数据迁移）

## 下一步

先做第 2 步（harvest_definitions.py），把生成器要用的真实定义抓齐落库。
这步不依赖生成器，先抓：几个测试实体的 attributes + 一个服务的 parameter + 一个枚举的枚举项。
