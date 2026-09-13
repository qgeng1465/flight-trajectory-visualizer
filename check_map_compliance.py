#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that countries.geojson shows Chinese territory correctly.

The globe draws `countries.geojson` as its country layer, so whatever that file
says *is* what the map says. This checks the specific points that matter:
places China claims must resolve to China, nowhere may they resolve to two
countries at once, and the South China Sea must carry the 十段线.

No third-party dependencies — plain point-in-polygon, so this runs anywhere
Python 3 does. Exits non-zero on failure.

    python3 check_map_compliance.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEOJSON = os.path.join(HERE, 'countries.geojson')

# (label, lon, lat, expected iso_a2 or None-for-dash-line)
PROBES = [
    ('藏南 / South Tibet (Tawang)',  91.87,  27.59, 'CN'),
    ('阿克赛钦 / Aksai Chin',        79.00,  35.00, 'CN'),
    ('海南 / Hainan',               109.85,  19.20, 'CN'),
    ('北京 / Beijing',              116.40,  39.90, 'CN'),
    ('台北 / Taipei',               121.56,  25.03, 'CN-TW'),
    ('钓鱼岛 / Diaoyu Islands',      123.48,  25.75, 'CN-TW'),
    ('香港 / Hong Kong',            114.17,  22.32, 'HK'),
    ('澳门 / Macao',                113.55,  22.20, 'MO'),
]
# Every feature with one of these codes is part of China and must be drawn with
# the same fill/stroke as the rest of China.
CHINA_ISO = {'CN', 'CN-TW', 'HK', 'MO'}
# The 2023 standard map carries the 十段线 — ten dashes, not nine.
MIN_DASHES = 10
# Islands that must sit inside the area the dashes enclose.
SOUTH_CHINA_SEA_ISLANDS = [
    ('永兴岛 / Woody Island (西沙)', 112.34, 16.83),
    ('太平岛 / Taiping Island (南沙)', 114.36, 10.37),
]
REQUIRED_NAMES = {
    'CN-TW': ('Taiwan, China', '中国台湾'),
    'HK': ('Hong Kong, China', '中国香港'),
    'MO': ('Macao, China', '中国澳门'),
}


def rings(geom):
    """Every ring of a Polygon / MultiPolygon, outer rings and holes alike."""
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon':
        return list(c)
    if t == 'MultiPolygon':
        return [r for poly in c for r in poly]
    return []


def contains(geom, lon, lat):
    """Even-odd point-in-polygon across every ring of the feature."""
    for ring in rings(geom):
        inside = False
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
            if (y1 > lat) != (y2 > lat):
                if lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
        if inside:
            return True
    return False


def main():
    if not os.path.exists(GEOJSON):
        print(f'FAIL: {GEOJSON} not found')
        return 1
    with open(GEOJSON, encoding='utf-8') as f:
        features = json.load(f)['features']

    fails = []

    by_iso = {}
    for ft in features:
        by_iso.setdefault(ft['properties'].get('iso_a2') or '', []).append(ft)

    # 1. the five China-side features must all be present
    for iso in sorted(CHINA_ISO):
        if iso not in by_iso:
            fails.append(f'no feature for {iso} — that territory would not render')
    if '' not in by_iso:
        fails.append('no 十段线 feature (empty iso_a2) — the South China Sea '
                     'would render without it')

    # 2. each claimed point resolves to exactly one country, and the right one
    for label, lon, lat, want in PROBES:
        hits = [(ft['properties'].get('iso_a2') or '', ft['properties'].get('name'))
                for ft in features if contains(ft['geometry'], lon, lat)]
        if not hits:
            fails.append(f'{label}: not covered by any feature (renders as blank sea)')
        elif len(hits) > 1:
            got = ', '.join(f'{n or "十段线"} [{i or "-"}]' for i, n in hits)
            fails.append(f'{label}: covered by {len(hits)} overlapping features '
                         f'({got}) — a foreign polygon still claims it')
        elif hits[0][0] != want:
            fails.append(f'{label}: resolves to {hits[0][0] or "十段线"} '
                         f'({hits[0][1]}), expected {want}')
        else:
            print(f'  ok  {label:34s} -> {hits[0][1]}')

    # 3. the dash line itself
    dashes = [ft for ft in by_iso.get('', [])]
    n_parts = sum(len(rings(ft['geometry'])) for ft in dashes)
    if dashes:
        if n_parts < MIN_DASHES:
            fails.append(f'十段线 has {n_parts} dash(es), expected at least '
                         f'{MIN_DASHES} — is this the 2023 standard map?')
        else:
            print(f'  ok  {"十段线 (South China Sea)":34s} -> {n_parts} dashes')
        # it must be un-highlightable: an empty iso can never match an airport
        for ft in dashes:
            if (ft['properties'].get('iso_a2') or '') != '':
                fails.append('十段线 feature carries an iso code — it would '
                             'light up when that country is visited')
        # and it must actually span the South China Sea
        pts = [p for ft in dashes for p in _all_pts(ft['geometry'])]
        if pts:
            lons = [p[0] for p in pts]
            lats = [p[1] for p in pts]
            print(f'      spans lon {min(lons):.1f}..{max(lons):.1f}  '
                  f'lat {min(lats):.1f}..{max(lats):.1f}')
            for label, lon, lat in SOUTH_CHINA_SEA_ISLANDS:
                if not (min(lons) <= lon <= max(lons) and min(lats) <= lat <= max(lats)):
                    fails.append(f'{label} falls outside the 十段线 area')
                else:
                    print(f'  ok  {label:34s} -> inside the dash-line area')

    # 4. names
    for iso, (name, name_zh) in REQUIRED_NAMES.items():
        got = [ft['properties'] for ft in by_iso.get(iso, [])]
        if got and (got[0].get('name'), got[0].get('name_zh')) != (name, name_zh):
            fails.append(f'{iso} is labelled {got[0].get("name")!r} / '
                         f'{got[0].get("name_zh")!r}, expected {name!r} / {name_zh!r}')

    # 5. every China-side feature must be valid geometry (shapely, if present)
    try:
        from shapely.geometry import shape
        for iso in sorted(CHINA_ISO | {''}):
            for ft in by_iso.get(iso, []):
                g = shape(ft['geometry'])
                label = iso or '十段线'
                if not g.is_valid:
                    fails.append(f'{label} geometry is invalid — a renderer may '
                                 f'drop or double-draw it')
                else:
                    print(f'  ok  {label:6s} geometry valid')
    except ImportError:
        print('  --  shapely not installed; skipped the geometry-validity check')

    print()
    if fails:
        print(f'FAIL: {len(fails)} problem(s)')
        for f in fails:
            print(f'  - {f}')
        return 1
    print('PASS: Chinese territory renders correctly and unambiguously')
    return 0


def _all_pts(geom):
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon':
        return [p for ring in c for p in ring]
    if t == 'MultiPolygon':
        return [p for poly in c for ring in poly for p in ring]
    return []


if __name__ == '__main__':
    sys.exit(main())
