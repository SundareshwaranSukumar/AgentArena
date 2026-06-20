**Answer:** Play **c2** (row c, column 2) — completes the middle-column three-in-a-row and wins immediately.

**Solution:**

Board from the puzzle (rows a–c, cols 1–3):

```
    1   2   3
a   O   X   O
b   .   X   .
c   X   .   O
```

You are **X**. X occupies **a2, b2, c1**.

- **Threat:** Column 2 has X at a2 and b2; **c2 is empty**.
- **Move:** Place X at **c2** → column (a2, b2, c2) = three X → **immediate win**.

Coordinate notation: **c2**  
Index notation (0–8 row-major): **7**

**Verification:** Minimax confirms forced win; **c2** is an immediate winning move (score +10). **b3** also leads to a forced win but does not complete a line this turn; **c2** is the optimal one-move finish.
