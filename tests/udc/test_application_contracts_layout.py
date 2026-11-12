"""docs/operation-contracts/udc/application/ 的域入口必须与磁盘和 registry.py 一致。

这个域此前零入口（上级总表标 ❌）。补入口时撞出三件事，都必须被守住：

① `registry-entries.md` 自称「本任务不改 registry.py（冻结）」——实测 5/5 早已落库。
   不守的话，后人会把它当待办去"照抄"。
② `udc.deployment.app_online` 在 registry.py 里**整个命名空间都不存在**。
   这不是漂移，是该 op 自己写着「test2 当前无可用 appId 来源」。
   不守的话，后人会当漂移去"修"——修就是给一条进不去的写面注册 key。
③ `udc.sandbox.flexible.test_status` 在 registry 里掉了 `udc.` 前缀。
   按名字 grep 会误判「未落库」，按路径才能对上。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "application"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/application/README.md（域入口）"
    return p.read_text(encoding="utf-8")


def _contracts():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def test_table_matches_disk():
    """表里的字节/行数必须与磁盘一致，且 7 份契约一份不漏。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 7, "规模表解析出 %d 行（应有 7 份契约，不含本 README）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        f = D / name
        if not f.is_file():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        raw = f.read_bytes()
        size, lines = len(raw), len(raw.decode("utf-8").splitlines())
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d B" % (name, size_s, size))
        if lines != int(lines_s):
            bad.append("%s: 表写 %s 行 磁盘 %d 行" % (name, lines_s, lines))
    assert not bad, "契约规模表已腐坏：\n  " + "\n  ".join(bad)


def test_every_contract_is_listed():
    """目录里每份契约都必须被入口提到——否则有人加了新契约就悄悄成了孤岛。"""
    text = _readme()
    missing = [f.name for f in _contracts() if f.name not in text]
    assert not missing, "这些契约没在域入口 README 里出现：%s" % missing


def test_registry_entries_already_landed():
    """① 「供 UDC-MERGE 照抄」是过去时——5/5 已落库，必须写成表且数字为真。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    entries = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    keys = sorted(set(re.findall(r'contracts\["([a-z0-9_.]+)"\]', entries)))
    assert keys, "registry-entries.md 里没有 contracts[...] 字面量，解析口径变了"
    landed = [k for k in keys if '"%s"' % k in reg]
    assert len(landed) == len(keys), (
        "registry-entries.md 声称可以照抄的 %d 条里，只有 %d 条在 registry.py：缺 %s"
        % (len(keys), len(landed), [k for k in keys if k not in landed]))

    text = _readme()
    m = re.search(r"该文件列出的 `contracts\[\.\.\.\]` 条数 \|\s*(\d+)", text)
    assert m, "README §二 找不到「该文件列出的 contracts[...] 条数」这一行"
    assert int(m.group(1)) == len(keys), (
        "README 写 file 列 %s 条，实测 %d 条" % (m.group(1), len(keys)))
    assert "5 / 5" in text or "**5 / 5**" in text, "README 没写清「5 / 5 已落库」"
    assert "别把它当待办" in text, "README 没点明「别当待办去照抄」"


def test_app_online_namespace_is_absent_by_design():
    """② app_online 的命名空间在 registry.py 里不存在，且 README 必须说「这是正确状态」。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    assert "app_online" not in reg, (
        "registry.py 里出现了 app_online —— 若真的注册了，README §三① 的"
        "「docs 有、registry 无是正确状态」已成假话，必须同步改写")
    text = _readme()
    for token in ("udc.deployment.app_online", "零命中", "正确状态"):
        assert token in text, "README §三① 缺「%s」——后人会把这个命名空间差异当漂移去修" % token
    # 那条契约自己必须仍在声明「当前无可用 appId 来源」
    online = (D / "udc-app-online-contract.md").read_text(encoding="utf-8", errors="replace")
    assert "无可用 appId 来源" in online, (
        "udc-app-online-contract.md 不再声明「当前无可用 appId 来源」——"
        "那 README 里「不是遗漏」的整段推理失去依据")


def test_prefix_dropped_key_documented():
    """③ sandbox.flexible.test_status 在 registry 里掉了 udc. 前缀，必须写明。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    assert '"sandbox.flexible.test_status"' in reg, (
        "registry.py 里已不是 sandbox.flexible.test_status —— README §三② 过期")
    assert '"udc.sandbox.flexible.test_status"' not in reg, (
        "registry.py 里出现了带 udc. 前缀的版本 —— README §三② 的「掉了前缀」已不成立")
    text = _readme()
    assert "sandbox.flexible.test_status" in text, "README §三② 没点名这个 key"
    assert "掉了" in text and "前缀" in text, "README §三② 没说明是前缀缺失"


def test_no_customer_identifiers():
    """入口文件不许出现客户应用名/域名（脱敏面）。"""
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
