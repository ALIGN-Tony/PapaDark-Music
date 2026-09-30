# BoneLock — antenna wire winder · end insulator · wire lock

3D-printable winder/insulator for adjustable-length wire antennas: wind the unused remainder of one continuous wire onto the body, lock the deployed length with friction wraps around two retained posts, and hang the antenna from the insulated support eye at the far end.

Design target: 150 ft of wire stored on a body no longer than 10 inches — Rev F sized for 18 AWG / 2.05 mm OD, Rev G for FIPNOT 20 AWG silicone / 1.8 mm OD. Prototype status — not printed, load-qualified, or transmitter-tested. Analyzer/VNA power only.

## Revisions

- **`BoneLock_RevC/`** — first compact (250 × 84 mm) sizing. Functionally correct but a straight-sided paddle body that lost the approved smooth styling. Kept for reference; superseded.
- Rev D (separate bone lobes; bulbous, thin slotted neck) and Rev E (continuous flat silhouette) were review iterations, removed from the tree; they survive in git history.
- **`BoneLock_RevF/`** — full-size (250 × 84 mm) sculpted design for 18 AWG / 2.05 mm OD wire: continuous smooth silhouette, domed coil flanges bracketing the winding waist, bone-end lobes, thick rounded support-eye ring, recessed K4DIA mark, flat printable underside. Tool-free retention via printed 20 mm thumb knobs over M3 nylon hardware.
- **`BoneLock_RevG/`** — current. Compact resize (210 × 72 mm) of Rev F for the purchased FIPNOT 20 AWG silicone wire (1.8 mm OD): same 150 ft target wound in 7 layers, same sculpt and mark, hardware and keeper interface unchanged (Rev F keepers/knobs fit). Fits a standard 220 × 220 mm bed.

## Retention plan

The captive quick-snap latch shown in the concept rendering is intentionally **not** implemented yet. Rev F/G use a removable screw-down keeper so wire routing and friction retention can be bench-tested first. The keeper's mounting interface is frozen and documented in `BoneLock_RevG/Retention_Roadmap.md`, together with the requirements the future quick-snap latch (fast, captive, holds under tension) must meet as a drop-in replacement.

Start with `BoneLock_RevG/README_Print_and_Test.md` (compact, 20 AWG silicone) or `BoneLock_RevF/README_Print_and_Test.md` (full-size, 18 AWG).
