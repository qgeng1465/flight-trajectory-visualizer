#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild airports.csv (airport + city + country) and countries.geojson.

Sources — download once, keep them next to this script or in /tmp:

  * OurAirports airports.csv  (authoritative IATA codes, coordinates, `municipality`
    = the city, and `iso_country` = a *correct* ISO 3166-1 alpha-2 code)
  * OurAirports countries.csv (ISO code -> English country name)
  * Natural Earth 110m admin_0 countries  -> display geometry (small, bundled)
  * Natural Earth 10m  admin_0 countries  -> geometry fallback for small islands

    curl -o ourairports.csv           https://davidmegginson.github.io/ourairports-data/airports.csv
    curl -o ourairports_countries.csv https://davidmegginson.github.io/ourairports-data/countries.csv

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
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OURAIRPORTS = os.environ.get('OURAIRPORTS_CSV', '/tmp/ourairports.csv')
OURAIRPORTS_COUNTRIES = os.environ.get('OURAIRPORTS_COUNTRIES_CSV', '/tmp/ourairports_countries.csv')
NE110M = os.environ.get('NE110M', '/tmp/ne110m.geojson')
NE10M = os.environ.get('NE10M', '/tmp/ne10m.geojson')
OUT_CSV = os.path.join(HERE, 'airports.csv')
OUT_GEOJSON = os.path.join(HERE, 'countries.geojson')

# Politically correct labels. 香港 / 澳门 / 台湾 are always shown as part of China.
POLITICAL = {
    'HK': ['Hong Kong, China', '中国香港'],
    'MO': ['Macao, China', '中国澳门'],
    'CN-TW': ['Taiwan, China', '中国台湾'],
}
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

    def rnd(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], 3), round(c[1], 3)]
        return [rnd(x) for x in c]

    ten_m = {}
    for ft in ne10['features']:
        iso = ne_iso(ft['properties'])
        if iso:
            ten_m.setdefault(iso, ft['geometry'])

    out_features, used_ids = [], set()
    for i, ft in enumerate(ne110['features']):
        iso = ne_iso(ft['properties'])
        if iso not in used_iso or iso in used_ids:
            continue          # Kosovo appears 5x in the 110m set — keep one
        used_ids.add(iso)
        nm = country_names(iso)
        out_features.append({
            'type': 'Feature',
            'properties': {'id': i, 'name': nm[0], 'name_zh': nm[1], 'iso_a2': iso},
            'geometry': ft['geometry'],
        })
    # Small places with no 110m polygon (Singapore, Hong Kong, …) come from 10m.
    for iso in sorted(used_iso - used_ids):
        if iso not in ten_m:
            continue
        g = dict(ten_m[iso])
        g['coordinates'] = rnd(g['coordinates'])
        nm = country_names(iso)
        out_features.append({
            'type': 'Feature',
            'properties': {'id': 9000 + len(out_features), 'name': nm[0],
                           'name_zh': nm[1], 'iso_a2': iso},
            'geometry': g,
        })

    with open(OUT_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'features': out_features}, f,
                  ensure_ascii=False, separators=(',', ':'))

    missing = sorted(used_iso - {x['properties']['iso_a2'] for x in out_features})
    print(f'airports: {len(rows)}  (unknown iso: {len(unknown)} {unknown[:10]})')
    print(f'geojson : {len(out_features)} features for {len(used_iso)} iso codes')
    print(f'cities  : {sum(1 for r in rows if r["city"])}/{len(rows)} have a city name')
    if missing:
        print(f'no polygon (will never highlight): {missing[:20]}')
    for probe in ('FR', 'NO', 'XK', 'CN-TW', 'HK', 'MO', 'SG'):
        n = sum(1 for r in rows if r['iso'] == probe)
        has = any(x['properties']['iso_a2'] == probe for x in out_features)
        print(f'  {probe:6s} airports={n:4d} polygon={"yes" if has else "NO"}')


if __name__ == '__main__':
    main()
