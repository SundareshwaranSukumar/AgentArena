from datetime import date, timedelta

today = date(2026, 6, 20)  # session date
future = today + timedelta(days=365 * 10 + 2)  # ~10 years
birth = date(1809, 2, 12)
death = date(1865, 4, 15)

hypothetical_age = future.year - birth.year - ((future.month, future.day) < (birth.month, birth.day))
years_since_death = (future - death).days // 365

print(f"today={today} future~={future}")
print(f"hypothetical_age_if_alive={hypothetical_age}")
print(f"deceased_since={death}")
print(f"actual_status=deceased; cannot age")
