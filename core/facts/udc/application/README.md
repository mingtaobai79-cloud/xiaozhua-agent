# core/facts/udc/application/ 索引

## 这个目录是什么

**UDC 应用域事实层**：这个域实际怎么读写、哪些操作真跑过。7 份 md / 77,959 B + 17 份证据 JSON。

★ **与应用域契约层的分工**——这是本域最容易走错的一步：

| 层 | 目录 | 回答 |
|---|---|---|
| **事实层（本目录）** | `core/facts/udc/application/` | 这个域**实际长什么样、哪些真跑通过**（含 LIVE 实测、抓包形状、踩坑） |
| 契约层 | `docs/operation-contracts/udc/application/` | **端点 / 必填 / 报错**的接口约定 |

## 一、7 份一览（2026-11-07 实测）

| 文件 | 字节 | 行 | 性质 | 证据等级 |
|---|---:|---:|---|---|
| `applog-family.md` | 22,362 | 180 | 九段式事实格 · S4：applog 全族 8 条 operation_id | 静态 + 离线 LIVE 记录（09-18 窗口**已过期**） |
| `application-search.md` | 20,056 | 170 | 九段式事实格 · S3：非草稿面 get / search×2 | LIVE 已 PASS（`app-search-live-20260926.md`） |
| `app-inner-pages.md` | 12,576 | 186 | 应用内功能页接口地图（左侧菜单 / 底部日志） | **LIVE**：点击录制 + cookie 重放实测回包 |
| `app-frontend-callsurface.md` | 6,149 | 98 | 前端真的怎么调（19 条 verb+path） | **LIVE**：设计器已加载 chunk 提取 |
| `app-inner/app-inner-write-chain.md` | 5,761 | 99 | 写链与踩坑（依赖设置 + 沙箱构建） | **LIVE**（2026-10-22 test2） |
| `app-inner/create.md` | 5,380 | 78 | 应用内功能页事实格（摘要，指向写链详版） | **LIVE** |
| `evidence/app-search-live-20260926.md` | 5,675 | 62 | 探测量（非事实格）：search 两端点只读补测 | LIVE 只读，`write=False` |
| **合计** | **77,959** | **873** | | |

另有 17 份证据 JSON（136,955 B）+ `app-inner/`、`evidence/` 两个子目录。

## 二、读的顺序（跟着证据链走）

```
① 想调一个应用域接口？
   application-search.md（get / search 两条，含入参响应逐字段）
   applog-family.md      （日志族 8 条）

② 想在「应用设计器」页面里操作（不是调接口，是点页面）？
   app-inner-pages.md    （子路由表 / 每页触发哪些请求 / 抓法三层）
        ↓ 要动写面（依赖增删、构建、部署）
   app-inner/create.md   （事实格摘要，带状态列：LIVE / OBSERVED）
        ↓ 要真实请求体与踩坑
   app-inner/app-inner-write-chain.md  （写链 6 步逐条 + 真实抓包字段名）

③ 想知道前端到底调了什么（不看后端签名，看 JS 里写的路径）
   app-frontend-callsurface.md  （19 条 verb + path + 出处 chunk）
```

## 三、三条「这目录会骗人」的地方

### ① 「LIVE」有三种含义，不是一种

- `LIVE PASS` —— 真跑通，看过回包（如 `create.md` 的沙箱就绪态 `state=RUNNING`）
- `OBSERVED` —— **只看见页面自己发过，没主动触发过**（`create.md` 的一致性检测、构建部署）
- 离线窗口**已过期** —— `applog-family.md` 引用的 09-18 窗口记录，**现在重放不了**

**看到 `OBSERVED` 不要当"已验证可用"。**

### ② `applog-family.md` 只有 2 条有 LIVE 记录，6 条是 404 负证据

它的基线写着：registry 6 条契约 + 在盘 LIVE 记录 **2 条** + 微流程负证据 **6 件（均为 404）**。
**404 也是结论**——它证明了"这些端点在这个版本上不存在"，但**不能推出"该功能不存在"**。

### ③ `evidence/app-search-live-20260926.md` 里的 `main/`、`implementer/` 路径指向**会话目录，不在仓库**

那 4 处路径（`main/S1P-PROBE-HANDOFF.md`、`implementer/probe_app_search_live.py`、
`S1P-PROBE.out.json`、`S1P-PROBE.err.txt`）**全库 grep 不到**，且文档自己写明
「会话目录；仓库零改动」。**它们不是死引用，也不要"修"成仓库内路径**——
那是当时那个会话的临时目录，修成仓内路径会编造一个不存在的文件。
正确读法：**该探针的规格与原始 stdout 没有入库**，只有本文件记录的结论部分可引用。

## 四、拿不到什么

- **`applog` 写端点**：只注记、不入格、不计数（原格明确写的边界）。
- **`draft` 两条**：归 S2，本目录不重复。
- **`create.md` 的 `OBSERVED` 项**：构建+部署只看见页面发过，**没有自己跑过一遍**。
- **跨版本**：全部基于 `udc-web` 5.3.517 / test2。换版本要重测，不能线性外推。

## 五、不要做的事

- **不要**手改事实格里的 `LIVE`/`OBSERVED` 状态：那是证据等级，不是主观评价。
- **不要**把 `main/`、`implementer/` 那 4 处路径"修"成仓库内路径（见 §三③）。
- **不要**在本目录写端点必填/报错约定——那是 `docs/operation-contracts/udc/application/` 的活。
- **不要**只读 `app-inner/create.md`：它只是摘要，写面细节在 `app-inner/app-inner-write-chain.md`。

---

维护：新增/删除任何一份都必须同步 §一 表的份数、字节、行数与合计
（`tests/udc/test_application_facts_layout.py` 会核对）。
