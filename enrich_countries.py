#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich airports.csv with country fields + rebuild countries.geojson with names.

- Reads Natural Earth 110m admin_0 countries (with NAME / NAME_ZH / ISO_A2).
- Point-in-polygon assigns each airport to a country (bbox-culled ray casting).
- Writes airports.csv with extra columns: country, country_zh, iso.
- Writes countries.geojson with stripped props {id, name, name_zh, iso_a2}
  and coordinates rounded to 3 decimals (keeps the file ~half its former size).
"""
import csv
import json

NE = '/tmp/ne110m.geojson'   # bundled for rendering (small)
NE10 = '/tmp/ne10m.geojson'  # build-time only, precise point-in-polygon (includes islands/coasts)
AIRPORTS = 'airports.csv'
OUT_CSV = 'airports.csv'
OUT_GEOJSON = 'countries.geojson'

# Politically correct labels (applied to airports.csv, country meta and geojson props).
# 香港 / 澳门 / 台湾 must always be shown as part of China.
POLITICAL = {
    'HK': ['Hong Kong, China', '中国香港'],
    'MO': ['Macao, China', '中国澳门'],
    'CN-TW': ['Taiwan, China', '中国台湾'],
}

with open(NE) as f:
    ne = json.load(f)
with open(NE10) as f:
    ne10 = json.load(f)

# --- mapping source: 10m (precise) ---
features = []
for i, ft in enumerate(ne10['features']):
    p = ft['properties']
    features.append({
        'name': p.get('NAME') or p.get('NAME_EN') or p.get('SOVEREIGNT') or '',
        'name_zh': p.get('NAME_ZH') or '',
        'iso': (p.get('ISO_A2') or '').strip() or '',
        'geom': ft['geometry'],
    })

# --- display source: 110m (small, bundled) ---
display_meta = {}
for i, ft in enumerate(ne['features']):
    p = ft['properties']
    iso = (p.get('ISO_A2') or '').strip()
    display_meta[iso] = {
        'name': p.get('NAME') or p.get('NAME_EN') or p.get('SOVEREIGNT') or '',
        'name_zh': p.get('NAME_ZH') or '',
    }

# Precompute bboxes
bboxes = []
for f in features:
    minx = miny = float('inf')
    maxx = maxy = float('-inf')
    geom = f['geom']
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    for poly in polys:
        for ring in poly:
            for x, y in ring:
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
    bboxes.append((minx, miny, maxx, maxy))


def point_in_rings(x, y, polys):
    inside = False
    for poly in polys:
        for ring in poly:
            j = len(ring) - 1
            for i in range(len(ring)):
                xi, yi = ring[i]
                xj, yj = ring[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
    return inside


def locate(lon, lat):
    for i, (minx, miny, maxx, maxy) in enumerate(bboxes):
        if lat < miny or lat > maxy or lon < minx or lon > maxx:
            continue
        f = features[i]
        geom = f['geom']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        if point_in_rings(lon, lat, polys):
            return i
    return None


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def _dist_to_feature(lon, lat, f):
    geom = f['geom']
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    best = float('inf')
    for poly in polys:
        for ring in poly:
            j = len(ring) - 1
            for i in range(len(ring)):
                ax, ay = ring[i]
                bx, by = ring[j]
                d = _seg_dist(lon, lat, ax, ay, bx, by)
                if d < best:
                    best = d
                j = i
    return best


NEAREST_KM = 100  # nearest-polygon fallback threshold for coastal / island airports


def locate_nearest(lon, lat):
    best = None
    best_d = NEAREST_KM / 111.0  # approximate degrees
    for i, (minx, miny, maxx, maxy) in enumerate(bboxes):
        # cheap bbox rejection with padding
        pad = best_d
        if lat < miny - pad or lat > maxy + pad or lon < minx - pad or lon > maxx + pad:
            continue
        d = _dist_to_feature(lon, lat, features[i])
        if d < best_d:
            best_d = d
            best = i
    return best


def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 3), round(c[1], 3)]
    return [rnd(x) for x in c]


def main():
    rows = list(csv.DictReader(open(AIRPORTS, encoding='utf-8')))
    matched = 0
    unmatched = []
    for r in rows:
        try:
            lon, lat = float(r['longitude_deg']), float(r['latitude_deg'])
        except (TypeError, ValueError):
            r['country'] = r['country_zh'] = r['iso'] = ''
            unmatched.append((r.get('iata_code'), 'no coords'))
            continue
        idx = locate(lon, lat) if locate(lon, lat) is not None else locate_nearest(lon, lat)
        if idx is None:
            r['country'] = r['country_zh'] = r['iso'] = ''
            unmatched.append((r.get('iata_code'), r.get('name')))
        else:
            f = features[idx]
            iso = f['iso'] or f['name'] or str(idx)
            if iso in POLITICAL:
                r['country'], r['country_zh'] = POLITICAL[iso]
            else:
                r['country'], r['country_zh'] = f['name'], f['name_zh']
            r['iso'] = iso
            matched += 1

    header = ['iata_code', 'name', 'latitude_deg', 'longitude_deg', 'type', 'country', 'country_zh', 'iso']
    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)

    # Only keep display features for places that actually have (civil) airports in
    # airports.csv — no civilian airport => not shown on the globe / not a "country".
    used_iso = {r['iso'] for r in rows if r.get('iso')}

    # Build an iso -> (name, name_zh) lookup from the 110m display set, then fill any
    # gaps from the precise 10m set. (Do NOT capture the loop variable `ft` in a
    # closure — it ends up pointing at the last feature.)
    name_by_iso = {}
    for _ft in ne['features']:
        _p = _ft['properties']
        _iso = (_p.get('ISO_A2') or '').strip()
        if _iso:
            name_by_iso[_iso] = [
                _p.get('NAME') or _p.get('NAME_EN') or _p.get('SOVEREIGNT') or '',
                _p.get('NAME_ZH') or '',
            ]
    for _ft in ne10['features']:
        _p = _ft['properties']
        _iso = (_p.get('ISO_A2') or '').strip()
        if _iso and _iso not in name_by_iso:
            name_by_iso[_iso] = [
                _p.get('NAME') or _p.get('NAME_EN') or _p.get('SOVEREIGNT') or '',
                _p.get('NAME_ZH') or '',
            ]

    def _names(iso_a2):
        if iso_a2 in POLITICAL:
            return POLITICAL[iso_a2]
        return name_by_iso.get(iso_a2, [iso_a2, ''])

    # Some airport-bearing places (e.g. Hong Kong / Macau / Taiwan, and small
    # islands like Singapore that are too small for the 110m set) are missing from
    # the 110m display set as separate polygons — pull them from the precise 10m set.
    ten_m = {}
    for ft in ne10['features']:
        p = ft['properties']
        iso = (p.get('ISO_A2') or '').strip()
        if iso:
            ten_m.setdefault(iso, ft['geometry'])

    out_features = []
    used_ids = set()
    for i, ft in enumerate(ne['features']):
        iso_a2 = (ft['properties'].get('ISO_A2') or '').strip()
        if iso_a2 not in used_iso:
            continue
        nm = _names(iso_a2)
        used_ids.add(iso_a2)
        out_features.append({
            'type': 'Feature',
            'properties': {'id': i, 'name': nm[0], 'name_zh': nm[1], 'iso_a2': iso_a2},
            'geometry': ft['geometry'],
        })
    for iso_a2 in sorted(used_iso - used_ids):
        if iso_a2 in ten_m:
            nm = _names(iso_a2)
            _g = dict(ten_m[iso_a2])
            _g['coordinates'] = rnd(_g['coordinates'])
            out_features.append({
                'type': 'Feature',
                'properties': {'id': 9000 + len(out_features), 'name': nm[0], 'name_zh': nm[1], 'iso_a2': iso_a2},
                'geometry': _g,
            })
    out = {'type': 'FeatureCollection', 'features': out_features}
    print(f'display geojson keeps {len(out_features)}/{len(ne["features"])} features (only places with airports)')
    with open(OUT_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

    print(f'total={len(rows)} matched={matched} unmatched={len(unmatched)}')
    for code, name in unmatched[:30]:
        print('  unmatched:', code, '|', name)


if __name__ == '__main__':
    main()
