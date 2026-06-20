**Answer:**

```python
def intersection(arr1, arr2):
    """Return elements appearing in both arrays, preserving first-array order, O(n) time."""
    lookup = set(arr2)          # O(n) space, O(n) build
    seen = set()
    result = []
    for value in arr1:          # O(n) single pass
        if value in lookup and value not in seen:
            result.append(value)
            seen.add(value)
    return result
```

**Solution:**

**Before (O(n²)):** nested loops compare every pair; duplicate suppression uses `not in result` (another O(n) scan).

**After (O(n)):**
1. Build `set(arr2)` for O(1) membership checks.
2. Single pass over `arr1`; append values present in `set2` once using `seen`.
3. Time **O(n + m)**, space **O(n + m)** — linear vs quadratic.

**Verification:**

| arr1 | arr2 | Output |
|------|------|--------|
| `[1,2,3,2,1]` | `[2,2,3,4]` | `[2, 3]` |
| `[]` | `[1,2]` | `[]` |
| `[1,1,1]` | `[1]` | `[1]` |

Matches naive intersection on test cases; complexity reduced from O(n²) to O(n).
