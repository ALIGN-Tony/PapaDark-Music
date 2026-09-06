#!/bin/bash
# HamPi kiosk setup: make the Pi boot straight into the dashboard on its own
# screen (RasPad / HDMI display), full-screen, no full desktop. The network
# service (hampi-dash on :8073) is untouched, so phones/laptops keep full
# access - this only ADDS the local screen.
#
# Usually run for you by setup.sh (--kiosk, and automatically for --image-build).
# To add it to an already-running Pi:
#   sudo HAMPI_KIOSK_USER=hamop bash scripts/kiosk-setup.sh
#
# Undo: sudo rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf \
#                  "$HOME/.xinitrc"; and remove the startx block from ~/.bash_profile.

set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Run with sudo (root needed to install packages)." >&2; exit 1; }

# The desktop user that should auto-login and show the kiosk. HAMPI_KIOSK_USER
# is set by setup.sh (e.g. inside the image-build chroot, where SUDO_USER isn't
# set); otherwise fall back to the sudo user or the first human account.
U="${HAMPI_KIOSK_USER:-${SUDO_USER:-hamop}}"
if ! id "$U" >/dev/null 2>&1; then
    U="$(getent passwd 1000 | cut -d: -f1)"    # first human account
fi
HOME_DIR="$(getent passwd "$U" | cut -d: -f6)"
echo "==> Kiosk user: $U   home: $HOME_DIR"

echo "==> Installing a minimal browser kiosk (no full desktop)…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
    xserver-xorg xserver-xorg-legacy xinit openbox unclutter
# Chromium package name differs across Debian/RPi repos - take whichever exists.
apt-get install -y --no-install-recommends chromium-browser \
    || apt-get install -y --no-install-recommends chromium

echo "==> Allowing the console user to start X…"
cat > /etc/X11/Xwrapper.config <<'EOF'
allowed_users=anybody
needs_root_rights=yes
EOF

echo "==> Enabling console autologin on tty1 for $U…"
install -d /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $U --noclear %I \$TERM
EOF

echo "==> Writing the kiosk session…"
cat > "$HOME_DIR/.xinitrc" <<'EOF'
#!/bin/sh
xset s off -dpms
xset s noblank
unclutter -idle 1 &
openbox &
exec hampi-kiosk --kiosk
EOF
chown "$U:$U" "$HOME_DIR/.xinitrc"
chmod +x "$HOME_DIR/.xinitrc"

# Start X automatically when $U logs in on the physical console (tty1).
PROFILE="$HOME_DIR/.bash_profile"
if ! grep -q 'HAMPI kiosk autostart' "$PROFILE" 2>/dev/null; then
    cat >> "$PROFILE" <<'EOF'

# HAMPI kiosk autostart: launch the dashboard full-screen on the local display.
if [ -z "${DISPLAY:-}" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec startx
fi
EOF
    chown "$U:$U" "$PROFILE"
fi

systemctl daemon-reload 2>/dev/null || true   # no running systemd inside a build chroot
echo
echo "============================================================"
echo " Kiosk installed. Reboot and the Pi boots into the dashboard"
echo " on its own screen. Phones/laptops still use http://<ip>:8073."
echo "     sudo reboot"
echo "============================================================"
