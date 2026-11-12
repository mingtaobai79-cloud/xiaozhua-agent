from typing import Any, Protocol, runtime_checkable

class ToolPort(Protocol):
    def call(self, name: str, **kwargs: Any) -> Any: ...


class SnapshotProvider(Protocol):
    def read(self) -> dict[str, Any]: ...

@runtime_checkable
class ComponentPort(Protocol):
    name: str
    read_only: bool
    def capabilities(self) -> list[str]: ...
    def inspect(self, target: str) -> dict[str, Any]: ...
