#!/usr/bin/env python3
"""sangse 검증 게이트 3 — 실제 브라우저 렌더 스크린샷 + 레이아웃 계측.

사용법:
  python3 render_check.py <sangse/{slug} 디렉토리> [--widths 390,860] [--full]

동작:
  - Playwright(Node)로 index.html을 열어 각 폭에서 첫 화면(높이 844) 스크린샷을 qa/render-{w}.png에 저장.
    --full 이면 qa/render-{w}-full.png(전체 페이지)도 저장.
  - 계측: 가로 스크롤 여부(scrollWidth > viewport), 첫 화면 안에 Q1 h2가 있는지, 첫 두 화면(1688px) 안에 CTA가 있는지,
    플레이스홀더(.todo) 개수, 이미지 로드 실패 수. 결과를 qa/render_check.json으로 저장하고 FAIL이면 exit 1.
  - 헤드리스 Chrome CLI(--window-size)는 최소 창 폭이 500px라 390 스크린샷이 잘려 보이는 함정이 있다. 이 스크립트는
    Playwright의 viewport 에뮬레이션을 쓰므로 그 문제가 없다.

의존: Node + playwright 패키지. 탐색 순서: $SANGSE_NODE_MODULES → ~/.insane-search/node/node_modules → 전역(require 해석).
브라우저는 시스템 Chrome(channel=chrome)을 우선 쓰고, 없으면 번들 Chromium.
"""
import json
import os
import subprocess
import sys
import tempfile

JS = r"""
const path = require('path');
const [,, dir, widthsArg, full] = process.argv;
const widths = widthsArg.split(',').map(Number);
let pw;
try { pw = require('playwright'); } catch (e) { try { pw = require('patchright'); } catch (e2) { console.error('NO_PLAYWRIGHT'); process.exit(3); } }
(async () => {
  let browser;
  try { browser = await pw.chromium.launch({ channel: 'chrome', headless: true }); }
  catch (e) { browser = await pw.chromium.launch({ headless: true }); }
  const url = 'file://' + path.join(dir, 'index.html');
  const out = {};
  for (const w of widths) {
    const ctx = await browser.newContext({ viewport: { width: w, height: 844 }, deviceScaleFactor: 1, isMobile: w < 600, hasTouch: w < 600 });
    const page = await ctx.newPage();
    const failed = [];
    page.on('requestfailed', r => failed.push(r.url()));
    await page.goto(url, { waitUntil: 'load' });
    // lazy 이미지는 스크롤 전엔 로드되지 않아 무한 대기가 된다 → eager로 바꾸고 5초 상한으로 기다린다
    await page.evaluate(() => { for (const i of document.images) { i.loading = 'eager'; if (i.src) { const s = i.src; i.src = ''; i.src = s; } } });
    await Promise.race([
      page.evaluate(() => Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })))),
      page.waitForTimeout(5000),
    ]);
    await page.waitForTimeout(200);
    const m = await page.evaluate(() => {
      const vw = window.innerWidth;
      const h2 = document.querySelector('#q1 h2');
      const cta = document.querySelector('.cta');
      const imgs = [...document.images];
      return {
        vw,
        scrollWidth: document.documentElement.scrollWidth,
        horizontalScroll: document.documentElement.scrollWidth > vw + 1,
        q1HeadlineTop: h2 ? Math.round(h2.getBoundingClientRect().top) : null,
        q1HeadlineInFirstViewport: h2 ? (h2.getBoundingClientRect().bottom <= 844) : false,
        firstCtaTop: cta ? Math.round(cta.getBoundingClientRect().top + window.scrollY) : null,
        ctaInFirstTwoViewports: cta ? (cta.getBoundingClientRect().top + window.scrollY) <= 1688 : false,
        placeholders: document.querySelectorAll('.todo, .todo-inline').length,
        brokenImages: imgs.filter(i => !i.complete || i.naturalWidth === 0).length,
        imageCount: imgs.length,
        pageHeight: document.documentElement.scrollHeight,
      };
    });
    await page.screenshot({ path: path.join(dir, 'qa', `render-${w}.png`), fullPage: false });
    if (full === '1') await page.screenshot({ path: path.join(dir, 'qa', `render-${w}-full.png`), fullPage: true });
    m.requestFailed = failed;
    out[w] = m;
    await ctx.close();
  }
  await browser.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.error(String(e)); process.exit(4); });
"""


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr); sys.exit(2)
    base = os.path.abspath(args[0])
    widths = "390,860"
    if "--widths" in args:
        widths = args[args.index("--widths") + 1]
    full = "1" if "--full" in args else "0"
    if not os.path.exists(os.path.join(base, "index.html")):
        print("ERROR: index.html 없음 — 먼저 assemble_html.py", file=sys.stderr); sys.exit(2)
    os.makedirs(os.path.join(base, "qa"), exist_ok=True)

    node_paths = [p for p in [os.environ.get("SANGSE_NODE_MODULES"), os.path.expanduser("~/.insane-search/node/node_modules")] if p and os.path.isdir(p)]
    env = dict(os.environ)
    if node_paths:
        env["NODE_PATH"] = os.pathsep.join(node_paths + [env.get("NODE_PATH", "")]).strip(os.pathsep)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(JS); js_path = f.name
    proc = subprocess.run(["node", js_path, base, widths, full], capture_output=True, text=True, env=env)
    os.unlink(js_path)
    if proc.returncode == 3:
        print("ERROR: playwright 미설치 — `mkdir -p ~/.insane-search/node && cd ~/.insane-search/node && npm i playwright` 또는 SANGSE_NODE_MODULES 지정", file=sys.stderr); sys.exit(3)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr); sys.exit(4)
    data = json.loads(proc.stdout.strip().splitlines()[-1])

    checks = []
    for w, m in data.items():
        fails = []
        if m["horizontalScroll"]: fails.append(f"가로 스크롤 (scrollWidth {m['scrollWidth']} > {m['vw']})")
        if not m["q1HeadlineInFirstViewport"]: fails.append(f"Q1 헤드라인이 첫 화면 밖 (top={m['q1HeadlineTop']})")
        if not m["ctaInFirstTwoViewports"]: fails.append(f"첫 CTA가 두 화면 밖 (top={m['firstCtaTop']})")
        if m["brokenImages"]: fails.append(f"깨진 이미지 {m['brokenImages']}/{m['imageCount']}")
        checks.append({"width": int(w), "status": "FAIL" if fails else "PASS", "fails": fails, "metrics": m,
                       "screenshot": os.path.join(base, "qa", f"render-{w}.png")})
    result = {"checks": checks, "verdict": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"}
    json.dump(result, open(os.path.join(base, "qa", "render_check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for c in checks:
        mark = "✅" if c["status"] == "PASS" else "❌"
        m = c["metrics"]
        print(f"{mark} {c['width']}px — vw={m['vw']} 높이={m['pageHeight']} 이미지={m['imageCount']} 플레이스홀더={m['placeholders']} CTA@{m['firstCtaTop']} → {c['screenshot']}")
        for f_ in c["fails"]:
            print(f"     - {f_}")
    print(f"\n{result['verdict']} → {os.path.join(base, 'qa', 'render_check.json')}")
    sys.exit(0 if result["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
