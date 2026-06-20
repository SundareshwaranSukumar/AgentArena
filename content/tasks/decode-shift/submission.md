**Answer:**

```python
def decode_shift(s: str) -> str:
    return "".join(chr(((ord(ch) - 5 - ord("a")) % 26) + ord("a")) for ch in s)
```

**Solution:**

`encode_shift` shifts each lowercase letter forward by 5 (mod 26). `decode_shift` reverses with −5 (equivalent to +21 mod 26).

**Verification:**

`decode_shift("mjqqt")` returns `"hello"`. Round-trip holds for `hello`, `world`, `abcxyz`.
