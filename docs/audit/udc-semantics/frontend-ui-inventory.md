# UDC 设计器前端「每页 UI 全量」清单（可靠层）

> 日期：2026-10-13 | 来源：udc remoteEntry → 158 chunk → wakaru 解包 → 抽取
> 层：页面/组件的 文案 / 按钮 / 事件 / 组件 / 拖拽 / 弹窗 / 直接 op
> 证据：STATIC（chunk 字节码）| op 链（按钮→后端）在 frontend-page-ui-map 单列

页面/组件块：**99** | 带按钮 72 | 带拖拽 6

## 汇总表

| 页面/组件 | 字节 | 文案 | 按钮 | 事件 | 拖拽 | 直接op |
|---|---|---|---|---|---|---|
| `src_redux_store_ts.14dc061e` | 4140161 | 1851 | 247 | 1286 | 是 | 291 |
| `src_components_design_settings_common_operate-list_operateCm` | 1678440 | 728 | 101 | 1814 | 是 | 15 |
| `src_components_app-design_app_components_theme_app-style-des` | 1369510 | 544 | 63 | 158 |  | 0 |
| `dataflow-relation` | 271952 | 90 | 23 | 193 | 是 | 0 |
| `src_pages_app-design_rule_dataflow_relation-graph_index_tsx.` | 271952 | 90 | 23 | 193 | 是 | 0 |
| `src_pages_app-design_basic-info_index_tsx-node_modules_seeyo` | 130404 | 102 | 26 | 124 |  | 6 |
| `src_pages_app-design_rule_index_tsx-node_modules_xiaozhua_biz-` | 110910 | 73 | 14 | 97 | 是 | 0 |
| `src_components_design_stage_index_tsx.d0430eab` | 107272 | 20 | 6 | 31 |  | 0 |
| `src_pages_design_functions_index_tsx-src_components_page-par` | 91301 | 93 | 23 | 73 |  | 0 |
| `src_components_page-params_index_tsx-src_utils_treeUtils_pag` | 85964 | 47 | 10 | 66 |  | 0 |
| `src_pages_udc_application_index_tsx.a0f20272` | 78046 | 56 | 21 | 132 |  | 0 |
| `src_components_design_select-box_select-cmps_tsx-src_contain` | 78044 | 49 | 8 | 49 | 是 | 0 |
| `src_pages_app-design_entity-modeling_entity-fieldset_index_t` | 73439 | 64 | 7 | 44 |  | 0 |
| `src_components_app-design_app_components_theme_index_ts-src_` | 71290 | 9 | 2 | 9 |  | 0 |
| `src_pages_app-design_basic-setting_index_tsx-node_modules_se` | 59539 | 75 | 19 | 73 |  | 0 |
| `src_components_design_data-source_index_tsx.ecc90bb0` | 56612 | 19 | 2 | 7 |  | 0 |
| `src_components_app-design_parameter-definition_index_tsx.d0a` | 43323 | 23 | 7 | 34 |  | 1 |
| `src_components_design_top-tool-bar_index_tsx.bf7936ab` | 42679 | 28 | 6 | 36 |  | 0 |
| `src_containers_design_settings_index_tsx.d00dcd9e` | 41417 | 54 | 5 | 10 |  | 0 |
| `src_components_unify-console_items_operation-log_index_tsx.f` | 39415 | 37 | 1 | 10 |  | 1 |
| `src_pages_design_functions_components_page-info-edit_index_t` | 36740 | 15 | 2 | 22 |  | 0 |
| `src_pages_design_portlet_index_tsx-src_utils_getTerminalFrom` | 35817 | 41 | 13 | 12 |  | 0 |
| `src_pages_app-design_extension-plan_index_tsx.c111914a` | 34454 | 46 | 7 | 31 |  | 0 |
| `src_components_page-content_index_tsx-src_components_welcome` | 33797 | 36 | 12 | 16 |  | 0 |
| `src_pages_udc_app-log-data_list_index_tsx.f4b17d52` | 33154 | 20 | 4 | 18 |  | 0 |
| `src_pages_udc_upgrade-deploy_index_tsx.0c901b15` | 32980 | 50 | 12 | 22 |  | 0 |
| `src_pages_udc_customtype_index_tsx.21130696` | 32587 | 36 | 2 | 16 |  | 1 |
| `src_containers_design_page-design_index_tsx.6e093388` | 31831 | 15 | 6 | 6 |  | 0 |
| `src_pages_design_main_components_add-page_index_tsx.c6d3edce` | 30640 | 16 | 2 | 19 |  | 0 |
| `src_pages_udc_cmps_index_tsx-node_modules_xiaozhua_biz-icon-li` | 30218 | 31 | 5 | 44 |  | 6 |
| `src_components_design_settings_common_style-selector_index_m` | 29433 | 16 | 1 | 13 |  | 0 |
| `src_constants_design_page-type_ts-src_services_app-design_te` | 29000 | 8 | 2 | 0 |  | 14 |
| `src_pages_udc_backend-cmp_index_tsx-node_modules_xiaozhua_biz-` | 26288 | 30 | 3 | 41 |  | 3 |
| `src_pages_design_sub-pages_sider_tsx.ab0f4794` | 23699 | 14 | 6 | 18 |  | 0 |
| `src_pages_app-design_entity-modeling_enum-manger_enum-field_` | 22576 | 21 | 5 | 27 |  | 0 |
| `src_hooks_useGetPageLocked_ts-src_redux_design_actions_short` | 21811 | 10 | 2 | 4 |  | 0 |
| `src_pages_udc_sandbox_pages_elastic-deployment_index_tsx.b03` | 21720 | 21 | 2 | 15 |  | 0 |
| `src_pages_app-design_app-home_space-manage_SpaceManger_tsx.e` | 20620 | 7 | 3 | 16 |  | 0 |
| `src_pages_udc_sandbox_pages_sandbox-resource_index_tsx-src_p` | 20410 | 27 | 5 | 19 |  | 0 |
| `src_pages_udc_templateManage_index_tsx.edf44d56` | 19707 | 48 | 10 | 22 |  | 0 |
| `src_pages_udc_sandbox_pages_sandbox-application_index_tsx-sr` | 17923 | 16 | 10 | 18 |  | 0 |
| `src_components_design_outline_components_utils_ts.b77eaf66` | 17171 | 13 | 1 | 0 |  | 0 |
| `src_pages_udc_application_new-app_index_tsx-node_modules_see` | 16372 | 12 | 1 | 25 |  | 0 |
| `src_components_design_settings_common_data-source-container_` | 16361 | 1 | 0 | 0 |  | 0 |
| `src_pages_design_page-frame_actions_copy-page-frame_index_ts` | 16245 | 14 | 5 | 15 |  | 0 |
| `node_modules_xiaozhua_biz-enums_dist_index-9365ba29_js.e2c6841` | 16026 | 21 | 11 | 17 |  | 0 |
| `src_pages_udc_app-log-config_index_tsx-src_pages_app-design_` | 16009 | 18 | 3 | 12 |  | 0 |
| `src_pages_design_page-frame_sider_tsx.c4c52fcb` | 15185 | 12 | 6 | 13 |  | 0 |
| `src_pages_udc_sandbox_pages_application-test_index_tsx.ed623` | 15028 | 13 | 2 | 8 |  | 0 |
| `src_components_design_asidetool_trans-wrapper_tsx-src_compon` | 14856 | 14 | 3 | 21 |  | 0 |
| `src_components_common_component-select_useComponentsTree_ts-` | 14160 | 18 | 3 | 7 |  | 0 |
| `src_pages_design_main_components_formAppPageInfoEdit_index_t` | 14065 | 9 | 0 | 11 |  | 0 |
| `src_pages_udc_page-frame-tmp-manage_index_tsx.95ba118a` | 13782 | 25 | 8 | 22 |  | 0 |
| `src_pages_app-design_template-manage_index_tsx.7ebad08d` | 13646 | 38 | 4 | 30 |  | 0 |
| `src_pages_app-design_entity-modeling_entity-field_components` | 13621 | 12 | 4 | 11 |  | 0 |
| `src_components_page-content_index_tsx-src_pages_design_const` | 12902 | 7 | 1 | 0 |  | 0 |
| `node_modules_xiaozhua_biz-enums_dist_index-7189faa2_js.4340c5f` | 12607 | 23 | 11 | 13 |  | 0 |
| `src_pages_udc_sandbox_components_common-column_index_tsx-src` | 12376 | 13 | 4 | 9 |  | 1 |
| `src_pages_app-design_rule_dataflow_components_log-content_in` | 12184 | 43 | 3 | 9 |  | 0 |
| `node_modules_xiaozhua_biz-serial-scheme_dist_index-aa2d4add_js` | 12151 | 15 | 6 | 8 |  | 0 |
| `node_modules_xiaozhua_biz-where_dist_modalWhere_js.aac960a8` | 12101 | 11 | 7 | 27 |  | 0 |
| `src_pages_udc_sandbox-manage_index_tsx.12c8fe7e` | 11603 | 18 | 0 | 15 |  | 0 |
| `src_pages_design_functions_components_add-space_index_tsx-no` | 10938 | 4 | 0 | 19 |  | 0 |
| `src_pages_app-design_rule_deductflow_log-content_index_tsx.4` | 10904 | 25 | 0 | 8 |  | 0 |
| `src_pages_app-design_entity-modeling_custom-extension_index_` | 10895 | 20 | 6 | 13 |  | 0 |
| `node_modules_xiaozhua_biz-where_dist_where_js.b3912f02` | 10854 | 11 | 7 | 16 |  | 0 |
| `src_pages_udc_sandbox_pages_app-environment_index_tsx.c5de57` | 10000 | 22 | 5 | 4 |  | 0 |
| `node_modules_xiaozhua_biz-serial-scheme_dist_index-a9cbbe00_js` | 9191 | 15 | 7 | 10 |  | 0 |
| `src_components_design_navbar_controls_cmps_tsx.e95e5a6f` | 9063 | 3 | 1 | 4 |  | 0 |
| `src_hooks_usePageDesignPathParams_ts.2243bb5f` | 8815 | 0 | 0 | 0 |  | 0 |
| `src_pages_app-design_page-rules_index_tsx-src_components_pag` | 8737 | 15 | 5 | 23 |  | 0 |
| `src_components_design_header_index_module_less-src_hooks_use` | 8332 | 0 | 0 | 0 |  | 0 |
| `node_modules_xiaozhua_biz-serial-scheme_dist_index-f62267af_js` | 8182 | 11 | 1 | 7 |  | 0 |
| `node_modules_xiaozhua_biz-serial-scheme_dist_index-63bbd6cd_js` | 8058 | 9 | 0 | 2 |  | 0 |
| `src_app4Exposes_tsx.1714867c` | 6541 | 1 | 0 | 0 |  | 0 |
| `src_pages_design_page-frame_index_tsx-src_utils_getTerminalF` | 6217 | 7 | 0 | 1 |  | 0 |
| `src_pages_design_index_tsx.9330b432` | 6151 | 0 | 0 | 0 |  | 0 |
| `src_pages_design_functions_components_space-desiger_index_ts` | 6144 | 8 | 0 | 0 |  | 0 |
| `node_modules_xiaozhua_biz-enums_dist_index-dfa7dac0_js.4ccc658` | 5983 | 15 | 9 | 10 |  | 0 |
| `src_components_data-type_instance_switch_tsx-src_pages_app-d` | 5636 | 2 | 0 | 7 |  | 0 |
| `src_pages_app-design_rule_microflow_entity-rule_tsx.175321c6` | 5525 | 1 | 0 | 0 |  | 0 |
| `src_pages_app-design_rule_microflow_index_tsx.d188187b` | 5519 | 1 | 0 | 0 |  | 0 |
| `src_pages_app-design_rule_microflow_page-rule_tsx.9fc6df85` | 5519 | 1 | 0 | 0 |  | 0 |
| `src_pages_design_functions_components_backend-default_index_` | 5319 | 19 | 1 | 0 |  | 0 |
| `node_modules_xiaozhua_biz-enums_dist_index-d16a4f98_js.a84d163` | 4764 | 13 | 5 | 5 |  | 0 |
| `src_pages_design_functions_components_add-function_index_tsx` | 4027 | 2 | 0 | 2 |  | 0 |
| `src_components_app-design_app_components_nav-header_import-a` | 3757 | 0 | 0 | 0 |  | 0 |
| `src_pages_design_personal_schemes_index_tsx.5fd5e034` | 3706 | 5 | 2 | 12 |  | 0 |
| `src_pages_design_sub-pages_index_tsx.9ad0800e` | 3557 | 0 | 0 | 0 |  | 0 |
| `src_pages_design_functions_components_outApp-page_index_tsx.` | 3550 | 7 | 0 | 0 |  | 0 |
| `src_pages_udc_app-log-data_config_index_tsx.3ea3e788` | 3489 | 4 | 2 | 5 |  | 0 |
| `src_pages_design_functions_components_edit-preset-page_index` | 3307 | 1 | 0 | 2 |  | 0 |
| `src_pages_design_functions_components_page-info_index_tsx.bc` | 3082 | 3 | 2 | 0 |  | 0 |
| `node_modules_xiaozhua_biz-where_dist_conditionRight_js.76ceea6` | 2682 | 0 | 0 | 8 |  | 0 |
| `src_components_app-design_parameter-definition_entry_tsx-src` | 2230 | 0 | 0 | 0 |  | 0 |
| `src_pages_udc_sandbox_pages_sandbox-log_index_tsx.bb68acba` | 2059 | 0 | 0 | 4 |  | 0 |
| `src_components_udc_udc-wrapper_index_tsx.aaf56dab` | 1902 | 1 | 0 | 1 |  | 0 |
| `src_pages_app-design_extension-plan_entry_tsx-src_components` | 1704 | 1 | 0 | 1 |  | 0 |
| `src_pages_udc_sandbox_pages_index_tsx.88b4dab5` | 1632 | 0 | 0 | 0 |  | 0 |

## 各页明细（按钮 + 关键文案）

### `src_redux_store_ts.14dc061e`

- 按钮：一键下载、上传图片、上传正文完成时、上传的附件、上传结果、上传附件、下一步、下载、下载全部、不保存、不设置全局提示、主题配置、保存失败、保存并复制、保存并提交、保存并新增、保存并设计、保存当前版本、保存待发、保存成功、保存提示、保存新版本、保存草稿、保存记录、停用、停用失败、停用成功、入参配置、关闭、关闭图标
- 组件：Button.Group、Checkbox.Group、Collapse.Panel、Form.Item、Form.useForm、Input.Group、Menu.Item、Radio.Group、Select.Option
- 弹窗/容器：Drawer、Modal、Popconfirm、Tabs、Tree、Upload
- 拖拽：有
- 文案：一对一 | 一对一实体不存在: | 一致性校验失败 | 一致性检查 | 一键下载 | 一键换文 | 一键换文切换 | 一键换文初始化 | 上下文变量解析前 | 上下文变量解析后 | 上传图片 | 上传正文完成时 | 上传的附件 | 上传结果 | 上传附件 | 上侧 | 上侧区域 | 上分区 | 上图标下文字 | 上文字下图标 | 上移 | 上级分类 | 上级枚举不能为空 | 下一步 | 下一节点信息 | 下一节点显示内容 | 下一节点选择方式 | 下侧 | 下侧区域 | 下分区 | 下划线(_) | 下发 | 下发授权 | 下拉字段 | 下移 | 下载 | 下载全部 | 下载对应附件控件下所有附件内容 | 不保存 | 不再处理

### `src_components_design_settings_common_operate-list_operateCmp_operateC`

- 按钮：下载文件、不设置全局提示、个性化参数设置、事件参数必须设置、事件覆盖确认、保存、保存成功、关闭、关闭图标、关闭方式、关闭页面布局、列宽设置、列配置、删除、删除参照携带、删除参照携带容器、删除文件、参数信息保存成功、参照方案设置、取消、取消阅、取消阅处、取消阅示、复制子页面、复制成功、宽度设置、密级设置、导出方式、导航配置、已设置
- 组件：Checkbox.Group、Collapse.Panel、Form.Item、Form.useForm、Menu.Item、Radio.Group、Select.Option
- 弹窗/容器：Modal、Popconfirm、Tabs、Tree、Upload
- 拖拽：有
- 文案：一对一 | 一对一实体不存在: | 一对多实体不存在: | 上午 09:40 | 上午 9:40 | 上级枚举 | 下拉字段 | 下拉样式 | 下拉框 | 下盖时拍照 | 下载文件 | 不可选范围 | 不在参照列表中显示，一般用于自定义列的计算 | 不录制 | 不支持同一个控件被多个跟随位置的面板绑定 | 不支持的节点类型 | 不能为空 | 不能大于最大值 | 不能小于最小值 | 不能输入特殊字符 | 不设置全局提示 | 与数据控件一致 | 个性化参数设置 | 个税扣缴义务人 | 中性灰 | 中间区 | 主按钮 | 主表 | 主题 | 九月十九日 | 事件 | 事件动作 | 事件参数必须设置 | 事件参数映射规则(子页面/外框) | 事件名称不能为空 | 事件覆盖确认 | 事项中心 | 二〇二一年九月 | 二〇二一年九月十九日 | 仅图标

### `src_components_app-design_app_components_theme_app-style-designer-mode`

- 按钮：上传图片、全选、全选时、分辨率设置、列分组配置、列配置、删除、删除分组、删除行、取消、取消全选时、取消勾选行、取消勾选行时、可折叠、向上添加分组、启用分页、启用操作列、启用节标题、启用行序号、启用跳转、启用过滤、基础设置、基础配置、复制、复制行、展开、展开全部一级节点、展开全部节点、展开方式、展开面板
- 组件：Form.Item、Form.useForm、Grid.Item、List.Item、Menu.Item
- 弹窗/容器：Modal、Tabs、Tree、Upload
- 拖拽：无
- 文案：一列 | 一级节点 | 一般用于弹窗页面数据变更后，控件自动刷新。需订阅父页面中操作的实体。 | 三级 1-1-1 | 三级 1-1-2 | 三级 1-1-3 | 三级 1-1-4 | 三级 1-1-5 | 三级 1-1-6 | 三级 1-1-7 | 三级 1-2-1 | 三级 1-2-10 | 三级 1-2-2 | 三级 1-2-3 | 三级 1-2-4 | 三级 1-2-5 | 三级 1-2-6 | 三级 1-2-7 | 三级 1-2-8 | 三级 1-2-9 | 上一条 | 上传图片 | 上侧 | 上侧高度 | 下一条 | 下侧 | 下侧高度 | 下拉显示 | 不换列 | 不换行 | 不显示 | 不限制行数 | 业务规则 | 两列 | 严重 | 中间区 | 主按钮 | 主轴 | 主轴方向 | 主题

### `dataflow-relation`

- 按钮：保存、删除提示、取消、已设置、提交、提示设置、新建或更新数据、新建数据、映射规则设置、是，前往保存、未设置、条件设置不正确、查看日志、点击设置内容、确定删除此数据、确认、编辑、编辑标题、要保存修改吗、设置、详情入参配置、请设置显示字段、请输入提示设置
- 组件：Checkbox.Group、Form.Item、Form.useForm、Radio.Group
- 弹窗/容器：Drawer、Modal、Popconfirm、Tabs、Tree
- 拖拽：有
- 文案：事件名称 | 事件属性 | 事件描述 | 事件过滤条件 | 仅文本、多行文本类型字段支持快捷搜索。仅在移动端生效 | 保存 | 保留已有映射组 | 像素 | 删除提示 | 升序 | 取消 | 可选字段 | 否，放弃修改 | 回写前置条件 | 回写时机 | 回写规则 | 基础信息 | 字段映射规则 | 实体映射规则 | 实体映射规则未配置 | 已设置 | 已选字段 | 当同一条来源数据允许多次推单时，可在此配置依据哪个字段进行拆单。 | 提交 | 提示设置 | 操作成功 | 新建或更新数据 | 新建数据 | 映射条件 | 映射来源实体 | 映射目标实体 | 映射类型 | 映射规则 | 映射规则设置 | 是，前往保存 | 更新数据 | 未找到相应数据 | 未设置 | 条件设置不正确 | 来源

### `src_pages_app-design_rule_dataflow_relation-graph_index_tsx.0ffd5e24`

- 按钮：保存、删除提示、取消、已设置、提交、提示设置、新建或更新数据、新建数据、映射规则设置、是，前往保存、未设置、条件设置不正确、查看日志、点击设置内容、确定删除此数据、确认、编辑、编辑标题、要保存修改吗、设置、详情入参配置、请设置显示字段、请输入提示设置
- 组件：Checkbox.Group、Form.Item、Form.useForm、Radio.Group
- 弹窗/容器：Drawer、Modal、Popconfirm、Tabs、Tree
- 拖拽：有
- 文案：事件名称 | 事件属性 | 事件描述 | 事件过滤条件 | 仅文本、多行文本类型字段支持快捷搜索。仅在移动端生效 | 保存 | 保留已有映射组 | 像素 | 删除提示 | 升序 | 取消 | 可选字段 | 否，放弃修改 | 回写前置条件 | 回写时机 | 回写规则 | 基础信息 | 字段映射规则 | 实体映射规则 | 实体映射规则未配置 | 已设置 | 已选字段 | 当同一条来源数据允许多次推单时，可在此配置依据哪个字段进行拆单。 | 提交 | 提示设置 | 操作成功 | 新建或更新数据 | 新建数据 | 映射条件 | 映射来源实体 | 映射目标实体 | 映射类型 | 映射规则 | 映射规则设置 | 是，前往保存 | 更新数据 | 未找到相应数据 | 未设置 | 条件设置不正确 | 来源

### `src_pages_app-design_basic-info_index_tsx-node_modules_xiaozhua_biz-icon`

- 按钮：保存失败、保存成功、发布中、发布失败、发布成功、发布时间、发布版本、发布状态、取消、团队设置、已发布、未发布、添加成员、确定、确定删除吗、确认、移动端、移除成功、组件已停用、页面发布中、页面发布失败、页面发布开始、页面发布成功、页面发布资源不足、页面发布超时、页面未开始发布
- 组件：Collapse.Panel、Form.Item、Form.useForm、Menu.Item、Radio.Group
- 弹窗/容器：Modal、Popconfirm、Tabs、Tree
- 拖拽：无
- 文案：依赖应用 | 依赖版本调整 | 依赖组件 | 依赖调整成功 | 保存失败 | 保存成功 | 修改失败 | 修改应用基础信息 | 元数据中心未找到该应用数据 | 元数据地址: | 全部 | 前端安装依赖详细日志: | 前端构建详细日志: | 包名 | 升级版本 | 历史状态 | 发布中 | 发布失败 | 发布成功 | 发布时间 | 发布版本 | 发布状态 | 发布的上一次测试版本 | 取消 | 名称 | 后端构建详细日志: | 团队成员 | 团队设置 | 图标 | 失败原因 | 已发布 | 平台 | 应用主题风格 | 应用名称 | 应用启动中 | 应用启动失败: | 应用启动成功 | 应用图标 | 应用描述 | 应用数据清除成功

### `src_pages_app-design_rule_index_tsx-node_modules_xiaozhua_biz-udc-graph_`

- 按钮：删除、必须配置扣减算法、扣减规则设置、新建分组、是，前往保存、查看日志、欢迎来到规则设置、添加、添加扣减规则、编辑标题、表达式设置、设置规则、请设置提示信息、请设置来源字段
- 组件：Form.Item、Form.useForm、Menu.Item、Radio.Group
- 弹窗/容器：Drawer、Modal、Popconfirm、Tabs、Tree
- 拖拽：有
- 文案：不能下划线结尾 | 不能使用连续的下划线 | 分组名称 | 删除 | 只能以字母开头，允许输入数字、字母和下划线 | 名称 | 名称不能为空 | 名称不能为重复 | 名称不能重复 | 否，放弃修改 | 在算法运行时，检查当前是否具备算法执行的必要条件 | 备注 | 已经修改完成 | 开始节点只能是单据节点 | 当前扣减规则图中没有来源，请设置来源之后再保存。 | 微流程 | 必须配置扣减算法 | 扣减算法不能为空 | 扣减算法提示 | 扣减规则 | 扣减规则设置 | 提示信息 | 提示并阻塞 | 操作 | 操作成功 | 新建分组 | 是，前往保存 | 是，前往修改 | 最长100个字符 | 有数据未能匹配时 | 未匹配数据跳过扣减继续执行 | 来源字段类型和目标字段不一致 | 来源实体 | 来源实体、目标实体之间已存在扣减规则，请检查 | 查看日志 | 检查未通过提示 | 检查规则 | 欢迎来到规则设置 | 注: 发布后，草稿状态的微流程无法使用 | 添加

### `src_components_design_stage_index_tsx.d0430eab`

- 按钮：关闭上侧区域、关闭下侧区域、关闭右侧区域、关闭左侧区域、删除控件、复制控件
- 组件：Breadcrumb.Item、Menu.Item
- 弹窗/容器：Modal
- 拖拽：无
- 文案：上侧 | 下侧 | 个字段 | 中间区 | 关闭上侧区域 | 关闭下侧区域 | 关闭右侧区域 | 关闭左侧区域 | 其他用户 | 删除控件 | 右侧 | 复制控件 | 左侧 | 开启上侧区域 | 开启下侧区域 | 开启右侧区域 | 开启左侧区域 | 拖拽组件 | 自适应宽度 | 隐藏控件（可通过大纲重新显示）

### `src_pages_design_functions_index_tsx-src_components_page-params_compon`

- 按钮：上方添加菜单、上方添加页面、下方添加菜单、下方添加页面、不支持向上移动、删除成功、取消、取消首页、复制、复制成功、复制空间、复制页面、提交成功、查看属性、添加、添加分组、添加空间、添加菜单、添加页面、确定、移动、编辑、设置页面入参
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：上方添加菜单 | 上方添加页面 | 上移 | 下方添加菜单 | 下方添加页面 | 下移 | 不支持向上移动 | 不支持该操作 | 不支持重命名 | 你输入的名称过长 | 入参 | 入参: | 公共页面规则 | 其他页面不能拖动到首页 | 分组 | 分组不能拖到其他分组下面 | 删除成功 | 升级 | 单据 | 取消 | 取消首页 | 变更记录 | 只支持同一层级下的菜单或页面批量移动 | 只能包含中文、英文、数字以及下划线 | 同时删除对应 WEB 页面 | 同时删除对应 WEB端 页面及引用页面 | 同时删除对应 移动端 页面 | 同时删除对应移动端页面 | 向上 | 向下 | 基础设置不能拖到其他菜单下面 | 复制 | 复制成功 | 复制空间 | 复制页面 | 外链 | 子菜单 | 平铺档案 | 应用首页或门户不允许添加页面 | 引用

### `src_components_page-params_index_tsx-src_utils_treeUtils_page-selector`

- 按钮：信息保存成功、参数设置、取消、添加入参、添加变量、确定、确认、设置值、页面事件保存成功、页面事件删除成功
- 组件：Form.Item、Form.useForm、Select.Option
- 弹窗/容器：Modal、Popconfirm、Tree
- 拖拽：无
- 文案：不能包含下划线 | 不能输入空格 | 为列表时，默认值无效 | 信息保存成功 | 列表 | 单选 | 参数类型 | 参数设置 | 取消 | 只能以字母开头，允许输入数字、字母 | 名称 | 名称不能超过10个字 | 名称必填 | 名称禁止输入空格 | 多选 | 实体 | 对象 | 提示 | 数据类型 | 日期 | 日期时间 | 时间 | 暂无数据 | 枚举 | 添加入参 | 添加变量 | 确定 | 确认 | 编码 | 编码必填 | 编码禁止输入空格 | 至少保留一个参数 | 设置值 | 请勾选数据 | 请输入名称 | 请输入编码 | 请选择 | 请选择参数类型 | 请选择实体 | 请选择枚举

### `src_pages_udc_application_index_tsx.a0f20272`

- 按钮：上传文件、删除、发布、发布应用、发布版本、发布目标环境、取消、复制、复制应用、导入应用、导入应用包、导入方式、导出、导出应用、导出应用成功、应用包导入失败、应用包导入成功、应用复制失败、确定、请先上传应用包、请选择发布版本
- 组件：Form.Item、Form.useForm、Menu.Item、Radio.Group、Select.Option
- 弹窗/容器：Modal
- 拖拽：无
- 文案：上传文件 | 创建时间 | 删除 | 发布 | 发布应用 | 发布版本 | 发布目标环境 | 取消 | 另存为新版本成功 | 复制 | 复制应用 | 导入应用 | 导入应用包 | 导入方式 | 导出 | 导出应用 | 导出应用成功 | 已上架 | 平台版本 | 应用包导入失败 | 应用包导入成功 | 应用名称 | 应用复制失败 | 应用所属人 | 应用编码 | 应用还未测试启动过，无法发布 | 所属机构 | 所有版本 | 操作 | 最多输入50个字符 | 版本号 | 版本号不得低于原版本的版本号 | 版本号不得高于下一个大版本号 | 版本号已存在 | 版本号整数部分和小数部分不得超过4位 | 版本描述 | 版本管理 | 状态 | 生成新版本 | 确定

### `src_components_design_select-box_select-cmps_tsx-src_containers_design`

- 按钮：一键展开、保存失败、删除、复制页面规则、复制页面规则失败、已设置表达式、新建分组、移动端
- 组件：Checkbox.Group、Form.Item、Form.useForm、Gy.Item、Menu.Item、Radio.Group、Select.Option
- 弹窗/容器：Modal、Tabs、Tree
- 拖拽：有
- 文案：一键展开 | 一键收起 | 不允许选择多个面板的控件 | 保存失败 | 公共页面规则 | 分组名称 | 删除 | 单据 | 名称 | 复制 PC 端规则 | 复制页面规则 | 复制页面规则失败 | 外框 | 大纲 | 子页面 | 已设置表达式 | 平铺档案 | 控件 | 提示 | 操作成功 | 数据 | 新建分组 | 显示 | 最长100个字符 | 未找到匹配记录 | 未找到调用方 | 查找调用控件 | 标准 | 树形档案 | 正式 | 状态由条件控制 | 目标页面 | 目标页面不能为空 | 移动端 | 筛选 | 表单 | 规则 | 请输入搜索关键字 | 请输入页面规则名称 | 请选择目标页面

### `src_pages_app-design_entity-modeling_entity-fieldset_index_tsx.fdeccdc`

- 按钮：删除、删除成功、取消、新建字段集、确定、编辑、编辑字段集
- 组件：Form.Item、Form.useForm、Radio.Group、Select.Option
- 弹窗/容器：Modal、Popconfirm
- 拖拽：无
- 文案：上级枚举字段 | 不能大于最大长度 | 不能小于最小长度 | 修改字段的数据类型会导致引用字段处报错，且会清除该字段的测试数据。 | 全文检索 | 关系类型 | 关联 | 删除 | 删除成功 | 取消 | 名称 | 唯一 | 基础 | 多选 | 字段发布之后，最大长度只能改大 | 字段发布之后，最小长度只能改小 | 字段集名称 | 字段集编码 | 实体 | 审计 | 小数位允许变大，不允许变小 | 小数位数 | 开启或关闭多选会导致引用字段处报错，且会清除该字段的测试数据。 | 必填 | 必填唯一 | 总长度 | 总长度允许变大，不允许变小 | 描述 | 敏感词检测 | 数据国际化 | 新建字段集 | 日期 | 日期时间 | 时间 | 最大值 | 最大长度 | 最小值 | 最小长度 | 枚举 | 校验

### `src_components_app-design_app_components_theme_index_ts-src_components`

- 按钮：已设置表达式、拖拽排序
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：伸缩 | 多级表头 | 已设置表达式 | 拖拽排序 | 操作列 | 节操作 | 表头搜索 | 配置排序规则后，该属性不生效 | 顶部操作

### `src_pages_app-design_basic-setting_index_tsx-node_modules_xiaozhua_biz-b`

- 按钮：保存成功、停用、删除、删除成功、取消、启用、导入导出模板、已设置、排序号、新建分类、新建选项集、未设置、确定、编辑、编辑分类、编辑成功、编辑选项集、选项集导入模板、重置
- 组件：Form.Item、Form.useForm、Menu.Item、Select.Option
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：中性灰 | 主题 | 二维码 | 你输入的分类名称过长 | 你输入的选项集名称过长 | 保存成功 | 信息 | 停用 | 其他 | 内置 | 创建成功 | 删除 | 删除成功 | 功能 | 参数 | 取消 | 只能是大写字母开头，允许输入数字和字母 | 名称 | 名称为必填项 | 启用 | 固定选项的合集，仅在设计态定义，仅支持一级，不支持运行态扩展。 | 图标 | 图片 | 基础 | 基础资料 | 填充 | 外框模板 | 字段集 | 导入导出模板 | 已经上架的选项集不能删除 | 已设置 | 成功 | 扩展实体 | 排序号 | 搜索时不支持拖动 | 支持自定义对象，用于微流程/页面规则之间的相互调用数据传递 | 文字 | 新建分类 | 新建选项集 | 未设置

### `src_components_design_data-source_index_tsx.ecc90bb0`

- 按钮：展开、拖拽数据操作取消
- 组件：—
- 弹窗/容器：Tree
- 拖拽：无
- 文案：一对一 | 一对多 | 分组 | 可拖拽字段到页面中 | 可用的关系数据源为空 | 大数据类型字段不允许拖到重复表中 | 实体 | 实体不允许拖到重复表中 | 实体关系 | 实体列表 | 展开 | 拖入字段与当前数据控件的数据源不符 | 拖拽数据操作取消 | 数据控件请先绑定数据源，再拖动字段 | 无法拖拽一对一实体到设计器，但可拖拽其下级字段 | 请将字段拖到合法的控件中 | 请将字段拖到数据控件中 | 请输入搜索关键字 | 选择多个实体下字段，对应实体必须选中

### `src_components_app-design_parameter-definition_index_tsx.d0a30409`

- 按钮：保存成功、取消、已设置、已设置表达式、排序号、新建参数、确定
- 组件：Form.Item、Form.useForm、Radio.Group、Select.Option
- 弹窗/容器：Modal、Popconfirm
- 拖拽：无
- 文案：不能大于最大值 | 不能小于最小值 | 保存成功 | 分组 | 参数属性 | 取消 | 只能输入数字字母下划线 | 名称 | 已设置 | 已设置表达式 | 排序号 | 描述 | 操作 | 数据类型 | 新建参数 | 确定 | 编码 | 表达式 | 请输入 | 请输入名称 | 请输入字段 | 选择上级枚举 | 默认值

### `src_components_design_top-tool-bar_index_tsx.bf7936ab`

- 按钮：保存失败、保存并提交、保存模板成功、移动端页面、请上传缩略图、转移动
- 组件：Checkbox.Group、Form.Item、Radio.Group
- 弹窗/容器：Modal、Tree
- 拖拽：无
- 文案：不开启时，web端网格控件不转换，网格中控件转换后会顺序排列 | 保存失败 | 保存并提交 | 保存模板成功 | 全屏 | 另存为模板 | 只能包含中文、英文、数字以及下划线 | 名称 | 名称不能超过50个字符 | 存模版 | 已存在重名的页面模版，请重新命名 | 当前页面是草稿态，可能导致应用检查无法定位问题，请注意保存页面。 | 描述 | 检测到已存在控件 | 概览 | 状态由条件控制 | 移动端和web端页面都 | 移动端页面 | 继续转换将为其创建为副本 (唯一标识将重新生成) | 请上传WEB端缩略图 | 请上传移动端缩略图 | 请上传缩略图 | 请输入名称 | 请输入描述 | 转换成功 | 转换范围 | 转移动 | 退出全屏

### `src_containers_design_settings_index_tsx.d00dcd9e`

- 按钮：分辨率设置、参数设置、可编辑列表页、页面入参设置、页面变量设置
- 组件：—
- 弹窗/容器：Tabs、Tree
- 拖拽：无
- 文案：上图标下文字 | 上文字下图标 | 业务首页 | 事件 | 事件列表 | 作为标题展示在Web端页签 | 作为标题展示在移动端页面标题栏 | 公开访问 | 其它 | 分辨率设置 | 列表详情组合页 | 列表页 | 单击时 | 参数设置 | 可编辑列表页 | 名称 | 固定 | 基础 | 外框 | 外框事件 | 外框布局 | 审批页 | 导航布局 | 导航样式 | 居中 | 居右 | 居左 | 属性 | 应用门户 | 底导航 | 悬浮 | 报表页 | 更多 | 标识 | 标题 | 栏目参数个性化 | 栏目页 | 类型 | 自定义导航 | 详情页

### `src_components_unify-console_items_operation-log_index_tsx.f29f0868`

- 按钮：删除
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：修改 | 元素 | 公共页面规则 | 创建 | 删除 | 外框 | 子页面 | 字段集 | 定位 | 属性 | 属性值（操作前） | 属性值（操作后） | 应用 | 应用版本 | 微流程 | 快照 | 扣减规则 | 操作 | 操作人 | 操作元素 | 操作时间 | 未知的微流程类型 | 栏目 | 模块 | 生单规则 | 自定义对象 | 获取初始化数据失败 | 菜单 | 该模块元素已不存在，无法定位。 | 请输入 | 请输入模块名称 | 请选择 | 还原 | 还原到 | 还原操作成功 | 选项集 | 门户

### `src_pages_design_functions_components_page-info-edit_index_tsx.d598ef8`

- 按钮：添加移动端分组、移动端
- 组件：Form.Item、Form.useForm、Select.Option
- 弹窗/容器：Modal
- 拖拽：无
- 文案：分组名称 | 归属修改成功 | 接入手工开发的页面时勾选 | 添加移动端分组 | 移动端 | 请输入页面名称 | 请输入页面标识 | 请选择web端页面归属 | 请选择实体 | 请选择移动端端页面归属 | 适配终端 | 页面名称 | 页面对应实体 | 页面标识 | 页面类型

### `src_pages_design_portlet_index_tsx-src_utils_getTerminalFromApi_ts-src`

- 按钮：删除、删除分组成功、删除文件夹、删除栏目成功、删除静态栏目页面、取消、栏目分组添加成功、添加分组、添加栏目、添加栏目成功、确定、移动端、编辑
- 组件：Checkbox.Group、Form.Item、Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：你输入的名称过长 | 修改栏目成功 | 公共页面规则 | 分组 | 分组不能拖到其他分组下面 | 分组名称 | 删除 | 删除分组成功 | 删除文件夹 | 删除栏目成功 | 删除静态栏目页面 | 单据 | 取消 | 只能包含中文、英文、数字以及下划线 | 名称不能为空 | 平铺档案 | 接入手工开发的页面时勾选 | 标准 | 栏目不能拖到其他栏目下面 | 栏目分组 | 栏目分组添加成功 | 栏目名称 | 栏目名称只能包含中文、英文、数字以及下划线 | 栏目标识 | 树形档案 | 欢迎来到栏目空间 | 添加分组 | 添加栏目 | 添加栏目成功 | 确定 | 移动端 | 编辑 | 表单 | 请输入分组名称 | 请输入栏目名称 | 请输入栏目标识 | 请选择栏目分组 | 请选择适配终端 | 适配终端 | 重命名

### `src_pages_app-design_extension-plan_index_tsx.c111914a`

- 按钮：删除、取消、新建扩展实体、确定、编辑、编辑扩展实体、预览
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal、Popconfirm
- 拖拽：无
- 文案：值范围 | 删除 | 取消 | 多选 | 字段发布之后，最大长度只能改大，最小长度只能改小 | 字段名称前缀 | 字段类型 | 小数位数 | 开启后，扩展字段数据在名称变更后，不会发生变化，仍为当时名称 | 开启快照 | 当前字段名称前缀已存在，不能重复添加 | 扩展实体名称 | 扩展实体是一组预留的空白字段，实体中关联后，可在运行态启用这些字段。 | 扩展实体编码 | 扩展方案 | 操作 | 新建扩展实体 | 最多预留 20 个 | 最大值不能小于最小值 | 最大长度不能为0 | 最大长度不能小于最小长度 | 最小值不应该超过最大值 | 最小值不能大于最大值 | 最小长度不能大于最大长度 | 确定 | 编辑 | 编辑扩展实体 | 请输入 | 请输入字段名称前缀 | 请输入小数位数 | 请输入扩展实体名称 | 请输入扩展实体编码 | 请输入最大值 | 请输入最大长度 | 请输入最小值 | 请输入最小长度 | 请输入预留字段数量 | 请选择字段类型 | 请选择方案 | 选择实体

### `src_components_page-content_index_tsx-src_components_welcome_index_tsx`

- 按钮：删除、复制、是，前往保存、暂不支持复制分组、暂不支持批量删除、暂不支持批量复制、添加、添加分组、添加成功、确认删除、移动、要保存修改吗
- 组件：—
- 弹窗/容器：Modal
- 拖拽：无
- 文案：上移 | 下移 | 不支持上移 | 不支持下移 | 公共页面规则 | 分组不能移动到分组内部 | 删除 | 单据 | 变更记录 | 名称或编码 | 名称长度不能超过100 | 否，放弃修改 | 复制 | 平铺档案 | 微流程 | 微流程创建失败 | 提示 | 是，前往保存 | 暂不支持复制分组 | 暂不支持批量删除 | 暂不支持批量复制 | 更新成功 | 查找 | 标准 | 树形档案 | 正式 | 添加 | 添加分组 | 添加成功 | 确认删除 | 移动 | 表单 | 要保存修改吗 | 选择的微流程或分组无法移动 | 重命名 | 默认分组

### `src_pages_udc_app-log-data_list_index_tsx.f4b17d52`

- 按钮：删除、新增、新增字段明细、新增明细表行
- 组件：—
- 弹窗/容器：Tabs、Tree
- 拖拽：无
- 文案：业务应用 | 修改 | 修改字段明细 | 全部 | 删除 | 名称、编码 | 实体ID | 审批应用 | 应用数据日志 | 操作 | 操作人员 | 操作实体 | 操作时间 | 操作类型 | 收起 | 新增 | 新增字段明细 | 新增明细表行 | 暂无数据，请选择左侧应用获取配置信息 | 更多

### `src_pages_udc_upgrade-deploy_index_tsx.0c901b15`

- 按钮：删除成功、发布中、发布失败、发布成功、发布状态、发布类型、启用状态、已启用、未发布、未启用、移动端、自动生成不可编辑
- 组件：Checkbox.Group、Form.Item、Form.useForm
- 弹窗/容器：Modal、Popconfirm、Tabs
- 拖拽：无
- 文案：上次更新时间 | 全部应用 | 删除成功 | 前端 | 前端组件名称 | 发布中 | 发布失败 | 发布成功 | 发布状态 | 发布类型 | 后端 | 启用状态 | 失败原因 | 失败数 | 宿主应用 | 已启用 | 应用名称 | 应用更新中 | 应用类型 | 应用编码 | 成功数 | 批次号 | 指定前端组件 | 指定应用 | 按照下面的查询条件更新应用 | 操作 | 更新日期 | 更新条件 | 更新记录 | 更新说明 | 未发布 | 未启用 | 本环境 | 查询指定应用 | 测试环境 | 版本 | 环境 | 移动端 | 组件更新出现未知错误 | 终端

### `src_pages_udc_customtype_index_tsx.21130696`

- 按钮：取消、确定
- 组件：Form.Item、Form.useForm、Radio.Group
- 弹窗/容器：Popconfirm
- 拖拽：无
- 文案：不能大于最大值 | 不能大于最大长度 | 不能小于最小值 | 不能小于最小长度 | 关联实体 | 匹配规则 | 取消 | 名称 | 基础类型 | 多选 | 小数位数 | 操作 | 显示名称 | 最大值 | 最大长度 | 最小值 | 最小值超出设定小数位数 | 最小长度 | 确定 | 类型 | 自动生成（可修改） | 请输入 | 请输入匹配正则规则 | 请输入名称 | 请输入搜索关键字 | 请输入显示名称 | 请输入类型 | 请输入错误时提示信息 | 请选择 | 请选择关联实体 | 请选择应用 | 请选择需要删除的数据 | 选择应用 | 错误时提示 | 默认值 | 默认值超出设定小数位数

### `src_containers_design_page-design_index_tsx.6e093388`

- 按钮：不保存、保存、全选、删除、取消、复制
- 组件：—
- 弹窗/容器：Modal
- 拖拽：无
- 文案：不保存 | 保存 | 全选 | 删除 | 剪切 | 取消 | 复制 | 已知晓 | 当前页面是草稿态，可能导致应用检查无法定位问题，请先保存页面。 | 恢复 | 撤销 | 离开实体设计器时 | 离开页面设计器时 | 粘贴 | 退出

### `src_pages_design_main_components_add-page_index_tsx.c6d3edce`

- 按钮：添加移动端分组、移动端
- 组件：Checkbox.Group、Form.Item、Form.useForm、Select.Option
- 弹窗/容器：Modal
- 拖拽：无
- 文案：分组名称 | 归属 | 接入手工开发的页面时勾选 | 添加移动端分组 | 移动端 | 菜单名称 | 请输入页面名称 | 请选择实体 | 请选择适配终端 | 请选择页面对应实体 | 请选择页面类型 | 适配终端 | 页面名称 | 页面对应实体 | 页面标识 | 页面类型

### `src_pages_udc_cmps_index_tsx-node_modules_xiaozhua_biz-icon-library_dist`

- 按钮：停用、前端组件同步日志、前端组件导入、启用、组件导入成功
- 组件：Form.Item、Form.useForm、Menu.Item、Radio.Group
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：停用 | 全部状态 | 其他 | 前端组件同步日志 | 前端组件导入 | 包名 | 历史版本信息 | 名称 | 启用 | 基础信息 | 描述 | 操作成功 | 时间 | 是否要进行版本同步 | 版本号 | 版本时间 | 状态 | 类型 | 组件中文名 | 组件信息 | 组件名称 | 组件图标 | 组件导入成功 | 组件描述 | 自定义 | 请输入 | 请输入名称或编码搜索 | 请输入完整包名 | 输入的顺序超出限制 | 顺序 | 顺序需要大于0

### `src_components_design_settings_common_style-selector_index_module_less`

- 按钮：已绑定表达式
- 组件：Radio.Group
- 弹窗/容器：Drawer、Tree
- 拖拽：无
- 文案：事件 | 只读 | 工具栏操作 | 已绑定表达式 | 必填 | 控件 | 搜索控件 | 操作列 | 正常 | 状态 | 禁用 | 节操作 | 计算值 | 隐藏 | 顶部操作 | 默认值

### `src_constants_design_page-type_ts-src_services_app-design_template_ts-`

- 按钮：全表编辑页、移动端
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：全表编辑页 | 其它 | 列表页 | 外框 | 子页面 | 栏目页 | 移动端 | 详情页

### `src_pages_udc_backend-cmp_index_tsx-node_modules_xiaozhua_biz-icon-libra`

- 按钮：后端组件导入、导入成功、请上传第三方组件
- 组件：Form.Item、Form.useForm、Menu.Item、Radio.Group、Select.Option
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：全部版本 | 全部类型 | 历史版本信息 | 名称 | 后端组件导入 | 基础信息 | 导入成功 | 描述 | 操作成功 | 是否要进行版本同步 | 更新成功 | 版本 | 版本号 | 版本时间 | 版本类型 | 状态 | 第三方 | 第三方组件包 | 类型 | 组件信息 | 组件图标 | 自定义 | 请上传第三方组件 | 请输入 | 请输入名称、groupId、artifactId搜索 | 请选择 | 输入的顺序超出限制 | 顺序 | 顺序需要大于0 | 预置

### `src_pages_design_sub-pages_sider_tsx.ab0f4794`

- 按钮：删除成功、复制子页面、复制成功、新增、移动端、编辑
- 组件：Checkbox.Group、Form.Item、Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：你输入的标识过长 | 删除成功 | 只能输入字母 | 复制子页面 | 复制成功 | 子页面名称 | 子页面标识 | 新增 | 移动端 | 终端 | 编辑 | 请勾选终端 | 请输入子页面名称 | 请输入子页面标识

### `src_pages_app-design_entity-modeling_enum-manger_enum-field_index_tsx`

- 按钮：删除成功、取消、新建组、确定、移动至
- 组件：Collapse.Panel、Form.Item、Form.useForm、Select.Option
- 弹窗/容器：Drawer、Modal、Popconfirm
- 拖拽：无
- 文案：修改成功，你可以继续下列操作： | 创建枚举 | 删除成功 | 取消 | 您确定要删除此信息吗 | 操作 | 新建组 | 显示名称 | 枚举值 | 枚举项 | 枚举项值 | 枚举项名称 | 枚举项显示名称 | 确定 | 移动至 | 组名 | 自动生成（可修改） | 请输入 | 请输入组名 | 请选择 | 选择分组

### `src_hooks_useGetPageLocked_ts-src_redux_design_actions_shortcuts_tsx.0`

- 按钮：向上添加、移除
- 组件：Form.Item
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：分组 | 列数 | 向上添加 | 容器 | 撤销部分数据还原失败 | 移除 | 网格 | 请输入列数 | 转为 | 页签

### `src_pages_udc_sandbox_pages_elastic-deployment_index_tsx.b0321575`

- 按钮：删除成功、查看应用
- 组件：—
- 弹窗/容器：Modal
- 拖拽：无
- 文案：创建时间 | 删除成功 | 启动中 | 启动失败 | 已停止 | 已启动 | 应用名称 | 应用版本 | 应用编码 | 弹性容器ID | 弹性容器创建成功 | 操作 | 更新时间 | 构建时间 | 查看应用 | 查询成功 | 检测完成 | 正在启动 | 状态 | 请选择状态 | 运行中

### `src_pages_app-design_app-home_space-manage_SpaceManger_tsx.e54d3ae5`

- 按钮：关闭、删除成功、请输入整数排序号
- 组件：Form.Item、Form.useForm、Radio.Group
- 弹窗/容器：Modal
- 拖拽：无
- 文案：修改成功 | 关闭 | 删除后不可恢复，确定删除指定空间 | 删除成功 | 只能删除停用的空间 | 空间名称 | 请输入整数排序号

### `src_pages_udc_sandbox_pages_sandbox-resource_index_tsx-src_pages_udc_s`

- 按钮：删除成功、已停用、已启用、查看应用、配置规则
- 组件：—
- 弹窗/容器：Modal
- 拖拽：无
- 文案：创建失败 | 创建时间 | 删除成功 | 卸载成功 | 已停用 | 已启用 | 应用名称 | 应用版本 | 应用编码 | 操作 | 新建沙箱前请确认是否已上传沙箱镜像到镜像仓库，如未上传将会导致沙箱新建失败。 | 更新时间 | 最近活跃时间 | 构建时间 | 查看应用 | 查询成功 | 检测完成 | 正在重启 | 沙箱ID | 沙箱创建成功 | 沙箱删除后沙箱内的应用将同步删除，该操作不可撤销，请谨慎操作。 | 沙箱版本 | 状态 | 租户名称 | 请选择状态 | 配置规则 | 重启失败

### `src_pages_udc_templateManage_index_tsx.edf44d56`

- 按钮：删除、删除成功、取消、复制成功、排序号、新建分类、添加分类、确定、移动端、编辑模板
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal、Popconfirm、Tree
- 拖拽：无
- 文案：主子实体 | 你输入的名称过长 | 修改成功 | 分类名称 | 创建人 | 创建分类 | 创建时间 | 删除 | 删除成功 | 单据 | 取消 | 只能包含中文、英文、数字以及下划线 | 名称不能超过10个字符 | 复制成功 | 平台预置 | 平铺档案 | 序号 | 应用创建 | 所属应用 | 排序号 | 推荐标签 | 操作 | 新建分类 | 无实体 | 标准 | 标准应用 | 树形档案 | 模板分类 | 模板名称 | 模板描述 | 模板描述不能为空 | 模板来源 | 添加分类 | 独立实体 | 确定 | 移动端 | 终端 | 编辑模板 | 缩略图 | 表单

### `src_pages_udc_sandbox_pages_sandbox-application_index_tsx-src_pages_ud`

- 按钮：保存成功、删除、删除成功、取消、新增、新增成功、是否确定删除、查看、确定、编辑
- 组件：Form.useForm、Radio.Group、Select.Option
- 弹窗/容器：Modal、Popconfirm
- 拖拽：无
- 文案：保存成功 | 创建应用数 | 创建应用数、测试运行数不能为0 | 删除 | 删除成功 | 取消 | 新增 | 新增成功 | 是否确定删除 | 查看 | 测试运行数 | 确定 | 租户ID | 租户名称 | 编辑 | 请选择租户名称

### `src_components_design_outline_components_utils_ts.b77eaf66`

- 按钮：已设置表达式
- 组件：Gy.Item
- 弹窗/容器：Tabs
- 拖拽：无
- 文案：上侧区域 | 下侧区域 | 不能拖入到页签根部，请拖入指定页签 | 单元格 | 右侧区域 | 大纲拖拽:PC端 绑定了列表数据的控件，不支持拖拽 到树表录入内部 | 大纲拖拽:PC端 绑定了列表数据的控件，不支持拖拽 到重复节内部 | 大纲拖拽:PC端 绑定了列表数据的控件，不支持拖拽 到重复表录入内部 | 左侧区域 | 已设置表达式 | 树表录入内部控件不能移动位置 | 重复节 | 重复表录入

### `src_pages_udc_application_new-app_index_tsx-node_modules_xiaozhua_biz-ic`

- 按钮：返回
- 组件：Checkbox.Group、Form.Item、Form.useForm、Menu.Item
- 弹窗/容器：Modal
- 拖拽：无
- 文案：去设计 | 平台版本 | 应用名称 | 应用所属人 | 应用描述 | 应用编码 | 所属机构 | 支持终端 | 最多输入255个字符 | 请输入应用描述 | 请选择所属机构 | 返回

### `src_pages_design_page-frame_actions_copy-page-frame_index_tsx-src_page`

- 按钮：复制外框、复制成功、新增外框、移动端、编辑外框
- 组件：Checkbox.Group、Form.Item、Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：你输入的名称过长 | 修改外框成功 | 只能包含中文、英文、数字以及下划线 | 复制外框 | 复制成功 | 外框名称 | 外框标识 | 新增外框 | 移动端 | 编辑外框 | 请输入外框名称 | 请输入外框标识 | 请选择适配终端 | 适配终端

### `node_modules_xiaozhua_biz-enums_dist_index-9365ba29_js.e2c68411`

- 按钮：停用、删除、删除成功、取消、启用、批量导出、排序号、新建、没有枚举可导出、确定、编辑
- 组件：—
- 弹窗/容器：Modal、Popconfirm
- 拖拽：无
- 文案：停用 | 删除 | 删除成功 | 取消 | 启用 | 图片枚举不允许导入 | 图片枚举不允许导出 | 批量导出 | 排序号 | 操作 | 新建 | 枚举名称 | 枚举项值 | 枚举项名称 | 没有枚举可导出 | 状态 | 确定 | 编辑 | 请输入枚举项名称 | 请选择要删除的枚举项 | 预置

### `src_pages_udc_app-log-config_index_tsx-src_pages_app-design_rule_dataf`

- 按钮：日志设置、设置失败、设置成功
- 组件：Form.Item、Form.useForm、Radio.Group
- 弹窗/容器：Tabs、Tree
- 拖拽：无
- 文案：业务应用 | 剩余时长 | 包括微流程、生单规则、扣减规则、页面规则日志 | 包括微流程、生单规则、页面规则日志 | 包括微流程、页面规则日志 | 名称、编码 | 审批应用 | 应用运行日志 | 微流程运行日志 | 扣减运行日志 | 日志设置 | 暂无数据，请选择左侧应用获取配置信息 | 生单运行日志 | 记录时长 | 记录运行日志 | 设置失败 | 设置成功 | 集成应用

### `src_pages_design_page-frame_sider_tsx.c4c52fcb`

- 按钮：删除、取消、复制、确定、移动端、编辑
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：删除 | 取消 | 只能包含中文、英文、数字以及下划线 | 名称不能为空 | 复制 | 确定 | 移动端 | 编辑 | 请输入外框名称 | 请输入正确的外框名称 | 重命名 | 重命名成功

### `src_pages_udc_sandbox_pages_application-test_index_tsx.ed62315f`

- 按钮：设置、设置成功
- 组件：Radio.Group
- 弹窗/容器：Modal
- 拖拽：无
- 文案：应用上架失败 | 应用名称 | 应用所属人 | 应用版本 | 应用编码 | 所属弹性容器 | 操作 | 最近活跃时间 | 构建时间 | 知道了 | 租户名称 | 设置 | 设置成功

### `src_components_design_asidetool_trans-wrapper_tsx-src_components_desig`

- 按钮：向上添加、新建方案、移除
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：分组 | 列数 | 向上添加 | 容器 | 数据 | 新建方案 | 方案名称 | 移除 | 网格 | 请输入 | 请输入列数 | 请输入方案名称 | 转为 | 页签

### `src_components_common_component-select_useComponentsTree_ts-src_compon`

- 按钮：已设置表达式、新建页面规则、新建页面规则失败
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：上侧 | 下侧 | 区域 | 单元格 | 右侧 | 外框 | 左侧 | 已设置表达式 | 所属分组 | 新建页面规则 | 新建页面规则失败 | 规则描述 | 请输入规则描述 | 请输入页面规则名称 | 页面 | 页面规则名称 | 页面规则名称不能为空 | 默认分组

### `src_pages_design_main_components_formAppPageInfoEdit_index_tsx.879ee13`

- 按钮：—
- 组件：Checkbox.Group、Form.Item、Form.useForm、Select.Option
- 弹窗/容器：—
- 拖拽：无
- 文案：请输入页面名称 | 请选择实体 | 请选择页面类型 | 适配终端 | 页面信息修改成功 | 页面名称 | 页面对应实体 | 页面标识 | 页面类型

### `src_pages_udc_page-frame-tmp-manage_index_tsx.95ba118a`

- 按钮：删除成功、取消、新建分类、模板预览、添加分类、确定、移动端、编辑模板
- 组件：Form.Item、Form.useForm、Menu.Item
- 弹窗/容器：Modal、Popconfirm、Tree
- 拖拽：无
- 文案：你输入的名称过长 | 分类名称 | 创建分类 | 删除成功 | 取消 | 只能包含中文、英文、数字以及下划线 | 名称不能超过10个字符 | 操作 | 新建分类 | 模板分类 | 模板名称 | 模板描述 | 模板描述不能为空 | 模板预览 | 添加分类 | 确定 | 移动端 | 终端 | 编辑模板 | 请上传模板预览图片 | 请输入分类名称 | 请输入模板名称 | 选择分类 | 重命名 | 页面类型

### `src_pages_app-design_template-manage_index_tsx.7ebad08d`

- 按钮：删除成功、排序号、编辑、请上传模板缩略图
- 组件：Form.Item
- 弹窗/容器：Modal
- 拖拽：无
- 文案：主子实体 | 修改成功 | 公开模板 | 公开模板成功 | 分类 | 创建人 | 创建时间 | 删除后应用中将不能再使用该模板 | 删除成功 | 单据 | 只能包含中文、英文、数字以及下划线 | 名称 | 名称不能超过255个字符 | 名称不能超过50个字符 | 外框 | 已存在重名的页面模版，请重新命名 | 平铺档案 | 所属应用 | 排序号 | 推荐标签 | 描述 | 操作 | 无实体 | 标准 | 树形档案 | 模板名称 | 状态 | 独立实体 | 类型 | 终端 | 编辑 | 表单 | 请上传模板缩略图 | 请输入模板名称 | 请输入模板名称搜索 | 请输入模板描述 | 请选择模板分类 | 页面

### `src_pages_app-design_entity-modeling_entity-field_components_rule-Form`

- 按钮：设置条件、设置汇总、设置筛选条件、请设置筛选条件
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：上级实体 | 汇总 | 聚合函数 | 要汇总的实体 | 设置条件 | 设置汇总 | 设置筛选条件 | 请设置筛选条件 | 请选择函数 | 请选择字段 | 请选择实体 | 选择字段

### `src_components_page-content_index_tsx-src_pages_design_constants_ts-sr`

- 按钮：移动端
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：公共页面规则 | 单据 | 平铺档案 | 标准 | 树形档案 | 移动端 | 表单

### `node_modules_xiaozhua_biz-enums_dist_index-7189faa2_js.4340c5f3`

- 按钮：停用、取消、启用、排序号、排序号为必填项、新建、确定、编辑、编辑成功、请上传图片、连续新建
- 组件：Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：停用 | 创建成功 | 取消 | 启用 | 排序号 | 排序号不能大于1000000 | 排序号为必填项 | 新建 | 枚举项值 | 枚举项值为必填项 | 枚举项名称 | 枚举项名称为必填项 | 父节点 | 状态 | 状态为必填项 | 确定 | 编辑 | 编辑成功 | 请上传图片 | 请输入 | 连续新建 | 首尾不能输入空格 | 默认语言的值下不能为空

### `src_pages_udc_sandbox_components_common-column_index_tsx-src_pages_udc`

- 按钮：取消、确定、设置、配置规则
- 组件：Form.Item、Form.useForm、Radio.Group
- 弹窗/容器：Modal
- 拖拽：无
- 文案：修改成功 | 创建应用总数 | 创建应用总数来源于商城购买，如余量不足请联系客户经理充值。 | 取消 | 定时重启 | 操作 | 最大物理沙箱数 | 最小可用物理沙箱数 | 测试运行总数 | 确定 | 禁止输入空格 | 设置 | 配置规则

### `src_pages_app-design_rule_dataflow_components_log-content_index_tsx.fa`

- 按钮：新建、新建或更新、新建目标实体数据
- 组件：Form.Item、Form.useForm
- 弹窗/容器：—
- 拖拽：无
- 文案：事件订阅 | 入参 | 全部 | 出参 | 动作描述 | 发起BPM流程 | 失败 | 将来源实体数据进行分组 | 序号 | 开始 | 异步消息通知 | 成功 | 手工触发 | 执行动作 | 执行回写规则 | 执行时间 | 执行状态 | 拍平来源实体聚合数据 | 拍平目标实体聚合数据 | 操作 | 操作类型 | 新建 | 新建或更新 | 新建目标实体数据 | 更新 | 更新目标实体数据 | 来源实体 | 来源实体数据 | 来源实体过滤条件 | 来源数据行条件匹配 | 查找来源实体聚合数据 | 查找目标实体聚合数据 | 状态 | 生单规则 | 目标实体 | 目标实体数据 | 组装目标实体数据 | 结束 | 触发方式 | 请输入生单规则名称

### `node_modules_xiaozhua_biz-serial-scheme_dist_index-aa2d4add_js.0de18369`

- 按钮：关闭、取消、查看当前号、查看空号、确定、编辑
- 组件：Form.Item、Form.useForm、Select.Option
- 弹窗/容器：Modal
- 拖拽：无
- 文案：关闭 | 取消 | 当前号 | 当前号只允许增大，不能减小 | 当前号只能输入正整数 | 更新成功 | 查看当前号 | 查看空号 | 流水依据 | 确定 | 空号 | 编辑 | 规则名称 | 规则编码 | 请输入正确的数字

### `node_modules_xiaozhua_biz-where_dist_modalWhere_js.aac960a8`

- 按钮：删除、取消分组、复制、添加、添加条件、添加条件组、确认
- 组件：Menu.Item
- 弹窗/容器：Modal
- 拖拽：无
- 文案：删除 | 取消分组 | 复制 | 条件 | 添加 | 添加条件 | 添加条件组 | 确认 | 继续分组 | 转为条件 | 转为条件组

### `src_pages_udc_sandbox-manage_index_tsx.12c8fe7e`

- 按钮：—
- 组件：—
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：停止 | 停止应用 | 停止运行 | 创建人 | 可在此查看测试发布的应用，并可操作应用的启停、数据清除。 | 启动 | 已停止 | 应用名称 | 应用版本 | 应用编码 | 操作 | 构造时间 | 清除并重启 | 清除数据 | 清除数据应用 | 请输入关键字搜索 | 运行中 | 重启

### `src_pages_app-design_rule_deductflow_log-content_index_tsx.49fb832a`

- 按钮：—
- 组件：Form.Item、Form.useForm
- 弹窗/容器：—
- 拖拽：无
- 文案：入参 | 全部 | 出参 | 判断扣减算法是否执行 | 动作描述 | 回滚（UNDO）扣减算法 | 失败 | 序号 | 开始 | 成功 | 扣减规则 | 执行动作 | 执行时间 | 执行状态 | 执行（DO）扣减算法 | 拍平来源实体聚合数据 | 操作 | 来源实体 | 查找扣减目标实体数据 | 检查扣减算法 | 状态 | 目标实体 | 结束 | 请输入扣减规则名称 | 错误信息

### `src_pages_app-design_entity-modeling_custom-extension_index_tsx.400f88`

- 按钮：删除、取消、启用、确定、自定义扩展配置、预览
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Drawer、Popconfirm
- 拖拽：无
- 文案：删除 | 取消 | 启用 | 字段名称前缀 | 操作 | 数据类型 | 数据类型已存在，请重新选择 | 状态 | 确定 | 自定义扩展配置 | 请输入 | 请输入字段名称前缀 | 请输入数据类型 | 请输入长度 | 请输入预留字段数量 | 请输入默认值 | 长度 | 预留字段数量 | 预览 | 默认值

### `node_modules_xiaozhua_biz-where_dist_where_js.b3912f02`

- 按钮：删除、取消分组、复制、添加、添加条件、添加条件组、确认
- 组件：Menu.Item
- 弹窗/容器：—
- 拖拽：无
- 文案：删除 | 取消分组 | 复制 | 条件 | 添加 | 添加条件 | 添加条件组 | 确认 | 继续分组 | 转为条件 | 转为条件组

### `src_pages_udc_sandbox_pages_app-environment_index_tsx.c5de5775`

- 按钮：删除、删除成功、新增、查看、编辑
- 组件：Form.Item、Form.useForm、Radio.Group、Select.Option
- 弹窗/容器：—
- 拖拽：无
- 文案：修改成功 | 删除 | 删除成功 | 实施 | 应用定制 | 开发 | 新增 | 无环境编码 | 查看 | 测试 | 测试环境 | 测试运行 | 环境名称 | 环境数量 | 环境标识 | 环境编码 | 生产 | 生产环境 | 生产运行 | 禁止输入空格 | 编辑 | 请输入环境名称

### `node_modules_xiaozhua_biz-serial-scheme_dist_index-a9cbbe00_js.c3e8b8dd`

- 按钮：关闭、删除、取消选择、启用、批量删除、批量启用、批量禁用
- 组件：Form.useForm、Select.Option
- 弹窗/容器：Modal、Popconfirm
- 拖拽：无
- 文案：关闭 | 删除 | 取消选择 | 启用 | 已选择 | 序号 | 成功 | 批量删除 | 批量启用 | 批量禁用 | 操作 | 状态 | 禁用 | 空号 | 空号管理

### `src_components_design_navbar_controls_cmps_tsx.e95e5a6f`

- 按钮：添加依赖组件
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：其他 | 添加依赖组件 | 请输入关键字

### `src_pages_app-design_page-rules_index_tsx-src_components_page-content_`

- 按钮：取消、新建公共页面规则、新建分组、欢迎来到规则设置、确定
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：公共页面规则 | 分组名称 | 取消 | 所属分组 | 描述信息 | 操作成功 | 新建公共页面规则 | 新建分组 | 最长100个字符 | 欢迎来到规则设置 | 确定 | 规则名称 | 规则名称长度最长45个字符 | 重命名分组 | 默认分组

### `node_modules_xiaozhua_biz-serial-scheme_dist_index-f62267af_js.f827461e`

- 按钮：绑定实体
- 组件：—
- 弹窗/容器：Modal、Tabs
- 拖拽：无
- 文案：上下文字段 | 公共流水号 | 常量 | 当前应用流水号 | 更新成功 | 流水号 | 绑定实体 | 规则名称 | 规则组成 | 规则编码 | 选择流水号

### `node_modules_xiaozhua_biz-serial-scheme_dist_index-63bbd6cd_js.14fc2408`

- 按钮：—
- 组件：Form.Item、Form.useForm
- 弹窗/容器：Modal
- 拖拽：无
- 文案：实体 | 实体名称 | 无条件 | 暂无数据 | 流水号类型字段 | 生成/释放条件配置 | 生成条件 | 被以下实体字段绑定 | 释放条件

### `src_pages_design_page-frame_index_tsx-src_utils_getTerminalFromApi_ts-`

- 按钮：—
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：公共页面规则 | 单据 | 平铺档案 | 标准 | 树形档案 | 欢迎来到外框设计器 | 表单

### `src_pages_design_functions_components_space-desiger_index_tsx.46d104ee`

- 按钮：—
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：公共页面规则 | 单据 | 平铺档案 | 标准 | 树形档案 | 欢迎来到菜单空间 | 表单 | 请传入正确地址

### `node_modules_xiaozhua_biz-enums_dist_index-dfa7dac0_js.4ccc658d`

- 按钮：上一步、上传文件、下一步、下载失败数据、下载模板、导入中，请稍后、导入完成、导入数据、成功导入
- 组件：—
- 弹窗/容器：Modal
- 拖拽：无
- 文案：上一步 | 上传文件 | 下一步 | 下载失败数据 | 下载模板 | 只能上传xls，xlsx文件 | 失败 | 完成 | 导入中，请稍后 | 导入完成 | 导入数据 | 成功导入 | 扩展名支持：xls，xlsx，大小支持：50M 以内 | 按标注提示修改后重新导入 | 条数据

### `src_pages_design_functions_components_backend-default_index_tsx.632094`

- 按钮：导入导出模板配置
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：公共页面规则 | 单据 | 单据分类 | 参数管理 | 导入导出模板配置 | 平铺档案 | 扣减规则 | 扩展方案 | 文档模板 | 枚举管理 | 标准 | 标签打印日志 | 标签模板管理 | 树形档案 | 档案分类 | 流水号规则 | 生单规则 | 表单 | 请在运行态应用管理后台使用该功能

### `node_modules_xiaozhua_biz-enums_dist_index-d16a4f98_js.a84d1636`

- 按钮：排序号、排序号为必填项、新建分类、编辑分类、编辑成功
- 组件：Form.useForm
- 弹窗/容器：—
- 拖拽：无
- 文案：分类名称不能为空 | 创建成功 | 名称 | 名称为必填项 | 排序号 | 排序号不能大于1000000 | 排序号为必填项 | 新建分类 | 编辑分类 | 编辑成功 | 请输入 | 首尾不能输入空格 | 默认语言的值下不能为空

### `src_pages_design_personal_schemes_index_tsx.5fd5e034`

- 按钮：取消、确定
- 组件：—
- 弹窗/容器：Modal、Popconfirm、Tree
- 拖拽：无
- 文案：取消 | 操作 | 方案名称 | 确定 | 请输入搜索关键字

### `src_pages_design_functions_components_outApp-page_index_tsx.bcd09f9e`

- 按钮：—
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：公共页面规则 | 单据 | 平铺档案 | 标准 | 树形档案 | 表单 | 请在原始应用中进行页面设计

### `src_pages_udc_app-log-data_config_index_tsx.3ea3e788`

- 按钮：设置失败、设置成功
- 组件：Form.Item、Form.useForm
- 弹窗/容器：—
- 拖拽：无
- 文案：记录数据日志 | 记录时长 | 设置失败 | 设置成功

### `src_pages_design_functions_components_page-info_index_tsx.bca6ec6a`

- 按钮：复制、复制成功
- 组件：—
- 弹窗/容器：—
- 拖拽：无
- 文案：其他 | 复制 | 复制成功

