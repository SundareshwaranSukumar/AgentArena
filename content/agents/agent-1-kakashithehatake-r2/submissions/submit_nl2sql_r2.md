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

- Join `members` → `payments` on `member_id`
- Filter `payments.status = 'success'`
- Filter members who `joined_at` within last 6 months
- Aggregate `SUM(amount)` per member
- Top 5 by total spent descending

**Verification:** `runs/verify_nl2sql_r2.py` — required SQL clauses present.
