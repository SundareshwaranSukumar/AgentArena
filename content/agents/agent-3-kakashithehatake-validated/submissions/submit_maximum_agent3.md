**Answer:**

```python
def maximum(arr, k):
    if k == 0:
        return []
    return sorted(sorted(arr, reverse=True)[:k])
```

**Solution:**

Return the **k largest** elements from `arr`, sorted in **ascending** order.

Algorithm:
1. Sort `arr` descending and take the first `k` elements (the k maximum values).
2. Sort that sublist ascending for the required output format.

Time: O(n log n) — acceptable for n ≤ 1000.

**Verification:**

`runs/verify_maximum_agent3.py` — all examples pass:
```
maximum() all tests passed
```
- `maximum([-3, -4, 5], 3)` → `[-4, -3, 5]`
- `maximum([4, -4, 4], 2)` → `[4, 4]`
- `maximum([-3, 2, 1, 2, -1, -2, 1], 1)` → `[2]`
