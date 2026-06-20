def maximum(arr, k):
    if k == 0:
        return []
    return sorted(sorted(arr, reverse=True)[:k])

tests = [
    ([-3, -4, 5], 3, [-4, -3, 5]),
    ([4, -4, 4], 2, [4, 4]),
    ([-3, 2, 1, 2, -1, -2, 1], 1, [2]),
    ([1, 2, 3], 0, []),
]
for arr, k, expected in tests:
    result = maximum(arr, k)
    assert result == expected, f"fail arr={arr} k={k}: got {result} expected {expected}"
print("maximum() all tests passed")
