# 证据件索引

> 自动生成，勿手改。`python tools/core/platform/emit_evidence_index.py` 重跑。
> 所有产物都可重建；数字以本文件为准，别信记忆里的旧数字。

## 一、事实格（权威，环境无关）

`core/facts/standard-product/` 共 28 份 md，按用途分五组：

| 组 | 文件 | 管什么 |
|---|---|---|
| **用法** | `transport-usage.md` | 出入参包装 |
| | `appservice-usage.md` | AppService 调用约定 |
| | `appservice-invocation.md` | 两条调用通路 + 泛化调用协议 |
| | `appservice-dto-fields.md` | DTO 字段表 |
| | `dao-and-mybatis.md` | Dao 层与条件构造 |
| | `dubbo-cross-service.md` | 跨服务调用 |
| | `boot-core-utils-and-annotations.md` | 工具类与注解 |
| | `enums-and-constants.md` | 枚举 758 个 / 常量 |
| | `platform-annotations.md` | 109 个注解的元信息 |
| **扩展点** | `extension-point-decision-table.md` | 60 行场景表：要干什么 → 实现哪个接口 |
| | `extension-point-consumers.md` | 154 跨包 / 21 同包 / 8 零引用 |
| | `extension-registration-mechanisms.md` | 四条注册通路 |
| | `udc-microflow-extend-interfaces.md` | 微流程 128 接口 |
| | `extension-project-skeleton.md` | 五模块骨架 + 只有 -ext 可写 |
| **查询** | `business-action-index.md` | 业务动作索引（要做什么→调哪个） |
| | `api-usage-cards.md` | 接口使用卡说明 + @DtoAttribute |
| | `service-business-flow.md` | 业务流转两层结构 |
| | `interface-inventory.md` | 1457 个接口全量清单
| **平台面** | `platform-package-capability-index.md` | 91 构件包级能力 |
| | `standard-product-appservice-surfaces.md` | 标准产品 AppService 面 |
| | `standard-product-contracts.md` | 契约总表 |
| **前端** | `frontend-platform-packages.md` | 三包分工 |
| | `frontend-package-capability-index.md` | 50 包能力 |
| | `frontend-component-signatures.md` | 117 组件 props |
| **运行** | `udc-runtime-and-extend-packages.md` | UDC 运行时包 |

## 二、证据件（含版本，可重跑）

| 文件 | 体量 | 内容 | 生成器 |
|---|---|---|---|
| `interfaces.json` | 63.9 MB | 21389 类 / 1457 接口 / 327 AppService / 224320 方法 | `index_backend_interfaces.py` + `merge_biz_index.py` |
| `dto-meta.json` | 932 KB | 1305/1331 个 DTO 的 `@DtoAttribute` | `scan_dto_meta.py` |
| `impl-map.json` | 51 KB | 269 接口 → 实现类 | `build_impl_map.py` |
| `action-index.md` | 125 KB | 业务动作 → 方法 → DTO → 流转 | `emit_action_index.py` |
| `interface-inventory.md` | 146 KB | 接口全量清单 | `emit_interface_inventory.py` |
| `batch3/` | 62.2 MB | 21 个 biz 构件原始抽取 | `rebuild_surfaces.py` |
| `packages/` | 3.2 MB | 91 份构件签名 | `emit_package_surfaces.py` |
| `domains/` | 379 KB | 11 份域签名 | `emit_domain_surfaces.py` |
| `dto-fields/` | 549 KB | 12 份域 DTO 字段 | `emit_dto_fields.py` |
| `api-usage/` | 3.3 MB | 10 份接口使用卡 | `emit_api_usage.py` |
| `service-flow-20261103/` | 5.1 MB | 17 份方法体调用链 | `emit_service_flow.py` |
| `frontend-surface-20261102/` | 1.5 MB | 50 包 / 117 组件 props | `extract_extension_surface.py` + `resolve_external_props.py` |

## 三、重跑命令（按依赖顺序）

```bash
cd <SEEYON_AGENT_ROOT>

# 0) 实现 jar（只跑一次；已下到 <MAVEN_REPO>-extra）
python tools/core/platform/fetch_biz_jars.py \
    --base http://10.0.0.1/artifactory/libs-release/com/seeyon --out <MAVEN_REPO>-extra

# 1) 抽符号（91 facade + 21 biz）
python tools/core/platform/rebuild_surfaces.py --interfaces <seed.json> \
    --repo <MAVEN_REPO>-extra --out-dir <D>/batch3 --jobs 8 --timeout 5400

# 2) 合并索引
python tools/core/platform/merge_biz_index.py --interfaces <D>/interfaces.json \
    --batch <D>/batch3 --emit <D>/interfaces.json

# 3) 接口→实现映射（读字节码，不能靠命名猜）
python tools/core/platform/build_impl_map.py --repo <MAVEN_REPO>-extra \
    --emit <D>/impl-map.json

# 4) 方法体调用链
python tools/core/platform/emit_service_flow.py --repo <MAVEN_REPO>-extra \
    --pkg <构件...> --only-impl --suffix=-appservice --emit-dir <flow-dir>

# 5) DTO 字段说明（javap -p -v，GBK 解码）
python tools/core/platform/scan_dto_meta.py --interfaces <D>/interfaces.json \
    --emit <D>/dto-meta.json

# 6) 三份查询表
python tools/core/platform/emit_action_index.py --interfaces <D>/interfaces.json \
    --flow-dir <flow-dir> --impl-map <D>/impl-map.json --emit <D>/action-index.md
python tools/core/platform/emit_api_usage.py --interfaces <D>/interfaces.json \
    --impl-map <D>/impl-map.json --flow-dir <flow-dir> --dto-meta <D>/dto-meta.json \
    --emit-dir docs/audit/artifacts/api-usage
python tools/core/platform/emit_interface_inventory.py --interfaces <D>/interfaces.json \
    --emit <D>/interface-inventory.md

# 7) 契约探针（编译验证）
python tools/core/platform/probe_contracts.py --src tools/core/platform/probe_contracts \
    --repo <MAVEN_REPO> --interfaces <D>/interfaces.json

# 8) 索引自身
python tools/core/platform/emit_evidence_index.py
```

## 四、可信等级（照这个判，别混用）

| 等级 | 含义 | 本轮覆盖 |
|---|---|---|
| `VERIFIED_COMPILE` | 用真实 jar 编译通过 | 3 个动作（BPM 发起 / 建实体 / 发布） |
| `VERIFIED_STATIC_BYTECODE` | 反编译/javap 逐字读到 | 全部签名、字段、流转、注解 |
| `LIVE` | 真实环境跑通 | **0** |
| `INFER` | 从证据推断，未直接验证 | 254 个无实现接口的归属 |
| `UNVERIFIED` | 明确没验 | 运行时行为、字段必填、`paramJson` 边界 |

## 五、机器环境（换机器要改的）

```
javap/javac   <LOCAL_ROOT>/java/bin/
maven 仓库    <MAVEN_REPO>           （facade/api，1854 个 jar）
实现 jar      <MAVEN_REPO>-extra     （21 个 *-biz）
cfr           <PATH>
python        ./.venv/Scripts/python.exe
```

## 六、已知坑（跑之前先看）

- **javap 必须 `-p -v`**：只 `-v` 看不到 private 字段，字段注解全丢。
- **javap 输出是 GBK**：按 utf-8 解得到 `ģ��code`，要 gbk 解。
- **native 程序不认 MSYS 路径**：`-cp /d/repo/x.jar` 失败，用 `<PATH>
- **bpm-biz 会超时**：2943 类，`--timeout` 给到 5400 且单独跑。
- **不要按命名猜实现**：`BpmAppService` → `BpmApiAppServiceImpl`，只能读字节码。
- **`--suffix=-xxx` 必须等号形式**：argparse 会把 `-xxx` 当选项。
