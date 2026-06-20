text = open(r"d:\AgentArena\runs\submit_ratelimit_agent3.md", encoding="utf-8").read().lower()
for term in ["token bucket", "redis", "in-memory", "lua", "distributed", "race"]:
    assert term.replace("-", " ").replace("in memory", "in-memory") in text or term in text, term
print("rate limiter design validation passed")
