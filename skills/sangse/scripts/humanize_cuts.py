#!/usr/bin/env python3
"""sangse Step 4-1 윤문 — cuts.md의 카피를 Codex CLI(GPT)가 사람답게 재생성하고, 컷별 가드로 걸러 치환한다. 표준 라이브러리만.

사용법:
  python3 humanize_cuts.py <sangse/{slug}> [--category common|food|health_food ...] [--apply] [--model <m>]
                           [--dry-run] [--from-json <gpt-response.json>] [--timeout <sec>]

동작:
  1) cuts.md 파싱 → references/humanize.md의 <!-- PROMPT:BEGIN/END --> 시스템 프롬프트 + 템플릿 한도 + 컷 텍스트로 프롬프트 조립
  2) codex exec 호출 — 응답 스키마(assets/humanize-schema.json)는 프롬프트에 인라인한다. --output-schema는 로컬 프록시(opencodex 등)가
     구조화 출력을 못 받아 스트림이 끊기는 것을 실측(2026-09-03)해 쓰지 않는다. env 프록시는 우회(SANGSE_KEEP_PROXY=1로 해제)
  3) 컷별 가드: 새 숫자 금지 · 플레이스홀더 보존 · 슬롯 한도(cut-templates.json) · 카테고리 금지어(banned-words.json)
     위반 컷은 원문 유지. headline/sub/body/footnote/cta 외 필드는 원본에서 그대로.
  4) cuts.humanized.md + qa/humanize.json 기록. --apply면 cuts.md ← humanized (원본은 cuts.original.md)
종료코드 0 정상(거부 컷이 있어도 0) / 1 GPT 호출·파싱 실패 / 2 입력 오류 / 3 codex 없음
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
TEMPLATES = json.load(open(os.path.join(SKILL, "assets", "cut-templates.json"), encoding="utf-8"))["templates"]
BANNED = json.load(open(os.path.join(SKILL, "assets", "banned-words.json"), encoding="utf-8"))
SCHEMA = os.path.join(SKILL, "assets", "humanize-schema.json")
RULES = os.path.join(SKILL, "references", "humanize.md")

CUT_RE = re.compile(r"^##\s*(C\d{2})\s*[·•\-]\s*([A-Z]\d{1,2})\s*[·•\-]\s*((?:Q\d(?:[·/,]Q\d)*|brand))\s*[·•\-]\s*h\s*=\s*(\d+)\s*$", re.MULTILINE)
PH_RE = re.compile(r"\[(자료 필요|선택|이미지 생성 실패)[^\]]*\]")
NUM_RE = re.compile(r"\d[\d,.]*")  # 숫자만. 조사·단위까지 묶으면 "1회"↔"1회라면"이 다른 숫자로 오탐난다(E2E 실측 2026-09-03)
UNIT_RE = re.compile(r"\d[\d,.]*\s*[A-Za-z가-힣%]{1,3}")
TEXT_FIELDS = ("headline", "sub", "body", "footnote", "cta")


def klen(s):
    return len(re.sub(r"\s", "", s or ""))


def load_prompt():
    md = open(RULES, encoding="utf-8").read()
    m = re.search(r"<!-- PROMPT:BEGIN -->\n(.*?)<!-- PROMPT:END -->", md, re.DOTALL)
    if not m:
        sys.exit("ERROR: humanize.md에 PROMPT:BEGIN/END 블록이 없다")
    return m.group(1).strip()


def parse(md):
    """cuts.md → (header_text, [cut]) — cut = {id,tpl,q,h,heading,lines:[(key,val|list)], order:[keys]}"""
    ms = list(CUT_RE.finditer(md))
    if not ms:
        return md, []
    header = md[: ms[0].start()]
    cuts = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(md)
        block = md[m.end():end]
        cut = {"id": m.group(1), "tpl": m.group(2), "q": m.group(3), "h": int(m.group(4)), "heading": m.group(0), "fields": {}, "order": [], "tail": ""}
        lines = block.split("\n")
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
                        if lines[j].strip():
                            body.append(lines[j].strip())
                        j += 1
                    cut["fields"][key] = body
                    cut["order"].append(key)
                    continue
                cut["fields"][key] = val
                cut["order"].append(key)
            j += 1
        cuts.append(cut)
    return header, cuts


def render(header, cuts):
    out = [header.rstrip("\n"), ""]
    for c in cuts:
        out.append(c["heading"])
        for k in c["order"]:
            v = c["fields"][k]
            if isinstance(v, list):
                out.append(f"{k}: |")
                out.extend(f"  {ln}" for ln in v)
            else:
                out.append(f"{k}: {v}")
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def cut_text(c, fields=TEXT_FIELDS):
    parts = []
    for k in fields:
        v = c["fields"].get(k)
        if isinstance(v, list):
            parts.extend(v)
        elif v:
            parts.append(v)
    return "\n".join(parts)


def numbers(s):
    return {re.sub(r"\s", "", n) for n in NUM_RE.findall(s or "")}


def guard(orig, new_fields, cats):
    """컷 하나의 재생성 필드를 검사. 위반 사유 리스트 반환(빈 리스트 = 통과)."""
    t = TEMPLATES.get(orig["tpl"], {})
    reasons = []
    merged = dict(orig["fields"])
    merged.update(new_fields)
    new_text = cut_text({"fields": merged})
    old_text = cut_text(orig)
    # 숫자: 새 숫자 금지 (원본 컷 시트 전체 기준은 호출자가 all_numbers로 넘김)
    extra = numbers(new_text) - guard.all_numbers
    if extra:
        reasons.append(f"숫자 신규 유입: {sorted(extra)[:3]}")
    # 숫자+단위 토큰이 원본에 없으면 경고(거부 아님): "10 mL"→"10일" 같은 단위 변조는 게이트 1·리뷰어가 본다
    new_units = {re.sub(r"\s", "", u) for u in UNIT_RE.findall(new_text)}
    guard.warnings = sorted(u for u in new_units if u not in guard.all_units)
    # 플레이스홀더 보존
    for ph in [m.group(0) for m in PH_RE.finditer(old_text)]:
        if ph not in new_text:
            reasons.append(f"플레이스홀더 소실: {ph[:30]}")
    # 슬롯 한도
    # 슬롯 한도는 바뀐 필드에만 적용한다(원문 초과분은 게이트 1의 몫)
    head = new_fields.get("headline", "")
    rows = [r for r in head.split("|") if r.strip()] if isinstance(head, str) else []
    if t.get("headline_max", 0) == 0 and rows:
        reasons.append("텍스트 없는 템플릿에 headline 생성")
    if len(rows) > 3:
        reasons.append(f"headline {len(rows)}행 > 3")
    for r in rows:
        if t.get("headline_max") and klen(r) > t["headline_max"]:
            reasons.append(f"headline '{r.strip()}' {klen(r)}자 > {t['headline_max']}")
    sub = new_fields.get("sub", "")
    if isinstance(sub, str) and t.get("sub_max") and klen(sub) > t["sub_max"]:
        reasons.append(f"sub {klen(sub)}자 > {t['sub_max']}")
    body = new_fields.get("body", [])
    if isinstance(body, list):
        if t.get("body_lines_max") and len(body) > t["body_lines_max"]:
            reasons.append(f"body {len(body)}줄 > {t['body_lines_max']}")
        for ln in body:
            if t.get("line_max") and klen(ln) > t["line_max"]:
                reasons.append(f"body 줄 '{ln[:12]}…' {klen(ln)}자 > {t['line_max']}")
    for k in ("footnote", "cta"):
        v = new_fields.get(k)
        if isinstance(v, str) and t.get("line_max") and klen(v) > t["line_max"] + 10:
            reasons.append(f"{k} {klen(v)}자 > {t['line_max'] + 10}")
    # 금지어(원문에 없던 것만)
    for cat in cats:
        for w in BANNED.get(cat, {}).get("ban", []):
            if w in new_text and w not in old_text:
                reasons.append(f"금지어 유입({cat}): {w}")
    return reasons


def build_prompt(header, cuts, cats):
    sysp = load_prompt()
    tone = re.search(r"^tone:\s*(.+)$", header, re.MULTILINE)
    style = re.search(r"^style:\s*(.+)$", header, re.MULTILINE)
    if not tone and style:
        pp = os.path.join(SKILL, "assets", "style-packs", style.group(1).strip() + ".json")
        if os.path.exists(pp):
            pt = json.load(open(pp, encoding="utf-8")).get("typography", {}).get("tone_default")
            if pt: tone = re.match(r"(.+)", pt)
    limits = {}
    for c in cuts:
        t = TEMPLATES.get(c["tpl"])
        if t:
            limits[c["tpl"]] = {k: t.get(k) for k in ("headline_max", "sub_max", "body_lines_max", "line_max")}
    bans = sorted({w for cat in cats for w in BANNED.get(cat, {}).get("ban", [])})
    payload = []
    for c in cuts:
        f = {k: c["fields"][k] for k in TEXT_FIELDS if k in c["fields"]}
        payload.append({"id": c["id"], "template": c["tpl"], "q": c["q"], **f})
    return (
        f"{sysp}\n\n### 이번 입력\n"
        f"- tone: {tone.group(1).strip() if tone else '(미지정 — 입력 문체 유지)'}\n"
        f"- 템플릿 슬롯 한도(공백 제외 글자 수, headline_max는 행당·최대 3행): {json.dumps(limits, ensure_ascii=False)}\n"
        f"- 카테고리 금지어(새로 넣지 말 것): {json.dumps(bans, ensure_ascii=False)}\n\n"
        f"### 컷 시트 (JSON)\n{json.dumps(payload, ensure_ascii=False, indent=1)}\n\n"
        f"### 출력 스키마 (이 JSON Schema에 맞는 JSON 객체 하나만, 코드블록·설명 없이)\n{open(SCHEMA, encoding='utf-8').read().strip()}\n"
    )


def codex_bin():
    return shutil.which("codex")


def call_codex(prompt, model=None, timeout=600):
    out_path = tempfile.mktemp(prefix="humanize-out-", suffix=".json")
    cmd = [codex_bin(), "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-o", out_path]
    if model:
        cmd += ["-m", model]
    cmd.append(prompt)
    env = dict(os.environ)
    if os.environ.get("SANGSE_KEEP_PROXY", "0") != "1":
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
            env.pop(k, None)
    try:
        r = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        sys.exit(f"ERROR: codex exec {timeout}s 타임아웃")
    if r.returncode != 0 or not os.path.exists(out_path):
        sys.stderr.write((r.stderr or "")[-2000:])
        sys.exit(f"ERROR: codex exec 실패 (exit {r.returncode})")
    raw = open(out_path, encoding="utf-8").read().strip()
    return parse_response(raw)


def parse_response(raw):
    """코드블록·앞뒤 설명을 벗겨 첫 '{'~마지막 '}'를 JSON으로 읽는다."""
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    i, j = raw.find("{"), raw.rfind("}")
    if i < 0 or j <= i:
        sys.exit(f"ERROR: GPT 응답에 JSON 객체가 없다:\n{raw[:400]}")
    try:
        return json.loads(raw[i:j + 1])
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: GPT 응답이 JSON이 아니다: {e}\n{raw[:400]}")


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("--"):
        print(__doc__, file=sys.stderr); sys.exit(2)
    base = os.path.abspath(a[0])
    cats = ["common"]
    if "--category" in a:
        i = a.index("--category") + 1
        while i < len(a) and not a[i].startswith("--"):
            cats.append(a[i]); i += 1
    model = a[a.index("--model") + 1] if "--model" in a else None
    timeout = int(a[a.index("--timeout") + 1]) if "--timeout" in a else 600
    apply = "--apply" in a
    dry = "--dry-run" in a
    from_json = a[a.index("--from-json") + 1] if "--from-json" in a else None

    cp = os.path.join(base, "cuts.md")
    if not os.path.exists(cp):
        sys.exit(f"ERROR: {cp} 없음")
    md = open(cp, encoding="utf-8").read()
    header, cuts = parse(md)
    if not cuts:
        sys.exit("ERROR: cuts.md에서 컷을 찾지 못했다 (## Cnn · 템플릿 · Q · h=px)")
    prompt = build_prompt(header, cuts, cats)
    if dry:
        print(prompt); return

    if from_json:
        resp = json.load(open(from_json, encoding="utf-8"))
    else:
        if not codex_bin():
            print("SKIP: codex CLI 없음 — 윤문 생략", file=sys.stderr); sys.exit(3)
        resp = call_codex(prompt, model, timeout)

    guard.all_numbers = numbers(md)
    guard.all_units = {re.sub(r"\s", "", u) for u in UNIT_RE.findall(md)}
    guard.warnings = []
    by_id = {c["id"]: c for c in cuts}
    accepted, rejected, unchanged = [], [], []
    meanings = {}
    new_cuts = []
    for c in cuts:
        r = next((x for x in resp.get("cuts", []) if x.get("id") == c["id"]), None)
        nc = {**c, "fields": dict(c["fields"]), "order": list(c["order"])}
        if not r:
            unchanged.append({"id": c["id"], "note": "GPT 응답에 없음"}); new_cuts.append(nc); continue
        meanings[c["id"]] = r.get("meaning", "")
        if r.get("unchanged"):
            unchanged.append({"id": c["id"], "note": r.get("note", "")}); new_cuts.append(nc); continue
        new_fields = {}
        for k in TEXT_FIELDS:
            if k in r and r[k] is not None:
                if k not in c["fields"]:
                    continue  # 원문에 없던 필드는 만들지 않는다
                v = r[k]
                if k == "body":
                    v = [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else [s.strip() for s in str(v).split("\n") if s.strip()]
                else:
                    v = str(v).strip()
                if v != c["fields"][k]:
                    new_fields[k] = v
        if not new_fields:
            unchanged.append({"id": c["id"], "note": "변경 없음"}); new_cuts.append(nc); continue
        reasons = guard(c, new_fields, cats)
        if reasons:
            rejected.append({"id": c["id"], "reasons": reasons, "proposed": new_fields})
        else:
            nc["fields"].update(new_fields)
            accepted.append({"id": c["id"], "fields": sorted(new_fields), "unit_warnings": guard.warnings})
        new_cuts.append(nc)

    old_all = "\n".join(cut_text(c) for c in cuts)
    new_all = "\n".join(cut_text(c) for c in new_cuts)
    change_rate = round(1 - difflib.SequenceMatcher(None, old_all, new_all).ratio(), 3)
    out_md = render(header, new_cuts)
    open(os.path.join(base, "cuts.humanized.md"), "w", encoding="utf-8").write(out_md)
    os.makedirs(os.path.join(base, "qa"), exist_ok=True)
    report = {
        "cuts": len(cuts), "accepted": accepted, "rejected": rejected, "unchanged": unchanged,
        "change_rate": change_rate, "change_rate_warn": change_rate > 0.5,
        "meanings": meanings, "gpt_notes": resp.get("notes", []),
        "applied": False, "category": cats, "model": model or "codex default",
    }
    if apply:
        shutil.copyfile(cp, os.path.join(base, "cuts.original.md"))
        open(cp, "w", encoding="utf-8").write(out_md)
        report["applied"] = True
    json.dump(report, open(os.path.join(base, "qa", "humanize.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"HUMANIZE: cuts={len(cuts)} accepted={len(accepted)} rejected={len(rejected)} unchanged={len(unchanged)} "
          f"change_rate={change_rate}{' (WARN >0.5)' if change_rate > 0.5 else ''} applied={report['applied']}")
    for r in rejected:
        print(f"  - {r['id']} 거부: {'; '.join(r['reasons'])}")


if __name__ == "__main__":
    main()
