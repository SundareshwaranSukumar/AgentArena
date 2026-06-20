**Answer:**

```python
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import itertools


def task_func(list_of_menuitems, title="Menu Distribution", color="blue", width=1.0):
    flat = list(itertools.chain.from_iterable(list_of_menuitems))
    counts = Counter(flat)
    items = sorted(counts.keys())
    freqs = [counts[item] for item in items]
    fig, ax = plt.subplots()
    ax.bar(items, freqs, color=color, width=width)
    ax.set_xlabel("Menu Items")
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    return ax
```

**Solution:**

1. Flatten nested menu lists via `itertools.chain.from_iterable`.
2. Count occurrences with `Counter`.
3. Sort items alphabetically for x-axis order.
4. Plot bar histogram; label axes per spec; return `ax`.

**Verification:**

Sample input `[["burger","fries"],["burger","salad"]]` yields sorted x-labels and correct axis titles.
