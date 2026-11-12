# 微流程节点前端校验清单（生成器闸门输入）

来源：24 类 node_modals 的 validation_rules + 校验接口（udcConditionCheckPost/checkSchema）+ 用户演示确认。
标注：★=用户演示实测确认；△=从契约推导待实测。

## 一、通用校验（所有节点）

| # | 规则 | 状态 |
|---|---|---|
| G-A | 节点出参名称必填（几乎所有节点） | ★ |
| G-B | 引用类字段（选变量/列表/节点/实体）必须引用「前序已创建」的对象，不能引用后面的 | ★ G8 |
| G-C | 引用类型必须匹配（实体变量 vs 基本变量 vs 列表[多条] vs 单条） | ★ |
| G-D | 字段/条件/表达式里引用的字段必须来自「该节点选定的实体/DTO」的 attributes | ★ |

## 二、逐节点必填/条件必填（24 类）

### 数据活动（7）
- RETRIEVE 查询单条：查询方式★ / 选择应用★ / 选择实体★ / 节点出参名称★；ID查询→选择该记录的ID★；条件查询→过滤条件每行 字段+运算符+值 都不空★（否则「值不能为空」）；未查到=终止→提示内容★
- RETRIEVE_ARRAY 查询多条：应用/实体/出参名称★；分页查询=是→分页数据(PageInfo)★；聚合→聚合方法+计算字段★；ID集合→ID集合★
- CREATE_ENTITY 插入：应用★/实体★(选完回填 attributes 带 md5)/赋值方式★/出参名称★；字段赋值每值编辑器 Simple/SelectParam/Expression 不空★
- CREATE_BATCH_ENTITY 批量插入：记录列表(实体[多条])★/出参名称★
- CHANGE_ENTITY 更新：更新的数据(实体变量)★/出参名称★；字段赋值每值不空★
- CHANGE_BATCH_ENTITY 批量更新：记录列表(实体[多条])★/出参名称★
- DELETE_ENTITY 删除：删除规则★(指定/过滤/ID集合)；指定→选择节点★；过滤→实体+过滤条件★；ID集合→实体+ID集合★

### 变量/列表（5）
- CREATE_VARIABLE 创建变量：变量类型★(基本/实体/自定义对象/选项集/元数据/事件对象/其他)；按类型补 数据类型/实体/自定义对象/选项集/其他类型★；出参名称★
- CHANGE_VARIABLE 修改变量：变量★(前序已创建 G8)/变量值★；基本变量=单值编辑器，实体变量=字段映射
- CREATE_LIST 创建列表：列表类型★(基本/实体/自定义对象/选项集/事件对象)；按类型补★；出参名称★
- MODIFY_LIST 修改列表：选择列表★/操作类型★；增加/全量替换→列表对象★；删除→删除凭据字段★
- LIST_OPERATION 列表操作：选择列表★/操作类型★/出参名称★；按操作类型补 计算字段/操作数据/分组字段/过滤条件/第几条/排序规则★

### 映射（2）
- CREATE_MAPPING_GROUP 创建映射组：至少一组键值对(键+值)★；出参名称★
- MAPPING_OPERATION 映射操作：选择映射★/操作类型★；获取→映射键+值类型+数据类型+是否列表；赋值→键值对；删除→键；获取键列表→出参名称

### 逻辑（4）
- BRANCH 分支：每个「符合条件」分支必须有表达式(布尔)★；默认分支无条件(expression=null)；≥1符合条件分支+1默认分支
- FOR 计数循环：起始值/终止值/步长/循环变量名称★；执行条件(循环变量 比较 终止值)
- FOR 列表循环：选择列表★/循环对象名称★
- CUSTOM_ERROR 自定义错误：错误提示方式★(全局/定位)；全局→填写错误★；定位→原始数据+错误数据+定位字段+填写错误★

### 服务/加工（6）
- CUSTOM_SERVICE 自定义服务：应用★/服务★/赋值方式★(字段映射/对象引用/自动映射)/出参名称★；参数按服务入参(SearchMethodByName 返回的 parameter)★
- EVENT_DELIVERY 事件投递：事件类型★(应用间/应用内)/应用★/可投递的事件★(应用内=SearchEventList/应用间=SearchSendMqList)/普通或延迟★
- SUB_MICROFLOW 子微流程：微流程服务★/参数(按子微流程入参)★/出参名称★
- TYPE_CONVERT 类型转换：变量类型★(写死8种)/选择数据★/出参名称★
- DATA_CONVERSION 数据转换：来源数据★/目标类型★/所属应用★/实体对象★/映射关系★(未配置报错)/出参名称★
- CALL_DATA_FLOW 执行生单规则：来源实体★/生单规则★(按 sourceEntityId 查)/数据来源方式★(查询→过滤条件★；选择→来源实体数据★)/出参名称★

## 三、保存时校验（后端）

| 接口 | 触发 | 返回 | 状态 |
|---|---|---|---|
| udcConditionCheckPost | 过滤/筛选条件填写后校验 | content(不通过说明) | ★ |
| udcMicroflowCheckSchemaUpdatePost | 保存前检查 | content{check,errors,errorMessage[{errorCode,errorType,level,message,nodeCaption,nodeId,path,propertyKey}]} | ★ |
| udcMicroflowUpdatePost | 实际保存 | content | ★ |

## 四、校验失败表现（前端）

- 必填未填：字段红框 + 工具提示「值不能为空」/「请选择」/「请输入」★
- 引用失效：下拉显示「已失效」/「请重新选择」★
- 类型不匹配：选项置灰 / 提示「请选择类型为XX的数据」★
- 校验不通过(保存时)：errorMessage 带 nodeId/propertyKey/path，定位到具体节点+字段★

## 五、与现有闸门的映射

现有 gates.py G1-G8 已覆盖部分；需按本清单补：
- G-D（字段来自所选实体的 attributes）—— 已有「节点确定后元数据重载」机制对应
- 每节点条件必填（如 RETRIEVE ID查询→ID、聚合→计算字段）—— 需按节点子模式展开
- 保存后必须 FindByIdGet 读回 dataSchema 验证 state/节点完整性 ★

## 六、待确认（△）

- CUSTOM_SERVICE 参数填写时的「校验」具体接口（用户观察「填参数有时走校验」，疑似 udcConditionCheckPost 或独立接口）
- 选项集/事件对象/元数据 选中后是否还有「选枚举项/选事件字段」的二级校验
- 表达式「验证」按钮走哪个接口（疑似 udcExpressionSchemaPost 或独立校验）
