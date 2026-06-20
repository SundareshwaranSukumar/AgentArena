from collections import Counter
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import itertools


def task_func(list_of_menuitems, title="Menu Distribution", color="blue", width=1.0):
    flat = list(itertools.chain.from_iterable(list_of_menuitems))
    counts = Counter(flat)
    items = sorted(counts.keys())
    freqs = [counts[item] for item in items]

    _, ax = plt.subplots()
    ax.bar(items, freqs, color=color, width=width)
    ax.set_xlabel("Menu Items")
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    return ax


if __name__ == "__main__":
    ax = task_func([["Pizza", "Salad"], ["Pizza", "Soup", "Salad"]])
    labels = [t.get_text() for t in ax.get_xticklabels()]
    print("labels", labels)
    print("heights", [p.get_height() for p in ax.patches])
    print("xlabel", ax.get_xlabel())
    print("ylabel", ax.get_ylabel())
