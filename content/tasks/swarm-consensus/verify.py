# Byzantine quorum math for n=50 agents
n = 50
f = (n - 1) // 3  # max Byzantine faults tolerated
quorum = 2 * f + 1

assert f == 16
assert quorum == 33
assert quorum > n // 2  # majority
assert quorum + f <= n  # honest majority exists

# Token-efficient gossip: hash-only rounds vs full diff broadcast
hash_tokens = 64  # sha256 hex + metadata
full_diff_tokens = 2000  # typical patch
agents = 50
rounds = 5
gossip_cost = agents * rounds * hash_tokens
broadcast_cost = agents * full_diff_tokens
savings = 1 - gossip_cost / broadcast_cost

print(f"n={n} f={f} quorum={quorum}")
print(f"gossip_tokens={gossip_cost} broadcast_tokens={broadcast_cost} savings={savings:.1%}")
