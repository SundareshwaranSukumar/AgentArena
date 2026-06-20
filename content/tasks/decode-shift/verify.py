def encode_shift(s: str) -> str:
    return "".join(chr(((ord(ch) + 5 - ord("a")) % 26) + ord("a")) for ch in s)


def decode_shift(s: str) -> str:
    return "".join(chr(((ord(ch) - 5 - ord("a")) % 26) + ord("a")) for ch in s)


for word in ["hello", "world", "abcxyz", "a"]:
    assert decode_shift(encode_shift(word)) == word, word

encoded = encode_shift("hello")
assert decode_shift(encoded) == "hello"
assert encoded == "mjqqt"
print("ok", encoded, "->", decode_shift(encoded))
