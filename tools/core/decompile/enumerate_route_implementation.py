# -*- coding: utf-8 -*-
"""路由「有实现 / 无实现」双轴裁定器 —— 钉死 `/udc/micro-flow-group/search-list` 的三选一。

**要回答的问题**（PROGRESS 第十六轮遗留，候选 (vi) 剩余二选一）：
第九轮 LIVE 在真实 URL 面观测到 `/udc/micro-flow-group/search-list` 与
`/udc/micro-flow-group/select-by-appid/{appId}`，但 674 契约（udc-web 5.3.517）
与**部署态字节码**里都没有这两条 mapping。原候选三选一：
  (a) 部署的 udc-web 版本 ≠ 5.3.517；(b) 另一构件提供；(c) 死路径。
第十轮已用 LIVE 部署 tag 证伪 (a)。本件给出 (b)(c) 的裁定。

**两条轴（互相独立，均仓内可复核）**

轴 1 · 静态「提供者唯一性」：
  对**完整 jar 仓库**逐 class 直读字节码常量池，统计「声明了类级 mapping
  `udc/micro-flow-group` 的 class」有多少个。
  - 若只有 1 个（= udc-web 的 MicroFlowGroupController），则 (b) 不成立：
    `/udc/micro-flow-group/**` 这个前缀下不存在第二个提供者，
    所以不能再有「别的构件在这个前缀下补了 search-list」这回事。

轴 2 · 静态「该 class 的映射全集」：
  用 `tools/enumerate_class_http_mappings.py`（**直读 .class 二进制**，不经 javap、
  不经 CFR，因而免疫文本视图的截断/丢字面量）枚举该类 7 个方法的全部 mapping。
  - 若 7 个方法里没有 `search-list`，则该前缀的注册面**完整**且其中无此路由。
  - 关键反例：同类的 `selectByAppId` 方法，其 `@PostMapping` 字面量 = **`select-by-type`**
    （平台源码自身复制粘贴瑕疵）⇒ 同一份字节码里「方法名」与「路由字面量」已经脱钩过一次，
    证明「方法名猜路径」不可靠，判据只能是逐字 `full_path`。

**约束**：纯离线只读；jar 仓库根取自 `config/environments.yaml` 的 `local-maven.maven_root`
（命令行可用 `--repo-root` 覆盖）；产物不含客户业务明细与凭据。

产物契约：jars_scanned 属**可变域**计数（本地 maven 仓库会被其它工作流写入，客户构件随构建落地），
**结论面不含它**；护栏按 结论面逐字 + 扫描域不得缩小 双判据。

用法：
    uv run --no-project python tools/enumerate_route_implementation.py --json
    uv run --no-project python tools/enumerate_route_implementation.py --repo-root <MAVEN_REPO>
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts' / '_api_full.json')
ENV = ROOT / 'config' / 'environments.yaml'

# 待裁定的目标：类级 mapping + 观测到但契约没有的叶子
CLASS_MAPPING = b'udc/micro-flow-group'
TARGET_LEAVES = (b'search-list', b'select-by-appid')
# 已知存在的对照叶子（证扫描器不是空转）
CONTROL_LEAVES = (b'select-by-type', b'batch-move')


def default_repo_root() -> Path | None:
    """从 config/environments.yaml 的 local-maven.maven_root 读 jar 仓库根。"""
    if not ENV.exists():
        return None
    for line in ENV.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if s.startswith('maven_root:'):
            return Path(s.split(':', 1)[1].split('#')[0].strip())
    return None


def scan(classes_needle: bytes, leaves: tuple[bytes, ...], repo_root: Path) -> dict:
    """逐 jar 逐 class 直读字节码，统计类级 mapping 提供者，并在命中类内查叶子字面量。"""
    providers: list[tuple[str, str]] = []
    leaf_hits: dict[str, list[str]] = {lf.decode(): [] for lf in leaves}
    jars = sorted(repo_root.rglob('*.jar'))
    for j in jars:
        try:
            with zipfile.ZipFile(j) as z:
                for n in z.namelist():
                    if not n.endswith('.class'):
                        continue
                    b = z.read(n)
                    if classes_needle in b:
                        providers.append((str(j.relative_to(repo_root)), n))
                        for lf in leaves:
                            if lf in b:
                                leaf_hits[lf.decode()].append(n)
        except (zipfile.BadZipFile, OSError, RuntimeError):
            continue
    return {'jars_scanned': len(jars), 'providers': providers, 'leaf_hits': leaf_hits}


def contract_routes() -> list[str]:
    data = json.loads(CONTRACT.read_text(encoding='utf-8'))
    prefix = '/' + CLASS_MAPPING.decode()
    out = []
    for body in data.values():
        for m in body.get('methods', []):
            fp = m.get('full_path') or ''
            if fp.startswith(prefix + '/'):
                out.append(fp)
    return sorted(set(out))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='路由有实现/无实现双轴裁定器（离线只读）')
    ap.add_argument('--repo-root', default=None, help='jar 仓库根（默认取 environments.yaml）')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--emit', default=None, help='把证据件写到该路径（与 --json 同形态）')
    a = ap.parse_args(argv)

    repo = Path(a.repo_root) if a.repo_root else default_repo_root()
    if not repo or not repo.exists():
        print(json.dumps({'error': 'repo_root 未找到', 'repo_root': str(repo)}, ensure_ascii=False))
        return 2

    res = scan(CLASS_MAPPING, TARGET_LEAVES + CONTROL_LEAVES, repo)
    routes = contract_routes()
    providers = res['providers']
    payload = {
        'schema': 'route-implementation-verdict.v1',
        'evidence': 'VERIFIED_STATIC_BYTECODE (直读 .class 常量池, 不经 javap/CFR)',
        'repo_root': str(repo),
        'jars_scanned': res['jars_scanned'],
        'jars_scanned_note': '可变域计数：本地 maven 仓库会被其它工作流写入（客户构件随构建落地），'
                             '不参与结论面比对；护栏按 结论面逐字 + 扫描域不得缩小 判定，'
                             '见 tests/udc/test_route_implementation_verdict.py',
        'class_mapping': CLASS_MAPPING.decode(),
        'axis1_provider_uniqueness': {
            'providers_declaring_class_mapping': providers,
            'provider_count': len(providers),
            'other_component_branch': 'REFUTED' if len(providers) == 1 else 'POSSIBLE',
        },
        'axis2_registered_leaves': {
            'contract_routes_under_prefix': routes,
            'contract_route_count': len(routes),
            'target_leaf_literal_hits_in_providers': res['leaf_hits'],
            'control_leaf_must_be_present': {c.decode(): res['leaf_hits'][c.decode()]
                                             for c in CONTROL_LEAVES},
        },
    }
    if a.emit:
        # 换行显式固定为 CRLF（同证据件既有字节）：不再依赖宿主文本模式
        Path(a.emit).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n',
                                encoding='utf-8', newline='\r\n')
        print('WROTE', a.emit)
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(f"jar 仓库 : {repo}  ({res['jars_scanned']} jar)")
        print(f"类级 mapping {CLASS_MAPPING.decode()!r} 的提供者 = {len(providers)} 个")
        for p in providers:
            print('   ', p)
        print(f"契约内 {CLASS_MAPPING.decode()} 下的路由 = {len(routes)} 条")
        for r in routes:
            print('   ', r)
        print('目标叶子字面量命中：')
        for k, v in res['leaf_hits'].items():
            print(f"    {k:18} -> {v if v else '无命中'}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
