"""Simple CLI chat testbed for the routing orchestrator."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Make `app` importable when run from the repo root or backend/.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.orchestrator import orchestrate
from app.agents.state import init_state

init_state()


async def _chat_loop() -> None:
    print("=== Maplewood CLI Chat Testbed ===")
    print("Type 'exit' to quit.\n")

    phone = "555-0198"

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Exiting chat. Goodbye!")
            return

        response = await orchestrate(phone, user_input)
        print(f"Bot: {response}\n")


def main() -> None:
    asyncio.run(_chat_loop())


if __name__ == "__main__":
    main()
