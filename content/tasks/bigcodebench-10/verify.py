import statistics
import random

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

random.seed(0)
r = task_func(["1", "2"])
assert len(r) == 3
assert isinstance(r[0], float) and isinstance(r[1], float) and isinstance(r[2], int)
assert len(task_func(["2"])) == 3  # size=2 list
try:
    task_func([])
except statistics.StatisticsError:
    pass
else:
    raise AssertionError("expected StatisticsError")
print("bcb10 validation passed", r)
