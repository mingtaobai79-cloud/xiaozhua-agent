# core/facts/modules/｜平台模块能力总索引

> 覆盖 **115** 个应用 / **176** 个构件 / **24618** 个类 / **249560** 个方法
> 来源：`docs/audit/artifacts/extension-surface-full/interfaces-full.json`（176 构件 javap 全量，无截断）

## 〇、已写「接口面」文档的模块（22 个）

这 22 个模块的 README 有完整四段：构件清单 → facade 入参表 → biz 服务/事件 → web Controller → 典型调用链。

| 模块 | 路径 | 接口 | 方法 |
|---|---|---:|---:|
| 组织架构 | `03-business-app/organization/` | 55 | 421 |
| 流程 | `03-business-app/bpm/` | 39 | 278 |
| 协同事项 | `03-business-app/ctp-affair/` | 10 | 79 |
| 用户中心 | `03-business-app/ctp-user/` | 40 | 220 |
| 消息通知 | `03-business-app/ctp-message/` | 11 | 41 |
| 应用管理/日志/媒体 | `03-business-app/ctp-other/` | 11 | 58 |
| 连接器 | `03-business-app/cip-connector/` | 25 | 124 |
| 集成能力 | `03-business-app/cip-capability/` | 47 | 446 |
| 集成提供方 | `03-business-app/cip-provider/` | 48 | 330 |
| 集成周边 | `03-business-app/cip-other/` | 23 | 94 |
| 低代码平台 | `02-udc/udc/` | 67 | 555 |
| 平台内核 | `01-platform/boot/` | 47 | 141 |
| 数据平台 | `03-business-app/cdp/` | 19 | 90 |
| 通用应用 | `03-business-app/app/` | 22 | 119 |
| 门户 | `03-business-app/portal/` | 5 | 36 |
| 移动端 | `03-business-app/m5/` | 6 | 30 |
| 开放集成 | `03-business-app/ocip/` | 4 | 16 |
| AI 能力 | `03-business-app/ai/` | 0 | 0（无 AppService，见 README）|
| 运维 | `01-platform/devops/` | 0 | 0（starter，无 AppService）|
| 网关 | `01-platform/gateway/` | 0 | 0（基础设施）|
| 构建插件 | `01-platform/maven/` | 0 | 0（构建期）|
| 构建 Mojo | `01-platform/mymojo/` | 0 | 0（构建期）|
| **合计** | | **479** | **3,078** |

**479 / 3,078 与索引里的 `*.api.*` + `*.appservice.*` 接口总数完全一致，无遗漏、无重复**
（`tools/core/platform/verify_all_modules.py` 自证，退出码 0）。

剩下 93 个应用目录只有结构性 README（构件 + 类数 + 调用方式判据），还没写接口表。

## 一、分组

| 分组 | 应用数 | 说明 |
|---|---:|---|
| `01-platform/` | 72 | 平台内核 + 每个 boot-starter 组件独立成应用 |
| `02-udc/` | 2 | UDC 自身（22 个构件） |
| `03-business-app/` | 41 | 标品业务应用 |

## 二、全部应用

| 分组 | 应用 | 构件 | 类 | 方法 | 层 |
|---|---|---:|---:|---:|---|
| 01-platform | **platform-core** | 4 | 557 | 4,166 | core |
| 01-platform | **boot-starter-datamigration** | 1 | 247 | 2,250 | starter |
| 01-platform | **boot-starter-formula** | 1 | 202 | 1,245 | starter |
| 01-platform | **boot-starter-mybatis** | 1 | 138 | 878 | starter |
| 01-platform | **boot-starter-communication** | 1 | 108 | 693 | starter |
| 01-platform | **boot-starter-extmetadata** | 1 | 106 | 1,223 | starter |
| 01-platform | **boot-starter-documentnumber** | 1 | 101 | 1,170 | starter |
| 01-platform | **boot-starter-cip** | 1 | 98 | 967 | starter |
| 01-platform | **boot-starter-file** | 1 | 89 | 1,045 | starter |
| 01-platform | **boot-starter-datainit** | 1 | 88 | 587 | starter |
| 01-platform | **boot-starter-serialnumber** | 1 | 85 | 874 | starter |
| 01-platform | **boot-starter-metadata** | 1 | 81 | 1,160 | starter |
| 01-platform | **boot-starter-condition** | 1 | 77 | 396 | starter |
| 01-platform | **boot-starter-excel** | 1 | 72 | 866 | starter |
| 01-platform | **boot-starter-graphql** | 1 | 71 | 627 | starter |
| 01-platform | **boot-starter-mq** | 1 | 68 | 495 | starter |
| 01-platform | **boot-starter-opinion** | 1 | 64 | 990 | starter |
| 01-platform | **boot-starter-web** | 1 | 60 | 426 | starter |
| 01-platform | **boot-starter-qrcode** | 1 | 59 | 495 | starter |
| 01-platform | **boot-starter-basicdata** | 1 | 57 | 676 | starter |
| 01-platform | **boot-starter-sandbox** | 1 | 53 | 531 | starter |
| 01-platform | **boot-starter-sharding** | 1 | 52 | 386 | starter |
| 01-platform | **boot-starter-enums** | 1 | 51 | 754 | starter |
| 01-platform | **boot-starter-cache** | 1 | 50 | 270 | starter |
| 01-platform | **boot-starter-ganttchart** | 1 | 50 | 572 | starter |
| 01-platform | **boot-starter-schedule** | 1 | 50 | 364 | starter |
| 01-platform | **boot-starter-dubbo** | 1 | 48 | 220 | starter |
| 01-platform | **boot-starter-dynamicsql** | 1 | 42 | 381 | starter |
| 01-platform | **boot-starter-appservice** | 1 | 41 | 196 | starter |
| 01-platform | **boot-starter-formconvert** | 1 | 40 | 402 | starter |
| 01-platform | **boot-starter-module** | 1 | 40 | 216 | starter |
| 01-platform | **boot-starter-prometheus** | 1 | 32 | 122 | starter |
| 01-platform | **boot-starter-datasource** | 1 | 29 | 622 | starter |
| 01-platform | **boot-starter-i18n** | 1 | 28 | 367 | starter |
| 01-platform | **boot-starter-queue** | 1 | 28 | 90 | starter |
| 01-platform | **platform-tooling** | 4 | 27 | 304 | tooling |
| 01-platform | **boot-starter-elasticsearch** | 1 | 25 | 252 | starter |
| 01-platform | **boot-starter-k8s** | 1 | 25 | 194 | starter |
| 01-platform | **boot-starter-swagger** | 1 | 25 | 131 | starter |
| 01-platform | **boot-starter-index** | 1 | 24 | 133 | starter |
| 01-platform | **boot-starter-nacos** | 1 | 24 | 184 | starter |
| 01-platform | **boot-starter-captcha** | 1 | 23 | 77 | starter |
| 01-platform | **boot-starter-datatype** | 1 | 23 | 160 | starter |
| 01-platform | **boot-starter-eventbus** | 1 | 23 | 138 | starter |
| 01-platform | **boot-starter-labelprint** | 1 | 23 | 213 | starter |
| 01-platform | **boot-starter-parameter** | 1 | 22 | 248 | starter |
| 01-platform | **boot-starter-proxy** | 1 | 18 | 115 | starter |
| 01-platform | **boot-starter-license** | 1 | 17 | 168 | starter |
| 01-platform | **boot-starter-security** | 1 | 17 | 83 | starter |
| 01-platform | **boot-starter-artifact** | 1 | 16 | 96 | starter |
| 01-platform | **boot-starter-attachment** | 1 | 15 | 151 | starter |
| 01-platform | **boot-starter-dynamicloader** | 1 | 15 | 109 | starter |
| 01-platform | **boot-starter-k8s-adapter** | 1 | 15 | 105 | starter |
| 01-platform | **boot-starter-monitor** | 1 | 15 | 151 | starter |
| 01-platform | **boot-starter-transaction** | 1 | 15 | 56 | starter |
| 01-platform | **platform-sentinel** | 2 | 15 | 133 | module |
| 01-platform | **boot-starter-dynamiccode** | 1 | 14 | 136 | starter |
| 01-platform | **boot-starter-threadpool** | 1 | 14 | 113 | starter |
| 01-platform | **boot-starter-upgrade** | 1 | 14 | 106 | starter |
| 01-platform | **boot-starter-environment** | 1 | 13 | 77 | starter |
| 01-platform | **boot-starter-spi** | 1 | 12 | 52 | starter |
| 01-platform | **boot-starter-lock** | 1 | 9 | 80 | starter |
| 01-platform | **boot-starter-mgn-export** | 1 | 9 | 48 | starter |
| 01-platform | **boot-starter-sensitive** | 1 | 9 | 40 | starter |
| 01-platform | **boot-starter-test** | 1 | 9 | 37 | starter |
| 01-platform | **boot-starter-filterchain** | 1 | 8 | 22 | starter |
| 01-platform | **boot-starter-frontend-log** | 1 | 8 | 26 | starter |
| 01-platform | **boot-starter-websocket** | 1 | 8 | 23 | starter |
| 01-platform | **boot-starter-tomcat** | 1 | 7 | 51 | starter |
| 01-platform | **boot-starter-shortlink** | 1 | 5 | 15 | starter |
| 01-platform | **boot-starter-systemvariable** | 1 | 4 | 147 | starter |
| 01-platform | **boot-starter-scanner** | 1 | 2 | 124 | starter |
| 02-udc | **udc** | 22 | 3,708 | 40,349 | biz,facade,module,starter,web |
| 02-udc | **udc-plugin** | 1 | 307 | 2,667 | api |
| 03-business-app | **bpm** | 3 | 3,326 | 37,610 | biz,facade,web |
| 03-business-app | **cdp-data** | 3 | 2,102 | 16,464 | biz,facade,web |
| 03-business-app | **cip-capability** | 4 | 1,709 | 15,510 | api,biz,facade,web |
| 03-business-app | **cip-connector** | 4 | 1,463 | 14,404 | api,biz,facade,web |
| 03-business-app | **ctp-user** | 4 | 1,227 | 13,448 | api,biz,facade,web |
| 03-business-app | **organization** | 3 | 1,142 | 18,032 | biz,facade,web |
| 03-business-app | **app-common** | 3 | 770 | 7,376 | biz,facade,web |
| 03-business-app | **portal** | 3 | 675 | 8,373 | biz,facade,web |
| 03-business-app | **app-doc** | 3 | 500 | 4,686 | biz,facade,web |
| 03-business-app | **cdp-schedule** | 2 | 486 | 3,896 | biz,web |
| 03-business-app | **ctp-affair** | 3 | 481 | 6,782 | biz,facade,web |
| 03-business-app | **m5** | 3 | 473 | 4,056 | biz,facade,web |
| 03-business-app | **cip-capability-common** | 1 | 425 | 5,252 | module |
| 03-business-app | **cip-manager** | 3 | 423 | 3,574 | biz,facade,web |
| 03-business-app | **cdp-common** | 1 | 279 | 2,452 | module |
| 03-business-app | **app-approval** | 3 | 269 | 2,599 | biz,facade,web |
| 03-business-app | **ctp-message** | 3 | 205 | 1,333 | biz,facade,web |
| 03-business-app | **ai** | 2 | 136 | 1,258 | biz,web |
| 03-business-app | **ocip-common** | 1 | 125 | 2,315 | module |
| 03-business-app | **ai-core** | 1 | 101 | 548 | module |
| 03-business-app | **bpm-org** | 2 | 89 | 706 | facade,module |
| 03-business-app | **apps-ocip-sdk** | 1 | 86 | 570 | module |
| 03-business-app | **cip-openapi-gateway** | 2 | 64 | 418 | biz,web |
| 03-business-app | **devops-starter-pipeline** | 1 | 60 | 704 | module |
| 03-business-app | **cip-convert** | 3 | 56 | 404 | biz,facade,web |
| 03-business-app | **devops-starter-repo** | 1 | 53 | 722 | module |
| 03-business-app | **devops-starter-artifact** | 1 | 51 | 611 | module |
| 03-business-app | **devops-starter-common** | 1 | 51 | 338 | module |
| 03-business-app | **ctp-webapi-gateway** | 2 | 38 | 188 | biz,web |
| 03-business-app | **ctp-media** | 3 | 27 | 356 | biz,facade,web |
| 03-business-app | **cip-openapi-common** | 1 | 21 | 134 | module |
| 03-business-app | **devops-starter-migration** | 1 | 16 | 121 | module |
| 03-business-app | **devops-starter-images** | 1 | 14 | 135 | module |
| 03-business-app | **gateway-spi** | 1 | 13 | 55 | module |
| 03-business-app | **ocip-common-mime** | 1 | 10 | 58 | module |
| 03-business-app | **cip-spi-user-sso-changhong** | 1 | 5 | 29 | module |
| 03-business-app | **gateway-filter** | 1 | 2 | 2 | module |
| 03-business-app | **ocip-exchange-axis2** | 1 | 1 | 5 | module |
| 03-business-app | **bpm-ext-models** | 1 | 0 | 0 | module |
| 03-business-app | **jakarta.persistence** | 1 | 0 | 0 | api |
| 03-business-app | **mobile-message-client** | 1 | 0 | 0 | api |

## 三、怎么用这个目录

```
要调某个能力：
  1. 先在本表找到应用
  2. 进 <分组>/<应用>/README.md 看构件清单与层职责
  3. facade 层查方法签名 → core/facts/platform-dev-system/04
  4. 要知道数据落哪张表 → 该模块 README 的「## 落表」段
     （全量清单与证据链：docs/audit/artifacts/tables/README.md）
  5. 判断能否泛化 → core/facts/usage/U1-invocation-decision.md
```

### 落表覆盖（阶段3 第一轮已完成）

15 / 22 个模块拿到真实表名（670 张次），证据 = class 常量池字面量 × `information_schema` 白名单，
等级 `VERIFIED_STATIC_BYTECODE` + `LIVE`。粒度是**类级**；方法级仍未取证（平台 SQL 内联，需逐类反编译）。
7 个模块无表名常量（`boot` / `ocip` / `ai` / `devops` / `gateway` / `maven` / `mymojo`），标 `N/A`，不猜。

## 四、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 24,618 类 / 249,560 方法 | 176 构件 javap 全量提取（`--limit 100000`） | **VERIFIED_STATIC_BYTECODE** |
| 7 个失败构件 | `boot-maven-plugins` / `bpm-ext-models` / `cglib` / `jakarta.persistence-api` / `mobile-message-client-api` / `seeyon-archetype-ext` / `udc-test`（均无 `com.seeyon` 类） | **VERIFIED_STATIC_BYTECODE** |
