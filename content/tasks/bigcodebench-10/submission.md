**Answer:**

```python
import numpy as np
import itertools
import random
import statistics


def task_func(T1, RANGE=100):
    if not T1:
        raise statistics.StatisticsError("T1 is empty")
    size = sum(int(x) for x in T1)
    if size <= 0:
        raise statistics.StatisticsError("no data")
    data = [random.randint(0, RANGE - 1) for _ in range(size)]
    return (
        float(statistics.mean(data)),
        float(statistics.median(data)),
        int(statistics.mode(data)),
    )
```

**Solution:**

1. Raise `statistics.StatisticsError` when `T1` is empty (required).
2. Convert elements to int; `size = sum(...)` determines list length.
3. Generate `size` random integers in `[0, RANGE-1]`.
4. Return mean/median as floats, mode as int via `statistics`.

**Verification:**

Local execution confirms: empty `T1` and zero-sum inputs raise `StatisticsError`; valid input returns `(float, float, int)` tuple. Example with seed 0 and `T1=["2","3"]`: `(47.4, 49.0, 49)`.
