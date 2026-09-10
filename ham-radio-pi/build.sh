#!/bin/bash -e
#
# Build the HamPi flashable image with pi-gen inside Docker.
#
# Requirements on the build host (any x86_64 or arm64 Linux box):
#   - Docker
#   - ~30 GB free disk, a few hours on first build
#
# Usage:
#   FIRST_USER_PASS='YourPassword' ./build.sh
#
# Output: pi-gen/deploy/<date>-HamPi-hampi.img.xz
#         Flash with Raspberry Pi Imager or:  xzcat *.img.xz | sudo dd of=/dev/sdX bs=4M status=progress

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PI_GEN_DIR="${SCRIPT_DIR}/pi-gen"
PI_GEN_REPO="https://github.com/RPi-Distro/pi-gen.git"
PI_GEN_BRANCH="${PI_GEN_BRANCH:-master}"

command -v docker >/dev/null || { echo "Docker is required." >&2; exit 1; }

if [ ! -d "$PI_GEN_DIR" ]; then
    git clone --depth 1 --branch "$PI_GEN_BRANCH" "$PI_GEN_REPO" "$PI_GEN_DIR"
fi

"${SCRIPT_DIR}/prepare-stage.sh"

rm -rf "${PI_GEN_DIR}/stage-ham"
cp -a "${SCRIPT_DIR}/stage-ham" "${PI_GEN_DIR}/stage-ham"

# Materialize the config (resolving FIRST_USER_PASS from the environment).
FIRST_USER_PASS="${FIRST_USER_PASS:-hampi-field}"
sed "s|\${FIRST_USER_PASS:-hampi-field}|${FIRST_USER_PASS}|" \
    "${SCRIPT_DIR}/pi-gen.config" > "${PI_GEN_DIR}/config"

cd "$PI_GEN_DIR"
./build-docker.sh

echo
echo "Done. Images are in ${PI_GEN_DIR}/deploy/"
ls -lh deploy/ 2>/dev/null || true
