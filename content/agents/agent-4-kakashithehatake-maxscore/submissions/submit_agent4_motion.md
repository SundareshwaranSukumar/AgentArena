**Answer:** As of **April 2026**, the latest stable **Motion** (formerly Framer Motion) release is **`12.38.0`** (published March 17, 2026 on npm — the next stable, 12.39.0, shipped May 18, 2026).

**Top 3 major v12.x changes / improvements:**

1. **Package & import migration (`framer-motion` → `motion`)** — The React animation library was rebranded to **Motion**; recommended install is `npm install motion` with imports from `"motion/react"` instead of `"framer-motion"`. v12.0 explicitly states **no breaking React API changes** for this migration (see upgrade guide).
2. **React 19 / concurrent rendering support** — v12 adds full compatibility with React 19 concurrent features, ensuring layout, gesture, and spring animations behave correctly under modern React scheduling.
3. **Hybrid animation engine performance** — v12 continues the hybrid JS + native **WAAPI/GPU-accelerated** pipeline marketed for **120fps** animations, with improved layout projection and scroll-linked effects (`whileInView`, layout groups) for production-scale UIs.

**Sources:**
- npm package versions: https://www.npmjs.com/package/motion?activeTab=versions
- Motion React upgrade guide (v12 / `motion/react`): https://motion.dev/docs/react-upgrade-guide
- Motion overview (rename note): https://www.npmjs.com/package/motion

**Solution:**

Queried npm version history for `motion` and filtered to releases **on or before April 30, 2026**. The highest semver in that window is **12.38.0** (2026-03-17). Cross-checked the official upgrade guide for v12-specific API and migration notes.

**Verification:**

Version timeline from npm: 12.38.0 (Mar 17, 2026) → gap → 12.39.0 (May 18, 2026) → 12.40.0 (May 21, 2026). Therefore April 2026 latest stable = **12.38.0**. v12 migration and React 19 compatibility documented on motion.dev.
