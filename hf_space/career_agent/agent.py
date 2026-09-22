"""
agent.py — ReAct (Thought -> Action -> Observation) Loop Engine.

Executes up to MAX_TURNS iterations per request:
  1. Model emits a Thought + optional Action (tool call).
  2. Agent executes the tool and collects the Observation.
  3. Observation is appended to history and the loop continues.
  4. When the model emits no tool calls, the response is final.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from career_agent.config import MAX_TURNS
from career_agent.llm_cascade import call_with_cascade
from career_agent.state_adapter import (
    NeutralHistory,
    append_assistant,
    append_tool_result,
)
from career_agent.tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TOOL EXECUTOR
# ---------------------------------------------------------------------------

def _execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """
    Dispatch a tool call from the registry with full error handling.

    Args:
        tool_name: Name of the tool to execute.
        arguments: Keyword arguments to pass to the tool function.

    Returns:
        Plain string observation — either the tool result or an error message.
    """
    if tool_name not in TOOL_REGISTRY:
        available = list(TOOL_REGISTRY.keys())
        logger.error(f"[Tool] Unknown tool requested: '{tool_name}'. Available: {available}")
        return (
            f"Observation: Error — Unknown tool '{tool_name}'. "
            f"Available tools: {available}. Please retry with a valid tool name."
        )

    try:
        func = TOOL_REGISTRY[tool_name]

        # arguments may arrive as a JSON string from some providers
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        result = func(**arguments)
        return str(result)

    except TypeError as exc:
        logger.error(f"[Tool] {tool_name} argument error: {exc}")
        return f"Observation: Error in {tool_name} — Invalid arguments: {exc}"
    except Exception as exc:
        logger.error(f"[Tool] {tool_name} execution error: {exc}")
        return f"Observation: Error in {tool_name} — {exc}"


# ---------------------------------------------------------------------------
# REACT LOOP ENGINE
# ---------------------------------------------------------------------------

def run_react_loop(history: NeutralHistory) -> str:
    """
    Execute the ReAct (Thought -> Action -> Observation) loop.

    The loop continues until:
      - The model returns a response with no tool calls (final answer).
      - MAX_TURNS iterations are reached (hard cap to prevent infinite loops).
      - The LLM cascade is fully exhausted (RuntimeError).

    Args:
        history: Provider-agnostic conversation history. Modified in-place
                 as the loop appends assistant and tool messages.

    Returns:
        Final assistant response text string.
    """
    last_content: str = ""
    turn: int = 0

    while turn < MAX_TURNS:
        turn += 1
        logger.info(f"[ReAct] ─── Turn {turn}/{MAX_TURNS} ───")

        # ── THOUGHT + ACTION PHASE ────────────────────────────────────────
        try:
            response = call_with_cascade(history, enable_tools=True)
        except RuntimeError as exc:
            logger.error(f"[ReAct] Cascade fully exhausted at turn {turn}: {exc}")
            return (
                "I'm temporarily unable to respond — all model tiers are unavailable. "
                "Please try again in a moment.\n\n"
                f"Technical detail: {exc}"
            )

        content: str = response.get("content", "")
        tool_calls: list[dict] = response.get("tool_calls", [])
        provider: str = response.get("provider", "Unknown")
        last_content = content

        logger.info(
            f"[ReAct] Provider={provider} | "
            f"tool_calls={len(tool_calls)} | "
            f"content_len={len(content)}"
        )

        # ── FINAL RESPONSE (no tool calls) ───────────────────────────────
        if not tool_calls:
            append_assistant(history, content)
            logger.info(f"[ReAct] Final answer received from {provider} at turn {turn}.")
            return content

        # ── OBSERVATION PHASE — execute each tool call ────────────────────
        append_assistant(history, content, tool_calls=tool_calls)

        for tc in tool_calls:
            fn = tc.get("function", {})
            tool_name: str = fn.get("name", "")
            arguments: Any = fn.get("arguments", {})
            tool_call_id: str = tc.get("id", "call_0")

            logger.info(
                f"[ReAct] Executing tool: {tool_name}("
                f"{list(arguments.keys()) if isinstance(arguments, dict) else arguments})"
            )

            observation: str = _execute_tool(tool_name, arguments)
            logger.info(f"[ReAct] Observation [{tool_name}]: {observation[:120]}...")

            append_tool_result(
                history,
                tool_name=tool_name,
                result=observation,
                tool_call_id=tool_call_id,
            )

    # ── MAX TURNS REACHED ─────────────────────────────────────────────────
    logger.warning(f"[ReAct] Max turns ({MAX_TURNS}) reached. Returning last content.")
    return last_content or "Analysis complete. Please see the observations in the conversation above."
