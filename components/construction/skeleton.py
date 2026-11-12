"""Java 后端骨架渲染器 —— 证据驱动、声明级、不臆造方法体。

北极星落点：需求（实体 + 属性）→ ConstructionEngine 生成计划 → 骨架源码。
证据边界（全部来自 golden javap dump，docs/audit/artifacts/customer-*）：
- DTO extends com.seeyon.udc.common.dto.BaseRootDto（HetongdanganDto javap 实证）
- entity extends com.seeyon.boot.domain.entity.BaseEntity
- service extends com.seeyon.boot.starter.lowcode.service.BaseEntityCurdService<Dto FQN>
- app_service_impl implements <app>.api.<X>AppService
- dao: interface extends com.seeyon.boot.starter.mybatis.BaseMybatisDao<entity FQN>
- abstract_controller: class <AbstractXController<T>> extends
  com.seeyon.boot.starter.dynamicsql.controller.AbstractDynamicSelectController
- controller extends com.seeyon.boot.starter.web.BaseController
- api: interface

方法体/字段注入依赖 = UNVERIFIED（契约 caveat: "Observed output contract only;
generator causality UNKNOWN"）——骨架只出可证部分，方法体留 TODO 标注，
禁止按经验拼方法。Java 类型词表取 golden javap 观测分布。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from .models import UNKNOWN, GeneratedArtifact, GeneratedArtifactPlan

_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

# golden javap 字段类型观测（197 dump）：高频类型映射（短名→全限定名）
JAVA_TYPES = {
    "String": "java.lang.String",
    "java.lang.String": "java.lang.String",
    "Long": "java.lang.Long",
    "java.lang.Long": "java.lang.Long",
    "Integer": "java.lang.Integer",
    "java.lang.Integer": "java.lang.Integer",
    "Boolean": "java.lang.Boolean",
    "java.lang.Boolean": "java.lang.Boolean",
    "BigDecimal": "java.math.BigDecimal",
    "java.math.BigDecimal": "java.math.BigDecimal",
    "Date": "java.util.Date",
    "java.util.Date": "java.util.Date",
}

# golden javap 实证的声明模板（{pkg}=package root, {X}=实体名, {appstem}=应用 id 首字母大写）
_DECL = {
    "dto": ("class", "com.seeyon.udc.common.dto.BaseRootDto"),
    "entity": ("class", "com.seeyon.boot.domain.entity.BaseEntity"),
    "domain_service": ("class", "com.seeyon.boot.starter.lowcode.service.BaseEntityCurdService"),
    "app_service_impl": ("class", None),  # implements 应用自身 api（见 _impl_header）
    "dao": ("interface", "com.seeyon.boot.starter.mybatis.BaseMybatisDao"),
    "abstract_controller": ("class", "com.seeyon.boot.starter.dynamicsql.controller.AbstractDynamicSelectController"),
    "controller": ("class", "com.seeyon.boot.starter.web.BaseController"),
    "api": ("interface", None),
}

# 各类型泛型参数（golden 实证：service<DtoFqn>, dao<EntityFqn>）
_GENERIC = {
    "domain_service": "domain_dto",
    "dao": "entity",
    "abstract_controller": None,  # golden: AbstractXController<T>，T 留给实现
}


@dataclass
class GeneratedSource:
    artifact_type: str
    relative_path: str
    source: str
    evidence: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)


def _attr_name(attr: Any) -> str | None:
    if isinstance(attr, dict):
        return attr.get("name")
    return getattr(attr, "name", None)


def _attr_type(attr: Any) -> str:
    if isinstance(attr, dict):
        return str(attr.get("type", UNKNOWN))
    return str(getattr(attr, "type", UNKNOWN))


class JavaSkeletonRenderer:
    """把 artifact plan 渲染为声明级 Java 骨架（每类一个文件内容）。"""

    SCHEMA = "udc.construction.skeleton.v1"

    def render(self, plan: GeneratedArtifactPlan, model) -> list[GeneratedSource]:
        stem = (model.application_id[:1].upper() + model.application_id[1:])
        root = self._root(model)
        out: list[GeneratedSource] = []
        for art in plan.artifacts:
            src = self._render_one(art, model, stem, root)
            if src:
                out.append(src)
        return out

    def _root(self, model) -> str:
        # package root = com.seeyon.<application_id>（v0.2 冻结语义）
        root = "com.seeyon." + model.application_id
        if getattr(model, "package_root", None):
            root = str(model.package_root)
        return root

    def _render_one(self, art: GeneratedArtifact, model, stem: str, root: str) -> GeneratedSource | None:
        kind = art.type
        x = model.entity_name
        if not _IDENTIFIER.match(x):
            return None
        decl, base = _DECL.get(kind, (None, None))
        if decl is None:
            return None
        pkg = art.package
        cls = art.class_name
        fq_dto = f"{root}.dto.{x}Dto"
        fq_entity = f"{root}.domain.entity.{x}"

        unverified = ["method-bodies: UNVERIFIED (generator causality UNKNOWN per contract caveat)"]
        lines: list[str] = []

        if kind == "api":
            lines += [f"package {pkg};", ""]
            lines.append(f"public interface {cls} {{")
            lines.append(f"    // UNVERIFIED: 方法签名集未从 golden 泛化（需实体级 javap 证据），暂不生成")
            lines.append("}")
        elif kind in ("dto", "entity"):
            lines += [f"package {pkg};", ""]
            lines.append(f"import {base};")
            lines.append("")
            lines.append(f"public class {cls} extends {base.rsplit('.', 1)[-1]} {{")
            lines.append("    private static final long serialVersionUID = 1L;")
            for attr in model.attributes:
                name = _attr_name(attr)
                typ = _attr_type(attr)
                java_type = JAVA_TYPES.get(typ)
                if not name or not _IDENTIFIER.match(str(name)):
                    lines.append(f"    // UNVERIFIED: 字段 {name}({typ}) 名非 Java 标识符或类型未证实，待宿主确认后生成")
                    continue
                if java_type:
                    lines.append(f"    private {java_type} {name};")
                else:
                    lines.append(f"    // UNVERIFIED: 类型 {typ} 无 golden 观测映射，字段 {name} 待确认")
            if not any(_attr_name(a) and JAVA_TYPES.get(_attr_type(a)) for a in model.attributes):
                unverified.append(f"fields: 0 known types (attributes empty or unmapped) — golden observed {list(JAVA_TYPES)[:4]}…")
            lines.append("}")
        elif kind == "domain_service":
            lines += [f"package {pkg};", "",
                      f"import {root}.dto.{x}Dto;",
                      "import com.seeyon.boot.starter.lowcode.service.BaseEntityCurdService;",
                      ""]
            lines.append(f"public class {cls} extends BaseEntityCurdService<{fq_dto}> {{")
            lines.append("    // UNVERIFIED: 方法体/依赖注入字段未生成")
            lines.append("}")
        elif kind == "app_service_impl":
            lines += [f"package {pkg};", "",
                      f"import {root}.api.{x}AppService;",
                      f"import {root}.domain.service.{x}Service;",
                      ""]
            lines.append(f"public class {cls} implements {x}AppService {{")
            lines.append(f"    // 依赖: {x}Service (golden 实证 domainService 字段)；方法体 UNVERIFIED")
            lines.append("}")
        elif kind == "dao":
            lines += [f"package {pkg};", "",
                      f"import {root}.domain.entity.{x};",
                      "import com.seeyon.boot.starter.mybatis.BaseMybatisDao;",
                      ""]
            lines.append(f"public interface {cls} extends BaseMybatisDao<{fq_entity}> {{")
            lines.append("    // golden 实证: 方法由 BaseMybatisDao 提供，无自定义方法观测")
            lines.append("}")
        elif kind == "abstract_controller":
            lines += [f"package {pkg};", "",
                      f"import {root}.api.{x}AppService;",
                      "import com.seeyon.boot.starter.dynamicsql.controller.AbstractDynamicSelectController;",
                      ""]
            lines.append(f"public class {cls}<T> extends AbstractDynamicSelectController {{")
            lines.append(f"    // 依赖: appService={x}AppService (golden 实证)；方法体 UNVERIFIED")
            lines.append("}")
        elif kind == "controller":
            lines += [f"package {pkg};", "",
                      f"import {root}.controller.Abstract{x}Controller;",
                      "import com.seeyon.boot.starter.web.BaseController;",
                      ""]
            lines.append(f"public class {cls} extends BaseController {{")
            lines.append("    // 路由/方法 UNVERIFIED（golden 方法级注解未泛化）")
            lines.append("}")
        else:
            return None

        src = "\n".join(lines) + "\n"
        return GeneratedSource(
            artifact_type=kind,
            relative_path=art.relative_path,
            source=src,
            evidence=[f"golden-javap:{kind}" for _ in [0]] + [art.rule_id],
            unverified=unverified,
        )


__all__ = ["JavaSkeletonRenderer", "GeneratedSource", "JAVA_TYPES"]
