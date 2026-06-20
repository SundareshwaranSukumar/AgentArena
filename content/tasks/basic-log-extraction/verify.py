from collections import Counter
import re

LOG = """
2026-04-18 10:01:05 INFO 192.168.1.1 GET /index.html 200
2026-04-18 10:02:12 WARN 10.0.0.42 GET /admin/config 404
2026-04-18 10:02:45 INFO 192.168.1.1 GET /styles.css 200
2026-04-18 10:03:01 WARN 10.0.0.42 GET /login 404
2026-04-18 10:04:10 WARN 10.0.0.42 GET /wp-admin 404
2026-04-18 10:05:05 INFO 172.16.0.5 GET /api/v1/status 200
"""

counts = Counter()
for line in LOG.strip().splitlines():
    if " 404" in line or line.rstrip().endswith("404"):
        ip = re.search(r"\b(\d+\.\d+\.\d+\.\d+)\b", line).group(1)
        counts[ip] += 1

result = [ip for ip, c in counts.items() if c > 2]
assert result == ["10.0.0.42"], result
print(result[0])
