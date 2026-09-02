#!/usr/bin/env python3
"""sangse 검증 게이트 1 (컷 시트 모드) — cuts.md + legal.md를 결정론적으로 판정. 표준 라이브러리만.

사용법:
  python3 check_cuts.py <sangse/{slug}> [--category common|food|health_food ...] [--platform web|smartstore|kmong] [--json]

검사:
  T1  컷 헤딩 문법(## Cnn · 템플릿 · Q · h=px), 템플릿 ID 존재, 높이가 템플릿 범위 안
  T2  헤드라인 행 수·행당 글자 수, body 줄 수·줄당 글자 수가 템플릿 한도 안 (공백 제외 글자 수)
  T3  컷 수 10~20, Q1~Q8 각각 최소 1컷(Q4·Q8은 자료 없으면 생략 허용 → WARN), 순서가 Q1/Q2 → … → Q7/Q8 흐름
  T4  첫 컷(anchor)이 K2 또는 K1, 각 컷 bg 지정, K4에 footnote, K7 body에 고시 문구 포함(health_food)
  T5  cuts.md + legal.md의 숫자가 raw-input.md/intake-checklist.md에 존재(파생 계산식 허용)
  T6  카테고리 금지어(assets/banned-words.json) — cuts.md 전체 + legal.md
  T7  legal.md 필수 블록 존재(카테고리별) — 없으면 FAIL, 내용이 [자료 필요]면 INFO
  I   image: 경로 실존(있는 것만), 해상도 폭 ≥ 900 (sips 없이 PNG/JPEG 헤더 파싱)
종료코드 0 PASS / 1 FAIL / 2 입력 오류. 결과 qa/check_cuts.json
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = json.load(open(os.path.join(HERE, "..", "assets", "cut-templates.json"), encoding="utf-8"))["templates"]
BANNED = json.load(open(os.path.join(HERE, "..", "assets", "banned-words.json"), encoding="utf-8"))
CUT_RE = re.compile(r"^##\s*(C\d{2})\s*[·•\-]\s*([A-Z]\d{1,2})\s*[·•\-]\s*((?:Q\d(?:[·/,]Q\d)*|brand))\s*[·•\-]\s*h\s*=\s*(\d+)\s*$", re.MULTILINE)
PH_RE = re.compile(r"\[(자료 필요|선택|이미지 생성 실패)[^\]]*\]")
LEGAL_REQUIRED = {
    "health_food": ["기능성", "주의사항", "제품 상세정보", "영양", "원료명", "환불"],
    "food": ["주의사항", "제품 상세정보", "원료명", "환불"],
    "common": ["환불"],
}
Q_ORDER = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]


def klen(s):
    return len(re.sub(r"\s", "", s or ""))


def parse_cuts(md):
    header = {}
    for k in ("platform", "width", "brand", "tone", "anchor"):
        m = re.search(rf"^{k}:\s*(.+)$", md, re.MULTILINE)
        if m: header[k] = m.group(1).strip()
    cuts = []
    ms = list(CUT_RE.finditer(md))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(md)
        block = md[m.end():end]
        cut = {"id": m.group(1), "tpl": m.group(2), "q": m.group(3).strip(), "h": int(m.group(4)), "fields": {}}
        lines = block.splitlines()
        j = 0
        while j < len(lines):
            ln = lines[j]
            km = re.match(r"^([a-z_]+):\s*(.*)$", ln)
            if km:
                key, val = km.group(1), km.group(2).strip()
                if val == "|":
                    body = []
                    j += 1
                    while j < len(lines) and (lines[j].startswith("  ") or not lines[j].strip()):
                        if lines[j].strip(): body.append(lines[j].strip())
                        j += 1
                    cut["fields"][key] = body
                    continue
                cut["fields"][key] = val
            j += 1
        cuts.append(cut)
    return header, cuts


def png_jpeg_size(path):
    try:
        with open(path, "rb") as f:
            head = f.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24]); return w, h
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF: return None
                    if marker[1] in (0xC0, 0xC1, 0xC2):
                        f.read(3); h, w = struct.unpack(">HH", f.read(4)); return w, h
                    seg = struct.unpack(">H", f.read(2))[0]; f.seek(seg - 2, 1)
    except Exception:
        return None
    return None


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr); sys.exit(2)
    base = os.path.abspath(args[0])
    cats = ["common"]
    if "--category" in args:
        i = args.index("--category") + 1
        while i < len(args) and not args[i].startswith("--"):
            cats.append(args[i]); i += 1
    platform = args[args.index("--platform") + 1] if "--platform" in args else "web"
    as_json = "--json" in args
    cp = os.path.join(base, "cuts.md")
    if not os.path.exists(cp):
        print(f"ERROR: {cp} 없음", file=sys.stderr); sys.exit(2)
    md = open(cp, encoding="utf-8").read()
    legal = open(os.path.join(base, "legal.md"), encoding="utf-8").read() if os.path.exists(os.path.join(base, "legal.md")) else ""
    sources = ""
    for n in ("raw-input.md", "intake-checklist.md"):
        p = os.path.join(base, n)
        if os.path.exists(p): sources += open(p, encoding="utf-8").read() + "\n"

    checks = []
    def add(cid, st, msg, detail=None): checks.append({"id": cid, "status": st, "message": msg, "detail": detail or []})

    header, cuts = parse_cuts(md)
    # T1
    bad = []
    for c in cuts:
        t = TEMPLATES.get(c["tpl"])
        if not t: bad.append(f"{c['id']}: 템플릿 {c['tpl']} 없음"); continue
        lo, hi = t["h"]
        if not (lo - 50 <= c["h"] <= hi + 50): bad.append(f"{c['id']}: h={c['h']} (템플릿 {c['tpl']} 범위 {lo}~{hi})")
    add("T1", "FAIL" if bad else "PASS", "컷 헤딩·템플릿·높이" + (" 위반" if bad else " 정상"), bad)
    # T2
    bad = []
    for c in cuts:
        t = TEMPLATES.get(c["tpl"]);
        if not t: continue
        f = c["fields"]
        head = f.get("headline", "")
        rows = [r for r in head.split("|") if r.strip()] if isinstance(head, str) else []
        if not rows: bad.append(f"{c['id']}: headline 없음")
        if len(rows) > 3: bad.append(f"{c['id']}: headline {len(rows)}행 (최대 3)")
        for r in rows:
            if klen(r) > t["headline_max"]: bad.append(f"{c['id']}: headline 행 '{r.strip()}' {klen(r)}자 > {t['headline_max']}")
        sub = f.get("sub", "")
        if isinstance(sub, str) and klen(sub) > t["sub_max"] and not PH_RE.search(sub): bad.append(f"{c['id']}: sub {klen(sub)}자 > {t['sub_max']}")
        body = f.get("body", [])
        if isinstance(body, str): body = [body] if body else []
        if len(body) > t["body_lines_max"]: bad.append(f"{c['id']}: body {len(body)}줄 > {t['body_lines_max']}")
        for ln in body:
            if klen(ln) > t["line_max"] and not PH_RE.search(ln): bad.append(f"{c['id']}: body 줄 '{ln[:14]}…' {klen(ln)}자 > {t['line_max']}")
    add("T2", "FAIL" if bad else "PASS", "텍스트 슬롯 한도" + (" 초과" if bad else " 정상"), bad)
    # T3
    bad, warn = [], []
    if not (10 <= len(cuts) <= 20): bad.append(f"컷 수 {len(cuts)} (10~20)")
    qs = [c["q"] for c in cuts]
    covered = {q for c in cuts for q in re.split(r"[·,/ ]+", c["q"]) if q.startswith("Q")}
    for q in Q_ORDER:
        if q not in covered:
            (warn if q in ("Q4", "Q8") else bad).append(f"{q} 컷 없음")
    firstq = [int(q[1]) for c in cuts for q in [re.split(r"[·,/ ]+", c["q"])[0]] if q.startswith("Q")]
    if firstq and firstq[-1] < 7: bad.append(f"마지막 컷이 Q{firstq[-1]} — Q7/Q8로 끝나야 함")
    if firstq and firstq[0] > 2: bad.append(f"첫 컷이 Q{firstq[0]} — Q1/Q2로 시작해야 함")
    add("T3", "FAIL" if bad else ("WARN" if warn else "PASS"), "컷 수·Q 커버리지·순서", bad + warn)
    # T4
    bad = []
    if cuts and cuts[0]["tpl"] not in ("K2", "K1"): bad.append(f"첫 컷 템플릿 {cuts[0]['tpl']} (K2/K1 권장)")
    for c in cuts:
        f = c["fields"]
        if not f.get("bg"): bad.append(f"{c['id']}: bg 없음")
        if c["tpl"] == "K4" and not f.get("footnote"): bad.append(f"{c['id']}: K4 TPO 컷에 footnote(섭취 횟수 가드) 없음")
        if c["tpl"] == "K7" and "health_food" in cats:
            body = " ".join(f.get("body", []) if isinstance(f.get("body"), list) else [f.get("body", "")])
            if "도움을 줄 수 있음" not in body and "도움을 줄 수 있" not in body: bad.append(f"{c['id']}: K7에 고시 기능성 문구 없음")
    add("T4", "FAIL" if bad else "PASS", "앵커·배경·법정 가드", bad)
    # T5 numbers
    text = PH_RE.sub("", md + "\n" + legal)
    text = re.sub(r"(?m)^\s*\d+\.\s", "", text)
    text = re.sub(r"(?m)^## C\d{2}.*$", "", text)
    text = re.sub(r"h\s*=\s*\d+", "", text)
    text = re.sub(r"#[0-9A-Fa-f]{3,6}", "", text)
    text = re.sub(r"(?m)^(width|platform|anchor|image|visual|text_pos|brand|tone):.*$", "", text)  # 지시문·메타는 카피가 아님
    src_digits = {re.sub(r"[,\s]", "", d) for d in re.findall(r"\d[\d,\.]*", sources)}
    untraced = sorted({tok for tok in re.findall(r"\d[\d,\.]*", text) if not (len(re.sub(r"[,\s]", "", tok)) == 1 and tok in "1234") and re.sub(r"[,\s]", "", tok) not in src_digits})
    if not sources: add("T5", "WARN", "raw-input/intake 없음 — 출처 추적 불가")
    else: add("T5", "FAIL" if untraced else "PASS", f"출처 없는 숫자 {len(untraced)}개" if untraced else "모든 숫자가 입력에 존재", untraced)
    # T6 banned
    clean = PH_RE.sub("", md + "\n" + legal)
    fails, warns = [], []
    for cat in cats:
        rules = BANNED.get(cat, {})
        for w in rules.get("ban", []):
            for m in re.finditer(w, clean):
                ls = clean.rfind("\n", 0, m.start()) + 1; le = clean.find("\n", m.end()); line = clean[ls:le if le != -1 else None]
                if re.search(r"아닙니다|아님|오인|금지|하지 (마|않)", line): continue  # 법정 부정문("의약품이 아닙니다")은 제외
                fails.append(f"[{cat}] '{m.group(0)}' @L{clean.count(chr(10), 0, m.start()) + 1}")
        for w in rules.get("warn", []):
            for m in re.finditer(w, clean): warns.append(f"[{cat}] '{m.group(0)}' @L{clean.count(chr(10), 0, m.start()) + 1}")
    add("T6", "FAIL" if fails else ("WARN" if warns else "PASS"), f"금지어 {len(fails)}건 / 경고어 {len(warns)}건", fails + warns)
    # T7 legal blocks
    req = []
    for cat in cats: req += LEGAL_REQUIRED.get(cat, [])
    missing = [r for r in dict.fromkeys(req) if not re.search(rf"^##\s*.*{re.escape(r)}", legal, re.MULTILINE)]
    if not legal: add("T7", "FAIL", "legal.md 없음")
    else: add("T7", "FAIL" if missing else "PASS", "legal 블록 누락" if missing else f"legal 블록 {len(dict.fromkeys(req))}개 존재", missing)
    # I images
    missing, small, present = [], [], 0
    for c in cuts:
        img = c["fields"].get("image")
        if not img or PH_RE.search(str(img)): continue
        p = os.path.join(base, img)
        if not os.path.exists(p): missing.append(f"{c['id']}: {img}"); continue
        present += 1
        sz = png_jpeg_size(p)
        if sz and sz[0] < 900: small.append(f"{c['id']}: 폭 {sz[0]} < 900")
    add("I", "FAIL" if (missing or small) else ("PASS" if present else "INFO"), f"이미지 {present}장 실존" + (f", 누락 {len(missing)}, 저해상 {len(small)}" if (missing or small) else ""), missing + small)
    # placeholders
    phs = [m.group(0) for m in PH_RE.finditer(md + "\n" + legal)]
    add("P", "INFO", f"플레이스홀더 {len(phs)}개", phs)

    n_fail = sum(1 for c in checks if c["status"] == "FAIL"); n_warn = sum(1 for c in checks if c["status"] == "WARN")
    result = {"path": cp, "cuts": len(cuts), "category": cats, "platform": platform, "checks": checks, "fail": n_fail, "warn": n_warn, "verdict": "PASS" if n_fail == 0 else "FAIL"}
    os.makedirs(os.path.join(base, "qa"), exist_ok=True)
    json.dump(result, open(os.path.join(base, "qa", "check_cuts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if as_json: print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            print({"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}[c["status"]], c["id"], c["message"])
            for d in c["detail"][:15]: print("     -", d)
        print(f"\n{result['verdict']}: cuts={len(cuts)} fail={n_fail} warn={n_warn}")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
