**Answer:**

```sql
SELECT
  m.id,
  m.email,
  SUM(p.amount) AS total_spent
FROM members m
INNER JOIN payments p ON p.member_id = m.id
WHERE p.status = 'success'
  AND m.joined_at >= CURRENT_TIMESTAMP - INTERVAL '6 months'
GROUP BY m.id, m.email
ORDER BY total_spent DESC
LIMIT 5;
```

**Solution:**

1. Join `members` to `payments` on `member_id`.
2. Filter successful payments only (`status = 'success'`).
3. Restrict to members who joined within the last 6 months.
4. Aggregate `SUM(amount)` per member; return top 5 by total spent descending.

**Verification:**

Query includes JOIN, success filter, 6-month window on `joined_at`, GROUP BY, ORDER BY DESC, LIMIT 5 — satisfies all request constraints.
