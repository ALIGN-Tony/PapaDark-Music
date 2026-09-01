#!/bin/bash
#
# RF Pi (RFπ) Field Station installer - K4DIA / Tony (PapaDark)'s
# amateur radio software suite. (Internal names keep the hampi- prefix.)
#
# Runs in two contexts:
#   1. Inside the pi-gen chroot during an image build:  setup.sh --image-build
#   2. Directly on an existing Raspberry Pi OS (Bookworm) system:  sudo ./setup.sh
#
# Best-effort philosophy: a failure in one optional component (e.g. a download
# host being down) must never abort the whole install. Failures are collected
# and reported at the end.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD_DIR="${SCRIPT_DIR}/payload"

IMAGE_BUILD=0
WITH_RASPAD=0
SKIP_HEAVY=0
TARGET_USER=""

usage() {
    cat <<EOF
Usage: sudo ./setup.sh [options]

Options:
  --image-build   Non-interactive mode for use inside a pi-gen chroot.
  --raspad        Also install the SunFounder RasPad 3 launcher/rotation support.
  --skip-heavy    Skip long source builds (HamClock, VOACAP).
  --user NAME     Target user to configure (default: hamop in image builds,
                  otherwise the user who invoked sudo).
  -h, --help      Show this help.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --image-build) IMAGE_BUILD=1 ;;
        --raspad)      WITH_RASPAD=1 ;;
        --skip-heavy)  SKIP_HEAVY=1 ;;
        --user)        TARGET_USER="$2"; shift ;;
        -h|--help)     usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    esac
    shift
done

if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must run as root (use sudo)." >&2
    exit 1
fi

if [ -z "$TARGET_USER" ]; then
    if [ "$IMAGE_BUILD" -eq 1 ]; then
        TARGET_USER="hamop"
    else
        TARGET_USER="${SUDO_USER:-pi}"
    fi
fi

export DEBIAN_FRONTEND=noninteractive

FAILURES=()

log()  { echo -e "\n==> $*"; }
warn() { echo "WARNING: $*" >&2; }

# Run a named step; record (but don't die on) failure.
best_effort() {
    local name="$1"; shift
    log "$name"
    if "$@"; then
        return 0
    fi
    warn "$name failed - continuing."
    FAILURES+=("$name")
    return 1
}

BOOT_CONFIG="/boot/firmware/config.txt"
[ -f "$BOOT_CONFIG" ] || BOOT_CONFIG="/boot/config.txt"

# ---------------------------------------------------------------------------
# 1. APT packages
# ---------------------------------------------------------------------------

install_apt_packages() {
    apt-get update || return 1

    # Grouped for readability; installed in one transaction, with a
    # per-package fallback pass so one missing package can't sink the rest.
    local pkgs=(
        # --- Digital modes / soundcard ---
        wsjtx                 # FT8/FT4/JT65/WSPR (weak-signal HF)
        fldigi flrig flmsg flamp flwrap   # PSK31/RTTY/Olivia + NBEMS EmComm forms
        qsstv                 # Slow-scan TV
        multimon-ng           # Decode POCSAG/DTMF/AFSK from audio
        # --- Packet / APRS ---
        direwolf              # Software TNC (APRS, AX.25, Winlink ARDOP peer)
        ax25-tools ax25-apps
        xastir                # APRS mapping client
        # --- CAT control ---
        libhamlib-utils       # rigctl / rigctld / rotctl / rotctld
        grig                  # Simple graphical rig control
        # --- SDR / waterfall ---
        rtl-sdr               # RTL2832U tools (rtl_test, rtl_power, rtl_fm...)
        gqrx-sdr              # Waterfall receiver #1 (GNU Radio based)
        cubicsdr              # Waterfall receiver #2 (lighter, touch-friendly)
        soapysdr-tools soapysdr-module-all  # Hardware abstraction: RTL/Airspy/HackRF/SDRplay...
        airspy hackrf         # Native tools + udev rules for those radios
        # --- Satellites ---
        gpredict              # Pass prediction + rotator/rig doppler control
        # --- Logging / awards ---
        klog trustedqsl
        # --- Antenna modelling ---
        nec2c xnec2c
        # --- GPS + precision time (FT8 needs <1 s clock accuracy off-grid) ---
        gpsd gpsd-clients chrony pps-tools
        # --- Weather ---
        metar
        # --- Power / battery monitoring (I2C sensors) ---
        i2c-tools python3-smbus
        # --- HamPi dashboard (web UI) + desktop on-screen keyboards ---
        python3-flask
        python3-cryptography   # RF Pi license key verification (Ed25519)
        squeekboard matchbox-keyboard   # system OSKs for non-dashboard apps
        # --- Tooling used by HamPi scripts and installers ---
        python3-requests python3-serial pipx jq curl wget git whiptail
        build-essential cmake
        # CHIRP runtime (wx from apt so pipx doesn't have to compile it)
        python3-wxgtk4.0 python3-yattag
        # HamClock build deps
        libx11-dev xdg-utils
        # VOACAP build deps
        gfortran automake autoconf
        # Audio plumbing
        pavucontrol sox alsa-utils
    )

    if apt-get install -y --no-install-recommends "${pkgs[@]}"; then
        return 0
    fi

    warn "Bulk apt install failed; retrying packages individually."
    local p rc=0
    for p in "${pkgs[@]}"; do
        if ! apt-get install -y --no-install-recommends "$p"; then
            warn "Package not installed: $p"
            FAILURES+=("apt:$p")
            rc=1
        fi
    done
    return $rc
}

# ---------------------------------------------------------------------------
# 2. User, groups, hardware interfaces
# ---------------------------------------------------------------------------

configure_user_and_groups() {
    if ! id "$TARGET_USER" >/dev/null 2>&1; then
        warn "User $TARGET_USER does not exist; skipping group setup."
        return 1
    fi
    # dialout: USB CAT/serial; audio: soundcard modes; i2c/gpio/spi: sensors.
    local g
    for g in dialout audio plugdev i2c gpio spi tty video; do
        getent group "$g" >/dev/null && usermod -aG "$g" "$TARGET_USER"
    done
    return 0
}

enable_hw_interfaces() {
    [ -f "$BOOT_CONFIG" ] || { warn "No boot config.txt found; enable I2C/UART manually."; return 1; }

    grep -q '^# HamPi hardware interfaces' "$BOOT_CONFIG" && return 0
    cat >> "$BOOT_CONFIG" <<'EOF'

# HamPi hardware interfaces
dtparam=i2c_arm=on
# UART for GPS modules on GPIO14/15
enable_uart=1
# Uncomment for a GPS PPS line on GPIO18 (then see /etc/chrony/conf.d/hampi-gps.conf)
#dtoverlay=pps-gpio,gpiopin=18
EOF
    # Load the i2c-dev module at boot so /dev/i2c-1 exists for the power monitor.
    echo i2c-dev > /etc/modules-load.d/hampi-i2c.conf
    return 0
}

# ---------------------------------------------------------------------------
# 3. HamPi payload: field tools, configs, services, menu entries
# ---------------------------------------------------------------------------

install_payload() {
    [ -d "$PAYLOAD_DIR" ] || { warn "Payload directory missing: $PAYLOAD_DIR"; return 1; }

    install -d /etc/hampi /var/log/hampi /opt/hampi

    local t n
    for t in "$PAYLOAD_DIR"/tools/*; do
        n=$(basename "$t")
        install -m 0755 "$t" "/usr/local/bin/$n"
        # Brand alias: every hampi-* tool also answers to rfpi-*.
        ln -sf "$n" "/usr/local/bin/${n/hampi-/rfpi-}"
    done
    ln -sf hampi-menu /usr/local/bin/rfpi

    # Config templates: never clobber operator-edited files. License and
    # open-source notices are always refreshed so the legal text stays current.
    local c dest base
    for c in "$PAYLOAD_DIR"/configs/*; do
        base="$(basename "$c")"
        dest="/etc/hampi/$base"
        case "$base" in
            LICENSE-RFPI.txt|OPEN-SOURCE.txt)
                install -m 0644 "$c" "$dest" ;;   # always refresh legal notices
            *)
                [ -e "$dest" ] || install -m 0644 "$c" "$dest" ;;
        esac
    done

    install -m 0644 "$PAYLOAD_DIR"/systemd/*.service /etc/systemd/system/
    sed -i "s/__HAMPI_USER__/${TARGET_USER}/" /etc/systemd/system/hampi-dash.service
    install -d /usr/share/applications
    install -m 0644 "$PAYLOAD_DIR"/desktop/*.desktop /usr/share/applications/

    # Dashboard web UI (server script is installed with the other tools above).
    install -d /usr/local/share/hampi-dash /var/lib/hampi
    cp -a "$PAYLOAD_DIR"/dash/. /usr/local/share/hampi-dash/
    chown -R "$TARGET_USER":"$TARGET_USER" /var/lib/hampi 2>/dev/null || true

    # RF Pi licensing: enforcement arms only when the vendor public key is
    # present (create with scripts/rfpi-keygen.py --init; the PRIVATE key
    # never ships). Without it this stays a free/dev build.
    if [ -f "$SCRIPT_DIR/vendor/vendor.pub" ]; then
        install -m 0644 "$SCRIPT_DIR/vendor/vendor.pub" /etc/hampi/vendor.pub
        echo "RF Pi licensing armed (vendor.pub installed)."
    fi

    # Bring the dashboard up in an app window when the desktop session starts,
    # so the RasPad boots straight into the widgets. Delete this file to opt out.
    install -d /etc/xdg/autostart
    install -m 0644 "$PAYLOAD_DIR"/desktop/hampi-dashboard.desktop \
        /etc/xdg/autostart/hampi-dashboard.desktop

    # Chrony: accept time from gpsd via shared memory (works with any USB GPS).
    install -d /etc/chrony/conf.d
    cat > /etc/chrony/conf.d/hampi-gps.conf <<'EOF'
# GPS time via gpsd shared memory - keeps FT8/JS8 usable with no internet.
refclock SHM 0 refid GPS precision 1e-1 offset 0.2 delay 0.2
# With a PPS line wired (see config.txt pps-gpio overlay), uncomment for ~1 us time:
#refclock PPS /dev/pps0 refid PPS lock GPS
EOF

    # gpsd: auto-grab hot-plugged USB GPS pucks.
    if [ -f /etc/default/gpsd ]; then
        sed -i 's/^USBAUTO=.*/USBAUTO="true"/' /etc/default/gpsd
        sed -i 's/^GPSD_OPTIONS=.*/GPSD_OPTIONS="-n"/' /etc/default/gpsd
    fi

    chown -R "$TARGET_USER":"$TARGET_USER" /var/log/hampi 2>/dev/null || true

    systemctl daemon-reload 2>/dev/null || true
    # The unit is gated on /etc/hampi/power.enabled, so enabling it is harmless
    # on systems with no power sensor attached.
    systemctl enable hampi-power.service 2>/dev/null || true
    systemctl enable hampi-dash.service 2>/dev/null || true
    # Field hotspot when no known Wi-Fi is in range at boot.
    # Opt out: sudo touch /etc/hampi/hotspot-auto.disabled
    systemctl enable hampi-hotspot-auto.service 2>/dev/null || true
    systemctl enable gpsd 2>/dev/null || true
    [ "$IMAGE_BUILD" -eq 0 ] && systemctl restart hampi-dash.service 2>/dev/null || true
    return 0
}

configure_sdr() {
    # The kernel's DVB-T driver grabs RTL-SDR dongles before librtlsdr can;
    # blacklisting it is what makes gqrx/CubicSDR "just work" on first plug-in.
    cat > /etc/modprobe.d/hampi-rtlsdr-blacklist.conf <<'EOF'
# RTL2832U dongles are SDRs here, not DVB-T tuners.
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
EOF
    return 0
}

# ---------------------------------------------------------------------------
# 4. Software not packaged in Debian (best-effort downloads / builds)
# ---------------------------------------------------------------------------

install_sdrpp() {
    # SDR++ - modern waterfall UI. Upstream nightlies don't always ship an
    # arm64 .deb, so this is best-effort; gqrx and CubicSDR (from apt) are the
    # guaranteed waterfalls either way.
    local arch pat url tmp
    arch="$(dpkg --print-architecture)"
    case "$arch" in
        arm64) pat='(arm64|aarch64|raspios)' ;;
        *)     pat="$arch" ;;
    esac
    url=$(curl -fsSL https://api.github.com/repos/AlexandreRouma/SDRPlusPlus/releases \
        | jq -r '.[].assets[].browser_download_url | select(endswith(".deb"))' \
        | grep -Ei "$pat" | grep -i bookworm | head -n1)
    [ -n "$url" ] || url=$(curl -fsSL https://api.github.com/repos/AlexandreRouma/SDRPlusPlus/releases \
        | jq -r '.[].assets[].browser_download_url | select(endswith(".deb"))' \
        | grep -Ei "$pat" | head -n1)
    if [ -z "$url" ]; then
        warn "No SDR++ .deb for $arch published upstream; using gqrx/CubicSDR instead."
        return 1
    fi
    tmp=$(mktemp -d)
    curl -fsSL -o "$tmp/sdrpp.deb" "$url" && apt-get install -y "$tmp/sdrpp.deb"
    local rc=$?
    rm -rf "$tmp"
    return $rc
}

install_pat() {
    # Pat - Winlink email client (la5nta/pat), arm64 .deb from GitHub releases.
    local arch url tmp
    arch="$(dpkg --print-architecture)"
    url=$(curl -fsSL https://api.github.com/repos/la5nta/pat/releases/latest \
        | jq -r --arg a "$arch" '.assets[].browser_download_url | select(test("linux_" + $a + "\\.deb$"))' \
        | head -n1)
    [ -n "$url" ] && [ "$url" != "null" ] || { warn "No Pat .deb found for $arch"; return 1; }
    tmp=$(mktemp -d)
    curl -fsSL -o "$tmp/pat.deb" "$url" && apt-get install -y "$tmp/pat.deb"
    local rc=$?
    rm -rf "$tmp"
    return $rc
}

install_chirp() {
    # CHIRP-next radio programmer: official wheel via pipx, using the system
    # wxPython (compiling wx on a Pi takes hours - never do that).
    local url
    url=$(python3 - <<'EOF'
import re, requests
base = "https://archive.chirpmyradio.com/chirp_next/"
idx = requests.get(base, timeout=30).text
builds = sorted(set(re.findall(r'next-(\d+)', idx)))
if not builds:
    raise SystemExit(1)
b = builds[-1]
page = requests.get(f"{base}next-{b}/", timeout=30).text
m = re.search(r'href="([^"]+\.whl)"', page)
if not m:
    raise SystemExit(1)
whl = m.group(1)
print(whl if whl.startswith("http") else f"{base}next-{b}/{whl}")
EOF
    ) || { warn "Could not locate a CHIRP wheel."; return 1; }

    PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin \
        pipx install --system-site-packages "$url"
}

install_js8call() {
    # JS8Call publishes builds on files.js8call.com; naming varies by release,
    # so scrape for a matching .deb and fall back to a manual-install note.
    local arch pat url tmp
    arch="$(dpkg --print-architecture)"
    case "$arch" in
        arm64) pat='(arm64|aarch64)' ;;
        armhf) pat='(armhf|armv7|raspbian)' ;;
        *)     pat="$arch" ;;
    esac
    url=$(curl -fsSL http://files.js8call.com/latest.html \
        | grep -oE 'href="[^"]+\.deb"' | cut -d'"' -f2 \
        | grep -E "$pat" | head -n1)
    if [ -z "$url" ]; then
        warn "No JS8Call .deb for $arch found; install manually from http://files.js8call.com/"
        return 1
    fi
    case "$url" in http*) ;; *) url="http://files.js8call.com/$url" ;; esac
    tmp=$(mktemp -d)
    curl -fsSL -o "$tmp/js8call.deb" "$url" && apt-get install -y "$tmp/js8call.deb"
    local rc=$?
    rm -rf "$tmp"
    return $rc
}

install_hamclock() {
    # HamClock (WB0OEW): propagation, solar data, DX cluster, beam headings,
    # grayline - the field operator's wall display. Built from source.
    local src=/opt/hampi/build/ESPHamClock
    install -d /opt/hampi/build
    rm -rf "$src"
    curl -fsSL -o /opt/hampi/build/ESPHamClock.tgz \
        https://www.clearskyinstitute.com/ham/HamClock/ESPHamClock.tgz || return 1
    tar -xzf /opt/hampi/build/ESPHamClock.tgz -C /opt/hampi/build || return 1
    make -C "$src" -j"$(nproc)" hamclock-800x480 || return 1
    install -m 0755 "$src/hamclock-800x480" /usr/local/bin/hamclock
    rm -f /opt/hampi/build/ESPHamClock.tgz
    return 0
}

install_voacap() {
    # VOACAP (voacapl fork) - the reference HF point-to-point/area propagation
    # engine, used by hampi-prop --voacap for coverage predictions.
    local src=/opt/hampi/build/voacapl
    install -d /opt/hampi/build
    rm -rf "$src"
    git clone --depth 1 https://github.com/jawatson/voacapl "$src" || return 1
    (
        cd "$src" &&
        ./autogen.sh &&
        ./configure --prefix=/usr/local &&
        make -j"$(nproc)" &&
        make install &&
        make installitshfbc
    ) || return 1
    return 0
}

install_raspad_support() {
    # SunFounder RasPad 3: launcher, screen rotation, onboard battery indicator.
    local src=/opt/hampi/build/raspad-launcher
    install -d /opt/hampi/build
    rm -rf "$src"
    git clone --depth 1 https://github.com/raspad-tablet/raspad-launcher "$src" || return 1
    (cd "$src" && ./install) || return 1
    return 0
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

log "HamPi Field Station install starting (user: $TARGET_USER, image build: $IMAGE_BUILD)"

best_effort "Install apt packages"            install_apt_packages
best_effort "Configure user and groups"       configure_user_and_groups
best_effort "Enable I2C/UART interfaces"      enable_hw_interfaces
best_effort "Configure SDR (RTL driver blacklist)" configure_sdr
best_effort "Install HamPi field tools"       install_payload
best_effort "Install SDR++ waterfall"         install_sdrpp
best_effort "Install Pat (Winlink)"           install_pat
best_effort "Install CHIRP (radio programming)" install_chirp
best_effort "Install JS8Call"                 install_js8call

if [ "$SKIP_HEAVY" -eq 0 ]; then
    best_effort "Build HamClock"              install_hamclock
    best_effort "Build VOACAP (voacapl)"      install_voacap
else
    log "Skipping heavy source builds (--skip-heavy)."
fi

if [ "$WITH_RASPAD" -eq 1 ]; then
    best_effort "Install RasPad 3 support"    install_raspad_support
fi

apt-get clean

log "HamPi install finished."
if [ ${#FAILURES[@]} -gt 0 ]; then
    echo "The following optional steps failed and can be retried later by re-running setup.sh:"
    printf '  - %s\n' "${FAILURES[@]}"
    echo "(Everything else installed normally.)"
fi

if [ "$IMAGE_BUILD" -eq 0 ]; then
    echo
    echo "Next steps:"
    echo "  1. Edit /etc/hampi/station.conf (callsign, grid, coordinates)."
    echo "  2. Reboot to activate I2C/UART and group membership."
    echo "  3. Run 'hampi-menu' for the field dashboard."
fi
exit 0
