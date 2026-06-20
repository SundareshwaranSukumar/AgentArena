expected = {
    "codename": "Ares",
    "teams": {"Vulcan", "Hermes"},
    "conflict_keywords": ["400khz", "1mhz", "spi", "clock"],
}
text = open(r"d:\AgentArena\runs\submit_rag_agent3.md", encoding="utf-8").read().lower()
assert "ares" in text
assert "vulcan" in text and "hermes" in text
hits = sum(1 for k in expected["conflict_keywords"] if k in text)
assert hits >= 3, f"conflict keywords found: {hits}"
print("rag synthesis validation passed")
