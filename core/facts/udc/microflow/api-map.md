# 微流程节点 → 接口 → 数据 映射（抓取记录）

抓取时间：2026-10-25。方式：页面内 fetch/XHR 拦截器（`install_fetch_recorder`）+ `performance.getEntriesByType('resource')` 提取 GraphQL operation 名。

## 一、接口命名规律（核心）

- 全部是 GraphQL，POST 到 `/service/udc/graphql`，query string 里带 operation 名。
- 命名 = `udcMicroflow` + 动词 + 对象 + Post/Get（读用 Get，写用 Post）。
- 多个 operation 用 `&` 合并批量（如 `?udcMicroflowSearchAppsPost&udcMicroflowSearchTreeEntityPost&udcMicroflowFindCustomDtoPost`）。
- 图标/通用接口：`appCommonIconNameListPost`（图标名列表）。

## 二、已确认映射（节点操作 → 接口 → 返回数据）

| 操作 | 接口 | 返回数据 |
|---|---|---|
| 选择应用（下拉） | `udcMicroflowSearchAppsPost` | 应用列表（数据迁移/基础设置/BPM引擎/…） |
| 选择实体（树形下拉 ant-tree-select） | `udcMicroflowSearchTreeEntityPost` | 实体树（含分组，如 日志方案信息/迁移日志） |
| 选择自定义对象/DTO | `udcMicroflowFindCustomDtoPost` | 自定义对象列表（入参/出参 DTO/分页对象） |
| 选择子微流程 | `udcMicroflowServiceListSubMfPost` | 子微流程列表（按分组） |
| 读微流程详情（打开编辑器） | `udcMicroflowFindByIdGet` | 微流程 dataSchema/节点 |
| 保存前检查 | `udcMicroflowCheckSchemaUpdatePost` | check/errors（校验结果） |
| 分组选择 | `udcMicroFlowGroupSelectByTypePost` | 分组（默认分组/数据迁移…） |
| 禁用节点 | `udcMicroflowDisableNodePost` | — |
| 编辑锁 | `udcMultiEditLockPost` | 编辑锁状态 |
| 表达式 schema | `udcExpressionSchemaPost` | 表达式可选范围（系统变量/函数） |
| 表达式·日期变量 | `GET /service/app-common/expression/system/values/date` | 日期系统变量值 |
| 依赖应用选择 | `udcApplicationDependentApplicationSelectByConditionPost` | 依赖应用列表 |
| 应用搜索检测 | `udcApplicationSearchDetectionPost` | 检测结果 |
| 图标名列表 | `appCommonIconNameListPost` | 节点图标名 |

## 三、链路机制（已确认）

- **点击节点中心**（不是标题）用 `Input.dispatchMouseEvent` 三连（mouseMoved/pressed/released）打开配置抽屉 `.ant-drawer`。
- 打开节点面板时，自动触发「选择应用」接口 `udcMicroflowSearchAppsPost` + 图标 `appCommonIconNameListPost`。
- 「选择实体」是 `ant-tree-select`（树形），「选择应用」是 `ant-select`。
- 每个下拉点开时触发对应的 list/search 接口；**接口只在首次加载触发，之后前端缓存，重复点开不重发**。

## 四、抓取瓶颈（重要）

- 前端对已加载数据有缓存：事后重放点击，接口**不重复触发**，抓不到完整清单。
- 要抓全 24 类节点的接口，最可靠是**首次操作时同步抓**，或从前端 bundle 源码 grep 全部 `udcMicroflow*Post` 定义。
- 已通过 performance 抓到 26 个已触发 operation（见 `scratch/node_api_map.jsonl` + 本节表）。

## 五、复用方法（抓其它页面接口同法）

1. `CdpClient.install_fetch_recorder()` 装页面 fetch/XHR 拦截器。
2. 操作页面（点下拉/选实体）。
3. `read_captured()` 读最近 50 条请求（url/reqBody/respBody 截断）。
4. 补：`performance.getEntriesByType('resource')` 过滤 `graphql?` 提取 operation 名（可拿历史已触发清单）。

## 六、24 类节点 → 接口 完整推导表

接口名可推导：`udcMicroflow + 动词 + 对象 + Post/Get`。已确认 11 个（★运行时抓到），其余按规律推导（标注 待确认）。

选择类动词：SearchApps(应用)/SearchTreeEntity(实体树)/FindCustomDto(自定义对象)/ServiceListSubMf(子微流程)。

| 节点 | 面板「选择」操作 | 对应接口 | 状态 |
|---|---|---|---|
| 查询单条/多条 | 选择应用 / 选择实体 | SearchAppsPost / SearchTreeEntityPost | ★ |
| 插入/更新/批量插入/批量更新 | 选择应用+实体 / 选择列表(引用变量) | SearchAppsPost+SearchTreeEntityPost / 无(引用) | ★/— |
| 删除(指定/过滤/ID集合) | 选择节点(引用) / 选择实体 / ID集合 | — / SearchTreeEntityPost / — | ★/— |
| 创建变量/创建列表 | 实体对象 / 自定义对象 / 选项集 / 事件对象 | SearchTreeEntityPost / FindCustomDtoPost / ?选项集 / ?事件对象 | ★/待 |
| 修改变量/修改列表 | 选择变量/列表(引用) | — | — |
| 列表操作 | 选择列表(引用) + 计算字段 | — | — |
| 创建映射组 | 键值对(无选择) | — | — |
| 映射操作 | 选择映射(引用) | — | — |
| 分支/循环 | 表达式 | udcExpressionSchemaPost / 表达式日期变量 | ★ |
| 自定义错误 | 原始/错误数据(引用) | — | — |
| 自定义服务 | 选择应用+服务+方法 | ?服务列表 | 待 |
| 事件投递 | 选择应用+事件对象 | ?事件对象列表 | 待 |
| 子微流程 | 选择微流程服务 | udcMicroflowServiceListSubMfPost | ★ |
| 数据转换 | 来源数据+目标实体+映射关系 | SearchTreeEntityPost | ★ |
| 类型转换 | 选择类型 | ? | 待 |
| 执行生单规则 | 选择规则 | ?规则列表 | 待 |

**结论**：绝大多数节点「选择」操作落在 4 个已确认接口上（应用/实体/自定义对象/子微流程），引用类操作（选变量/列表/节点）不触发接口。真正待确认的只有 5 个：选项集、事件对象、服务列表、元数据、生单规则列表——这些可在首次操作时同步抓，或从微流程编辑器懒加载 chunk 里 grep。
