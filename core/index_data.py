"""平台索引数据的定位（签名库 / 表面索引）。

为什么需要这一层
----------------
签名库（`signatures.txt.gz`）和表面索引（`surface-index.tar.gz`）是**随产品发行的数据**，
但历史上它们躺在 `docs/audit/` 底下 —— 而 `docs/` 是工作区（审计报告、客户证据），
安装时被 `installer/selfupdate.py::IGNORE_DIRS` 整个排除。

0.2.7 收紧安装树之后，`xiaozhua_platform_class_search` 在装机环境里直接报
「signatures.txt.gz 不存在（缺件，索引不可用）」——因为代码只认 `docs/audit/`。

定位顺序（先发行位置，后工作区旧位置）
--------------------------------------
1. `$XIAOZHUA_INDEX_DIR/<name>`         显式覆盖（容器/多版本并存时用）
2. `<src>/fixtures/reference/<name>`    发行树里的正式位置（随产品走，installed 也有）
3. `<src>/docs/audit/<name>`            工作区旧位置（开发机上常有）
4. `<src>/docs/audit/reference/<name>`  参考包位置
5. `~/.xiaozhua/data/<name>`            用户自备/热更新

拿不到时**不要只说「缺件」** —— 要告诉调用者三条自修路径。
"""
from __future__ import annotations

import os
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]


def candidates(name: str) -> list[Path]:
    out: list[Path] = []
    env_dir = os.environ.get("XIAOZHUA_INDEX_DIR")
    if env_dir:
        out.append(Path(env_dir) / name)
    out += [
        _SRC / "fixtures" / "reference" / name,
        _SRC / "docs" / "audit" / name,
        _SRC / "docs" / "audit" / "reference" / name,
        Path.home() / ".xiaozhua" / "data" / name,
    ]
    return out


def resolve(name: str) -> Path | None:
    """返回第一个存在的候选路径；都没有则 None。"""
    for path in candidates(name):
        if path.is_file():
            return path
    return None


def missing_message(name: str, what: str = "离线索引") -> str:
    tried = "\n".join(f"  - {p}" for p in candidates(name))
    return (
        f"{what}缺件：{name} 未找到。已尝试：\n{tried}\n"
        "修法（任一）：\n"
        "  1) `xiaozhua update` 重新同步发行树（0.2.8+ 已把索引放进 fixtures/reference/）\n"
        f"  2) 从源码仓 `fixtures/reference/{name}` 复制到 `~/.xiaozhua/data/{name}`\n"
        "  3) 设 `XIAOZHUA_INDEX_DIR` 指向含有该文件的目录"
    )