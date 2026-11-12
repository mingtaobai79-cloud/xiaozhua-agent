# MCP 工具权威清单（自动生成，勿手改）

> 生成器：`tools/gen_mcp_manifest.py`（`--check` 校验一致性）
> 数据源：`seeyon_host_bootstrap.bootstrap()` + `adapters/mcp/server.py`
> 手工维护的 `adapters/*/MCP-TOOL-MANIFEST.md` 只作历史记录，**以本文件为准**。

## 概览

```
bootstrap 可调用能力  57
MCP 工具总数          54
需要凭据的工具        4（seeyon_microflow_publish / seeyon_expression_verify / seeyon_expression_filter / seeyon_entity_rule_publish）
```

## 按域分布

| 域 | 工具数 |
|---|---:|
| 跨模块 | 10 |
| application | 5 |
| entity | 4 |
| setting | 16 |
| serial | 2 |
| flow | 7 |
| rule | 2 |
| expression | 3 |
| page | 4 |
| SPI | 1 |

## 全部工具

### 跨模块（10）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_dispatch` | `intent` | `target` | 按 intent 路由到组件 |
| `seeyon_generate` | `application_id`, `entity_name` | `attributes`, `caption` | 实体 → 后端骨架 + 前端页面定义 |
| `seeyon_generate_from_requirement` | `text`, `application_id` | — | 自然语言 → 实体模型 |
| `seeyon_live_probe` | — | `cred_file` | 活体只读探测（默认离线 BLOCKED） |
| `seeyon_capability_index` | — | `domain` | 九大域能力总索引 |
| `seeyon_repo_state` | `repo_dir` | `recent` | 客开仓库只读状态 |
| `seeyon_repo_sync` | `repo_dir`, `action`, `confirm` | `message`, `paths` | 客开仓库写操作（confirm 授权） |
| `seeyon_code_targets` | `target`, `app_name` | `backend_dir`, `frontend_dir`, `page_url`, `extension_point` | 客开代码该写在哪 |
| `seeyon_project_shape` | `backend_dir` | — | 探工程形态（五模块/单模块） |
| `seeyon_repo_url` | `app_name`, `git_base` | `side`, `local_repo_dir` | 拼客开仓库地址（base 必填） |

### application（5）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_app_dependency_body` | `app_id`, `dep_app_name`, `dep_app_caption`, `dep_app_version` | `dependent_app_type`, `dep_app_base_package`, `extra` | 添加依赖 body（SERVICE/FRONTEND） |
| `seeyon_app_dependency_remove_body` | — | `row_id`, `ids` | 移除依赖 body（GraphQL 单删 / REST 批删） |
| `seeyon_app_deploy_body` | `app_id` | `project_type`, `terminal_type`, `deploy_type` | 沙箱立即构建 body |
| `seeyon_app_version_list` | `app_name` | `page_size` | 发布版本列表 body |
| `seeyon_app_build_info` | `app_id` | — | 构建信息查询（含 logs[]） |

### entity（4）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_deploy_plan` | `application_id`, `entity_name`, `attributes` | `caption`, `stereotype`, `deploy_type` | 建实体四步部署方案（出 body） |
| `seeyon_index_body` | `caption`, `entity_id`, `field_ids` | — | 索引 body |
| `seeyon_dto_body` | `app_id`, `caption`, `name`, `attributes` | — | DTO + 属性 body |
| `seeyon_refer_config_body` | `app_id`, `entity_id`, `caption`, `refer_type`, `terminals` | `group_id` | 实体参照配置 body |

### setting（16）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_enum_body` | `app_id`, `caption`, `name` | `order_no` | 枚举 body |
| `seeyon_enum_item_body` | `app_id`, `enum_id`, `caption`, `item_value`, `enum_code`, `order_no` | `enable`, `parent_id` | 枚举项 body |
| `seeyon_event_body` | `app_id`, `caption`, `event_name`, `dto_id` | — | 事件 body |
| `seeyon_enum_category_body` | `app_id`, `name` | `order_no`, `parent_id`, `description` | 枚举分组 body |
| `seeyon_event_data_body` | `app_id`, `caption`, `event_name`, `entity_id`, `attrs` | `description`, `message_type` | 带数据事件 body |
| `seeyon_option_set_category_body` | `app_id`, `app_guid`, `name`, `caption` | `order_no`, `parent_id`, `description` | 选项集分组 body |
| `seeyon_option_set_body` | `app_id`, `app_guid`, `name`, `caption`, `category_id` | `order_no` | 选项集 body |
| `seeyon_option_set_item_body` | `app_id`, `app_guid`, `enum_id`, `name`, `caption`, `code` | `order_no`, `enable` | 选项集项 body |
| `seeyon_attribute_set_body` | `app_id`, `name`, `caption` | `description`, `source_type`, `order_no` | 字段集 body（父 REST） |
| `seeyon_attribute_set_field_body` | `app_id`, `set_id`, `name`, `caption` | `data_type`, `not_null`, `min_length`, `max_length`, `decimal_digits`, `multi_select`, `searchable`, `uniqueness`, `attribute_group_id`, `order_no`, `column_name`, `widget_config`, `encryption`, `desensitization` | 字段集字段 body（子 GraphQL） |
| `seeyon_scalability_option_body` | `app_id`, `name`, `caption` | — | 扩展实体方案 body |
| `seeyon_scalability_field_body` | `app_id`, `option_id`, `prefix`, `caption` | `count`, `data_type`, `data_type_properties` | 扩展实体字段 body |
| `seeyon_qrcode_body` | `app_id`, `app_guid`, `name` | `qr_type`, `link_type`, `entity_full_name`, `value_field_code`, `pc_page_path`, `mobile_page_path` | 二维码/条码/链接码 body |
| `seeyon_parameter_body` | `app_id`, `app_guid`, `name`, `caption` | `data_type`, `data_type_properties`, `description`, `param_group`, `value`, `order_no`, `param_type` | 应用参数 body |
| `seeyon_excel_template_body` | `app_id`, `app_guid`, `name`, `caption`, `main_full_name`, `columns` | `is_import`, `is_custom` | 导入导出模板 body |
| `seeyon_excel_template_column` | `attribute_full_name`, `display_name` | `data_type` | 导入导出模板列 |

### serial（2）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_serial_scheme_body` | `app_id`, `app_guid`, `code`, `name`, `sections` | `contain_flow`, `active`, `reset_rule`, `edit_entity`, `serial_type`, `sort_num`, `org_id`, `entity_full_name`, `source_app_name` | 流水号方案 body |
| `seeyon_serial_section` | `size` | `section_type`, `value`, `caption`, `fill_type`, `cut_type`, `fill_char`, `date_type`, `date_pattern`, `show`, `flow`, `increase`, `section_rank`, `serial_current`, `start_value`, `end_value`, `source_app_name` | 流水号段 |

### flow（7）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_microflow_create_body` | `name`, `caption`, `application_id`, `data_schema` | `trigger_type` | 微流程 create/checkSchema body |
| `seeyon_microflow_node` | `action` | `app`, `structure`, `entity`, `title`, `caption`, `condition_`, `value`, `fetch_type`, `mapping_type`, `mapping`, `delete_type`, `select_param`, `select_method`, `mf_service`, `data_type`, `param_type`, `level`, `for_end`, `nodes`, `output_desc`, `variable_title`, `null_handling` | 单节点构造（11 种 action） |
| `seeyon_microflow_gates` | `schema` | `app_name` | G1–G41 静态闸门 |
| `seeyon_microflow_capability` | — | `action` | 节点能力矩阵 |
| `seeyon_microflow_trigger` | — | `kind`, `node_id`, `job_caption`, `cycle_type`, `rotation_type`, `value`, `day_of_week`, `param_type`, `output`, `caption`, `basic`, `event`, `out_param_name` | 触发器（MANUAL/SCHEDULE/EVENT/MF_EVENT） |
| `seeyon_microflow_data_schema` | `name`, `caption`, `trigger`, `nodes` | `mf_type`, `trigger_type`, `end_output`, `input_param`, `description` | 组装 dataSchema |
| `seeyon_microflow_publish` 🔑 | `mid`, `app_id`, `data_schema` | `host`, `cookie`, `cdp_port`, `name`, `caption`, `trigger_type`, `group_id` | 发布到 RELEASE |

### rule（2）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_entity_rule_body` | `app_id`, `entity_id`, `name` | `caption`, `group_type`, `nodes`, `trigger`, `description`, `state` | 实体规则 body + 作用域校验 |
| `seeyon_entity_rule_publish` 🔑 | `dto` | `host`, `cookie`, `cdp_port` | 实体规则 checkSchema + create |

### expression（3）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_expression_catalog` | — | `kind`, `group` | 88 函数 / 131 系统变量 |
| `seeyon_expression_verify` 🔑 | `tokens`, `context` | `host`, `cookie`, `cdp_port`, `result_type`, `is_multi_select` | 校验+编译表达式 |
| `seeyon_expression_filter` 🔑 | `dto_full`, `list_desc`, `entity_model` | `host`, `cookie`, `cdp_port`, `field`, `op`, `const`, `spec`, `title` | FILTER 过滤条件表达式 |

### page（4）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_list_page_schema` | `application_id`, `entity_name`, `caption`, `attributes` | `entity_meta` | 列表页 pageSchema 骨架 |
| `seeyon_detail_page_schema` | `application_id`, `entity_name`, `caption`, `attributes` | `entity_meta` | 详情页 pageSchema 骨架 |
| `seeyon_filter_plan_body` | `app_name`, `app_id`, `page_id`, `grid_suffix`, `driven_entity`, `caption`, `conditions` | — | 过滤方案 body |
| `seeyon_custom_page_scaffold` | `page_url`, `app_id` | `title`, `with_fetch` | customPage.tsx 骨架 |

### SPI（1）

| 工具 | 必填参数 | 可选参数 | 说明 |
|---|---|---|---|
| `seeyon_spi_catalog` | — | — | SPI 扩展点事实目录 |

## 凭据边界

🔑 标记的工具**强制要求 `host` + `cookie` 两个必填参数**，不传凭据根本调不起来。
这是「MCP 面默认只读」红线的实现方式 —— 写动作必须由宿主显式授权。

守它的测试：`tests/test_mcp_server.py::test_write_not_exposed`
（断言凡是写类工具，`required` 必须包含 `host` 和 `cookie`）。
