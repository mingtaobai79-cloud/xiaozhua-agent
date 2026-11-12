#!/usr/bin/env python3
"""INDEX.md 加第 21 格（业务动作索引），并改格数。用脚本写避开 shell 反引号。"""
from pathlib import Path

P = Path("<SEEYON_AGENT_ROOT>/core/facts/INDEX.md")
NEW = (
    "㉑`business-action-index.md` **业务动作索引**（要做什么→调哪个方法：2258 个 AppService 方法"
    "按八类动作归类——查询 1197（按接口聚合）/ 创建 237 / 修改 159 / 删除 137 / 校验 41 / "
    "导入导出 35 / 发布 29 / 流程 22 / 启用禁用 11 / 其他 390；每行给全：动作方法→接口→入参 DTO→"
    "实现类→流转第一步；**覆盖现实**：322 个 AppService 只有 68 个在仓库有实现（46 个在 udc-biz），"
    "517 个方法有实现、370 个能追流转，**BPM/组织/事项/连接器的实现在平台服务端、流转 UNVERIFIED**；"
    "典型速查：`deployNormal`→`DeployNormalDto`→`ApplicationService.deploy`、流程 22 个方法全在 "
    "`BpmAppService`、导入导出对应 `TransportHandler`/`Importable`/`SaveAsHandler` 扩展点）。"
)


def main() -> int:
    t = P.read_text(encoding="utf-8")
    t = t.replace("| standard-product | 20 格平台能力（包用法，环境无关） |",
                  "| standard-product | 21 格平台能力（包用法，环境无关） |")
    if "㉑" in t:
        print("已存在 ㉑，跳过")
        return 0
    anchor = "证据 `docs/audit/artifacts/extension-surface-20261029"
    i = t.find(anchor)
    if i == -1:
        print("ERR: 找不到插入锚点")
        return 5
    t = t[:i] + NEW + t[i:]
    P.write_text(t, encoding="utf-8")
    print("已插入 ㉑")
    j = t.find("㉑")
    print("预览:", t[j:j + 130])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
