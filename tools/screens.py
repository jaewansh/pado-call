"""Screenshots of the live demo (real map) for the plan deck — demo banner hidden, chosen scroll positions."""
import asyncio
import os

from playwright.async_api import async_playwright

BASE = 'https://jaewansh.github.io/pado-call/'
OUT = 'shots2'
os.makedirs(OUT, exist_ok=True)
HIDE = 'aside.demo { display: none !important; }'

PHONE = [
    # name, lang, day, time, hash, scrollY
    ('airport_en', 'en', 'drone', '1930', '#/call', 0),
    ('airport_en_card', 'en', 'drone', '1930', '#/call', 384),
    ('ride_zh', 'zhHans', 'drone', '1930', '#/call?seg=ride&from=haeundae&to=gwangalli', 0),
    ('ride_zh_gauge', 'zhHans', 'drone', '1930', '#/call?seg=ride&from=haeundae&to=gwangalli', 60),
    ('wave_ja', 'ja', 'drone', '1930', '#/wave', 0),
    ('ride_ko_cruise', 'ko', 'cruise', '1100', '#/call?seg=ride&from=ydcruise&to=gamcheon', 0),
    ('wave_ko_cruise', 'ko', 'cruise', '1200', '#/wave?zone=B', 0),
    ('airport_ko_card', 'ko', 'drone', '1930', '#/call', 384),
    ('ride_en_cruise', 'en', 'cruise', '1100', '#/call?seg=ride&from=ydcruise&to=gamcheon', 0),
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
    await pg.wait_for_timeout(5000)
    return 'schematic' if await pg.locator('.map-note').count() else 'real'


async def open_page(b, url, w=390, h=844, scale=3):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=scale)
    pg = await ctx.new_page()
    await pg.goto(url, wait_until='domcontentloaded')
    await pg.add_style_tag(content=HIDE)
    return ctx, pg


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, lang, day, t, h, y in PHONE:
            ctx, pg = await open_page(b, f'{BASE}?lang={lang}&day={day}&t={t}&fresh=1{h}')
            mode = await settle(pg)
            if y:
                await pg.evaluate(f'window.scrollTo(0, {y})')
                await pg.wait_for_timeout(1200)
            await pg.screenshot(path=f'{OUT}/{name}.png')
            print(name, mode, flush=True)
            await ctx.close()
        # trips after an airport booking and a ride call (Korean)
        ctx, pg = await open_page(b, f'{BASE}?lang=ko&day=drone&t=1930&fresh=1#/call')
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
        print('trips_ko', flush=True)
        await ctx.close()
        # control dashboard (desktop, Korean)
        for name, day, t in (('dash_drone', 'drone', '1930'), ('dash_cruise', 'cruise', '1100')):
            ctx, pg = await open_page(b, f'{BASE}?day={day}&t={t}&fresh=1#/control', 1440, 900, 2)
            await pg.wait_for_load_state('networkidle')
            await pg.wait_for_timeout(1500)
            await pg.screenshot(path=f'{OUT}/{name}.png')
            await pg.screenshot(path=f'{OUT}/{name}_full.png', full_page=True)
            print(name, flush=True)
            await ctx.close()
        await b.close()


asyncio.run(main())
