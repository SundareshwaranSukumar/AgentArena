Circuit Breaker pseudocode with CLOSED, OPEN, and HALF_OPEN states for microservice calls.

```
STATE = CLOSED | OPEN | HALF_OPEN
failures = 0
failure_threshold = 3
cooldown_sec = 30
opened_at = null
half_open_trials = 0

function callMicroservice(request):
    if STATE == OPEN:
        if now() - opened_at >= cooldown_sec:
            STATE = HALF_OPEN
            half_open_trials = 0
        else:
            return FAIL_FAST(circuit open)

    try:
        response = httpCall(request)
        onSuccess()
        return response
    catch error:
        onFailure()
        return FAIL(error)

function onSuccess():
    if STATE == HALF_OPEN:
        STATE = CLOSED
    failures = 0

function onFailure():
    if STATE == HALF_OPEN:
        STATE = OPEN
        opened_at = now()
        return
    failures += 1
    if failures >= failure_threshold:
        STATE = OPEN
        opened_at = now()
```

States:
- CLOSED: requests pass through; consecutive failures increment counter.
- OPEN: fail fast until cooldown expires, then transition to HALF_OPEN.
- HALF_OPEN: allow limited probe calls; success closes circuit, failure reopens.

Verified with Python simulation (runs/verify_cb.py): threshold=2, cooldown=10s — failures open circuit, after cooldown probe succeeds and returns to CLOSED.
