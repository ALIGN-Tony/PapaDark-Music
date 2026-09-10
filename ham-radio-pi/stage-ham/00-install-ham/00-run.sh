#!/bin/bash -e
# Copy the HamPi installer + payload into the image and run it in the chroot.
# prepare-stage.sh must have populated files/hampi before the build.

if [ ! -f files/hampi/setup.sh ]; then
    echo "stage-ham: files/hampi is empty - run ham-radio-pi/prepare-stage.sh first" >&2
    exit 1
fi

install -d "${ROOTFS_DIR}/opt/hampi/installer"
cp -a files/hampi/. "${ROOTFS_DIR}/opt/hampi/installer/"
chmod +x "${ROOTFS_DIR}/opt/hampi/installer/setup.sh"

on_chroot << EOF
/opt/hampi/installer/setup.sh --image-build --raspad --user ${FIRST_USER_NAME}
EOF
