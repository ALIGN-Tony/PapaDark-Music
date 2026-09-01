#!/bin/bash -e
# Populate stage-ham/00-install-ham/files/hampi with the installer + payload
# so pi-gen can copy it into the image. Run before any pi-gen build.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${SCRIPT_DIR}/stage-ham/00-install-ham/files/hampi"

rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "${SCRIPT_DIR}/setup.sh" "${SCRIPT_DIR}/payload" "$DEST/"
echo "Stage payload prepared at $DEST"
