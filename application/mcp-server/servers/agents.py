# (The correct implementation is the block at the top of this file.)
"""Agents for the four main orchestration tasks.

This module prefers to provide four task-specific agents (device-orchestration,
access-control, network-monitoring, verification). When Crew (Auto multi-agent) is not available
the module creates safe stub agents so the server remains testable and
lightweight.
"""
from typing import Any, Dict, Optional, List
import logging


# Internal registry mapping task_name -> agent (or agent wrapper)
_agents: Dict[str, Any] = {}


def _make_stub_agent(name: str):
    class StubAgent:
        def __init__(self, name: str):
            self.name = name

        def run(self, payload: Dict[str, Any]):
            keys = sorted(list(payload.keys()))
            return {"agent": self.name, "note": f"stub response; payload_keys={keys}"}

    return StubAgent(name)


# Try to import Crew at module import time so availability is explicit.
try:
    from crewai import Agent, Task, Crew 

    _crewai_available = True
except Exception:
    Agent = Task = Crew = None  
    _crewai_available = False


_KNOWN_TASKS = (
    ("device-orchestration", "Translate user intent into detailed execution plans containing devices, services, and instruction sequences."),
    ("deployment-monitoring", "Maintain up-to-date device status including IP address, location, services, and connectivity."),
    ("plan-validation", "Validate execution plans against security, energy, transmission, location, and privacy constraints."),
    ("network-configuration", "Configure network settings and manage OTA firmware updates (push/pull modes with RSA-2048 signatures)."),
    ("plan-execution", "Execute orchestration plans by translating high-level instructions into concrete device commands (HTTP, MQTT, etc)."),
    ("access-control", "Manage user permissions, roles, and credentials for device access and plan execution."),
)


def initialize_agents() -> None:
    """Initialize the agent registry for known tasks.

    Safe to call multiple times.
    """
    global _agents
    if _agents:
        return

    if _crewai_available:
        for task_name, instruction in _KNOWN_TASKS:
            try:
                # CrewAI v1.9.2 requires role, goal, and backstory
                a = Agent(
                    role=task_name.replace('-', ' ').title(),
                    goal=instruction,
                    backstory=f"Expert agent specialized in {task_name} for SDN-WISE network orchestration",
                    verbose=False,
                    allow_delegation=False
                )
                _agents[task_name] = {"type": "crew", "agent": a}
                logging.info(f"Initialized CrewAI agent: {task_name}")
            except Exception as e:
                logging.exception(f"Failed to construct crew Agent for {task_name}, falling back to stub: {e}")
                _agents[task_name] = _make_stub_agent(task_name)
    else:
        logging.info("crewai not available; creating stub agents for known tasks")
        for task_name, _ in _KNOWN_TASKS:
            _agents[task_name] = _make_stub_agent(task_name)


def list_agents() -> List[str]:
    """Return the list of known agent/task names."""
    if not _agents:
        initialize_agents()
    return list(_agents.keys())


def get_agent(name: str) -> Optional[Any]:
    if not _agents:
        initialize_agents()
    return _agents.get(name)


def run_agent(name: str, payload: Dict[str, Any]) -> Optional[Any]:
    """Run the agent for a task with the provided payload.

    Returns a structured dict. If Crew is available we construct a Task
    and call `Crew.kickoff()` with a single agent and single task. Any
    errors fall back to a stub-style result so callers never fail due to
    agent runtime errors.
    """
    if not _agents:
        initialize_agents()

    agent = _agents.get(name)
    if not agent:
        return None

    try:
        # Crew-backed agent stored as: {"type": "crew", "agent": <Agent>}
        if isinstance(agent, dict) and agent.get("type") == "crew":
            crew_agent = agent.get("agent")
            try:
                if not _crewai_available:
                    raise RuntimeError("crewai not available at runtime")
                task_obj = Task(name=f"{name}-task", payload=payload)
                crew = Crew(agents=[crew_agent], tasks=[task_obj])
                result = crew.kickoff()
                return {name: {"agent": getattr(crew_agent, "name", str(crew_agent)), "result": result}}
            except Exception:
                logging.exception("Crew execution failed for %s; returning fallback", name)
                return {name: {"agent": getattr(crew_agent, "name", str(crew_agent)), "note": "crew failed"}}

        # Stub or generic agent interface: try run/execute/act
        if hasattr(agent, "run"):
            return agent.run(payload)
        if hasattr(agent, "execute"):
            return agent.execute(payload)
        if hasattr(agent, "act"):
            return agent.act(payload)

        # Fallback: return a simple descriptor
        return {"agent": getattr(agent, "name", str(agent)), "note": "no executable method"}
    except Exception:
        logging.exception("Agent execution failed for %s", name)
        return None
