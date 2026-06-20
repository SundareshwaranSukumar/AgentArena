**Answer:** Choreography saga: Flight → Hotel → Car. If **Car-Svc (step 3) fails**, compensate **Hotel cancel** then **Flight release**. Flight idempotency via **Idempotency-Key** + dedup store.

**Solution:**

### Choreography Flow (events, no central orchestrator)

```
BOOK_REQUESTED
  → Flight-Svc: FlightReserved
  → Hotel-Svc: HotelBooked
  → Car-Svc: CarRented → BookingConfirmed

Car-Svc failure → CarRentFailed
  → Hotel-Svc: CancelHotel (compensating)
  → Flight-Svc: ReleaseFlight (compensating)
  → BookingAborted
```

### Compensating Transactions (Step 3 fails)

| Step completed | Compensating action |
|----------------|---------------------|
| Flight reserved | `ReleaseFlightReservation(flightId, reason=CAR_FAILED)` |
| Hotel booked | `CancelHotelBooking(hotelId, refundPolicy=FULL)` |
| Car rent failed | (no forward action — triggers saga rollback) |

Order: **cancel hotel first**, then **release flight** (avoid orphan hotel if flight released first).

### Flight-Svc Idempotency on Retries

1. Client sends `Idempotency-Key: {bookingId}:reserve-flight` header
2. Flight-Svc stores `(key → reservationId, status)` in Redis/DB with TTL
3. On retry with same key: return **same reservationId** without double-booking
4. Reserve endpoint is **idempotent** — safe at-least-once delivery from message bus

**Verification:** Saga rollback order and idempotency key pattern satisfy choreography + compensation requirements.
