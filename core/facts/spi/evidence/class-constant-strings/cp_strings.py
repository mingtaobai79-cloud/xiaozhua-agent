"""Extract CONSTANT_Utf8 (tag=1) entries from .class files as proper UTF-8 text.
javap renders Chinese constant-pool strings with the platform charset (GBK on this host),
producing mojibake in the VERBATIM javap output; this script re-reads the raw class bytes
so the true string values are recorded. Usage: python cp_strings.py <a.class> [b.class ...]
"""
import struct
import sys


def parse(path):
    data = open(path, "rb").read()
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise SystemExit("not a class file: %s" % path)
    off = 8
    cp_count = struct.unpack_from(">H", data, off)[0]
    off += 2
    i = 1
    out = []
    while i < cp_count:
        tag = data[off]
        off += 1
        if tag == 1:
            n = struct.unpack_from(">H", data, off)[0]
            off += 2
            raw = data[off:off + n]
            off += n
            out.append((i, raw.decode("utf-8", "replace")))
        elif tag in (7, 8, 16, 19, 20):
            off += 2
        elif tag == 15:
            off += 3
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            off += 4
        elif tag in (5, 6):
            off += 8
            i += 1
        else:
            raise SystemExit("unknown tag %d at %d in %s" % (tag, off, path))
        i += 1
    return out


for p in sys.argv[1:]:
    print("==== %s" % p)
    for idx, s in parse(p):
        print("#%d\t%s" % (idx, s))
