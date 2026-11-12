# UDC 交互表地图（LIVE：MySQL `udc_test2` schema，99 张表）

**证据**：`SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_SCHEMA='udc_test2' AND TABLE_NAME LIKE 'udc_%'` → **99 张**。

**设计态 vs 运行态两族**：
- **设计态表**（`udc_*`）：应用/实体/属性/页面/菜单/微流程/枚举/连接器等的元数据（元数据权威源）。
- **运行态表**（`udc_rt_*` + `udc_filter_plan_formal`/`udc_filter_plan_rt` + `udc_affair_register*`）：
  发布后运行路径的日志/映射/筛选方案（与发布镜像/Redis 配合）。

> 元数据双写链：设计态落 MySQL → 发布 → 运行态读 `udc_rt_*` / 发布镜像（Redis 缓存按配置，见 PROGRESS 存储层）。

## 设计态表（80 张）
- `udc_app_collaboration`
- `udc_app_custom_error`
- `udc_app_version`
- `udc_application`
- `udc_application_capability`
- `udc_attachment_template`
- `udc_attr_snapshot`
- `udc_attribute`
- `udc_attribute_group`
- `udc_attribute_set`
- `udc_backend_component`
- `udc_custom_application`
- `udc_custom_control`
- `udc_custom_data_type`
- `udc_custom_ext_field`
- `udc_custom_plan`
- `udc_custom_plan_content`
- `udc_data_flow`
- `udc_data_flow_mapping`
- `udc_data_transfer_object`
- `udc_deduction_algorithm`
- `udc_deduction_id_mapping`
- `udc_deduction_map`
- `udc_deduction_rule`
- `udc_deduction_rule_detail`
- `udc_dependent_application`
- `udc_deploy_record`
- `udc_dto_attribute`
- `udc_entity`
- `udc_entity_group`
- `udc_entity_preset`
- `udc_enum`
- `udc_enum_category`
- `udc_enum_item`
- `udc_event`
- `udc_filter_plan`
- `udc_function`
- `udc_function_node`
- `udc_function_refer`
- `udc_history_metadata`
- `udc_id_to_key_map`
- `udc_index`
- `udc_indicator_atom_category`
- `udc_indicator_derive_category`
- `udc_indicator_table_category`
- `udc_last_version_metadata`
- `udc_message_category`
- `udc_message_link`
- `udc_micro_flow_group`
- `udc_microflow_info`
- `udc_microflow_node_template`
- `udc_microflow_preset_template`
- `udc_operation_log`
- `udc_page_component`
- `udc_page_component_category`
- `udc_page_component_data_type`
- `udc_page_data_source`
- `udc_page_group`
- `udc_page_info`
- `udc_page_layout`
- `udc_page_schema`
- `udc_page_template`
- `udc_page_template_category`
- `udc_page_template_published`
- `udc_parameter`
- `udc_personal_plan`
- `udc_portlet`
- `udc_portlet_group`
- `udc_push_association`
- `udc_refer_config`
- `udc_refer_config_group`
- `udc_reference`
- `udc_resource`
- `udc_role`
- `udc_role_resource`
- `udc_scalability`
- `udc_scalability_option`
- `udc_serial_config`
- `udc_upgrade_info`
- `udc_upgrade_record`

## 运行态表（18 张）
- `udc_affair_register`
- `udc_affair_register_extend`
- `udc_affair_register_param`
- `udc_entity_monitor_log`
- `udc_filter_plan_formal`
- `udc_filter_plan_rt`
- `udc_rt_app_log`
- `udc_rt_attachment_template`
- `udc_rt_data_flow_log`
- `udc_rt_data_flow_map`
- `udc_rt_data_flow_mapping`
- `udc_rt_deduction_algorithm`
- `udc_rt_deduction_log`
- `udc_rt_deduction_map`
- `udc_rt_deduction_rule`
- `udc_rt_deduction_rule_detail`
- `udc_rt_entity_log`
- `udc_rt_page_log`

## 关键表
- `udc_application` / `udc_application_capability` / `udc_app_version` 应用与版本
- `udc_entity` / `udc_attribute` / `udc_entity_group` 实体与属性（设计态权威源）
- `udc_page_info` / `udc_page_schema` / `udc_page_layout` / `udc_page_group` 页面与外框
- `udc_function` / `udc_function_node` / `udc_function_refer` 菜单/功能节点
- `udc_microflow_info` / `udc_microflow_node_template` / `udc_micro_flow_group` 微流程
- `udc_enum` / `udc_enum_category` / `udc_enum_item` 枚举
- `udc_data_transfer_object` / `udc_dto_attribute` DTO
- `udc_filter_plan` / `udc_filter_plan_formal` / `udc_filter_plan_rt` 筛选方案（设计/正式/运行三态）
- `udc_refer_config` 参照配置；`udc_serial_config` 流水号
