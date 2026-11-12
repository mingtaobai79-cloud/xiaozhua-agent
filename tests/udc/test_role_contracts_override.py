"""角色域契约的「撤回记录不许被整理掉」闸门。

为什么它值得单独一条：
`docs/operation-contracts/udc/role/write-chain.contract.md` 是全仓**唯一一份
「主动撤回自己此前结论并写明理由」**的契约（17 处更正标记）。而它的 6 条撤回里，
有三条会直接让人做错事：

  ① `role-auth-all` 不传 code → 空数组 被当成「该角色无授权」
     —— 实测三种结果都出现过（413 项 / 0 行 / 11 角色），**取不到不报错**。
  ② `create-system-admin` 曾被标 STATIC「未调用」
     —— 实际进页面就自动调 3 次，且 **DB 一行没变**（被调用过 ≠ 建了东西）。
  ③ 「进角色权限页是只读观测」—— **不存在只读观测**。

⇒ 这条闸门守的是「撤回记录不许被清掉」，而**清理撤回记录正是"让文档看起来干净"最自然的做法**。
   它是方法论第 64 条（删掉「我错了」比删掉任何结论都危险）的机器版。

只读，不写。不校验字节数（字节数由入口自己的表守）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "docs").is_dir() and (ROOT / "tests").is_dir(), (
    "ROOT 解析错了：%s 不是仓库根（parents 层数写错？）" % ROOT)
D = ROOT / "docs" / "operation-contracts" / "udc" / "role"
CONTRACT = D / "write-chain.contract.md"
README = D / "README.md"


def _contract() -> str:
    assert CONTRACT.is_file(), "角色域契约不见了：%s" % CONTRACT
    return CONTRACT.read_text(encoding="utf-8", errors="replace")


def _readme() -> str:
    assert README.is_file(), "角色域入口不见了：%s" % README
    return README.read_text(encoding="utf-8", errors="replace")


def test_withdrawals_are_still_in_the_contract():
    """6 条撤回的**锚点**必须都还在正文里。删任何一条，闸门红。"""
    t = _contract()
    must = {
        "409 条与 DB 互证 已撤回": r"409 条与 DB 互证.*已撤回|原「与 DB rr_app=409 互证」已撤回",
        "必填静默拦截 已撤回（DECISION-19）": r"必填静默拦截.*已被撤回|DECISION-19.*撤回",
        "引用纪律：不能只 grep 命中处": r"引审计件不能只 grep 命中处",
        "role-auth-all 无 code 假阴性": r"假阴性",
        "create-system-admin 原 STATIC 是错的": r"原写 STATIC「未调用」是错的",
    }
    missing = [name for name, pat in must.items() if not re.search(pat, t, re.S)]
    assert not missing, (
        "这些撤回记录/纪律不见了 —— 它们正是这份契约最值钱的部分：\n  "
        + "\n  ".join(missing))


def _endpoint_row(n: int):
    """从 15 端点总表里取出第 n 行，解析成列。"""
    t = _contract()
    row = next((l for l in t.splitlines() if re.match(r"^\| %d \|" % n, l)), None)
    assert row, "契约的 15 端点总表里找不到第 %d 行 —— 表格格式变了？" % n
    return [c.strip() for c in row.split("|")]


def test_role_auth_all_is_not_upgraded_to_live():
    """#12 不许记 ✅ LIVE（「有回包 ≠ 结论成立」）。

    历史：该行曾写 `**LIVE**`，而 L159 汇总与 §8.6 都写 `⚠️ 部分 LIVE` ——
    **同一份文件三处口径不一致**。第 58 轮已统一为 ⚠️。
    """
    cols = _endpoint_row(12)
    level = cols[5]
    assert "部分 LIVE" in level, (
        "#12（role-auth-all）的等级列是 %r —— 它的结论曾错并被撤回，"
        "按「有回包 ≠ 结论成立」只能记 ⚠️ 部分 LIVE" % level)
    assert "**LIVE**" != level, "#12 被改回 **LIVE** 了"
    # 汇总行必须同口径
    t = _contract()
    assert re.search(r"✅ LIVE 只有 4 个", t), "「✅ LIVE 只有 4 个」这句不见了"


def test_endpoint_levels_agree_across_three_places():
    """总表 / 汇总行 / §8.6 三处对 #12 的说法必须一致。

    这是本轮的真实事故：总表写 LIVE、汇总写「#12 结论曾撤回」、§8.6 写「⚠️ 部分 LIVE，不记 ✅」。
    """
    t = _contract()
    summary = next((l for l in t.splitlines() if "✅ LIVE 只有" in l), None)
    assert summary, "找不到 LIVE 汇总行"
    assert "#12 结论曾撤回" in summary, "汇总行没标 #12 —— 三处口径又分叉了"
    assert "⚠️ 部分 LIVE，不记 ✅" in t, "§8.6 的口径句不见了"


def test_create_system_admin_not_marked_uncalled():
    """#15 不许记回 STATIC「未调用」—— 它被页面自动调用 3 次。

    ⚠️ 判据坑：这一行的等级列**故意**含「原写 STATIC「未调用」是错的」这句更正记录，
    所以不能在整行里搜「未调用」（那样会永远红）。只能看**等级列里是否以 STATIC 开头**。
    （这正是方法论第 70 条：更正记录与结论必须分栏，判据也必须分栏取。）
    """
    cols = _endpoint_row(15)
    level = cols[5]
    assert not level.startswith("**STATIC"), (
        "#15（create-system-admin）被写回 STATIC 了 —— 它实际是页面加载自动调用 3 次"
        "（BOOT_0000 / data.content:1），调用前后 DB 计数一致")
    assert "部分 LIVE" in level, "#15 应记 ⚠️ 部分 LIVE，实际等级列是 %r" % level
    # 更正记录必须仍在（不许把人"修"出去）
    assert "原写 STATIC「未调用」是错的" in cols[6] or "原写 STATIC「未调用」是错的" in level, (
        "#15 的更正记录被删了 —— 它记录了「被调用过 ≠ 建了东西」这条教训")


def test_readme_carries_the_correction_table():
    """入口必须有 §〇★ 更正表 + 那条引用纪律；否则读者只能顺序读到撤回段。"""
    t = _readme()
    assert "〇★" in t, "入口缺 §〇★ 更正索引（这是本轮的产物）"
    for needle, why in [
        ("假阴性", "① role-auth-all 无 code 的假阴性"),
        ("被调用过 ≠ 建了东西", "② #15 被调用但不生效"),
        ("不存在只读观测", "③ 进页面即写"),
        ("409", "④ 409 条口径撤回"),
        ("DECISION-19", "⑤ 必填静默拦截撤回"),
        ("有回包 ≠ 结论成立", "⑥ #12 等级口径"),
        ("引审计件不能只 grep 命中处", "引用纪律"),
    ]:
        assert needle in t, "入口缺：%s（%s）" % (why, needle)


def test_entry_declares_single_file_and_sizes():
    """入口声明的「1 份 / N B / M 行」必须与磁盘一致（这份是单文件域，容易漂）。"""
    t = _readme()
    m = re.search(r"1 份 / ([\d,]+) B / (\d+) 行", t)
    assert m, "入口缺「1 份 / N B / M 行」规模声明"
    size, lines = int(m.group(1).replace(",", "")), int(m.group(2))
    real_size = len(CONTRACT.read_bytes())
    real_lines = len(_contract().splitlines())
    assert (size, lines) == (real_size, real_lines), (
        "入口声明 %s B / %d 行，磁盘 %d B / %d 行" % (size, lines, real_size, real_lines))


def test_gate_bites_when_withdrawal_is_removed():
    """变异用例：把「409 已撤回」的两种写法都抹掉后，第 1 条断言必须变红。

    教训（本轮踩到）：§8.3 与 L462 各有一句撤回，**只抹一处不会变红** ——
    说明"撤回记录"是多点冗余的；变异用例必须抹到判据真的失效。
    """
    gutted = re.sub(r"409 条与 DB 互证", "", _contract())
    gutted = re.sub(r"原「与 DB rr_app=409 互证」已撤回", "", gutted)
    still = re.search(r"409 条与 DB 互证.*已撤回|原「与 DB rr_app=409 互证」已撤回", gutted, re.S)
    assert not still, "变异用例失效：两种写法都抹掉后断言仍通过 —— 判据写错了"
