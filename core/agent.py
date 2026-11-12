import re
from dataclasses import dataclass, field
from typing import Any, Protocol
from .registry import ComponentRegistry
from .policy import PolicyGate
from . import intent_actions

class ContextPort(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...

class SessionPort(Protocol):
    def append(self, event: dict[str, Any]) -> None: ...

class PolicyPort(Protocol):
    def allows(self, action: str) -> bool: ...

@dataclass
class MemoryContext:
    values: dict[str, Any] = field(default_factory=dict)
    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

@dataclass
class MemorySession:
    events: list[dict[str, Any]] = field(default_factory=list)
    def append(self, event: dict[str, Any]) -> None:
        self.events.append(event)

class ReadOnlyPolicy:
    def __init__(self):
        self.gate = PolicyGate(network_enabled=False)
    def allows(self, action: str) -> bool:
        return self.gate.evaluate(action).get("allowed", False)

@dataclass(frozen=True)
class AgentRequest:
    intent: str
    context: dict[str, Any] = field(default_factory=dict)

class XiaozhuaAgent:
    def __init__(self, components=None, *, context=None, session=None, policy=None):
        if isinstance(components, ComponentRegistry):
            self.registry = components
            self.components = {name: self.registry.get(name) for name in self.registry.names()}
        else:
            self.components = components or {}
            self.registry = ComponentRegistry(self.components.values())
        self.context = context or MemoryContext()
        self.session = session or MemorySession()
        self.policy = policy or ReadOnlyPolicy()

    def route(self, request: AgentRequest) -> str:
        text = request.intent.lower()
        keywords = {
            "udc": ("udc", "低代码", "实体", "页面", "微流程", "microflow"),
            "integration": ("接口同步", "落库", "第三方", "同步失败"),
            "runtime": ("pod", "redis", "nacos", "运行态"),
            "spi": ("spi", "单点", "sso", "mq"),
        }
        def contains(term):
            if term.isascii() and term.isalpha():
                return re.search(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', text) is not None
            return term in text

        matches = [domain for domain, terms in keywords.items() if any(contains(term) for term in terms)]
        return matches[0] if len(matches) == 1 else "unknown"

    def intent_index(self) -> dict[str, list[str]]:
        """宿主发现面：{component: {action: [keywords]}}，只含组件已登记的能力。"""
        out: dict[str, list[str]] = {}
        for name in self.registry.names():
            caps = self.registry.capabilities(name)
            out[name] = intent_actions.intent_index(name, caps)
        return out

    def action_for(self, request: AgentRequest, component_name: str) -> str:
        """组件内只读 action：先按意图表挑已登记能力，否则用该域默认 action。"""
        return intent_actions.resolve_action(
            component_name, request.intent, self.registry.capabilities(component_name))

    def dispatch(self, request: AgentRequest) -> dict[str, Any]:
        component_name = self.route(request)
        component = self.registry.get(component_name)
        if component is None:
            return {"status": "UNAVAILABLE", "component": component_name}
        action = self.action_for(request, component_name)
        if not self.policy.allows(action):
            return {"status": "DENIED", "component": component_name, "action": action}
        target = request.context.get("target", "request")
        result = self.registry.dispatch(component_name, target, action)
        # 组件结果不总带 action（如 udc.inspect_application 走 report()）；
        # 路由决策是宿主可见的契约，缺失时补上，不覆盖组件自己声明的值。
        if isinstance(result, dict):
            result.setdefault("action", action)
        self.session.append({"component": component_name, "action": action, "result": result})
        return result
