# Trace timeline verification
spans = [
    {"id": "span-1", "service": "gatekeeper", "start": 0, "duration": 5, "status": 200},
    {"id": "span-2", "service": "order-svc", "start": 6, "duration": 1500, "status": 504},
    {"id": "span-3", "service": "inventory", "start": 10, "duration": 2000, "status": "WAITING"},
]

order_end = spans[1]["start"] + spans[1]["duration"]  # 1506ms
inv_end = spans[2]["start"] + spans[2]["duration"]  # 2010ms (still waiting)

assert order_end < inv_end, "order-svc times out before inventory completes"
assert spans[2]["status"] == "WAITING", "inventory holds lock / blocked"
lock_holder = spans[2]["service"]
assert lock_holder == "inventory"
print(f"lock_holder={lock_holder} order_timeout_at={order_end}ms inventory_still_waiting_at={inv_end}ms")
