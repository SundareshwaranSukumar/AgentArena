# Circuit breaker state machine verification
CLOSED, OPEN, HALF_OPEN = "CLOSED", "OPEN", "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold=3, cooldown_sec=30, half_open_max=1):
        self.state = CLOSED
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.cooldown_sec = cooldown_sec
        self.half_open_max = half_open_max
        self.opened_at = None
        self.half_open_trials = 0
        self.now = 0

    def call(self, fn):
        if self.state == OPEN:
            if self.now - self.opened_at >= self.cooldown_sec:
                self.state = HALF_OPEN
                self.half_open_trials = 0
            else:
                raise RuntimeError("circuit open")

        try:
            result = fn()
            self.on_success()
            return result
        except Exception:
            self.on_failure()
            raise

    def on_success(self):
        if self.state == HALF_OPEN:
            self.state = CLOSED
        self.failures = 0

    def on_failure(self):
        if self.state == HALF_OPEN:
            self.state = OPEN
            self.opened_at = self.now
            return
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = OPEN
            self.opened_at = self.now

cb = CircuitBreaker(failure_threshold=2, cooldown_sec=10)
ok = lambda: "ok"
fail = lambda: (_ for _ in ()).throw(RuntimeError("down"))

assert cb.call(ok) == "ok"
try:
    cb.call(fail)
except RuntimeError:
    pass
try:
    cb.call(fail)
except RuntimeError:
    pass
assert cb.state == OPEN
cb.now = 11
assert cb.call(ok) == "ok"
assert cb.state == CLOSED
print("circuit breaker simulation passed")
