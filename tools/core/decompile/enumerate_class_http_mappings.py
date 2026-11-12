# Independent (second-parser) enumerator of HTTP-annotated methods read DIRECTLY from a
# .class file (constant pool + RuntimeVisibleAnnotations), with no javap and no CFR.
#
# Why this exists: every route fact in this repo currently comes from a *text* view of a
# class (javap dump or CFR decompile), and both views are lossy. The in-repo dump
# docs/audit/artifacts/metadata-5.3.358/MetadataController.javap.txt was produced WITHOUT
# -v, so it contains no annotation values at all: grepping it for any route literal returns
# 0 even though the .class file plainly contains it. Any "route X is absent" conclusion
# drawn from such a dump is therefore a false negative, not evidence of absence.
#
# This parser reads the binary class file itself, so it stays valid after scratch is pruned
# and provides an axis genuinely independent of the text-based extractors.
#
# Evidence level: VERIFIED_STATIC_BYTECODE. Read-only, offline, no network.
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

HTTP_ANNS = {
    "GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
    "DeleteMapping": "DELETE", "PatchMapping": "PATCH", "RequestMapping": "ANY",
}
_FIXED = {3: 4, 4: 4, 9: 4, 10: 4, 11: 4, 12: 4, 17: 4, 18: 4}
# Reference-type constants: tag -> index byte width (2 for all but MethodHandle).
_REF = {7: 2, 8: 2, 16: 2, 19: 2, 20: 2}
_WIDE = {5: 8, 6: 8}


class _Reader:
    def __init__(self, data: bytes):
        self.d = data
        self.o = 0

    def u1(self) -> int:
        v = self.d[self.o]
        self.o += 1
        return v

    def u2(self) -> int:
        v = struct.unpack_from(">H", self.d, self.o)[0]
        self.o += 2
        return v

    def u4(self) -> int:
        v = struct.unpack_from(">I", self.d, self.o)[0]
        self.o += 4
        return v

    def skip(self, n: int) -> None:
        self.o += n


def _parse_constant_pool(r: _Reader):
    count = r.u2()
    pool = [None] * count
    i = 1
    while i < count:
        tag = r.u1()
        if tag == 1:
            n = r.u2()
            pool[i] = ("Utf8", r.d[r.o:r.o + n].decode("utf-8", "replace"))
            r.skip(n)
        elif tag in _WIDE:
            pool[i] = (tag,)
            r.skip(_WIDE[tag])
            i += 1  # long/double occupy two constant-pool slots
        elif tag in _REF:
            pool[i] = (tag, r.u2())
        elif tag == 15:                      # MethodHandle: kind byte + index
            kind = r.u1()
            pool[i] = (15, kind, r.u2())
        elif tag in _FIXED:
            pool[i] = (tag,)
            r.skip(_FIXED[tag])
        else:
            raise ValueError("unknown constant-pool tag %r at offset %d" % (tag, r.o))
        i += 1
    return pool


def _utf8(pool, idx):
    if not idx or idx >= len(pool) or pool[idx] is None:
        return ""
    e = pool[idx]
    return e[1] if e[0] == "Utf8" else ""


def _class_name(pool, idx):
    e = pool[idx] if idx < len(pool) else None
    return _utf8(pool, e[1]) if e and e[0] == 7 else ""


def _const(pool, idx):
    e = pool[idx] if idx < len(pool) else None
    if not e:
        return ""
    if e[0] == 8:      # CONSTANT_String -> Utf8
        return _utf8(pool, e[1])
    if e[0] == "Utf8":
        return e[1]
    return ""


def _element_value(r: _Reader, pool):
    tag = chr(r.u1())
    if tag in ("B", "C", "D", "F", "I", "J", "S", "Z", "s"):
        return _const(pool, r.u2())
    if tag == "e":      # enum constant
        return "%s.%s" % (_utf8(pool, r.u2()), _utf8(pool, r.u2()))
    if tag == "c":      # class literal
        return _class_name(pool, r.u2())
    if tag == "@":      # nested annotation
        return _read_annotation(r, pool)
    if tag == "[":      # array of values
        n = r.u2()
        return [_element_value(r, pool) for _ in range(n)]
    raise ValueError("unknown element_value tag %r" % tag)


def _elements(r: _Reader, pool, count):
    out = {}
    for _ in range(count):
        name = _utf8(pool, r.u2())
        out.setdefault(name, []).append(_element_value(r, pool))
    return out


def _read_annotation(r: _Reader, pool):
    type_name = _utf8(pool, r.u2())
    return {"type": type_name, "elements": _elements(r, pool, r.u2())}


def _skip_attributes(r: _Reader, count):
    for _ in range(count):
        r.u2()
        r.skip(r.u4())


def _simple(annotation_type):
    """Bare annotation name from a descriptor ('Lorg/.../GetMapping;' -> 'GetMapping')."""
    t = annotation_type
    if t.startswith("L") and t.endswith(";"):
        t = t[1:-1]
    return t.rsplit("/", 1)[-1]


def _routes_from(anns):
    """[(http, [fragments], simple_name)] for each HTTP-mapping annotation present."""
    out = []
    for a in anns:
        simple = _simple(a["type"])
        if simple not in HTTP_ANNS:
            continue
        frags = []
        for item in a["elements"].get("value") or []:
            for x in (item if isinstance(item, list) else [item]):
                if isinstance(x, str):
                    frags.append(x)
        out.append((HTTP_ANNS[simple], frags, simple))
    return out


def parse_class_file(path):
    r = _Reader(Path(path).read_bytes())
    if r.u4() != 0xCAFEBABE:
        raise ValueError("not a class file: %s" % path)
    r.skip(4)
    pool = _parse_constant_pool(r)
    r.u2()
    this_class = _class_name(pool, r.u2())
    r.u2()
    r.skip(2 * r.u2())

    for _ in range(r.u2()):        # fields
        r.skip(6)
        _skip_attributes(r, r.u2())

    methods = []
    for _ in range(r.u2()):
        r.u2()
        name = _utf8(pool, r.u2())
        desc = _utf8(pool, r.u2())
        anns = []
        for _ in range(r.u2()):
            aname = _utf8(pool, r.u2())
            length = r.u4()
            if aname == "RuntimeVisibleAnnotations":
                anns = [_read_annotation(r, pool) for _ in range(r.u2())]
            else:
                r.skip(length)
        if name == "<init>" or name.startswith("lambda$"):
            continue
        routes = _routes_from(anns)
        op = None
        for a in anns:
            if _simple(a["type"]) == "RestApiOperation":
                vals = a["elements"].get("value") or []
                op = vals[0] if vals and isinstance(vals[0], str) else ""
        if routes:
            methods.append({"method": name, "descriptor": desc,
                            "routes": routes, "op_code": op})

    class_mapping = None
    for _ in range(r.u2()):
        aname = _utf8(pool, r.u2())
        length = r.u4()
        if aname == "RuntimeVisibleAnnotations":
            for a in [_read_annotation(r, pool) for _ in range(r.u2())]:
                for _http, frags, _s in _routes_from([a]):
                    if frags:
                        class_mapping = frags[0]
        else:
            r.skip(length)

    return {"class_file": Path(path).name, "this_class": this_class,
            "class_mapping": class_mapping, "methods": methods}


def enumerate_routes(path):
    parsed = parse_class_file(path)
    base = (parsed["class_mapping"] or "").strip("/")
    endpoints = []
    for m in parsed["methods"]:
        for http, frags, simple in m["routes"]:
            frag = (frags[0] if frags else "").lstrip("/")
            full = "/" + "/".join(x for x in (base, frag) if x)
            endpoints.append({"method": m["method"], "http": http, "sub_path": frag,
                              "full_path": full, "op_code": m["op_code"],
                              "annotation": simple})
    return {**parsed, "endpoints": endpoints}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Enumerate HTTP mappings straight from a .class file.")
    ap.add_argument("class_file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    res = enumerate_routes(args.class_file)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    print("class     : %s" % res["this_class"])
    print("mapping   : %s" % res["class_mapping"])
    print("endpoints : %d" % len(res["endpoints"]))
    print("with op   : %d" % sum(1 for e in res["endpoints"] if e["op_code"]))
    for e in res["endpoints"]:
        print("  %s%-4s %-52s <- %s" % ("op " if e["op_code"] else "   ",
                                        e["http"], e["full_path"], e["method"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
