"""Record the 40-second foreign-visitor demo video with the real OpenFreeMap map.

Runs on a GitHub Actions runner (open internet). The stage page video/stage.html holds the built app
(docs/) in iframes and plays a fixed timeline; each tick() moves it to frame f and we screenshot 1920x1080.

  python video/record.py          full run -> video/out/<NAME>
  python video/record.py probe    load the first screen only and report the map state
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
VID = ROOT / 'video'
FR = VID / '_frames'
OUT = VID / 'out'
NAME = '파도콜_외국인_사용영상_40초_실제지도.mp4'
FPS = 30
PORT = 8767


async def run(probe: bool, check: list[float] | None = None, blank: bool = False) -> None:
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.0)
        async with async_playwright() as p:
            b = await p.chromium.launch(args=['--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
            ctx = await b.new_context(viewport={'width': 1680, 'height': 945}, device_scale_factor=1920 / 1680,
                                      locale='en-US', timezone_id='Asia/Seoul', service_workers='block')
            pg = await ctx.new_page()
            errors: list[str] = []
            pg.on('pageerror', lambda e: errors.append(str(e)))
            await pg.goto(f'http://127.0.0.1:{PORT}/video/stage.html' + ('?map=blank' if blank else ''), wait_until='load')
            cdp = await ctx.new_cdp_session(pg)
            await cdp.send('Animation.enable')
            await cdp.send('Animation.setPlaybackRate', {'playbackRate': 0.3})  # app's own CSS motion ~ real speed on video
            t0 = time.time()
            print('init:', await pg.evaluate('init()'), f'{time.time() - t0:.1f}s', flush=True)
            state = await pg.evaluate('mapState()')
            print('map state after the first screen:', state, flush=True)
            OUT.mkdir(parents=True, exist_ok=True)
            await pg.screenshot(path=str(OUT / 'first_frame.png'))
            if state != 'ready':
                raise SystemExit(f'real map not ready ({state}) - stopping so the schematic map is not recorded')
            if probe:
                await b.close()
                return
            dur = await pg.evaluate('DUR')
            FR.mkdir(exist_ok=True)
            n = round(FPS * dur)
            t0 = time.time()
            want = {round(t * FPS) for t in check} if check else None
            for f in range(n):
                await pg.evaluate(f'tick({f})')
                if want is not None:
                    if f in want:
                        await pg.screenshot(path=str(OUT / f't{f / FPS:05.2f}.png'))
                    continue
                await pg.screenshot(path=str(FR / f'f{f:04d}.jpg'), type='jpeg', quality=94)
                if f % 150 == 0:
                    print(f'frame {f} / {n}  {time.time() - t0:.0f}s', flush=True)
                if f in (int(1.5 * FPS), int(13.0 * FPS)):  # airport map, Day 2 ride map
                    await pg.screenshot(path=str(OUT / f'check_{f / FPS:04.1f}s.png'))
            print('map state at the end:', await pg.evaluate('mapState()'), flush=True)
            if errors:
                print('page errors:', errors[:5], flush=True)
            await b.close()
    finally:
        srv.terminate()


def encode() -> Path:
    out = OUT / NAME
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(FR / 'f%04d.jpg'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(out)], check=True)
    return out


if __name__ == '__main__':
    probe = len(sys.argv) > 1 and sys.argv[1] == 'probe'
    if len(sys.argv) > 1 and sys.argv[1] == 'blank-check':  # local dry run: empty map style, a few frames only
        asyncio.run(run(False, [float(x) for x in sys.argv[2:]], blank=True))
        sys.exit(0)
    asyncio.run(run(probe))
    if not probe:
        o = encode()
        print(o.name, round(o.stat().st_size / 1024 / 1024, 2), 'MB', flush=True)
