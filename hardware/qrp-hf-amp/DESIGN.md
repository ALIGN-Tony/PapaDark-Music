# "PocketWatt" — 15 W HF QRP Linear Amplifier

**Supply:** 13.8 V DC nominal (12.5–14.4 V) · **Output:** 10–20 W PEP, 1.8–30 MHz
**Bias regulation:** National Semiconductor **LM340T12** (12 V, TO-220)
**Form factor:** pocket size, ~105 × 70 × 30 mm, heatsink plate as chassis base
**No switching converters anywhere** — 100 % linear, RF-quiet by construction.

---

## 1. Design philosophy — where the LM340T12 fits

The LM340T12 is a 12 V three-terminal *linear* regulator (the TO-220 "T"
package). It is not an RF power device and it is limited to about 1 A with
current limiting and thermal shutdown built in. Used correctly, it is the
quietest possible way to derive a stable sub-rail from 13.8 V: it has no
switching element, so it generates **zero conversion hash, no birdies, and
no spurs** — exactly what you want next to a receiver.

So the architecture is:

| Rail | Source | Feeds | Why |
|------|--------|-------|-----|
| **+13.8 V raw** | battery / PSU, fused | PA transistor **drains** | RF power FETs rated for 12.5 V service are designed to run straight off a 13.8 V vehicle/shack supply. Maximum efficiency, no series loss. |
| **+12 V regulated** | **LM340T12** | Gate **bias voltage dividers**, T/R relay, status LED | Bias voltage must not move when the battery sags from 14.4 V to 12.5 V, or your idle current (and IMD) would wander. The LM340 pins it. |

### 1.1 Why the resistor divider sets the *bias*, not the *drain* rail

A resistive divider is the right tool where the load current is tiny and
constant — the FET gates draw essentially **zero DC current**, so a
few-milliamp divider chain holds the gate voltage rock-solid. That is the
divider circuit in this design (Section 4).

Dropping the *drain* supply resistively is not done, and here is the math:
at 15 W out the PA pulls ~2.2 A. Dropping 13.8 V→12 V resistively needs
0.82 Ω dissipating ~4 W, and the "12 V" would swing volts up and down with
the SSB envelope (current varies 0.4–2.5 A), badly modulating the rail.
The fix is simpler: **don't drop it at all.** The RD16HHF1 finals are
rated 17 V absolute max and are characterized at 12.5 V; 13.8 V on the
drains is their normal operating point. Full supply on the drains, divider
on the gates, LM340 holding the divider's reference — every part doing the
job it's good at.

### 1.2 LM340T12 dropout check at 13.8 V in

Headroom is 13.8 − 12.0 = 1.8 V. The LM340's worst-case dropout of ~2 V is
specified at 1 A; this rail draws only **~40–60 mA** (bias chains + relay),
where dropout is ≈1.3–1.5 V. It therefore stays in regulation at 13.8 V
nominal. On a deeply sagged battery (<13.5 V) it degrades gracefully into
tracking mode — the bias drifts down slightly rather than jumping, which
is benign (idle current falls, it never runs away).

---

## 2. Specifications (design targets)

| Parameter | Value |
|---|---|
| Frequency range | 1.8–30 MHz (band LPF required, see §6) |
| Output power | 15 W typ., 20 W max (13.8 V) |
| Drive required | 0.5–1 W for full output (optional −7 dB pad for 5 W rigs) |
| Gain | ~16 dB (80/40 m) falling to ~13 dB (10 m) |
| Mode | Class AB push-pull linear — SSB/CW/digital |
| IMD3 | better than −30 dBc @ 15 W PEP (250 mA/device idle) |
| Harmonics | < −50 dBc after LPF (meets FCC −43 dBc with margin) |
| Supply current | ~2.2 A @ 15 W; 0.5 A idle (keyed, no drive) |
| Input/output Z | 50 Ω, BNC |
| T/R | PTT-keyed relay bypass (RX passes straight through) |

---

## 3. RF line-up

Single push-pull stage, two **Mitsubishi RD16HHF1** RF MOSFETs.

**Why RD16HHF1 and not IRF510:** the user requirement is "RF quiet."
The RD16HHF1 is a purpose-built 30 MHz RF MOSFET (16 W @ 12.5 V) with low
input capacitance (~90 pF vs ~180 pF), gain that holds up through 10 m, a
gentle, well-characterized transfer curve for clean class AB, and a
TO-220-style flanged package that bolts straight to the heatsink base.
IRF510s are switching FETs pressed into RF service — they work, but need
28 V for comparable power and are markedly dirtier (worse IMD) at 13.8 V.
A push-pull pair loafing at 15 W from parts rated 32 W combined is the
quiet, low-stress way to do this. Push-pull also cancels even-order
harmonics (~−40 dBc on H2 before the LPF even starts working).

```
                       +13.8V (fused, RF-filtered)
                              |
                       T2 CT feed choke
              ┌───────────────┴───────────────┐
              |                               |
  RF in    ┌──┴──┐                         ┌──┴──┐    T3 1:4Z     LPF     RF out
  o──[T1]──┤ Q1  ├── drains, push-pull ────┤ T3  ├──── (§6) ────o (via T/R relay)
   1W      | Q2  |                         └─────┘
           └──┬──┘
     gates: bias via dividers (§4), 220Ω+100nF drain→gate NFB each side
```

### Stage detail

- **T1 (input):** 1:1 balun, 10 bifilar turns #28 on BN43-2402 binocular
  core. Each secondary end drives one gate through a **4.7 Ω gate-stopper**
  (parasitic suppression). A **27 Ω** resistor from each gate to its bias
  node flattens input SWR across HF.
- **Negative feedback:** **220 Ω + 100 nF** in series, drain→gate on each
  side. Levels the gain vs frequency (tames the excess low-band gain),
  stabilizes the stage unconditionally, and improves IMD. This is the main
  reason the amp stays "quiet" — no parasitic oscillations, ever.
- **Q1/Q2:** RD16HHF1, sources grounded directly to the heatsink ground
  plane with the shortest possible leads (source inductance is the enemy
  of stability).
- **T2 (drain feed):** center-tapped choke, 2 × 8 bifilar turns #24 on
  FT50-43. Center tap to +13.8 V through a ferrite bead, decoupled with
  100 nF ∥ 10 nF ∥ 470 µF at the tap.
- **T3 (output):** 1:2 turns = 1:4 impedance step-up on a BN43-3312
  binocular (or 2 stacked FT50-43). Primary 1+1 turn (drain to drain,
  100 nF DC blocks), secondary 2 turns to the LPF.
  Load line check: R(drain-drain) = 2·(13.8 − 1.3)²/P → at 25 W capability
  ≈ 12.5 Ω, matching the 1:4 transformation from 50 Ω. Comfortable for
  15–20 W with headroom.

---

## 4. Bias network — the resistor voltage divider (heart of the request)

Each gate gets its **own divider + trimmer** off the LM340's regulated
12 V, so the two devices can be balanced individually (MOSFET Vgs(th)
spreads ±0.5 V part-to-part).

```
 +12V (LM340T12 out)
   |
  [100Ω]──┬────────────► to Q2's identical divider
   |    [10µF] (bias rail filter)
   |      |
   |     GND
   ├──[4.7kΩ]──┬──[10kΩ trimmer]──┬──[3.3kΩ]──GND
   |           |   (multiturn)    |
   |           └── wiper ──[1kΩ]──┴─► gate bias node Q1
   |                               |
   |                            [100nF]
   |                               |
   |                              GND
```

- Divider chain current ≈ 12 V / 18 kΩ ≈ **0.7 mA per side** — stiff
  beyond need for a zero-current load, negligible battery drain.
- Wiper range spans ≈ 2.2–5.1 V, bracketing the RD16HHF1 threshold
  (Vgs(th) ≈ 2 V) with room to set class AB idle.
- The 1 kΩ + 100 nF at the gate node keeps RF out of the divider; bias DC
  reaches the gate through T1's secondary winding / the 27 Ω network.
- **Idle current target: 250 mA per device** (500 mA total). This is the
  linearity sweet spot for SSB; drop to 100 mA/device for CW-only battery
  work.
- **Optional thermal tracking:** replace the 3.3 kΩ lower leg with 2.7 kΩ
  in series with a 1N4148 glued to the heatsink between Q1/Q2. The diode's
  −2 mV/°C walks the bias down as the sink warms, canceling the FETs'
  threshold tempco. With the oversized heatsink base this is optional, but
  it's two parts and worth having for FT8 duty cycles.

### LM340T12 hookup (per datasheet)

```
 +13.8V ──[bead]──┬── IN │LM340T12│ OUT ──┬──────► +12V bias rail
                  |      │  (tab=GND)│    |
               [0.33µF]      GND        [0.1µF] ∥ [10µF]
                  |           |           |
                 GND ─────────┴───────────┘
```

TO-220 pinout facing the label: **1 = IN, 2 = GND (tab), 3 = OUT.**
Bolt it flat to the heatsink base — no insulator needed since the tab is
ground. Dissipation is (1.8 V × 60 mA) ≈ 0.11 W; it will run cold.

---

## 5. T/R switching and protection

- **T/R:** one DPDT telecom relay (12 V coil, e.g. Omron G6K/G5V-2 class,
  contacts fine at 20 W HF into 50 Ω). PTT (ground-to-transmit) energizes
  the coil from the regulated 12 V rail; 1N4148 flyback diode across the
  coil. De-energized = RX, antenna passes straight through the amp —
  amp adds nothing on receive (and being linear, it radiates nothing).
- **Protection:** 4 A blade fuse in the +13.8 V lead; reverse-polarity
  shunt diode (SS54/1N5822) behind the fuse. For battery portability,
  upgrade to a P-FET ideal-diode (IRF4905, gate to GND via 10 k) — zero
  drop, still no switching noise.
- **Input pad (optional):** if driving from a 5 W QRP rig, a −7 dB, 5 W
  pi-pad at the input (150 Ω / 39 Ω / 150 Ω, 2 W resistors paralleled)
  brings drive into range and improves input match.

---

## 6. Output low-pass filter (mandatory)

One 7-element Chebyshev (0.1 dB ripple, 50 Ω) per band, either as a
plug-in header or a small slide-switch pair for a two-band pocket build.
Capacitors ≥100 V C0G or silver mica; toroids T37-2 (red), #26 wire.

| Band | C1 = C7 | C3 = C5 | L2 = L6 | L4 |
|------|---------|---------|---------|-----|
| 40 m (fc ≈ 8.0 MHz) | 470 pF | 820 pF | 1.42 µH — 19 t T37-2 | 1.57 µH — 20 t T37-2 |
| 20 m (fc ≈ 15 MHz) | 240 pF | 470 pF | 0.75 µH — 14 t T37-2 | 0.84 µH — 15 t T37-2 |

(Values computed from g-coefficients g1=1.1812, g2=1.4228, g3=2.0967,
g4=1.5734; scale the same way for other bands. Verify fc with a NanoVNA
before final assembly — squeeze/spread turns to trim.)

---

## 7. Thermal and mechanical

- **Heatsink = chassis base**, per the requirement: finned aluminum
  extrusion ~100 × 70 × 15–20 mm (≈3 °C/W). Worst case key-down at 20 W
  out / ~57 % efficiency ⇒ ~15 W dissipated ⇒ ~45 °C rise. Fine for
  SSB/CW; for 100 %-duty FT8 either back off to 10 W or pick a 2 °C/W
  extrusion.
- Q1, Q2 and the LM340T12 all bolt flat to the base plate. RD16HHF1 tabs
  are **source (ground)** and the LM340 tab is **ground** — so all three
  mount **directly, no insulators**, with thermal compound. That's the
  lowest thermal resistance and the best RF grounding simultaneously.
- Board: single-sided Manhattan/pad-per-hole over continuous ground, or a
  simple 2-layer PCB with stitched ground pour. Keep the gate leads
  <10 mm.
- Lid: folded aluminum U over the base. Total ≈ 105 × 70 × 30 mm, ~250 g
  with lid — genuinely pocketable.

---

## 8. Bill of materials

| Ref | Part | Qty | Notes |
|-----|------|-----|-------|
| Q1, Q2 | Mitsubishi RD16HHF1 | 2 | matched pair preferred |
| U1 | **LM340T12** (= LM7812 class), TO-220 | 1 | the specified part |
| T1 | BN43-2402, 10 t bifilar #28 | 1 | input balun |
| T2 | FT50-43, 2×8 t bifilar #24 | 1 | drain feed choke |
| T3 | BN43-3312, 1+1 t : 2 t | 1 | output transformer |
| RV1, RV2 | 10 kΩ multiturn trimmer | 2 | bias set |
| R divider | 100 Ω, 4.7 kΩ, 3.3 kΩ, 1 kΩ, 27 Ω, 4.7 Ω | — | see §4 |
| R fb | 220 Ω 1 W | 2 | feedback |
| C | 100 nF ∥ 10 nF X7R, 0.33 µF, 10 µF, 470 µF/25 V | — | decoupling per §3–4 |
| K1 | DPDT 12 V telecom relay | 1 | T/R |
| LPF | per §6 table | 1–2 bands | T37-2 + C0G/mica |
| F1 | 4 A blade fuse + holder | 1 | |
| D | SS54, 1N4148 ×2 | | protection/flyback/tempco |
| J1–J3 | BNC ×2, DC barrel or Powerpole, 3.5 mm PTT | | |
| HS | Al extrusion ~100×70×18 mm, ~3 °C/W | 1 | chassis base |

Everything except the RD16HHF1s is junk-box grade; the finals are ~$6–8 ea.

---

## 9. First power-up and bias adjustment

1. Both trimmers fully **counter-clockwise** (gates near 0 V, FETs off).
   No drive. Dummy load on the output. Insert an ammeter in the 13.8 V lead.
2. Power on, key PTT. Baseline current = relay + LED (~50 mA).
3. Advance RV1 until total current rises **+250 mA**. Stop.
4. Advance RV2 until it rises a further **+250 mA** (≈550 mA total).
5. Un-key/re-key; confirm idle returns to the same value (bias stability —
   this is the LM340 doing its job).
6. Apply 0.5 W drive on 40 m, verify ~12–15 W into the dummy load and a
   clean two-tone pattern if you have a scope. Check the heatsink warms
   evenly under both finals (balance check).
7. Sweep each band's LPF output on a scope/SDR: all harmonics should be
   below −50 dBc.

---

## 10. Why this amp is "RF quiet" — summary

1. **No switching converters** — the only voltage conversion is a linear
   LM340T12; the spectrum contains nothing you didn't put there.
2. **Purpose-built RF FETs run at half rating** — clean class AB, low IMD.
3. **Push-pull symmetry** cancels even harmonics before the LPF.
4. **Drain-gate negative feedback** guarantees stability (no parasitics).
5. **Regulated bias from a stiff resistor divider** — idle current, and
   therefore linearity, doesn't move with battery voltage or keying.
6. **Direct-to-heatsink grounding** of both finals and the regulator.
