# 仓库事故记录 REPO-INCIDENT-20261018

> 本文件记录 2026-10-18 发生在 `<SEEYON_AGENT_ROOT>` 的两起误入库事故，
> 目的是让后续 `git log` 到相关 commit 的人**不误判仓库状态**。
> 禁止删除本文件；处置变化时在本文件末尾追加，不改前文。

---

## 事故 1：`25ccf75` —— `git add -A` 把 2,221 个文件卷进一个 docs commit

### 事实
```
commit   25ccf75  2026-10-18 14:39:01
标题     docs(udc): 总览索引补 D50/D51 —— 26 条与 DECISIONS 标题数一致
预期     1 file changed
实际     2221 files changed, 684,780 insertions(+), 85 deletions(-)
         其中 A=2213（新增）/ M=8（修改）
仓库文件数  25ccf75~1 = 6,902  →  25ccf75 = 9,115  （+2,213）
```

### 根因
执行了 `git add "$f" && git add -A`。后半句是为"怕文件没加进去"加的兜底，
而 `git status --porcelain <file>` 输出为空实际表示**已 staged 且与 HEAD 无差异**，不是"没加进去"。

### 波及内容
```
（浏览器 profile，2026-10-20 已清理）        1,230
docs/audit/artifacts/scratch-migrated/ctpenum-fix       157
（浏览器 profile，2026-10-20 已清理）-b3       148
（浏览器 profile，2026-10-20 已清理）-b3b      131
docs/audit                105
docs/audit/artifacts/decompiled/audit-slice-b2     73
docs/audit/artifacts/scratch-migrated/cfr-sbx            55
docs/audit/artifacts/scratch-migrated/audit-slice-b1     40
node_modules/ws            20   ← 用户随后用 d2ff36b 清掉
```

### 影响边界（必须分清，否则会误判）
```
① 「读当前 HEAD」安全 —— 内容损失为 0，文件本来就在工作区
② 「checkout 历史版本」不安全 —— 若在 25ccf75 之后、d2ff36b 之前 checkout，
   会得到含 node_modules/ws 的工作区（20 个文件，无 package.json 的悬空依赖）
③ 历史可读性受损 —— 一个标题写"补两行索引"的 commit 实际改 68 万行，
   任何人 git log --stat 看到都会误判
```
**⇒ 结论：不要 checkout `25ccf75` ~ `d2ff36b^` 之间的任何版本用于交付或分发。**

### 未修
历史未改写（禁止 push，污染限于本机）。`25ccf75` 本身的树内容是"当时工作区快照"，
不含恶意改动，但**不能当作一次干净的 docs 提交引用**。

---

## 事故 2：浏览器凭据库被跟踪（`25ccf75` 引入，`aaf1cde` 才移出）

### 事实
```
25ccf75~1 凭据类文件  → 0
25ccf75                → 14
HEAD (aaf1cde 之前)    → 14
HEAD (aaf1cde 之后)    → 0
```
14 个文件（`（浏览器 profile，2026-10-20 已清理）` / `-b3` / `-b3b` 三个 profile）：
```
Default/History          3,268,608 B（edge-cdp、b3 各一，b3b 282,624 B）
Default/Login Data         200,704 B / 206,848 B / 51,200 B
Default/Network/Cookies     32,768 B × 3
Default/Web Data           874,496 B / 874,496 B / 229,376 B
Default/Preferences         32,943 B（仅 edge-cdp）
Local State                 31,332 B（仅 edge-cdp）
```

### 风险
```
① 当前无 remote（git remote -v = 0 条）⇒ 未外泄
② 但 Cookies / Login Data / Local State 是浏览器凭据库本体，
   且这份 profile 正是 test2 CDP 登录态所用的那份
③ 一旦将来 push / 打包分发 / 仓库被复制 ⇒ 等同把测试环境凭据库带出去
```

### 已处置（`aaf1cde`，15:02:23）
```
git rm --cached（不删工作区）14 个文件
.gitignore 增凭据类规则（精确 + 通配兜底）
tracked 体积 735.1 MB → 726.1 MB（−9.0 MB）
工作区文件全部保留（未删任何实际数据）
```

### 未处置 —— 历史里仍可检出（重要）
```
git show 25ccf75:"docs/audit/artifacts/scratch-migrated/edge-cdp/Local State" | wc -c  → 31,332   （仍可取）
git show 4029179:"docs/audit/artifacts/scratch-migrated/edge-cdp/Local State" | wc -c  → 31,332   （仍可取）
.git 体积 456 MB（这些 blob 仍占用）
```
⇒ **`25ccf75` ~ `4029179` 区间内任何人 checkout 都能取到完整凭据库。**
**按"已泄露"对待**：不 push、不打包、不复制本仓库到不受控位置。

**若要彻底清除**：`git filter-repo` 改写历史 ⇒ 所有 commit hash 变更（含他组的 `53567f5` / `d2ff36b`），
协作会话的全部锁点失效。**未做，需仓库所有者裁决。**

---

## 与 `.gitignore` 既有口径的关系（避免下一个人以为口径打架）

`.gitignore` L46-47（`d2ff36b`，operator-a本人写）：
```
# scratch：过程产物。既有 6880 个已跟踪文件保留（其中 67 个被 docs/core/aud 引用为证据路径），
#   仅阻止新增；不做批量 rm --cached（避免打断契约可复现性）
```

**本文件事故 2 的处置与此不冲突**，理由：
```
那条防的是"打断契约可复现性"；
而移出的 14 个凭据文件，被 docs/core/aud/tools 引用数 = 0（逐个 grep -rlF 核实）。
1,509 个 （浏览器 profile，2026-10-20 已清理）* 文件中，1,495 个非凭据类全部保留。
```
**⇒ 未来的正确做法：不要按目录整批 `rm --cached`；只对"无引用且属私密数据"的单个文件处理。**

---

## 给后续接手者的一句
```
git log --stat 看到 25ccf75 的 2221 files / 684,780 insertions 时：
  先读本文件，再判断。它不是一次正常的 docs 提交。
```
