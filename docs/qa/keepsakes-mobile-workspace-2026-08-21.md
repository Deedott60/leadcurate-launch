# Interactive Digital Keepsakes mobile workspace QA — 2026-08-21

## Scope

- Surface: LeadCurate OS at `http://76.13.25.117/command/`.
- Viewport: 390 × 844 CSS pixels.
- Goal: make Interactive Digital Keepsakes unmistakably separate from Projects and provide one-tap copy controls for the public website and reusable football demos.

## Evidence

- Before: `dashboard-mobile-keepsakes-before.png`.
- After: `dashboard-mobile-keepsakes-copy-links.png`.
- Finished football links: `dashboard-mobile-football-copy-link.png`.
- Side-by-side comparison: `dashboard-mobile-keepsakes-comparison.png`.

## Verification

- A persistent `Keepsakes` shortcut appears in the mobile top bar.
- The destination is titled `Standalone Keepsakes workspace` and explicitly states that it is separate from Projects.
- Product website, Favorite Fan 21+ demo, Queen City Fan demo, and GitHub project each provide visible `Open` and `Copy link` controls.
- Product website and Queen City copy actions both displayed their successful copy confirmation.
- The normal `/command/` URL sends `Cache-Control: no-cache, no-store, must-revalidate`, `Pragma: no-cache`, and `Expires: 0` so phones do not remain on the older Projects-only dashboard.
- Mobile layout has no horizontal overflow and browser console errors are empty.
- Nginx configuration syntax passed and the service is active.

## Findings

- P1 resolved: the phone could retain an older dashboard where Keepsakes appeared only through Projects.
- P1 resolved: mobile resource cards opened destinations but did not expose copyable links.
- No actionable P0, P1, or P2 findings remain for this correction.

final result: passed
