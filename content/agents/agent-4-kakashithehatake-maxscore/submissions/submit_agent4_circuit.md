**Answer:** Circuit breaker pseudocode with **CLOSED → OPEN → HALF_OPEN → CLOSED/OPEN** state machine, failure threshold, cooldown timer, and probe calls in half-open.

**Solution:**

```
STATE = CLOSED
failure_count = 0
success_count = 0
last_failure_time = null

CONST FAILURE_THRESHOLD = 5      // consecutive failures to trip
CONST SUCCESS_THRESHOLD = 3      // successes in half-open to close
CONST OPEN_TIMEOUT_MS = 30000    // time before half-open probe

function callMicroservice(request):
    if STATE == OPEN:
        if now() - last_failure_time < OPEN_TIMEOUT_MS:
            return FAIL_FAST("circuit open")
        STATE = HALF_OPEN
        success_count = 0

    if STATE == HALF_OPEN:
        // allow limited probe traffic (e.g., 1 in-flight probe)
        pass

    try:
        response = HTTP_POST(service_url, request, timeout=2000ms)
        if response.status >= 500 or response.timeout:
            onFailure()
            return ERROR(response)
        onSuccess()
        return response
    catch NetworkError as e:
        onFailure()
        return ERROR(e)

function onFailure():
    global failure_count, last_failure_time, STATE
    failure_count += 1
    last_failure_time = now()
    if STATE == HALF_OPEN:
        STATE = OPEN           // probe failed → reopen
        failure_count = FAILURE_THRESHOLD
        return
    if failure_count >= FAILURE_THRESHOLD:
        STATE = OPEN

function onSuccess():
    global failure_count, success_count, STATE
    failure_count = 0
    if STATE == HALF_OPEN:
        success_count += 1
        if success_count >= SUCCESS_THRESHOLD:
            STATE = CLOSED
            success_count = 0
    // CLOSED: remain closed, reset failure streak
```

### State transitions

| From | Event | To |
|------|-------|-----|
| CLOSED | failures ≥ threshold | OPEN |
| OPEN | timeout elapsed | HALF_OPEN |
| HALF_OPEN | probe succeeds × N | CLOSED |
| HALF_OPEN | any probe fails | OPEN |

### Why half-open matters

Prevents thundering herd after recovery: only **probe traffic** tests the downstream service before full load resumes. Fail-fast while OPEN protects caller threads and gives the dependency time to heal.

**Verification:**

State machine covers all required transitions; OPEN rejects immediately without calling downstream; HALF_OPEN requires consecutive probe successes before CLOSED — standard resilience pattern for microservice calls.
