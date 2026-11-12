import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, Mapping, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class ProviderError:
    """Stable, provider-independent description of a read failure."""

    kind: str
    message: str
    details: Mapping[str, Any] | None = None

    VALID_KINDS = frozenset({"timeout", "auth", "permission", "not_found", "parse", "unavailable"})

    def __post_init__(self):
        if self.kind not in self.VALID_KINDS:
            raise ValueError(f"unsupported provider error kind: {self.kind}")


class ProviderResult(dict, Generic[T]):
    """Mapping-compatible provider result with optional structured error."""

    def __init__(self, value: T | Mapping[str, Any] | None = None, *, error: ProviderError | None = None, **fields):
        if value is not None:
            if isinstance(value, Mapping):
                fields = {**value, **fields}
            else:
                fields["value"] = value
        super().__init__(fields)
        self.value = value
        self.error = error

    @property
    def ok(self) -> bool:
        return self.error is None


class FileSnapshotProvider:
    def __init__(self, path): self.path = Path(path)
    def read(self): return json.loads(self.path.read_text(encoding="utf-8"))


class ReadOnlyProbeProvider(ABC):
    """Read-only source for runtime and HTTP probe snapshots."""

    @abstractmethod
    def read_runtime(self) -> dict:
        """Read the runtime probe payload."""

    @abstractmethod
    def read_http(self) -> dict:
        """Read the HTTP probe payload."""


class JSONProbeProvider(ReadOnlyProbeProvider):
    """Read runtime and HTTP probe payloads from local JSON files."""

    def __init__(self, runtime_path, http_path):
        self.runtime_path = Path(runtime_path)
        self.http_path = Path(http_path)

    @staticmethod
    def _read(path):
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(value, dict):
                return ProviderResult(error=ProviderError("parse", "probe input must be a JSON object", {"path": str(path)}))
            return ProviderResult(value)
        except FileNotFoundError as exc:
            return ProviderResult(error=ProviderError("unavailable", "probe input file was not found", {"path": str(path), "exception": type(exc).__name__}))
        except (OSError, UnicodeError) as exc:
            return ProviderResult(error=ProviderError("unavailable", "probe input file is unavailable", {"path": str(path), "exception": type(exc).__name__}))
        except (TypeError, ValueError) as exc:
            return ProviderResult(error=ProviderError("parse", "probe input is not valid JSON", {"path": str(path), "exception": type(exc).__name__}))

    def read_runtime(self) -> dict:
        return self._read(self.runtime_path)

    def read_http(self) -> dict:
        return self._read(self.http_path)

    @property
    def sources(self) -> dict[str, str]:
        return {"runtime": str(self.runtime_path), "http": str(self.http_path)}


class ReadOnlyHttpProvider(ABC):
    """Offline/read-only HTTP provider contract; never performs network I/O."""

    @staticmethod
    def classify_status(status):
        if status is None: return "UNVERIFIED"
        if 200 <= status < 300: return "PASS"
        if status in {401, 403}: return "BLOCKED"
        if 300 <= status < 400: return "UNVERIFIED"
        return "FAIL"

    @abstractmethod
    def request(self, method: str, url: str) -> dict:
        """Return a normalized response record without network access."""


def _error_for_status(status):
    return {401: "auth", 403: "permission", 404: "not_found"}.get(status)

def _error_for_text(text):
    text = str(text).lower()
    for kind in ("timeout", "auth", "permission", "not_found", "parse", "unavailable"):
        if kind in text or kind.replace("_", " ") in text: return kind
    if "invalid json" in text or "malformed" in text: return "parse"
    return "unavailable"


class JsonHttpProvider(ReadOnlyHttpProvider):
    """Serve normalized HTTP responses from a local JSON fixture."""

    def __init__(self, fixture_path):
        self.fixture_path = Path(fixture_path)

    def request(self, method: str, url: str) -> dict:
        result = {"method": method.upper(), "url": url, "status": None, "headers": {}, "body_prefix": "", "classification": "UNVERIFIED"}
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            return ProviderResult(result, error=ProviderError("unavailable", "HTTP fixture was not found", {"path": str(self.fixture_path), "exception": type(exc).__name__}))
        except (OSError, UnicodeError) as exc:
            return ProviderResult(result, error=ProviderError("unavailable", "HTTP fixture is unavailable", {"path": str(self.fixture_path), "exception": type(exc).__name__}))
        except (TypeError, ValueError) as exc:
            return ProviderResult(result, error=ProviderError("parse", "HTTP fixture is not valid JSON", {"path": str(self.fixture_path), "exception": type(exc).__name__}))
        if not isinstance(payload, dict):
            return ProviderResult(result, error=ProviderError("parse", "HTTP fixture must be a JSON object", {"path": str(self.fixture_path)}))
        entry = payload.get(f"{result['method']} {url}")
        if entry is None:
            return ProviderResult(result, error=ProviderError("not_found", "HTTP fixture entry was not found", {"method": result["method"], "url": url}))
        if not isinstance(entry, dict):
            return ProviderResult(result, error=ProviderError("parse", "HTTP fixture entry must be an object", {"method": result["method"], "url": url}))
        if entry.get("error"):
            kind = _error_for_text(entry["error"])
            result["classification"] = "TIMEOUT" if kind == "timeout" else "UNVERIFIED"
            return ProviderResult(result, error=ProviderError(kind, str(entry["error"])))
        status = entry.get("status")
        result.update({"status": status, "headers": entry.get("headers", {}), "classification": self.classify_status(status)})
        body = entry.get("body", "")
        result["body_prefix"] = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        kind = _error_for_status(status)
        return ProviderResult(result, error=ProviderError(kind, f"HTTP status {status}") if kind else None)
