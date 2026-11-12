#!/usr/bin/env python3
"""实现 jar 到手后，更新两个事实格的覆盖数字与结论。"""
from pathlib import Path

FD = Path("<SEEYON_AGENT_ROOT>/core/facts/standard-product")

REPS_ACTION = [
    ("| 仓库里有实现类 | **517**（68 个接口） |",
     "| 有实现类 | **2127**（269 个接口） |"),
    ("| 能追到方法体流转 | **370** |",
     "| 能追到方法体流转 | **1884** |"),
    ("**关键事实**：322 个 AppService 里**只有 68 个在仓库有实现类**（46 个在 udc-biz）。\n\n"
     "⇒ **BPM / 组织架构 / 事项 / 连接器 的实现在平台服务端**，仓库里只有接口 jar。\n"
     "这些域只能给「接口 + 入参 DTO」，流转追不到，要实测或看平台日志。\n"
     "**UDC 域（46 个 AppService）能追全链**。",
     "**关键事实**：322 个 AppService 里 **269 个已拿到实现类**。\n\n"
     "实现 jar 不在本机 Maven 仓库（`<MAVEN_REPO>` 只有 facade/api），\n"
     "从 Artifactory `libs-release` 下载了 21 个 `*-biz` 构件（40 MB / 15869 类）到\n"
     "`<MAVEN_REPO>-extra`：bpm-biz、organization-biz、ctp-{affair,user,message,media}-biz、\n"
     "cip-{capability,connector,convert,manager,openapi-gateway}-biz、app-{approval,common,doc}-biz、\n"
     "cdp-{data,schedule}-biz、m5-biz、portal-biz、ai-biz、udc-biz。\n\n"
     "⇒ **BPM / 组织架构 / 事项 / 连接器 / 连接器能力 的流转现在都能追**。\n"
     "剩下 53 个接口的实现确实不在这些 jar 里（多为纯接口或平台运行时装配）。\n\n"
     "⚠️ 仓库**没有 `-sources.jar`**（Artifactory 搜索 `*-sources.jar` 返回空），\n"
     "只有 class jar，所以是反编译方法体，不是读源码。"),
    ("`send` / `submit` / `saveDraft` / `stepBack` / `repeal` / `stop` / `takeBack` /\n"
     "`replace` / `pause` / `cancelPause` / `counterSignNode` / `addNode` —— 全在 `BpmAppService`。\n"
     "入参 DTO 在 `dto-fields/bpm.md`（`BpmSendDto` 10 字段等），流转标 UNVERIFIED。",
     "`send` / `submit` / `saveDraft` / `stepBack` / `repeal` / `stop` / `takeBack` /\n"
     "`replace` / `pause` / `cancelPause` / `counterSignNode` / `addNode` —— 全在 `BpmAppService`，\n"
     "实现是 **`BpmApiAppServiceImpl`**（不是 `BpmAppServiceImpl`，命名不规则，靠猜会漏）。\n\n"
     "`send()` 的真实流转（反编译 `bpm-biz-appservice.md`）：\n\n"
     "```\n"
     "BpmUserTemplateService.selectCanSendTemplateByCode   ← 查可用模板\n"
     "BpmTemplateService.selectEntityById                   ← 查模板实体\n"
     "UserAppServiceProxy.getBpmMemberPost                  ← 跨服务取人员岗位\n"
     "BpmOperationService.send                              ← 真正的发送\n"
     "MessageRepository.getMessage                          ← 消息\n"
     "BpmCommonUtil.isLongNull / ExceptionUtil.isTrue       ← 参数校验与异常\n"
     "BeanCopier.copy                                        ← DTO 拷贝\n"
     "```\n\n"
     "入参 DTO 在 `dto-fields/bpm.md`（`BpmSendDto` 10 字段）。"),
    ("- 254 个 AppService 无实现类 → 流转 UNVERIFIED\n"
     "- 流程类 22 个方法全部无法追流转（BPM 实现在服务端）\n"
     "- 「流转」列只给第一步，完整链路看 flow 文件",
     "- 53 个 AppService 仍未找到实现类 → 流转 UNVERIFIED\n"
     "- 「流转」列只给第一步，完整链路看 flow 文件\n"
     "- 实现是**反编译**不是源码（仓库无 sources jar），注释和局部变量名已丢失"),
    ("docs/audit/artifacts/extension-surface-20261029/action-index.md   101 KB\n"
     "  覆盖现实 → 动作分布 → 八类动作逐条 → 查询类按接口聚合 → 用法 → 缺口\n\n"
     "生成器 tools/core/platform/emit_action_index.py\n"
     "  数据源 interfaces.json + service-flow-20261103/*.md\n"
     "  闸门：能追流转的方法 < 100 则 WARN（flow 解析可能失效）",
     "docs/audit/artifacts/extension-surface-20261029/\n"
     "  action-index.md   124 KB（覆盖现实 → 动作分布 → 八类动作逐条 → 查询类聚合 → 用法 → 缺口）\n"
     "  impl-map.json      51 KB（269 个接口 → 实现类，读字节码 implements 子句）\n\n"
     "实现 jar：<MAVEN_REPO>-extra/（21 个 *-biz / 40 MB / 15869 类）\n"
     "  来源 http://10.0.0.1/artifactory/libs-release/com/seeyon（只读 GET）\n\n"
     "生成器\n"
     "  tools/core/platform/fetch_biz_jars.py      下实现 jar\n"
     "  tools/core/platform/build_impl_map.py      扫 implements 关系（命名不规则，必须读字节码）\n"
     "  tools/core/platform/emit_action_index.py   --impl-map 合并两路映射\n"
     "  闸门：能追流转的方法 < 100 则 WARN"),
    ("| 254 个 AppService「实现在平台服务端」 | **推断**（仓库 jar 里无实现类），未逐一核实服务端 |\n"
     "| 流程类方法的实际行为 | **UNVERIFIED**（无实现可反编译） |",
     "| 269 个接口 → 实现类映射 | `VERIFIED_STATIC_BYTECODE`（javap 读 implements） |\n"
     "| 1884 个方法的流转第一步 | `VERIFIED_STATIC_BYTECODE`（反编译方法体） |\n"
     "| 53 个接口仍无实现 | **推断**（21 个 biz jar 里都没有），未核实是否在其他构件 |"),
]

REPS_FLOW = [
    ("| `datamigration…-biz.md` | 客户应用「数据迁移」27 个 | 164 KB | Service 901 |",
     "| `datamigration…-biz.md` | 客户应用「数据迁移」27 个 | 164 KB | Service 901 |\n"
     "| `bpm-biz-appservice.md` | **BPM 门面 52 类** | 143 KB | Dao 21 / Service 628 / Util 394 / Event 4 |\n"
     "| `organization-biz-appservice.md` | **组织 53 类** | 326 KB | Dao 678 / Service 2253 / Util 887 / Event 4 |\n"
     "| `cip-capability-biz-appservice.md` | 连接器能力 132 类 | 323 KB | Dao 128 / Service 2936 / Util 1985 / Event 24 |\n"
     "| `cip-connector-biz-appservice.md` | 连接器 97 类 | 180 KB | Dao 14 / Service 1146 / Util 1024 / Event 41 |\n"
     "| `ctp-user-biz-appservice.md` | 人员 50 类 | 74 KB | Dao 15 / Service 346 / Util 214 |\n"
     "| `cdp-data-biz-appservice.md` | 数据平台 55 类 | 82 KB | Dao 11 / Service 43 / Util 93 |\n"
     "| `ctp-affair-biz-appservice.md` | 事项 10 类 | 21 KB | Dao 1 / Service 90 / Util 35 |\n"
     "| `app-common-biz-appservice.md` 等 | 应用通用等 5 个 | 41 KB | — |"),
    ("```\ndocs/audit/artifacts/service-flow-20261103/\n  udc-biz-appservice.md   151 KB / 83 类\n  udc-biz-domain.md       646 KB / 265 类\n  znxmglpt…-biz.md        2.4 MB / 458 类\n  xiangmuguanli…-biz.md   719 KB / 130 类\n  datamigration…-biz.md   164 KB / 27 类\n\n生成器 tools/core/platform/emit_service_flow.py\n  --pkg <构件> [--only-impl | --paths <路径片段...>] [--suffix=-xxx]\n  闸门：抽到的类 < 5 则 exit 5",
     "```\ndocs/audit/artifacts/service-flow-20261103/   16 份 / 5.2 MB\n  平台实现（<MAVEN_REPO>-extra，21 个 *-biz jar）\n    bpm-biz-appservice.md            143 KB / 52 类\n    organization-biz-appservice.md   326 KB / 53 类\n    cip-capability-biz-appservice.md 323 KB / 132 类\n    cip-connector-biz-appservice.md  180 KB / 97 类\n    ctp-user-biz / cdp-data-biz / ctp-affair-biz / ctp-message-biz / cip-manager-biz …\n  UDC（<MAVEN_REPO>）\n    udc-biz-appservice.md  151 KB / 83 类（门面层）\n    udc-biz-domain.md      647 KB / 265 类（业务层）\n  客户应用\n    znxmglpt…-biz.md       2.4 MB / 458 类\n    xiangmuguanli…-biz.md  720 KB / 130 类\n    datamigration…-biz.md  165 KB / 27 类\n\n实现 jar 来源 http://10.0.0.1/artifactory/libs-release/com/seeyon（只读 GET，21 个 *-biz，40 MB）\n⚠️ 仓库无 -sources.jar，是反编译 class 不是读源码\n\n生成器 tools/core/platform/emit_service_flow.py\n  --repo <仓库根> --pkg <构件...> [--only-impl | --paths <路径片段...>] [--suffix=-xxx]\n  闸门：单个构件抽到的类 < 5 则跳过（不中断整批）"),
]


def apply(path: Path, reps: list[tuple[str, str]]) -> None:
    t = path.read_text(encoding="utf-8")
    hit = 0
    for old, new in reps:
        if old in t:
            t = t.replace(old, new)
            hit += 1
        else:
            print(f"  WARN {path.name}: 未匹配 → {old[:50]}…")
    path.write_text(t, encoding="utf-8")
    print(f"  {path.name}: {hit}/{len(reps)} 处替换")


def main() -> int:
    apply(FD / "business-action-index.md", REPS_ACTION)
    apply(FD / "service-business-flow.md", REPS_FLOW)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
