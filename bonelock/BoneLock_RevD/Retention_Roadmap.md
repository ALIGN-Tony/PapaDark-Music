# BoneLock retention roadmap

Written 14 September 2026 for Rev D.

## Where retention stands

The initial rendering shows a captive sliding wire keeper. That latch has never been designed in CAD — the rendering is a visual concept only. Revisions C and D deliberately use a simpler removable keeper so the wire path, friction-wrap geometry, and post loading can be physically tested before any latch is engineered around them.

- **Rev C:** keeper + two M3 nylon screws, loose nuts, tools or fingers on small hardware.
- **Rev D (current):** same keeper interface, now tightened by two printed 20 mm thumb knobs with captured M3 nylon nuts — fully tool-free, but still a spin-on/spin-off action, not a quick snap.

Test Rev D first. The slip loads, wrap counts, and handling annoyances recorded in the Rev D bench sequence are the design inputs for the next retention method.

## Frozen mounting interface

The future latch housing must mount to the body using the existing features, so the body does not need another redesign. These are fixed as of Rev D and must not be moved by later revisions without incrementing this document:

| Interface feature | Value |
|---|---|
| Screw bores | Ø3.4 mm through, centers (x, y) = (8, 0) and (36, 0) mm |
| Head counterbores | Ø7 × 3 mm deep on the underside of the body |
| Wrap posts | Ø12 mm, centers (22, −10) and (22, +10) mm, tops at z = 20 mm |
| Body top surface (keeper seat) | z = 12 mm |
| Keeper roof plane | z = 20.4 (underside) to 23.4 mm (top) |
| Clear plan envelope for the housing | the keeper-shoulder lobe, roughly x = 0…46, y = ±42 mm |

Anything that bolts through the two Ø3.4 bores and clears the two posts is a valid retention module: the Rev C/D keeper, and the future snap latch alike.

## Requirements for the quick-snap latch (next retention revision)

From the design conversation: the change must be anticipated now, then executed after Rev D testing.

1. **Quick snap:** single-handed engage/release with no rotation of fasteners — target under 2 seconds each way, with gloves on.
2. **Holds under tension:** the latch must not release or creep while the deployed wire is loaded through the figure-eight wraps. Acceptance to be set from Rev D data; not less than the 20 N screening load held for 60 s with < 1 mm movement.
3. **Fails safe:** overload should slip the friction wraps or deform the latch visibly before the wire jacket is damaged or the latch releases suddenly.
4. **Captive:** no loose parts in the field. Sliding or hinged element stays attached to its housing; the housing stays bolted to the frozen interface above (nylon screws remain acceptable as permanent mounting, since they are no longer touched during deployment).
5. **No wire pinching:** like the keeper, the latch prevents wraps lifting off the posts; it is not a toothed clamp on the conductor.
6. **Printable:** FDM PETG without supports in one orientation, and living-hinge-free (printed snap arms must load across layers, not along them).
7. **Serviceable:** replaceable after wear by undoing the two mounting screws.

## Open questions Rev D testing must answer

- What tension do two figure-eight wraps actually hold with this wire, and how many wraps are needed for margin?
- Does the keeper roof see any real load, or do the wraps carry everything? (Determines how strong the snap needs to be.)
- Is the 0.4 mm roof-to-post gap right, or does the wire need more/less headroom?
- How often is retention adjusted in a real deployment? (Sets how fast the snap really needs to be.)
