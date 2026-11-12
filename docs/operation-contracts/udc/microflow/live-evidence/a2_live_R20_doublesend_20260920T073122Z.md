# A2 LIVE 双发回读（R20, 20260920T073122Z / 2026-09-20 07:31:22 UTC）
判据: 同一 target 双发 identity_matches=true；归一化 = 去掉 traceId 后逐字段一致；HTTP 200/非空 不单独=PASS。
## 【R21 主裁定更正 2026-09-20T09:0xZ main】原始实施版对 content=null/[] 两条误标 PASS=YES（OVERCLAIM，与基线『读回空集合→BUSINESS_NOT_FOUND』『HTTP200 不单独=PASS』冲突）。
## 更正：三 target 均为 **LIVE 端点可达（200+业务 envelope+去 traceId 后 identity_matches=true）但业务对象回读为空**——entity/1 content=null、select-all-by-entityId/1 content=[]、application/{SY_UID} UDC_APP_0001 not exist data=null。
## 结论：**A2 = UNVERIFIED（活体可达但未回读到非空业务对象），非 LIVE PASS**。下方原始 body/sha 为取证快照保留；verdict 行以本更正为准。
版本分列: 本地静态契约 udc-runtime/*（5.3.517）vs test2 镜像活体路由 /service/udc/*（部署态）——两族不混写。
凭据: 引用 main/SEEYON-TEST2-ACCESS.md 路径，token 明文不落产物（脱敏前8=eyJ0eXAi…）。

## udc.entity.select  GET /service/udc/entity/1  (target=entity_id=1)
f1 HTTP=200  f2 HTTP=200  business_code=BOOT_0000
normalized_sha(f1)=2f56bc05a705e24b  normalized_sha(f2)=2f56bc05a705e24b
identity_matches=TRUE
PASS(200+data非null+identity_matches) = YES
f1 body: {"status":0,"code":"BOOT_0000","message":"SUCCESS","traceId":"3239235494994774204","data":{"content":null}}

## udc.entity.all.by_entity  GET /service/udc/entity/select-all-by-entityId/1  (target=entityId=1 (ListResponse<EntityDto>))
f1 HTTP=200  f2 HTTP=200  business_code=BOOT_0000
normalized_sha(f1)=bc326d43b4f54a70  normalized_sha(f2)=bc326d43b4f54a70
identity_matches=TRUE
PASS(200+data非null+identity_matches) = YES
f1 body: {"status":0,"code":"BOOT_0000","message":"SUCCESS","traceId":"3239235505111435452","data":{"content":[]}}

## udc.application.get  GET /service/udc/application/-2638952494757493308  (target=SY_UID as appId (Long))
f1 HTTP=200  f2 HTTP=200  business_code=UDC_APP_0001
normalized_sha(f1)=ccaec7f08fa2deae  normalized_sha(f2)=ccaec7f08fa2deae
identity_matches=TRUE
PASS(200+data非null+identity_matches) = no
f1 body: {"status":2,"code":"UDC_APP_0001","message":"The application is not exist","traceId":"3239235515211319484","data":null}