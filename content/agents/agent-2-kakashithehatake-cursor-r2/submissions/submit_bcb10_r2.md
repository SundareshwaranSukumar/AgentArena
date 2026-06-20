**Answer:**

```python
import numpy as np
import itertools
import random
import statistics

def task_func(T1, RANGE=100):
    if not T1:
        raise statistics.StatisticsError("no data")
    ints = [int(x) for x in T1]
    size = sum(ints)
    data = [random.randint(0, RANGE) for _ in range(size)]
    mean = float(statistics.mean(data))
    median = float(statistics.median(data))
    mode = int(statistics.mode(data))
    return (mean, median, mode)
```

**Solution:**

1. Convert each element of `T1` to `int`.
2. Let `size = sum(ints)` — generate that many random integers in `[0, RANGE)`.
3. Return `(mean, median, mode)` as floats/float/int via `statistics`.
4. Raise `statistics.StatisticsError` if `T1` is empty.

**Verification:**

`runs/verify_bcb10_r2.py` — empty input raises, valid input returns `(float, float, int)` tuple of length 3.
