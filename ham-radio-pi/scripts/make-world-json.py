#!/usr/bin/env python3
"""Regenerate payload/dash/world.json from Natural Earth 110m coastline data.

The dashboard's map widget needs offline coastlines (field use - no CDN).
Source (public domain):
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_coastline.geojson

Usage: make-world-json.py ne_110m_coastline.geojson > ../payload/dash/world.json

Output format: {"lines": [[lat0,lon0,lat1,lon1,...], ...]} with coordinates
rounded to 0.1 deg (~11 km - plenty at azimuthal-map scale) and short
fragments dropped.
"""

import json
import sys


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = json.load(open(sys.argv[1]))
    lines = []
    for feat in src["features"]:
        geom = feat["geometry"]
        parts = [geom["coordinates"]] if geom["type"] == "LineString" \
            else geom["coordinates"]
        for coords in parts:
            flat, last = [], None
            for lon, lat in coords:
                pt = (round(lat, 1), round(lon, 1))
                if pt != last:
                    flat.extend(pt)
                    last = pt
            if len(flat) >= 8:   # skip specks
                lines.append(flat)
    json.dump({"lines": lines}, sys.stdout, separators=(",", ":"))


if __name__ == "__main__":
    main()
