# BoneLock Rev G — print and bench-test package

Prepared for Tony Pelfanio, K4DIA • 30 September 2026

## What this revision is

Rev G is the compact resize for the actual wire on hand: FIPNOT 20 AWG silicone, 1.8 mm insulated OD (300 ft spool — one spool fills two units at the 150 ft target). The body shrinks from 250 × 84 to 210 × 72 mm by compressing the winding section for the thinner wire and winding seven layers instead of six. This is the practical floor while keeping 150 ft aboard: hardware features (keeper, thumb knobs, M3 screws, posts, bores) do NOT scale and are identical to Rev F, so the fixed-size ends dominate any further shrink. The Rev F sculpt carries over: continuous silhouette, domed coil flanges, bone-end lobes, thick rounded eye ring, recessed K4DIA mark, flat printable underside. At 210 mm the body now fits a standard 220 × 220 mm bed. The supplied STLs are real mesh parts, not images. Rev G is a mechanical fit and antenna-analyzer prototype. It has NOT been physically printed, load qualified, or transmitter tested.

**Retention in this revision is deliberately NOT the captive sliding latch shown in the rendering.** Rev G keeps the removable screw-down keeper so the wire path and friction retention can be tested first, and upgrades it to tool-free tightening with two printed 20 mm thumb knobs. The mounting interface (two screw bores + two posts) is fixed and documented in `Retention_Roadmap.md` so the future quick-snap captive latch can be developed as a drop-in replacement without redesigning the body.

Sized for a 150-foot storage target using FIPNOT 20 AWG silicone wire with 1.8 mm insulated outside diameter, well under the 10-inch length limit at 210 mm. Winding grooves and band markings are not included yet.

Files:

- `BoneLock_body_RevG.stl`: print one per antenna end.
- `BoneLock_keeper_RevG.stl`: print one per body; already oriented roof-down.
- `BoneLock_knob_RevG.stl`: print two per body; printed thumb nuts.
- `BoneLock_RevG.scad`: editable OpenSCAD source, dimensions in millimeters (`part` = body / keeper / knob / assembly).
- `CAD_preview.png`: views of the actual CAD geometry.
- `Retention_Roadmap.md`: current retention, fixed mounting interface, and requirements for the future quick-snap latch.
- `Prior_Art_Screen.md`: preliminary search findings, carried forward.
- `Capacity_Calculation.md`: storage calculation updated for the rounded core.
- `Mesh_Validation.txt`: geometry checks, not a physical print certification.

## Parts and tools

| Item | Quantity per unit | Notes |
|---|---:|---|
| Printed body | 1 | Unfilled PETG for mechanical/analyzer trials |
| Printed keeper | 1 | Same material |
| Printed thumb knob | 2 | Same material, 100% infill |
| M3 × 30 mm nylon machine screw | 2 | Through-fastened from below, no printed threads |
| M3 nylon nut | 2 | Pressed into the knob's hex pocket |
| M3 nylon washer | 2–4 | Under the knob face; verify remaining thread engagement |
| Insulated stranded antenna wire | As required | Specified wire: FIPNOT 20 AWG silicone, 1.8 mm insulated outside diameter (caliper-verify) |
| Nonconductive support cord | As required | Initial fit trial: 2–4 mm diameter |
| Abrasive paper, deburring tool, caliper | 1 set | Smooth every wire-contact surface |
| Antenna analyzer or VNA | 1 | Used at its normal measurement power |
| Spring scale | 1 | Controlled low-load slip screening |

Do not substitute conductive, ESD, carbon-filled, or metal-filled filament. PLA is acceptable for a desk appearance sample, but use PETG for this mechanical test sequence. PETG here is a prototype choice, not an established RF dielectric or outdoor support rating.

## CAD dimensions

| Feature | Nominal value |
|---|---:|
| Body overall | 210 × 72 mm (8.27 × 2.83 in) |
| Sculpted flange height | body rises to 16 mm at the coil flanges and eye ring |
| Flat body thickness | 12 mm, edges rounded 3 mm |
| Body height including posts | 20 mm |
| Assembled height excluding knobs | 23.4 mm; add 8 mm knob height |
| Clear winding waist | between the coil flanges (x = 47…166); winding on the 40 × 12 mm slab, 3 mm rounded edges; count on 115 mm effective after the blend fillets |
| Wrap posts | 12 mm diameter × 8 mm above body, rounded tops, flared roots |
| Post centers | x = 22 mm, y = −10 and +10 mm |
| Support eye | thick rounded ring, OD 34 mm, bore ID 16 mm, 16 mm tall, center x = 193 (outer edge at x = 210) |
| Screw bores | 3.4 mm diameter; centers x = 8 and 36 mm, y = 0; 7 mm × 3 mm head counterbores underneath |
| Keeper print footprint | 36 × 48 mm, roof 3 mm, roof-to-post-top gap 0.4 mm |
| Thumb knob | 20 mm diameter × 8 mm, scalloped grip, M3 hex-nut pocket |
| Maker's mark | recessed 84 × 24 mm panel centered on the winding waist; "DESIGNED BY / K4DIA" raised inside the pocket, top 0.2 mm below the winding surface (no wire contact) |
| Tail parking hole | 4 mm diameter at (172, 22), through the mid coil flange |

The body length runs along x, left antenna end toward right support eye. The neck and support eye must remain free of antenna wire. The keeper screws are entirely at the antenna end. Rev C keepers still fit Rev G bodies (same bore spacing, post height, and roof plane).

## Printing steps

1. Import the body STL into your slicer. Confirm millimeters and 100% scale: its maximum length must read 210 mm. Do not use fit-to-bed scaling.
2. Use a bed with at least 215 × 80 mm usable space for the body — a standard 220 × 220 mm bed now works (place the body diagonally if your printer's usable area is trimmed by clips). Print the keeper and knobs separately if needed. Do not split and glue the load-bearing body without a separately engineered joint.
3. Use a 0.4 mm nozzle, 0.20 mm layers, six perimeters, six top/bottom layers, and 50% gyroid infill as engineering starting settings for the body. Use 100% infill for the keeper and knobs, and local 100% infill modifiers around the post roots and the support eye if your slicer supports them.
4. Orientation: body broad flat underside down, posts UP. Keeper as supplied, flat roof down, standoffs UP. Knobs flat face down, hex pocket UP. The 3 mm edge rounding produces shallow overhangs only; supports are not expected — inspect your slicer preview.
5. Start from the filament manufacturer's PETG preset (a common starting point is 240 °C nozzle / 80 °C bed) with a PETG-compatible build surface.
6. Inspect the slice: posts, screw bores, counterbores, hex pockets, neck slot, and support eye must all be present with no unsupported islands.
7. After cooling, remove strings, burrs, and elephant foot. Hand-clear screw bores only enough for free M3 passage. Press an M3 nylon nut into each knob's hex pocket; a drop of PETG-safe adhesive may retain it, or rely on the press fit.
8. The rounded waist and shoulders are already close to cable-saddle geometry, but still hand-smooth every wire-contact surface. Test with scrap wire: pulling it over a contact surface must not shave or mark its jacket. Respect the wire manufacturer's minimum bend radius.

## Assembly and wire routing

1. Drop the two M3 × 30 nylon screws up through the body from BELOW; their heads seat in the counterbores so the body still lies flat.
2. Start at the FREE FAR END of the antenna wire. Pass a short tail through the 4 mm parking hole on the right winding shoulder and retain it with a loose nonconductive tie on the shoulder; do not run it across the neck or through the support eye. Mechanical retention only: do not strip or electrically join the tail.
3. Wind toward the left on the narrow waist, adjacent turns in one consistent rotational direction. For initial RF comparisons, use one layer with consistent spacing. Do not wind the coil section as a figure eight.
4. When the desired wire length remains deployed, route the deployed section around the two left posts in a figure-eight friction path. Start with two complete figure-eight wraps for the slip experiment. Keep wraps flat and below the post tops; stay clear of the two screw shafts.
5. Place the keeper standoffs-DOWN over the screws onto the body. Add a washer and spin a knob (with its captured nut) onto each screw. Tighten finger-tight only — the standoffs bottom out on the body so the roof cannot squeeze the wire. If a wire is pinched, remove and reroute it; tightening harder is not the remedy. No tools are needed at any point.
6. Tie the support cord through the large eye. The tension path is deployed wire → wrap posts → body → support eye → support cord. The keeper prevents wraps lifting off; it is not a toothed wire clamp. The neck slot is for a storage strap or lashing only.
7. For adjustment, completely remove tension, spin off the knobs, lift the keeper, change the wound turns, rewrap the posts, and reassemble.

A keeper that flexes enough for the wire to escape, or friction wraps that slip, is a failed prototype test. Do not compensate by pinching the conductor. Record the failure — it feeds the quick-snap latch requirements in `Retention_Roadmap.md`.

## Bench-test sequence

These are proposed screening conditions, not a working-load rating.

1. Check dimensions and fit; photograph any warping, poor layers, or screw misalignment. Verify the knobs spin freely and the nuts do not rotate in their pockets.
2. Mark the wire at its exit from the locking area. With no transmitter connected, apply 5 N, then 10 N, then 20 N axial tension with a spring scale, holding each for 60 seconds. Stop at slip, cracking, whitening, permanent bend, or jacket damage. Keep out of the recoil path.
3. Record movement against the mark. Target: less than 1 mm movement at each step, no visible damage, normal disassembly afterward. Development target only.
4. Cycle winding, locking, releasing and rewinding 25 times — this now exercises the knobs too; note any thread wear on the nylon screws or pocket loosening. Do not leave this unrated print supporting an unattended antenna.
5. Log every retention observation (slip loads, wrap counts that held, annoyances during deployment). These are direct inputs to the quick-snap latch design.

## RF experiment

Unchanged from Rev C — the electrical geometry (core size, winding zone, insulating neck and eye) is identical. Use an established antenna/feed arrangement as baseline, analyzer/VNA power only, and follow the Rev C measurement sequence: fully deployed baseline, then rewind 5/10/15 turns, recording exposed length, SWR, R, X, and sweep traces; verify repeatability after a full unwind/rewind. A good match alone does not establish radiation efficiency. No 50 W or 100 W rating is claimed.

## Compact storage target

150 ft of 1.8 mm OD silicone wire within the compact 210 mm body. The winding section is 115 mm effective on the 40 × 12 mm slab; seven layers give about 181.2 ft ideal geometric capacity, about 154 ft after a 15% practical allowance — see `Capacity_Calculation.md`. Confirm with the ACTUAL 150-foot piece before claiming the capacity is demonstrated. The seventh layer stands proud of the 16 mm flanges; keep the coil tidy and use a loose nonconductive strap around the waist for transport if needed.

## Revision changes and remaining decisions

Rev G changes versus Rev E (closer match to the approved rendering):

- Sculpted mass, flat bottom: two domed coil flanges rise to 16 mm — a ridge at x ≈ 42…48 beside the keeper deck and a broad hump at x ≈ 188…204 — bracketing the winding waist exactly as the rendering shows. They double as axial coil retention.
- The support eye is now a thick rounded ring: OD 44 mm, bore ID 18 mm (up from 16), 16 mm tall, domed rim, flat underside. Center moved to x = 228; outer edge still exactly at 250 mm.
- Subtle bone-end lobes added at the keeper end, matching the rendering's left-end silhouette.
- Strap slot shortened to 8 × 7 mm at x = 206…214; tail parking hole relocated to (218, 12) in the neck plate (the mid shoulder is now a dome with no flat for it). Both keep ≥ 5 mm to every neighboring feature.
- Keeper grip grooves increased from three to four, per the rendering's cap.
- Recessed maker's mark on the winding waist: "DESIGNED BY" (small) over "K4DIA" (large). The lettering rises inside a 1 mm pocket and stops 0.2 mm below the winding surface, so the wire never touches it; it is visible whenever the waist is not fully wound.
- Retained from Rev E: one continuous blended silhouette, wide solid neck (no thin-neck weak point), winding directly on the rounded slab, tool-free thumb-knob retention, frozen keeper interface. Rev C keepers remain compatible.
- The captive sliding latch from the rendering is still intentionally absent: test this screw-keeper revision first. `Retention_Roadmap.md` freezes the mounting interface and lists requirements for the future quick-snap latch that must hold under tension.

Remaining inputs: printer model/usable bed area, actual wire jacket material and bend-radius specification, antenna topology, and intended support tension. Actual storage, mechanical retention and RF behavior remain to be tested.
