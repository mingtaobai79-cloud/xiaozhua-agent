# 应用测试→构建→运行：前端真实接口链（2026-10-31 实测）

> 来源：设计器右上角「测试」按钮抓包（应用测试弹窗 → 立即构建）。
> 这是 RUNTIME/BUILD 验收的权威链路，此前「无执行器」的推断部分作废。

## 1. 接口链

| 步骤 | 接口 | 要点 |
|---|---|---|
| 触发构建 | `udcRuntimeDeployNormalPost`（GraphQL，mutation） | body `{"deployDto":{appId,deployType:"RELEASE",projectType:"ALL",terminalType:"ALL"}}` → `deployId` |
| 状态轮询 | `udcSandboxBuildInfoAppGet`（path: appId） | `{state(BUILDING/SUCCESS/FAIL), progress, buildVersion, buildTime, logs[]}`；`logs` 即「展开沙箱日志」全文 |
| 详细日志 | `GET /service/udc/file/download?storageKey=compile-info/{appId}/{yyyymmddhhMMss}/backBuild.log` | maven 输出，`BUILD SUCCESS/FAILURE` + javac 错误全文 |
| 前端日志 | 同上 `frontInstall.log` / 前端构建日志 | 前端 PC+MOBILE 编译先行 |

阶段进度：82% ≈ 后端编译（FAIL 案例停在 82；SUCCESS 走到 91→100）。
构建产物 6 模块：`-facade/-biz/-web/-ext/-assemble-resource`（biz 里是微流程生成代码）。
版本号 = appVersion 1.0.{n}，每次构建 +1。

## 2. 实测案例：SCHEMA+UI 全绿但构建失败

`验证-DATA_MAPPING1928`（RETRIEVE 单条 → DATA_MAPPING）：
checkSchema=0 错、一致性检测 0 项、UI 2/2、 prove 全绿 ——
构建 82% 处 FAIL：

```
VerifyDataMapping1928Service.java: 找不到符号 方法 getName()
位置: 类型为 java.util.List<MigrationDatasourceDto> 的变量 _DATA_MAPPING_fbfa43
```

结论：
- **DATA_MAPPING 的代码生成器按「列表转换」产出**（语料 39 条：SUB_ENTITY/children 13、空引用 22、
  parent+MASTER 单对象仅 1 且场景特殊）。上游为单对象主实体时生成代码把节点输出声明成
  `List<Dto>` 再取字段 → 编译必炸。
- **闸门 G29**（已落地）：DATA_MAPPING selectParam dtoType=MASTER_ENTITY 且 position=parent → 拦。
- 校验链层级铁证：**L1/L2/L3 + 检测全过 ≠ 能编译**。BUILD 是独立维度（RUNTIME 前置）。

## 2.5 DATA_MAPPING 列表形态：两轮构建校准后的正确形态（BUILD SUCCESS 实证）

流：`验证-数据映射列表形态`（8266019240028362944：RETRIEVE_ARRAY → DATA_MAPPING → 统计 → END）
结构：8266019240028362944 构建于 1.0.81 轮 BUILD SUCCESS；UI 3/3、L2 0 问题。

正确形态（错一次学一条，全部来自 backBuild.log）：
1. `selectParam.type=ARRAY`、`name/outputName=上游节点出参名`（RETRIEVE_ARRAY 的 `_RETRIEVE_ARRAY_xxx`）
2. `structure.key` 恒为 `<源实体全名>_<目标实体全名>` 两段，**同实体自映射也要拼两段**
3. `output.type=ARRAY`（javaType 仍是单个 Dto、dataType=DTO）
4. **列表出参不能直接接 END basic 出参** → `List<Dto> 无法转换为 Dto`（[161,140]）；
   必须用 LIST_OPERATION(统计)/CHANGE_ENTITY 等承接
5. mappingRule 行内 targetField.id=`<目标Dto>.<field>`、value.reference.id=`<源Dto>.<field>` 不变

G29 判据相应精化：拦 `type=OBJECT + MASTER_ENTITY + parent`（单对象节点出参上游），
`type=ARRAY` 放行。

「数据源配置信息带子表」核实结果（用户提示 vs 平台元数据）：`hasChild=false`、
无任何实体 parentEntityId 指向它、MigrationDatasourceDto 无子列表字段 ——
该实体当前**没有**配置子表；列表形态用 RETRIEVE_ARRAY 上游验证通过。

## 3. 运行态入口现状

- 构建成功后测试版本运行（buildVersion 1.0.79），但 `POST /service/{app}/microflow/{name}` 仍 404：
  流程 `open_api=STOP`（未开对外接口）时**没有 HTTP 入口**；页面规则内部调用不走 REST。
- RUNTIME_VERIFIED 前置条件：流程开对外接口（openApi）或绑定页面规则后经页面触发；
  运行记录看「更多 → 微流程运行日志」（测试版本执行后才有数据）。

## 4. 与旧事实的关系

- 旧记录「deploy-normal + DELTA + search-deploy-status」为后端直连链，仍有效；
  本格是**前端同款**（应用测试弹窗）的 GraphQL 等价物，deployType=RELEASE。
- 「设计器没有执行器」修正为：设计器的「测试」=构建入口；执行证据在运行日志，无独立执行器。
