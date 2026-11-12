# udc.runtime-data.read｜运行态表单数据查询（LIVE 2026-09-25）

## 1. Capability
`udc.flow.form_data_query`（registry 登记）/ 同端点双 ID 之一 `udc.entity_data.query_form_data`
（双斜杠路径 `udc-runtime/data//query` 逐字保留，registry L101-102 注记）。
CONFIG 型只读能力：按实体+数据 id 查单条表单数据。

## 2. Version
Canonical=5.3.517（registry 锚点）。`EntityDataRequestDto` 完整字段清单 UNVERIFIED
（本地无 jar 源，错误 oracle 反推三键，见 §3）。

## 3. Input（LIVE 实测错误信息即参数字典）
端点 `POST {gateway}/{PF}/udc-runtime/data/query`，body SingleRequest 包装：
`{"data":{...}}`。
- 三参数字典（2026-09-25 BOOT_3000 原文）：
  `appName 应用编码;  dataId 数据id;  entityFullName 实体FullName`
- 本端点是**按 dataId 查单条**语义，非列表分页（pageNo/pageSize 被忽略）。

## 4. Required
`appName` + `entityFullName` + `dataId` 三键语义并列（逐键必填性未单键实测 → 标注）。
网关前缀 `{PF}=/service/{app}` 下可通（2026-09-25 实测 BOOT_0000 级响应路径打开；
无 `udc-runtime/` 直挂 service 前缀被 nginx 403/404——前缀白名单见 A6/网关证据）。

## 5. Execution
只读查询；响应 `SingleResponse<EntityDataResponseDto>`。列表/详情/新建数据走生成态
controller（模板 `autocode/JAVA/2.9/templates/entity/pagecontroller.java.ftl`，
jar 内确认存在 2.7/2.8/2.9 三版；路由形态 UNVERIFIED——jar 解包未在本机完成）。

## 6. Side Effects
无（读面）。

## 7. Known Constraints
- 09-24 晚 `data/query` 曾被 nginx 403（IP 白名单时点收紧），09-25 恢复 200——
  该面对网络策略敏感，BLOCKED 先查环境再查契约。
- 运行态可读的前提：RELEASE 构建成功且实体 publishState 进运行态；未发布实体
  的 dataId 行为未实测（UNVERIFIED）。

## 8. Evidence
- LIVE 2026-09-25 15:5x：BOOT_3000 参数字典原文（本格 §3）；traceId 3246998001134078140 / 3246998500625352892
- 模板存在性：jar 清单 `unzip -l udc-biz-5.3.517.jar`（跳板 pod 只读，09-25）
- registry 契约行：`components/platform_operations/registry.py` F2 + entity md 双斜杠条

## 9. Verified
LIVE（端点+参数字典+响应形态）/ 其余字段级 = STATIC+UNVERIFIED。
