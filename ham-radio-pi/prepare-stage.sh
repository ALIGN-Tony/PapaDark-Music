#!/bin/bash -e
# Populate stage-ham/00-install-ham/files/hampi with the installer + payload
# so pi-gen can copy it into the image. Run before any pi-gen build.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${SCRIPT_DIR}/stage-ham/00-install-ham/files/hampi"

rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "${SCRIPT_DIR}/setup.sh" "${SCRIPT_DIR}/payload" "${SCRIPT_DIR}/scripts" "$DEST/"
# Vendor PUBLIC key (arms license enforcement in the image). The private
# vendor.key is gitignored and must never be copied into a build.
if [ -f "${SCRIPT_DIR}/vendor/vendor.pub" ]; then
    mkdir -p "$DEST/vendor"
    cp "${SCRIPT_DIR}/vendor/vendor.pub" "$DEST/vendor/vendor.pub"
fi
echo "Stage payload prepared at $DEST"
