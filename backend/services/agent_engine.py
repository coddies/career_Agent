"""
backend/services/agent_engine.py — ReAct loop adapter with trace collection.

Wraps career_agent.agent.run_react_loop() and injects a trace collector
so the API layer can return Thought/Action/Observation logs to the frontend.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from fastapi import HTTPException

# Import core agent modules from sibling package
import career_agent.agent as _core_agent
import career_agent.llm_cascade as _cascade
from career_agent.state_adapter import NeutralHistory, append_user

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RESULT DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """Structured result from a single agent turn."""
    response: str
    active_provider: str
    failover_occurred: bool
    turns_taken: int
    agent_traces: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# TRACE-ENABLED REACT LOOP
# ---------------------------------------------------------------------------

def run_agent_turn(history: NeutralHistory, user_message: str) -> AgentResult:
    """
    Append the user message to history and run the ReAct loop.
    Collects Thought/Action/Observation traces for the response metadata.

    Args:
        history: Mutable provider-agnostic conversation history.
        user_message: Validated user input string.

    Returns:
        AgentResult with response, provider info, and trace list.

    Raises:
        HTTPException 500: If all model tiers are exhausted.
    """
    append_user(history, user_message)

    traces: list[str] = []
    providers_used: list[str] = []
    turns_counter = [0]   # mutable reference for inner closure

    # ── Patch the cascade to intercept per-turn provider info ────────────
    original_cascade = _cascade.call_with_cascade

    def traced_cascade(hist: NeutralHistory, enable_tools: bool = True):
        turns_counter[0] += 1
        result = original_cascade(hist, enable_tools=enable_tools)
        provider = result.get("provider", "Unknown")
        providers_used.append(provider)
        traces.append(f"[TURN {turns_counter[0]}] Provider: {provider}")
        return result

    # ── Patch tool executor to capture observations ───────────────────────
    original_execute = _core_agent._execute_tool

    def traced_execute(tool_name: str, arguments: dict) -> str:
        traces.append(f"[ACTION] Calling tool: {tool_name}({list(arguments.keys())})")
        observation = original_execute(tool_name, arguments)
        short_obs = observation[:150] + "..." if len(observation) > 150 else observation
        traces.append(f"[OBSERVATION] {short_obs}")
        return observation

    # Apply patches
    _cascade.call_with_cascade = traced_cascade
    _core_agent._execute_tool = traced_execute

    try:
        response_text = _core_agent.run_react_loop(history)
    except RuntimeError as exc:
        logger.error(f"[AgentEngine] All tiers exhausted: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"All model tiers are temporarily unavailable. Please retry in a moment. ({exc})",
        )
    finally:
        # Always restore originals — never leave patches active
        _cascade.call_with_cascade = original_cascade
        _core_agent._execute_tool = original_execute

    final_provider = providers_used[-1] if providers_used else "Unknown"
    failover = len(set(providers_used)) > 1

    return AgentResult(
        response=response_text,
        active_provider=final_provider,
        failover_occurred=failover,
        turns_taken=turns_counter[0],
        agent_traces=traces,
    )
