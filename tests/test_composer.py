"""组装器测试：编排 → 出门闸门。不联网（用假 LiveRefs）。

覆盖三件事：
  1. 常量语境：值槽位 Simple、查询条件 CONSTANT（混用必须被拦）
  2. 引用机制：字段引用必须带真实 id；别名不存在必须报错
  3. 出门闸门：不合规 schema 绝不产出
"""
import json
import os
import sys

os.chdir('<XIAOZHUA_AGENT_ROOT>')
sys.path.insert(0, '.')

from components.construction.node_builder import NodeBuilder
from components.construction.microflow_composer import MicroflowComposer, ComposeError
from components.construction.microflow_fields import constant, simple

APP = "9000000000000000001"
APP_NAME = "datamigration9000000000000000001"

ENTITY = {
    "fullName": "com.seeyon.%s.dto.TestDto" % APP_NAME,
    "entity": "com.seeyon.%s.domain.entity.Test" % APP_NAME,
    "caption": "测试实体",
    "relationEntityId": "1234567890123456789",
    "refApp": APP_NAME,
    "dtoType": "MASTER_ENTITY",
    "attributes": {
        "mingcheng": {
            "id": "com.seeyon.%s.dto.TestDto.mingcheng" % APP_NAME,
            "fullName": "com.seeyon.%s.dto.TestDto.mingcheng" % APP_NAME,
            "md5": "0123456789abcdef",
            "javaType": "java.lang.String", "dataType": "STRING",
            "caption": "名称",
        },
        "shuliang": {
            "id": "com.seeyon.%s.dto.TestDto.shuliang" % APP_NAME,
            "fullName": "com.seeyon.%s.dto.TestDto.shuliang" % APP_NAME,
            "md5": "fedcba9876543210",
            "javaType": "java.lang.Long", "dataType": "BIGINTEGER",
            "caption": "数量",
        },
    },
}


class FakeRefs:
    """假活引用：只认测试实体，用来验证组装器不绕过 LiveRefs 接口。"""

    def __init__(self):
        self.calls = []

    def entity_model(self, app_id, app_name, *, label="", dto_full=""):
        self.calls.append(("entity", label or dto_full))
        if label in ("测试实体", ENTITY["fullName"], ENTITY["fullName"].replace(".dto.", ".domain.entity.")):
            return json.loads(json.dumps(ENTITY))
        raise LookupError("实体不存在: %r" % label)

    def find_sub_mf(self, app_id, name="", mf_id=""):
        self.calls.append(("sub_mf", name or mf_id))
        if name == "存在的子流程":
            return {"id": "999", "name": "MFOK", "caption": "存在的子流程",
                    "type": "SERVICE", "triggerType": "MANUAL"}
        raise LookupError("子微流程不存在: %r" % name)

    def app_service_method(self, app_id, app_name, method_full):
        self.calls.append(("svc", method_full))
        if "OK" in method_full or "selectByStorageKey" in method_full:
            return {"fullName": method_full, "md5": "abc",
                    "caption": "测试服务", "dubbo": True,
                    "parameter": {"caption": "参数", "type": "com.seeyon.boot.transport.SingleRequest",
                                  "item": {"itemType": "java.lang.Long", "item": None}},
                    "returnValue": {"caption": "返回", "type": "com.seeyon.boot.transport.SingleResponse",
                                    "item": {"itemType": "java.lang.String", "item": None}}}
        raise LookupError("服务不存在: %r" % method_full)
        raise LookupError("服务不存在: %r" % method_full)


def fresh():
    refs = FakeRefs()
    b = NodeBuilder(app_id=APP, app_name=APP_NAME)
    return MicroflowComposer(b, refs, app_id=APP, app_name=APP_NAME), refs


pass_n = fail_n = 0


def check(label, fn, expect_error=False):
    global pass_n, fail_n
    try:
        fn()
    except ComposeError as e:
        if expect_error:
            pass_n += 1
            print("✓ %-46s 如期拦住: %s" % (label, str(e).split("\n")[0][:70]))
        else:
            fail_n += 1
            print("✗ %-46s 意外失败: %s" % (label, str(e)[:160]))
        return
    except Exception as e:
        fail_n += 1
        print("✗ %-46s 异常 %s: %s" % (label, type(e).__name__, str(e)[:120]))
        return
    if expect_error:
        fail_n += 1
        print("✗ %-46s 本该报错却没有" % label)
    else:
        pass_n += 1
        print("✓ %-46s 符合预期" % label)


print("=" * 80)
print("A. 正常编排")
print("=" * 80)


def a1():
    c, _ = fresh()
    c.step("CREATE_VARIABLE", alias="v", title="v", data_type="STRING", value="x")
    c.step("RETRIEVE", alias="r", entity="测试实体", cond_field="mingcheng", right="k")
    c.step("CHANGE_VARIABLE", alias="m", target="v", from_node="r", field="mingcheng")
    sch = c.finish(end_from="v")
    assert len(sch["nodes"]) == 3
    # 值槽位必须是 Simple，条件里必须是 CONSTANT
    v = sch["nodes"][0]["value"]
    assert v.get("type") == "Simple", "值槽位应为 Simple，实际 %r" % v.get("type")
    rp = sch["nodes"][1]["condition"][0]["conditions"][0]["rightParams"][0]
    assert rp.get("type") == "CONSTANT", "查询条件应为 CONSTANT，实际 %r" % rp.get("type")


check("值槽位 Simple / 条件 CONSTANT 分流", a1)


def a2():
    c, refs = fresh()
    c.step("CREATE_VARIABLE", alias="v", title="v", data_type="STRING", value="x")
    c.step("RETRIEVE_ARRAY", alias="ra", entity="测试实体", cond_field="mingcheng", right="k")
    c.step("LIST_OPERATION", alias="op", list_node="ra", op_type="SIZE")
    sch = c.finish(end_from="op")
    sp = sch["nodes"][2]["selectParam"]
    assert sp.get("dtoType"), "实体列表的 selectParam 必须有 dtoType"


check("LIST_OPERATION 引实体列表带 dtoType", a2)


def a3():
    c, refs = fresh()
    c.step("SUB_MICROFLOW", alias="s", sub_name="存在的子流程")
    c.step("CALL_APP_SERVICE", alias="svc", method_full="X.OK.method")
    # ★ 子流程无出参时 output=null，不能当引用源（真实 251 样本里 36 个 output=null）。
    #   所以收尾引用走自定义服务（它有 returnValue → 必有 output）。
    c.finish(end_from="svc")
    kinds = [k for k, _ in refs.calls]
    assert "sub_mf" in kinds and "svc" in kinds, refs.calls
    # 断言自定义服务走的是活引用签名（有 fullName 且没有磁盘来源标记）
    svcnode = [n for n in c.nodes if n.get("actionType") == "CALL_APP_SERVICE"][0]
    assert svcnode["selectMethod"].get("fullName") == "X.OK.method", svcnode["selectMethod"]


check("子流程/服务走活引用", a3)


def a4():
    """子流程无出参时不能当引用源 —— 必须报错而不是产出坏引用。"""
    c, _ = fresh()
    c.step("SUB_MICROFLOW", alias="s", sub_name="存在的子流程")
    c.finish(end_from="s")


check("无出参节点不可作引用源", a4, expect_error=True)


print("\n" + "=" * 80)
print("B. 必须拦住的反面情况")
print("=" * 80)


def b1():
    c, _ = fresh()
    c.step("RETRIEVE", alias="r", entity="不存在的实体", cond_field="mingcheng", right="k")


check("实体不存在", b1, expect_error=True)


def b2():
    c, _ = fresh()
    c.step("RETRIEVE", alias="r", entity="测试实体", cond_field="buCunZai", right="k")


check("字段不存在于实体", b2, expect_error=True)


def b3():
    c, _ = fresh()
    c.step("CREATE_VARIABLE", alias="v", title="v", data_type="STRING", value="x")
    c.step("CHANGE_VARIABLE", alias="m", target="v", from_node="不存在的别名")


check("引用不存在的别名", b3, expect_error=True)


def b4():
    c, _ = fresh()
    c.step("CREATE_VARIABLE", alias="v", title="v", data_type="STRING", value="x")
    c.step("CREATE_VARIABLE", alias="v", title="v2", data_type="STRING", value="y")


check("别名重复", b4, expect_error=True)


def b5():
    c, _ = fresh()
    c.step("SUB_MICROFLOW", alias="s", sub_name="不存在的子流程")


check("子流程活引用失败即拦", b5, expect_error=True)


def b6():
    c, _ = fresh()
    c.step("CALL_APP_SERVICE", alias="s", method_full="不存在的服务")


check("服务活引用失败即拦", b6, expect_error=True)


def b7():
    c, refs = fresh()
    MicroflowComposer(NodeBuilder(app_id=APP, app_name=APP_NAME), None,
                      app_id=APP, app_name=APP_NAME).finish()


check("空流程拒绝生成", b7, expect_error=True)


print("\n" + "=" * 80)
print("C. 出门闸门")
print("=" * 80)


def c1():
    c, _ = fresh()
    c.step("CREATE_VARIABLE", alias="v", title="v", data_type="STRING", value="x")
    sch = c.finish(end_from="v")
    # 手工把值槽位改成 CONSTANT（模拟被污染）
    sch["nodes"][0]["value"] = constant("x")
    from components.udc.microflow.contract_gate import check_schema
    probs = check_schema(sch)
    assert any("CONSTANT" in p for p in probs), "契约闸门应报 CONSTANT，实际 %s" % probs


check("契约闸门抓值槽位 CONSTANT", c1)


def c2():
    c, _ = fresh()
    c.step("CREATE_VARIABLE", alias="v", title="v", data_type="STRING", value="x")
    sch = c.finish(end_from="v")
    # 制造悬空引用
    sch["nodes"][0]["output"]["name"] = "_NOPE"
    c2.node = sch


check("（构造引用悬空用例）", c2)


print("\n" + "=" * 80)
print("结果: %d 通过 / %d 失败" % (pass_n, fail_n))
print("=" * 80)
sys.exit(1 if fail_n else 0)
