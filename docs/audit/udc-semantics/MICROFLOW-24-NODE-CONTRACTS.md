# UDC 微流程 24 类节点真实契约（CDP 实测 2026-10-27）

来源：drawer「动作场景」逐个添加 + console `添加节点 => addNode` payload + 配置抽屉 DOM。
所有节点默认 `output: null`、`isCompleted: false`，确认后由前端生成 output。

## 1. 分支
- actionType: `(无 actionType)`  默认 nodeId 前缀: `BRANCH`
- 抽屉标题: （无抽屉，画布内联配置）
- 必填: 无
- 默认附加结构: `{"conditions": [{"nodeId": "CONDITION_EczywO", "name": "ifBranch", "type": "CONDITION", "caption": "符合条件即进入该分支", "description": "", "runAfter": null, "expression": {"title": "", "schema": null}, "nodes": [], "isCompleted": false}, {"nodeId": "CONDITION_PJtjGc", "name": "elseBranch", "type": "CONDITI`

## 2. 列表循环
- actionType: `(无 actionType)`  默认 nodeId 前缀: `ForEach`
- 抽屉标题: 列表循环
- 必填: ['选择列表', '循环对象名称']
- 默认附加结构: `{"nodes": [], "foreach": {"sourceItemes": []}}`

## 3. 计数循环
- actionType: `(无 actionType)`  默认 nodeId 前缀: `For`
- 抽屉标题: 计数循环
- 必填: ['循环起始值', '循环终止值', '步长', '循环变量名称']
- 选填: ['执行条件']
- select 默认: ['小于等于']
- 默认附加结构: `{"nodes": [], "foreach": {"sourceItemes": []}}`

## 4. 自定义错误
- actionType: `(无 actionType)`  默认 nodeId 前缀: `CUSTOM`
- 抽屉标题: 自定义错误
- 必填: ['填写错误']
- 选填: ['错误提示方式']

## 5. 创建变量
- actionType: `CREATE_VARIABLE`  默认 nodeId 前缀: `CREATE`
- 抽屉标题: 创建变量
- 必填: ['变量类型', '数据类型', '节点出参名称']
- 选填: ['默认值']
- radio 枚举: ['BASIC', 'ENTITY_OBJECT', 'DEFAULT_OBJECT', 'ENUM', 'METADATA', 'MESSAGE', 'OTHER']
- select 默认: ['文本']

## 6. 修改变量
- actionType: `CHANGE_VARIABLE`  默认 nodeId 前缀: `CHANGE`
- 抽屉标题: 修改变量
- 必填: ['变量']
- 选填: ['变量值']

## 7. 创建映射组
- actionType: `CREATE_MAP`  默认 nodeId 前缀: `CREATE`
- 抽屉标题: 创建映射组
- 必填: ['节点出参名称']
- 选填: ['添加映射']

## 8. 映射操作
- actionType: `MAP_OPERATION`  默认 nodeId 前缀: `MAP`
- 抽屉标题: 映射操作
- 必填: ['选择映射', '操作类型', '该值的映射键', '映射值类型', '数据类型', '是否列表', '节点出参名称', '提示内容']
- 选填: ['未获取到数据时']
- radio 枚举: ['BASIC', 'ENTITY_OBJECT', 'DEFAULT_OBJECT', 'ENUM', 'MAP']
- select 默认: ['获取']

## 9. 创建列表
- actionType: `CREATE_LIST`  默认 nodeId 前缀: `CREATE`
- 抽屉标题: 创建列表
- 必填: ['列表类型', '数据类型', '节点出参名称']
- 选填: ['默认值']
- radio 枚举: ['BASIC', 'ENTITY_OBJECT', 'DEFAULT_OBJECT', 'ENUM', 'MESSAGE']
- select 默认: ['文本']

## 10. 修改列表
- actionType: `CHANGE_LIST`  默认 nodeId 前缀: `CHANGE`
- 抽屉标题: 修改列表
- 必填: ['选择列表', '操作类型', '列表/对象']
- select 默认: ['增加']

## 11. 列表操作
- actionType: `LIST_OPERATION`  默认 nodeId 前缀: `LIST`
- 抽屉标题: 列表操作
- 必填: ['选择列表', '操作类型', '操作数据', '节点出参名称']

## 12. 查询单条数据
- actionType: `RETRIEVE`  默认 nodeId 前缀: `RETRIEVE`
- 抽屉标题: 查询单条数据
- 必填: ['选择应用', '选择实体', '节点出参名称', '提示内容']
- 选填: ['查询方式', '过滤条件', '排序规则', '查询聚合对象', '未查到数据时']
- radio 枚举: ['CONDITION', 'IDS']
- select 默认: ['加载中...']

## 13. 查询多条数据
- actionType: `RETRIEVE_ARRAY`  默认 nodeId 前缀: `RETRIEVE`
- 抽屉标题: 查询多条数据
- 必填: ['选择应用', '选择实体', '分页数据', '节点出参名称']
- 选填: ['查询方式', '筛选条件', '排序规则', '分页查询']
- radio 枚举: ['CONDITION', 'IDS', 'COUNT', 'OTHERS']
- select 默认: ['加载中...']

## 14. 插入数据
- actionType: `CREATE_ENTITY`  默认 nodeId 前缀: `CREATE`
- 抽屉标题: 插入数据
- 必填: ['选择应用', '选择实体', '赋值方式', '节点出参名称']
- radio 枚举: ['attrs', 'value']
- select 默认: ['加载中...']

## 15. 批量插入数据
- actionType: `CREATE_BATCH_ENTITY`  默认 nodeId 前缀: `CREATE`
- 抽屉标题: 批量插入数据
- 必填: ['选择插入的记录列表', '节点出参名称']

## 16. 更新数据
- actionType: `CHANGE_ENTITY`  默认 nodeId 前缀: `CHANGE`
- 抽屉标题: 更新数据
- 必填: ['选择更新的数据', '节点出参名称']
- 选填: ['字段赋值']

## 17. 批量更新数据
- actionType: `CHANGE_BATCH_ENTITY`  默认 nodeId 前缀: `CHANGE`
- 抽屉标题: 批量更新数据
- 必填: ['选择更新的记录列表', '节点出参名称']

## 18. 删除数据
- actionType: `DELETE_ENTITY`  默认 nodeId 前缀: `DELETE`
- 抽屉标题: 删除数据
- 必填: ['删除规则', '选择节点', '节点出参名称']
- radio 枚举: ['SELECT_PARAM', 'CONDITION', 'IDS']

## 19. 自定义服务
- actionType: `CALL_APP_SERVICE`  默认 nodeId 前缀: `CALL`
- 抽屉标题: 自定义服务
- 必填: ['选择应用', '选择服务', '节点出参名称']
- select 默认: ['加载中...', '']

## 20. 事件投递
- actionType: `PUBLISH_BUSINESS_EVENT`  默认 nodeId 前缀: `PUBLISH`
- 抽屉标题: 事件投递
- 必填: ['选择应用', '可投递的事件']
- 选填: ['事件类型', '事件类型']
- radio 枚举: ['AMONG_APP', 'IN_APP']
- select 默认: ['加载中...']

## 21. 子微流程
- actionType: `SUB_MICROFLOW`  默认 nodeId 前缀: `SUB`
- 抽屉标题: 子微流程
- 必填: ['选择微流程服务']
- select 默认: ['']

## 22. 执行生单规则
- actionType: `CALL_DATA_FLOW`  默认 nodeId 前缀: `CALL`
- 抽屉标题: 执行生单规则
- 必填: ['来源实体', '生单规则', '数据来源方式 ', '过滤条件', '节点出参名称']

## 23. 类型转换
- actionType: `CONVERT_DATA`  默认 nodeId 前缀: `CONVERT`
- 抽屉标题: 类型转换
- 必填: ['变量类型', '选择数据', '节点出参名称']

## 24. 数据转换
- actionType: `DATA_MAPPING`  默认 nodeId 前缀: `DATA`
- 抽屉标题: 数据转换
- 必填: ['来源数据', '目标数据对象类型', '目标数据对象所属应用', '实体对象', '映射关系', '节点出参名称']
- radio 枚举: ['ENTITY', 'DTO']
- select 默认: ['加载中...']
