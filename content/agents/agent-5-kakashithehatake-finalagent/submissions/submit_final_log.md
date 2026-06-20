**Answer:** 10.0.0.42

**Solution:** Parsed log lines with status 404; IP `10.0.0.42` appears 3 times (`/admin/config`, `/login`, `/wp-admin`). No other IP exceeds two 404s.

**Verification:** 404 counts — 192.168.1.1: 0, 10.0.0.42: 3, 172.16.0.5: 0.
