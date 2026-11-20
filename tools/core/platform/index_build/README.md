# 索引构建流水线

从接口字节码索引（`docs/audit/artifacts/extension-surface-full/interfaces-full.json`）
生成可查询的分片索引（`docs/audit/artifacts/index/`）。

## 一条命令重建

```bash
cd C:/Users/白明涛/xiaozhua-agent
python tools/core/platform/index_build/build_priority.py   # 权威类排序（解决 787 组重名）
python tools/core/platform/index_build/split_all.py        # by-domain 16 + by-starter 79
python tools/core/platform/index_build/split_apps.py       # by-app 115
python tools/core/platform/index_build/split_sub.py        # by-sub 185
python tools/core/platform/index_build/rebuild_tree.py     # TREE.md / INDEX.md
python tools/core/platform/index_build/verify_index.py     # 自证，退出码必须 0
```

## 顺序不能乱

```
build_priority  →  split_*  →  rebuild_tree  →  verify
   （独立）        （读全量源）   （读分片结果）   （校验总数）
```

`split_apps.py` 依赖 `apps.json`（115 应用 → 构件映射）。若丢失，
从 `core/facts/modules/` 的目录结构重建：每个应用目录名 + 其 README 里的构件清单。

## 分片口径

| 目录 | 数量 | 合计类数 | 切分依据 |
|---|---:|---:|---|
| `by-domain/` | 16 | 24,618（= 源） | `com.seeyon.{X}` 第二段，含 `com.seeyon.MyMojo` 这种三段类名 |
| `by-sub/` | 185 | 19,681（= 9 大域） | `com.seeyon.{X}.{Y}`，只切 cip/bpm/udc/cdp/ctp/app/organization/portal/m5 |
| `by-starter/` | 79 | 3,678（= boot.starter 全部） | `com.seeyon.boot.starter.{Y}` |
| `by-app/` | 115 | 24,618（= 源） | 类的 `pkg` 字段（构件名）落在该应用的 `artifacts` 里 |

**为什么 boot 不在 by-sub 里再切一遍**：boot 的内部结构就是 starter，
`by-starter/` 已经是它的二级切分，重复切会产生两份同内容文件。

## 两个真实坑

### 坑 1：`com.seeyon.MyMojo` 是三段类名，不是包

第一版用 `fq.startswith("com.seeyon.{dom}.")` 判断归属，这个类名后面没有点，
于是它被漏掉 → 域合计 24,617 ≠ 源 24,618，**被断言抓住**。

同理 `com.seeyon.boot.starter.DataFlowRuntimeAutoConfiguration` 也是类名本身。

**修法**：用 `dom_of(fq)` / `st_of(fq)` 按段数取值，不用前缀匹配。

### 坑 2：`sources` 里没有 `class_list`

`sources[pkg]` 只有 `{jar, file, classes, total_methods}`，没有类清单。
想按构件分组，**必须读每个类的 `pkg` 字段**，不能从 `sources` 反推。

第一版从 `sources` 反推 → 115 个应用全部 0 类，被自证抓住。

## 空分片

3 个应用分片为 0 类，原因是 jar 内没有 `com.seeyon.*` 类：
`bpm-ext-models` / `jakarta.persistence` / `mobile-message-client`。
`TREE.md` 里已标 ⚠️，`verify_index.py` 用白名单校验，
防止将来真有遗漏时被这条规则掩盖。

## 现在给 Agent 用的入口

```bash
python tools/core/platform/query_platform.py scopes
```