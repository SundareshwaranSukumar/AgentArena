**Answer:** The fork started at block height **1002**. The attacker is **NODE_EVIL**.

**Solution:**

### Fork Analysis

| Height | Hash | Miner | TXs | Chain |
|--------|------|-------|-----|-------|
| 1001 | 0xA... | NODE_1 | 50 | Canonical (genesis path) |
| 1002 | 0xB... | NODE_2 | 55 | Canonical |
| **1002** | **0xC...** | **NODE_EVIL** | **500** | **Ghost Chain (malicious fork)** |
| 1003 | 0xD... | NODE_EVIL | 500 | Ghost Chain continuation |

### Indicators of 51% / malicious fork

1. **Duplicate block height (1002):** Two competing blocks at the same height — canonical (`0xB`, NODE_2) and adversarial (`0xC`, NODE_EVIL). A fork always begins where two valid-looking blocks share the same parent height.

2. **Ghost Chain label:** Block `0xC` is explicitly marked as a ghost chain — an alternate history built in secret and released to outpace the honest chain.

3. **Abnormal TX volume:** NODE_EVIL blocks carry **500 TXs** vs 50–55 on honest blocks — consistent with an attacker stuffing blocks to maximize revenue (double-spend / reorder attacks).

4. **Miner concentration:** NODE_EVIL mines both fork block (1002) and its successor (1003), indicating sustained hashpower control typical of a 51% attack.

### Conclusion

- **Fork start height:** `1002` (first point of chain divergence from block 1001)
- **Attacker Miner ID:** `NODE_EVIL`
