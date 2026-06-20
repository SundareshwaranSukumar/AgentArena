"""Validate NL2SQL membership query structure."""
sql = open(r"d:\AgentArena\runs\submit_nl2sql_r2.md", encoding="utf-8").read().lower()
for kw in ["select", "members", "payments", "success", "6 month", "group by", "order by", "limit 5", "sum"]:
    assert kw in sql.replace("'", ""), kw
print("nl2sql validation passed")
