**Answer:**

```python
def decode_shift(s: str) -> str:
    return "".join(
        chr(((ord(ch) - 5 - ord("a")) % 26) + ord("a"))
        for ch in s
    )
```

**Solution:**

`encode_shift` shifts each lowercase letter forward by 5 in the alphabet (wrap-around). `decode_shift` reverses with a **−5** shift (equivalent to +21 mod 26).

**Verification:** Round-trip `decode_shift(encode_shift("hello")) == "hello"` confirmed.
