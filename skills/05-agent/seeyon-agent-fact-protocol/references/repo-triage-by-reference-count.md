# 仓库分层与清理：怎么决定「留 / 进 pending / 进 trash」

适用：一个大仓库里累积了几百个一次性脚本、几百 MB 证据，需要在不删任何东西的前提下先分层。
核心原则：**判定靠引用计数与可重建性，不靠文件名或印象。**

## 一、先量体积，再谈取舍

```bash
du -sh */ | sort -rh | head -25        # 根级谁大
du -sh docs/*/ | sort -rh              # 再往下钻一层
du -sh docs/audit/artifacts/*/ | sort -rh | head -18
```

经验形态：体积几乎总集中在 1~2 个目录（证据/反编译产物），而**噪音（脚本数）** 集中在
`tools/`。两者要分开决策：体积大的不一定能删，数量多的不一定占地方。

## 二、引用计数：唯一可信的「可否移动」判据

按文件名（不含 `.py`）在整仓搜：

```bash
for f in tools/core/*.py; do b=$(basename "$f" .py)
  if grep -rq "$b" tests/ docs/ components/ core/ --include=*.py --include=*.md; then
    echo "REF   $b"
  else echo "UNREF $b"; fi
done
```

### ★ 判据必须分三档，不能「docs 命中就算引用」

一次实测：按 `tests/ docs/ components/ core/` 一把搜，11 个「有引用」里有 7 个
只被 `docs/audit/` 下的历史证据文档点名；而那几份文档本身又在 `.gitignore` 里。
结论：这些脚本**没有活消费者**，留着就是一次性脚本占着可复用目录。

```
REF_LIVE   被 tests/ · components/ · core/ · docs/operation-contracts/
           · docs/capability/ · docs/construction-rules/ 引用   → 留 tools/core/_misc/
REF_EVID   仅被 docs/audit/ 引用（历史证据点名的「当时用它跑过」） → 进 pending
ZERO       零引用                                                → 进 pending
```

**为何 REF_EVID 不进 tools/core**：它证明的是「当时拿它跑过」，不是「现在有人用它」。
进 pending 同样保留了证据可复现性（文档里的命令仍然能找到该文件），且不会被当成能力。

### 陷阱 1：自引用会把「引用」算成真的

`tools/audit/b5_scan7.py` 搜 `b5_scan7` 会命中：

- `docs/audit/udc-semantics/*.md` 里的**运行命令**（真引用）
- 但也会命中 **另一个脚本**或该目录 README 的清单（伪引用）

⇒ 命中后要**打开看那一行是什么**。真引用 = 文档指着它跑 / 测试 assert 它的路径 /
代码 import 它。伪引用 = 只在某个清单里被列名字。

### 陷阱 2：名字太通用的会满屏假阳

`dump_six` / `pick6` / `detail_gen` / `a_cols` 这种名字，grep 会命中无关文本。
判据改为搜**文件名带扩展名**（`dump_six.py`）或直接搜 `tools/core/dump_six`。

## 三、体积维度：大文件单独判，不跟脚本一起判

```bash
find docs/audit/artifacts -type f -size +5M -exec ls -lh {} \; | awk '{print $5, $9}'
```

对每个大文件单独 grep 文件名（不带目录）：

```bash
for n in r33_corpus r34_msg_rows mf_all r33_s4; do
  echo -n "$n: "
  grep -rl "$n" docs/ core/ components/ tests/ 2>/dev/null | grep -v "artifacts/scratch" | head -3 | tr '\n' ' '
  echo
done
```

**零命中的大 JSON 是 pending 的首选**：它们含已取证事实（某次跑批的完整输出），
删了就没法复盘；但当前没有消费者，不该占着架构目录。这正是「pending ≠ trash」的由来。

## 四、git 跟踪面：决定「移走」还是「只需忽略」

```bash
git ls-files <dir> | wc -l        # 已跟踪 → 移动是 git mv，有历史可捞
git check-ignore -v <path>       # 已忽略 → 移动只影响工作区
```

| 状态 | 处理 |
|---|---|
| 已跟踪 + 零引用 | `git mv` 进桶（历史保留在旧路径，能 `git log --follow`） |
| 已跟踪 + 有引用 | 原地不动，或先改引用再移 |
| 已忽略 + 零引用 | 直接移进桶即可 |
| 已忽略 + 有引用 | **危险**：别人 clean 环境就是坏的，见下节 |

## 五、分层必须跑全量测试——它会抓出你以为没引用的东西

实测：把根目录 `http.json` 当垃圾移走后，
`tests/test_acceptance_boundaries.py` 直接 `FileNotFoundError`。

机理：那个文件在 `.gitignore` 里（运行产物），测试却读仓根那份 →
**本机跑过才有，新克隆必然失败**。这不是「我删错了」，而是那条测试本来就是缺陷。

修法永远是「测试自建到 `tmp_path`」，不是「把文件放回去」。

```bash
pytest tests -q --tb=line      # 只在移动后跑，不要 --tb=no（要看到真实栈顶行）
```

按失败清单分类：

```
A 路径断言失败      → 改测试里的路径
B 缺文件            → 先判「这文件该不该被依赖」，再决定补 fixture 还是改测试
C 逻辑回归          → 说明移动真的改坏了东西，回退
```

## 六、两个桶的台账格式

每条一行，缺列就不合格：

| # | 内容 | 体积 | 零引用验证 | 状态 | 去向 |
|---|---|---|---|---|---|
| P1 | `xxx/root/` 大 JSON | 132M | 逐个 grep 零命中 | PENDING | 待抽离：<哪个域的事实> |

状态只有三种：`PENDING`（未抽离）/ `EXTRACTED`（已抽成正式资产，注明去向）/ `KEEP`（复查后其实有引用）。

**「整目录搬走」不算处理完。** 台账必须逐条关闭，否则下次没人知道里面还剩什么。

## 七、清理节奏（不要一次做完）

```
第一轮   分层：建两桶 + 移零引用项 + 补 .gitignore + 跑全量
第二轮   抽离：做功能时先来 pending 捞，抽完改台账状态
最终     待全部 EXTRACTED/KEEP 后，pending 与 trash 一起删
```

⚠ 用户明确要求过：**领域（UDC 等）全部完工前，pending 桶不删**。
理由：里面的证据是后续做功能的原料，删早了等于丢原料。
