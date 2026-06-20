**Answer:** `10.0.0.42`

**Solution:**

Parsed each log line for IP and HTTP status:

| IP | Status codes |
|---|---|
| 192.168.1.1 | 200, 200 |
| **10.0.0.42** | **404, 404, 404** (3×) |
| 172.16.0.5 | 200 |

Only **10.0.0.42** produced more than two 404 responses (`/admin/config`, `/login`, `/wp-admin`).

**Verification:**

404 count by IP: `{192.168.1.1: 0, 10.0.0.42: 3, 172.16.0.5: 0}` — unique IP with count > 2 is **10.0.0.42**.
