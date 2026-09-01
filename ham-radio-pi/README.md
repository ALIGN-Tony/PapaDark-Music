# HamPi Field Station — Amateur Radio Raspberry Pi Image

A reproducible, flashable Raspberry Pi OS (Bookworm, 64-bit, desktop) image
purpose-built for portable/field amateur radio operation, plus an installer
you can run on any existing Raspberry Pi OS system. Linux all the way down —
nothing here is locked to Pi-only software, but it is tuned to run
outstanding on a Raspberry Pi 4 (including one mounted in a **RasPad 3**
tablet) and Pi 5.

## What's on the image

| Need | Software |
|---|---|
| Digital modes | WSJT-X (FT8/FT4/WSPR), JS8Call, fldigi + flmsg/flamp (NBEMS EmComm), QSSTV, multimon-ng |
| CAT control | Hamlib (`rigctl`/`rigctld` network CAT server), flrig, grig |
| Radio programming | CHIRP-next (Baofeng/Yaesu/Icom/Kenwood memory programming) |
| Packet / APRS / Winlink | Direwolf software TNC, Xastir, Pat (Winlink email) |
| Propagation | HamClock, VOACAP (`voacapl`), `hampi-prop` (live N0NBH solar indices + band conditions + advice, offline cache) |
| Antennas | `hampi-antenna` field cutting charts (dipole, inverted-V, EFHW, vertical+radials, NVIS, J-pole, random wire, choke) and great-circle **beam headings** from grid squares; xnec2c/nec2c modelling |
| Power / battery | `hampi-power`: INA219/INA260 I2C battery monitor — volts, amps, watts, state-of-charge for LiFePO4 & lead-acid, CSV logging, low-voltage alerts, Pi under-voltage flags |
| Weather | `hampi-wx` (GPS-located forecast with wind/antenna warnings, offline cache, METAR), `metar` |
| Off-grid time | gpsd + chrony pre-wired: plug in any USB GPS and the clock stays FT8-accurate with **no internet** |
| Satellites | Gpredict (pass prediction, doppler, rotator control) |
| SDR | rtl-sdr tools, Gqrx |
| Logging | KLog, TrustedQSL (LoTW) |
| Dashboard | `hampi-menu` — one terminal menu for all of the above |

Everything is listed on the Pi itself in `/etc/hampi/APPS.txt` (also via the
menu's "apps" entry).

## Getting the image

### Option A — GitHub Actions (no build machine needed)
Run the **Build HamPi image** workflow from the repo's Actions tab. It builds
the full image with pi-gen and uploads `*.img.xz` as an artifact
(~2 h runtime). Set a repo secret `HAMPI_PASSWORD` to bake in your own
password; otherwise the default is `hampi-field`.

### Option B — build locally with Docker
On any Linux box with Docker and ~30 GB free:

```bash
cd ham-radio-pi
FIRST_USER_PASS='YourPassword' ./build.sh
# output: ham-radio-pi/pi-gen/deploy/<date>-HamPi-hampi.img.xz
```

### Option C — install onto an existing Raspberry Pi OS
Already running Raspberry Pi OS Bookworm (64-bit recommended)? Skip the image:

```bash
git clone https://github.com/ALIGN-Tony/PapaDark-Music
cd PapaDark-Music/ham-radio-pi
sudo ./setup.sh            # add --raspad on a RasPad 3
sudo reboot
```

The installer is idempotent and best-effort: if a download host is down, that
one component is reported at the end and you just re-run `setup.sh` later.

## Flash & first boot

1. Flash with Raspberry Pi Imager (or `xzcat img.xz | sudo dd of=/dev/sdX bs=4M`).
2. Boot. Login: **hamop / hampi-field** (change it: `passwd`). Hostname `hampi`, SSH enabled.
3. Set your station identity:
   ```bash
   sudo nano /etc/hampi/station.conf     # CALLSIGN, GRID, LAT/LON
   ```
4. Run `hampi-menu` (or the "HamPi Field Menu" desktop icon).

## Wiring up the shack

**CAT control** — plug the radio's USB/CAT cable in, then serve CAT to every
app at once:

```bash
rigctl -l | grep -i <your radio>          # find the model number
rigctld -m 3087 -r /dev/ttyUSB0 &         # example: IC-7300
```

Point WSJT-X/JS8Call/fldigi at *Hamlib NET rigctl*, `localhost:4532`. One
radio, every program shares it. The menu's "rig" entry walks through a test.

**Sound** — DigiRig/Signalink/radio-USB soundcards appear via `arecord -l`;
select them inside WSJT-X/fldigi/Direwolf (`ADEVICE plughw:1,0`).

**GPS time (critical for FT8 off-grid)** — plug in any USB GPS puck. gpsd
auto-detects it and chrony (see `/etc/chrony/conf.d/hampi-gps.conf`) steers
the clock to well under a second. For microsecond time, wire the GPS PPS pin
to GPIO18 and uncomment the `pps-gpio` overlay in `config.txt` plus the PPS
refclock line.

**Battery monitor** — wire an INA219 (or INA260) module: `VIN+/VIN-` in the
battery positive lead, module GND to battery negative and Pi GND, `SDA`→pin 3,
`SCL`→pin 5, `VCC`→3V3 (pin 1). Then:

```bash
i2cdetect -y 1                       # sensor shows at 0x40
sudo nano /etc/hampi/power.conf      # chemistry: lifepo4 or leadacid
hampi-power                          # one-shot status
sudo touch /etc/hampi/power.enabled  # start background logging + alerts
sudo systemctl start hampi-power
```

You get live volts/amps/watts, a state-of-charge estimate, CSV history in
`/var/log/hampi/power.csv`, and `wall`/syslog alerts before the battery gets
damaged or the finals brown out mid-QSO.

**APRS/packet** — `cp /etc/hampi/direwolf.conf ~/`, set `MYCALL`, run
`direwolf`. Xastir and Pat talk to its KISS port (8001).

**Winlink** — `pat configure`, then `pat connect telnet` (internet) or via
Direwolf/ARDOP RF gateways for true off-grid email.

## Field workflow examples

```bash
hampi-prop                      # is 20m open? what should I run right now?
hampi-antenna 40m               # cutting chart: dipole/inverted-V/EFHW/NVIS...
hampi-antenna 7.1 --type nvis   # regional EmComm coverage antenna
hampi-antenna --heading JO01    # beam heading + distance from your grid
hampi-prop --voacap JO01        # full VOACAP circuit prediction
hampi-wx --metar KDFW           # forecast + gust warnings for your masts
hampi-power                     # how much battery is left?
```

`hampi-prop` and `hampi-wx` cache their last good reports, so you can review
conditions after you've lost internet in the field.

## RasPad 3 notes

The RasPad 3 is a Pi 4 carrier, so the stock image boots it as-is. The image
build already includes the SunFounder `raspad-launcher` (screen rotation,
touch-friendly launcher, onboard-battery indicator); on an existing system run
`sudo ./setup.sh --raspad`. HamClock at 800×480 fits the 1280×800 touchscreen
nicely windowed; the terminal tools are all touch-keyboard friendly via the
launcher. The RasPad's internal battery is separate from the *station* battery
monitor — `hampi-power` watches your 12 V radio supply.

## Layout

```
ham-radio-pi/
├── build.sh            # local pi-gen (Docker) image build
├── pi-gen.config       # image settings (hostname, user, stages)
├── prepare-stage.sh    # copies installer+payload into the pi-gen stage
├── stage-ham/          # custom pi-gen stage (runs setup.sh in the chroot)
├── setup.sh            # the installer (image build AND standalone use)
└── payload/
    ├── tools/          # hampi-menu, hampi-prop, hampi-antenna, hampi-power, hampi-wx
    ├── configs/        # /etc/hampi templates (station, power, direwolf, APPS)
    ├── systemd/        # hampi-power.service
    └── desktop/        # menu + HamClock launchers
```

## License / data sources

Solar data: N0NBH (hamqsl.com). Weather: Open-Meteo & aviationweather.gov.
VOACAP: jawatson/voacapl. HamClock: Clear Sky Institute (WB0OEW). All
installed applications retain their own licenses.
