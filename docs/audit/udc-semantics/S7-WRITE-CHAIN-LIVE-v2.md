# S7 写链实验 LIVE 结果 v2（微流程 + 枚举链补全）

> 日期：2026-10-14 | 应用：datamigration…（9000000000000000002）| xzh 前缀隔离 | 证据：**LIVE**
> 接续：S7-WRITE-CHAIN-LIVE.md（v1：实体/字段/菜单/页面）

## 新打通的写链

| # | 链路 | 形态 | 关键字段（javap 权威） | 结果 |
|---|---|---|---|---|
| W5 | **建微流程** | GraphQL `udcMicroflowCreatePost` | type=CUSTOM / triggerType=MANUAL / groupType=DEFAULT / nodes=[] / trigger={} | ✅ id=5810815099733137875（DRAFT，guid 自动生成）|
| W5b | **改微流程** | GraphQL `udcMicroflowUpdatePost`（整 schema 回传）| 全量 DTO 回传 + caption 修改 | ✅ content=1 |
| W6 | **建枚举** | REST `POST /udc/udc-enum` | **appId 必须数字 Long**；udcEnumType ∈ {DEFAULT,CONNECTOR,DYNAMIC_DEPENDENCY}；**name 必须大写字母开头** | ✅ id=3934748939202274853 |
| W6b | **加枚举项** | REST `POST /udc/udc-enum-item` | **enumId 必填**（不能与枚举一体创建）+ item.code 必填 Integer | ✅ ONE/TWO（code 1/2）|

## 本轮新增的机制实证

1. **微流程空基座即合法**：nodes=[] + triggerType=MANUAL 直接创建成功（schema 校验在 checkSchema/update 时才触发）
2. **校验错误链很有价值**（错误消息就是字段说明书）：
   - `UDC_ENUM_0001 code must start with uppercase` → 命名规范
   - `No enum constant UdcEnumTypeEnum.SYSTEM` → 合法值域
   - `enumId must not be null` → 枚举/枚举项必须分两步
   - `appId must be Long`（隐含在 BOOT_1001 里）→ 数字类型
3. **GraphQL batch 形态正式确立**（菜单/微流程通用）：
   ```
   POST /service/udc/graphql?{opName}
   {"query":"mutation {op}($body:{op}InputBody){...}","variables":{"body":{...}}}
   ```

## 累计写链（6 条全通）
实体 ✅ / 字段 ✅ / 菜单 ✅ / 页面 ✅ / 微流程（建+改）✅ / 枚举+项 ✅

## 遗留实验对象（xzh 前缀，可清理）
- 实体 xzhExp950795 + 字段 expText
- 菜单 小爪实验菜单（7853445889453184321）
- 页面 小爪实验页面951440（1520098474917276520）
- 微流程 xzhMf953182（5810815099733137875）
- 枚举 XzhEnum（3934748939202274853）+ 2 项

## 下一步
1. 字段类型扩展实验：枚举字段（CTPENUM 引用 W6 枚举）/ 人员多选 / 索引
2. 页面 schema 更新链（update/update-draf）
3. 全链通 → planner dry-run 对照 → 收敛为订单应用 spec 模板
