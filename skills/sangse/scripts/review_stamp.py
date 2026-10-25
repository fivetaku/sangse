#!/usr/bin/env python3
"""sangse 리뷰 스탬프 — 게이트 2가 본 카피와 지금 카피가 같은지 확인한다. 표준 라이브러리만.

사용법:
  python3 review_stamp.py <sangse/{slug}> record --review qa/sim-review-r{n}.md
  python3 review_stamp.py <sangse/{slug}> verify

record: 리뷰 취합 파일(VERDICT 줄 필수)을 근거로, 지금 cuts.md 컷별 카피(image: 제외)와 legal.md 섹션별
        본문의 SHA-256을 qa/review-stamp.json에 남긴다. 게이트 2 통과 직후, 또는 리뷰 뒤 수정분을
        재리뷰(델타 리뷰)한 직후에 실행한다.
verify: 스탬프 이후 바뀐 컷·legal 섹션을 나열한다. 바뀐 것이 없으면 exit 0, 있거나 스탬프가 없으면 exit 1.
        image: 줄 추가(Step 8)는 카피 변경이 아니므로 무시한다. 사용자 선택 반영·legal 형식 수정도 카피 변경이다 —
        바뀐 단위만 다시 리뷰하고 record 한다.
"""
import datetime
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assemble_html import parse_cuts  # noqa: E402

STAMP = os.path.join("qa", "review-stamp.json")


def _h(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def fingerprint(base_dir):
    units = {}
    cuts_path = os.path.join(base_dir, "cuts.md")
    if os.path.exists(cuts_path):
        for c in parse_cuts(open(cuts_path, encoding="utf-8").read()):
            fields = {k: v for k, v in c["f"].items() if k != "image"}
            units[c["id"]] = _h([c["tpl"], c["q"], c["h"], fields])
    legal_path = os.path.join(base_dir, "legal.md")
    if os.path.exists(legal_path):
        for n, sec in enumerate(re.split(r"(?m)^##\s+", open(legal_path, encoding="utf-8").read())):
            if not sec.strip(): continue
            title = "서두" if n == 0 else sec.partition("\n")[0].strip()
            units[f"legal:{title}"] = _h(sec.strip())
    return units


def verify(base_dir):
    path = os.path.join(base_dir, STAMP)
    if not os.path.exists(path):
        return False, "qa/review-stamp.json 없음 — 게이트 2 통과 뒤 record를 실행하지 않았다"
    old = json.load(open(path, encoding="utf-8"))["units"]
    now = fingerprint(base_dir)
    changed = sorted(k for k in now if k in old and now[k] != old[k])
    added = sorted(k for k in now if k not in old)
    removed = sorted(k for k in old if k not in now)
    if not (changed or added or removed):
        return True, "리뷰 이후 카피 변경 없음"
    parts = []
    if changed: parts.append("바뀜 " + ", ".join(changed))
    if added: parts.append("새로 생김 " + ", ".join(added))
    if removed: parts.append("사라짐 " + ", ".join(removed))
    return False, "; ".join(parts) + " — 이 단위만 다시 리뷰하고 record"


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[1] not in ("record", "verify"):
        print(__doc__, file=sys.stderr); sys.exit(2)
    base_dir = os.path.abspath(args[0])
    if args[1] == "verify":
        ok, detail = verify(base_dir)
        print(("FRESH: " if ok else "STALE: ") + detail)
        sys.exit(0 if ok else 1)
    if "--review" not in args:
        print("ERROR: --review <리뷰 취합 파일> 필요", file=sys.stderr); sys.exit(2)
    review = args[args.index("--review") + 1]
    review_path = review if os.path.isabs(review) else os.path.join(base_dir, review)
    if not os.path.exists(review_path) or not re.search(r"VERDICT:\s*(PASS|FAIL)", open(review_path, encoding="utf-8").read()):
        print(f"ERROR: {review} 가 없거나 VERDICT 줄이 없다 — 실제 리뷰 결과에만 스탬프를 찍는다", file=sys.stderr); sys.exit(2)
    stamp = {"review": os.path.relpath(review_path, base_dir), "recorded_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
             "units": fingerprint(base_dir)}
    os.makedirs(os.path.join(base_dir, "qa"), exist_ok=True)
    json.dump(stamp, open(os.path.join(base_dir, STAMP), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"RECORDED: {len(stamp['units'])}개 단위 ← {stamp['review']}")


if __name__ == "__main__":
    main()
