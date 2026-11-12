"""Minimal v1 DTO source generator.

This is deliberately limited to one DTO artifact. It renders source only after
the v0.2 artifact plan has selected and validated the DTO artifact.
"""
from dataclasses import dataclass
import re

from .models import UNKNOWN

_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


@dataclass(frozen=True)
class GeneratedSource:
    artifact_type: str
    relative_path: str
    source: str


class DtoSourceGenerator:
    def generate(self, plan, model) -> GeneratedSource:
        dto = next((a for a in plan.artifacts if a.type == "dto"), None)
        if dto is None:
            raise ValueError("plan does not contain a dto artifact")
        if not _IDENTIFIER.match(dto.class_name):
            raise ValueError(f"invalid dto class name: {dto.class_name}")
        lines = [f"package {dto.package};", "", "import com.seeyon.udc.common.dto.BaseRootDto;", "", f"public class {dto.class_name} extends BaseRootDto {{"]
        for attribute in model.attributes:
            name = getattr(attribute, "name", None)
            type_name = getattr(attribute, "type", UNKNOWN)
            if not name or not _IDENTIFIER.match(name) or type_name in (None, "", UNKNOWN):
                continue
            java_type = _JAVA_TYPES.get(str(type_name), str(type_name))
            if not _IDENTIFIER.match(java_type):
                continue
            lines.append(f"    private {java_type} {name};")
        lines.append("}")
        return GeneratedSource("dto", dto.relative_path, "\n".join(lines) + "\n")


_JAVA_TYPES = {
    "String": "String",
    "java.lang.String": "String",
    "Long": "Long",
    "java.lang.Long": "Long",
    "Integer": "Integer",
    "java.lang.Integer": "Integer",
    "Boolean": "Boolean",
    "java.lang.Boolean": "Boolean",
}
