# 资产清单（哪些进仓库、哪些不进）

> 自动生成，勿手改。`python tools/inventory_assets.py` 重跑。
> 体积与客户痕迹计数从磁盘现算；判定口径见脚本 `EXPORT_POLICY`。

- `docs/audit/artifacts` 合计 **390.3 MB** / 48 项
- 随仓库 **25** 项 · 可重建 **1** 项 · 不收录 **27** 项 · 未判定 **0** 项

## 一、随仓库（clone 就有）

| 资产 | 体积 | 文件 | 说明 |
|---|---|---|---|
| `udc-publish-5.3.517` | 3.19 MB | 63 | 在 udc-platform-*.tar.gz 中：页面/应用发布入口 |
| `udc-web-5.3.517-contracts` | 2.63 MB | 60 | 在 udc-platform-*.tar.gz 中：54 Controller / 674 端点的端点表 |
| `udc-web-5.3.517` | 2.38 MB | 1 | 在 udc-platform-*.tar.gz 中：全部 Controller javap 单文件 |
| `udc-runtime-5.3.517` | 1.84 MB | 75 | 在 udc-platform-*.tar.gz 中：UdcBaseGeneralController / UdcRestPathParse |
| `udc-resource-5.3.517` | 1.78 MB | 46 | 在 udc-platform-*.tar.gz 中 |
| `extmetadata-5.3.318` | 1.62 MB | 31 | 在 udc-platform-*.tar.gz 中：UdcEntityMetaDataService 元数据契约 |
| `metadata-5.3.358` | 0.78 MB | 10 | 在 udc-platform-*.tar.gz 中：MetadataService / MetadataController |
| `runtime-lowcode-5.3.517` | 0.51 MB | 1 | 在 udc-platform-*.tar.gz 中 |
| `udc-page-5.3.517` | 0.38 MB | 11 | 在 udc-platform-*.tar.gz 中，仅排除 2 个 LIVE-* 运行记录 |
| `udc-biz-5.3.517` | 0.33 MB | 65 | 在 udc-platform-*.tar.gz 中 |
| `udc-flow-5.3.517` | 0.15 MB | 20 | 在 udc-platform-*.tar.gz 中 |
| `udc-web-5.3.517-methods` | 0.14 MB | 1 | 在 udc-platform-*.tar.gz 中：方法索引 |
| `udc-app-basic` | 0.12 MB | 7 | 在 udc-platform-*.tar.gz 中 |
| `udc-user-5.3.517-contracts` | 0.09 MB | 2 | 在 udc-platform-*.tar.gz 中 |
| `udc-expression-functions.json` | 0.06 MB | 1 | 在 udc-platform-*.tar.gz 中：表达式函数树 |
| `udc-expression-samples.json` | 0.06 MB | 1 | 在 udc-platform-*.tar.gz 中：真实样本 |
| `udc-common-5.3.517` | 0.04 MB | 2 | 在 udc-platform-*.tar.gz 中 |
| `udc-expression-system-variables.json` | 0.03 MB | 1 | 在 udc-platform-*.tar.gz 中：系统变量 |
| `udc-expression-contracts.json` | 0.02 MB | 1 | 在 udc-platform-*.tar.gz 中：token 类型与可执行判定 |
| `udc-expression-schema-full.json` | 0.02 MB | 1 | 在 udc-platform-*.tar.gz 中：ENTITY / CONFIG_PARAM 结构 |
| `udc-runtime-5.3.517-javap` | 0.02 MB | 3 | 在 udc-platform-*.tar.gz 中 |
| `udc-entity-to-ctpenum-mechanism-20261013.md` | 0.01 MB | 1 | 在 udc-platform-*.tar.gz 中：关联字段→枚举切换机制 |
| `udc-expression-schema-paramtypes.json` | 0.01 MB | 1 | 在 udc-platform-*.tar.gz 中：参数类型 |
| `mf_realdataschema.json` | 0.00 MB | 1 | 在 udc-platform-*.tar.gz 中：微流程节点真实 io schema |
| `core/facts/**/evidence/（已脱敏的部分除外）` | 0.00 MB | 0 | 305 个事实依据文件已脱敏入仓 |

## 二、可重建（不随仓库，一条命令重造）

| 资产 | 原体积 | 文件 | 重建方式 |
|---|---|---|---|
| `extension-surface-20261029` | 293.74 MB | 341 | 原始反编译面 293 MB；签名已由 signatures.txt.gz 覆盖，契约/字段/实现类已由 surface-index.tar.gz + udc-platform 包覆盖 |

## 三、不收录（含客户痕迹或纯噪声）

| 资产 | 体积 | 文件 | 客户痕迹 | 原因 |
|---|---|---|---|---|
| `decompiled` | 43.69 MB | 7540 | 真人名×11、客户组织×91、客户名(中文)×12、环境域名×91、appId×178、内网IP×10 | 50 个临时 CFR 目录、版本重复，混客户组织名 / 环境域名 / 178 处真实 appId / 11 处真人名；需要源码用 cfr-0.152.jar 重跑 |
| `scratch-migrated` | 13.25 MB | 176 | appId×56、客户组织×11、环境域名×10、客户名(中文)×4 | 迁移过程草稿，无稳定结构，无代码引用 |
| `service-flow-20261103` | 5.13 MB | 18 | appId×1 | 文件名即含真实 appId 与手机号，客户业务流证据 |
| `api-usage` | 3.30 MB | 11 | 内网IP×2 | 含内网 IP 与客户侧字段示例，可重跑 emit_api_usage.py 得到 |
| `udc-web-5.3.517-javap` | 2.54 MB | 58 | — | 与 udc-web-5.3.517-contracts 内的 javap 同源重复，且含 1 处内网 IP |
| `udc-frontend-5.3.496` | 2.41 MB | 1 | — | 单个 2.4 MB 压缩后的 redux store chunk，噪声大于信息 |
| `udc-node-evidence` | 2.32 MB | 35 | 客户组织×5、环境域名×5、appId×29 | 含客户组织名、环境域名、29 处真实 appId |
| `udc-bi-5.3.260` | 2.01 MB | 104 | appId×17 | 含环境域名与 17 处真实 appId |
| `udc-bi-5.3.517` | 2.01 MB | 68 | 客户组织×3、环境域名×2、appId×3 | 含 CDP 抓包原文与客户组织名 |
| `frontend-surface-20261102` | 1.48 MB | 2 | appId×1 | 客户应用自己的前端快照（appId + @seeyon 依赖版本） |
| `udc-app-deploy-info-5.3.496` | 0.54 MB | 34 | 客户组织×19、环境域名×19、appId×20、真人名×1 | 20 处真实 appId + 真人名 |
| `udc-frontend-ops` | 0.40 MB | 5 | appId×2、客户组织×1 | 含真实 appId 与客户组织名 |
| `udc-menu-5.3.517` | 0.31 MB | 14 | 客户组织×1、环境域名×1 | 含客户组织名；且菜单域按既定边界不推进 |
| `udc-entity-5.3.517` | 0.29 MB | 16 | — | 含环境域名；实体域已有 core/facts/udc/entity 事实 |
| `udc-assemble-5.3.517-deployed` | 0.27 MB | 2 | 客户组织×1 | 含客户组织名与环境域名 |
| `u6-nacos-config` | 0.16 MB | 6 | 客户组织×4、内网IP×2、客户名(中文)×2、环境域名×2 | 含客户组织名、环境域名、内网 IP |
| `u5-storage` | 0.11 MB | 20 | — | 含环境域名 + 5 处内网 IP |
| `udc-entity-customplan-5.3.517` | 0.07 MB | 3 | — | 含环境域名 |
| `u4-gateway` | 0.02 MB | 2 | 客户组织×2、环境域名×2、内网IP×1 | 含客户组织名 + 内网 IP |
| `README.md` | 0.01 MB | 1 | — | 描述的是完整 409 MB 证据根，与分发形态不符；分发说明见 REGENERATE-EVIDENCE.md |
| `s7_w1_result.json` | 0.01 MB | 1 | appId×1 | 一次性实测返回（建单结果 id），结论已入 core/facts |
| `udc-expression-functions-raw.json` | 0.01 MB | 1 | — | 函数树原始中间件，已由 functions.json 结构化版本覆盖 |
| `s7_w3_result.json` | 0.00 MB | 1 | appId×1 | 一次性实测返回（建页结果 id），结论已入 core/facts |
| `docs/audit/evidence/` | 0.00 MB | 0 | — | 客户业务证据（截图/回读记录），脱敏后也失去证据价值 |
| `tools/core/feishu/` | 0.00 MB | 0 | — | 一次性排障脚本，硬编码真实飞书 TOKEN，运行时 0 引用 |
| `skills/06-delivery/<客户项目>-pmp/` | 0.00 MB | 0 | — | 客户项目专属 skill |
| `docs/audit/column-discovery/raw-nav-capture-*.json` | 0.00 MB | 0 | — | 页面导航抓包含 42 处真实操作人姓名 |

## 四、仓库外的排除项

| 位置 | 原因 |
|---|---|
| `docs/audit/evidence/` | 客户业务证据（截图/回读记录），脱敏后也失去证据价值 |
| `core/facts/**/evidence/（已脱敏的部分除外）` | 305 个事实依据文件已脱敏入仓 |
| `tools/core/feishu/` | 一次性排障脚本，硬编码真实飞书 TOKEN，运行时 0 引用 |
| `skills/06-delivery/<客户项目>-pmp/` | 客户项目专属 skill |
| `docs/audit/column-discovery/raw-nav-capture-*.json` | 页面导航抓包含 42 处真实操作人姓名 |

## 五、一句话重建全部证据

```bash
python tools/regen_evidence.py          # 抽取 + 聚合 + 签名索引
python tools/build_reference_bundle.py --profile core
python tools/build_reference_bundle.py --profile surface
python tools/build_app_service_index.py
python tools/build_component_index.py --modules <pc/node_modules>
```
