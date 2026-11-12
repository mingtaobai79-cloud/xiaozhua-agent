# 配置项能力矩阵（全节点静态归类，唯一事实源）

**位置**：seeyon-agent 仓库 `core/facts/udc/microflow/node-settings-capability.json`
**生成器**：`tools/build_settings_capability.py`（证据更新后重跑）

## 内容
- 24 类节点全覆盖；每个配置项：UI 标签/控件/选项/默认值/何时必填/来源
- 12 类节点 × 40 种子模式切换态的字段增删（VARIANTS.json 实测）
- 通用值槽三态：常量 Simple / 引用 SelectParam / 表达式 Expression
- compile_or_ui_facts：backBuild.log 级编译实证（G17/G19/G25-G29、END 列表赋值、DATA_MAPPING 形态等）

## 铁律
1. **任何节点配置项知识的更新，先进矩阵，再进构造器/闸门** —— 禁止只改构造器。
2. 构造器/闸门必须与矩阵一致；发现矩阵没有的形态 → 先补矩阵（带证据），再改代码。
3. 「赋值方式」三态存储键：字段映射=attrs / 对象引用=value / 自动映射=mapping；
   实体型必须显式带 mappingType；BASIC 型模式由 value 形态表达（无 mappingType）。
4. 子模式是级联的（选了前置才渲染赋值方式等字段），生成器必须按已选模式给齐联动必填。

## 闸门落位与待补形态
- G30（赋值方式）、G31（引用链类型）已从矩阵生成，落在 `gates.py`；语料裁决记录在 `references/gates.md`。
- 构造器形态级缺口（逐形态补，补一个过一轮构建）：实体型 mappingType=value（对象引用）/
  mapping（自动映射）构造器未实现；CHANGE_VARIABLE 剩 11 形态；CONVERT_DATA/CALL_DATA_FLOW
  部分子模式。
- 构造器×矩阵映射盘点法：grep 构造器模块 `def x(builder` 清单，与矩阵 actionType 对齐。

## 已知证据源（改矩阵前来这里找，别重新探测）
- `fixtures/microflow/node_modals/*.json` 抽屉字段契约（含旧命名别名）
- `scratch/variant-evidence/VARIANTS.json` 40 切换态全文
- `scratch/node-full-evidence/SUMMARY.json` 24 类实测抽屉
- `docs/audit/udc-semantics/MICROFLOW-*-CONTRACT.md` 35 篇逐节点契约
- `node-modal-and-value-editor.md`（用户口述权威）/ `node-variants.md` / `node-field-shape-contract.md`