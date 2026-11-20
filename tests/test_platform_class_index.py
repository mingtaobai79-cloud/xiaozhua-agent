"""平台后端全量类索引：规模、中文检索、不臆造。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.construction.platform_class_index import (  # noqa: E402
    TOKEN_ZH, _bucket, _tokenize, _zh_of, methods_of, search, stats,
)


def test_index_scale():
    """★索引规模必须覆盖 util/AppService/SPI 三类，不能只有几百个。"""
    s = stats()
    assert s["classes"] > 2000, s
    assert s["methods"] > 20000, s
    for b in ("util", "appservice", "spi"):
        assert s["byBucket"].get(b, 0) > 100, (b, s["byBucket"])


def test_boot_util_covered():
    """★com.seeyon.boot.util 必须有覆盖（原来 176 类 0 记录）。"""
    r = search(pkg="com.seeyon.boot.util", limit=200)
    assert r["total"] >= 100, r["total"]


def test_json_utils_found_by_class_name():
    r = search("JsonUtils")
    assert r["total"] >= 1
    names = [h["name"] for h in r["hits"]]
    assert "com.seeyon.boot.util.JsonUtils" in names, names[:5]


def test_json_utils_found_by_chinese():
    """★中文「JSON」必须能查到 JsonUtils，且排在前面。"""
    r = search("JSON", limit=5)
    assert r["total"] >= 1
    names = [h["name"] for h in r["hits"]]
    assert any("JsonUtils" in n for n in names), names


def test_date_chinese_finds_date_utils():
    r = search("日期", limit=5)
    assert r["total"] >= 1
    assert r["hits"][0]["simple"] == "DateUtils", r["hits"][0]


def test_date_utils_methods():
    m = methods_of("com.seeyon.boot.util.DateUtils")
    assert m["total"] > 40, m["total"]
    names = [x.get("name") for x in m["methods"]]
    for expect in ("format", "parse", "addDay", "getFirstDayInMonth"):
        assert expect in names, expect


def test_json_utils_methods_with_signature():
    """方法必须带入参/返回类型，不能只有名字。"""
    m = methods_of("com.seeyon.boot.util.JsonUtils")
    by_name = {x.get("name"): x for x in m["methods"] if x.get("name")}
    assert "toJson" in by_name
    assert by_name["toJson"]["returns"] == "java.lang.String"
    assert "fromJson" in by_name


def test_cache_chinese():
    r = search("缓存", limit=5)
    assert r["total"] >= 1
    assert any("Cache" in h["simple"] for h in r["hits"])


def test_excel_chinese():
    r = search("Excel", limit=5)
    assert r["total"] >= 1
    assert any("Excel" in h["simple"] for h in r["hits"])


def test_unknown_term_no_fabrication():
    """★查不到必须明说，不能编。"""
    r = search("量子纠缠调度器xyzzy")
    assert r["total"] == 0
    assert "不要发明类名" in r["note"]


def test_methods_of_unknown_class_suggests():
    r = methods_of("com.seeyon.boot.util.NotExistUtils")
    assert r["total"] == 0
    assert "不在索引里" in r["note"]


def test_bucket_only_three_kinds():
    """★只索引 util/appservice/spi，实现类不该进来。"""
    assert _bucket("com.seeyon.boot.util.JsonUtils") == "util"
    assert _bucket("com.seeyon.bpm.api.common.BpmAppService") == "appservice"
    assert _bucket("com.seeyon.x.spi.SomeProvider") == "spi"
    assert _bucket("com.seeyon.bpm.impl.FooServiceImpl") is None
    assert _bucket("com.seeyon.bpm.config.BarConfig") is None


def test_tokenize():
    assert _tokenize("JsonUtils") == ["json"]
    assert _tokenize("DateUtils") == ["date"]
    assert _tokenize("BpmAppService") == ["bpm"]
    assert "cache" in _tokenize("LocalInnerCacheUtils")


def test_zh_label():
    assert _zh_of(["date"]) == "日期"
    assert "JSON" in _zh_of(["json"])
    assert "缓存" in _zh_of(["cache"])


def test_token_dict_size():
    """token 词典要有规模，太少就退化成英文匹配。"""
    assert len(TOKEN_ZH) >= 500, len(TOKEN_ZH)


def test_quality_ranking():
    """★类名/token 命中要排在「只有方法名沾边」的前面。"""
    r = search("JSON", limit=10)
    qualities = [h["quality"] for h in r["hits"]]
    assert qualities == sorted(qualities, reverse=True), qualities


def test_bucket_filter():
    r = search("日期", bucket="util", limit=5)
    assert all(h["bucket"] == "util" for h in r["hits"])


def test_pkg_filter():
    r = search("Utils", pkg="com.seeyon.boot.util", limit=10)
    assert all(h["name"].startswith("com.seeyon.boot.util") for h in r["hits"])


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print("PASS", name)
        except Exception as ex:  # noqa: BLE001
            fails += 1
            print("FAIL", name, "->", ex)
    print()
    print("FAILS", fails)
    sys.exit(1 if fails else 0)
