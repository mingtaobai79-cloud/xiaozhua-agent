"""批量写节点（已合并到 microflow_nodes_extra，本模块只转发）。

★ 2026-11-02 更正记录
本模块原先自己实现 create_batch_entity / change_batch_entity，形态是
`attrs` + `output = DTO 数组`。全仓 95 个样本实测（含真实业务流
r44_e1_orig、真实前端抓包 real-type0-node-structures）：

  - 带 attrs 的样本：**0 个**
  - 真实出参：`dataType=INTEGER / type=OBJECT / desc="批量更新…成功的数量_1"`

即批量节点不做字段映射（值来自列表元素本身），出参是影响行数而非 DTO 数组。
原实现会生成平台不接受的形态，且与 extra 里的正确实现重复 —— 两套并存
意味着「导入哪个模块」决定生成对不对，这是不该存在的分叉。

保留文件名是为了不打断按模块名扫描的工具（tools/microflow_coverage.py）。
"""
from __future__ import annotations

from .microflow_nodes_extra import (  # noqa: F401
    change_batch_entity,
    create_batch_entity,
)

__all__ = ["create_batch_entity", "change_batch_entity"]
