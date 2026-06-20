**Answer:** O(1) LRU Cache in Python using **dict + doubly linked list** (Python port of the TypeScript TypescriptCodeGen task).

**Solution:**

```python
class Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.map = {}
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key: int) -> int:
        node = self.map.get(key)
        if not node:
            return -1
        self._move_to_front(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.map:
            node = self.map[key]
            node.value = value
            self._move_to_front(node)
            return
        node = Node(key, value)
        self.map[key] = node
        self._insert_after(self.head, node)
        if len(self.map) > self.capacity:
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]

    def _move_to_front(self, node):
        self._remove(node)
        self._insert_after(self.head, node)

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_after(self, ref, node):
        node.prev = ref
        node.next = ref.next
        ref.next.prev = node
        ref.next = node
```

- `dict` → O(1) key lookup
- Doubly linked list → O(1) recency updates and LRU eviction
- `get` / `put` both **O(1)**

**Verification:**

Capacity=2 sequence: put(1,1), put(2,2), get(1)=1, put(3,3) evicts 2, get(2)=-1, put(4,4) evicts 1 — all assertions pass.
