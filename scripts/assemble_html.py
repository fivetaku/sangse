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
    if not os.path.exists(copy_path):
        print(f"ERROR: {copy_path} 없음", file=sys.stderr); sys.exit(1)
    md = open(copy_path, encoding="utf-8").read()

    images = {}
    ij = os.path.join(base_dir, "images.json")
    if os.path.exists(ij):
        images = json.load(open(ij, encoding="utf-8"))

    report = {"sections": [], "missing_sections": [], "missing_images": [], "placeholders": []}

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
