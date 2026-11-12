# 微流程设计器节点面板定义（前端内置）

> 来源：`udc store chunk`（src_redux_store_ts）内置节点表 | 证据：STATIC
> 这是微流程设计器**左侧节点面板**（拖拽源）的权威定义

节点数：31

| order | 节点 | type | actionType |
|---|---|---|---|
| 1001 | 分支 | BRANCH | BRANCH |
| 1002 | 列表循环 | FOR_EACH | FOR_EACH |
| 1003 | 自定义错误 | CUSTOM_ERROR | CUSTOM_ERROR |
| 1004 | 计数循环 | FOR | FOR |
| 1005 | 跳出循环 | BREAK | BREAK |
| 2001 | 创建变量 | ACTIVITY | CREATE_VARIABLE |
| 2002 | 修改变量 | ACTIVITY | CHANGE_VARIABLE |
| 2011 | 创建映射组 | ACTIVITY | CREATE_MAP |
| 2012 | 映射操作 | ACTIVITY | MAP_OPERATION |
| 2013 | 数据转换 | ACTIVITY | DATA_MAPPING |
| 3001 | 创建列表 | ACTIVITY | CREATE_LIST |
| 3002 | 修改列表 | ACTIVITY | CHANGE_LIST |
| 3003 | 列表操作 | ACTIVITY | LIST_OPERATION |
| 4001 | 查询单条数据 | ACTIVITY | RETRIEVE |
| 4002 | 查询多条数据 | ACTIVITY | RETRIEVE_ARRAY |
| 4003 | 插入数据 | ACTIVITY | CREATE_ENTITY |
| 4003 | 批量插入数据 | ACTIVITY | CREATE_BATCH_ENTITY |
| 4004 | 更新数据 | ACTIVITY | CHANGE_ENTITY |
| 4004 | 批量更新数据 | ACTIVITY | CHANGE_BATCH_ENTITY |
| 4006 | 删除数据 | ACTIVITY | DELETE_ENTITY |
| 5000 | 连接器 | ACTIVITY | CONNECTOR |
| 5001 | 事件投递 | ACTIVITY | PUBLISH_BUSINESS_EVENT |
| 5001 | 执行生单规则 | ACTIVITY | CALL_DATA_FLOW |
| 5004 | 自定义服务 | ACTIVITY | CALL_APP_SERVICE |
| 7050 | 子微流程 | ACTIVITY | SUB_MICROFLOW |
| 11000 | 唯一 | ACTIVITY | ATTRIBUTE_UNIQUE |
| 11001 | 设置值 | ACTIVITY | ASSIGN_VALUE |
| 11001 | 默认值 | ACTIVITY | DEFAULT_VALUE |
| 11004 | 必填 | ACTIVITY | ATTRIBUTE_REQUIRED |
| 11005 | 显示信息 | ACTIVITY | SHOW_MESSAGE |
| 12000 | 类型转换 | ACTIVITY | CONVERT_DATA |
