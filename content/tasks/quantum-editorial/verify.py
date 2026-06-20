"""Validate quantum editorial structure and required concepts."""
from pathlib import Path

text = Path(r"d:\AgentArena\runs\submit_quantum_agent3.md").read_text(encoding="utf-8")

# Extract solution body (after **Solution:**)
body = text.split("**Solution:**", 1)[-1].split("**Verification:**", 1)[0].strip()
paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("**")]

assert len(paragraphs) >= 3, f"Expected 3+ paragraphs, got {len(paragraphs)}"

checks = {
    "entanglement": any(k in body.lower() for k in ("entangl", "spooky", "correlat")),
    "bell": "bell" in body.lower(),
    "non_locality": any(k in body.lower() for k in ("non-local", "nonlocal", "local realism", "local hidden")),
    "cryptography": any(k in body.lower() for k in ("cryptograph", "qkd", "bb84", "secure communication", "key distribution")),
}
for name, ok in checks.items():
    assert ok, f"Missing required concept: {name}"

print("validation passed")
print("paragraphs:", len(paragraphs))
print("checks:", checks)
