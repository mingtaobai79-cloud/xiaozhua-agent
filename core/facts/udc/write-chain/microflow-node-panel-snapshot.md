# UDC 微流程节点面板快照 —— 事实证据采集法（17 节点全量）

> 2026-10-16。目的：每个节点的**面板实际渲染内容**作为事实证据落盘，支撑"生成的每份都对"。

## 为什么需要
服务端 `checkSchema` 只做结构校验；面板红字/必填/候选匹配是**前端独立判定**。
两端不一致的实例（本轮实测）：
- 服务端 check=true 但面板红字「所选"可投递的事件"已失效」
- 服务端 check=true 但面板显示外部实体名（`nodeInfo.entityCaption="华为通知单"`）

## 采集法（dumpnodes.js）
1. CDP 新开 tab 打开编辑器 → 点「流程」tab（`Target.createTarget` 不动用户页面）
2. 遍历节点 caption 列表，逐个派发 `mousePressed/mouseReleased/click` 到节点卡片
3. 读右侧配置面板：`[class*="side-setting"|"setting-panel"|"node-config"|"drawer"|"config-panel"]`，宽 260–1100
4. 提取 `innerText` 全文 + 红字正则 + 输入值；Escape 关闭，下一个
5. 落盘 `scratch/nodes_panel_dump.json`

**红字正则**：`所选[^，。\n]{0,45}(失效|已变更|已删除)|不能为空|请输入|请选择[^，。\n]{0,16}|必填`

## 本轮结果（17 节点，落库态 FIXED20）

| 节点 | 红字 |
|---|---|
| 创建变量(1) / 查询单条数据(1) / 创建列表(1) / 修改列表(1) / 列表操作(1) | 0 |
| 创建映射组(1) / 映射操作(1) / 数据转换(1) / 修改变量(1) | 0 |
| 更新数据(1) / 批量更新数据(1) / 插入数据(1) / 删除数据(1) | 0 |
| 类型转换(1) / 子微流程(1) / 自定义服务(1) / 事件投递(1) | 0 |

（分支节点为容器节点，不在 ACTIVITY 面板采集范围内。）

## 发现的真实残留（已修）
`CHANGE_LIST` 节点 `selectParam.nodeInfo.entityCaption` 与 `dataSource.nodeInfo.entityCaption` = **"华为通知单"**（外部应用实体名）。
- 该值不影响服务端 check，但**面板会直接显示**（"实验列表数据[华为通知单]"），是用户可见的错误。
- 修复：全树 `entityCaption` 归一为本应用实体 caption（FIXED20，check errors=0，content=1）。
- **铁律**：`nodeInfo.entityCaption` 必须随实体选择一起归一化；只改 output/id/fullName 不够。

## 残留扫描口径（全树 JSON 文本）
`entityCaption` 逐节点比对 + 14 类业务词表：华为/通知单/合同/框架/账单/应收/投标/报备/营销/返点/核算/虹易/考勤/考核/智能/数字营销。

## 采集脚本
`scratch/dumpnodes.js`（17 节点一次跑完，约 3 分钟）。
