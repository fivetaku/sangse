// sangse 레퍼런스 캡처 — 실제 Chrome(헤드풀, WAF 통과용)으로 모바일 390 + 데스크톱 1280 전체 페이지 캡처 + 큰 이미지 인벤토리
// usage: NODE_PATH=~/.insane-search/node/node_modules node capture_reference.js <slug> <url> <outdir> [--headless]
// 출력: <outdir>/<slug>-mobile-full.png, <slug>-desktop-full.png, <slug>.json (페이지 높이·텍스트량·폭≥300 이미지 목록: src/w/h/naturalWidth/naturalHeight/top)
// 이후 절차는 references/reference-capture.md — 상세 이미지 원본(json의 nh가 큰 src) 다운로드 → 1,400px 조각 → 해부 에이전트
// 함정: 스마트스토어는 자동화 브라우저에 NAVER 로그인 벽, 쿠팡은 Access Denied(사용자 크롬 세션(paseo)에서 evaluate로 img 목록을 뽑는 방법만 통함)
const path = require('path');
const fs = require('fs');
let pw; try { pw = require('patchright'); } catch (e) { pw = require('playwright'); }
const [,, slug, url, outdir, ...flags] = process.argv;
const headless = flags.includes('--headless');
(async () => {
  const browser = await pw.chromium.launch({ channel: 'chrome', headless });
  const result = { slug, url, captured_at: new Date().toISOString(), views: {} };
  for (const view of [{ name: 'mobile', width: 390, height: 844, mobile: true, ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' },
                     { name: 'desktop', width: 1280, height: 900, mobile: false }]) {
    const ctx = await browser.newContext({ viewport: { width: view.width, height: view.height }, deviceScaleFactor: 1, isMobile: view.mobile, hasTouch: view.mobile, userAgent: view.ua, locale: 'ko-KR' });
    const page = await ctx.newPage();
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForTimeout(3000);
      // 상세정보 탭/더보기 버튼 시도 (플랫폼 공통 후보)
      for (const sel of ['button:has-text("상세정보 펼쳐보기")', 'button:has-text("상세정보 더보기")', 'button:has-text("더보기")', 'a:has-text("상품설명")', 'a:has-text("상품정보")', 'button:has-text("상품 상세")', 'li:has-text("상품설명")', 'text=상세정보']) {  // 올리브영은 '상품설명' 탭을 눌러야 상세가 펼쳐진다
        try { const el = page.locator(sel).first(); if (await el.isVisible({ timeout: 800 })) { await el.click({ timeout: 2000 }); await page.waitForTimeout(1200); } } catch (e) {}
      }
      // 끝까지 스크롤해 lazy 이미지 로드
      const total = await page.evaluate(async () => {
        let y = 0; const step = 700;
        while (y < document.documentElement.scrollHeight && y < 60000) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 250)); y += step; }
        window.scrollTo(0, 0); await new Promise(r => setTimeout(r, 800));
        return document.documentElement.scrollHeight;
      });
      // 이미지 인벤토리: 상세 영역의 큰 이미지들 (폭 300px 이상)
      // lazy 이미지(1×1 gif 자리표시자)는 data-src/data-original에 실제 URL이 있다 — 올리브영 실측(2026-09-02)
      const imgs = await page.evaluate(() => [...document.images].map(i => { const r = i.getBoundingClientRect(); const lazy = i.getAttribute('data-src') || i.getAttribute('data-original') || i.getAttribute('data-lazy') || ''; const cur = i.currentSrc || i.src || ''; const src = (cur.startsWith('data:') && lazy) ? lazy : (lazy && i.naturalWidth <= 1 ? lazy : cur); return { src: src.slice(0, 260), lazy: !!lazy && (cur.startsWith('data:') || i.naturalWidth <= 1), w: Math.round(r.width), h: Math.round(r.height), nw: i.naturalWidth, nh: i.naturalHeight, top: Math.round(r.top + window.scrollY), alt: (i.alt || '').slice(0, 80) }; }).filter(i => i.w >= 300 && i.h >= 120 && !i.src.startsWith('data:')));
      const textStats = await page.evaluate(() => { const t = document.body.innerText || ''; return { chars: t.length, lines: t.split('\n').filter(s => s.trim()).length }; });
      const shot = path.join(outdir, `${slug}-${view.name}-full.png`);
      await page.screenshot({ path: shot, fullPage: true });
      result.views[view.name] = { pageHeight: total, screenshot: shot, bigImages: imgs.length, bigImageTotalHeight: imgs.reduce((a, i) => a + i.h, 0), images: imgs, text: textStats, title: await page.title() };
    } catch (e) {
      result.views[view.name] = { error: String(e).slice(0, 300) };
    }
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(outdir, `${slug}.json`), JSON.stringify(result, null, 2));
  console.log(JSON.stringify({ slug, mobile: result.views.mobile && (result.views.mobile.error || { h: result.views.mobile.pageHeight, imgs: result.views.mobile.bigImages }), desktop: result.views.desktop && (result.views.desktop.error || { h: result.views.desktop.pageHeight, imgs: result.views.desktop.bigImages }) }));
})().catch(e => { console.error(String(e)); process.exit(1); });
