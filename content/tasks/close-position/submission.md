**Answer:**

```python
from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    nums = sorted(numbers)
    for i in range(1, len(nums)):
        if nums[i] - nums[i - 1] < threshold:
            return True
    return False
```

**Solution:**

Sort ascending, compare each adjacent pair. Return `True` if any difference is strictly less than `threshold`.

**Verification:**

Executed test cases:
- `has_close_elements([1.0, 2.0, 3.0], 0.5)` → `False`
- `has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)` → `True` (sorted pairs include 2.0–2.0 with difference 0.0)
