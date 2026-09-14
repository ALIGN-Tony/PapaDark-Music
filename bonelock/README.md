# BoneLock — antenna wire winder · end insulator · wire lock

3D-printable winder/insulator for adjustable-length wire antennas: wind the unused remainder of one continuous wire onto the body, lock the deployed length with friction wraps around two retained posts, and hang the antenna from the insulated support eye at the far end.

Design target: 150 ft of 18 AWG wire (2.05 mm insulated OD) stored on a body no longer than 10 inches. Prototype status — not printed, load-qualified, or transmitter-tested. Analyzer/VNA power only.

## Revisions

- **`BoneLock_RevC/`** — first compact (250 × 84 mm) sizing. Functionally correct but a straight-sided paddle body that lost the approved smooth styling. Kept for reference; superseded.
- Rev D (restyle with separate bone lobes) was rejected in design review — bulbous look and a thin slotted neck — and removed; it survives only in git history.
- **`BoneLock_RevE/`** — current. Same functional dimensions and keeper interface as Rev C, but one continuous smooth silhouette like the approved rendering: shoulders blending into the winding waist, gentle mid bump, wide solid neck flowing into the support eye. Tool-free retention via printed 20 mm thumb knobs over M3 nylon hardware.

## Retention plan

The captive quick-snap latch shown in the concept rendering is intentionally **not** implemented yet. Rev E uses a removable screw-down keeper so wire routing and friction retention can be bench-tested first. The keeper's mounting interface is frozen and documented in `BoneLock_RevE/Retention_Roadmap.md`, together with the requirements the future quick-snap latch (fast, captive, holds under tension) must meet as a drop-in replacement.

Start with `BoneLock_RevE/README_Print_and_Test.md`.
