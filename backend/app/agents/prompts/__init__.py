"""System prompts for Maplewood demo agents. One markdown file per agent."""

from pathlib import Path

_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt by agent name, for example ``refund_agent``."""
    path = _DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"No prompt file for {name!r} at {path}")
    return path.read_text(encoding="utf-8").strip() + "\n"
