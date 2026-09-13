#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drive the real app and check the README's harder-to-believe claims.

The README makes a number of promises that are easy to state and awkward to
prove — that the snapshot button really writes a JPEG, that a `tz` column really
shifts the displayed clock, that the share card really is 1080x1350, that lite
mode really stops drawing the expensive layers. This drives a headless browser
against a running copy of the app and checks each one against the DOM and the
JS model rather than trusting the wording.

    ./start_server.sh 8000 &
    python3 tests/verify_readme_claims.py http://127.0.0.1:8000/index.html

Needs playwright (`pip install playwright && playwright install chromium`); it
picks up a Chromium under ~/.cache/ms-playwright, or set CHROME_PATH.
Exits 0 only if every claim holds.
"""
import json
import os
import pathlib
import struct
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit('playwright is not installed: pip install playwright && playwright install chromium')

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000/index.html'
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
        '--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars']

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), str(detail)[:240]))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} :: {str(detail)[:220]}", flush=True)


def find_chrome():
    env = os.environ.get('CHROME_PATH')
    if env and os.path.exists(env):
        return env
    root = pathlib.Path.home() / '.cache' / 'ms-playwright'
    for p in sorted(root.glob('chromium-*/chrome-linux64/chrome'), reverse=True):
        return str(p)
    return None


def poll(pg, js, ms=25000):
    """Run `js` (a promise expression) and wait for it, without ever handing
    Playwright a promise that settles later — that pattern hangs the sync API."""
    pg.evaluate("(src)=>{window.__r=undefined;window.__e=null;(async()=>{try{"
                "window.__r=await eval(src);}catch(e){window.__e=String(e&&e.message||e);}})();}", js)
    for _ in range(ms // 100):
        pg.wait_for_timeout(100)
        if pg.evaluate("()=>window.__r!==undefined||window.__e!==null"):
            break
    return pg.evaluate("()=>window.__e?('ERR '+window.__e):window.__r")


def fresh(pg, url):
    """A clean slate: no stored log, no stored UI settings."""
    pg.goto(url, wait_until='load', timeout=90000)
    pg.wait_for_timeout(2500)
    pg.evaluate("()=>{localStorage.clear();}")
    pg.reload(wait_until='load')
    pg.wait_for_timeout(3000)


def sample(pg):
    pg.click("button:has-text('加载示例')")
    pg.wait_for_timeout(4000)


def import_csv(pg, filename, text):
    """Import through the app's own entry point, then wait for it to land."""
    before = pg.evaluate("()=>flights.length")
    poll(pg, "(async()=>{const f=new File([%s],%s,{type:'text/csv'});"
              "await importFlights(f);return true;})()" % (json.dumps(text), json.dumps(filename)))
    for _ in range(120):
        pg.wait_for_timeout(250)
        n = pg.evaluate("()=>flights.length")
        if n != before:
            return n - before
    return 0


def png_size(data):
    """Width/height straight out of the IHDR chunk, so we measure the bytes that
    were actually written rather than the canvas attributes we set."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    return struct.unpack('>II', data[16:24])


ISO_DATETIME = ('flight_id,origin,dest,time,tz\n'
                'MU5100,PVG,PEK,2025-01-04T09:10,Asia/Shanghai\n'
                'CA1501,PEK,CAN,2025-01-05T22:45,+08:00\n')
# 2025-01-04T09:10 in Asia/Shanghai is 01:10 UTC.
MS_0910_SHANGHAI = 1735953000000


def main():
    chrome = find_chrome()
    if not chrome:
        sys.exit('no Chromium found — set CHROME_PATH or run `playwright install chromium`')

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, args=ARGS)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900},
                                  permissions=['clipboard-read', 'clipboard-write'])
        pg = ctx.new_page()
        errors = []
        pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        pg.on('console', lambda m: errors.append(f'console.{m.type}: {m.text}') if m.type == 'error' else None)

        # ---------- 1. the snapshot buttons really write a JPEG ----------
        fresh(pg, URL)
        sample(pg)
        pg.evaluate("()=>world.pointOfView({lat:30,lng:104,altitude:1.55},0)")
        pg.wait_for_timeout(2600)
        for btn, stem in (('#btn-snap3d', 'Globe_3D_'), ('#btn-snap2d', 'Map_2D_')):
            try:
                with pg.expect_download(timeout=30000) as di:
                    pg.click(btn)
                dl = di.value
                raw = pathlib.Path(dl.path()).read_bytes()
                check(f'1. {btn} downloads a real JPEG',
                      dl.suggested_filename.startswith(stem) and dl.suggested_filename.endswith('.jpg')
                      and raw[:3] == b'\xff\xd8\xff' and raw[-2:] == b'\xff\xd9',
                      f'{dl.suggested_filename} {len(raw) // 1024} KB, magic {raw[:3].hex()}, {len(raw)} bytes')
            except Exception as e:                              # noqa: BLE001
                check(f'1. {btn} downloads a real JPEG', False, f'{type(e).__name__}: {e}')

        # ---------- 2. a `tz` column shifts the clock ----------
        fresh(pg, URL)
        added = import_csv(pg, 'tz.csv', ISO_DATETIME)
        pg.wait_for_timeout(1200)
        cards = pg.evaluate("""()=>Array.from(document.querySelectorAll('.flight-card')).map(c=>({
            id:c.querySelector('.fc-id').textContent,
            date:c.querySelector('.fc-date').textContent,
            time:(c.querySelector('.fc-row3').textContent.match(/\\u{1F6EB}\\s*([0-9:]+)/u)||[])[1]}))""")
        by_id = {c['id']: c for c in cards}
        want = {'MU5100': ['2025-01-04', '09:10'], 'CA1501': ['2025-01-05', '22:45']}
        got = {k: [by_id.get(k, {}).get('date'), by_id.get(k, {}).get('time')] for k in want}
        check('2. tz column ("Asia/Shanghai" and "+08:00") sets the local clock',
              added == 2 and got == want, f'rows added={added} expected={want} shown={got}')
        ts = pg.evaluate("()=>{const f=flights.find(x=>x.flight_id==='MU5100');return f?f.ts:null;}")
        check('2b. tz parses to the right UTC instant', ts == MS_0910_SHANGHAI,
              f'ts={ts} want={MS_0910_SHANGHAI} (2025-01-04T01:10Z)')

        # ---------- 3 + 4. theme and unit survive a reload ----------
        fresh(pg, URL)
        sample(pg)
        km_before = pg.evaluate("()=>document.getElementById('st-dist').textContent")
        pg.select_option('#themeSel', 'dark')
        pg.select_option('#unitSel', 'mi')
        pg.wait_for_timeout(2000)
        mi_before = pg.evaluate("()=>document.getElementById('st-dist').textContent")
        pg.reload(wait_until='load')
        pg.wait_for_timeout(4500)
        state = pg.evaluate("""()=>({theme:document.getElementById('themeSel').value,
            unit:document.getElementById('unitSel').value,
            label:document.getElementById('u-dist').textContent,
            dist:document.getElementById('st-dist').textContent})""")
        check('3. theme survives a reload',
              state['theme'] == 'dark' and pg.evaluate("()=>curTheme") == 'dark',
              f"themeSel={state['theme']} curTheme={pg.evaluate('()=>curTheme')}")
        check('4. km/mi survives a reload and still applies',
              state['unit'] == 'mi' and state['label'] == 'mi' and state['dist'] == mi_before
              and mi_before != km_before,
              f"unit={state['unit']} label={state['label']} dist {km_before} km -> {state['dist']} mi")

        # ---------- 5. the share card is really 1080x1350 ----------
        fresh(pg, URL)
        sample(pg)
        pg.click('#btn-share')
        pg.wait_for_timeout(2500)
        canvas = pg.evaluate("""()=>{const c=document.getElementById('share-canvas');
            let colours=-1;try{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
                const seen=new Set();for(let i=0;i<d.length;i+=4000){seen.add((d[i]<<16)|(d[i+1]<<8)|d[i+2]);}
                colours=seen.size;}catch(e){colours='ERR '+e.message;}
            return {w:c.width,h:c.height,modal:document.getElementById('share-modal').classList.contains('on'),
                    colours:colours};}""")
        check('5. the share card canvas is 1080x1350 and actually painted',
              canvas['modal'] and [canvas['w'], canvas['h']] == [1080, 1350]
              and isinstance(canvas['colours'], int) and canvas['colours'] > 20,
              json.dumps(canvas))
        try:
            with pg.expect_download(timeout=30000) as di:
                pg.click('#btn-share-save')
            raw = pathlib.Path(di.value.path()).read_bytes()
            check('5b. the saved share image is a 1080x1350 PNG',
                  png_size(raw) == (1080, 1350) and len(raw) > 20000,
                  f'{di.value.suggested_filename} IHDR={png_size(raw)} {len(raw) // 1024} KB')
        except Exception as e:                                  # noqa: BLE001
            check('5b. the saved share image is a 1080x1350 PNG', False, f'{type(e).__name__}: {e}')
        pg.click('#btn-share-close')

        # ---------- 6. a weight column counts as many flights ----------
        fresh(pg, URL)
        weighted = ('flight_id,origin,dest,time,weight\n'
                    'MU5601,PVG,SHE,2025-02-18T10:20:00Z,3\n'
                    'CA1806,PEK,CAN,2025-02-19T10:20:00Z,2\n')
        added = import_csv(pg, 'weighted.csv', weighted)
        pg.wait_for_timeout(1500)
        st = pg.evaluate("""()=>({count:document.getElementById('st-count').textContent,
            dur:document.getElementById('st-dur').textContent,
            arcs:rawArcs.map(a=>a._stroke)})""")
        seq = poll(pg, "(async()=>{startReplay();const n=replaySeq.length;stopReplay();return n;})()")
        check('6. weight drives the stats', added == 2 and st['count'] == '5',
              f"2 rows imported, st-count={st['count']} (weighted 5, not 2)")
        check('6b. weight drives the arc thickness',
              len(st['arcs']) == 2 and st['arcs'][0] > st['arcs'][1] > 0, f"strokes={st['arcs']}")
        check('6c. the replay walks rows, one leg per row (weight does not duplicate legs)',
              seq == 2, f'replaySeq={seq} for 2 rows / 5 weighted flights')
        try:
            with pg.expect_download(timeout=30000) as di:
                pg.click("button:has-text('导出 CSV')")
            csv = pathlib.Path(di.value.path()).read_text(encoding='utf-8')
            header = csv.splitlines()[0]
            check('6d. the CSV export carries the weight and the tz back out',
                  ',3,' in csv and ',2,' in csv and header.split(',')[-1] == 'tz'
                  and 'weight' in header, f'{len(csv.splitlines())} lines, header={header}')
        except Exception as e:                                  # noqa: BLE001
            check('6d. the CSV export carries the weight and the tz back out', False,
                  f'{type(e).__name__}: {e}')

        # ---------- 7. lite mode really stops drawing the heavy layers ----------
        # The country-border layer loads on a level-of-detail timer, and a single
        # programmatic camera move does not reliably wake it, so ask for it and
        # wait for it — otherwise "before" reads 0 and the comparison is vacuous.
        fresh(pg, URL)
        sample(pg)
        pg.evaluate("()=>world.pointOfView({lat:30,lng:104,altitude:1.2},0)")
        pg.evaluate("()=>{loadProvinces();}")
        for _ in range(80):
            pg.wait_for_timeout(250)
            if pg.evaluate("()=>isProvsOK"):
                break
        pg.evaluate("()=>upd()")
        pg.wait_for_timeout(2000)
        before = pg.evaluate("""()=>({glow:glowData.length,polys:(world.polygonsData()||[]).length,
            arcs:rawArcs.map(a=>[a._dashLen,a._dashGap,a._dashTime,a._stroke])})""")
        pg.click('#btn-lite')
        pg.wait_for_timeout(1800)
        pg.evaluate("()=>world.pointOfView({lat:30,lng:104,altitude:1.2},0)")
        pg.evaluate("()=>upd()")
        pg.wait_for_timeout(2500)
        arcs_after = pg.evaluate("()=>rawArcs.map(a=>[a._dashLen,a._dashGap,a._dashTime,a._stroke])")
        pg.evaluate("()=>{const f=flights[0];if(f)selectFlight(f.key);}")
        pg.wait_for_timeout(3000)
        after = pg.evaluate("""()=>({lite:liteMode,glow:glowData.length,
            polys:(world.polygonsData()||[]).length,plane:planeData.length})""")
        check('7. lite mode stops the glow layer',
              after['lite'] and after['glow'] == 0 and before['glow'] > 0,
              f"glowData {before['glow']} -> {after['glow']}")
        check('7b. lite mode stops the country borders',
              after['polys'] == 0 and before['polys'] > 0,
              f"polygon features {before['polys']} -> {after['polys']}")
        # Observed, not assumed: lite mode leaves the route layer alone.  The
        # README used to claim it hid "animated arcs"; it does not — the dash
        # parameters are identical either way, so the docs say what is true and
        # this check keeps them honest.
        check('7c. lite mode leaves the routes themselves untouched',
              arcs_after == before['arcs'] and len(before['arcs']) > 0,
              f'{len(before["arcs"])} arcs, styling unchanged: {arcs_after == before["arcs"]}')
        check('7d. lite mode stops the aircraft', after['plane'] == 0,
              f"planeData={after['plane']} after selecting a flight")

        # ---------- 8. drag & drop import ----------
        fresh(pg, URL)
        n0 = pg.evaluate("()=>flights.length")
        types = pg.evaluate("""()=>{
            const csv='flight_id,origin,dest,time\\nMU2101,PVG,SHE,2025-06-01T08:00:00Z\\nJQ7,SHE,CAN,2025-06-02T08:00:00Z\\n';
            const dt=new DataTransfer();
            dt.items.add(new File([csv],'dropped.csv',{type:'text/csv'}));
            document.dispatchEvent(new DragEvent('drop',{dataTransfer:dt,bubbles:true,cancelable:true}));
            return dt.types.join(',');}""")
        for _ in range(120):
            pg.wait_for_timeout(250)
            if pg.evaluate("()=>flights.length") > n0:
                break
        n1 = pg.evaluate("()=>flights.length")
        check('8. drag & drop imports without opening the file picker', n1 == n0 + 2,
              f'dataTransfer.types={types}, flights {n0} -> {n1}')

        # ---------- report ----------
        real = [e for e in errors if 'favicon' not in e]
        check('Z. no page or console errors', not real, f'{len(real)}: {real[:3]}')
        browser.close()

    bad = [r for r in results if not r[1]]
    print(f'\n{len(results) - len(bad)}/{len(results)} checks passed')
    if bad:
        print('FAILED:')
        for name, _, detail in bad:
            print(f'  - {name} :: {detail}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
