#!/usr/bin/env python3
"""copy.md (+ images.json) -> index.html 조립기. 표준 라이브러리만 사용.

사용법:
  python3 assemble_html.py <sangse/{slug} 디렉토리> [--platform web|smartstore|kmong] [--template <html>]

입력 규약:
  - copy.md: '## Q1' ~ '## Q8' 헤딩으로 섹션 구분. 헤딩 뒤 텍스트는 섹션 제목.
      본문은 단순 마크다운(문단, '-' 불릿, **굵게**, | 표 |, ![alt](path), [[CTA: 문구 | url]]).
      '[자료 필요: ...]' / '[선택: ...]' / '[이미지 생성 실패 ...]' 는 노란 플레이스홀더 박스로 렌더.
  - images.json (선택): {"Q1": "/abs/or/rel/path.png", ...}. 섹션 본문 위에 삽입.
      copy.md 안에 이미지가 이미 있으면 images.json 항목은 건너뜀.
  - cuts.md (있으면 컷 모드): '## Cnn · 템플릿 · Q · h=px' 블록의 image: 를 폭 100%로 세로 나열. 이미지 없는 컷은
      bg/headline/sub/body/footnote로 텍스트 플레이스홀더 블록 렌더. 뒤에 legal.md(마크다운)를 HTML 표·불릿으로 붙인다.
출력:
  - index.html (같은 디렉토리). 이미지 경로는 index.html 기준 상대경로로 변환.
  - 누락 이미지·누락 섹션·잔존 플레이스홀더는 stderr 경고 + stdout JSON 요약.
"""
import html
import json
import os
import re
import sys

SECTION_RE = re.compile(r"^##\s*(Q[1-8])\b[.:\s-]*(.*)$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"\[(자료 필요|선택|이미지 생성 실패)[^\]]*\]")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
CTA_RE = re.compile(r"\[\[CTA:\s*([^|\]]+?)\s*(?:\|\s*([^\]]+?))?\s*\]\]")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

PLATFORM_WIDTH = {"web": 720, "smartstore": 860, "kmong": 720, "insta": 600}


def rel(path, base_dir):
    if not path or path.startswith(("http://", "https://", "data:")):
        return path, path  # 원격/인라인 경로는 존재 검사 없이 그대로
    abs_path = path if os.path.isabs(path) else os.path.normpath(os.path.join(base_dir, path))
    return os.path.relpath(abs_path, base_dir).replace(os.sep, "/"), abs_path


def inline(text):
    text = html.escape(text, quote=False)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = PLACEHOLDER_RE.sub(lambda m: f'<mark class="todo-inline">{m.group(0)}</mark>', text)
    return text


def render_block(md, base_dir, report):
    """단순 마크다운 -> HTML 조각."""
    out = []
    para = []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    lines = md.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            flush(); i += 1; continue
        m = IMG_RE.fullmatch(line.strip())
        if m:
            flush()
            r, ap = rel(m.group(2), base_dir)
            if not ap.startswith(("http://", "https://", "data:")) and not os.path.exists(ap):
                report["missing_images"].append(m.group(2))
            out.append(f'<figure><img src="{html.escape(r)}" alt="{html.escape(m.group(1))}" loading="lazy"></figure>')
            i += 1; continue
        m = CTA_RE.search(line)
        if m:
            flush()
            label, href = m.group(1), (m.group(2) or "#")
            out.append(f'<a class="cta" href="{html.escape(href)}">{inline(label)}</a>')
            i += 1; continue
        if PLACEHOLDER_RE.fullmatch(line.strip()):
            flush()
            report["placeholders"].append(line.strip())
            out.append(f'<div class="todo">{inline(line.strip())}</div>')
            i += 1; continue
        if line.lstrip().startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                head_cells, body_rows = rows[0], rows[1:]
                thead = "<tr>" + "".join(f"<th>{inline(c)}</th>" for c in head_cells) + "</tr>"
                tbody = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body_rows)
                out.append(f'<table class="spec"><thead>{thead}</thead><tbody>{tbody}</tbody></table>')
            continue
        if line.lstrip().startswith(("- ", "* ")):
            flush()
            items = []
            while i < len(lines) and lines[i].lstrip().startswith(("- ", "* ")):
                items.append("<li>" + inline(lines[i].lstrip()[2:]) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if line.startswith("### "):
            flush(); out.append("<h3>" + inline(line[4:]) + "</h3>"); i += 1; continue
        # 문단 내부 플레이스홀더도 기록
        for m2 in PLACEHOLDER_RE.finditer(line):
            report["placeholders"].append(m2.group(0))
        para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


CUT_RE = re.compile(r"^##\s*(C\d{2})\s*[·•\-]\s*([A-Z]\d{1,2})\s*[·•\-]\s*((?:Q\d(?:[·/,]Q\d)*|brand))\s*[·•\-]\s*h\s*=\s*(\d+)\s*$", re.MULTILINE)


def parse_cuts(md):
    cuts = []
    ms = list(CUT_RE.finditer(md))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(md)
        lines = md[m.end():end].splitlines()
        f = {}
        j = 0
        while j < len(lines):
            km = re.match(r"^([a-z_]+):\s*(.*)$", lines[j])
            if km:
                key, val = km.group(1), km.group(2).strip()
                if val == "|":
                    body = []
                    j += 1
                    while j < len(lines) and (lines[j].startswith("  ") or not lines[j].strip()):
                        if lines[j].strip(): body.append(lines[j].strip())
                        j += 1
                    f[key] = body
                    continue
                f[key] = val
            j += 1
        cuts.append({"id": m.group(1), "tpl": m.group(2), "q": m.group(3).strip(), "h": int(m.group(4)), "f": f})
    return cuts


def render_cuts(cuts, base_dir, report):
    parts = []
    for c in cuts:
        f = c["f"]
        img = f.get("image")
        if img and not PLACEHOLDER_RE.search(img):
            r, ap = rel(img, base_dir)
            if not os.path.exists(ap):
                report["missing_images"].append(f"{c['id']}: {img}")
            parts.append(f'<figure class="cut" id="{c["id"].lower()}" data-tpl="{c["tpl"]}" data-q="{html.escape(c["q"])}"><img src="{html.escape(r)}" alt="{html.escape((f.get("headline") or "").replace("|", " "))}"></figure>')
            continue
        bg = f.get("bg") or "#f4f4f6"
        dark = False
        m = re.match(r"#([0-9a-fA-F]{6})", bg)
        if m:
            rr, gg, bb = int(m.group(1)[0:2], 16), int(m.group(1)[2:4], 16), int(m.group(1)[4:6], 16)
            dark = (0.299 * rr + 0.587 * gg + 0.114 * bb) < 140
        head = "<br>".join(inline(x.strip()) for x in (f.get("headline") or "").split("|") if x.strip())
        body = f.get("body") or []
        if isinstance(body, str): body = [body]
        for x in [f.get("headline", ""), f.get("sub", "")] + list(body) + [f.get("footnote", "")]:
            for m2 in PLACEHOLDER_RE.finditer(str(x)): report["placeholders"].append(m2.group(0))
        parts.append(
            f'<section class="cut-ph{" dark" if dark else ""}" id="{c["id"].lower()}" data-tpl="{c["tpl"]}" style="background:{html.escape(bg)};min-height:{int(c["h"] * 0.6)}px">'
            f'<div class="cut-meta">{c["id"]} · {c["tpl"]} · {html.escape(c["q"])} · 이미지 미생성</div>'
            f'<h2>{head}</h2>' + (f'<p class="sub">{inline(f["sub"])}</p>' if f.get("sub") else "") +
            "".join(f"<p>{inline(x)}</p>" for x in body) +
            (f'<p class="foot">{inline(f["footnote"])}</p>' if f.get("footnote") else "") +
            (f'<p class="visual">비주얼: {inline(f["visual"])}</p>' if f.get("visual") else "") + "</section>")
    return "\n".join(parts)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr); sys.exit(2)
    base_dir = os.path.abspath(args[0])
    platform = "web"
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "template.html")
    if "--platform" in args:
        platform = args[args.index("--platform") + 1]
    if "--template" in args:
        template_path = args[args.index("--template") + 1]

    copy_path = os.path.join(base_dir, "copy.md")
    if not os.path.exists(copy_path) and not os.path.exists(os.path.join(base_dir, "cuts.md")):
        print(f"ERROR: {copy_path} 또는 cuts.md 없음", file=sys.stderr); sys.exit(1)
    md = open(copy_path, encoding="utf-8").read() if os.path.exists(copy_path) else ""

    images = {}
    ij = os.path.join(base_dir, "images.json")
    if os.path.exists(ij):
        images = json.load(open(ij, encoding="utf-8"))

    report = {"sections": [], "missing_sections": [], "missing_images": [], "placeholders": []}

    cuts_path = os.path.join(base_dir, "cuts.md")
    if os.path.exists(cuts_path):
        cmd = open(cuts_path, encoding="utf-8").read()
        cuts = parse_cuts(cmd)
        report["mode"] = "cuts"; report["cuts"] = [c["id"] for c in cuts]
        if "--platform" not in args:
            pm = re.search(r"^platform:\s*(\w+)", cmd, re.MULTILINE)
            if pm: platform = pm.group(1)
        title_m = re.search(r"^#\s+(.+)$", cmd, re.MULTILINE)
        page_title = title_m.group(1).strip() if title_m else "상세페이지"
        legal_path = os.path.join(base_dir, "legal.md")
        legal_html = ""
        if os.path.exists(legal_path):
            lmd = open(legal_path, encoding="utf-8").read()
            secs = re.split(r"(?m)^##\s+", lmd)
            blocks = []
            for sec in secs:
                if not sec.strip(): continue
                t, _, b = sec.partition("\n")
                blocks.append(f'<section class="legal"><h2>{inline(t.strip())}</h2>{render_block(b, base_dir, report)}</section>')
            legal_html = "\n".join(blocks)
        else:
            report["placeholders"].append("[자료 필요: legal.md]")
        body_html = f'<div class="cutsheet">{render_cuts(cuts, base_dir, report)}</div>\n{legal_html}'
        template = open(template_path, encoding="utf-8").read()
        out = (template.replace("{{TITLE}}", html.escape(page_title)).replace("{{WIDTH}}", str(PLATFORM_WIDTH.get(platform, 720)))
                       .replace("{{PLATFORM}}", platform).replace("{{SECTIONS}}", body_html))
        out_path = os.path.join(base_dir, "index.html")
        open(out_path, "w", encoding="utf-8").write(out)
        for p_ in report["missing_images"]: print(f"WARN: 이미지 파일 없음: {p_}", file=sys.stderr)
        if report["placeholders"]: print(f"WARN: 플레이스홀더 {len(report['placeholders'])}개 잔존", file=sys.stderr)
        report["output"] = out_path
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    matches = list(SECTION_RE.finditer(md))
    sections = []
    for idx, m in enumerate(matches):
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md)
        sections.append((m.group(1), m.group(2).strip(), md[start:end]))
    found = {s[0] for s in sections}
    for n in range(1, 9):
        q = f"Q{n}"
        if q not in found:
            report["missing_sections"].append(q)

    title_m = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
    page_title = title_m.group(1).strip() if title_m else "상세페이지"

    parts = []
    for q, heading, body in sections:
        report["sections"].append(q)
        img_html = ""
        if q in images and not IMG_RE.search(body):
            r, ap = rel(images[q], base_dir)
            if not ap.startswith(("http://", "https://", "data:")) and not os.path.exists(ap):
                report["missing_images"].append(images[q])
            img_html = f'<figure><img src="{html.escape(r)}" alt="{html.escape(heading)}" loading="lazy"></figure>'
        hero = " hero" if q == "Q1" else ""
        parts.append(
            f'<section class="sec{hero}" id="{q.lower()}">\n{img_html}\n<h2>{inline(heading)}</h2>\n{render_block(body, base_dir, report)}\n</section>'
        )

    template = open(template_path, encoding="utf-8").read()
    out = (template.replace("{{TITLE}}", html.escape(page_title))
                   .replace("{{WIDTH}}", str(PLATFORM_WIDTH.get(platform, 720)))
                   .replace("{{PLATFORM}}", platform)
                   .replace("{{SECTIONS}}", "\n\n".join(parts)))
    out_path = os.path.join(base_dir, "index.html")
    open(out_path, "w", encoding="utf-8").write(out)

    for q in report["missing_sections"]:
        print(f"WARN: 섹션 {q} 없음", file=sys.stderr)
    for p in report["missing_images"]:
        print(f"WARN: 이미지 파일 없음: {p}", file=sys.stderr)
    if report["placeholders"]:
        print(f"WARN: 플레이스홀더 {len(report['placeholders'])}개 잔존", file=sys.stderr)
    report["output"] = out_path
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
