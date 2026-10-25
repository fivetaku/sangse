#!/usr/bin/env python3
"""sangse 검증 게이트 3 — 실제 브라우저 렌더 스크린샷 + 레이아웃 계측.

사용법:
  python3 render_check.py <sangse/{slug} 디렉토리> [--widths 390,860] [--full]

동작:
  - Playwright(Node)로 index.html을 열어 각 폭에서 첫 화면(높이 844) 스크린샷을 qa/render-{w}.png에 저장.
    --full 이면 qa/render-{w}-full.png(전체 페이지)도 저장.
  - 계측: 가로 스크롤 여부(scrollWidth > viewport), 첫 화면 안에 Q1 h2가 있는지, 첫 두 화면(1688px) 안에 CTA가 있는지,
    모든 컷의 실측 폭이 main 폭과 일치하는지(1px 허용), 플레이스홀더(.todo) 개수, 이미지 로드 실패 수.
  - 가독성: HTML 텍스트(legal·플레이스홀더 컷·푸터)의 글자 크기 14px 미만, 명암비 4.5:1 미만(큰 글자 3:1)을 FAIL로 잡는다.
    이미지에 구운 글자는 픽셀로 읽을 수 없으므로 컷마다 표시 배율과 '이 폭에서 14px가 되려면 원본에서 몇 px'인지
    (cutImageScale.sourcePxFor14, 브리프 단위인 폭 1000 환산은 px1000For14) 남긴다 — 이미지 검수는 그 값으로 서브·본문 크기를 판정한다.
    결과를 qa/render_check.json으로 저장하고 FAIL이면 exit 1.
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
    // Subscribe before eager loading; cached images settle immediately, stalled loads fail after 5s.
    await page.evaluate(() => Promise.all([...document.images].map(image => new Promise((resolve, reject) => {
      const cleanup = () => {
        clearTimeout(timer);
        image.removeEventListener('load', done);
        image.removeEventListener('error', done);
      };
      const done = () => { cleanup(); resolve(); };
      const timer = setTimeout(() => {
        cleanup();
        reject(new Error(`Image load timed out: ${image.currentSrc || image.src}`));
      }, 5000);
      image.addEventListener('load', done, { once: true });
      image.addEventListener('error', done, { once: true });
      image.loading = 'eager';
      if (image.complete) done();
    }))));
    const m = await page.evaluate(() => {
      const vw = window.innerWidth;
      const cutsMode = !!document.querySelector('.cutsheet');
      const cuts = [...document.querySelectorAll('.cutsheet > .cut, .cutsheet > .cut-ph')];
      const firstCut = cuts[0];
      const mainWidth = document.querySelector('main').getBoundingClientRect().width;
      const cutMeasurements = cuts.map(cut => ({ id: cut.id, width: cut.getBoundingClientRect().width }));
      const cutWidthMismatches = cutMeasurements.filter(cut => Math.abs(cut.width - mainWidth) > 1);
      const imageWidthMismatches = cuts.flatMap(cut => [...cut.querySelectorAll('img')]
        .map(image => ({ id: cut.id, width: image.getBoundingClientRect().width })))
        .filter(image => Math.abs(image.width - mainWidth) > 1);
      const h2 = cutsMode ? (firstCut ? firstCut : null) : document.querySelector('#q1 h2');
      const closingCut = document.querySelector('.cutsheet [data-q*="Q8"], .cutsheet [data-q*="Q7"]');
      const cta = document.querySelector('.cta');
      const imgs = [...document.images];
      // 가독성: 직접 텍스트를 가진 보이는 요소마다 글자 크기와 WCAG 명암비(불투명도·반투명 글자색 합성)
      const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
      const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
      const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a > 0) return c; } return { r: 255, g: 255, b: 255, a: 1 }; };
      const opacityOf = el => { let o = 1; for (let e = el; e; e = e.parentElement) o *= Number(getComputedStyle(e).opacity); return o; };
      const textIssues = [];
      let textChecked = 0;
      for (const el of document.querySelectorAll('main *')) {
        if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
        const cs = getComputedStyle(el); const rect = el.getBoundingClientRect();
        if (cs.visibility === 'hidden' || cs.display === 'none' || rect.width === 0 || rect.height === 0) continue;
        textChecked++;
        const size = parseFloat(cs.fontSize); const bold = Number(cs.fontWeight) >= 700;
        const fg = parse(cs.color); const bg = bgOf(el); const a = (fg ? fg.a : 1) * opacityOf(el);
        const mix = { r: fg.r * a + bg.r * (1 - a), g: fg.g * a + bg.g * (1 - a), b: fg.b * a + bg.b * (1 - a) };
        const L1 = lum(mix), L2 = lum(bg); const ratio = Math.round((Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05) * 100) / 100;
        const large = size >= 24 || (size >= 18.66 && bold);
        const reasons = [];
        if (size < 14) reasons.push(`글자 ${size}px < 14px`);
        if (ratio < (large ? 3 : 4.5)) reasons.push(`명암비 ${ratio}:1 < ${large ? 3 : 4.5}:1`);
        if (reasons.length) textIssues.push({ selector: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : ''), text: el.textContent.trim().slice(0, 40), fontSize: size, contrast: ratio, reasons });
      }
      const cutImageScale = cuts.flatMap(cut => [...cut.querySelectorAll('img')].filter(i => i.naturalWidth > 0).map(i => {
        const shown = i.getBoundingClientRect().width; const scale = shown / i.naturalWidth;
        return { id: cut.id, naturalWidth: i.naturalWidth, scale: Math.round(scale * 1000) / 1000, sourcePxFor14: Math.ceil(14 / scale), px1000For14: Math.ceil(14 * 1000 / shown) };
      }));
      return {
        textChecked,
        textIssues,
        cutImageScale,
        vw,
        scrollWidth: document.documentElement.scrollWidth,
        horizontalScroll: document.documentElement.scrollWidth > vw + 1,
        q1HeadlineTop: h2 ? Math.round(h2.getBoundingClientRect().top) : null,
        cutsMode,
        mainWidth,
        cutWidths: cutMeasurements.map(cut => cut.width),
        cutWidthMismatches,
        imageWidthMismatches,
        cutsFillMainWidth: cuts.length > 0 && cutWidthMismatches.length === 0 && imageWidthMismatches.length === 0,
        cutCount: document.querySelectorAll('.cutsheet > .cut').length,
        placeholderCuts: document.querySelectorAll('.cutsheet > .cut-ph').length,
        q1HeadlineInFirstViewport: h2 ? (cutsMode ? h2.getBoundingClientRect().top <= 100 : h2.getBoundingClientRect().bottom <= 844) : false,
        closingCutPresent: !!closingCut,
        closingCutTop: closingCut ? Math.round(closingCut.getBoundingClientRect().top + window.scrollY) : null,
        ctaPositionStatus: cutsMode && !cta ? 'manual_review' : 'measured',
        firstCtaTop: cta ? Math.round(cta.getBoundingClientRect().top + window.scrollY) : null,
        ctaInFirstTwoViewports: cta ? (cta.getBoundingClientRect().top + window.scrollY) <= 1688 : (cutsMode ? null : false),
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
        fails: list[str] = []
        if m["horizontalScroll"]: fails.append(f"가로 스크롤 (scrollWidth {m['scrollWidth']} > {m['vw']})")
        if m.get("cutsMode"):
            if not m["cutsFillMainWidth"]:
                fails.append(f"컷·이미지 폭이 main {m['mainWidth']}px와 불일치: {m['cutWidthMismatches'] + m['imageWidthMismatches']}")
            if not m["q1HeadlineInFirstViewport"]: fails.append("첫 컷이 첫 화면 상단에 없음")
            if not m["closingCutPresent"]: fails.append("Q7/Q8 컷(보증·CTA) 없음")
            if m.get("placeholderCuts"): fails.append(f"이미지 미생성 컷 {m['placeholderCuts']}개 (텍스트 플레이스홀더 렌더)")
        else:
            if not m["q1HeadlineInFirstViewport"]: fails.append(f"Q1 헤드라인이 첫 화면 밖 (top={m['q1HeadlineTop']})")
            if not m["ctaInFirstTwoViewports"]: fails.append(f"첫 CTA가 두 화면 밖 (top={m['firstCtaTop']})")
        if m["brokenImages"]: fails.append(f"깨진 이미지 {m['brokenImages']}/{m['imageCount']}")
        for t in m.get("textIssues", [])[:10]:
            fails.append(f"가독성 {t['selector']} '{t['text']}': {', '.join(t['reasons'])}")
        if len(m.get("textIssues", [])) > 10: fails.append(f"가독성 외 {len(m['textIssues']) - 10}건(qa/render_check.json)")
        checks.append({"width": int(w), "status": "FAIL" if fails else "PASS", "fails": fails, "metrics": m,
                       "screenshot": os.path.join(base, "qa", f"render-{w}.png")})
    result = {"checks": checks, "verdict": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"}
    json.dump(result, open(os.path.join(base, "qa", "render_check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for c in checks:
        mark = "✅" if c["status"] == "PASS" else "❌"
        m = c["metrics"]
        extra = f" 컷={m.get('cutCount')}(+미생성 {m.get('placeholderCuts')})" if m.get("cutsMode") else f" CTA@{m['firstCtaTop']}"
        print(f"{mark} {c['width']}px — vw={m['vw']} 높이={m['pageHeight']} 이미지={m['imageCount']} 플레이스홀더={m['placeholders']}{extra} → {c['screenshot']}")
        if m.get("cutImageScale"):
            need = max(s["sourcePxFor14"] for s in m["cutImageScale"])
            per1000 = max(s["px1000For14"] for s in m["cutImageScale"])
            print(f"     이미지 안 글자: 이 폭에서 14px가 되려면 폭 1000 환산 {per1000}px(원본 최대 {need}px) 이상 — 서브·본문·각주가 이보다 작으면 이미지 검수에서 재생성")
        for f_ in c["fails"]:
            print(f"     - {f_}")
    print(f"\n{result['verdict']} → {os.path.join(base, 'qa', 'render_check.json')}")
    sys.exit(0 if result["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
