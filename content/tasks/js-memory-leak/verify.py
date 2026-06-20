"""Validate memory leak fix patterns in submission."""
from pathlib import Path

text = Path(r"d:\AgentArena\runs\submit_jsleak_agent3.md").read_text(encoding="utf-8").lower()

required = [
    "removelistener",  # or off(
    "closure",
    "leak",
    "listener",
]
missing = [k for k in required if k not in text]
assert not missing, f"Missing keywords: {missing}"

# Must mention fix strategy
fix_terms = ["remove", "once", "abortsignal", "weakref", "off("]
assert any(t in text for t in fix_terms), "No fix strategy found"

print("js leak submission validation passed")
