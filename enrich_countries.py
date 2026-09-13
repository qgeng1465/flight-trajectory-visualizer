#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild airports.csv (airport + city + country) and countries.geojson.

Sources — download once, keep them next to this script or in /tmp:

  * OurAirports airports.csv  (authoritative IATA codes, coordinates, `municipality`
    = the city, and `iso_country` = a *correct* ISO 3166-1 alpha-2 code)
  * OurAirports countries.csv (ISO code -> English country name)
  * Natural Earth 110m admin_0 countries  -> display geometry (small, bundled)
  * Natural Earth 10m  admin_0 countries  -> geometry fallback for small islands
  * Aliyun DataV GeoAtlas 100000_full.json -> China display geometry (see below)

    curl -o ourairports.csv           https://davidmegginson.github.io/ourairports-data/airports.csv
    curl -o ourairports_countries.csv https://davidmegginson.github.io/ourairports-data/countries.csv
    curl -o datav_cn_full.json        https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json

Outputs:
  * airports.csv       iata_code,name,latitude_deg,longitude_deg,type,country,country_zh,iso,city,city_alt
  * countries.geojson  one feature per place that has a civil airport, props {id,name,name_zh,iso_a2}

Why ISO_A2_EH and not ISO_A2
-----------------------------
Natural Earth stores ISO_A2='-99' for France, Norway and Kosovo — the real codes
live in ISO_A2_EH (FR / NO / XK). Reading ISO_A2 (as this script used to) tagged
all 112 French and 41 Norwegian airports as '-99', which collapsed them — together
with every other '-99' place — into one fake country *and* made the globe
highlight Kosovo (the only ISO_A2='-99' polygon in the 110m set, and it appears
there five times) every time you flew to Paris. Everything is now keyed off
ISO_A2_EH, with OurAirports' iso_country as the airport-side authority.

Why China's geometry does not come from Natural Earth
-----------------------------------------------------
Natural Earth draws de-facto boundaries, which do not match the map China
publishes, and the differences are the ones reviewers look for:

  * 藏南 / South Tibet (Tawang, 27.59N 91.87E) falls inside Natural Earth's
    *Bhutan* polygon — it belongs to neither China nor India there.
  * The 南海诸岛 and the 九段线 / 十段线 are absent from the 110m set entirely.
  * 钓鱼岛 has no polygon at all.
  * Taiwan is a stand-alone country polygon, disjoint from the mainland.

China's own geometry therefore comes from Aliyun's DataV GeoAtlas
`100000_full.json`, which follows the 2023 standard map: 34 province-level
units (台湾省 / 香港特别行政区 / 澳门特别行政区 included) plus the 十段线
carried as its own feature, adcode `100000_JD`. Everything else still comes
from Natural Earth. 藏南 resolves to 西藏自治区 and 钓鱼岛 to 台湾省 there.

The four China-side features keep distinct `iso_a2` codes (CN / CN-TW / HK /
MO) so the app's per-airport highlighting still works: flying to Taipei lights
台湾省, not the whole mainland. They are drawn with the same fill and stroke as
every other country, so they read as one landmass. The 十段线 feature is given
an empty `iso_a2` so it can never be highlighted.

shapely is used to dissolve the province polygons into one outline per group.
It is optional: without it the provinces are emitted as separate rings, which
is just as correct, only larger and with the internal provincial borders drawn.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OURAIRPORTS = os.environ.get('OURAIRPORTS_CSV', '/tmp/ourairports.csv')
OURAIRPORTS_COUNTRIES = os.environ.get('OURAIRPORTS_COUNTRIES_CSV', '/tmp/ourairports_countries.csv')
NE110M = os.environ.get('NE110M', '/tmp/ne110m.geojson')
NE10M = os.environ.get('NE10M', '/tmp/ne10m.geojson')
DATAV_CN = os.environ.get('DATAV_CN', '/tmp/datav_cn_full.json')
OUT_CSV = os.path.join(HERE, 'airports.csv')
OUT_GEOJSON = os.path.join(HERE, 'countries.geojson')

# Politically correct labels. 香港 / 澳门 / 台湾 are always shown as part of China.
POLITICAL = {
    'CN': ['China', '中华人民共和国'],
    'HK': ['Hong Kong, China', '中国香港'],
    'MO': ['Macao, China', '中国澳门'],
    'CN-TW': ['Taiwan, China', '中国台湾'],
}
# China-side units whose display geometry comes from DataV, not Natural Earth.
# Keyed by DataV adcode; every other adcode in the file is mainland (CN).
CHINA_ISO = ('CN', 'HK', 'MO', 'CN-TW')
DATAV_GROUP = {'710000': 'CN-TW', '810000': 'HK', '820000': 'MO'}
DATAV_DASH_ADCODE = '100000_JD'
DASH_LINE_NAME = ('South China Sea Islands', '南海诸岛')
# OurAirports / Natural Earth give Taiwan as TW; we key it as CN-TW throughout.
ISO_ALIAS = {'TW': 'CN-TW'}
# Natural Earth folds these into their parent country (France, Netherlands,
# Australia), so they have no polygon of their own and no Chinese name. Without
# this they would render as a bare ISO code in the country list.
TERRITORY_ZH = {
    'GF': '法属圭亚那', 'RE': '留尼汪', 'GP': '瓜德罗普', 'MQ': '马提尼克',
    'YT': '马约特', 'BQ': '荷兰加勒比区', 'CC': '科科斯群岛', 'CX': '圣诞岛',
}
# Places that are not countries but do have civil airports; kept, but they should
# never be counted as a "country" the user visited. (Handled app-side by name.)
KEEP_TYPES = ('large_airport', 'medium_airport')
# Small airfields are only worth shipping when they have commercial passenger
# service — otherwise a real flight into a regional airport silently fails to
# import ("no valid flights"). Adds ~760 rows, no airfields.


def norm_iso(code):
    code = (code or '').strip().upper()
    if code in ('', '-99'):
        return ''
    return ISO_ALIAS.get(code, code)


def ne_iso(props):
    """Natural Earth ISO code, preferring the 'EH' column that actually holds
    France / Norway / Kosovo (ISO_A2 is '-99' for those)."""
    return norm_iso(props.get('ISO_A2_EH')) or norm_iso(props.get('ISO_A2'))


def clean_city(muni):
    """'Paris (Roissy-en-France, Val-d'Oise)' -> 'Paris'; keeps the tail separately."""
    s = (muni or '').strip()
    if not s:
        return '', ''
    head = s.split('(')[0].strip().rstrip(',').strip()
    return (head or s), (s if s != (head or s) else '')


def load_airports():
    if not os.path.exists(OURAIRPORTS):
        raise SystemExit(f'need OurAirports data at {OURAIRPORTS} (see docstring)')
    out, seen = [], set()
    with open(OURAIRPORTS, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['type'] not in KEEP_TYPES and not (
                    r['type'] == 'small_airport' and r['scheduled_service'] == 'yes'):
                continue
            iata = (r['iata_code'] or '').strip().upper()
            if len(iata) != 3 or iata in seen:
                continue
            if not r['latitude_deg'] or not r['longitude_deg']:
                continue
            seen.add(iata)
            out.append(r)
    return out


def load_ne(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def rnd(c):
    """Round every coordinate pair to 3 decimals — display precision only."""
    if isinstance(c[0], (int, float)):
        return [round(c[0], 3), round(c[1], 3)]
    return [rnd(x) for x in c]


def norm_geom(geom):
    """Any polygonal GeoJSON geometry -> MultiPolygon, coordinates rounded."""
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon':
        polys = [c]
    elif t == 'MultiPolygon':
        polys = c
    else:
        raise ValueError(f'not a polygonal geometry: {t}')
    return {'type': 'MultiPolygon',
            'coordinates': [[rnd(ring) for ring in poly] for poly in polys]}


def valid_rounded(geom):
    """Rounded MultiPolygon, repaired if rounding broke it.

    Rounding a province union to 3 decimals can collapse a tiny island ring to
    fewer than 4 points, which GEOS reports as invalid ("Too few points in
    geometry component"). The repair is lossless — China's area comes out
    identical to 4 dp — and it matters because an invalid ring in the South
    China Sea is exactly where a renderer might drop or double-draw something.
    """
    from shapely.geometry import shape
    from shapely.ops import unary_union
    from shapely.validation import make_valid

    rounded = norm_geom(_mapping(geom))
    if shape(rounded).is_valid:
        return rounded
    fixed = make_valid(shape(rounded))
    if fixed.geom_type == 'GeometryCollection':
        fixed = unary_union([p for p in fixed.geoms
                             if p.geom_type in ('Polygon', 'MultiPolygon')])
    rounded = norm_geom(_mapping(fixed))
    if shape(rounded).is_valid:
        return rounded
    repaired = shape(rounded).buffer(0)
    if repaired.geom_type == 'GeometryCollection':
        repaired = unary_union([p for p in repaired.geoms
                                if p.geom_type in ('Polygon', 'MultiPolygon')])
    return norm_geom(_mapping(repaired))


def _mapping(geom):
    from shapely.geometry import mapping
    return mapping(geom)


def build_china_features(path):
    """Display geometry for the four China-side units, from DataV GeoAtlas.

    Returns (features, body) where `body` is the shapely union of the four
    units — main() erases it from every other country, so no foreign polygon
    (Natural Earth draws 藏南 inside Bhutan) can overlap Chinese territory.

    shapely is required. Without it the provinces could still be emitted, but
    the erase could not be done, and a silently-overlapping 藏南 is exactly the
    defect this whole function exists to remove.
    """
    try:
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union
    except ImportError:
        raise SystemExit('shapely is required to build the China geometry '
                         '(pip install shapely) — see the module docstring')
    if not os.path.exists(path):
        raise SystemExit(f'need DataV China geometry at {path} (see docstring)')
    with open(path, encoding='utf-8') as f:
        src = json.load(f)

    groups, dash_feats = {}, []
    for ft in src['features']:
        ad = str(ft['properties'].get('adcode') or '')
        if ad == DATAV_DASH_ADCODE:
            dash_feats.append(ft)
        else:
            groups.setdefault(DATAV_GROUP.get(ad, 'CN'), []).append(ft)

    def repaired(f):
        """DataV's province rings share edges that are not perfectly noded, so
        GEOS rejects the raw union. buffer(0) drops the slivers and makes each
        polygon valid; it is the standard repair and leaves the outline alone."""
        return shape(f['geometry']).buffer(0)

    def polygonal(geom):
        """Drop non-areal parts a boolean op may leave behind, then union."""
        if geom.geom_type == 'GeometryCollection':
            geom = unary_union([g for g in geom.geoms
                                if g.geom_type in ('Polygon', 'MultiPolygon')])
        return geom

    out, body = [], []
    for iso in CHINA_ISO:
        feats = groups.get(iso)
        if not feats:
            raise SystemExit(f'DataV data has no polygon for {iso}')
        merged = polygonal(unary_union([repaired(f) for f in feats]))
        body.append(merged)
        name, name_zh = POLITICAL[iso]
        out.append({'properties': {'name': name, 'name_zh': name_zh,
                                   'iso_a2': iso},
                    'geometry': valid_rounded(merged)})

    # 十段线 / 九段线. The dashes are thin slivers; drawn like any other polygon
    # they render as the standard dash marks. Empty iso_a2 => never highlights.
    if dash_feats:
        polys = []
        for f in dash_feats:
            polys += norm_geom(f['geometry'])['coordinates']
        name, name_zh = DASH_LINE_NAME
        out.append({'properties': {'name': name, 'name_zh': name_zh,
                                   'iso_a2': ''},
                    'geometry': {'type': 'MultiPolygon', 'coordinates': polys}})

    # The erase mask must be the *rounded* outline that actually gets rendered,
    # not the full-precision one it was derived from. Erasing against the
    # unrounded shape and then rounding leaves China bulging up to half a
    # rounding step (≈55 m) back over its neighbours.
    rounded_body = polygonal(unary_union([shape(f['geometry']) for f in out
                                          if f['properties']['iso_a2']]))
    return out, rounded_body


def load_country_names():
    """iso -> English name, from OurAirports' own country table (covers the
    territories Natural Earth folds into a parent country)."""
    if not os.path.exists(OURAIRPORTS_COUNTRIES):
        return {}
    with open(OURAIRPORTS_COUNTRIES, encoding='utf-8') as f:
        return {r['code'].strip().upper(): r['name'].strip() for r in csv.DictReader(f)}


def main():
    airports = load_airports()
    ne110 = load_ne(NE110M)
    ne10 = load_ne(NE10M)

    # iso -> [name, name_zh] from the precise display set, filled with 10m gaps.
    name_by_iso = {}
    for src in (ne10, ne110):
        for ft in src['features']:
            p = ft['properties']
            iso = ne_iso(p)
            if iso and iso not in name_by_iso:
                name_by_iso[iso] = [
                    p.get('NAME') or p.get('NAME_EN') or p.get('SOVEREIGNT') or '',
                    p.get('NAME_ZH') or '',
                ]

    fallback_names = load_country_names()

    def country_names(iso):
        if iso in POLITICAL:
            return POLITICAL[iso]
        if iso in name_by_iso:
            return name_by_iso[iso]
        # No Natural Earth polygon of its own — use OurAirports' name + our zh table.
        return [fallback_names.get(iso, iso), TERRITORY_ZH.get(iso, '')]

    rows, unknown = [], []
    for r in airports:
        iso = norm_iso(r['iso_country'])
        if not iso:
            unknown.append(r['iata_code'])
        city, city_alt = clean_city(r['municipality'])
        country, country_zh = country_names(iso)
        rows.append({
            'iata_code': r['iata_code'].strip().upper(),
            'name': r['name'].strip(),
            'latitude_deg': r['latitude_deg'].strip(),
            'longitude_deg': r['longitude_deg'].strip(),
            'type': r['type'],
            'country': country,
            'country_zh': country_zh,
            'iso': iso,
            'city': city,
            'city_alt': city_alt,
            # OurAirports' own search keywords: local-language names, city codes
            # people actually type ("TYO", "München", "東京"), former names.
            'kw': (r.get('keywords') or '').strip(),
        })

    header = ['iata_code', 'name', 'latitude_deg', 'longitude_deg', 'type',
              'country', 'country_zh', 'iso', 'city', 'city_alt', 'kw']
    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)

    # ---- countries.geojson: only places that actually have a civil airport ----
    used_iso = {r['iso'] for r in rows if r['iso']}

    ten_m = {}
    for ft in ne10['features']:
        iso = ne_iso(ft['properties'])
        if iso:
            ten_m.setdefault(iso, ft['geometry'])

    out_features, used_ids = [], set()
    # China-side units first, from DataV (see the module docstring for why).
    # Their iso codes go into used_ids so the Natural Earth pass skips them.
    china_features, china_body = build_china_features(DATAV_CN)

    def without_china(geom):
        """Erase Chinese territory from a foreign polygon.

        Covering 藏南 with our own China polygon is not enough: Natural Earth
        still puts 藏南 inside Bhutan *and* inside India, so the same ground
        renders twice and the foreign colour wins where it overlaps. Every
        other country is therefore clipped against China's outline. Disjoint
        polygons are returned unchanged.

        The result is NOT rounded. Rounding a clipped neighbour shifts its
        whole border by up to half a rounding step, which is enough to open a
        sliver against that neighbour's *other* neighbours — it turned a
        Russia/Finland and a Thailand/Laos gap into overlaps. Untouched
        countries keep the precision they came with; only China's own outline
        is rounded, and the mask below is built from that rounded outline.
        """
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union
        g = shape(geom)
        if not g.intersects(china_body):
            return geom
        cut = g.difference(china_body)
        if cut.is_empty:
            return None
        if cut.geom_type == 'GeometryCollection':
            cut = unary_union([p for p in cut.geoms
                               if p.geom_type in ('Polygon', 'MultiPolygon')])
            if cut.is_empty:
                return None
        if cut.geom_type not in ('Polygon', 'MultiPolygon'):
            return None
        return mapping(cut)

    for ft in china_features:
        iso = ft['properties']['iso_a2']
        if iso:
            used_ids.add(iso)
        ft['properties']['id'] = 8000 + len(out_features)
        out_features.append({'type': 'Feature', 'properties': ft['properties'],
                             'geometry': ft['geometry']})

    clipped = 0
    for i, ft in enumerate(ne110['features']):
        iso = ne_iso(ft['properties'])
        if iso not in used_iso or iso in used_ids:
            continue          # Kosovo appears 5x in the 110m set — keep one
        used_ids.add(iso)
        nm = country_names(iso)
        geom = without_china(ft['geometry'])
        if geom is None:
            continue
        if geom is not ft['geometry']:
            clipped += 1
        out_features.append({
            'type': 'Feature',
            'properties': {'id': i, 'name': nm[0], 'name_zh': nm[1], 'iso_a2': iso},
            'geometry': geom,
        })
    # Small places with no 110m polygon (Singapore, Macao, …) come from 10m.
    for iso in sorted(used_iso - used_ids):
        if iso not in ten_m:
            continue
        geom = without_china(ten_m[iso])
        if geom is None:
            continue
        nm = country_names(iso)
        out_features.append({
            'type': 'Feature',
            'properties': {'id': 9000 + len(out_features), 'name': nm[0],
                           'name_zh': nm[1], 'iso_a2': iso},
            'geometry': geom,
        })

    with open(OUT_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'features': out_features}, f,
                  ensure_ascii=False, separators=(',', ':'))

    missing = sorted(used_iso - {x['properties']['iso_a2'] for x in out_features})
    print(f'airports: {len(rows)}  (unknown iso: {len(unknown)} {unknown[:10]})')
    print(f'geojson : {len(out_features)} features for {len(used_iso)} iso codes')
    print(f'cities  : {sum(1 for r in rows if r["city"])}/{len(rows)} have a city name')
    print(f'china   : {len(china_features)} DataV features '
          f'-> {", ".join(f["properties"]["iso_a2"] or "十段线" for f in china_features)}'
          f'  ({clipped} foreign polygon(s) clipped against China)')
    if missing:
        print(f'no polygon (will never highlight): {missing[:20]}')
    for probe in ('FR', 'NO', 'XK', 'CN-TW', 'HK', 'MO', 'SG'):
        n = sum(1 for r in rows if r['iso'] == probe)
        has = any(x['properties']['iso_a2'] == probe for x in out_features)
        print(f'  {probe:6s} airports={n:4d} polygon={"yes" if has else "NO"}')


if __name__ == '__main__':
    main()
