---
name: seeyon-external-api-testing
description: "致远低代码应用对外接口联调测试：四轮测试法、字段裸ID转化缺陷定位、DB取证换样本、UDC元数据与物理列配对修复。"
version: 0.2.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [2小爪, UDC, API-Testing, MySQL, Live-Testing]
---

# 2小爪 外部接口联调测试

Use when 用户要求测试致远低代码应用对外暴露的接口（如 `XmglApiController` 的 ESB/开放接口）、排查接口字段缺值/返回裸ID、或验证接口修复效果。环境连接材料见 `seeyon-low-code-environment` skill（本 skill 只管测试方法学，不管凭据）。

参考文件：`references/interface-live-test-triage.md`（对外接口实测分类与定位）、`references/udc-write-chain-and-runtime-errors.md`（写链路主键冲突/提交报错取证、前端运行时错误判定、库内清理写操作）。

## 核心原则

- **HTTP 200 + code=S ≠ 数据质量通过**。必须逐字段审计 null / 空串 / 裸ID（正则 `^-?\d{8,}$` 扫描）。
- **先读 Controller 源码再下结论**：定位数据源子表、组装路径、硬编码查询条件；值异常先查转化链，不臆测字段映射。
- 结论三分法：代码缺陷 / 样本无数据(UNVERIFIED) / 接口设计限制（与产品确认，不是 bug）。
- **修复边界：只修"崩溃与参数错"，不改"业务分流与取值来源"**（用户明确且反复要求）。可改：空指针/越界/`.getContent()` 未判空、类型转换崩溃（`NumberFormatException`）、查询条件键用错、入参被忽略这类**能被运行时证伪**的失败。不可自行改：业务分流逻辑（如 `business_id` 非空→查产品服务行、为空→查内部/非内部结算子表）、字段取值来源（枚举取 `itemValue` 还是 `enumCode`、ID 该用合同号还是档案主键）、字段转换的目标类型。这些属于**设计事实**，改前必须先向用户说明理由并取得确认。"看着不对"不等于运行时会崩。
- **一次只改有证据的失败点**：把顺手发现的同类"嫌疑点"列成待确认清单交用户挑，不要顺手一起改掉（改多了会掩盖真正的根因，也会把用户的业务逻辑搞乱，重测成本全部由他承担）。是否要批量扫同类点，先问一句再动。
- **汇报"还剩几个"先给数字再给明细**：用户问"还剩几个接口/还有几个问题"时，第一行就是计数结论（总项数 vs 本人负责数 + 四分类：已 LIVE PASS / 已调用未 VERIFIED / 明确问题 / 未测试），明细表放后面或等他要；不要用长表格或逐条叙述去回答一个"几个"的问题。
- 对外操作（改库、部署）先确认；只读 SELECT 和接口 GET/POST 测试可直接做。
- **鉴权优先用 Web 会话令牌，不要卡在 SK/签名链路上**：`Cookie: SY_ACCESS_TOKEN=<JWT>; SY_UID=<uid>` 就能以真实登录态调业务接口。让用户从浏览器复制一次即可（约 2 小时过期，过期直接再要，别为此去挖 SK）；SK 只在真正的对外 ESB 场景才需要。

## 四轮测试法

0. **先锁定责任范围与完整清单**：如果任务来自飞书/在线表格，先在指定 tab 内搜索责任人并读取全部命中项，不要把当前滚动窗口当完整表格。记录总任务数、命中数、业务序号、细项、责任人、状态、实施配置；按业务序号去重。对每个命中项先反查 Controller 的真实路由、HTTP 方法和请求 DTO，再决定是否 LIVE。
   - 用浏览器搜索结果计数（例如 `1/26`）核对命中总数。
   - Canvas 表格不要依赖 `body.innerText`；优先读取名称框/公式栏定位的 A-F 单元格原值，OCR 只作交叉核对。
   - 推送、保存、审批、同步等有副作用的接口只做源码确认，除非用户明确授权，不直接调用；查询接口才进入 LIVE 批测。
   - **"还有几个没测"这类问题要程序化统计，不能凭记忆报数**：把清单快照存成 JSON，用责任人过滤得到本人负责项，再与用例/结果文件比对，输出三分类——`已 LIVE 实测` / `已调用但未 VERIFIED`（返回 0 行、需造数、需修后复测）/ `未测试`（写推送类）。同一份清单要同时报"总项数 vs 本人负责项数"。依据快照的当前责任人列容易被他人改动，报告里注明快照来源与日期。

1. **全量实测**：按接口清单逐个 LIVE 调用，每接口统计行数、字段总数、有值/null/empty 分布，产出 FAIL / UNVERIFIED 分级。
2. **源码定位**：对 FAIL 项读源码找根因——组装路径差异、硬编码查询条件、吞异常、字段映射来源。
3. **DB 取证换样本**：直连业务库查子表数据分布，找有数据的合同号替换样本，LIVE 复测 UNVERIFIED 项。
4. **修复回归**：改码/改库 → 部署 → 回归验证 → 汇总"改了哪些接口、测了哪些接口"。

### 5. 跨版本回归（修复已由他人/CI 部署时）

回归前先确认运行环境实际部署的版本，不要假设镜像就是本地源码版本：
- Deployment 镜像 tag（如 `1.0.11075`）对比本地 pom `parent.version`（可能落后多个 build，如本地 11060 vs 部署 11075）。本地落后时，回归结论只覆盖自己验证过的修复点，不覆盖期间他人改动。
- 用 SSH→中间服务器→`kubectl --kubeconfig=configtest2 get rs -o wide` 看 RS 镜像演进历史 + 当前 Running Pod 的 image/lastState，判断新 RS 是否稳定、旧 Error Pod 是否属于旧版本残留。
- 回归报告要区分：修复点 LIVE PASS / 部分生效（如 `processType` 仅已生效合同有值，审批中合同为空串——需产品确认语义）/ 非缺陷维持原判 / 新镜像未复现的问题（如日志脱敏，只对新 Pod 日志 grep 计数）。
- **镜像 tag 对应的是"版本号提交"，不是你最新提交**：`update version to x.y.z` 之后 commit 的修复默认不在运行镜像里（CI 只构建被 bump 的那个提交，本地 commit 晚几分钟就漏掉）。所以"我改了但还报错"要先证明代码没上线再谈修：① 比对 `git log --format="%h %ci %s"` 里版本提交时间与你自己 commit 的时间；② 从线上 Pod 日志 `grep -c` 自己加的日志串/中文提示——命中即上线、0 即未上线；③ 堆栈里的 `类名:行号` 是**编译期行号**，必须与部署提交的源码比对，用当前工作区行号对号入座会得出错误结论；④ 运行版本还能由日志里的**代码形态**反推——日志显示的是修复前的写法（如那段查询没有 try/catch、warn 文案不在），就是你的修复没进这个镜像，别再 "修" 第二遍，直接要一次构建。

## LIVE 调用与测试脚手架

- **调用形态**：`POST {SEEYON_APP_BASE_URL}/service/{applicationId}/{Controller 的 @RequestMapping}/{方法}`，`Content-Type: application/json` + JSON body。Controller 注解里已含 applicationId 时不要重复拼。
- **不要每次手敲 curl**：用例写成 JSON 数组，跑 `scripts/run_cases.py`（POST + 留档原始响应 + 统计 行数/字段数/null/空串/裸ID）；字段级烂点用 `scripts/audit_detail.py` 定位；DB 取证用 `scripts/db_readonly.py`；改完代码用 `scripts/compile_check.sh` 做本地类型校验再交用户构建。细节见 `references/live-call-harness-and-sample-discovery.md`。
- **`kind=write` 的用例在脚手架里默认跳过**（记为 side-effect: source inspection only）。推送/保存/审批/同步类接口只有用户明确授权后才能置 `allow_live` 真跑。
- **凭据文件不要用 `source` / `.` 加载**：`.env` 里的 Windows 反斜杠路径和含特殊字符的密码未加引号，shell 加载会报 `command not found` 或把路径吃掉。用 Python 逐行 `split("=", 1)` 解析取值；私钥先复制到 `$LOCALAPPDATA/Temp` 再用正斜杠路径传给 `ssh -i`。
- **丢失的测试资产先试着找回，再决定重做**：表格快照/报告原文即使文件被删，历史会话里仍有原文——`session_search` 定位会话后，直接读 `state.db`（`sqlite3 "file:<profile>/state.db?mode=ro"`，`messages` 表 `content LIKE '%特征串%'`）取回，`read_file` 的 2000 行上限足够还原几十行的清单。

## 典型缺陷类别与定位手法

### 1. 裸ID未转化（值没被转化）
低代码 Controller 常有两条组装路径，转化覆盖不同：
- 旧接口：手工 `resultDataMap.put(...)`，逐字段显式调用 `getCtpEnumItemValue(Long)`（枚举）、`getMemberName(Long)`（人员）、`getHuilvpeizhibiaoName(Long)`（币种）。
- 新接口：`converter.convert()` → `BeanUtil.beanToMap()` 反射直通，中间的 `convertToString(Object)` 只是 `value.toString()`，ID 原样出。
- **修复手法**：不重写组装，写后置转化方法对同一批字段补调既有转化函数；解析失败保留原值 + warn 日志。
- DTO 里预留的 `*String`/`*Str` 字段（如 `signCurrencyString`）常从未被赋值，可作佐证。
- **裸ID 命中要逐字段分类，不能直接算缺陷数**：主键/外键型字段（`bizId`、`thirdPartyId`、`contractId`、`*Id`、`*Key`）本来就该是 ID，枚举/人员/币种/部门类字段（`signCurrency`、`saler`、`accountCate`、`projectIndustry`、`processType`…）跑到裸ID 才是"该转化没转化"。报告里报"裸ID 总数"之外必须给分类表，否则会把几千个合法 ID 写成缺陷（列表类接口尤其明显：一条行里多个 ID 列 ⇒ 行数×列数迅速过千）。

### 2. 接口查不到数据 ≠ bug
先查源码里的硬编码查询条件（如 `statusType=COME_INTO_FORCE` 只查"已生效"、`shenpileixing=枚举ID`），再到 DB 对比样本合同实际状态（`htspzt` 枚举=审批中/审批完成/已结束）。常见结论是"接口按设计工作，换已结束流程的合同"。

### 3. Long→Integer 溢出（UDC 生成表）
合同 ID 是 19 位 Long，UDC 生成表可能把 `contract_id` 定义为 `int(11)` + 元数据 `INTEGER(10)`。**必须两层配对修改**：
- 元数据：`udc_test2.udc_attribute SET data_type='BIGINTEGER', max_length='20'`
- 物理：`ALTER TABLE ... MODIFY COLUMN contract_id bigint(20)`
只改物理列会被运行时实体校验打回（教训见 references）。

### 4. 吞异常假成功
内部子查询失败（动态查询条件传 null、NPE）但外层仍组装 `code=S`。看 Pod 日志 trace 才能发现；响应字段不可信，不能标 LIVE PASS。

## DB 取证技巧（只读）

- 枚举 ID 解码：`ctp_enum` + `ctp_enum_item`（`name` 列是 `{"zh_CN":"xx"}` JSON，需解析）。
- UDC 元数据反查：`udc_test2.udc_entity`（按 `table_name`）→ `udc_attribute`（按 `entity_id` + `db_column_name`）。
- **换样本不用求用户造数**：子表 `parent_id JOIN hetongdan 主表` 统计有数据的合同号，按子表覆盖面挑样本；一个合同常能同时覆盖多个空接口。
- 金额来源甄别：历史遗留字段可能全库无值（如 `htzjehs` 0 条非零），真实金额在别的字段（如 `fnbjshtzehj`）——用 `COUNT(*) WHERE col != 0` 对比判断。
- 表名是拼音前缀+实体ID（如 `chanpinze_7279308198137569652`），**搜表要用 `udc_entity.caption/name` 反查，别只靠 LIKE 前缀**（会漏表、误判"全库无数据"）。
- `udc_entity` 对同一实体常返回**多张候选表**（设计态/历史/运行态），其中往往只有一张存在于业务库。用 `information_schema.tables` 枚举实际存在、且 `COUNT(*) > 0` 的那张，别猜、别拿 0 行的旧表当结论依据。
- **找样本直接 JOIN 档案表出合同号**：`SELECT h.hetonghao, COUNT(*) c FROM <子表> x JOIN <合同档案表> h ON h.id = x.parent_id WHERE h.hetonghao <> '' GROUP BY h.hetonghao ORDER BY c DESC LIMIT 6`。只看子表 `parent_id` 的 top 分布会大量命中孤儿/测试数据（`parent_id` 在档案表里查不到），据此挑样本会白测一轮。
- 合同档案主表由 `udc_entity.name='hetongdangan'` 反查（本环境为 `hetongdan_<id>`）；关键列：契约号 `hetonghao`、客户 `kehumingcheng`、档案状态 `status_type`、审批类型 `shenpileixing`、流程 `case_id`、迁移标记 `business_id`。重号合同的同一 `hetonghao` 有多条记录，各自 `business_id`/`case_id` 不同。

### 6. 需"配置数据"的接口：先 DB 取证再 LIVE，别下"接口挂了"结论（2026-09-14 补）

清单里标"待联调"≠有问题。对返回空但源码逻辑看似正常的接口，先从 DB 找真实样本再 LIVE 复测，常能直接翻案：

- **按协议号/客户名查配置的接口**（如 4.16 `findConfAddValueDataByNumber`、4.11 `confAddValuePage`）：先在配置表（如 `zzywkjxyp*`）查 `status_type='1'` 且编号/客户非空的行，用真实协议号/客户名 LIVE → 返回数据即 PASS。翻案时在报告里给出所用样本值。
- **共同核算类**（4.19/4.20）：子表的 `hetonghao` 列存的可能是**合同档案 Long ID 而非合同号字符串**（拼音列名≠语义）。发现 JOIN 不上时先 `SELECT hetonghao FROM 主表 WHERE id IN (子表值)` 反查验证，再决定用 ID 还是合同号作为接口入参换样本。
- **ID 语义甄别**：子表里的关联列（`dorder_notice_id`、`contract_id`）值域可能是 19 位 Long、小自增序号或外部系统单据号。值域与目标表主键不匹配（如 '33683' vs 19 位 Long）时，该关联永远 JOIN 不上——这是**数据/映射问题**，需要确认字段语义，不能只看代码改。

### 7. 参数双路径不一致 bug（contractId 正常 / contractNo 返回空）

同一接口支持 `contractId` 与 `contractNo` 两种入参时，必须**两条路径都用 DB 有数据的样本各测一次**。典型案例：`downFormListPage` 传 contractId 返回完整行，传 contractNo（同一合同）返回空数组。

**根因分级（2026-09-14 实锤两例）**：
1. **重号档案**：合同号在档案表有多条记录（历史重号），contractNo 路径按 `shenqingriqi DESC` 只取第一条，而数据挂在另一条（更早的）档案上 → 取错档案返回空。修复手法：contractNo 路径遍历候选档案、按子表 parentId 探测数据存在性优先选有数据的那条，全无数据回退第一条。需在 Service 加"按合同号返回全部档案"的 List 变体方法。
2. **解析链路不一致**：contractNo 只用于查合同，后续数据查询与 contractId 路径走不同代码分支。

这类 bug 只测一条路径会漏；修复后同样要两条路径都回归。

### 8. 金额=0 的甄别（4.15 类汇总接口）

按客户汇总合同金额返回 0.00 时，三层核实再下结论：① 客户名是否精确命中（`LIKE_kehumingcheng` + `status_type=3` 已生效）；② 金额来源子表（如产品服务表 `chanpinfu*`，**不是** `fnbjslb` 结算表）里该合同有无行；③ 行上的类型枚举（如 `ht_type`=`resolveId('sales_nature','2')`）是否匹配。DB 里逐层 COUNT 对比后，"0.00 与数据一致"和"取值来源错"是两种不同结论。

### 9. `code=S` + `data:[]` 可能是逐行内查失败被吞（不是空数据）

典型形态：先按 `parent_id` 查到关联表 N 行，再逐行 `selectById(关联列)`，查不到就 `log.error(...) + continue`，最后外层照样组装 `code=S` + 空数组。判据：**子表有行却返回空 → 缺陷**，看运行日志的 error 行 + 关联列值域才能定位。同族问题：另一处代码点用同一张表的另一个字段取值（如 `dorder_id` vs `dorder_notice_id`），说明字段语义本身要产品确认，不能猜着改。

### 10. 重号档案影响所有 `...ByContractNo` 调用方，不止一个接口

`contractNo →` 单个档案的服务方法（`shenqingriqi DESC` 取第一条）对重号合同会取到没有子表数据的那条，表现为报"XX不存在 / XX信息不存在"而不是返回空。**修完一个接口的 contractNo 路径后必须 grep 全部调用方**（`grep -rn "selectHetongdanganByContractNo" src/`）逐个判断是否同样需要"按子表数据择优"的 List 变体。

### 11. DTO 有参数字段 ≠ 接口支持该参数

入参 DTO 里声明了 `contractId`，方法体可能只读 `contractNo`，传 ID 必报错。双路径测试要覆盖"DTO 里出现的所有关联键"，报告里写明"入参字段被忽略/未实现（接口设计限制）"，不要写成数据问题。

### 12. 生效态过滤类接口的样本必须换"已生效"合同

若干接口硬编码 `statusType=COME_INTO_FORCE`（本环境实测枚举值 = 3，不是 -1；全库处于该态的合同只有个位数）。返 `没有对应的合同信息` / `不存在的客户名称` 时，先 `SELECT status_type, COUNT(*) FROM <档案表> GROUP BY status_type` 确认这类样本天然稀缺，再挑该态样本复测。**这类结果写"数据依赖"，不写缺陷**；反过来，不要拿"审批中"样本去证明它有 bug。

### 13. 写/推送类清单项：先定位入口，别直接判"无法联调"

清单里查不到 HTTP 路由的推送/保存项（保存、推送外采、推 ERP 等），先做两步再下结论：

1. **grep controller 看有没有人给它加过端点**：`grep -rn "<服务方法名>" src/main/java/.../extend/controller/`。这类接口当年为联调常被显式加过转发端点（几行 `@PostMapping("/x") → service.x(request)`），有端点就能直接 `POST {SEEYON_APP_BASE_URL}/service/{appId}/{Controller @RequestMapping}/{方法}`，body 多为 `SingleRequest<Long>`（即 `{"data": <合同档案ID>}`）。项目里的 `.idea/httpRequests/http-requests-log.http` 常留有历史调用，用它确认 URL 与 body 形态，比猜快。
2. **查平台元数据表**（不必找 facade 源码）：`udc_microflow_info`，列 `name`(微流程编码) / `caption`(业务名，常直接写清单编号) / `service_interface`(绑定的 appservice) / `app_id`(**数字**应用ID，不是 application_id 字符串) / `rest_api` / `rest_path`。判定：`rest_api=0` 表示平台未生成 REST 路径，只能由业务流程/表单事件触发。

**清单序号与实现类不是一一对应**：一个 `@AppService` 实现类常承载多个清单项（同一入口多方法，如"合同结束推合同信息"与"推审批记录"是两个方法、"保存/修改八张表"也是两个方法），也可能某个清单项在 `udc_microflow_info` 里**没有独立条目**而复用另一序号的方法。汇报"合成一个接口了 / 是几类"之前，按 `service_interface`（实现类）分组 + 该类的方法清单来数，不要按清单序号数：`SELECT service_interface, name, caption, rest_api FROM udc_microflow_info WHERE app_id=<数字appId>`，再用 `javap`/源码列出该实现类的方法，逐项对号。

**判定口径**：微流程 ≠ 只能走业务流程。有端点 → "可直接联调（有副作用，需授权+指定单据）"；无端点 → "只能业务触发，或照抄现有端点写法补一个 controller 端点"（补端点=新增对外接口，要用户点头）。**绝不要把"没找到 Controller"写成"无法联调"**——这是漏查，不是结论。映射表与列语义见 `references/seeyon-microflow-entry-mapping.md`。

薄壳端点写法：照 `@AppService` 实现类所实现 facade 接口的签名加一个 `@RestController`，`@PostMapping("/x") → service.x(request)`，参数 `@RequestBody SingleRequest<Long>`（body `{"data": <合同档案ID>}`），联调完删除该类。用户明确要求"缺入口就自己建一个仿照参数请求"时不要再问一遍，建完说明清楚它是临时通道即可。

**推送类接口的失败是链式的**：报文构造方法（`detail()` 这类上千行方法）里几十处 `getData().getContent()` 未判空，修完一处下一处才暴露（币种 → 商务档案 → 共同核算 …）。按堆栈行号逐个补：解析不到时 `log.warn` + 跳过而不是抛异常；`DozerUtil.convertor*(null)` 在 util 入口判空返回 null 由调用方处理；`.getContent().get(0)` 先判空列表。**每次构建都要用户 commit+push 触发 CI（本机 shell 无 GitLab 凭据），所以把已发现的同类空指针批量修完再请用户构建**，不要修一处跑一轮。

**补完薄壳端点后的 LIVE 判读**：`GET` 该路由返回 **405 = 路由已部署**（404 = 还没生效）。响应 `BOOT_0000` + `data.content=true|false` 是服务层正常返回，`false` 有两种来源，判定顺序是先源码后 DB：①**下游业务拒绝**（外采回 `{"code":"failure","result":"传入内容为空，请重试！"}` 这类，常见于该单据没有流程实例/审批记录）→ 换有流程记录的单据复测，不写缺陷；②**服务层自己的前置校验提前 return**（如"产品行 lineId 非空"）→ 回源码 `grep -n "return false" <Service>` 定位校验点，再回 DB 核对该字段（产品服务行 `business_id` 是否为空）。库里有值却仍 false ⇒ 取值来源还没对上，写"待定位"，不要写成数据问题结论。`BOOT_3000`/`status=3`/`message=null` 是被 `ExceptionHandleFilter` 兜住的业务异常（NPE 居多）→ 用响应体里的 `traceId` 去 Running Pod 日志 grep 根因栈帧。写法、取证命令与副作用披露口径见 `references/seeyon-microflow-entry-mapping.md`。

### 14. DTO 字段是「实体关联」还是「枚举」——先查 UDC 元数据再决定解析方式

低代码生成的 DTO 字段注解 `@DtoAttribute(relationDto=..., customs=[dataType=ENTITY|CTPENUM])` 就是权威声明，运行态等价证据在 `udc_test2.udc_attribute`（字段名 `name` 是 camelCase，与 DTO getter 对应）：

- `data_type='CTPENUM'` → 用 `ctpEnumItemService/CtpEnumItemAppService.selectById(枚举项id)` 解析；
- `data_type='ENTITY'` → **必须**用被关联实体的 AppService 解析（`relation_entity_name` 给出实体名，如「汇率配置表」`HuilvpeizhibiaoAppService`、「币种配置表」、「组织」）。用枚举服务解析 ENTITY 字段会拿到 null，随后 `xxx.getItemValue()` 直接 NPE。

合同档案（`hetongdan_7107967264754597333`）上的实例：

| 字段 | 元数据 | 正确解析 |
|---|---|---|
| `qianyuebizhong` 签约币种 | ENTITY → 汇率配置表 | `huilvpeizhibiaoAppService.selectById(id)` → `HuilvpeizhibiaoDto.getBizhongdaima()`（CNY/USD） |
| `currencyExchangeRate` 币种汇率 | ENTITY → 汇率配置表 | 同上 → `getDuihuanlv()` |
| `bizhong` 币种 | ENTITY → 汇率配置表 | 同上 |
| `shenpileixing` 审批类型 | CTPENUM | `ctpEnumItemService` |

**同名字段在不同实体上类型不同**（`caigoubizhong` 在「合同档案」是 ENTITY→币种配置表，在「实际成本」是 CTPENUM）——审计时必须按「接收者变量声明的实体」查元数据，不能按字段名一刀切。审计手法：正则抓 `ctpEnumItemService.selectById(X.getYyy())` 与 `huilvpeizhibiaoAppService.selectById(...getZzz())`，再用 udc_attribute 的 `data_type` 判定对错。

解析失败时的兜底要显式：汇率/币种拿不到时跳过换算 + `log.warn`，不要让它变成 NPE 把整个推送接口打成 `BOOT_3000`（吞掉堆栈只留 `NullPointerException: null`）。

**枚举项级别的同类错误：`getEnumCode()` 不是值。** `ctp_enum_item` 里 `enum_code` 是枚举编码（同一枚举的所有项完全一样，如 `kj_status`），`item_value` 才是值（数字 `0/1/2`、语义串 `receive/payment`）。把枚举编码喂给 `Long.valueOf/Integer.valueOf` 必抛 `NumberFormatException: For input string: "kj_status"`（或其它枚举编码），整个推送接口变 `BOOT_3000`。

- 判据：`grep -rnE "(valueOf|parseInt|parseLong)\([^)]*getEnumCode\(\)" src/` 用来**缩小排查范围**，命中本身不是缺陷证据：`enum_code` 列在某些环境/枚举里实际存的就是可解析的数字串，此时 `Long.valueOf(getEnumCode())` 正常运行，照 grep 结果改会变成无据改变取值来源。定级前要拿到运行时证据之一——① 线上堆栈出现 `NumberFormatException: For input string: "<枚举编码>"`；② DB 实测该枚举 `enum_code` 确为非数字串（`SELECT DISTINCT enum_code, item_value FROM ctp_enum_item WHERE ...`）而代码又把它喂给数值转换。两类证据都没有时，写进"待用户确认"清单，不要直接改。
- **取值来源（`itemValue` vs `enumCode`）的替换必须用户点头**：即使确认转换会崩，也要先说明"该字段实际该取哪一列、为什么"，由用户确认后再改；改完在报告里明确标出"此改动涉及取值来源，已确认"。
- 确认属于缺陷后，修复用统一 helper（`NumberUtil.isLong/isInteger(itemValue)` 通过才转换，否则 `log.warn` + 跳过/置空），不要就地 `try/catch` 复制 N 份；同理枚举 id 为空或为 0（未选择）时不要拿去 `selectById`；解析不到时兜底跳过而不是抛异常（`DozerUtil.convertor*(null)` 在 util 入口判空返回 null 由调用方处理），并把"兜底 warn 一次都没触发"当作修复生效的正面证据。

## Pitfalls

- **本地编译校验的三个假象**（会让人去改本来正确的代码）：① `target/classes` 里的旧 class（几个月前的产物）抢先解析，报"找不到符号 setXxx"而源码里该方法确实存在；② 全量 jar classpath 的顺序会让旧版本 facade/biz 抢先解析——把精选版本目录（facade/biz 指定版本）放在 classpath 最前，其余 jar 只做兜底；③ 不要加 `-sourcepath`，那会让 javac 从源码全量解析依赖、炸出几百条与改动无关的错误。判据：报错符号在源码中存在 ⇒ classpath 假象，在结论里如实标注"与本次改动无关"。
- Cookie/SK 被脱敏显示时（`sk-hwO...MS5J`）必须程序化从源文件提取，手工抄写拼错必 401。
- 接口多为 `@PostMapping`，用 GET 会 405；Content-Type 为 `application/json` + JSON body。
- 响应可能是 Whitelabel HTML 错误页，`json.loads` 前先判 content-type 或 try/except。
- `completeLegacyContractDetailFields` 用 `putIfAbsent` 补兼容空值，排查字段缺失时注意它不会覆盖已有 null。
- **改动要真编译验证，别退回"静态自检"**：本仓库是 `-ext` 单模块，离线 `mvn compile` 会因缺聚合父 POM（`com.seeyon:<appId>:pom:<parent.version>` 不在本地仓库）失败——但类型检查不依赖它：用 `javac` 拼 classpath 单文件编译（`target/classes` + 本地仓库的 `<appId>-facade` jar + `boot-core` + `spring-{web,beans,context}` + `slf4j-api`，`-encoding UTF-8`），exit 0 即证明 import / facade 签名 / 泛型都对得上，是能拿给用户看的证据。需要完整构建时走 `cmd.exe /c '<PATH><ver>\bin\mvn.cmd -s <settings> -Dmaven.repo.local=D:\repo ...'`（先设 `JAVA_HOME`），MSYS 下直接跑 `mvn` 会 `ClassNotFoundException: plexus-classworlds.launcher.Launcher`。
  现成脚本：`scripts/compile_check.sh <repo> [local_maven_repo]`（自动取 `git diff` 的改动文件并拼 classpath）。两个必踩的坑：① 传给原生 javac 的路径必须是 `D:/...` 形式，MSYS 的 `/d/...` 会报“找不到文件”；② classpath 除了 facade/boot-core/spring 还要带 `udc-common`（DTO 基类 `BaseRootDto`，缺了则所有继承来的 getter 都“找不到符号”）、`tomcat-embed-core`（`HttpServletRequest`）、`guava`、`dozer`、`hutool-all`、`fastjson`、`lombok`，缺一个就满屏“程序包不存在”。
- **判断"没有入口/没有实现"之前先看 jar**：扩展仓库里只有手写业务代码；UDC 生成的微流程接口、默认实现、事件监听器都在本地 Maven 仓库的 `<appId>-facade`/`<appId>-biz` jar 里（`<PATH><ORG>/com/seeyon/<appId>-{facade,biz,web}/<version>/`，用 `javap -classpath <jar> <FQCN>` 读签名）。微流程入口是 Dubbo 导出的 `@AppService` bean，不是 MVC controller——只在 `-ext` 里 grep 不到就报"无法联调"属于漏查。**连本地仓库都没有时，运行 pod 的扩展 jar 是等价权威产物**：`jar tf /app/libs/BOOT-INF/lib/<appId>-ext-<ver>.jar | grep -E 'Controller|Api|Listener'` 列出 `extend/controller/` 下的手写类，**一条 base64 单行命令一次批量导出多个 class**（pod 内逐个 `jar xf` 会被确认门反复拦下，外层 `sh -c` 嵌引号也易写错模式），取回本地 CFR 反编译整个目录后再 grep。开放接口常见命名形态是 `OpenApiController` + `/open/api/<业务名>`。
- **需求说"要新增"不等于"现在没有"——先用需求里的中文字面量反查一遍。** 把需求给的标题模板 / 错误文案 / 按钮名作为关键词扫扩展 jar 与反编译产物（class 常量池是 UTF-8，Python 直接读 bytes 就能搜中文字符串，比先反编译再搜快一个量级）。命中即证明该能力已存在，此时交付物是"已实现 + 缺哪一块"（如只差测试环境分支），不是"从零新增"——按后者写方案会被用户当场纠正。同理，找"某个业务动作的提醒该挂哪"要先确认这条数据是谁创建的（页面微流程 / 手写 Controller / 事件监听，分发表见 `seeyon-udc-runtime` 的 `references/app-mechanism-audit.md`）：**外部系统主动调本系统接口创建单据时，入口在手写 Controller，去页面微流程里找只会撞到一堆命名近似但条件读别的业务的干扰项。**

### 15. 标品单点/免登链路取证（cip-connector + ctp-user，2026-09-16 实证）

查标品源码的固定入口：本地标品仓库 `<PATH> 全在其中）；二进制交叉验证用 Artifactory `http://10.0.0.1/artifactory/libs-release/com/seeyon/<artifact>/<ver>/`（curl 下载 jar → unzip → `javap -p -cp <dir> <FQCN>`；javap 在 git-bash 不在 PATH，用 `/d/software/java/bin/javap.exe`，classpath 传 Windows 形式路径）。

钉钉免登真实调用链（全部已字节码/源码实证）：
- 前端入口 `POST /ctp-user/auth/third`，body=`CtpThirdLoginDto{thirdType:"DING_TALK", thirdAppId:<钉钉appKey/clientId>, thirdCode:<免登code>, clientType}`。cookie 有效时返回 `useCookies:true`（可作会话探测）。m5 插件无独立免登接口，最终都落这里。
- ctp-user → dubbo 泛化 `cip-connector: MobileSsoAppService#getMobilePluginSsoUserDto` → `DingTalkApplicationProviderServiceImpl#getMobileSsoUserDto`：access_token + code 调 `oapi.dingtalk.com/user/getuserinfo` → userid/mobile → 用户映射。配置缺失报 `MOBILE_CONFIG_NULL`（CONNECTOR_0083）。
- 移动插件标准单点入口页 `/oauth/home`，标品生成格式（`DingTalkApplicationProviderServiceImpl#getMobileUrlDto`）：`{frontBaseRoute}/oauth/home?type=DING_TALK&corpId={corpId}&appId={appKey}&web={webIndexPage}`。type 是大写 `DING_TALK`（PlatformConstant），参数名是 appId（=appKey）不是 code 位置。`/oauth/home` 是 ctp-user 前端路由（源码不在 backend 仓库），"URL code 是否被消费为 thirdCode" 需 LIVE 验证：造一个无效 code 直接开该 URL，F12 看 `/auth/third` 是否发起。
- 别混淆两条入口：`AuthController#thirdSsoBackend`（`/third/sso`，`businessType=outsider&mobile=&web=&type=&code=hidden` 格式）是外部系统后端重定向路径；移动插件 iframe 场景用 `/oauth/home` 格式。
- cip-connector 侧 dubbo 泛化查询接口与版本兼容：`CtpUserMobilePluginGeneralizationInvoker`（ctp-user-biz），错误前缀约定 `mobile-sso-err`。

iframe/postMessage 跳板页方案（三方系统嵌入 V8 单点）：跳板页必须与 ctp-user 同域部署（否则换不到 cookie）；在 iframe（三方域）里 cookie 属第三方上下文，需 V8 配置 `sameSite=none` 且全站 HTTPS，否则 `SY_ACCESS_TOKEN` 被浏览器丢弃且无报错。gateway 白名单放行 `/sso-bridge/**`。authCode 一次性（钉钉 5 分钟 + ctp-user redis 防重放 5 分钟），不可重放；回包必须校验 `event.origin` 白名单。已交付跳板页样例：`<SEEYON_AGENT_ROOT>/docs/deliverables/sso-bridge/index.html`（CONFIG 区集中配置 clientId/corpId/origin 白名单/lsKey/oauthHomePath，mode=sso 拼 `/oauth/home` 跳转为主路径）。

### 16. `selectListByConditions` 的条件键是**属性名**，不是物理列名

平台按 DTO 属性名（`udc_test2.udc_attribute.name`，camelCase）拼查询条件；传物理列名有两种失败形态，**都不能当成"库里没数据"**：

- 静默形态：返回 0 行、不报错，日志只留"未查询到…数据"的 WARN。
- 抛异常形态：`java.lang.IllegalArgumentException: 属性[swtzdbh]不存在`（MyBatis `### Cause:` 栈），被平台过滤器兜成 `code=BOOT_3000` / `message=null`，直接把整个推送接口打挂——同一段代码在有的平台版本/调用链上是静默 0 行，在别的链路上直接抛。

实测：按合同号查华为通知单必须 `map.put("huaweiOrderNumber", 合同号)`（该属性对应的物理列才是 `swtzdbh`）。

- 反查条件键：`SELECT name, db_column_name FROM udc_test2.udc_attribute WHERE entity_id=<实体id> AND name='<字段>'`，取 `name` 当 key（`db_column_name` 只用于直连 SQL）。
- 拿不准时按"属性名 → 列名"顺序各查一次，两次都空才判"无数据"；库里明明有行、查询却 0 行，先怀疑条件键。
- 兜底尝试必须包在 `try/catch` 里：包一层 `selectXxxByKey(条件键)` 私有方法（`catch (Exception e) { log.warn(...); return Collections.emptyList(); }`），否则列名那次尝试抛的异常会顶穿到外层响应。改完先本地编译再交用户构建，一次构建要带上所有已知同类点。

- 反查条件键：`SELECT name, db_column_name FROM udc_test2.udc_attribute WHERE entity_id=<实体id> AND name='<字段>'`，取 `name` 当 key（`db_column_name` 只用于直连 SQL）。
- 拿不准时按"属性名 → 列名"顺序各查一次，两次都空才判"无数据"；库里明明有行、查询却 0 行，先怀疑条件键。

### 17. 失败样本必须用 DB 定性：数据依赖 / 缺陷 / 设计限制

接口返回 `code=E`（如"XX信息不存在"）时，按源码里那句 error 的**判空条件**回查 DB，不要凭消息字面意思归类：

1. 定位 `return errorESB("...")` 上方的集合/对象，看它为什么为空（例："合同产品信息不存在"= 内部/非内部结算子表收集到的 `acount_cate` 为空）。
2. 用 DB 核对同一条件（该合同的结算子表行数 + `acount_cate` 非空计数）：库里有值 ⇒ 取数条件问题，升级为缺陷；库里为空 ⇒ 数据依赖，写"数据依赖"不写缺陷。
3. 客户名/协议号类的"不存在"，先确认精确匹配（客户档案），能命中一个样本即接口本身可用。

**关联键语义假设要用全量 JOIN 命中率验证，不要抽样几行**：`SELECT COUNT(*) FROM 关联表 r JOIN 目标表 t ON t.id = r.<列> WHERE t.<业务键> = r.<文本列>`，逐个候选列比对——命中 100% 才是关联键，0% 说明值域不匹配（旧系统序号、需业务键兜底）。抽样 3~5 行会得出反了的结论。

**跨表比对注意类型**：DB 取出的 id 是 int，`str(x) in set_of_int` 恒为 False，会得出"0/658 命中"这种错误结论。比较前统一归一化（转字符串 + 去空格 + 去 `.0`），结论确定前不要写进报告。

### 配套文件

- `references/udc-runtime-error-triage.md` —— 前端 `no exist store key as {app}/{page}@{组件类型}:{实例id}-{dataTarget}` 的连带/独立缺陷判据，以及 `BOOT_4004 违反主键约束`（create-bpm 类新增/提交接口）的四步定位法、日志取证要点（traceId 过滤别只 grep ERROR 关键词）与修法优先级。
- `templates/cleanup-duplicate-child-rows.sql` —— 清理子表重复行（一对一子表插成多条/重复提交）：探测 → 备份 → 定向删除 → 校验 → 回滚。

## 测试库造数（用户授权后，2026-09-14 验证）

清单标"需造数"的空接口可以在用户授权后直接 DB 造数打通验证，比等页面造数快：
- **配置类**（增值框架配置等）：INSERT 一行到配置表，`status_type='1'`、客户名取**已有已生效合同的客户**（保证接口能通过合同→客户名→配置表链路命中）、编号用可辨识标记（如 `KJXYTEST<日期>`）。
- **金额类**：向金额来源子表插入一行，`parent_id` 指向已生效合同，类型枚举列取该表**众数枚举 ID**（GROUP BY 排第一的），金额任意小值。注意 `INSERT...SELECT` 里不能用 `?`/`%s` 占位参数——先 SELECT 模板行再显式 INSERT VALUES。
- **必须回读**：INSERT 后 SELECT 同一 id 确认，再 LIVE 调接口闭环；报告里附清理 DELETE 语句。
- 值域冲突：生成的 ID 用独立区段（如 `-80…`/`-81…` 开头 + 随机尾数），避免与既有 19 位 Long 撞车。

### 18. 法务平台类外部接口：person 入参是 ERP 工号，不是致远人员编码

`法务平台` 系列（`LegalPlatFormAppService`：1.1法务平台模版列表 `MFCUSTOMZS4NAE`、1.4人员名称映射ERPID `mFCUSTOMXFHAYQ`、模版绑定/占用解除）全部**直连外部 OpenAPI**，本地业务库里查不到"有没有数据"，必须真调：

- 端点与凭据在应用 Nacos 配置里（`seeyon-uat`/`seeyon-test2`, `dataId=<applicationId>`, `group=seeyon`；Open API 路径是 `/nacos/v1/cs/configs`，注意是复数）：`seeyon.legalAffairsPlatform.legalContractQueryUrl|orgQueryUrl|templateBindingUrl`、凭据用 `seeyon.sample.accessKey/secretKey`（配置是缩进 YAML，按缩进层级解析，不要用平铺正则）。
- **erpId ≠ 致远人员编码**：`org_member.code`（如 48181）喂给 `LEGAL_CONTRACT_QUERY` 稳定返回 0 条；正确做法是先调 `ERP_FIND_PER_PEOPLE_HISTORY_V`（body `{accessKey, secretKey, contents:{person_name, primary_flag:"Y"}}`）取 `data[0].ASSIGNMENT_NUMBER`（如 6106）再查模版。查某人"有没有数据"前必须先做这一步映射，否则会误报"无数据"。
- **应用层过滤会把有数据筛成空**：`MFCUSTOMZS4NAE` 会把 `lsfwmblb`（历史法务模板列表）里的 `template_id` 全量当"已占用"排除。UAT/test2 该表 35,288 行全部在 9 分钟内一次性灌入（`creator=0`, `batch_id=20260911000000`）⇒ 是迁移批次，命中率 100%，任何人查出来都是 0 条。报"接口没数据"前先查该表的写入形态（时间窗/creator/batch_id）判断是"当前占用"还是"历史全量"，再决定写缺陷还是待产品确认。
- 外部 OpenAPI 的 `totalElements` 与逐页 `content` 条数可能不一致（实测 totalElements=43，翻页只取回 23），报告里如实标注分页差异，不要用 totalElements 当已取回条数。

### 19. 详情页报 `[获取实体数据失败] 查询结果为多条记录` = 主表 + 一对一子表 join fan-out

UDC 详情页/表单取数接口 `{base}/service/{appId}/{pageUrl}/{entityAppName}/{entityName}/{componentId}/select-cascade-by-conditions` 是平台的"条件查询单一记录"：

- 实现链：`UdcGeneralController`(`@PostMapping("{entityAppName}/{entityName}/select-cascade-by-conditions")`) → `BaseEntityCurdService.selectOne2OneCascadeByDyCondition`。源码里 `pageInfo.setPageSize(2)`，`resultList.size() > 1` 就 `throw BusinessException.message("查询结果为多条记录")`，同时 `log.error("单一记录{}查询条件：{}", entityFullName, proxyJoinParamDto)` 会把实际条件打进日志。
- **条件为空也要查**：请求体只有 `{id, controlId, pageGuid, searchParamDto:{}, bpmInfo}` 时，过滤条件就是**主键 id**，主表必是 1 行——此时"多条"只能来自 join 的**一对一子实体**有 2+ 行（一对多子表不会 fan-out 到这条查询上）。
- 定位手法（全静态可做）：① `javap -classpath <appId>-facade-<ver>.jar <appId>.dto.<主实体>Dto | grep -E "public .*Dto get"` 里**不带 List 的 getter**（如 `getKuozhanxinxiDto()`）就是一对一的子实体，其余 `getXxxDtoList()` 是一对多；② 该子表 `SELECT parent_id, COUNT(*) FROM <子表> GROUP BY parent_id HAVING COUNT(*)>1` 找出重复；③ 用页面 schema（`udc_page_schema.page_schema`）交叉验证：子实体以内联 `xxxDto.字段` 出现在主表单 dataSource 里、`dataShape=SINGLE` 即为一对一，`dataShape=LIST`+`componentName=重复表录入` 是一对多。
- 修法与边界：数据侧合并/清理重复的一对一行（先备份再删，删后回读）；机制侧让写入方"存在则 update、不存在才 insert"（复制/变更/迁移链路是高发源）；页面/标品侧的降级（取第一条+warn）属平台行为，只能提平台。
- 反例警示：这类报错**不要**先归因到"重号合同/业务编号不唯一"——本案例中 作废数据里 16/34 行合同号为空、`'发起合同自动生成'` 占位 11 行、全库空号 UAT 114 行，但请求体证明条件里根本没有合同号，真因是一对一子表重复。先看请求体再定因。

### 20. `BOOT_4004 违反主键约束`：用 traceId 回放 payload，逐个核对子表行 id 是否已存在

UDC 新增/提交（`.../{pageUrl}/{entityAppName}/{entityName}/{componentId}/create-bpm`）报 `BOOT_4004 / MESSAGE:PRIMARY` 时，冲突通常在**子表**而不是主表：

- 主档 id 由平台流水号服务生成（失败时日志有 `RecycleSerialNumberAppServiceFilter: 需要回收本次产生的流水号, 数据id:[...]`），这行 id 基本不会是冲突点；
- 真正来源：前端表单把子表行的 id（`BaseEntityActionDto(id=..., actionType=INSERT)`）一并提交，服务端**不重生子键**直接 INSERT；同一页面再次提交（重试/改完再提/变更复制带入）会拿**同一个 id** 再插一次 → `Duplicate entry ... for key 'PRIMARY'`。

取证固定三步（全部可复现）：
1. `kubectl logs <pod> --tail=N | grep <traceId>`，从 `表达式content: {<rootEntity>=...}` 那行里抽出所有 `actionType=INSERT` 行的实体字段名与 id；
2. 直连业务库逐个核对该 id 是否已存在，并回查其 `parent_id / create_time`；子表行 id 若指向**另一个合同**（常见是同一账号几分钟前那一次写入残留），即坐实“前端复用旧 id”；
3. 看时间线：同一账号短时间内多次 create-bpm + 同一批子表 id 重复出现 = 前端未重置，重试多少次都撞同一个 key。

解封手段：把那个已存在的子表行（或那条废单的主档+全部子行）删掉释放 id，再由用户重试；根治必须落在“服务端对 INSERT 行重生主键 / 前端提交前清空行 id / 复制变更入口重置源单 id”三者之一。

### P0 SQL 执行前先核现状

"待执行"的修复 SQL 可能已被其他人/CI/环境流程执行过。执行前先查两层现状（`udc_attribute.data_type` + `information_schema.columns.column_type`），全已生效时**不要重复执行**，把结论写进报告（含运行态佐证：Pod 日志 grep 无溢出错误）。backup 表按原方案保留不动。

## 详细案例

见 `references/live-call-harness-and-sample-discovery.md`：LIVE 调用与鉴权形态、用例 JSON + 响应留档 + 字段级审计脚手架、按子表覆盖挑样本的 SQL、孤儿 `parent_id` 判别、报告口径。

见 `references/znxmglpt-config-data-disambiguation-20260914.md`：11075 镜像回归结果、4.16/4.11/4.19/4.20 配置数据翻案样本、4.17 双路径 bug 与 4.14 ID 域不匹配的完整证据链、拼音列名≠语义的取证陷阱。

见 `references/znxmglpt-fix-seed-sql-20260914.md`：4.17 重号档案根因与双文件修复内容、4.21/4.15 造数参数与 LIVE 闭环、P0 SQL 已被执行的核查证据、INSERT 模板行参数化写法。

见 `references/seeyon-microflow-entry-mapping.md`：写/推送类清单项的入口定位法——controller grep 优先、`udc_microflow_info` 列语义与查询、`rest_api` 语义、微流程→实现类映射、UDC 生成物在 facade/biz jar 中的位置与 `@AppService` 接线、汇报口径。

见 `references/udc-query-and-enum-semantics.md
- `references/udc-write-path-pk-conflict.md` — create-bpm/update-bpm 路由选择、id=0 视为空、子行 id 重生条件、违反主键约束取证三步与修法矩阵`：条件键=属性名的反查 SQL 与"0 行"症状、枚举项 `enum_code` vs `item_value` 的安全转换 helper、关联键 ID 域的全量 JOIN 验证法与类型比较陷阱、本地编译校验的三个假象。

浏览器/CDP 侧的飞书表格读取细节（`spread.sheets[i].getValue(row,col)` 0-based 整表快扫、公式栏滞后警告、Canvas/404 陷阱）沉淀在 `references/feishu-responsibility-sweep.md` 的 "Cell readback method" 一节；chrome-profiles skill 同主题内容未纳管（curator adopt 前不可编辑）。
