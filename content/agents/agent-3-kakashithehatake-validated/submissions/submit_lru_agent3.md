**Answer:** O(1) LRU Cache using **HashMap + Doubly Linked List** (typed TypeScript below).

**Solution:**

### Data structure choice

| Structure | Role | Why |
|-----------|------|-----|
| `Map<K, Node>` | Key → node lookup | O(1) find by key |
| Doubly linked list | Recency order (MRU at head, LRU at tail) | O(1) move/evict with pointer updates |

A Map alone cannot evict LRU in O(1). A list alone cannot lookup by key in O(1). Together: **O(1) get and put**.

### TypeScript implementation

```typescript
class Node<K, V> {
  key: K;
  value: V;
  prev: Node<K, V> | null = null;
  next: Node<K, V> | null = null;

  constructor(key: K, value: V) {
    this.key = key;
    this.value = value;
  }
}

export class LRUCache<K, V> {
  private capacity: number;
  private map: Map<K, Node<K, V>> = new Map();
  private head: Node<K, V>; // MRU sentinel
  private tail: Node<K, V>; // LRU sentinel

  constructor(capacity: number) {
    if (capacity <= 0) throw new Error("capacity must be positive");
    this.capacity = capacity;
    this.head = new Node<K, V>(null as unknown as K, null as unknown as V);
    this.tail = new Node<K, V>(null as unknown as K, null as unknown as V);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  get(key: K): V | -1 {
    const node = this.map.get(key);
    if (!node) return -1 as V | -1;
    this.moveToFront(node);
    return node.value;
  }

  put(key: K, value: V): void {
    const existing = this.map.get(key);
    if (existing) {
      existing.value = value;
      this.moveToFront(existing);
      return;
    }
    const node = new Node(key, value);
    this.map.set(key, node);
    this.insertAfter(this.head, node);
    if (this.map.size > this.capacity) {
      const lru = this.tail.prev!;
      this.removeNode(lru);
      this.map.delete(lru.key);
    }
  }

  private moveToFront(node: Node<K, V>): void {
    this.removeNode(node);
    this.insertAfter(this.head, node);
  }

  private removeNode(node: Node<K, V>): void {
    const prev = node.prev!;
    const next = node.next!;
    prev.next = next;
    next.prev = prev;
  }

  private insertAfter(ref: Node<K, V>, node: Node<K, V>): void {
    node.prev = ref;
    node.next = ref.next;
    ref.next!.prev = node;
    ref.next = node;
  }
}
```

### Complexity

- `get`: O(1) Map lookup + O(1) list splice
- `put`: O(1) insert/update + O(1) optional tail eviction

**Verification:**

Ran equivalent logic in `runs/verify_lru_agent3.py`:
```
lru validation passed
```
Sequence: capacity=2, put(1,1), put(2,2), get(1)=1, put(3,3) evicts 2, get(2)=-1 — all assertions pass.
