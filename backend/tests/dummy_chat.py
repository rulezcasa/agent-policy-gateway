"""Simple CLI chat testbed for the routing orchestrator."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Make `app` importable when run from the repo root or backend/.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.orchestrator import continue_after_approval, orchestrate
from app.agents.state import init_state
from app.policy_engine.store import get_pending
from app.settings import USE_GATEWAY, agent_mcp_url

init_state()


async def _wait_for_decision(action_id: str) -> dict:
    while True:
        task = get_pending(action_id)
        if task and task.get("status") in {"executed", "rejected"}:
            return task
        await asyncio.sleep(1)


async def _chat_loop() -> None:
    print("=== Maplewood CLI Chat Testbed ===")
    mode = "gateway (policy checks on)" if USE_GATEWAY else "direct tools (policy checks off)"
    print(f"Path: {mode} → {agent_mcp_url()}")
    print("Type 'exit' to quit.\n")

    phone = "555-0198"

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Exiting chat. Goodbye!")
            return

        result = await orchestrate(phone, user_input)
        customer_message = result.get("customer_message")
        if customer_message:
            print(f"Bot: {customer_message}\n")
            continue

        pending_id = result.get("pending_action_id")
        if not pending_id:
            print(f"Bot: {result['reply']}\n")
            continue

        print(
            "Bot: Your request has been submitted and needs approval. "
            "You'll hear back shortly.\n"
        )
        task = await _wait_for_decision(pending_id)
        if task.get("status") == "executed":
            follow_up = await continue_after_approval(pending_id)
            print(f"Bot: {follow_up}\n")
        else:
            print("Bot: Your request was declined.\n")


def main() -> None:
    asyncio.run(_chat_loop())


if __name__ == "__main__":
    main()
