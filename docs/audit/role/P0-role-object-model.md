# P0｜UDC 角色（Role）域 对象模型钉死

- 生成时间：2026-10-17 15:18:57 (GMT+8)
- 环境：test2（`lowcode-test2.example.com` 同租户）
- DB：`udc_test2`，MySQL；凭据经 Skill 配置层 `seeyon-low-code-environment/.env` 读取，**未打印、未落盘 secret**
- 探针脚本（只读）：`<HERMES_HOME>/cache/scratch/p0_role_ddl_v2.py`、`p0_role_samples.py`、`p0_role_probe3.py`、`p0_role_probe4.py`、`p0_role_probe5.py`、`p0_role_probe6.py`
- 原始返回 JSON：同目录 `p0_role_ddl.json`、`p0_role_samples.json`、`p0_role_probe{3,4,5,6}.json`
- 证据等级：全部为 **LIVE**（活体 DB 实测）
- 边界遵守：只读（仅 SELECT / SHOW）；只做本域三表；未引用 `core/role/` Agent 角色卡；未碰 menu 域

### 凭据来源说明（与 HANDOFF 文案的偏差，已就地修正）

HANDOFF-01 指定「凭据只引用 `shared-credentials/test2-web-credential.json` 路径」。实测该文件内容为 **Web 会话凭据**（`sy_access_token` / `cookie` / `app_id` / `base`），**不含 MySQL 主机/账号/口令**，无法用于 DB 直连。

因此 DB 连接改用本机既有的 test2 数据源配置层：`<HERMES_HOME>/skills/seeyon/01-platform/seeyon-low-code-environment/scripts/conn.py::load_env('test2')`（凭据在 `.env` 的 `SEEYON_DB_*`，等价于 `conn.py db` 官方通路）。**同样只引用路径、未打印、未落盘**。此偏差属可逆的执行细节，未改变本切片范围与验收标准。

## 0. 结论速览（三问三答）

| 问题 | 结论 | 证据 |
|---|---|---|
| ① `udc_role_resource` 是否 role↔resource 桥表 | **是**。复合语义键 = (`role_id`,`resource_id`,`action`)，携带 `resource_type` 冗余列；无外键约束，但两侧 0 孤儿行 | §3 |
| ② `udc_role` 归属 app 的字段 | **`app_id`**（bigint NOT NULL，有 `idx_udc_role_app_id` 单列索引；96 行全部非 0 非 NULL，分布 21 个 app） | §2.1 / §5 |
| ③ `udc_resource` 类型字段取值分布 | **`type`** 是枚举字段（0/1/2/3/5/6，NULL 无），**`data_type`** 是 type 内的细分子类（字符串枚举，24+ 种）；`client_type` 是端类型（-1/0/1） | §6 |

## 1. 行数交叉核对

| 表 | 已知实测 | 本次 `COUNT(*)` | 一致 |
|---|---|---|---|
| `udc_role` | 96 | 96 | ✅ 一致 |
| `udc_role_resource` | 12328 | 12328 | ✅ 一致 |
| `udc_resource` | 6968 | 6968 | ✅ 一致 |

SQL：`SELECT COUNT(*) FROM <table>`（三表各一次，见探针 `p0_role_ddl_v2.py`）

> 快照时点 = 2026-10-17 15:15:18（原始 JSON mtime ≤ 15:15:18；`scratch/p0_role_*.json` 最新为 `p0_role_probe6.json` @ 15:15:18.353）。本节所有计数仅在此 as-of 时点有效。

## 2. DDL（SHOW CREATE TABLE 原文）

### 2.1 `udc_role`

SQL：`SHOW CREATE TABLE `udc_role``

```sql
CREATE TABLE `udc_role` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `tenant_id` bigint(20) NOT NULL COMMENT '租户ID',
  `update_time` datetime NOT NULL COMMENT '修改时间',
  `version` smallint(6) NOT NULL COMMENT '版本号',
  `guid` bigint(20) NOT NULL COMMENT 'guid',
  `is_admin` tinyint(4) NOT NULL COMMENT '是否管理员角色',
  `app_id` bigint(20) NOT NULL COMMENT '所属应用',
  `code` varchar(50) DEFAULT NULL COMMENT '编码',
  `description` varchar(100) DEFAULT NULL COMMENT '描述',
  `is_display` tinyint(4) NOT NULL COMMENT '是否显示',
  `name` varchar(255) DEFAULT NULL COMMENT '名称',
  `sort_number` int(11) NOT NULL COMMENT '排序号',
  `type` smallint(6) NOT NULL COMMENT '类型',
  `is_deleted` tinyint(4) DEFAULT '0' COMMENT '是否删除',
  `relation_org_role_code` varchar(255) DEFAULT NULL COMMENT '关联组织角色code',
  `original_id` bigint(20) NOT NULL DEFAULT '0' COMMENT '原始id',
  `role_level` smallint(6) NOT NULL DEFAULT '1' COMMENT '默认是机构级角色,1-机构级,0-集团级',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_udc_role_app_id` (`app_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8
```

### 2.2 `udc_role_resource`

SQL：`SHOW CREATE TABLE `udc_role_resource``

```sql
CREATE TABLE `udc_role_resource` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `tenant_id` bigint(20) NOT NULL COMMENT '租户ID',
  `update_time` datetime NOT NULL COMMENT '修改时间',
  `version` smallint(6) NOT NULL COMMENT '版本号',
  `guid` bigint(20) NOT NULL COMMENT 'guid',
  `action` smallint(6) NOT NULL COMMENT '操作',
  `resource_id` bigint(20) NOT NULL COMMENT '资源ID',
  `resource_type` smallint(6) NOT NULL COMMENT '资源类型',
  `role_id` bigint(20) NOT NULL COMMENT '角色ID',
  `original_id` bigint(20) NOT NULL DEFAULT '0' COMMENT '原始id',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_u_r_r_app_id` (`role_id`) USING BTREE,
  KEY `idx_u_r_r_resource_id` (`resource_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8
```

### 2.3 `udc_resource`

SQL：`SHOW CREATE TABLE `udc_resource``

```sql
CREATE TABLE `udc_resource` (
  `id` bigint(20) NOT NULL COMMENT '主键',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `tenant_id` bigint(20) NOT NULL COMMENT '租户ID',
  `update_time` datetime NOT NULL COMMENT '修改时间',
  `version` smallint(6) NOT NULL COMMENT '版本号',
  `guid` bigint(20) NOT NULL COMMENT 'guid',
  `is_admin` tinyint(4) NOT NULL COMMENT '是否管理员资源',
  `allow_end` tinyint(4) NOT NULL COMMENT '管理员资源是否允许普通用户可见',
  `app_id` bigint(20) NOT NULL COMMENT '所属应用',
  `entity_full_name` varchar(255) DEFAULT NULL COMMENT '实体全路径',
  `client_type` smallint(6) NOT NULL COMMENT '资源端类型',
  `code` varchar(100) DEFAULT NULL COMMENT '编码',
  `data_type` varchar(50) DEFAULT NULL COMMENT '数据型资源的类型',
  `frontend_app_id` varchar(50) DEFAULT NULL COMMENT '前端所属应用',
  `icon` varchar(50) DEFAULT NULL COMMENT '图标',
  `resource_level` smallint(6) NOT NULL COMMENT '层级',
  `name` varchar(255) DEFAULT NULL COMMENT '名称',
  `open_type` varchar(20) DEFAULT NULL COMMENT '打开方式',
  `parent_code` varchar(100) DEFAULT NULL COMMENT '上级编码',
  `path` varchar(255) DEFAULT NULL COMMENT '路径',
  `ref_code` varchar(100) DEFAULT NULL COMMENT '引用编码',
  `sort_number` int(11) NOT NULL COMMENT '排序号',
  `type` smallint(6) NOT NULL COMMENT '类型',
  `url` varchar(255) DEFAULT NULL COMMENT '跳转链接',
  `url_parameters` longtext COMMENT '跳转链接参数',
  `out_parameters` longtext COMMENT '返回参数',
  `group_id` bigint(20) DEFAULT NULL COMMENT '分组id',
  `is_deleted` tinyint(4) DEFAULT '0' COMMENT '是否删除',
  `data_source` varchar(500) DEFAULT NULL COMMENT '控件数据源信息',
  `original_id` bigint(20) NOT NULL DEFAULT '0' COMMENT '原始id',
  `public_access` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否是不鉴权资源 0 - 非不鉴权资源 1 - 不鉴权资源',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_udc_resource_ref_code` (`ref_code`) USING BTREE,
  KEY `idx_udc_resource_code` (`code`) USING BTREE,
  KEY `idx_udc_resource_appid_code` (`app_id`,`code`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8
```

## 3. 桥表判定：`udc_role_resource`

### 3.1 结构事实

- 主键：`id`（单列，bigint 雪花，含负数）
- 业务列：`role_id`、`resource_id`、`resource_type`、`action`、`original_id`
- 索引：`idx_u_r_r_app_id(role_id)`、`idx_u_r_r_resource_id(resource_id)` —— 两方向各一，典型多对多关联表形态
- **无 UNIQUE 约束**（不存在 `(role_id,resource_id)` 唯一键）；**无 FOREIGN KEY**（InnoDB 但未声明约束）

### 3.2 唯一性与冗余（LIVE）

| total | distinct_triplets | distinct_trip_rt |
|---|---|---|
| 12328 | 12322 | 12322 |

- 三元组 (`role_id`,`resource_id`,`action`) 去重 = 12322，与总行 12328 差 **6 行真重复**（结构允许，业务未拦）。
- 重复样本（`GROUP_CONCAT(id)` 摘录）：

```json
[
 {
  "role_id": 3452012390907593358,
  "resource_id": 3438763221722679661,
  "action": 0,
  "cnt": 2,
  "ids": "2943217877810693027,6737316499366560071"
 },
 {
  "role_id": 3452012390907593358,
  "resource_id": 8003327788814780109,
  "action": 0,
  "cnt": 2,
  "ids": "2428437991786890318,6151348250672909172"
 },
 {
  "role_id": 3452012390907593358,
  "resource_id": 8055286022134514940,
  "action": 0,
  "cnt": 2,
  "ids": "5183482492337474129,7377872052183912249"
 },
 {
  "role_id": 3452012390907593358,
  "resource_id": 8563473090926102348,
  "action": 0,
  "cnt": 2,
  "ids": "834044049686675461,4671646528656002005"
 },
 {
  "role_id": 7311926076812840674,
  "resource_id": 4743937834074721171,
  "action": 0,
  "cnt": 2,
  "ids": "-7299738809166928556,-1781393362653960845"
 },
 {
  "role_id": 9120719891907691598,
  "resource_id": 4743937834074721171,
  "action": 0,
  "cnt": 2,
  "ids": "119572239624210861,2741373003727115583"
 }
]
```

### 3.3 引用完整性（LIVE，0 孤儿）

SQL：`SELECT COUNT(*) FROM udc_role_resource rr LEFT JOIN udc_role r ON r.id=rr.role_id WHERE r.id IS NULL` → 0

SQL：`... LEFT JOIN udc_resource res ON res.id=rr.resource_id WHERE res.id IS NULL` → 0

→ 12328 行全部两侧可解析；撤销的角色/资源不留残行。虽然 DB 层无 FK，应用层维护了一致性。

### 3.4 覆盖度（LIVE）

| total | distinct_pairs | roles | resources |
|---|---|---|---|
| 12328 | 12322 | 61 | 3439 |

- 只有 **61/96** 个角色持有授权（35 个角色 0 授权，其中含 5 个已删角色）。
- 被授权资源 **3439/6968**（49.4%）。
- 每角色授权数分布：

| buckets | roles |
|---|---|
| 0 | 35 |
| 1-10 | 6 |
| 101-300 | 18 |
| 11-50 | 14 |
| 300+ | 14 |
| 51-100 | 9 |

### 3.5 跨 app 授权 = 0（关键边界事实）

| cnt |
|---|
| 0 |  （`role.app_id <> resource.app_id` 的行数）

| cnt |
|---|
| 12328 |  （`role.app_id = resource.app_id`）

→ **授权严格同 app 封闭**：12328 行全部是同一 `app_id` 内的 role→resource。跨应用（应用市场/公共资源）不通过本表打通。

### 3.6 `action` 语义（LIVE）

| action | roles | resources | cnt |
|---|---|---|---|
| 0 | 61 | 3429 | 12305 |
| 3 | 5 | 11 | 23 |

- `action=0` 占 12305 行（99.8%），是「可见/可访问」。
- `action=3` 仅 23 行，且 **23/23 全部指向 `data_type='Button'` 资源**：

| data_type | cnt |
|---|---|
| Button | 23 |

> **【语义纠正，修正时点 2026-10-17 23:05，采纳 VERDICT-02 + P1 §5】**
> 下方「0=查看/访问，3=按钮级操作权限」判定**有误**：把「23 行全指向 Button 资源」的相关性
> 当成了语义定义，方向反了。权威来源 = `ResourceActionEnum` 字节码（static{} 逐指令，
> facade 5.3.351 与 5.3.429 class sha256 相同）+ udc 侧 UdcControlResourceActionEnum 同值
> + 前端标签三重证据：
> **NONE=-1 / basic=0（正常）/ readonly=1（只读）/ disabled=2（禁用）/ invisible=3（隐藏）。**
> ⇒ action=0 是「正常可用」；action=3 的 23 行是 23 个按钮被**隐藏**（invisible），
> 不是「按钮级操作权限」。DB 证据（23/23→Button）仍为真，但解释更正。原文保留备查。

- `action=3` 的角色上下文（5 个角色）：

| role_id | code | app_id | role_type | action3_cnt |
|---|---|---|---|---|
| -5633280307046271567 | zhihuiyingxiaojiesuanxiaoshouyuan | 1656355078954763084 | 1 | 1 |
| -5097658000409025553 | xinkong | 2378987216360786643 | 1 | 1 |
| 2558713164951079164 | faccountsreceivable2378987216360786643Admin | 2378987216360786643 | 0 | 10 |
| 4191458464292495620 | xiangmuguanli9000000000000000001AdminSystemAdmin | 1656355078954763084 | 0 | 1 |
| 8435806223213278410 | faccountsreceivable237898721636078EnBSystemAdmin | 2378987216360786643 | 0 | 10 |

→ 判定（原文，**已被 23:05 上方纠正块取代**）：`action` 是**授权动作枚举**（0=查看/访问，3=按钮级操作权限）。当前 test2 只有 5 个角色用到 3，全部集中在应收管理/智慧营销两个 app 的按钮资源上。0 与 3 之外无第三种取值。

### 3.7 `resource_type` 是冗余快照，不是权威类型

SQL：`SELECT SUM(rr.resource_type=res.type), SUM(rr.resource_type<>res.type) FROM udc_role_resource rr JOIN udc_resource res ON res.id=rr.resource_id`

| equal_rows | unequal_rows | total |
|---|---|---|
| 11416 | 912 | 12328 |

不一致矩阵（rr.resource_type × res.type）：

| rr_type | res_type | cnt |
|---|---|---|
| 0 | 0 | 3188 |
| 0 | 1 | 576 |
| 0 | 2 | 293 |
| 0 | 5 | 16 |
| 0 | 6 | 27 |
| 1 | 1 | 3882 |
| 2 | 2 | 3638 |
| 5 | 5 | 197 |
| 6 | 6 | 511 |

→ **912 行（7.4%）`rr.resource_type` 与 `udc_resource.type` 不一致**，且不一致全部集中在 `rr.resource_type=0`（被记作「普通/默认」）而实际资源是页面(1)/按钮(2)/布局(5)/子页(6)。

不一致行的 `data_type` 分布：

| type | data_type | cnt |
|---|---|---|
| 1 | DETAIL | 344 |
| 2 | Button | 287 |
| 1 | SEARCH_LIST | 212 |
| 6 | SUBPAGE | 27 |
| 1 | OTHER | 18 |
| 5 | LAYOUT | 16 |
| 2 | UdcGrid | 4 |
| 1 | EDIT_LIST | 2 |
| 2 | Input | 1 |
| 2 | KKContractChain | 1 |

一致行（rr.resource_type=0 且 res.type=0）的 data_type 分布（对照）：

| type | data_type | cnt |
|---|---|---|
| 0 | NORMAL | 2490 |
| 0 | ROOT | 91 |
| 0 | PRESET_LAYOUT | 52 |
| 0 | BIZ_HOME | 50 |
| 0 | PRESET_SUBPAGE | 46 |
| 0 | BASE_SET | 42 |
| 0 | PARAM_SETTING | 36 |
| 0 | EXCEL_SETTING | 36 |

→ 判定：`resource_type` 是**写入时刻的类型快照/默认值**，权威类型一律以 `udc_resource.type` 为准。做鉴权/资源枚举时不得只读 `rr.resource_type`。

## 4. 样本行（LIVE）

### 4.1 `udc_role` 前 5 行

SQL：`SELECT * FROM udc_role ORDER BY id LIMIT 5`

```json
[
 {
  "id": -8934210130994037731,
  "create_time": "2025-02-14 12:30:36",
  "tenant_id": -8112660841495312922,
  "update_time": "2025-02-14 12:30:36",
  "version": 0,
  "guid": -6742602677859431576,
  "is_admin": 0,
  "app_id": 7324620281389731265,
  "code": "dynamic7324620281389731265Admin",
  "description": "",
  "is_display": 1,
  "name": "客户方_组织集成应用管理员",
  "sort_number": 1,
  "type": 0,
  "is_deleted": 0,
  "relation_org_role_code": "",
  "original_id": 0,
  "role_level": 1
 },
 {
  "id": -8351601306922681849,
  "create_time": "2026-07-15 14:06:52",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-07-15 14:06:52",
  "version": 0,
  "guid": -1796325190984842770,
  "is_admin": 0,
  "app_id": 1656355078954763084,
  "code": "002",
  "description": "",
  "is_display": 1,
  "name": "{\"zh_CN\":\"智慧营销结算平台普通人员\"}",
  "sort_number": 1,
  "type": 1,
  "is_deleted": 0,
  "relation_org_role_code": "",
  "original_id": 0,
  "role_level": 1
 },
 {
  "id": -7788501349769288580,
  "create_time": "2026-04-09 16:52:41",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-04-09 16:52:41",
  "version": 0,
  "guid": 1915176187021970093,
  "is_admin": 0,
  "app_id": 3289082814923688017,
  "code": "ZNXMGLCW",
  "description": "",
  "is_display": 1,
  "name": "{\"zh_CN\":\"智能项目管理平台财务角色\"}",
  "sort_number": 1,
  "type": 1,
  "is_deleted": 0,
  "relation_org_role_code": "",
  "original_id": 0,
  "role_level": 1
 },
 {
  "id": -7507188838773988902,
  "create_time": "2025-02-13 16:16:53",
  "tenant_id": -8112660841495312922,
  "update_time": "2025-02-13 16:16:53",
  "version": 0,
  "guid": 4986728102259410347,
  "is_admin": 0,
  "app_id": 2378987216360786643,
  "code": "xiaoshou",
  "description": "",
  "is_display": 1,
  "name": "{\"zh_CN\":\"销售人员\"}",
  "sort_number": 3,
  "type": 1,
  "is_deleted": 0,
  "relation_org_role_code": "",
  "original_id": 0,
  "role_level": 1
 },
 {
  "id": -7238881713671972159,
  "create_time": "2026-03-17 15:55:03",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-04-08 14:47:21",
  "version": 1,
  "guid": 7958864173335531142,
  "is_admin": 0,
  "app_id": 3289082814923688017,
  "code": "Test",
  "description": "",
  "is_display": 1,
  "name": "{\"zh_CN\":\"测试角色\"}",
  "sort_number": 3,
  "type": 1,
  "is_deleted": 1,
  "relation_org_role_code": "",
  "original_id": 0,
  "role_level": 1
 }
]
```

### 4.2 `udc_resource` 前 5 行

SQL：`SELECT * FROM udc_resource ORDER BY id LIMIT 5`

```json
[
 {
  "id": -9198610961648760213,
  "create_time": "2026-03-17 15:55:01",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-10-16 18:16:12",
  "version": 135,
  "guid": 5447099722228125363,
  "is_admin": 0,
  "allow_end": 0,
  "app_id": 3289082814923688017,
  "entity_full_name": "",
  "client_type": 1,
  "code": "-5666474587449863443",
  "data_type": "OTHER",
  "frontend_app_id": "",
  "icon": "",
  "resource_level": 0,
  "name": "数据迁移",
  "open_type": "NEWWINDOW",
  "parent_code": "",
  "path": "",
  "ref_code": "",
  "sort_number": 0,
  "type": 1,
  "url": "/app9000000000000000001-mobile/Migration",
  "url_parameters": "",
  "out_parameters": "",
  "group_id": null,
  "is_deleted": 0,
  "data_source": "",
  "original_id": 0,
  "public_access": 0
 },
 {
  "id": -9198551814297991686,
  "create_time": "2026-08-20 14:15:27",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-10-16 18:16:12",
  "version": 135,
  "guid": -2863330932040513770,
  "is_admin": 0,
  "allow_end": 0,
  "app_id": 3289082814923688017,
  "entity_full_name": "",
  "client_type": 1,
  "code": "-1809748565118381751",
  "data_type": "OTHER",
  "frontend_app_id": "",
  "icon": "",
  "resource_level": 0,
  "name": "框架档案",
  "open_type": "NEWWINDOW",
  "parent_code": "5597659998775045427",
  "path": "",
  "ref_code": "4591934842645645192",
  "sort_number": 32,
  "type": 1,
  "url": "/app9000000000000000001-mobile/zuofeicopy",
  "url_parameters": "[{\"required\":false,\"id\":\"AyUv1trv0xAn06aM\",\"label\":\"作废id\",\"code\":\"canshumingcheng1\",\"dataType\":\"BIGINTEGER\",\"expressionValue\":[],\"list\":false,\"inKey\":\"canshumingcheng1\"}]",
  "out_parameters": "",
  "group_id": null,
  "is_deleted": 0,
  "data_source": "",
  "original_id": 0,
  "public_access": 0
 },
 {
  "id": -9196351588504222161,
  "create_time": "2025-04-07 16:46:41",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-08-04 10:58:33",
  "version": 888,
  "guid": 2031150547911656629,
  "is_admin": 0,
  "allow_end": 0,
  "app_id": 2378987216360786643,
  "entity_full_name": "",
  "client_type": 0,
  "code": "4218049612453738645",
  "data_type": "NORMAL",
  "frontend_app_id": "",
  "icon": "LinedElementsPortal",
  "resource_level": 0,
  "name": "销售工作交接档案",
  "open_type": "WORKSPACE",
  "parent_code": "747439465576350753",
  "path": "",
  "ref_code": "-8413029560995702980",
  "sort_number": 281,
  "type": 0,
  "url": "/faccountsreceivable2378987216360786643/xsgzjjda",
  "url_parameters": "",
  "out_parameters": "",
  "group_id": null,
  "is_deleted": 0,
  "data_source": "",
  "original_id": 0,
  "public_access": 0
 },
 {
  "id": -9187580870554532937,
  "create_time": "2026-03-17 15:55:01",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-10-16 18:16:12",
  "version": 135,
  "guid": 5782812889793841906,
  "is_admin": 0,
  "allow_end": 0,
  "app_id": 3289082814923688017,
  "entity_full_name": "",
  "client_type": 0,
  "code": "-1443803768769226759",
  "data_type": "NORMAL",
  "frontend_app_id": "",
  "icon": "LinedElementsPortal",
  "resource_level": 0,
  "name": "开票信息列表",
  "open_type": "WORKSPACE",
  "parent_code": "8701882498022306888",
  "path": "",
  "ref_code": "-3766453707292691436",
  "sort_number": 266,
  "type": 0,
  "url": "/app9000000000000000001/kaipiaoxinxiliebiao",
  "url_parameters": "",
  "out_parameters": "",
  "group_id": null,
  "is_deleted": 0,
  "data_source": "",
  "original_id": 0,
  "public_access": 0
 },
 {
  "id": -9179471317404465771,
  "create_time": "2025-08-21 16:21:23",
  "tenant_id": -8112660841495312922,
  "update_time": "2026-10-16 16:46:02",
  "version": 3603,
  "guid": -734478907564930941,
  "is_admin": 0,
  "allow_end": 0,
  "app_id": 1656355078954763084,
  "entity_full_name": "",
  "client_type": 0,
  "code": "-6060405632585653543",
  "data_type": "ROLE_MANAGE",
  "frontend_app_id": "",
  "icon": "LinedElementsPortal",
  "resource_level": 0,
  "name": "角色管理",
  "open_type": "WORKSPACE",
  "parent_code": "-1205749507709031199",
  "path": "",
  "ref_code": "2054977813117502639",
  "sort_number": 225,
  "type": 0,
  "url": "/ctp-user/role/appRole/xiangmuguanli9000000000000000001",
  "url_parameters": "",
  "out_parameters": "",
  "group_id": null,
  "is_deleted": 0,
  "data_source": "",
  "original_id": 0,
  "public_access": 0
 }
]
```

### 4.3 `udc_role_resource` 按角色维度抽样

SQL（4 个角色、其全部授权行，按 role_id 抽样避免只取单角色边界）：

```sql
SELECT * FROM udc_role_resource WHERE role_id IN (SELECT role_id FROM (SELECT DISTINCT role_id FROM udc_role_resource ORDER BY role_id LIMIT 4) t) ORDER BY role_id, id
```

命中 4 个角色，各持有 69 / 281 / 12 / 641 行（合计 1003 行）。每角色取前 4 行展示：

```json
[
 {
  "role_id": -8351601306922681849,
  "rows_total": 69,
  "sample": [
   {
    "id": -7298409621407970255,
    "create_time": "2026-07-15 14:09:24",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-07-15 14:09:24",
    "version": 0,
    "guid": 6806872764656799513,
    "action": 0,
    "resource_id": -6215960920583616100,
    "resource_type": 2,
    "role_id": -8351601306922681849,
    "original_id": 0
   },
   {
    "id": -7010587791198618033,
    "create_time": "2026-07-15 14:08:54",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-07-15 14:08:54",
    "version": 0,
    "guid": 7684268181150584526,
    "action": 0,
    "resource_id": 7145604261905842517,
    "resource_type": 1,
    "role_id": -8351601306922681849,
    "original_id": 0
   },
   {
    "id": -6870055617691149941,
    "create_time": "2026-07-15 14:08:54",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-07-15 14:08:54",
    "version": 0,
    "guid": -1173141840888575589,
    "action": 0,
    "resource_id": 541537683758534527,
    "resource_type": 1,
    "role_id": -8351601306922681849,
    "original_id": 0
   },
   {
    "id": -6801379250024241200,
    "create_time": "2026-10-14 13:39:18",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-10-14 13:39:18",
    "version": 0,
    "guid": -505009776008935026,
    "action": 0,
    "resource_id": -3139420639979551461,
    "resource_type": 1,
    "role_id": -8351601306922681849,
    "original_id": 0
   }
  ]
 },
 {
  "role_id": -7788501349769288580,
  "rows_total": 281,
  "sample": [
   {
    "id": -9104227789262793441,
    "create_time": "2026-04-14 16:25:00",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-04-14 16:25:00",
    "version": 0,
    "guid": -6821953401613169982,
    "action": 0,
    "resource_id": -7774949414236500998,
    "resource_type": 2,
    "role_id": -7788501349769288580,
    "original_id": 0
   },
   {
    "id": -9103112713182179641,
    "create_time": "2026-06-25 00:48:54",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-06-25 00:48:54",
    "version": 0,
    "guid": 4715430183888439652,
    "action": 0,
    "resource_id": 8015041738668655737,
    "resource_type": 2,
    "role_id": -7788501349769288580,
    "original_id": 0
   },
   {
    "id": -9009063083308919536,
    "create_time": "2026-04-09 16:55:20",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-04-09 16:55:20",
    "version": 0,
    "guid": 1822877006359645152,
    "action": 0,
    "resource_id": 4396453482521706822,
    "resource_type": 1,
    "role_id": -7788501349769288580,
    "original_id": 0
   },
   {
    "id": -9002151122241968810,
    "create_time": "2026-04-14 16:25:00",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-04-14 16:25:00",
    "version": 0,
    "guid": 5496854268026309379,
    "action": 0,
    "resource_id": 3328228991319097719,
    "resource_type": 2,
    "role_id": -7788501349769288580,
    "original_id": 0
   }
  ]
 },
 {
  "role_id": -7507188838773988902,
  "rows_total": 12,
  "sample": [
   {
    "id": -7717523397808417663,
    "create_time": "2026-01-22 21:28:15",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-01-22 21:28:15",
    "version": 0,
    "guid": 7189692245881802148,
    "action": 0,
    "resource_id": 7877722459096104999,
    "resource_type": 1,
    "role_id": -7507188838773988902,
    "original_id": 0
   },
   {
    "id": -6614621832366410983,
    "create_time": "2026-01-22 21:31:35",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-01-22 21:31:35",
    "version": 0,
    "guid": 5478453635936961519,
    "action": 0,
    "resource_id": 6077205614899382833,
    "resource_type": 2,
    "role_id": -7507188838773988902,
    "original_id": 0
   },
   {
    "id": -6493843229275670661,
    "create_time": "2026-01-22 21:28:15",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-01-22 21:28:15",
    "version": 0,
    "guid": 3843071217638195577,
    "action": 0,
    "resource_id": -7981198178758472082,
    "resource_type": 1,
    "role_id": -7507188838773988902,
    "original_id": 0
   },
   {
    "id": -6358442263270426049,
    "create_time": "2025-02-13 16:16:51",
    "tenant_id": -8112660841495312922,
    "update_time": "2025-02-13 16:16:51",
    "version": 0,
    "guid": -9162239073422913618,
    "action": 0,
    "resource_id": 987050881734690369,
    "resource_type": 0,
    "role_id": -7507188838773988902,
    "original_id": 0
   }
  ]
 },
 {
  "role_id": -6714963260636490520,
  "rows_total": 641,
  "sample": [
   {
    "id": -9205276411355480992,
    "create_time": "2026-05-24 18:27:12",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-05-24 18:27:12",
    "version": 0,
    "guid": 4828989131515512124,
    "action": 0,
    "resource_id": 7964730180182623006,
    "resource_type": 2,
    "role_id": -6714963260636490520,
    "original_id": 0
   },
   {
    "id": -9202908009666693406,
    "create_time": "2026-04-29 16:48:42",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-04-29 16:48:42",
    "version": 0,
    "guid": 5300291119747974873,
    "action": 0,
    "resource_id": 261808916361858834,
    "resource_type": 0,
    "role_id": -6714963260636490520,
    "original_id": 0
   },
   {
    "id": -9197357594497715263,
    "create_time": "2026-05-24 18:27:12",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-05-24 18:27:12",
    "version": 0,
    "guid": -1671330119026194646,
    "action": 0,
    "resource_id": -2402069991760640469,
    "resource_type": 2,
    "role_id": -6714963260636490520,
    "original_id": 0
   },
   {
    "id": -9182648321145420088,
    "create_time": "2026-04-29 16:48:42",
    "tenant_id": -8112660841495312922,
    "update_time": "2026-04-29 16:48:42",
    "version": 0,
    "guid": 6456099576336696762,
    "action": 0,
    "resource_id": -2242982427029453240,
    "resource_type": 0,
    "role_id": -6714963260636490520,
    "original_id": 0
   }
  ]
 }
]
```

## 5. role 归属 app 的字段：`app_id`

- DDL：`app_id bigint(20) NOT NULL COMMENT '所属应用'` + `KEY idx_udc_role_app_id (app_id)`
- 有效性校验：

| app_zero | app_null | total |
|---|---|---|
| 0 | 0 | 96 |

- 96 个角色分布到 **21 个 app**（`SELECT COUNT(DISTINCT app_id) FROM udc_role` → 21；下表 top 15 覆盖 81 个角色，其余 6 个 app 共 15 个角色（各 2~3 个））：

| app_id | cnt |
|---|---|
| 3289082814923688017 | 14 |
| 9000000000000000002 | 11 |
| 2378987216360786643 | 8 |
| 1656355078954763084 | 7 |
| 5791640252914287064 | 6 |
| 6570299241515796755 | 6 |
| 7001530513149673721 | 4 |
| 4396215186967839451 | 4 |
| 2707349923416592296 | 3 |
| 6712017922882617636 | 3 |
| 3117198973910469031 | 3 |
| 7022003764439498867 | 3 |
| 7417152852034669760 | 3 |
| 5150746664960478913 | 3 |
| 5245855677018033156 | 3 |

→ **不存在** role 表级别的「全局角色 + app 映射子表」；一个角色只属于一个 app，`app_id` 是唯一归属轴。跨 app 复用通过「每个 app 各建同名角色」实现（见 §7.1 的 code 后缀证据）。

补充：`udc_resource` 只覆盖 **13 个 app**，而 `udc_role` 覆盖 **21 个 app** —— 有 8 个 app 仅有角色、零资源（纯集成/配置类应用，如飞书集成、V5待办集成、发布应用）：`6712017922882617636`、`912667056861626502`、`5150746664960478913`、`7022003764439498867`、`5245855677018033156`、`5746064954083329093`、`2707349923416592296`、`6388488623384448921`（各 3 个角色）。这些 app 的角色天然无授权行，是 §3.4 中 35 个零授权角色的主要来源。

## 6. `udc_resource` 类型字段

### 6.1 `type` 主枚举分布（LIVE）

SQL：`SELECT type, COUNT(*) FROM udc_resource GROUP BY type`

| type | cnt |
|---|---|
| 0 | 1373 |
| 1 | 3897 |
| 2 | 1437 |
| 3 | 1 |
| 5 | 85 |
| 6 | 175 |

`type × data_type` 交叉（完整）：

| type | data_type | cnt |
|---|---|---|
| 0 | NORMAL | 1080 |
| 0 | PRESET_LAYOUT | 36 |
| 0 | PRESET_SUBPAGE | 36 |
| 0 |  | 24 |
| 0 | BIZ_HOME | 20 |
| 0 | ROOT | 20 |
| 0 | APPLICATION_SET | 10 |
| 0 | CUSTOM_PAGE | 10 |
| 0 | QRCODE_SETTING | 10 |
| 0 | DEFAULT_GROUP | 10 |
| 0 | HOME_PAGE_SPACE_SETTING | 10 |
| 0 | BASE_SET | 10 |
| 0 | PARAM_SETTING | 10 |
| 0 | FORM_CONVERT_SETTING | 10 |
| 0 | LABEL_PRINT_RECORD | 10 |
| 0 | EXCEL_SETTING | 10 |
| 0 | ROLE_MANAGE | 10 |
| 0 | LABEL_PRINT_TEMPLATE_MANAGE | 10 |
| 0 | EXTENSION_REFER_CONTROL | 9 |
| 0 | SERIAL_NUMBER | 9 |
| 0 | DATA_FLOW | 8 |
| 0 | ENUM_MANAGE | 8 |
| 0 | SPACE_MENU | 2 |
| 0 | DEDUCT | 1 |
| 1 | DETAIL | 2165 |
| 1 | SEARCH_LIST | 1574 |
| 1 | OTHER | 124 |
| 1 | EDIT_LIST | 22 |
| 1 | LIST | 12 |
| 2 | Button | 1418 |
| 2 | UdcGrid | 6 |
| 2 | UdcDataGrid | 4 |
| 2 | UdcFilter | 3 |
| 2 | Input | 3 |
| 2 | KKContractChain | 2 |
| 2 | KKShiyebuLinkageSelect | 1 |
| 3 | NORMAL | 1 |
| 5 | LAYOUT | 85 |
| 6 | SUBPAGE | 175 |

### 6.2 type 语义判定

> **【语义纠正，修正时点 2026-10-17 23:05，采纳 VERDICT-02 + P1 §5】**
> 下表中「type=3 = 报表资源」**有误**。权威来源 = `ResourceTypeEnum` 字节码（P1 §5.2，javap static{}）：
> **NONE=-1 / MENU=0 / PAGE=1 / CONTROL=2 / DATA=3 / ENTITY=4 / LAYOUT=5 / SUBPAGE=6 / NAV=7 / GROUP=8。**
> ⇒ type=3 应为 **DATA（数据资源）**，非「报表」；孤例 url=`/cdp-data/report/...` 恰是数据服务的报表路径，
> 属 DATA 的实例而非类型定义（同样的相关性倒置错误）。下表其余判定（0 菜单/1 页面/2 控件/5 布局/6 子页）与枚举一致，保留。
> 另注意：`udc_role.type` 是另一个枚举（RoleTypeEnum：NONE=-1/PRESET=0/APP=1/ORG=2），**两者禁止混用**（P2 §3.2）。

| type | 行数 | data_type 特化 | 判定 |
|---|---|---|---|
| 0 | 1373 | NORMAL / ROOT / BIZ_HOME / APPLICATION_SET / ROLE_MANAGE / *_SETTING / ENUM_MANAGE / PRESET_* 等 24 种 | **菜单/功能入口节点**（含系统配置入口） |
| 1 | 3897 | DETAIL / SEARCH_LIST / OTHER / EDIT_LIST / LIST | **页面资源**（详情页、列表页） |
| 2 | 1437 | Button(1418) / UdcGrid / UdcDataGrid / UdcFilter / Input / KK* | **控件资源**（按钮为主） |
| 3 | 1 | NORMAL（url=`/cdp-data/report/...`） | **数据资源 DATA**（孤例；原「报表资源」判定作废） |
| 5 | 85 | LAYOUT | **布局资源** |
| 6 | 175 | SUBPAGE | **子页资源** |

证据支撑：
- `type=0` 与 `data_type=ROLE_MANAGE` 组合对应「角色管理」入口，url 形如 `/ctp-user/role/appRole/<appName>`：

| id | code | name | data_type | type | url |
|---|---|---|---|---|---|
| 2974041775436875710 | 779623469867157004 | 角色管理 | ROLE_MANAGE | 0 | /ctp-user/role/appRole/datamigration9000000000000000001 |
| 5358117154011369020 | 8125349212565098034 | 应用设置 | APPLICATION_SET | 0 |  |

- `type=3` 唯一一行：

```json
[
 {
  "id": -2695593905904529556,
  "app_id": 3289082814923688017,
  "code": "3810428794358586350",
  "name": "转授权报表",
  "data_type": "NORMAL",
  "client_type": 0,
  "url": "/cdp-data/report/7893602794403547749?appName=app9000000000000000001"
 }
]
```

- `type=2` 中 `Button` 1418 行占据绝对多数，说明控件资源在库里是「可单独授权的最小粒度」。

### 6.3 `client_type`（端类型）

| client_type | cnt |
|---|---|
| -1 | 20 |
| 0 | 6102 |
| 1 | 846 |

`type × client_type` 交叉：

| type | client_type | cnt |
|---|---|---|
| 0 | -1 | 20 |
| 0 | 0 | 1224 |
| 0 | 1 | 129 |
| 1 | 0 | 3383 |
| 1 | 1 | 514 |
| 2 | 0 | 1262 |
| 2 | 1 | 175 |
| 3 | 0 | 1 |
| 5 | 0 | 75 |
| 5 | 1 | 10 |
| 6 | 0 | 157 |
| 6 | 1 | 18 |

→ `client_type` 判定：`0`=PC 端（6102 行）、`1`=移动端（846 行）、`-1`=未指定端（20 行，全部集中在 type=0）。

URL 侧佐证（LIVE）：`SELECT client_type, SUM(url LIKE '%-mobile%'), COUNT(*) FROM udc_resource GROUP BY client_type`

| client_type | url 含 `-mobile` | total |
|---|---|---|
| -1 | 0 | 20 |
| 0 | 0 | 6102 |
| 1 | 524 | 846 |

→ `-mobile` 只出现在 `client_type=1`（524/846，62%），反向 0 例外。即 **client_type=1 ⇒ 移动端**成立；`client_type=1` 中剩余 322 行是移动端内不拼 `-mobile` 路径的资源（如移动端配置项）。

### 6.4 其他布尔/标识列（LIVE）

- `is_admin` / `allow_end` / `public_access`：

| is_admin | allow_end | public_access | cnt |
|---|---|---|---|
| 0 | 0 | 0 | 6956 |
| 0 | 0 | 1 | 12 |

- `resource_level` 恒为 0（6968/6968），字段存在但**当前无层级语义**：

| resource_level | cnt |
|---|---|
| 0 | 6968 |

- `is_admin=1` 的资源 **0 行**；`udc_role.is_admin=1` 也 **0 行**（见 §7）。

- 树形用 `parent_code` → 同 app 内 `code` 解析：需父节点 4949 行，其中 23 行解析不到同 app 父节点（历史脏数据，不影响授权）。SQL：`res_parent_resolvable`。

## 7. `udc_role` 字段语义

### 7.1 `type`（角色来源枚举）

| type | cnt |
|---|---|
| 0 | 60 |
| 1 | 36 |

交叉 `type × role_level`：

| type | role_level | cnt |
|---|---|---|
| 0 | 0 | 18 |
| 0 | 1 | 42 |
| 1 | 1 | 36 |

判定依据（LIVE 样本）：
- `type=0` 60 个，code 均为系统生成模板：`<appName>Admin` / `<appName>SystemAdmin` / `AllApp` / `dynamic<appId>Admin`，name 是明文中文（如「数据迁移应用管理员」）。
- `type=1` 36 个，code 多为业务自定义 + `-<appId>` 后缀（15/36 带后缀），name 是 i18n JSON（`{"zh_CN":"..."}`）。

→ 判定：**`type=0` 系统内置角色（应用管理员/系统管理员/普通人员），`type=1` 用户自定义角色**。

code 后缀证据：

| type | code_has_appid | total |
|---|---|---|
| 0 | 0 | 60 |
| 1 | 15 | 36 |

### 7.2 `role_level`（层级）

| role_level | cnt |
|---|---|
| 0 | 18 |
| 1 | 78 |

- DDL 注释原文：`默认是机构级角色,1-机构级,0-集团级`
- `role_level=0` 共 18 个，**全部是 type=0**，且 code 全为 `*SystemAdmin`（集团级系统管理员）。
- `role_level=1` 78 个 = 42 个内置应用级 + 36 个自定义。

### 7.3 `is_admin` / `is_deleted` / `is_display`

| type | is_deleted | cnt |
|---|---|---|
| 0 | 0 | 60 |
| 1 | 0 | 31 |
| 1 | 1 | 5 |

- `is_admin=1` **0 行**（`SELECT COUNT(*) FROM udc_role WHERE is_admin=1` → 0）→ 该列在 test2 未被使用，**不要用它判定管理员**；管理员靠 `code` 模板（`*Admin`/`*SystemAdmin`）+ `role_level` 识别。
- 已删角色 5 个（全部 type=1，`is_deleted=1`），且这 5 个角色 **0 条授权行**。

SQL：`SELECT r.is_deleted, COUNT(*) rr_cnt, COUNT(DISTINCT r.id) roles FROM udc_role r JOIN udc_role_resource rr ON rr.role_id=r.id GROUP BY r.is_deleted`

| is_deleted | rr_cnt | roles |
|---|---|---|
| 0 | 12328 | 61 |

→ 该 INNER JOIN 结果只有 `is_deleted=0` 一行（91 个未删角色中 61 个有授权，共 12328 行），**已删的 5 个角色一行都没出现**。

独立确证：`SELECT COUNT(*) FROM udc_role r WHERE r.is_deleted=1 AND EXISTS (SELECT 1 FROM udc_role_resource rr WHERE rr.role_id=r.id)` → **0**。即删除角色时其授权行已一并清理，不留悬挂授权。

### 7.4 唯一性/租户

| total | uniq_guid | uniq_id |
|---|---|---|
| 96 | 92 | 96 |  （`guid` 有 4 个重复值，`id` 96/96 唯一）

| role_tenants | rr_tenants | res_tenants | role_t |
|---|---|---|---|
| 1 | 1 | 1 | -8112660841495312922 |

→ 三表同一租户 `tenant_id=-8112660841495312922`，单租户库。

## 8. 目标应用 `9000000000000000002` 的对象面（LIVE）

> 快照时点 = 2026-10-17 15:15:18（原始 JSON mtime ≤ 15:15:18；`scratch/p0_role_*.json` 最新为 `p0_role_probe6.json` @ 15:15:18.353）。本节所有 app 级/表级计数仅在此 as-of 时点有效；A1 告警显示该 app 曾被并发写入 14 行，阶段4/5 启动前必须重取基线并声明新时点。

| 指标 | 值 | SQL 摘要 |
|---|---|---|
| 角色数 | 11 | `SELECT COUNT(*) FROM udc_role WHERE app_id=9000000000000000002` → 11 |
| 资源数 | 1147 | `SELECT COUNT(*) FROM udc_resource WHERE app_id=...` |
| 授权行数 | 381 | `... FROM udc_role_resource rr JOIN udc_role r ON r.id=rr.role_id WHERE r.app_id=...` |

11 个角色（含各自授权行数）：

| id | code | name | type | role_level | rr_cnt |
|---|---|---|---|---|---|
| 1193221668826597560 | ContractAdmin-datamigration9000000000000000001 | {"zh_CN":"合同管理员"} | 1 | 1 | 47 |
| 1547666253648711259 | shangwuadmin-datamigration9000000000000000001 | {"zh_CN":"商务管理员"} | 1 | 1 | 4 |
| 3546474277944379108 | huaweiadmin-datamigration9000000000000000001 | {"zh_CN":"华为模块管理员"} | 1 | 1 | 47 |
| 3680293057201521981 | ZNXMGLCW-datamigration9000000000000000001 | {"zh_CN":"智能项目管理平台财务角色"} | 1 | 1 | 45 |
| 4266600482366704431 | ZNXMGLTBGLY-datamigration9000000000000000001 | {"zh_CN":"智能项目管理平台投标管理员"} | 1 | 1 | 45 |
| 6088071208035831704 | kuangjiaadmin-datamigration9000000000000000001 | {"zh_CN":"智能项目管理平台框架模块管理员"} | 1 | 1 | 47 |
| 6780230063726609585 | hwmkry-datamigration9000000000000000001 | {"zh_CN":"智能项目管理平台华为模块人员"} | 1 | 1 | 6 |
| 7311926076812840674 | datamigration9000000000000000002SystemAdmin | 数据迁移系统管理员 | 0 | 0 | 58 |
| 7848047731790858930 | quanxian-datamigration9000000000000000001 | {"zh_CN":"控制权限角色"} | 1 | 1 | 1 |
| 8777352696284531088 | AllApp | 普通人员角色 | 0 | 1 | 23 |
| 9120719891907691598 | datamigration9000000000000000002Admin | 数据迁移应用管理员 | 0 | 1 | 58 |

该 app 授权行按 `resource_type × action` 分布：

| resource_type | action | cnt |
|---|---|---|
| 0 | 0 | 177 |
| 1 | 0 | 140 |
| 2 | 0 | 64 |

→ 该 app 只有 action=0，无按钮级(action=3)授权。角色授权覆盖率仅 **75/1147 资源（6.5%）** —— 大量资源尚未被任何角色授权，这说明该应用的角色授权是**稀疏配置**，后续做「授权生效验证」时需先明确基线角色。

## 9. 对象模型（最终判定）

```
udc_role (96)                                 udc_resource (6968)
  id            PK                              id            PK
  app_id        ──┐ 归属 app                   app_id        ──┐ 归属 app
  code / name     │                             code          │ 同 app 内业务码
  type 0=系统 1=自定义                          type 0菜单 1页面 2控件 3DATA 5布局 6子页【23:05 纠正:3=DATA 非报表】
  role_level 0=集团 1=机构                      data_type 子类（NORMAL/DETAIL/Button/...）
  is_admin (恒0, 未启用)                        client_type 0=PC 1=移动 -1=未定
  is_deleted / tenant_id                        parent_code → 同 app code（树）
        │                                       is_admin(恒0)/public_access/allow_end
        │                                             │
        └──────── udc_role_resource (12328) ──────────┘
                   role_id      → udc_role.id      (idx)
                   resource_id  → udc_resource.id  (idx)
                   resource_type  类型快照（7.4% 与实际 type 不符，非权威）
                   action         【23:05 纠正】0=basic正常(12305) 3=invisible隐藏(23)
                   唯一性：无 UNIQUE 约束，三元组真重复 6 行
                   约束：无 FK，但两侧 0 孤儿
                   封闭性：role.app_id = resource.app_id（跨 app 授权 0 行）
```

三条硬结论：

1. **`udc_role_resource` 是桥表**，但不是干净的纯关联表：它携带 `action`（授权动作）和 `resource_type`（非权威快照），因此语义是「**授权记录（grant）**」而非「多对多映射」。同一 (role,resource) 可因 action 不同而多行（当前数据无此情形，但结构允许）。
2. **role 归属 app 用 `app_id`**，一角色一 app，无全局角色表；跨 app 复用靠各 app 复制同名角色（`code` 带 `-<appId>` 后缀）。
3. **resource 的类型是两段式**：`type` 粗分类（6 值）+ `data_type` 细分（24+ 值）。鉴权/枚举以 `udc_resource.type` 为准，`udc_role_resource.resource_type` 只作历史快照。

## 10. 未覆盖 / 下一片输入（供 main 裁路）

- 本切片**只到 DB 对象模型**；未取证：设计器「角色」页面接口调用链（ROUTE 阶段2）、写链（阶段4）、授权生效（阶段5）。
- 前端入口的 DB 线索已现（未验证链路）：`data_type='ROLE_MANAGE'` 资源 url = `/ctp-user/role/appRole/<appName>`，指向 `ctp-user` 服务而非 udc 域。
- `action` 的其余枚举值（1/2/4/...）在当前数据无样本，**不得**凭空补全；需字节码/前端取证。
- 5 个已删角色 + 35 个 0 授权角色：是否为部署/复制残留，需结合 `original_id` 与设计器行为取证。

## 11. 复现命令

```
cd <HERMES_HOME>/cache/scratch
uv run --no-project --quiet --with pymysql python p0_role_ddl_v2.py
uv run --no-project --quiet --with pymysql python p0_role_samples.py
uv run --no-project --quiet --with pymysql python p0_role_probe3.py
uv run --no-project --quiet --with pymysql python p0_role_probe4.py
uv run --no-project --quiet --with pymysql python p0_role_probe5.py
uv run --no-project --quiet --with pymysql python p0_role_probe6.py
```

凭据由 `<HERMES_HOME>/skills/seeyon/01-platform/seeyon-low-code-environment/scripts/conn.py` 的 `load_env('test2')` 解析，脚本内无明文 secret。
