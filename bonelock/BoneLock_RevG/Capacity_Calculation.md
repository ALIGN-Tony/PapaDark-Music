# BoneLock Rev G — compact capacity calculation

Engineering estimate only. No physical winding trial performed. Recomputed for 20 AWG silicone wire and the 210 × 72 mm Rev G body.

## Requirements

- Wire: FIPNOT 20 AWG silicone, insulated outside diameter d = 1.8 mm nominal (VERIFY with a caliper; jacket ODs vary).
- Preserve the 150-foot storage target per unit (a 300 ft spool fills two units).
- Keep all hardware (keeper, knobs, M3 screws, posts) at Rev F size — they do not scale.

## Actual CAD and assumptions

- Body = 210 × 72 mm, with 12 mm base thickness.
- Coil flange faces at x ≈ 47 and 166 (119 mm apart). The concave blend fillets (r = 7 mm) flare the outline over the last few millimetres at each end, so the calculation uses a conservative effective L = 115 mm; turns wound against the flange ramps gain a little length back.
- Waist cross-section width W = 40 mm; thickness T = 12 mm; four 3 mm corner fillets (the slab's edge rounding).
- Assumed axial turn pitch = d + 0.20 = 2.0 mm.
- Turns per layer n = floor(L / pitch) = 57.
- Envelope k = 7 layers, radial buildup k × d = 12.6 mm.

Core perimeter P = 2(W + T) − 8r + 2πr = 104 − 24 + 18.850 = 98.850 mm.

Assume each wire centerline follows an offset contour around the convex core. At layer j, offset r_j = (j − 0.5)d; approximate turn perimeter = P + 2πr_j.

Total wire length ≈ n × [kP + πdk²]
                    = 57 × (691.950 + 277.088)
                    = 55,235.2 mm
                    = 181.22 ft ideal geometric capacity.

Apply a 15% allowance for hand winding, leads, interlayer transitions and imperfect packing: **154.0 ft planning capacity.** This allowance is an estimate, not a validated lower bound.

A 150 ft piece is 45,720 mm, about 82.8% of the ideal capacity — the same comfort margin the full-size Rev F had.

Seven-layer bundle dimensions ≈ (40 + 2×12.6) × (12 + 2×12.6) = 65.2 × 37.2 mm. Shoulder width is 72 mm, so the bundle stays inside the plan silhouette; it stands proud of the 16 mm coil flanges from roughly the third layer up, as on any open winder. Keep the insulating neck, eye ring and keeper clear, and use a loose nonconductive waist strap for transport if necessary.

Why not half or third scale: the wire got only 12% thinner (2.05 → 1.8 mm), which cuts required winding volume ~23%, while uniform scaling cuts capacity roughly with the cube of the factor. Half scale stores only ≈ 50 ft of this wire and breaks every fastener fit; 210 × 72 is the practical floor at 150 ft with unscaled hardware.

This is only a storage calculation. It does not predict inductance, antenna resonance, radiation efficiency, insulation strength or support load rating.
