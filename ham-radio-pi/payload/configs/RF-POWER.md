# RF Pi inline power / SWR sampling — wiring guide

Sample your transmitter's forward and reflected power and read live watts + SWR
on the RF Pi dashboard. The Pi has no ADC and cannot take RF directly, so the
chain conditions a small, calibrated sample of the RF down to a DC voltage that
rides in on the same I2C bus the battery monitor already uses.

## The signal chain

```
             ┌── forward coupled port ──► pad ──► RF detector ──► A0 ┐
 antenna ──► │ directional coupler │                                 │ ADS1115 ──I2C──► Pi
   line  ──► │  (Mini-Circuits)    │                                 │ (0x48)
             └── reflected port ───────► pad ──► RF detector ──► A1 ┘
```

**Never connect RF to the ADS1115.** The detector's output is a bounded DC
voltage; that is the only thing the ADC ever sees.

## Parts

| Block | Part (example) | Notes |
|---|---|---|
| Dual directional coupler | **Mini-Circuits ZGBDC30-372HP+** (30 dB, 300 W) or ZFBDC20-62HP+ (20 dB, 250 W) | taps a fixed fraction of fwd + rev; pick coupling for your power |
| Attenuator pad | **Mini-Circuits VAT-20+** (20 dB) etc. | drops the coupled sample to the detector's sweet spot |
| RF power detector | **Mini-Circuits ZX47-40+** (AD8318, 10 MHz–8 GHz) or a homebrew **AD8307** | log detector: DC volts linear in dBm |
| ADC | **ADS1115** 16-bit I2C module (~$5) | A0 = forward, A1 = reflected |

Use **matched** couplers/pads/detectors on the forward and reflected paths so
their gains cancel in the SWR calculation.

## External USB sensor pod (RasPad and tablets)

On a RasPad or any tablet build there's no room to stack a HAT, and you don't
want RF detectors inside the display anyway. Put the whole front end in its own
small box near the radio and connect it to the Pi with **one USB cable** instead
of the GPIO header:

```
coupler ─► pad ─► AD8307 ─► ADS1115 ─► MCP2221A (USB↔I2C) ─USB─► RasPad
```

The **MCP2221A** USB-to-I2C bridge makes the ADS1115 appear as a normal I2C bus
over USB. No code change: find the bus with `i2cdetect -l` (look for
"MCP2221 usb-i2c bridge") and set that number as `I2C_BUS` in `rfpower.conf`.
The battery monitor stays on the Pi's onboard bus; this is a separate bus.

Enclosure: interior ~120 × 100 × 45 mm or larger; diecast aluminum shields the
detectors and acts as the ground plane. Mount the AD8307s against the wall with
their SMA connectors through it; put the USB connector on the opposite wall so
RF-in and USB-out are apart. A 5 × 7 cm perfboard holds the ADS1115 + MCP2221A.

## Worked example: a ≤20 W station (K4DIA)

Parts: Mini-Circuits **ZFBDC20-62HP+** (20 dB bidirectional, 10–600 MHz),
**2× 20 dB / 1 W SMA** pads, **2× AD8307** modules, **ADS1115**, **MCP2221A**,
in N/BNC/SMA connectors.

Budget at 20 W (+43 dBm): coupled port = +43 − 20 = **+23 dBm (0.2 W)**; through a
20 dB pad → **+3 dBm** at the AD8307 — safe (max ~+15 dBm) and in the log-linear
sweet spot, with range to spare down to QRP. A 1 W pad is ample at 0.2 W.

Connectors: coupler main line is **BNC**, coupled ports **SMA**. Use an N↔BNC
adapter to reach the feedline; SMA jumper → SMA pad → SMA AD8307 on each sample.

Band note: the coupler is **10–600 MHz**, so power/SWR are accurate on **20 m and
up**; below 10 MHz (40/80/160 m) directivity drops and readings degrade.

`rfpower.conf` starting point (then calibrate, which overrides these):
`COUPLER_DB=20`, `PAD_DB=20`, `SLOPE_DB_PER_V=40`, `OFFSET_DBM=-84`.

## Power budget (worked example: 100 W HF station)

100 W = **+50 dBm** on the main line.

| Stage | Loss / level |
|---|---|
| Main line | +50 dBm (100 W) |
| After 30 dB coupler (coupled port) | +20 dBm |
| After 20 dB pad | **0 dBm (1 mW)** at the detector — ideal, well under the ZX47-40's +15 dBm max |

So the chain gain to add back is **coupler (30) + pad (20) = 50 dB**: an antenna
power of +50 dBm shows 0 dBm at the detector. For QRP (5–10 W) use less coupling
(a 20 dB coupler) or less pad so the detector still sees roughly −10…+5 dBm.

`hampi-rfpower` handles the math; you only tell it `COUPLER_DB`, `PAD_DB`, and
the detector transfer — or better, calibrate (below), which folds the whole
chain into one fit.

## Wiring to the Pi

ADS1115 → Pi (3.3 V keeps every input safely under the ADC's absolute max):

| ADS1115 | Pi header |
|---|---|
| VDD | 3V3 (pin 1) |
| GND | GND (pin 6) — common with the detector grounds |
| SCL | GPIO3 / SCL (pin 5) |
| SDA | GPIO2 / SDA (pin 3) |
| ADDR | GND → I2C address 0x48 |
| A0 | forward detector output |
| A1 | reflected detector output |

I2C is already enabled by the RF Pi installer. Confirm the board:
`i2cdetect -y 1` should show `48` (and `40` if the battery monitor is fitted).

## Bench-test the ADC first (no RF)

Before wiring RF, prove the ADC + software with a 10 kohm pot: 3.3 V → wiper →
A0 → GND, then:

```bash
hampi-rfpower --raw        # live voltage per channel - turn the pot, watch it move
```

The same command is the best troubleshooting tool once the real detector is in
line: it shows exactly what the ADS1115 sees.

## Calibrate (recommended)

Datasheet defaults get you close; a two-point calibration into a **dummy load**
makes it accurate and cancels your exact coupler/pad/detector:

```bash
# key down ~10 W into a dummy load, then:
hampi-rfpower --cal 10
# key down ~100 W, then:
hampi-rfpower --cal 100
```

That writes `/etc/hampi/rfpower.cal` (a linear antenna-dBm-vs-volts fit). Re-run
any time. Then:

```bash
hampi-rfpower                        # one-shot forward/reflected/SWR
sudo touch /etc/hampi/rfpower.enabled
sudo systemctl start hampi-rfpower   # background logging + high-SWR alerts
```

The dashboard's **TX Power / SWR** widget shows it live while you transmit, with
peak-hold and a high-SWR warning. Data logs to `/var/log/hampi/rfpower.csv`.

## Safety

- Size the coupler for your **maximum** power with margin (CW/key-down, not PEP).
- Keep the detector input below its rated max at full power — check the budget.
- This meter is diagnostic; it does not key or unkey your radio. Watching SWR is
  the operator's job — the alert is a prompt, not an interlock.
