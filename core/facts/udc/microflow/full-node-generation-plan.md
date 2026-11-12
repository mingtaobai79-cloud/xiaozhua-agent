# 全量节点业务测试生成计划

## 目标
生成覆盖 24 类节点的真实业务微流程（采购供应链 P2P），定义驱动 + 真实引用，
checkSchema errors=0 + state=RELEASE（生成即正确，不做事后脚本补丁）。

## 24 类节点清单（模板+modal 已盘点）
逻辑活动(4): BRANCH 分支 / FOR-forEach 列表循环 / FOR-fori 计数循环 / CUSTOM_ERROR 自定义错误
变量活动(2): CREATE_VARIABLE 创建变量 / CHANGE_VARIABLE 修改变量
映射活动(2): CREATE_MAP 创建映射组 / MAP_OPERATION(DATA_MAPPING) 映射操作
列表活动(3): CREATE_LIST 创建列表 / CHANGE_LIST(MODIFY_LIST) 修改列表 / LIST_OPERATION 列表操作
数据活动(7): RETRIEVE 查询单条 / RETRIEVE_ARRAY 查询多条 / CREATE_ENTITY 插入 /
             CREATE_BATCH_ENTITY 批量插入 / CHANGE_ENTITY 更新 / CHANGE_BATCH_ENTITY 批量更新 /
             DELETE_ENTITY 删除
基础服务(3): CALL_APP_SERVICE 自定义服务 / EVENT_DELIVERY 事件投递 / SUB_MICROFLOW 子微流程
数据加工(3): TYPE_CONVERT 类型转换 / CONVERT_DATA 数据转换 / CALL_DATA_FLOW 执行生单规则

## 现状
- 模板 23 个（来自 V16 全节点流程，缺 EVENT_DELIVERY/TYPE_CONVERT 用 modal 补）
- modal 23 个（24 类契约，含 frontend-validation.md）
- 定义库很薄：2 实体、1 服务、1 枚举、1 事件
- 生成器 microflow_nodes.py 仍是样本克隆版，未重写

## 步骤
1. 补全定义库（harvest_definitions.py 扩展）：
   - 实体 attributes：XzhExp950795Dto 已有；补 YsFull6956Dto(全量)、MigrationPlan 等
   - 自定义服务 parameter：FileAppService.copy 已有；补 1-2 个业务服务
   - 枚举：已有 items_1045264166166260005
   - 事件：events/list.json 只有 235B（太薄，补事件字段）
   - 生单规则：dataflows/ 缺失，抓 udcDataFlowListManuallyMappingPost
   - 子微流程：确认桩 id
2. 重写 components/construction/microflow_nodes.py（定义驱动 + 符号表）
3. 设计采购供应链 P2P 业务流 spec（24 类节点顺序 + 真实数据）
4. 生成 dataSchema + 闸门校验
5. 推送 + checkSchema + 读回验证

## 关键约束（用户拍板，必须遵守）
- 结构来自 node_templates（不新增键），字段来自定义库（真实 attributes/参数/枚举项，含 md5）
- 引用按链路顺序（符号表：前序出参注册 → 后序引用解析）
- 真实引用：entityObject 走 SearchTreeEntityPost，defaultObject 走 SearchNonEntityDtoPost
- entityObject 10 键（key/entity=domain 类，id/fullName=DTO），defaultObject 11 键
- 入参/出参定义挂 trigger/endNode 的 paramType（NONE/BASIC/ENTITY_OBJECT/DEFAULT_OBJECT）
- 每节点用表达式/真实数据，不空壳
- 保存后 FindByIdGet 读回验证（不只是 UpdatePost 返回）
- 取证只走接口，不碰 DB
