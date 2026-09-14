# BoneLock Rev D — compact capacity calculation

Engineering estimate only. No physical winding trial performed. Updated from Rev C for the rounded core corners; all envelope dimensions unchanged.

## Requirements

- Overall body length no more than 254 mm (10 in). Body is 250 mm.
- Insulated wire outside diameter d = 2.05 mm; conductor 18 AWG.
- Preserve the 150-foot storage target; extra capacity beyond 170 ft is unnecessary.

## Actual CAD and assumptions

- Body = 250 × 84 mm, with 12 mm base thickness.
- Clear winding length L = 136 mm (x = 44…180).
- Core width W = 48 mm; thickness T = 12 mm.
- Four corner fillets r = 3 mm (Rev C used 2 mm 45° chamfers).
- Assumed axial turn pitch = d + 0.20 = 2.25 mm.
- Turns per layer n = floor(L / pitch) = 60.
- Envelope k = 6 layers, radial buildup k × d = 12.3 mm.

Core perimeter P = 2(W + T) − 8r + 2πr = 120 − 24 + 18.850 = 114.850 mm.

Assume each wire centerline follows an offset contour around the convex core. At layer j, offset r_j = (j − 0.5)d; approximate turn perimeter = P + 2πr_j.

Total wire length ≈ n × [kP + πdk²]
                    = 60 × (689.100 + 231.832)
                    = 55,255.9 mm
                    = 181.29 ft ideal geometric capacity.

Apply a 15% allowance for hand winding, leads, interlayer transitions and imperfect packing: **154.1 ft planning capacity.** This allowance is an estimate, not a validated lower bound. Idealized offset layers omit small helical path increments and simplify layer transitions.

A 150 ft piece is 45,720 mm, about 82.7% of the ideal capacity. A 170 ft piece is 51,816 mm, about 93.8% of ideal, with much less tolerance for imperfect winding. Use 150 ft as the initial acceptance test; do not advertise a verified 170 ft rating.

Six-layer bundle dimensions ≈ (48 + 2×12.3) × (12 + 2×12.3) = 72.6 × 36.6 mm, inside the 84 mm shoulder width in plan view. The bundle projects above and below the flat body. Keep the insulating neck, eye and keeper clear, and use a loose nonconductive storage strap (the neck slot is provided for this) if necessary.

Compared with Rev C, the fillet change reduces ideal capacity by about 0.55 ft — negligible against the 15% allowance. Everything else is identical.

This is only a storage calculation. It does not predict inductance, antenna resonance, radiation efficiency, insulation strength or support load rating.
