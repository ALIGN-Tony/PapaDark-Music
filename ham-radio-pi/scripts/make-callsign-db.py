#!/usr/bin/env python3
"""Build RF Pi's offline callsign database from the FCC ULS amateur dump.

Turns the FCC's public "l_amat" license archive into a compact, indexed
SQLite file the dashboard queries with no internet. Public-domain data
(fcc.gov/uls), US amateur licenses only.

    # download the weekly FCC dump and build the DB:
    make-callsign-db.py --out /var/lib/hampi/callsign.sqlite

    # build from an already-extracted dump directory (EN.dat, HD.dat, AM.dat):
    make-callsign-db.py --from ./l_amat --out callsign.sqlite

The result has one row per active callsign: name, city, state, zip, license
class, status and expiry. FCC ULS carries no coordinates, so there is no grid
here - the map/spots get grids from on-air data instead.

Rebuild weekly to stay current; ~60 MB download, ~250 MB output, a few minutes.
Requires only the Python standard library.
"""

import argparse
import io
import os
import sqlite3
import sys
import tempfile
import urllib.request
import zipfile

FCC_URL = "https://data.fcc.gov/download/pub/uls/complete/l_amat.zip"

# operator_class code -> label
CLASS = {"E": "Amateur Extra", "A": "Advanced", "G": "General",
         "T": "Technician", "P": "Tech Plus", "N": "Novice"}
# license_status code -> label (we keep only Active in the shipped DB)
STATUS = {"A": "Active", "E": "Expired", "C": "Cancelled", "T": "Terminated"}


def fields(line):
    # ULS .dat files are pipe-delimited, one record per line.
    return line.rstrip("\n").split("|")


def open_dat(src_dir, name):
    """Open EN.dat / HD.dat / AM.dat case-insensitively."""
    for cand in (name, name.lower(), name.upper()):
        p = os.path.join(src_dir, cand)
        if os.path.exists(p):
            return open(p, encoding="latin-1", errors="replace")
    raise FileNotFoundError(f"{name} not found in {src_dir}")


def build(src_dir, out_path):
    tmp = out_path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.executescript("""
        PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
        CREATE TABLE en (usi INTEGER PRIMARY KEY, call TEXT, name TEXT,
                         city TEXT, state TEXT, zip TEXT);
        CREATE TABLE hd (usi INTEGER PRIMARY KEY, status TEXT, expires TEXT);
        CREATE TABLE am (usi INTEGER PRIMARY KEY, class TEXT);
    """)

    def load(name, sql, pick):
        n = 0
        batch = []
        with open_dat(src_dir, name) as fh:
            for line in fh:
                f = fields(line)
                row = pick(f)
                if row is None:
                    continue
                batch.append(row)
                if len(batch) >= 5000:
                    db.executemany(sql, batch)
                    batch.clear()
                n += 1
        if batch:
            db.executemany(sql, batch)
        db.commit()
        return n

    def pick_en(f):
        # EN: 4=call, 7=entity_name, 8=first, 10=last, 16=city, 17=state, 18=zip
        if len(f) < 19 or not f[4]:
            return None
        first, last, entity = f[8].strip(), f[10].strip(), f[7].strip()
        name = f"{first} {last}".strip() if (first or last) else entity
        return (int(f[1]), f[4].strip().upper(), name.title() if name else "",
                f[16].strip().title(), f[17].strip().upper(), f[18].strip()[:5])

    def pick_hd(f):
        # HD: 5=license_status, 8=expired_date
        if len(f) < 9 or f[5] not in STATUS:
            return None
        return (int(f[1]), STATUS[f[5]], f[8].strip())

    def pick_am(f):
        # AM: 5=operator_class
        if len(f) < 6:
            return None
        return (int(f[1]), CLASS.get(f[5].strip(), f[5].strip()))

    print("Parsing EN.dat (entities)…", file=sys.stderr)
    n_en = load("EN.dat", "INSERT OR IGNORE INTO en VALUES (?,?,?,?,?,?)", pick_en)
    print("Parsing HD.dat (license status)…", file=sys.stderr)
    load("HD.dat", "INSERT OR IGNORE INTO hd VALUES (?,?,?)", pick_hd)
    print("Parsing AM.dat (operator class)…", file=sys.stderr)
    load("AM.dat", "INSERT OR IGNORE INTO am VALUES (?,?)", pick_am)

    print("Composing callsign table…", file=sys.stderr)
    db.executescript("""
        CREATE TABLE calls (
            call TEXT PRIMARY KEY, name TEXT, city TEXT, state TEXT,
            zip TEXT, class TEXT, status TEXT, expires TEXT);
        INSERT OR REPLACE INTO calls
            SELECT en.call, en.name, en.city, en.state, en.zip,
                   COALESCE(am.class,''), COALESCE(hd.status,'Active'),
                   COALESCE(hd.expires,'')
            FROM en
            LEFT JOIN hd ON hd.usi = en.usi
            LEFT JOIN am ON am.usi = en.usi
            WHERE COALESCE(hd.status,'Active') = 'Active';
        DROP TABLE en; DROP TABLE hd; DROP TABLE am;
    """)
    n_calls = db.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
    import datetime
    db.execute("CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT)")
    db.executemany("INSERT INTO meta VALUES (?,?)", [
        ("built", datetime.date.today().isoformat()),
        ("count", str(n_calls)),
        ("source", "FCC ULS l_amat (public domain)")])
    db.commit()
    print("Vacuuming…", file=sys.stderr)
    db.execute("VACUUM")
    db.commit()
    db.close()
    os.replace(tmp, out_path)
    size_mb = os.path.getsize(out_path) / 1e6
    print(f"Built {out_path}: {n_calls:,} active callsigns "
          f"(from {n_en:,} entities), {size_mb:.0f} MB.", file=sys.stderr)


def download_and_build(out_path):
    with tempfile.TemporaryDirectory() as td:
        print(f"Downloading {FCC_URL} …", file=sys.stderr)
        req = urllib.request.Request(FCC_URL, headers={"User-Agent": "RF-Pi-build"})
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
        print(f"  {len(data)/1e6:.0f} MB, extracting…", file=sys.stderr)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(td)
        build(td, out_path)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="/var/lib/hampi/callsign.sqlite",
                    help="output SQLite path")
    ap.add_argument("--from", dest="src", metavar="DIR",
                    help="build from an extracted dump dir instead of downloading")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    if args.src:
        build(args.src, args.out)
    else:
        download_and_build(args.out)


if __name__ == "__main__":
    main()
