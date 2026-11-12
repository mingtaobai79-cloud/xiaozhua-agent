"""C：widgetConfig 逐类型页面实证 —— 打开字段集面板，看每种类型渲染成什么控件。

接口层已经证明 DB 里 widget_config 正确；本脚本验证**页面真的按它渲染**。

判据（不看 DB、不看接口返回，只看 DOM）：
  点开字段集 → 逐行读「控件」列 / 行内控件的 class 与标签
  例如 DATE 应渲染出 date-picker 类、BOOLEAN 渲染 switch、
  ATTACHMENT 渲染 upload、CONTENT 渲染正文编辑器。

用法：
  python tools/core/setting/attribute_widget_page_verify.py --open --set-name <字段集名>
  python tools/core/setting/attribute_widget_page_verify.py --verify
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# 控件 → DOM 判据（哪个选择器/class 出现即算该控件渲染成功）
WIDGET_DOM_HINTS = {
    "Input":            [".ant-input:not(.ant-input-number-input)", "input.ant-input"],
    "InputNumber":      [".ant-input-number"],
    "TextArea":         ["textarea.ant-input", ".ant-input[rows]"],
    "Select":           [".ant-select"],
    "TreeSelect":       [".ant-select", ".ant-tree-select"],
    "CascaderSelect":   [".ant-select", ".ant-cascader-picker"],
    "DatePicker":       [".ant-picker"],
    "DateTimePicker":   [".ant-picker"],
    "TimePicker":       [".ant-picker"],
    "Switch":           [".ant-switch"],
    "Currency":         [".ant-input-number"],
    "UdcReference":     [".ant-select", "[class*=reference]"],
    "Attachment":       [".ant-upload", "[class*=attachment]"],
    "Upload":           [".ant-upload"],
    "UiBusinessContent":[".ant-input", "textarea", "[class*=content]"],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--target-prefix", default="13AF8487")
    ap.add_argument("--app-id", default=None)
    ap.add_argument("--set-name", default="zxjTypeFull")
    ap.add_argument("--open", action="store_true", help="导航到字段集 tab")
    ap.add_argument("--verify", action="store_true", help="读 DOM 判定控件")
    a = ap.parse_args()

    from providers.cdp import CdpClient

    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix}")
        return 2
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=cand[0])

    if a.open:
        # ★ 域名不硬编码：从当前页面 location.origin 取（仓库脱敏铁律，
        #   写死域名会被 tests/test_deidentification.py 判为客户组织 PII）
        origin = c.evaluate("location.origin", await_promise=False)
        url = (f"{origin}/main/child-frame/udc/"
               f"app-design/basic-setting?appId={a.app_id}")
        print("导航到:", url)
        try:
            c.send("Page.navigate", url=url)
        except Exception as e:
            print("  navigate 异常(导航会断连，预期):", type(e).__name__)
        time.sleep(10)
        c.close()
        print("已导航。请手动确认页面停在设计器设置页，然后跑 --verify")
        return 0

    if not a.verify:
        print("\n下一步：在页面上点开「字段集」tab 并选中目标字段集，然后跑 --verify")
        c.close()
        return 0

    # 读当前页面所有可见表格行（字段集面板是表格）
    js = r"""
    (() => {
      const out = [];
      const panes = [...document.querySelectorAll('.ant-tabs-tabpane')]
        .filter(p => p.offsetParent !== null);
      const roots = panes.length ? panes : [document.body];
      for (const root of roots) {
        for (const t of root.querySelectorAll('table')) {
          const head = [...t.querySelectorAll('thead th')].map(x => x.innerText.trim());
          const rows = [...t.querySelectorAll('tbody tr')].map(tr =>
            [...tr.querySelectorAll('td')].map(td => td.innerText.trim()));
          if (rows.length) out.push({head, rows});
        }
      }
      return JSON.stringify(out);
    })()
    """
    raw = c.evaluate(js, await_promise=False)
    try:
        tables = json.loads(raw)
    except Exception:
        print("读表格失败:", str(raw)[:200])
        c.close()
        return 3

    print(f"可见表格 {len(tables)} 个")
    for i, t in enumerate(tables):
        print(f"\n[{i}] head: {t['head']}")
        for r in t["rows"][:30]:
            print("   ", " | ".join(r)[:150])

    # 控件类名统计（判断渲染出的控件种类）
    stat = c.evaluate(r"""
    (() => {
      const panes = [...document.querySelectorAll('.ant-tabs-tabpane')]
        .filter(p => p.offsetParent !== null);
      const root = panes.length ? panes[0] : document.body;
      const cls = ['ant-input-number','ant-picker','ant-switch','ant-upload',
                   'ant-select','ant-cascader-picker','ant-tree-select'];
      const out = {};
      for (const k of cls) out[k] = root.querySelectorAll('.' + k).length;
      return JSON.stringify(out);
    })()
    """, await_promise=False)
    print("\n控件类名命中:", stat)
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
