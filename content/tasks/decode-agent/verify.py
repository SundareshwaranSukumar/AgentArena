def encode_shift(s: str) -> str:
    return "".join(chr(((ord(ch) + 5 - ord("a")) % 26) + ord("a")) for ch in s)

def decode_shift(s: str) -> str:
    return "".join(chr(((ord(ch) - 5 - ord("a")) % 26) + ord("a")) for ch in s)

assert decode_shift(encode_shift("hello")) == "hello"
assert decode_shift(encode_shift("abcxyz")) == "abcxyz"
print("decode_shift ok", decode_shift(encode_shift("test")))
