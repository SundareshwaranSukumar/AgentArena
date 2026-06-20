import math

def dot(a, b):
    return sum(x * y for x, y in zip(a, b))

def cosine(a, b):
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot(a, b) / (na * nb)

# Normalized vectors (unit length)
u = [0.6, 0.8]
v = [0.8, 0.6]
assert abs(math.sqrt(dot(u, u)) - 1.0) < 1e-9
assert abs(dot(u, v) - cosine(u, v)) < 1e-9
print("normalized: dot == cosine", dot(u, v))

# Unnormalized — dot scales with magnitude; cosine is angle-only
a = [3.0, 4.0]  # |a|=5
b = [6.0, 8.0]  # |b|=10, same direction as a
assert abs(cosine(a, b) - 1.0) < 1e-9
assert dot(a, b) == 50.0
assert dot(b, b) > dot(a, a)  # magnitude affects dot ranking
print("unnormalized: same direction cosine=1, dot scales with magnitude")

# Different directions
c = [1.0, 0.0]
d = [0.0, 1.0]
assert cosine(c, d) == 0.0
print("orthogonal: cosine=0")

print("vector math verification passed")
