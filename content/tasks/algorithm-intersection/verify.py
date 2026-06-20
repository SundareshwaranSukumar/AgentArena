def intersection_naive(arr1, arr2):
    result = []
    for a in arr1:
        for b in arr2:
            if a == b and a not in result:
                result.append(a)
    return result


def intersection(arr1, arr2):
    lookup = set(arr2)
    seen = set()
    result = []
    for value in arr1:
        if value in lookup and value not in seen:
            result.append(value)
            seen.add(value)
    return result


assert intersection([1, 2, 3, 2, 1], [2, 2, 3, 4]) == [2, 3]
assert intersection([], [1, 2]) == []
assert intersection([1, 2], []) == []
assert intersection([1, 1, 1], [1]) == [1]
print("ok")
