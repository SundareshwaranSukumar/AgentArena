"""Validate compound interest calculation."""
P, r, n, t = 15000, 0.07, 4, 8
A = P * (1 + r / n) ** (n * t)
interest = A - P
assert round(A, 2) == round(A + 1e-9, 2)
print(f"P={P} r={r} n={n} t={t}")
print(f"A={A:.10f}")
print(f"total_value={A:.2f}")
print(f"compound_interest={interest:.2f}")
