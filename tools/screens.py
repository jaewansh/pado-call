"""Screenshots of the live demo (real map) for the plan deck."""
import asyncio
import os

from playwright.async_api import async_playwright

BASE = 'https://jaewansh.github.io/pado-call/'
OUT = 'shots'
os.makedirs(OUT, exist_ok=True)

SCENES = [
    # name, lang, day, time, hash
    ('airport_en', 'en', 'drone', '1930', '#/call'),
    ('ride_zh', 'zhHans', 'drone', '1930', '#/call?seg=ride&from=haeundae&to=gwangalli'),
    ('wave_ja', 'ja', 'drone', '1930', '#/wave'),
    ('airport_ko', 'ko', 'drone', '1930', '#/call'),
    ('ride_ko', 'ko', 'drone', '1930', '#/call?seg=ride&from=haeundae&to=gwangalli'),
    ('wave_ko', 'ko', 'drone', '1930', '#/wave'),
    ('ride_ko_cruise', 'ko', 'cruise', '1100', '#/call?seg=ride&from=ydcruise&to=gamcheon'),
    ('ride_en_cruise', 'en', 'cruise', '1100', '#/call?seg=ride&from=ydcruise&to=gamcheon'),
    ('wave_ko_cruise', 'ko', 'cruise', '1200', '#/wave?zone=B'),
    ('wave_zht_cruise', 'zhHant', 'cruise', '1200', '#/wave?zone=B'),
    ('airport_ja_dep', 'ja', 'weekend', '1500', '#/call?seg=dep'),
]


async def settle(pg):
    try:
        await pg.wait_for_selector('.rmap canvas, .map-note', timeout=20000)
    except Exception:
        pass
    try:
        await pg.wait_for_load_state('networkidle', timeout=20000)
    except Exception:
        pass
    await pg.wait_for_timeout(5000)  # tiles and label layout
    offline = await pg.locator('.map-note').count()
    return 'schematic' if offline else 'real'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, lang, day, t, h in SCENES:
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3)
            pg = await ctx.new_page()
            await pg.goto(f'{BASE}?lang={lang}&day={day}&t={t}&fresh=1{h}', wait_until='domcontentloaded')
            mode = await settle(pg)
            await pg.screenshot(path=f'{OUT}/{name}.png')
            await pg.screenshot(path=f'{OUT}/{name}_full.png', full_page=True)
            print(name, mode, flush=True)
            await ctx.close()
        # trips after an airport booking and a ride call (Korean)
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3)
        pg = await ctx.new_page()
        await pg.goto(f'{BASE}?lang=ko&day=drone&t=1930&fresh=1#/call', wait_until='domcontentloaded')
        await settle(pg)
        await pg.fill('#flight', 'OZ8961')
        await pg.click('text=공항 셔틀 예약')
        await pg.wait_for_timeout(400)
        await pg.click('nav.tabbar >> text=호출')
        await pg.click('text=지금 호출')
        await pg.select_option('#from', 'gwangalli')
        await pg.select_option('#to', 'centum')
        await pg.click('button:has-text("셔틀 부르기")')
        await pg.wait_for_timeout(600)
        await pg.evaluate('window.scrollTo(0,0)')
        await pg.wait_for_timeout(4000)
        await pg.screenshot(path=f'{OUT}/trips_ko.png')
        await pg.screenshot(path=f'{OUT}/trips_ko_full.png', full_page=True)
        print('trips_ko done', flush=True)
        await ctx.close()
        await b.close()


asyncio.run(main())
