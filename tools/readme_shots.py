"""Screens for the README slides and demo GIF (live demo, real map). BASE/OUT can be overridden by env."""
import asyncio
import os

from playwright.async_api import async_playwright

BASE = os.environ.get('BASE', 'https://jaewansh.github.io/pado-call/')
OUT = os.environ.get('OUT', 'shots3')
os.makedirs(OUT, exist_ok=True)
HIDE = 'aside.demo { display: none !important; } .toast { display: none !important; }'
log = []


async def settle(pg, maps=True):
    if maps:
        try:
            await pg.wait_for_selector('.rmap canvas, .map-note', timeout=20000)
        except Exception:
            pass
    try:
        await pg.wait_for_load_state('networkidle', timeout=20000)
    except Exception:
        pass
    await pg.wait_for_timeout(5000 if maps else 800)
    return 'schematic' if await pg.locator('.map-note').count() else 'real'


async def phone(b, url, scale=3, w=390, h=844):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=scale)
    pg = await ctx.new_page()
    await pg.goto(url, wait_until='domcontentloaded')
    await pg.add_style_tag(content=HIDE)
    return ctx, pg


async def scroll_to(pg, sel, off):
    await pg.evaluate(
        """([s, o]) => { const el = document.querySelector(s); if (!el) return;
           const y = el.getBoundingClientRect().top + window.scrollY - o; window.scrollTo(0, Math.max(0, y)); }""",
        [sel, off],
    )
    await pg.wait_for_timeout(1200)


async def shot(pg, name, full=False):
    await pg.screenshot(path=f'{OUT}/{name}.png', full_page=full)
    log.append(name)
    print(name, flush=True)


def u(q, h):
    return f'{BASE}?{q}&fresh=1{h}'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()

        # 1. airport arrival (English)
        ctx, pg = await phone(b, u('lang=en&day=drone&t=1930', '#/call'))
        print('map', await settle(pg))
        await shot(pg, 'air_en_top')
        await scroll_to(pg, '.card.airport', 10)
        await shot(pg, 'air_en_card')
        await pg.click('.card.airport button.btn-primary')
        await pg.wait_for_timeout(700)
        await shot(pg, 'pay_en_air')
        await ctx.close()

        # 2. hotel pickup to the airport (Japanese)
        ctx, pg = await phone(b, u('lang=ja&day=drone&t=1500', '#/call?dir=dep'))
        await settle(pg)
        await shot(pg, 'dep_ja_top')
        await scroll_to(pg, '.slot', 150)
        await shot(pg, 'dep_ja_slots')
        await ctx.close()

        # 3. ride now (Simplified Chinese) → pay → QR pass → driver check → boarded
        ctx, pg = await phone(b, u('lang=zhHans&day=drone&t=1930', '#/call?seg=ride&from=haeundae&to=gwangalli'))
        await settle(pg)
        await shot(pg, 'ride_zh_top')
        await scroll_to(pg, '.gauge', 250)
        await shot(pg, 'ride_zh_gauge')
        await scroll_to(pg, '.photo', 70)
        await shot(pg, 'ride_zh_photo')
        await pg.click('button.btn-primary >> nth=-1')
        await pg.wait_for_timeout(700)
        await shot(pg, 'pay_zh')
        await pg.click('.pay-opt >> nth=2')
        await pg.wait_for_timeout(200)
        await shot(pg, 'pay_zh_alipay')
        await pg.click('.sheet .btn-primary')
        await pg.wait_for_timeout(1500)
        await pg.evaluate('window.scrollTo(0, 0)')
        await pg.wait_for_timeout(600)
        await shot(pg, 'qr_zh')
        await pg.click('.qr-btn')
        await pg.wait_for_timeout(500)
        await shot(pg, 'qr_zh_full')
        await pg.keyboard.press('Escape')
        await pg.wait_for_timeout(300)
        await pg.click('a.demo-link')
        await pg.wait_for_timeout(1200)
        await shot(pg, 'drv_phone_list')
        await pg.click('.pk.hl button')
        await pg.wait_for_timeout(900)
        await scroll_to(pg, '.verdict', 12)
        await shot(pg, 'drv_phone_ok')
        await pg.goto(BASE + '?lang=zhHans&day=drone&t=1930#/trips', wait_until='domcontentloaded')
        await pg.add_style_tag(content=HIDE)
        await settle(pg, maps=False)
        await shot(pg, 'trips_zh_boarded')
        await ctx.close()

        # 4. ride on a cruise day from the Yeongdo cruise terminal (Korean)
        ctx, pg = await phone(b, u('lang=ko&day=cruise&t=1100', '#/call?seg=ride&from=ydcruise&to=gamcheon'))
        await settle(pg)
        await shot(pg, 'ride_ko_cruise')
        await scroll_to(pg, '.photo', 70)
        await shot(pg, 'ride_ko_photo')
        await ctx.close()

        # 5. crowd map (Japanese, drone show Saturday)
        ctx, pg = await phone(b, u('lang=ja&day=drone&t=1930', '#/wave'))
        await settle(pg)
        await shot(pg, 'wave_ja_top')
        await scroll_to(pg, '.alert', 120)
        await shot(pg, 'wave_ja_alert')
        await scroll_to(pg, '.fc', 150)
        await shot(pg, 'wave_ja_fc')
        await ctx.close()

        # 6. crowd map, zone B on a cruise day (Korean)
        ctx, pg = await phone(b, u('lang=ko&day=cruise&t=1200', '#/wave?zone=B'))
        await settle(pg)
        await shot(pg, 'wave_ko_b')
        await scroll_to(pg, '.alt-list', 200)
        await shot(pg, 'wave_ko_b_alts')
        await ctx.close()

        # 7. trips with an airport pass (English) for the GIF
        ctx, pg = await phone(b, u('lang=en&day=drone&t=1930', '#/call'))
        await settle(pg)
        await pg.fill('#flight', 'KE1234')
        await pg.click('.card.airport button.btn-primary')
        await pg.wait_for_timeout(500)
        await pg.click('.pay-opt >> nth=1')
        await pg.click('.sheet .btn-primary')
        await pg.wait_for_timeout(1500)
        await pg.evaluate('window.scrollTo(0, 0)')
        await pg.wait_for_timeout(500)
        await shot(pg, 'qr_en_air')
        await ctx.close()

        # 8. desktop: control dashboard, model page
        for name, q, h in (('dash_cruise', 'day=cruise&t=1100', '#/control'), ('dash_drone', 'day=drone&t=1930', '#/control'), ('model', 'day=drone&t=1930', '#/model')):
            ctx = await b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)
            pg = await ctx.new_page()
            await pg.goto(u(q, h), wait_until='domcontentloaded')
            await settle(pg, maps=False)
            await pg.wait_for_timeout(1200)
            await shot(pg, name)
            await shot(pg, name + '_full', full=True)
            await ctx.close()

        # 9. desktop: driver app after a Chinese passenger's QR was checked, English airport pass waiting
        ctx = await b.new_context(viewport={'width': 1280, 'height': 860}, device_scale_factor=2)
        pg = await ctx.new_page()
        await pg.goto(u('lang=en&day=drone&t=1930', '#/call'), wait_until='domcontentloaded')
        await settle(pg)
        await pg.fill('#flight', 'KE1234')
        await pg.click('.card.airport button.btn-primary')
        await pg.wait_for_timeout(500)
        await pg.click('.sheet .btn-primary')
        await pg.wait_for_timeout(1500)
        await pg.goto(BASE + '?lang=zhHans&day=drone&t=1930#/call?seg=ride&from=haeundae&to=gwangalli', wait_until='domcontentloaded')
        await settle(pg)
        await pg.click('button.btn-primary >> nth=-1')
        await pg.wait_for_timeout(500)
        await pg.click('.pay-opt >> nth=2')
        await pg.click('.sheet .btn-primary')
        await pg.wait_for_timeout(1500)
        await pg.goto(BASE + '?day=drone&t=1930#/driver', wait_until='domcontentloaded')
        await settle(pg, maps=False)
        await pg.click('.pk >> nth=0 >> button')
        await pg.wait_for_timeout(1200)
        await pg.evaluate('window.scrollTo(0, 0)')
        await pg.wait_for_timeout(500)
        await shot(pg, 'driver_desk')
        await shot(pg, 'driver_desk_full', full=True)
        await ctx.close()

        await b.close()
    print('done', len(log))


asyncio.run(main())
