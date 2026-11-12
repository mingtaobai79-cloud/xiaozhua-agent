# 逐节点开面板审计（UDC 微流程编辑器，Edge CDP）

目的：核对每个节点的面板实况（选择服务、参数映射是否赋值、出参是不是“未命名”），
而不是只看画布文字或 checkSchema 返回值。

## 关键事实

- 编辑器 URL：`/main/child-frame/udc/app-design/rule/microflow/editor/<microflowId>?appId=<appId>`。
- 节点容器：`.udc-microflow-editor-node-container`，**id 就是 nodeId**（如 `CALL_APP_SERVICE_uJE4Br`）。
- **单击（合成 click 或单次真实点击）都不会弹面板**。合成 `MouseEvent` 一律无效；真实鼠标事件必须 `clickCount=2` 双击。
- 节点常在画布视口外（`getBoundingClientRect().x` 为负），必须先 `scrollIntoView({block:'center',inline:'center'})` 再取中心坐标，否则点击落到别处。
- 面板 = Ant Drawer：`.ant-drawer-content-wrapper`，含 `ant-drawer-content-wrapper-hidden` 就是没打开；内容在 `.ant-drawer-body`，标题在 `.ant-drawer-title`。关闭用 `.ant-drawer-close`。
- 若点开但 `.ant-drawer-title` 是「自定义错误」等别的节点名，说明坐标打偏，该节点结果作废，不要当成“已验证”。

## 可复用步骤

```python
from providers.cdp import CdpClient
c = CdpClient(9250, allow_network=True, timeout=600); c.connect()

pos = c.evaluate("""(()=>{const el=document.getElementById('NODE_ID');
  el.scrollIntoView({block:'center',inline:'center'});
  const r=el.getBoundingClientRect();
  return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});})()""")
for cc in (1, 2):
    c.send('Input.dispatchMouseEvent', type='mousePressed',  x=p['x'], y=p['y'], button='left', clickCount=cc)
    c.send('Input.dispatchMouseEvent', type='mouseReleased', x=p['x'], y=p['y'], button='left', clickCount=cc)
```

读面板：

```js
(()=>{const w=document.querySelector('.ant-drawer-content-wrapper');
 const b=document.querySelector('.ant-drawer-body');
 return JSON.stringify({hidden:w?w.className.includes('hidden'):true,
   body:b?(b.innerText||''):''});})()
```

判读规则：面板出现 `所选数据已失效 / 请重新选择 / 空值 / 未命名的参数` = 该节点映射或出参有问题；
参数名右侧没有任何值框内容 = 没赋值。

## 整个流程的检查面

点顶部「检查」后读 `.ant-table-tbody tr`，每行 `类型|模块元素|错误代码|错误信息`。
它与 `udcMicroflowCheckSchemaUpdatePost` 不是同一层：后者 check:true 仍可能被 UI 检查报
`UDC_MICRO_FLOW_04004`（前序节点变更 / 依赖应用已删除 / 生单规则已被删除）。两个都要看。
