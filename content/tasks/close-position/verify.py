from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    nums = sorted(numbers)
    for i in range(1, len(nums)):
        if nums[i] - nums[i - 1] < threshold:
            return True
    return False

assert has_close_elements([1.0, 2.0, 3.0], 0.5) is False
assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) is True
assert has_close_elements([], 0.1) is False
assert has_close_elements([1.0], 0.1) is False
print("has_close_elements validation passed")
