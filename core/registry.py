from typing import Any, Iterable

from .ports import ComponentPort


class ComponentRegistry:
    """Registry and dispatch boundary for xiaozhua Agent components."""

    def __init__(self, components: Iterable[ComponentPort] | None = None):
        self._components: dict[str, ComponentPort] = {}
        for component in components or ():
            self.register(component)

    def register(self, component: ComponentPort) -> ComponentPort:
        name = getattr(component, "name", None)
        if not isinstance(name, str) or not name:
            raise ValueError("component name must be a non-empty string")
        if name in self._components:
            raise ValueError(f"component already registered: {name}")
        self._components[name] = component
        return component

    def get(self, name: str) -> ComponentPort | None:
        return self._components.get(name)

    def names(self) -> list[str]:
        return list(self._components)

    def capabilities(self, name: str) -> list[str]:
        component = self._components.get(name)
        return list(component.capabilities()) if component else []

    def discover(self) -> dict[str, list[str]]:
        return {name: list(component.capabilities()) for name, component in self._components.items()}

    def dispatch(self, component_name: str, target: str, action: str = "inspect") -> dict[str, Any]:
        component = self.get(component_name)
        if component is None:
            return {"status": "UNAVAILABLE", "component": component_name, "action": action}
        if action not in component.capabilities():
            return {"status": "UNAVAILABLE", "component": component_name, "action": action}
        execute = getattr(component, "execute", None)
        if callable(execute):
            from dataclasses import make_dataclass
            request_type = make_dataclass("ComponentRequest", [("action", str), ("target", str)])
            return execute(request_type(action, target))
        if action == "inspect":
            return component.inspect(target)
        method = getattr(component, action, None)
        if callable(method):
            return method(target)
        return {"status": "UNAVAILABLE", "component": component_name, "action": action}
