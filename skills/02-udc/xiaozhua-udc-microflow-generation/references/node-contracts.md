# 节点契约表（node_contracts.py）

目的：把「点开抽屉逐项填」前移到生成时。每个节点的每个页签，必填 / 可空 / 可表达式，全部落表。

代码：`components/udc/microflow/node_contracts.py`，已作为 **G23** 接进 `gates.run_gates`。

## 为什么需要
- 设计器是分页签的：「查询单条数据」分 ID 查询 / 条件查询，两个页签必填项不同；
- 有一批字段只有前端认（`trigger.desc` 参数名称、`attrType` 16 键、`isCompleted`），
  服务端 checkSchema/发布/编译全绿，页面上却是空黄框或红节点；
- 这些规则散在 643 条语料里，人工记不住。

## 契约维度
| 维度 | 含义 |
|---|---|
| `required` | 缺了 UI 就是空黄框 / 红字 |
| `present` | 字段必须在（允许空数组，如 CREATE_LIST.value=[]） |
| `optional` | 真实语料大量为空，不影响 |
| `expr` | 支持表达式 / 变量引用的位置 |
| `tabs` | 该节点在设计器的页签，不同页签必填不同 |
| `note` | 踩过的坑（编译失败/部署拒/UI 红字） |

## 已固化的形态（举例）
```
RETRIEVE      ID查询：selectParam(记录ID)    条件查询：condition(GROUP>CONDITION)
RETRIEVE_ARRAY 条件查询：condition            ID集合查询：selectParam(ids 列表)
CHANGE_*      selectParam(活动节点出参) + attrs；出参 INTEGER
CREATE_LIST   structure(实体) + value([])
CHANGE_LIST   selectParam(列表) + action + dataSource
CREATE_VARIABLE 基本类型=value；实体对象=structure(实体)+attrs(字段映射)
LIST_OPERATION selectParam + operationType；引实体列表必带 dtoType
SUB_MICROFLOW mfService.id；hasInput→attrs；hasOutput→output.name
CALL_APP_SERVICE selectMethod + output.name（入参定义由后端返回）
FOR           forStart/forEnd/forStep/targetName/output(INTEGER)
DATA_MAPPING  selectParam(源) + structure(目标) + mappingRule
CUSTOM_ERROR  error 非空（节点本身是红色，信息为空才是错）
BRANCH        conditions[0].expression 非空；elseBranch.isCompleted=None 正常
```

## 维护规则
- 新增契约只能来自真实语料或 UI 实测，不能凭直觉；
- 验证方式：拿环境里已有的 RELEASE 流程跑 `check_contracts`，**必须 0 问题**；
  报出来的一律当回归（要么契约错、要么流程真错）；
- `tests/test_composer.py` 必须 13/13。
