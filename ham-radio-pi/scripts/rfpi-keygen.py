#!/usr/bin/env python3
"""RF Pi vendor key tool - generates the signing keypair and issues customer
license keys. This is VENDOR-SIDE ONLY: it never ships in the image.

One-time setup (creates vendor/vendor.key + vendor/vendor.pub):
    ./rfpi-keygen.py --init

vendor/vendor.pub is baked into the image by setup.sh and may be committed.
vendor/vendor.key is the business - anyone holding it can mint licenses.
It is gitignored; keep an offline backup.

Issue a customer key (paste the output into the buyer's delivery email):
    ./rfpi-keygen.py --call K4DIA --name "Tony" --email buyer@example.com

Check a key against the public key:
    ./rfpi-keygen.py --verify "RFPI1.xxxx.yyyy"

Key format: RFPI1.<base64url(payload json)>.<base64url(ed25519 signature)>
Payload: {"p":"rfpi","v":1,"call":...,"name":...,"email":...,"issued":...}
The Pi verifies the signature offline with the embedded public key - no
activation server, which is the point for an off-grid field device.

Requires: python3-cryptography (apt install python3-cryptography).
"""

import argparse
import base64
import datetime
import json
import os
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
from cryptography.exceptions import InvalidSignature

VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "vendor")


def b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def init_keys(vendor_dir):
    os.makedirs(vendor_dir, exist_ok=True)
    key_path = os.path.join(vendor_dir, "vendor.key")
    pub_path = os.path.join(vendor_dir, "vendor.pub")
    if os.path.exists(key_path):
        sys.exit(f"{key_path} already exists - refusing to overwrite the "
                 "signing key (existing customer licenses depend on it).")
    priv = Ed25519PrivateKey.generate()
    raw_priv = priv.private_bytes_raw()
    raw_pub = priv.public_key().public_bytes_raw()
    with open(key_path, "wb") as fh:
        fh.write(base64.b64encode(raw_priv) + b"\n")
    os.chmod(key_path, 0o600)
    with open(pub_path, "wb") as fh:
        fh.write(base64.b64encode(raw_pub) + b"\n")
    print(f"Signing key : {key_path}  (PRIVATE - back it up offline, never commit)")
    print(f"Public key  : {pub_path}  (baked into the image; safe to commit)")
    print("\nNext: rebuild the image (or copy vendor.pub to /etc/hampi/vendor.pub")
    print("on existing installs) so RF Pi starts enforcing trial/licenses.")


def load_priv(vendor_dir):
    path = os.path.join(vendor_dir, "vendor.key")
    try:
        raw = base64.b64decode(open(path, "rb").read().strip())
    except OSError:
        sys.exit(f"No signing key at {path} - run --init first.")
    return Ed25519PrivateKey.from_private_bytes(raw)


def issue(vendor_dir, call, name, email):
    priv = load_priv(vendor_dir)
    payload = json.dumps({
        "p": "rfpi", "v": 1,
        "call": call.strip().upper(),
        "name": name.strip(),
        "email": email.strip(),
        "issued": datetime.date.today().isoformat(),
    }, separators=(",", ":"), sort_keys=True).encode()
    key = f"RFPI1.{b64e(payload)}.{b64e(priv.sign(payload))}"
    print(key)
    print(f"\nLicensed to {call.upper()} ({name}). Deliver the full RFPI1.… "
          "string; the buyer pastes it into the dashboard's activation screen "
          "or saves it as /var/lib/hampi/license.key.", file=sys.stderr)


def verify(vendor_dir, key_text):
    pub_path = os.path.join(vendor_dir, "vendor.pub")
    try:
        raw = base64.b64decode(open(pub_path, "rb").read().strip())
    except OSError:
        sys.exit(f"No public key at {pub_path}.")
    pub = Ed25519PublicKey.from_public_bytes(raw)
    parts = key_text.strip().split(".")
    if len(parts) != 3 or parts[0] != "RFPI1":
        sys.exit("Malformed key (expected RFPI1.<payload>.<signature>).")
    payload, sig = b64d(parts[1]), b64d(parts[2])
    try:
        pub.verify(sig, payload)
    except InvalidSignature:
        sys.exit("INVALID signature - this key was not issued by this vendor key.")
    print("VALID:", json.dumps(json.loads(payload), indent=2))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vendor-dir", default=VENDOR_DIR)
    ap.add_argument("--init", action="store_true", help="generate the vendor keypair")
    ap.add_argument("--call", help="buyer callsign to license")
    ap.add_argument("--name", default="", help="buyer name")
    ap.add_argument("--email", default="", help="buyer email")
    ap.add_argument("--verify", metavar="KEY", help="verify an issued key")
    args = ap.parse_args()

    if args.init:
        init_keys(args.vendor_dir)
    elif args.verify:
        verify(args.vendor_dir, args.verify)
    elif args.call:
        issue(args.vendor_dir, args.call, args.name, args.email)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
