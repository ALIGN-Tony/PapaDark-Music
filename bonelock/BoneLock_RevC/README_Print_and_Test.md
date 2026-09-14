# BoneLock Rev C — print and bench-test package

Prepared for Tony Pelfanio, K4DIA • 14 September 2026

## What this revision is

Sized for a 150-foot storage target using 18 AWG wire with 2.05 mm insulated outside diameter. An original CAD interpretation of the approved visual concept: wire winder, end insulator body, and retained wrap posts. The supplied STLs are real mesh parts, not images. Rev C is a mechanical fit and antenna-analyzer prototype. It has NOT been physically printed, load qualified, or transmitter tested.

The illustrated captive sliding latch is replaced in Rev C by a removable keeper and two nylon screws. This allows the wire path and friction retention to be inspected while we develop the latch. It is not a finished quick-release product. Winding grooves and band markings are not included yet.

Files:

- `BoneLock_body_RevC.stl`: print one per antenna end.
- `BoneLock_keeper_RevC.stl`: print one per body; already oriented roof-down.
- `BoneLock_RevC.scad`: editable OpenSCAD source, dimensions in millimeters.
- `CAD_preview.png`: views of the actual CAD geometry.
- `Prior_Art_Screen.md`: preliminary search findings and links.
- `Mesh_Validation.txt`: geometry checks, not a physical print certification.

## Parts and tools

| Item | Quantity per unit | Notes |
|---|---:|---|
| Printed body | 1 | Unfilled PETG for mechanical/analyzer trials |
| Printed keeper | 1 | Same material |
| M3 × 30 mm nylon machine screw | 2 | Through-fastened, no printed threads |
| M3 nylon nut | 2 | Finger-tight plus only enough to seat |
| M3 nylon washer | 4 | Verify remaining thread engagement with your hardware |
| Insulated stranded antenna wire | As required | Specified wire: 18 AWG conductor, 2.05 mm insulated outside diameter |
| Nonconductive support cord | As required | Initial fit trial: 2–4 mm diameter |
| Abrasive paper, deburring tool, caliper | 1 set | Smooth every wire-contact surface |
| Antenna analyzer or VNA | 1 | Used at its normal measurement power |
| Spring scale | 1 | Controlled low-load slip screening |

Do not substitute conductive, ESD, carbon-filled, or metal-filled filament. PLA is acceptable for a desk appearance sample, but use PETG for this mechanical test sequence. PETG here is a prototype choice, not an established RF dielectric or outdoor support rating.

## CAD dimensions

| Feature | Nominal value |
|---|---:|
| Body overall | 250 × 84 mm (9.84 × 3.31 in) |
| Flat body thickness | 12 mm |
| Body height including posts | 20 mm |
| Assembled height excluding screw heads/nuts | 23.4 mm |
| Clear winding waist | 136 mm long × 48 mm wide; 12 mm thick with 2 mm corner chamfers |
| Wrap posts | 12 mm diameter × 8 mm above body |
| Post centers | x = 22 mm, y = −10 and +10 mm |
| Support eye | 16 mm inside diameter |
| Support-eye center | x = 234 mm, y = 0 |
| Screw bores | 3.4 mm diameter; centers x = 8 and 36 mm, y = 0 |
| Keeper print footprint | 36 × 48 mm |
| Keeper roof thickness | 3 mm |
| Roof-to-post-top design gap | 0.4 mm |
| Tail parking hole | 4 mm diameter at right winding shoulder |

The body length runs along x, left antenna end toward right support eye. The neck and support eye must remain free of antenna wire. The keeper screws are entirely at the antenna end.

## Printing steps

1. Extract the ZIP. Import the body STL into your slicer. Confirm millimeters and 100% scale: its maximum length must read 250 mm. Do not use fit-to-bed scaling.
2. Select the exact printer and nozzle profile. Use a bed with at least 260 × 95 mm usable space for the body and clearance. A printer with a 300 × 300 mm bed is the straightforward choice; a 256 × 256 mm bed may fit with a small or omitted brim if the full required area is usable. Verify slicer exclusions and brim before printing. A standard 220 × 220 mm bed cannot accommodate this body flat at full scale. Print the keeper separately if needed. Do not split and glue the load-bearing body without a separately engineered joint.
3. Use a 0.4 mm nozzle, 0.20 mm layers, six perimeters, six top layers, six bottom layers, and 50% gyroid infill as engineering starting settings. Use 100% infill for the keeper and local 100% infill modifiers around the two post roots and the support eye if supported by your slicer.
4. Body orientation: broad flat underside on the plate, posts UP. Keeper orientation: retain its supplied flat-roof-down orientation, with two cylindrical standoffs UP. The body core has shallow 45-degree lower chamfers. Supports are not expected in these orientations; inspect your slicer preview.
5. Start from the filament manufacturer's PETG preset for nozzle temperature, bed temperature, cooling, and speed. A nominal starting point when compatible with that filament/printer is 240 °C nozzle and 80 °C bed. These are not universal settings. Use a PETG-compatible build surface and the printer manufacturer's release/adhesion guidance.
6. Use a 4–5 mm brim only if your adhesion or corner-lift history calls for it. Inspect the slice: all posts, screw bores, and the support eye must be present; no unsupported islands should appear.
7. Slice and generate G-code for YOUR printer only. This package intentionally contains no universal G-code. Use the slicer's material/time estimate; none has been measured for this build.
8. Let the plate cool before removing the parts. Remove strings, burrs, and any elephant foot. Hand-clear screw bores only enough for free M3 passage; do not force a screw into an undersized hole.
9. The winding core now has four 2 mm, 45-degree longitudinal chamfers. Smooth and soften both edges of every chamfer by hand; these are not fully rounded cable saddles. Smooth post edges, the tail hole, and the support eye. Test with scrap wire: pulling it over a contact surface must not shave or mark its jacket. Respect the wire manufacturer's minimum bend radius; larger-radius posts may be necessary for other wire types.

Manufacturer background: [Prusa PETG material guide](https://help.prusa3d.com/article/petg_2059). Its published temperatures are specific starting guidance; use your own material/printer profile.

## Assembly and wire routing

1. With the keeper removed, inspect both posts and their roots for voids or cracking.
2. Start at the FREE FAR END of the antenna wire. Pass a short tail through the 4 mm parking hole on the right winding shoulder. Retain that tail with a loose nonconductive tie on the shoulder; do not run it across the neck or through the support eye. This is mechanical retention only: do not strip or electrically join the tail.
3. Wind toward the left on the narrow waist, making adjacent turns in one consistent rotational direction. For initial RF comparisons, use one layer and keep the same spacing. Do not wind the coil section as a figure eight.
4. When the desired wire length remains deployed, route that deployed section around the two left posts in a figure-eight friction path. Start with two complete figure-eight wraps for the slip experiment. Keep wraps flat and below the post tops. Stay clear of the two screw standoffs; route the coil lead around their outside if needed. These local retention wraps are separate from the same-direction coil winding.
5. Place the keeper with its standoffs DOWN onto the body. Its roof should sit above the post tops without squeezing the wire. Fit the nylon screws, washers and nuts through the two aligned holes. Tighten gently to seat the standoffs. If a wire is pinched, remove and reroute it; tightening harder is not the remedy.
6. Tie the support cord through the opposite large eye. The tension path is deployed wire → wrap posts → body → support eye → support cord. The keeper prevents wraps lifting off; it is not a toothed wire clamp.
7. For adjustment, completely remove tension, undo the keeper, change the number of wound turns, rewrap the posts, and reassemble. No sliding latch is present in Rev C.

A keeper that flexes enough for the wire to escape, or friction wraps that slip, is a failed prototype test. Do not compensate by pinching the conductor. Record the failure for the next geometry revision.

## Bench-test sequence

These are proposed screening conditions, not a working-load rating.

1. Check dimensions and fit; photograph any warping, poor layers, or screw misalignment.
2. Mark the wire at its exit from the locking area. With the assembly near a bench and no transmitter connected, apply 5 N, then 10 N, then 20 N axial tension using a spring scale. Hold each for 60 seconds. Stop at slip, cracking, whitening, permanent bend, or jacket damage. Keep out of the recoil path.
3. Record movement against the mark. Target: less than 1 mm movement at each screening step, no visible damage, and normal disassembly afterward. This threshold is a development target only.
4. Cycle winding, locking, releasing and rewinding 25 times. Reinspect the wire and post roots. Do not leave this unrated print supporting an unattended antenna.

## RF experiment: what we are actually testing

Your objective is one continuous wire with deployment length adjusted by winding the remainder onto the device. That is the design intent. However, an open-ended wound remainder is a distributed electromagnetic structure with inductance, capacitance and possible self-resonances. It is not automatically equivalent to a known lumped series loading coil. Its location near an antenna end also matters. We have not established multiband coverage, loss, efficiency, or power handling.

1. Use an established antenna/feed arrangement as the baseline: a dipole with an appropriate current choke or an end-fed with its existing suitable matching system. This device does not replace the feedpoint matching system.
2. Keep the same wire, feedline routing, support height, ground/counterpoise arrangement and environment throughout a comparison. For a dipole, use two devices and change both sides equally.
3. With the analyzer only, measure a fully deployed baseline. Record wire length, SWR, resistance, reactance, and the sweep trace.
4. Rewind 5 turns, then 10, then 15, recording the actual exposed length and the amount of wire on the device each time. Reposition the end support as needed while keeping height and general geometry consistent; record position changes because they also influence the result.
5. Preserve the free-tail length and route. Record wrap spacing, layer count and lock-wrap count. Search for resonances broadly rather than assuming every added turn moves resonance in one direction.
6. Repeat a useful setting after completely unwinding and rewinding. Repeatability matters more than one favorable SWR dip.
7. A good match alone does not establish radiation efficiency. Field-strength comparisons or a controlled comparative radiated test are a separate later step.

For Rev C, restrict RF testing to analyzer/VNA power. A DMM continuity test does not prove RF insulation. Transmitter-power and wet-condition qualification remain separate work; no 50 W or 100 W rating is claimed.

## Compact storage target

Rev C is sized for 150 ft of 18 AWG wire with 2.05 mm insulated outside diameter, under a 10-inch overall length limit. The body is 250 mm (9.84 in), leaving 4 mm below that limit. It is also narrowed to 84 mm (3.31 in). The earlier roughly 193-foot planning capacity is no longer the design target. There is no need to provision storage beyond the requested 150–170 ft range.

The revised winding section is 136 mm long, with a 48 × 12 mm chamfered core. Assuming 2.25 mm axial pitch including a small hand-winding gap, 60 turns fit per layer. Six layers give about 181.8 ft ideal geometric capacity, or about 154.6 ft after a 15% practical allowance. This supports a 150-foot prototype target but must be physically verified. A well-packed 170-foot piece may fit with a smaller packing allowance (about 6.5%); 170 ft is not guaranteed. The calculated ideal capacity is not a hard stop: the user can always overfill an open winder, so we do not call 170 ft an absolute mechanical maximum.

Six layers build 12.3 mm outward, giving a nominal wound bundle of 72.6 × 36.6 mm before straps or hardware. This is inside the 84 mm shoulder width in plan view. The bundle projects above and below the flat body. Keep the insulating neck, eye and keeper clear, and use a loose nonconductive storage strap if necessary.

Confirm with the ACTUAL 150-foot piece before claiming the capacity is demonstrated. Mark every 25 ft before winding; record the wire diameter, layer count, packed dimensions, lead routing, and whether the keeper stays accessible. Suggested storage acceptance: all 150 ft retained within the six-layer target, no coils spilling past the shoulders, neck clear, and no jacket damage after 25 pack/deploy cycles. Try 170 ft only as an optional upper-range check.

`Capacity_Calculation.md` records the calculation and assumptions. Multilayer winding changes the electromagnetic behavior; no calibrated inductance, frequency labels, or transmitter power rating is assigned.

## Revision changes and remaining decisions

Rev C replaces Rev B for this request. Changes: body 284 → 250 mm long, 100 → 84 mm wide; winding zone 170 → 136 mm; core width 50 → 48 mm; wire diameter assumption 2.15 → 2.05 mm. Body thickness remains 12 mm to avoid introducing another strength variable during the first fit tests. The narrower and shorter body reduces the CAD solid volume; no physical strength equivalence is claimed.

The keeper is unchanged and earlier printed keepers can be reused. Use two M3 × 30 mm nylon screws with the 12 mm body. It remains a screw-secured prototype keeper; a captive sliding latch is not implemented. The one-piece body preserves the continuous tension path. Never scale the whole part down to fit a printer, since that changes the wire fit, keeper and fastener bores.

Remaining inputs: printer model/usable bed area, actual wire jacket material and bend-radius specification, antenna topology, and intended support tension. Actual storage, mechanical retention and RF behavior remain to be tested.
