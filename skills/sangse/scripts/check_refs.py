#!/usr/bin/env python3
"""sangse 레퍼런스 수집 검증 — 수집기의 `ok`를 그대로 믿지 않고 긴 상세 이미지를 실제로 받았는지 본다.

사용법:
  python3 check_refs.py <sangse/{slug}> [--min-long 1500] [--json]

refs/manifest.json(insane-research-refs 결과)을 읽어 페이지마다 다시 판정한다:
  detail          높이 min_long 이상 이미지가 1장 이상 — 상세 원본 확보
  partial:thumbs  수집기는 ok인데 긴 이미지 0장(썸네일·배너만) — 상세 미확보, capture_reference.js 캡처 대상
  partial:empty   수집기는 ok인데 저장 이미지 0장
  그 밖           수집기 상태 그대로(no_large_images, blocked:* 등) — 캡처 대상
저장 수(saved)와 발견 수(found)가 다르면 함께 적는다. 결과는 refs/refs_check.json.
exit 0 = 상세 원본 1페이지 이상, 1 = 상세 원본 0페이지, 2 = manifest 없음/형식 오류.
레퍼런스는 파이프라인을 막는 단계가 아니다 — exit 1이어도 진행하되 보고에 `상세 0/N`으로 쓴다.
"""
import json
import os
import sys


def check(base_dir, min_long=None):
    path = os.path.join(base_dir, "refs", "manifest.json")
    m = json.load(open(path, encoding="utf-8"))
    min_long = min_long or int(m.get("min_long") or 1500)
    pages = []
    for p in m.get("pages", []):
        imgs = p.get("images") or []
        longest = max((int(i.get("h") or 0) for i in imgs), default=0)
        long_n = sum(1 for i in imgs if int(i.get("h") or 0) >= min_long)
        status = p.get("status", "")
        if status == "ok":
            verdict = "detail" if long_n else ("partial:thumbs" if imgs else "partial:empty")
        else:
            verdict = status or "unknown"
        pages.append({"n": p.get("n"), "domain": p.get("domain"), "url": p.get("url"), "collector_status": status,
                      "verdict": verdict, "saved": len(imgs), "found": p.get("found"), "long_images": long_n,
                      "longest_h": longest, "needs_capture": verdict != "detail"})
    detail = sum(1 for p in pages if p["verdict"] == "detail")
    return {"min_long": min_long, "pages": pages, "detail_pages": detail, "total_pages": len(pages),
            "collector_ok": sum(1 for p in pages if p["collector_status"] == "ok"),
            "summary": f"상세 원본 {detail}/{len(pages)} (수집기 ok {sum(1 for p in pages if p['collector_status'] == 'ok')})"}


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr); sys.exit(2)
    base_dir = os.path.abspath(args[0])
    min_long = int(args[args.index("--min-long") + 1]) if "--min-long" in args else None
    try:
        res = check(base_dir, min_long)
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: refs/manifest.json 읽기 실패 — {e}", file=sys.stderr); sys.exit(2)
    json.dump(res, open(os.path.join(base_dir, "refs", "refs_check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if "--json" in args:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for p in res["pages"]:
            mark = "✅" if p["verdict"] == "detail" else "⚠️"
            cnt = f"저장 {p['saved']}" + (f"/발견 {p['found']}" if p["found"] not in (None, p["saved"]) else "")
            print(f"{mark} p{p['n']:02d} {p['domain']} — {p['verdict']} (수집기 {p['collector_status']}, {cnt}, 긴 이미지 {p['long_images']}, 최장 {p['longest_h']}px)")
        print(f"\n{res['summary']} — 상세 미확보 페이지는 capture_reference.js 대상 → refs/refs_check.json")
    sys.exit(0 if res["detail_pages"] else 1)


if __name__ == "__main__":
    main()
