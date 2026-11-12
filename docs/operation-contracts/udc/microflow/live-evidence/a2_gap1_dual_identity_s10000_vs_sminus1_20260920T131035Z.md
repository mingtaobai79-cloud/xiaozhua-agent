# s=-1 复测 A2 缺口①（人指 20:53 第一动作，双身份对照证据）
# 时间：20260920T131035Z（21:10:35 北京），token s=-1 窗内（TK_EXP=1789914674=22:31:14 北京，left_s 实测 5074 @ 13:06Z）
# 判据（人指）：s=-1 复测缺口①——业务对象可见 → A2 LIVE PASS；仍 BOOT_3000 全空 → 缺口①升级为身份数据范围/权限，记双身份对照。
# 原生件：s_minus1_C1_node_tree_f1/f2_20260920T131035Z.json（本目录，GAPS-1 标准可重算）

## 缺口①复测结果（s=-1 身份，宿主应用 = <appId 字面·脱敏>（宿主标识，非凭据；权威口径以 a6 脱敏版为准））
| 端点 | HTTP | 业务 | data | 判读 |
|---|---|---|---|---|
| /service/udc/application/{APP} | 200 | BOOT_3000 st=3 | None | 业务对象不可见 |
| /service/udc/entity/select-by-appid/tree/{APP} | 200 | BOOT_3000 st=3 | None | 业务对象不可见 |
| /service/udc/entity/select-all-by-entityId/{APP} | 200 | BOOT_3000 st=3 | None | 业务对象不可见 |
| /service/udc/entity/primary/select-root/1 | 200 | UDC_ENTITY_0007 st=2 | None | 业务未找到 |

**s=-1 下 entity/application 族仍全 BOOT_3000 空，与上轮 s=10000 结果完全一致。**
→ 缺口①升级归因：**非 s=10000 单身份数据范围问题，而是该 UDC 只读身份体系（s=10000 / s=-1 双身份对照）对 znxmglpt 宿主应用的 entity/application 业务数据均无可见范围（BOOT_3000 status=3 = 身份数据权限边界）**。
  双身份对照证据：s=10000 轮（R20b a2_live_readback_R20b_20260920T103050Z.md，BOOT_3000 全空）+ s=-1 轮（本件，BOOT_3000 全空）→ 一致 → 身份数据范围/权限问题，非 token 值问题。

## C1 跨身份稳定性确认（A2 LIVE PASS 不受影响）
C1 /service/udc/udc-runtime/meta-data/select-function-node-tree/{APP}（C1 族，A2 已达 LIVE PASS 的 target）在 s=-1 下：
- f1/f2 均 200 BOOT_0000 status=0；去 traceId 归一化 normalized_sha f1=f2=**26ceca1edc115505**（与 s=10000 轮 R21 a2_live_pass 同值）→ **identity_matches=TRUE**；
- data.content = 函数节点树 **23 节点（非空业务对象）**，首节点 id=23088985804278345（双发一致）。
→ **C1 族（菜单/函数节点读面）跨身份 s=10000 / s=-1 均稳定可读（同 sha、同 23 节点），A2 LIVE PASS 结论不因身份切换而变；缺口的仅 entity/application 业务数据面（BOOT_3000 身份数据权限边界，已升级归因，非 A2 达成必需——A2 判据 = ≥1 条 test2 LIVE PASS，C1 已满足）。**

## 结论
- A2 缺口①（entity/application 业务数据可见性）= **身份数据范围/权限问题（双身份对照证据在案）**，与 token 值/身份枚 s 值无关；test2 UDC 只读身份对 znxmglpt 宿主应用 entity/application 数据无可见范围（BOOT_3000）。
- 缺口②（404 未部署）已 P1 部署态 jar 取证解阻（R21）：udc-runtime 前缀漏段非未部署，C1 带段即 200 命中。
- A2 = LIVE PASS 维持（C1 族双发 identity_matches=TRUE + 非空 23 节点，跨身份稳定）；entity/application 业务数据面 = UNVERIFIED（身份数据权限边界，双身份对照证据已登记）。

## 红线
全程只读 GET；token 明文零落盘（仅脱敏前8）；原生 f1/f2 JSON 随证落盘（s_minus1_*）；未写/发布/部署/DB/Redis；冻结件（R20/R20b/R21 VERDICT + P1 三件 + A2 重探 3 件 + a6 报告）字节未动。
