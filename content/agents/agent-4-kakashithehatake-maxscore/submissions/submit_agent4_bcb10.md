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
    mean = float(statistics.mean(data))
    median = float(statistics.median(data))
    mode = int(statistics.mode(data))
    return (mean, median, mode)
```

**Solution:**

1. **Validate input** — empty `T1` raises `statistics.StatisticsError` as required.
2. **Convert & size** — cast each element to `int`; `size = sum(...)` determines how many random draws to generate.
3. **Generate list** — `size` integers uniformly in `[0, RANGE - 1]` via `random.randint`.
4. **Statistics** — `statistics.mean` and `statistics.median` as `float`; `statistics.mode` as `int`.
5. **Edge case** — if converted sum is ≤ 0 (e.g. `T1 = [0]`), statistics on an empty generated list also raises `StatisticsError`.

**Verification:**

- Empty `T1` → `StatisticsError` (confirmed).
- `T1 = ["1", "2", "3"]` → sum = 6 → tuple of `(float, float, int)`; e.g. with seed 42: `(43.0, 33.0, 81)`.
- Return type matches spec: mean/median floats, mode integer.
