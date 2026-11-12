# 上移/下移/跨分组 = udcEntityBatchUpdateEntityGroupIdAndOrdernoPost

- op: udcEntityBatchUpdateEntityGroupIdAndOrdernoPost (mutation, body 数组)
- params0: [{id, appId, name, caption, stereotype, features, entityGroupId, orderNo}, ...]（全量替换语义，元素必填链同 udcEntityPost：appId/name/caption/stereotype/features/entityGroupId/orderNo 全要）
- 缺 appId/name/caption → BOOT_1001 逐字段报；缺 stereotype → BOOT_1001 业务版型选一不能为空
- LIVE PASS：交换两实体 orderNo → 回读互换成功；复原 → 回读还原。content=影响条数。
- 右键菜单「上移/下移」即前端调本 op；「移动到分组」同 op 改 entityGroupId。
