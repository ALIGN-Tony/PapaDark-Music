# BoneLock Rev C — compact capacity calculation

Engineering estimate only. No physical winding trial performed.

## Requirements

- Overall body length no more than 254 mm (10 in).
- Insulated wire outside diameter d = 2.05 mm; conductor 18 AWG.
- Preserve the 150-foot storage target; extra capacity beyond 170 ft is unnecessary.

## Actual CAD and assumptions

- Body = 250 × 84 mm, with 12 mm base thickness.
- Clear winding length L = 136 mm.
- Core width W = 48 mm; thickness T = 12 mm.
- Four 45-degree corner chamfers c = 2 mm.
- Assumed axial turn pitch = d + 0.20 = 2.25 mm.
- Turns per layer n = floor(L / pitch) = 60.
- Envelope k = 6 layers, radial buildup k × d = 12.3 mm.

Core perimeter P = 2(W + T) − 8c + 4c√2 = 115.314 mm.

Assume each wire centerline follows an offset contour around the convex core. At layer j, offset r_j = (j − 0.5)d. Approximate turn perimeter = P + 2πr_j.

Total wire length ≈ n × [kP + πdk²]
                    = 55,423.907 mm
                    = 181.837 ft ideal geometric capacity.

Apply a 15% allowance for hand winding, leads, interlayer transitions and imperfect packing: 154.561 ft planning capacity. This allowance is an estimate, not a validated lower bound. Idealized offset layers omit small helical path increments and simplify layer transitions.

A 150 ft piece is 45,720 mm, about 82.5% of the ideal capacity. A 170 ft piece is 51,816 mm, about 93.5% of ideal capacity, so it has much less tolerance for imperfect winding. Use 150 ft as the initial acceptance test; do not advertise a verified 170 ft rating.

Six-layer bundle dimensions ≈ (48 + 2×12.3) × (12 + 2×12.3) = 72.6 × 36.6 mm. Shoulder width is 84 mm. Extra straps and fasteners add to packed size. Keep the neck and eye free of antenna wire.

Compared with Rev B, length falls 34 mm (12.0%) and width falls 16 mm (16.0%). The enclosing plan footprint falls about 26.1%. Actual material reduction is reported by CAD volume in the validation record; print mass depends on slicer settings.

This is only a storage calculation. It does not predict inductance, antenna resonance, radiation efficiency, insulation strength or support load rating.
