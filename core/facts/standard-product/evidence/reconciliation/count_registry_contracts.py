"""HANDOFF-2 P2: reproduce UdcOperationRegistry base-contract count (live, in-process).

Run: python <this-file>
Pure static/in-process: no network, no host, no HTTP.
"""
import sys, json
from collections import Counter, defaultdict

REPO = r"<SEEYON_AGENT_ROOT>"
sys.path.insert(0, REPO)

from components.platform_operations.registry import UdcOperationRegistry

reg = UdcOperationRegistry.default()
d = reg.all()                       # dict(operation_id -> UdcOperationContract)
ids = sorted(d.keys())
ops = {k: d[k] for k in ids}
total = len(ids)                    # expect 64

# ---- alias detection: rename-derived entries are signature-identical to a sibling ----
sig = defaultdict(list)
for k, o in ops.items():
    sig[(o.method, o.path, o.request_type, o.response_type, str(o.status), o.write)].append(k)
alias_groups = sorted([sorted(g) for g in sig.values() if len(g) > 1])
alias_count = sum(len(g) - 1 for g in alias_groups)     # each colliding group contributes (n-1) aliases
declared_alias_ids = ["udc.entity.get", "udc.entity.list", "udc.attribute.list"]
declared_alias_group_of = {a: [g for g in alias_groups if a in g][0] for a in declared_alias_ids}

# canonical member of each group = the id that is NOT a declared alias
alias_members = []
for g in alias_groups:
    for m in g:
        if m in declared_alias_ids:
            alias_members.append(m)
alias_members = sorted(set(alias_members))

# ---- R18 deploy family ----
deploy_ids = sorted(k for k in ids if k.startswith("udc.deploy."))

base_ids = sorted(k for k in ids if k not in set(alias_members) and k not in set(deploy_ids))
base = len(base_ids)

# ---- non-alias (61) segment census for cross-check vs MODULE-INVENTORY ----
non_alias_ids = [k for k in ids if k not in set(alias_members)]
seg61 = Counter(k.split(".")[1] for k in non_alias_ids)

seg64 = Counter(k.split(".")[1] for k in ids)
non_udc = [k for k in ids if not k.startswith("udc.")]
sp_probe = ("bpm", "ctp", "cip", "connector", "sso", "mobile", "standard", "spi", "gateway")
sp_hits = [k for k in ids if any(k.startswith(p + ".") for p in sp_probe)]

write_ids = sorted(k for k, o in ops.items() if o.write)
status_census = Counter(str(o.status).split(".")[-1] for o in ops.values())
evl_census = Counter((o.evidence[0].get("evidence_level", "NONE")
                      if o.evidence and isinstance(o.evidence[0], dict) else "NONE") for o in ops.values())

result = {
    "measured_by": "components.platform_operations.registry.UdcOperationRegistry.default() (in-process)",
    "total_entries": total,
    "alias_groups": alias_groups,
    "alias_count": alias_count,
    "declared_alias_ids": declared_alias_ids,
    "declared_alias_group_of": declared_alias_group_of,
    "deploy_ids": deploy_ids,
    "deploy_count": len(deploy_ids),
    "base_count": base,
    "formula": f"{total} - {alias_count} alias - {len(deploy_ids)} deploy = {base}",
    "segment_census_all64": dict(sorted(seg64.items())),
    "segment_census_non_alias61": dict(sorted(seg61.items())),
    "non_alias_total": len(non_alias_ids),
    "non_udc_prefix_entries": non_udc,
    "standard_product_registry_count": len(sp_hits),
    "write_count": len(write_ids),
    "read_count": total - len(write_ids),
    "write_ids": write_ids,
    "status_census": dict(status_census),
    "evidence_level_census": dict(evl_census),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
