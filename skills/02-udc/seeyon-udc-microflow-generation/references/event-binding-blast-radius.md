# 事件微流程绑错实体的爆炸半径

建/改事件类微流程时要先看清楚绑到哪个实体的哪个事件上——选错的代价不是“这个微流程不生效”，
而是**目标实体的所有写入全部静默失败**。

## 症状（极容易被误判成代码 bug）

- 业务接口返回“新建失败：null”或“保存失败：null”（平台 `message` 字段本来就是 null）。
- 库里 0 行，代码里没有任何异常，业务代码的 `beforeCreate/afterCreate` 是空实现。
- 换个接口同实体也一样失败；换别的实体则正常。

## 定位链

1. 响应体取 `traceId`。
2. 服务日志按 traceId 过滤：`kubectl logs <pod> | grep <traceId>`。
3. 找形如 `Exception thrown by subscriber method onAfterCreateEvent(...) on subscriber ...microflow.EvtXxxListener` 的行，
   以及紧随的 `AppService Exception Occur, CODE:UDC_MICROFLOW_RUNTIME_0001`。
4. 拿 listener 名反查微流程：`SELECT id,name,caption,data_schema FROM <udc schema>.udc_microflow_info WHERE name='evtXxx'`，
   看 `data_schema` 里的 `input.id`——形如 `<entity>.com.seeyon.udc.common.event.AfterCreateEvent`，
   这就直接给出了绑定实体与事件。

**注意**：绑定关系**不在** `udc_event` 表里（那张表只有显式建的 5 条事件，查它一定查空）。
也别只 grep 控制器/服务代码，钩子是从实体元数据派发的，代码里看不到绑定。

## 处置

不要擅自停用别人的微流程（可能有人在用）。把三件事报给用户让他决定解绑还是停用：
哪个微流程、绑的是哪个实体的哪个事件、以及“这看起来是 A 业务的逻辑挂到了 B 实体上”（例如“收票状态复刻”“备货核算复刻”
挂在数据源实体的 AfterCreate 上）。

停用/解绑后才做写入验证——依赖这个实体写入的验收项，在绑定修好前一律记 BLOCKED，不要记 FAIL 代码缺陷。

## 预防

建事件微流程时先回读一次 `data_schema` 里的 `input.id`，确认实体与事件都对，再发布。
发布后拿一次最小的真实写入（新建一条再删掉）验证该实体仍能正常写——如果新建失败但日志里没异常，先怀疑自己刚绑的微流程。

横跨任意平台的同类排查（入参丢字段 / 子表标记 / 钩子回滚四层）见 `webapp-write-api-audit` 技能。
