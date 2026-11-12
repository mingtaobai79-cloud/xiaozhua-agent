# 沉淀归位规则（xiaozhua Agent）

> **核心要求**（用户 2026-10-20）：
> 「记住你写的这些东西必须都进 xiaozhua agent，保证后续我只要一个需求你能里面实现功能」
>
> 即：能力不能只活在 Hermes 的 skill、我的临时脚本、或者对话上下文里，
> 必须落在 `xiaozhua-agent` 仓库内，**可被发现、可执行、可复用**。

## 一、判定标准：什么算「必须进仓库」

| 产出 | 去处 | 判定 |
|---|---|---|
| 平台行为的结论、约束、错误字典 | `core/facts/udc/<域>/` | **必须** |
| 可执行的校验器 / 构造器 / 分析器 | `components/udc/<域>/` | **必须** |
| 可调用的 operation 契约 | `components/platform_operations/registry.py` | **必须** |
| 抓包/反编译/DB 原始证据 | `docs/audit/artifacts/` | **必须**（仓外客户证据除外） |
| 一次性取证脚本 | `tools/one-off/` | 归档，不维护 |
| 可复用工具 | `tools/core/<域>/` | **必须** |
| 使用方法与坑 | `skills/xiaozhua-udc-<域>-<子模块>/SKILL.md` | **必须** |
| 只在对话里的中间结论 | —— | **不合格**，必须落盘 |

## 二、四个必须成对存在的东西

任何模块推进完一轮，这四类必须同时存在且**互相引用**：

```
实现   components/udc/<域>/<子模块>_*.py
事实   core/facts/udc/<域>/<子模块>/create.md + <子模块>-write-chain.md
契约   docs/operation-contracts/udc/<域>/<子模块>-contracts.md
skill  skills/xiaozhua-udc-<域>-<子模块>/SKILL.md
```

缺一类 = 模块没沉淀完。`tools/core/capability_report.py --check` 会报出缺口。

## 三、进来一个新需求时的标准流程

```
1. 跑能力自检，定位域与已有能力
     python tools/core/capability_report.py
     （输出：九域各自的 实现/事实/契约/脚本 落位 + 缺口 + 仓库内 skill 清单）

2. 读该域的事实格与契约
     core/facts/udc/<域>/<子模块>/create.md      ← 能力现状与等级
     core/facts/udc/<域>/<子模块>/*-write-chain.md ← 请求体/错误字典/踩坑
     docs/operation-contracts/udc/<域>/<子模块>-contracts.md

3. 判断：能复用还是要新建
     能复用 → 用现成构造器 + 校验器，直接走
     要新建 → 按四类资产补齐，落位规范见
              skills/xiaozhua-udc-module-landing/SKILL.md

4. 写完做三件事
     a) 事实格更新（新增能力 + 等级；作废的旧说法显式声明）
     b) 落位测试（tests/udc/test_<域>_<子模块>_asset_layout.py）
     c) 能力自检 --check 无缺口

5. 脱敏闸门必须过
     pytest tests/test_deidentification.py
```

## 四、事实必须分级，不许混着说

`create.md` 的 R-E9 段逐项标注：

| 等级 | 含义 |
|---|---|
| `LIVE PASS` | 跑通 + 独立回读核实 |
| `LIVE` | 跑通但回读维度有限 |
| `VERIFIED_STATIC_BYTECODE` | 静态证据坐实，未跑 |
| `UNVERIFIED` | **真实不可用/未验证**（写明缺口） |
| `VACUUM` | **真实不存在**（完备负证据） |

| 「待删除」单独小节，`DONE` 必须有回读证据，`PENDING` 明确依赖关系。

## 四之二、证据必须可复现：R-E8 写三样

事实格的 `R-E8 Evidence` 段，**每条证据必须写全三样**，缺一不算完成：

```
① 路径    docs/audit/artifacts/<来源>/<版本>/xxx.json     ← 相对仓根
② 复现    命令或步骤（哪个脚本 / 页面怎么点 / 哪条 SQL）
③ 校验    你怎么知道它对（DB 回读哪张表哪列 / 接口回读哪个字段）
```

反例（2026-10-22 复核发现的现状）：

```
❌ 「枚举：id -1052013552430069963，ctp_enum.category_id 正确指向分组」
   → 三个月后没人知道这个 id 哪来的、怎么重跑
✅ 「枚举 id=…；证据 docs/audit/artifacts/udc-web-5.3.517/…json；
   复现 tools/core/setting/enum_seed.py --app-id X；
   校验 SELECT category_id FROM ctp_enum WHERE id=…」
```

**只有 id、没有路径与复现方法的证据行，不算沉淀。** 详见
Hermes skill `xiaozhua-agent-fact-protocol`（§三）。

## 五、仓库与外部的边界

```
仓库内   实现 / 事实 / 契约 / skill / 工具 / 脱敏后的证据
仓库外   客户明细、真实 golden 样本、凭据文件
         → <EVIDENCE_ROOT>/xiaozhua-customer-evidence（config/environments.yaml 记路径）
         → 凭据只从环境变量或仓外文件读，永不入库
```

黄金样本这类"客户真值"是**运行时事实**（`golden_application_id()` 从仓外解析），
不是仓库内常量。改仓库内常量会让两侧不一致 —— 这个坑已经踩过。

## 六、自检工具

```bash
# 能力清单（九域落位 + 契约数 + 仓库内 skill）
python tools/core/_meta/capability_report.py
python tools/core/_meta/capability_report.py --json
python tools/core/_meta/capability_report.py --check    # 退出码非 0 = 有缺口

# 脱敏扫描（结论区 vs 证据区）
python tools/core/audit/scan_pii.py
python tools/core/audit/plan_deident.py

# 事实格/契约同步
python tools/core/audit/sync_test_counts.py
```

## 七、当前状态（2026-10-20）

```
契约      88 条（写面 14 条）
域落位    设置 ✅ 完整 / 实体 ✅ 完整
          应用 ○ 有契约无事实格
          菜单 规则 流程 BI 栏目 角色 ⚠ 缺事实格
skill     15 个已入仓
```

缺口按域推进顺序补：设置（枚举 ✅ → 自定义对象）→ 应用 → 实体 → 规则 → 菜单 → …
