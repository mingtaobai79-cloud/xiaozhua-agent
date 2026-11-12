# S7 写链实验 LIVE 结果（数据迁移应用）

> ⚠️ **已被部分取代**：v1 只覆盖 W1–W4（实体/字段/菜单/页面）。微流程与枚举链见
> `S7-WRITE-CHAIN-LIVE-v2.md`（W5/W5b/W6/W6b）。本文件保留作历史记录。

> 日期：2026-10-14 | 应用：`8704025620829192834`（datamigration…）
> 隔离：全部实验对象用 `xzh` 前缀（小爪），不碰已有业务对象 | 证据：**LIVE**

## 已打通的写链（全部回读验证）

| # | 链路 | 接口/形态 | 结果 |
|---|---|---|---|
| W1 | 建实体 | REST `POST /udc/entity`（EntityDto：appId/name/caption/stereotype=standard/type）| ✅ id=474806313816300867（7→8）|
| W2 | 加字段 | REST `POST /udc/entity/attribute`（name/caption/dataType=STRING/dataTypeCategory=PRIMITIVE/type=INPUT）| ✅ id=8016904624316689195（12 字段=9 预置+1 新）|
| W4 | 建菜单 | **GraphQL** `udcFunctionPost`（batch 形态 `?op` + query+variables；type=MENU/parentId=0）| ✅ id=7853445889453184321 |
| W3 | 建页面 | REST `POST /udc/page-info/base-info/create`（**PageDefinitionDto**：curTerminalType + pageItems[].urlType/menuId + masterEntityIds）| ✅ id=1520098474917276520（21→22）|

## 关键机制实证

### 1. 双通道确认（第三例）
- 实体/字段走 **REST**；菜单走 **GraphQL**（udcFunctionPost 只在 schema 里，无 REST）
- 页面 REST 路径是 `/udc/page-info/base-info/create`（**带 page-info 前缀**）
  —— `_api_full.json` 里 `/udc/base-info/create` 是 PageInfoController 类级路径拼接缺前缀（已证 404）
  —— **该缺陷已于 2026-10-14 修复**：`tools/core/decompile/merge_udc_web_api.py` 原把方法级 value 以 "/" 开头当绝对路径，
     已改为**恒拼接** class_mapping（657 方法中 159 个 full_path 被纠正），并加 8 项回归护栏。

### 2. PageDefinitionDto（javap 权威）
```
POST /udc/page-info/base-info/create 必需：
  appId/caption/pageType/pageUrl + masterEntityIds(复数带s)
  + curTerminalType: "PC"
  + pageItems: [{urlType:"PC", pageUrl, actionType:"INSERT", menuId, menuName, orderNo}]
  （"页面必需绑定归属资源" = pageItems[].menuId 必须先建菜单）
```

### 3. GraphQL batch 形态（LIVE 通）
```
POST /service/udc/graphql?{opName}
body: {query: "mutation {op}($body:{op}InputBody){...}", variables:{body:{...}}}
仅 schema 内已注册的 op 可用（udcFunctionPost ✅ / udcPageInfoFunctionBaseInfoCreatePost ❌ 不在后端 5.3.496 schema）
```

### 4. 预置属性机制 LIVE 证实
新建实体自动获得 9 个系统字段（creator/tenantId/draft/version/createTime…），
与 platform_mechanism_model 的 9 标准事件/预置属性记录一致。

## 实验产物（遗留，可清理）
- 实体 xzhExp950795（474806313816300867）+ 字段 expText
- 菜单 小爪实验菜单（7853445889453184321）
- 页面 小爪实验页面951440（1520098474917276520，relationGroupId=-6298081275352303163）

## 下一步
1. 微流程建链（udcMicroflowCreatePost，GraphQL 形态待试）
2. 枚举建链（BOOT_1001 待调 body）
3. 全链打通后 → planner dry-run 对照 → 订单应用 spec 复用
