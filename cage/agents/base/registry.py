"""Registry of agent implementations available to Cage."""

from __future__ import annotations

from cage.agents.base.definition import AgentType
from cage.contracts.exceptions import ConfigError

_AGENT_TYPE_REGISTRY: dict[str, type[AgentType]] = {}


def register_agent_type(cls: type[AgentType]) -> type[AgentType]:
    """Register an ``AgentType`` class under its public name."""

    _AGENT_TYPE_REGISTRY[cls.name] = cls
    return cls


def get_agent_type(name: str) -> AgentType:
    """Instantiate a registered agent type by name."""

    cls = _AGENT_TYPE_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_AGENT_TYPE_REGISTRY.keys()))
        raise ConfigError(
            f"Unknown agent kind: {name!r}\n"
            f"  Available agent kinds: {available}\n"
            f"  Set one of these as `kind:` on the agent in your project.yml."
        )
    return cls()
