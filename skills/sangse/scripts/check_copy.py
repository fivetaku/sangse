#!/usr/bin/env python3
"""sangse 자동 검사 게이트 — copy.md를 결정론적으로 판정한다. 표준 라이브러리만.

사용법:
  python3 check_copy.py <sangse/{slug} 디렉토리> [--category common|food|health_food|cosmetics ...] [--platform web|smartstore|kmong] [--json]

검사 항목 (review-checklist.md C1~C10 중 기계 판정 가능한 것):
  C1  Q1~Q8 헤딩 8개, 순서 정확
  C2  Q1 섹션에 창업자 언어(첫 화면 금지어) 없음
  C3  copy.md의 숫자(가격·수량·함량·기간)가 raw-input.md 또는 intake-checklist.md에 존재 (출처 추적).
      합계·환산 같은 파생 수치는 intake-checklist.md에 "파생: 300 mL = 10 mL × 30포" 식으로 계산식을 적어야 통과
  C5  Q8의 날짜·할인율이 raw-input에 존재 (C3에 포함)
  C7  섹션 헤드라인 20자 이내
  C8  [[CTA: …]] 3개 이상, 문구 동일
  C9  카테고리 금지어 (assets/banned-words.json) — ban=FAIL, warn=WARN
  C10 Q6에 사양 표(|---|) 존재, 물성 플랫폼이면 Q7 아래 ### FAQ 존재
  P   플레이스홀더([자료 필요]/[선택]/[이미지 생성 실패]) 목록 — FAIL 아님, 보고용
  I   images.json이 있으면 파일 실존 확인

종료코드: 0 = PASS(FAIL 0), 1 = FAIL 있음, 2 = 입력 오류
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BANNED = os.path.join(HERE, "..", "assets", "banned-words.json")

SECTION_RE = re.compile(r"^##\s*(Q[1-8])\b[.:\s-]*(.*)$", re.MULTILINE)
CTA_RE = re.compile(r"\[\[CTA:\s*([^|\]]+?)\s*(?:\|[^\]]*)?\]\]")
PLACEHOLDER_RE = re.compile(r"\[(자료 필요|선택|이미지 생성 실패)[^\]]*\]")
NUM_RE = re.compile(r"\d[\d,\.]*\s*(?:원|%|mg|g|mL|ml|kcal|포|캡슐|정|일|개월|곳|칸|박스|명|년근|월|x|×)?")
PHYSICAL_PLATFORMS = {"smartstore", "kmong", "funding", "coupang"}


def split_sections(md):
    ms = list(SECTION_RE.finditer(md))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(md)
        out.append((m.group(1), m.group(2).strip(), md[m.end():end]))
    return out


def norm_num(tok):
    return re.sub(r"[,\s]", "", tok)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    base = os.path.abspath(args[0])
    cats = ["common"]
    platform = "web"
    as_json = "--json" in args
    if "--category" in args:
        i = args.index("--category") + 1
        while i < len(args) and not args[i].startswith("--"):
            cats.append(args[i]); i += 1
    if "--platform" in args:
        platform = args[args.index("--platform") + 1]

    copy_path = os.path.join(base, "copy.md")
    if not os.path.exists(copy_path):
        print(f"ERROR: {copy_path} 없음", file=sys.stderr); sys.exit(2)
    md = open(copy_path, encoding="utf-8").read()
    sources = ""
    for name in ("raw-input.md", "intake-checklist.md"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            sources += open(p, encoding="utf-8").read() + "\n"
    banned = json.load(open(BANNED, encoding="utf-8"))

    checks = []
    def add(cid, status, msg, detail=None):
        checks.append({"id": cid, "status": status, "message": msg, "detail": detail or []})

    secs = split_sections(md)
    ids = [s[0] for s in secs]
    # C1
    if ids == [f"Q{i}" for i in range(1, 9)]:
        add("C1", "PASS", "Q1~Q8 순서 정상")
    else:
        add("C1", "FAIL", f"섹션 순서/누락: {ids}")
    body = {s[0]: s[2] for s in secs}
    head = {s[0]: s[1] for s in secs}

    # C2 — Q1 hero banned words
    q1 = (head.get("Q1", "") + "\n" + body.get("Q1", ""))
    hero = banned.get("q1_hero", {})
    hits = [w for w in hero.get("ban", []) if re.search(w, q1)]
    warns = [w for w in hero.get("warn", []) if re.search(w, q1)]
    if hits:
        add("C2", "FAIL", "Q1 첫 화면에 창업자 언어", hits)
    elif warns:
        add("C2", "WARN", "Q1에 자기 서술 경고", warns)
    else:
        add("C2", "PASS", "Q1 금지어 없음")

    # C3 — number traceability
    src_nums = {norm_num(t) for t in NUM_RE.findall(sources)}
    src_digits = set(re.findall(r"\d[\d,\.]*", sources))
    src_digits = {norm_num(d) for d in src_digits}
    untraced = []
    for q, h, b in secs:
        text = h + "\n" + b
        text = PLACEHOLDER_RE.sub("", text)
        text = re.sub(r"(?m)^\s*\d+\.\s", "", text)  # 번호 목록 마커 제외
        for tok in re.findall(r"\d[\d,\.]*", text):
            n = norm_num(tok)
            if len(n) == 1 and n in "1234":  # 목록 번호·단계 번호 제외
                continue
            if n not in src_digits:
                untraced.append(f"{q}: {tok}")
    if not sources:
        add("C3", "WARN", "raw-input.md/intake-checklist.md 없음 — 출처 추적 불가")
    elif untraced:
        add("C3", "FAIL", f"출처 없는 숫자 {len(untraced)}개", sorted(set(untraced)))
    else:
        add("C3", "PASS", "모든 숫자가 입력에 존재")

    # C7 — headline length
    long_heads = [f"{q} ({len(h)}자): {h}" for q, h, _ in secs if len(h) > 20]
    add("C7", "FAIL" if long_heads else "PASS", "헤드라인 20자 초과" if long_heads else "헤드라인 길이 정상", long_heads)

    # C8 — CTA
    ctas = [c.strip() for c in CTA_RE.findall(md)]
    if len(ctas) < 3:
        add("C8", "FAIL", f"CTA {len(ctas)}개 (3개 이상 필요)", ctas)
    elif len(set(ctas)) > 1:
        add("C8", "WARN", "CTA 문구가 섹션마다 다름", sorted(set(ctas)))
    elif re.fullmatch(r"(구매하기|결제하기|바로 구매|주문하기)", ctas[0]):
        add("C8", "WARN", "CTA가 행동 단독 문구", ctas)
    else:
        add("C8", "PASS", f"CTA {len(ctas)}회, 문구 동일: {ctas[0]}")

    # C9 — category banned words (whole copy, excluding placeholders)
    clean = PLACEHOLDER_RE.sub("", md)
    fails, warnings = [], []
    for cat in cats:
        rules = banned.get(cat)
        if not rules:
            warnings.append(f"카테고리 '{cat}' 사전 없음")
            continue
        for w in rules.get("ban", []):
            for m in re.finditer(w, clean):
                line = clean.count("\n", 0, m.start()) + 1
                fails.append(f"[{cat}] L{line}: '{m.group(0)}'")
        for w in rules.get("warn", []):
            for m in re.finditer(w, clean):
                line = clean.count("\n", 0, m.start()) + 1
                warnings.append(f"[{cat}] L{line}: '{m.group(0)}'")
    if fails:
        add("C9", "FAIL", f"금지어 {len(fails)}건", fails)
    elif warnings:
        add("C9", "WARN", f"경고어 {len(warnings)}건 — 문맥 확인", warnings)
    else:
        add("C9", "PASS", f"금지어 없음 (카테고리: {', '.join(cats)})")

    # C10 — spec table & FAQ
    has_table = "|---" in body.get("Q6", "") or "| ---" in body.get("Q6", "")
    has_faq = bool(re.search(r"^###\s*FAQ", body.get("Q7", ""), re.MULTILINE))
    if not has_table:
        add("C10", "FAIL", "Q6에 사양 표 없음")
    elif platform in PHYSICAL_PLATFORMS and not has_faq:
        add("C10", "FAIL", f"{platform}인데 Q7 아래 ### FAQ 없음")
    else:
        add("C10", "PASS", "사양 표" + (" + FAQ" if has_faq else "") + " 존재")

    # P — placeholders
    phs = PLACEHOLDER_RE.findall(md)
    ph_list = [m.group(0) for m in PLACEHOLDER_RE.finditer(md)]
    add("P", "INFO", f"플레이스홀더 {len(ph_list)}개", ph_list)

    # I — images
    ij = os.path.join(base, "images.json")
    if os.path.exists(ij):
        imgs = json.load(open(ij, encoding="utf-8"))
        missing = [f"{k}: {v}" for k, v in imgs.items() if not os.path.exists(os.path.join(base, v))]
        add("I", "FAIL" if missing else "PASS", "이미지 파일 누락" if missing else f"이미지 {len(imgs)}장 실존", missing)
    else:
        add("I", "INFO", "images.json 없음 (이미지 단계 전)")

    n_fail = sum(1 for c in checks if c["status"] == "FAIL")
    n_warn = sum(1 for c in checks if c["status"] == "WARN")
    result = {"path": copy_path, "category": cats, "platform": platform, "checks": checks,
              "fail": n_fail, "warn": n_warn, "verdict": "PASS" if n_fail == 0 else "FAIL"}
    qa_dir = os.path.join(base, "qa")
    os.makedirs(qa_dir, exist_ok=True)
    json.dump(result, open(os.path.join(qa_dir, "check_copy.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            mark = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}[c["status"]]
            print(f"{mark} {c['id']} {c['message']}")
            for d in c["detail"][:12]:
                print(f"     - {d}")
        print(f"\n{result['verdict']}: fail={n_fail} warn={n_warn} → {os.path.join(qa_dir, 'check_copy.json')}")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
