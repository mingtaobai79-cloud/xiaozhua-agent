# UDC 平台 REST 操作面全集（反编译 udc-web 5.3.517）

**证据源**：`<MAVEN_REPO>/com/seeyon/udc-web/5.3.517/udc-web-5.3.517.jar`
反编译 `com.seeyon.udc.controller.*` 共 **54 个 Controller / 299 个 REST 端点**。
每个端点带 `@RestApiOperation(value="<中文操作名>")`，是**页面交互 → 后端处理的权威映射表**。

**链路**：前端设计器按钮 → `POST/GET /service/udc/<Base>/<Path>`（ingress `/service/(.*)` → `ctp-webapi-gateway` → `udc-web` → `udc-biz`）。
权限：多数 Controller 标 `@HasRole({"udcAppDesigner","udcSystemAdmin"})`。

> 微流程 Controller（`udc/microflow`，编号 1.1~1.x）已单独详列于 MICROFLOW-*.md；
> 本文件是**其余全部域**的操作面。

## 端点全集（按 Controller）


### udc/collaboration  (3)
  POST   /create                                添加协作成员
  POST   /handover                              移交应用
  POST   /members                               获取当前机构的应用设计师或流程设计师

### udc/application  (19)
  POST   delete-rename                          【删除】根据ID删除应用信息（有人在删除应用，暂时改名，排查问题）
  POST   schema/form/download/by-app-ids        批量下载指定表单应用
  POST   copy                                   复制应用
  POST   transfer/batch/                        批量迁移表单应用
  POST   schema/download/templates              下载当前系统中所有的应用模板
  POST   save-as-newDesign                      另存新设计态文件(表单应用)
  POST   /save/normal/newDesign                 另存新设计态文件(普通应用)
  POST   create-from-template                   从模板创建
  POST   search/detection                       根据应用ID查询检测结果列表
  POST   summary/detection                      根据应用ID查询检测汇总结果
  POST   do/detection                           执行应用一致性检测
  POST   do/detection-state                     应用一致性检测运行状态
  POST   search/front-detection                 根据应用ID查询只发前端检查结果
  POST   do/front-detection                     执行应用前端发布检测
  GET    search/detection/all-form-app          查询全量应用一致性检查结果
  POST   push-data                              跨环境推送应用信息
  POST   design-data-change                     获取设计态数据变化情况
  GET    /role-resource                         【查询】当前用户按钮权限
  GET    /user-role                             【查询】当前用户的角色编码

### udc/attachment-template  (4)
  POST   /create                                创建附件模板记录
  POST   /create-batch                          批量创建创建附件模板记录
  POST   /select-by-guids                       根据guid获取附件模板记录(批量查询)
  POST   /delete-by-guids                       根据guids批量删除附件模板记录

### udc/attribute-group  (5)
  POST   create                                 1.1:创建分组
  POST   update                                 1.2:修改分组
  POST   cancel                                 1.3:取消分组
  POST   remove                                 1.4:移除分组
  POST   swap                                   1.5:交换顺序（前端传入全量数据）

### udc/attributeSet  (8)
  POST   delete                                 删除字段集
  POST   batch-delete                           批量删除字段集
  POST   update                                 修改字段集
  POST   search-list                            根据条件获取字段集列表(不分页)
  POST   select-by-appid                        根据应用id获取应用下所有字段集列表
  POST   select-by-name/attributes              根据字段集/特性名称获取对应字段(如果是特性,则appId不传)
  POST   search/term                            根据关键字模糊查询，获取所有满足条件的字段集列表
  POST   select-attribute-list                  查找字段集的字段列表

### udc/backend-component  (6)
  POST   /search                                根据条件分页查询后端组件信息
  POST   /search/app                            根据条件分页查询某个应用可添加的后端组件信息
  POST   /import                                导入
  GET    /refresh-version                       刷新版本
  POST   /update                                修改信息
  GET    refresh                                刷新

### udc/app-split  (4)
  POST   /coli/split/result                     4:查找拆分结果
  POST   /coli/app/delete                       5:删除中海拆分后的应用
  POST   /coli/entity/map                       x:查找新旧实体编码映射
  POST   /coli/record/delete                    x:删除拆分记录(慎用!!!会导致拆分后的应用无法批量删除)

### udc/data-flow  (3)
  POST   entity-not-exist-ids                   1.12 判断指定实体是否存在
  POST   mapping                                2.01 新建映射规则
  POST   mapping/update                         2.02 更新映射规则

### udc/data-transfer-object  (0)

### udc/data-type  (4)
  GET    data-types                             获取数据类型列表
  GET    data-types/base                        获取基础数据类型列表
  GET    data-types/param                       获取参数数据类型列表
  POST   select-by-params                       根据条件查询数据类型列表

### udc/deduction  (1)
  POST   entity-not-exist-ids                   返回不存在的实体id

### udc/dependency/analysis  (0)

### udc/runtime  (0)

### udc/deployment  (0)

### udc/entity  (32)
  POST   update                                 2.1:修改实体信息
  POST   batch-update-entity-group-id-and-orderno 2.2:批量更新实体的分组号和排序号,仅仅是为了升级老数据和可能存在的性能问题使用
  POST   update-extension-linkage               2.3:修改扩展字段联动
  POST   search                                 4.2:根据条件获取实体列表(分页)
  POST   search-list                            4.3:根据条件获取实体列表(不分页)
  POST   search/term                            4.4:根据关键字模糊查询，获取所有满足条件的实体列表
  POST   children/search                        4.6:根据条件获取实体子实体列表
  POST   entity-copy                            6.1 实体复制
  POST   attribute-transfer                     6.2 字段转移
  POST   attribute                              创建属性
  POST   attribute-batch                        创建属性(批量)
  POST   attribute/update                       修改属性信息
  POST   attribute/batch-update                 修改属性信息(批量)
  POST   attribute/delete                       删除属性
  POST   attribute/batch-delete                 批量删除属性
  POST   attribute/search-list                  根据条件获取实体属性列表(不分页)
  POST   attribute/search/term                  根据模糊查询获取属性列表(不分页)
  POST   attribute/select-parent-enum-attrs     查询枚举的上级枚举字段列表
  POST   attribute-group/search                 实体定义，属性列表查询，返回属性的精简信息
  POST   attribute-group/bath-update            实体定义，字段排序（全量保存）
  POST   attribute-group/create-update          创建分组
  POST   attribute-group/cance-group            取消分组
  POST   preset/create-default-excel-template   预置数据-根据实体ID创建默认模板
  POST   preset/create                          预置数据-创建实体预置数据
  POST   preset/update                          预置数据-修改实体预置数据信息
  POST   constraint/entity                      查询实体可以选择的约束实体（平铺返回，只返回根实体与子实体，孙实体暂不支持）
  POST   association/serial                     查询实体可以选择的流水号
  POST   association/group/serial               查询实体可以选择的流水号(包含依赖应用)
  POST   sql/deploy-record/total                5.1 获取应用下全量sql -- 从发布记录中获取上一次成功发布的schema 生成sql
  POST   sql/deploy-record/replace              5.2 获取应用下全量sql -- 从发布记录中获取上一次成功发布的schema 生成sql 并上传到文件服务中 返回新的sqlStorageKey
  GET    sql/not-null-repair                    5.6 not null字段升级为允许null字段的补充接口
  GET    ext/remove-linkage                     5.7 取消所有实体的扩展联动属性

### udc/entity-group  (3)
  POST   create                                 1.1:新建分组
  POST   update                                 1.2:修改分组
  POST   update-batch                           1.3:批量修改分组

### udc/entity-open-api  (1)
  GET    /select                                1.1:获取openApi展示

### udc/event  (3)
  POST   delete                                 3.1 根据id删除事件
  POST   delete-batch                           3.2 根据id删除事件(批量)
  POST   search/term                            4.4 根据模糊查询获取事件列表(不分页)

### udc/feature  (2)
  GET    list                                   获取特性清单
  GET    sys-attributes                         获取系统属性清单

### udc/function  (4)
  POST   batch-delete                           批量删除功能/引用
  POST   find/tree-and-group                    获取菜单树和移动分组列表
  POST   update/root/to-user-center             更新菜单数据到用户中心
  POST   update/root/handle-function            处理菜单数据

### udc/index  (0)

### udc/meta-data  (26)
  POST   search-available-app                   1.3:【应用】查询可以被关联依赖的应用
  POST   search-available-app-multi-version     1.3.1:【应用】查询被关联依赖的应用多版本信息
  POST   select-app-by-id                       1.5:【应用】获取应⽤信息，可查询关联应用
  POST   select-entity                          2.1:【实体】通过实体 id/fullName 查询实体元数据信息(查询当前实体)
  POST   select-aggregation-entity              2.2:【聚合根实体】通过实体 id/fullName 查找聚合根实体（包含子实体，一层关联实体），
  POST   select-aggregation-entity-without-association 2.4:【聚合根实体】通过实体 id/fullName 获取聚合根实体元信息（不包含关联实体）
  POST   select-simple-entity                   2.6:【聚合根实体】通过应用名称，获取应⽤下聚合根实体名称清单
  POST   select-refer-by-entity                 3.1:【参照】通过实体 id/fullName 查询参照信息
  POST   merge-refer                            3.3:【参照】通过实体 id/fullName，参照id-进行参照方案合并返回
  POST   merge-refer-by-map                     3.3.2:【参照】通过实体 id/fullName，参照id-进行参照方案合并返回
  POST   refer-and-app                          3.2:【参照】通过实体 id/fullName 查询参照信息(包含应用信息)
  POST   select-ctp-enum-by-app                 4.1:【数据库枚举】通过应用Id查询应用下可使用的枚举元数据
  POST   select-ctp-enum-by-app1                4.2【数据库枚举】通过应用Id，查询应用下可使用的枚举元数据
  POST   select-ctp-enum-item                   4.2:【数据库枚举】查询枚举项
  POST   select-java-enum-by-app                4.3【Java枚举】通过应用Id/appName，查询JAVA枚举信息
  POST   select-java-enum-item                  4.4【Java枚举】通过枚举Id/FullName，查询枚举下可使用的JAVA枚举项元数据
  POST   select-page                            【页面】根据id或者fullName查询页面元数据
  POST   select-page-info-list                  【页面】根据条件查询应用下面的页面信息（不包含页面schema）
  POST   select-all-page-by-app                 【页面】根据应用Id查询应用下页面元数据(包括关联应用的页面信息，不包含页面schema)
  POST   select-function-node-with-page-tree    【页面】根据应用Id查询应用下页面元数据(包括关联应用的菜单及页面信息，不包含页面schema)
  POST   select-page-list                       【页面】通过查询对象查询页面schema接口（废弃，使用运行态元数据接口）
  POST   select-all-layout-by-app               【外框】查询应用下外框元数据(包括宿主应用的外框)
  POST   select-page-layout-info                【外框】查询页面外框元数据(不包含schema)
  POST   select-page-layout                     【外框】查询外框元数据信息(包含Schema)
  POST   select-page-layout-list                【外框】批量查询外框元数据信息(包含Schema)
  POST   select-by-file-name                    根据文件名查询元数据(临时)

### udc/microflow  (56)
  POST   search                                 1.2根据条件获取分页微流程列表
  POST   search-no-page                         1.3根据条件获取微流程列表
  POST   checkSchema                            1.4校验微流程Schema
  POST   checkSchema/update                     1.5校验并更新微流程
  POST   create                                 1.6新建微流程（强制草稿态）
  POST   update                                 1.7更新微流程（强制草稿态）
  POST   update/order-no-and-group              1.8更新微流程排序号和分组
  POST   batch-move                             1.9批量移动微流程
  POST   search/term                            1.10根据微流程标题查询
  POST   disable-last-version-metadata          1.12停用上一版本元数据
  POST   search/entityRule                      2.0根据实体id查询实体业务规则
  POST   delete-by-source-id                    2.1根据sourceId删除微流程
  POST   delete                                 2.2根据id删除微流程
  POST   delete-by-ids                          2.21根据ids删除微流程
  GET    listOperationType                      2.4获取列表操作分组下拉数据
  POST   service/list                           2.5分页获取后台已发布服务定义微流程
  POST   service/list/sub-mf                    2.5.1分页获取后台已发布服务定义微流程(后端子微流程)
  POST   service/details/dynamic                2.6.1获取服务定义微流程详情(个性化应用)
  POST   check/micro-flow/caption               2.7检查微流程显示名称是否已存在
  POST   check/micro-flow/name                  2.8检查微流程名称是否已存在
  POST   /copy                                  3.01复制微流程
  POST   /copyBySourceId                        3.02根据sourceId复制微流程
  POST   copy/page-rule-bound-control           3.03复制控件绑定的页面规则
  POST   /search/nonEntityDto                   3.04根据应用appName查询自定义DTO列表
  POST   /find/customDto                        3.05根据元数据DtoFullName查询封装DTO元数据
  POST   /search/treeEntity                     3.06根据应用appName查询实体DTO树
  POST   /search/appService                     3.07根据DtoFullname和应用name查询appService
  POST   /search/appService-by-appName          3.08根据appName查找下面的AppService列表
  POST   /search/appService-by-name             3.09根据serviceName查询AppService信息
  POST   /search/method-by-name                 3.10根据methodName查询method详情
  POST   /find/dto-by-entity                    3.11根据实体fullName对应的dto
  POST   /batch-find/agg-dto                    3.12根据聚合DTO的fullName批量查询聚合DTO信息
  POST   /search/rest-exclude-boot              4.0查询指定服务Rest信息(排除组件)
  POST   /filter/event                          4.1过滤实体事件消息
  POST   /filter/mq                             4.2过滤系统MQ信息
  POST   /search/enum-by-appName                4.3根据appName查询枚举
  POST   /find/enum-by-name                     4.4根据enumName查询枚举详情
  POST   /search/apps                           4.5应用列表查询(包含扩展)
  POST   /disable-node                          4.6不可用节点
  POST   /tree-entity-dto                       4.7查询当前应用的实体DTO树
  POST   /search/send-mq-list                   4.8可消息投递的mq列表
  POST   /search/event-list                     4.9获取微流程事件列表
  POST   create-message                         4.10创建消息对象
  POST   update-message                         5.0修改消息对象
  POST   message-dto/delete                     5.3根据id删除消息对象
  POST   /search/message-dto                    5.4根据应用appName查询消息对象列表
  POST   check/dto-metadata/exist               5.6检查对象元数据是否存在
  POST   service/frontend/list                  5.6获取前端页面规则子流程下拉列表
  POST   /batch-find/java-enum                  5.7根据聚合DTO的fullName批量查询Java枚举信息
  POST   /find/full-agg-dto                     5.8根据DTO的fullName查询全量聚合DTO信息
  POST   /find/data-system                      5.9获取某个DTO对象的数据体系
  POST   /filter/not-virtual                    5.10过滤非虚拟DTO
  POST   find/call-info/upstream                6.1获取某一微流程的上游调用信息
  POST   find/call-info/downstream              6.2获取某一微流程的下游调用信息
  POST   find/node-schema                       6.3根据条件获取节点 Schema 信息
  POST   select-by-condition-for-deploy         6.4根据条件查询微流程全量（仅前端生成代码使用,大字段只查询dataSchema）

### udc/micro-flow-functional-check  (6)
  POST   check-call-times                       1.1 检测页面规则节点调用次数
  POST   find-event-bound-page-rule             1.2 获取指定页面事件类型绑定的页面规则信息
  POST   find-lt-specified-num-nodes-page-rule  1.3 获取节点数量小于指定数量的页面规则信息
  POST   find-page-rule-include-specified-node-type 1.4 获取含有指定节点的页面规则
  POST   calculate-nodes-number-percentage      2.2 计算节点数量百分比
  POST   calculate-micro-flow-usage-percentage  2.3 计算应用使用微流程的百分比

### udc/micro-flow-group  (6)
  POST   create                                 新建微流程分组
  POST   update                                 更新微流程分组
  POST   batch-move                             批量移动微流程分组
  POST   delete                                 根据ID删除分组
  POST   delete-batch                           批量删除微流程分组与微流程
  POST   select-by-type                         获取应用下所有分组信息

### udc/micro-flow-macro  (0)

### udc/microflow-refactor  (2)
  POST   resolve-nodes-reference-relationships  1. 解析节点引用关系
  POST   refactored                             2. 重构

### udc/micro-flow-upgrade  (1)
  GET    batch/thirdEntity                      第三方实体方法全应用升级

### udc/multi-edit  (5)
  POST   lock                                   获取操作锁
  POST   renewal                                续期操作锁
  POST   unlock                                 取消操作锁
  POST   force-unlock                           强制取消操作锁
  POST   current-lock                           查询操作锁

### udc/operation-log  (1)
  POST   delete-all                             手动删除日志

### udc/page-info  (2)
  POST   /select-list/by-conditions             根据条件查询页面列表（包括详细信息）
  POST   /select-list-with-draft-schema/by-conditions 根据条件查询页面列表（包括详细信息）

### udc/page-layout  (3)
  POST   /search-no-page-available              根据条件查询页面外框列表（可用外框）
  POST   /select-list/by-conditions             根据条件查询页面外框列表（包括详细信息）
  POST   /select-list-with-draft-schema/by-conditions 根据条件查询页面外框列表（包括详细信息）

### udc/page-route  (0)

### udc/page-template-class  (3)
  POST   /delete                                根据id删除页面模板分类
  POST   /search                                搜索页面模板分类
  GET    /select-tree                           获取页面模板分类树

### udc/page-template  (4)
  POST   delete-by-id                           根据id删除
  POST   delete-by-ids                          根据id删除
  POST   /publish                               公开模版
  POST   /check-name                            验证名称是否重复

### udc/page-template/published  (3)
  POST   delete-by-id                           根据id删除
  POST   delete-by-ids                          根据id删除
  POST   /check-name                            验证名称是否重复

### udc/portlet  (0)

### udc/portlet-group  (0)

### udc/publish-state  (1)
  POST   update                                 更新发布状态

### udc/refer-config  (8)
  POST   create                                 新建参照配置
  POST   create-or-update                       新建或更新自定义参照配置
  POST   create-config-info                     创建参照（带多个终端参照数据）
  POST   convert-to-mobile                      自定义参照pc转移动
  POST   update-config-info                     更新参照（带多个终端参照数据）
  POST   update                                 更新参照配置
  POST   delete                                 根据id删除某一参照配置
  POST   search                                 根据条件获取参照配置分页列表(分页)

### udc/sandbox  (0)

### udc/scalability  (3)
  POST   update                                 修改扩展方案明细信息
  POST   delete                                 删除扩展方案明细信息
  POST   batch-delete                           批量删除扩展方案明细信息

### udc/scalability-option  (3)
  POST   update                                 修改自定义扩展方案信息
  POST   delete                                 删除自定义扩展方案信息
  POST   select-all-optionName                  获取所有扩展方案信息

### udc/stereotype  (1)
  GET    list                                   获取版型清单

### udc/preset/microflow  (0)

### udc/udc-enum-item  (5)
  POST   /select-one-by-id-and-app              获取枚举项详情
  POST   search-by-enum-code                    根据枚举code和appId查询枚举项
  POST   search-by-enum-codes                   根据枚举codes和appId查询枚举项
  POST   search-cascade-tree-by-enum-code       根据枚举code和appId查询枚举树
  POST   search-item-by-relation-app            查询依赖应用的所有枚举项

### udc/design-metadata  (47)
  GET    service                                Service.2.按服务名查询微服务
  GET    rest                                   Rest.1.查询指定服务Rest信息
  POST   rest-by-names                          Rest.2.批量查询Rest信息
  POST   rest-by-name                           Rest.3.查询Rest信息
  GET    rest-exclude-boot                      Rest.4.查询指定服务Rest信息(排除组件)
  GET    open-api                               OpenApi.1.查询指定服务OpenApi信息
  POST   open-api-by-names                      OpenApi.2.批量查詢OpenApi信息
  POST   open-api-by-name                       OpenApi.3.查询OpenApi信息
  GET    dto                                    DTO.1.查询指定服务DTO信息
  POST   dto-by-names                           DTO.2.批量查詢DTO信息
  POST   dto-by-name                            DTO.3.查询DTO信息
  GET    entity-relation-dto                    DTO.4.查询实体关联的DTO信息
  POST   dto-by-entitys                         DTO.5.按实体FullName批量查询关联的DTO信息
  POST   dto-by-entity                          DTO.6.按实体FullName查询关联的DTO信息
  GET    dto-exclude-boot                       DTO.7.查询指定服务DTO信息(排除组件)
  GET    entity-relation-dto-exclude-boot       DTO.8.查询实体关联的DTO信息(排除组件)
  GET    enum                                   JavaEnum.1.查询指定服务Enum信息
  POST   enum-by-names                          JavaEnum.2.批量查询Enum信息
  POST   enum-by-name                           JavaEnum.3.查询Enum信息
  GET    entity                                 Entity.1.查询指定服务Entity信息
  POST   entity-by-names                        Entity.2.批量查询Entity信息
  POST   entity-by-name                         Entity.3.查询Entity信息
  GET    entity-exclude-boot                    Entity.4.查询指定服务Entity信息(排除组件)
  GET    app-service                            AppService.1.查询指定服务AppService元数据信息
  POST   app-service-by-names                   AppService.2.批量查询AppService信息
  POST   app-service-by-name                    AppService.3.查询AppService信息
  POST   app-service-dto                        AppService.4.按DTO的FullName查询AppService信息
  GET    app-service-exclude-boot               AppService.5.查询指定服务AppService元数据信息(排除组件)
  GET    mq                                     MQ.1.查询指定服务MQ元数据信息
  POST   mq-by-names                            MQ.2.批量查询MQ信息
  POST   mq-by-name                             MQ.3.查询MQ信息
  GET    mq-exclude-boot                        MQ.4.查询指定服务MQ元数据信息(排除组件)
  GET    agg                                    Agg.1.查询指定服务聚合根列表
  POST   agg-by-names                           Agg.2.批量查询聚合根列表
  POST   agg-by-name                            Agg.3.按实体FullName查询聚合根信息
  GET    agg-entity                             Agg.4.查询指定服务聚合根(包含实体元数据)
  POST   agg-entity-by-name                     Agg.5.按实体FullName查询聚合根(包含实体元数据)
  POST   agg-entity-by-names                    Agg.6.按实体FullName批量查询聚合根(包含实体元数据)
  POST   entity-by-agg                          Agg.7.查询聚合根下实体元数据列表
  GET    agg-exclude-boot                       Agg.8.查询指定服务聚合根列表(排除组件)
  GET    agg-entity-exclude-boot                Agg.9.查询指定服务聚合根(包含实体元数据)(排除组件)
  POST   refer                                  Refer.1.按实体FullName查询参照信息
  POST   refer-and-app                          Refer.2.按实体FullName查询参照及微服务信息
  GET    basic-entity                           Basic-Entity.1.查询指定服务Entity信息
  POST   basic-entity-by-names                  Basic-Entity.2.批量查询Entity信息
  POST   basic-entity-by-name                   Basic-Entity.3.查询Entity信息
  POST   page                                   Page.1.查询指定服务Page信息

### udc/udc-enum-category  (2)
  POST   delete                                 根据id删除枚举分类
  POST   batch-delete                           根据id列表批量删除枚举分类

### udc/udc-enum  (3)
  POST   delete                                 根据id删除枚举
  POST   batch-delete                           根据id列表批量删除枚举
  POST   search/term                            根据模糊查询获取枚举列表(不分页)

### udc/udc-enum-item  (5)
  POST   delete                                 根据id删除枚举项
  POST   batch-delete                           批量删除枚举项
  POST   search/term                            根据模糊查询获取枚举项列表(不分页)
  POST   export                                 excel导出(支持条件查询)
  POST   import                                 excel导入

### udc/runtime/file  (0)

### udc/manager  (1)
  POST   component/log                          组件同步日志

### udc/sandbox/logs  (0)

## 关键归属
- `udc/entity`（32）实体设计态；`udc/application`（19）应用生命周期/检测/模板；`udc/meta-data` 元数据。
- `udc/attributeSet` / `udc/attribute-group` / DTO / data-transfer-object 属性。
- `udc/event` 事件；`udc/backend-component` 后端组件；`udc/deployment` / `udc/runtime` 发布运行。
- 0 端点的 Controller（如 data-transfer-object/deployment/runtime）说明其端点在**继承的父类**或
  经 GraphQL AppService（见 PLATFORM-GRAPHQL-OPERATIONS.md）暴露，需进一步反编译父类。
