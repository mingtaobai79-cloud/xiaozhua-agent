"""可复用性闸门：tools 脚本不许写死 appId / 端口默认值。

为什么
------
2026-10-23 审计：`tools/core/**` 下 16 个脚本各自写死
`APP_ID = "<19 位数字>"`，其中一个文件里出现 11 次。
后果不是"不好看"，是：
  · 换个应用要改代码，改了还容易漏（11 处里漏一处就写错应用）
  · appId 是"某次实测的目标"，写进代码等于把测试值当配置
  · 用户实际踩到的是更糟的形态：**第一步取 appGuid 就卡住**

规则
----
tools 脚本必须通过 `--app-id` 或 `SEEYON_APP_ID` 拿 appId，
**不允许出现默认 appId**（默认值写错应用比报错危险得多）。

例外（白名单，逐个说明理由）：
  _fixtures/live_targets.py   LIVE 测试目标坐标的集合处，本身就是"某次实测的目标"
  证据注释/evidence 目录      实测记录，写的是"当时在哪个 app 上验证过"
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

TOOLS = ROOT / "tools"
APPID = re.compile(r"\b\d{17,20}\b")

# 允许出现的文件（相对 tools/）
ALLOW = {
    "core/_fixtures/live_targets.py",   # 测试锚点集合处，用途明确
}

# 允许出现的行级形态：证据注释 / 证据常量 / 文档示例
LINE_OK = re.compile(
    r"(LIVE\s*[(（]|证据|evidence|EVIDENCE|实测|示例|example|app=|<appId>|"
    r"APP_ID\b.*不含|不要写死)")

# 判 appId 的强特征：这些上下文里出现的长数字才算 appId
# ★ 不能只看"19 位数字" —— 微流程 id、实体 id 也都是这个量级，
#   它们写在 MFS = {1734035400068212199: '...'} 这类证据表里是完全正常的
_NUM = r"\d{17,20}"
APP_ID_CONTEXT = re.compile(
    "|".join([
        r"appId\s*[:=]\s*[\"']?\{?" + _NUM,   # appId=... / "appId": "..."
        r"APP_ID\s*=\s*[\"']" + _NUM,          # APP_ID = "123..."
        r"--app-id\s+[\"']?" + _NUM,           # 命令行示例
        r"\bapp_id\s*=\s*[\"']?" + _NUM,       # SQL 里 app_id=数字
    ]))


def py_files():
    for p in TOOLS.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        yield p


def test_tools_have_no_hardcoded_app_id():
    bad = []
    for p in py_files():
        rel = p.relative_to(TOOLS).as_posix()
        if rel in ALLOW:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8",
                                             errors="replace").splitlines(), 1):
            if not APP_ID_CONTEXT.search(line):
                continue
            if LINE_OK.search(line):
                continue
            if line.lstrip().startswith("#"):
                continue
            bad.append("%s:%d  %s" % (rel, i, line.strip()[:90]))
    assert not bad, "tools 脚本写死 appId（改用 --app-id / SEEYON_APP_ID）:\n  " + \
                    "\n  ".join(bad[:12])


def test_tools_reject_default_app_id():
    """★ 反模式：`add_argument("--app-id", default="<19位>")` 比不传更糟 ——
    看起来参数化了，实际仍在用某个特定应用。"""
    bad = []
    for p in py_files():
        txt = p.read_text(encoding="utf-8", errors="replace")
        if re.search(r'add_argument\("--app-id"[^\n]*default="\d{15,}"', txt):
            bad.append(p.relative_to(TOOLS).as_posix())
    assert not bad, "这些脚本的 --app-id 带死默认值: %s" % bad


def test_env_entry_exists():
    assert (ROOT / "tools" / "core" / "_env.py").is_file()


def test_env_refuses_to_guess_app_id():
    """公用入口不能自己编一个 appId 出来。"""
    from tools.core._env import EnvError, resolve_app_id

    try:
        resolve_app_id(None)
    except EnvError as exc:
        assert "appId" in str(exc) and "SEEYON_APP_ID" in str(exc)
    else:
        raise AssertionError("缺 appId 应抛 EnvError，不能给默认值")


def test_env_rejects_non_numeric_app_id():
    from tools.core._env import EnvError, resolve_app_id

    try:
        resolve_app_id("abc")
    except EnvError as exc:
        assert "纯数字" in str(exc)
    else:
        raise AssertionError("非数字 appId 应被拒")


def test_env_accepts_valid_app_id():
    from tools.core._env import resolve_app_id

    assert resolve_app_id("9000000000000000001") == "9000000000000000001"


def test_env_optional_mode_returns_none():
    """平台级脚本（不针对某应用）允许不传。"""
    from tools.core._env import resolve_app_id

    assert resolve_app_id(None, required=False) is None


def test_tools_load_env_from_one_place():
    """不许每个脚本自己抄一遍 8 行 .env 解析。"""
    dup = []
    for p in py_files():
        txt = p.read_text(encoding="utf-8", errors="replace")
        # 自解析 .env 的特征写法
        if 'if "=" in line and not line.startswith' in txt:
            if p.name != "_env.py":
                dup.append(p.relative_to(TOOLS).as_posix())
    assert not dup, ("这些脚本各自复制了 .env 解析，请改用 tools.core._env.load_env: %s"
                     % dup[:8])
