# 微流程编辑器「查看模式」陷阱 —— 假通过的真凶

## 现象

点「保存并提交」→ 无任何报错 → 接口全 200：

```
udcMicroflowCheckSchemaUpdatePost  200
udcMicroflowFindByIdGet            200
udcMicroflowSearch                 200
udcMicroflowDisableNodePost        200
udcMicroFlowGroupSelectByTypePost  200
```

前端画布上表达式、条件、节点全都正常显示。
**但后端 `dataSchema` 回读，分支的 conditions 是空的，表达式根本没存进去。**

## 根因

页面打开时处于**查看模式**，顶部有提示弹窗：

```
提示
您现在处于查看模式，所有的修改都无法被保存
[进行编辑]  [继续查看]
```

- 查看模式下，**所有 UI 编辑操作照常生效，画布正常变化，节点抽屉正常提交**
- 但「保存并提交」只走只读路径，不写库
- 唯一提示是打开页面时那个 modal，一旦点掉就再也看不到
- 点掉 modal 后没有任何持续标识，DOM 里也查不到模式标记

这是一个**静默失败**：所有信号都显示成功，实际零写入。

## 判定方法（必须做）

**永远不要相信「保存并提交」的成功提示，必须后端回读比对。**

```python
backend = read_schema(mid)        # udcMicroflowFindByIdGet
frontend = store.flowNodes        # 前端
# 逐节点比对 actionType / caption / output.name / expression / condition
```

本次实测差异：

| 项 | 前端 | 后端 |
|---|---|---|
| 分支节点 | 有 | 有 ✓ |
| ifBranch 表达式 | 有（卡片显示完整表达式） | **无** ✗ |
| RETRIEVE condition | 有 | 有 ✓ |
| RETRIEVE nullHandling | TERMINATION | TERMINATION ✓ |

→ 说明「带抽屉确认」的节点（RETRIEVE）写进去了，
「画布内联配置」的节点（BRANCH 表达式）没写进去。
但更深一层：查看模式下连 RETRIEVE 都可能是上次编辑模式时存下的旧数据。

## 恢复编辑模式

```js
// 弹窗里点「进行编辑」
const m = [...document.querySelectorAll('.ant-modal')].find(x => (x.textContent||'').includes('查看模式'));
const b = [...m.querySelectorAll('button')].find(x => (x.textContent||'').trim() === '进行编辑');
b.click();
```

编辑模式下 frame 会重新加载（分支节点 id 会变，如 `BRANCH_uCjtD5` → `BRANCH_CGZ2GI`）。

## 防范规则

1. **每次进入编辑器，第一件事：检查是否有「查看模式」弹窗，有就点「进行编辑」**
2. 保存后必须后端回读，逐节点比对，不能看提示
3. 分支这类「画布内联配置」的节点，确认后不会立刻走 `udcMicroflowUpdatePost`，
   必须靠流程级「保存并提交」才会写库 → 更容易被查看模式吞掉

## 检测脚本

```python
# 探针：是否有查看模式弹窗
def in_view_mode(d):
    return d.eval(r"""
    (() => {
      const m = [...document.querySelectorAll('.ant-modal')]
        .find(x => (x.textContent||'').includes('查看模式'));
      return m ? 1 : 0;
    })()""") == 1

def enter_edit_mode(d):
    r = d.eval(r"""
    (() => {
      const m = [...document.querySelectorAll('.ant-modal')]
        .find(x => (x.textContent||'').includes('查看模式'));
      if (!m) return 'not in view mode';
      const b = [...m.querySelectorAll('button')]
        .find(x => (x.textContent||'').trim() === '进行编辑');
      if (!b) return 'no btn';
      b.click();
      return 'ok';
    })()""")
    time.sleep(4)
    return r
```
