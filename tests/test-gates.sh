#!/usr/bin/env bash
#
# test-gates.sh — sangse 결정론 게이트 회귀 테스트
#
# examples/ 3종(가상 건기식)을 픽스처로 삼아 다음을 고정한다:
#   1) check_cuts.py(게이트 1)가 각 예시에서 PASS(exit 0)하고 qa/check_cuts.json에 verdict=PASS를 남긴다
#   2) assemble_html.py 컷 모드가 index.html을 만들고, 컷 이미지 14장이 전부 <img>로 들어간다
#   3) check_deps.sh가 이 머신에서 exit 0 (필수 의존성 OK) — 없으면 SKIP(환경 문제, 코드 결함 아님)
#   4) SKILL.md·commands/sangse.md 프런트매터 계약: AskUserQuestion이 allowed-tools에 없다
#
# 예시 폴더는 절대 건드리지 않는다 — 임시 디렉토리로 복사한 뒤 돌린다.
# Usage: bash tests/test-gates.sh
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPTS="$PLUGIN_DIR/skills/sangse/scripts"
EXAMPLES="$PLUGIN_DIR/examples"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS=0; FAIL=0; SKIP=0
ok()   { PASS=$((PASS+1)); printf '  \033[0;32m✓\033[0m %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  \033[0;31m✗\033[0m %s\n     %s\n' "$1" "$2"; }
skip() { SKIP=$((SKIP+1)); printf '  \033[0;33m-\033[0m %s (skip: %s)\n' "$1" "$2"; }

command -v python3 >/dev/null 2>&1 || { echo "python3 필요"; exit 1; }

echo
echo "sangse 게이트 회귀"
echo "────────────────────────────────────────"

FIXTURES=(punggi-red-ginseng-stick gwangyang-maesil-jelly jeju-greentea-catechin)

for ex in "${FIXTURES[@]}"; do
  echo "[$ex]"
  SRC="$EXAMPLES/$ex"
  if [ ! -f "$SRC/cuts.md" ]; then bad "픽스처 존재" "$SRC/cuts.md 없음"; continue; fi
  W="$TMP/$ex"; mkdir -p "$W"; cp -R "$SRC/." "$W/"
  rm -f "$W/index.html" "$W/qa/check_cuts.json"

  # 1) 게이트 1
  python3 "$SCRIPTS/check_cuts.py" "$W" --category health_food --platform smartstore >"$W/.gate1.out" 2>"$W/.gate1.err"
  rc=$?
  if [ "$rc" -eq 0 ] && grep -q '^PASS:' "$W/.gate1.out"; then
    ok "check_cuts.py exit 0 + PASS"
  else
    bad "check_cuts.py" "exit=$rc — $(tail -1 "$W/.gate1.out" 2>/dev/null)$(tail -1 "$W/.gate1.err" 2>/dev/null)"
  fi
  if [ -f "$W/qa/check_cuts.json" ] && python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('verdict')=='PASS' and d.get('fail')==0 else 1)" "$W/qa/check_cuts.json"; then
    ok "qa/check_cuts.json verdict=PASS fail=0"
  else
    bad "qa/check_cuts.json" "없거나 verdict≠PASS"
  fi

  # 2) 조립기 컷 모드
  python3 "$SCRIPTS/assemble_html.py" "$W" --platform smartstore >"$W/.asm.out" 2>"$W/.asm.err"
  rc=$?
  if [ "$rc" -eq 0 ] && [ -s "$W/index.html" ]; then
    ok "assemble_html.py exit 0 + index.html 생성"
  else
    bad "assemble_html.py" "exit=$rc — $(tail -1 "$W/.asm.err" 2>/dev/null)"
  fi
  n_cuts=$(grep -c '^## C[0-9][0-9]' "$W/cuts.md")
  n_img=$(grep -o '<img[^>]*src="images/c[0-9][0-9]\.png"' "$W/index.html" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n_img" -eq "$n_cuts" ] && [ "$n_cuts" -ge 10 ]; then
    ok "index.html에 컷 이미지 $n_img/$n_cuts 전부 삽입"
  else
    bad "index.html 컷 이미지" "cuts=$n_cuts img=$n_img"
  fi
  if grep -q 'missing_images": \[\]' "$W/.asm.out"; then
    ok "누락 이미지 0"
  else
    bad "누락 이미지" "$(grep -A3 missing_images "$W/.asm.out" | tr -d '\n' | cut -c1-120)"
  fi
done

echo "[윤문 가드 — humanize_cuts.py, 네트워크 없음]"
HZ="$TMP/hz"; mkdir -p "$HZ"; cp -R "$EXAMPLES/punggi-red-ginseng-stick/." "$HZ/"
python3 "$SCRIPTS/humanize_cuts.py" "$HZ" --category health_food --dry-run >"$HZ/.prompt" 2>&1 \
  && grep -q '### 컷 시트 (JSON)' "$HZ/.prompt" && grep -q '"id": "C14"' "$HZ/.prompt" \
  && ok "--dry-run: 시스템 프롬프트 + 14컷 JSON 조립" || bad "--dry-run" "$(tail -1 "$HZ/.prompt")"
cat > "$HZ/gpt.json" <<'EOJ'
{"cuts":[
 {"id":"C01","meaning":"출근길 한 포","body":["홍삼차 우릴 틈 없는 아침","가방에서 꺼내 한 포","6년근 홍삼농축액 10 mL","하루 한 포면 됩니다"]},
 {"id":"C02","meaning":"x","body":["하루 99잔 커피 대신 한 포","서랍 속 홍삼정은 그만","10 mL 한 포로 끝"]},
 {"id":"C03","meaning":"x","headline":"이 헤드라인은 슬롯 한도를 훨씬 넘기도록 아주 길게 쓴 문장입니다"},
 {"id":"C04","meaning":"x","body":["피로 회복 치료제 대신 한 포"]},
 {"id":"C06","meaning":"x","unchanged":true,"note":"자연스러움"}
]}
EOJ
python3 "$SCRIPTS/humanize_cuts.py" "$HZ" --category health_food --from-json "$HZ/gpt.json" >"$HZ/.hz.out" 2>&1
rc=$?
[ "$rc" -eq 0 ] && [ -f "$HZ/cuts.humanized.md" ] && [ -f "$HZ/qa/humanize.json" ] \
  && ok "--from-json exit 0 + cuts.humanized.md + qa/humanize.json" || bad "--from-json" "exit=$rc $(tail -1 "$HZ/.hz.out")"
python3 - "$HZ/qa/humanize.json" <<'PY' && ok "가드 판정: C01 채택 · C02 숫자 거부 · C03 슬롯 거부 · C04 금지어 거부 · C06 미변경" || bad "가드 판정" "$(cat "$HZ/qa/humanize.json" | head -c 300)"
import json,sys
d=json.load(open(sys.argv[1]))
acc={a["id"] for a in d["accepted"]}; rej={r["id"]:" ".join(r["reasons"]) for r in d["rejected"]}; unc={u["id"] for u in d["unchanged"]}
ok = acc=={"C01"} and set(rej)=={"C02","C03","C04"} and "숫자" in rej["C02"] and "headline" in rej["C03"] and "금지어" in rej["C04"] and "C06" in unc and d["applied"] is False
sys.exit(0 if ok else 1)
PY
[ ! -f "$HZ/cuts.original.md" ] && grep -q '홍삼차 우릴 시간 없이' "$HZ/cuts.md" && ok "--apply 없이는 cuts.md 불변" || bad "cuts.md 불변" "원본이 바뀌었다"
cp "$HZ/cuts.humanized.md" "$HZ/cuts.md"
python3 "$SCRIPTS/check_cuts.py" "$HZ" --category health_food --platform smartstore >"$HZ/.g1" 2>&1 \
  && ok "윤문 결과물이 게이트 1 PASS" || bad "윤문 결과물 게이트 1" "$(tail -1 "$HZ/.g1")"

echo "[의존성 점검]"
if bash "$SCRIPTS/check_deps.sh" >"$TMP/deps.out" 2>&1; then
  ok "check_deps.sh exit 0"
else
  skip "check_deps.sh exit 0" "이 머신에 필수 의존성 누락 — $(grep '❌' "$TMP/deps.out" | head -1)"
fi

echo "[프런트매터 계약]"
for f in commands/sangse.md skills/sangse/SKILL.md; do
  fm=$(awk 'NR==1&&$0!="---"{exit} NR>1&&$0=="---"{exit} NR>1{print}' "$PLUGIN_DIR/$f")
  if printf '%s\n' "$fm" | grep -q 'AskUserQuestion'; then
    bad "$f allowed-tools" "AskUserQuestion이 frontmatter에 있으면 자동 승인되어 UI가 안 뜬다"
  else
    ok "$f: frontmatter에 AskUserQuestion 없음"
  fi
done
v_json=$(python3 -c "import json;print(json.load(open('$PLUGIN_DIR/.claude-plugin/plugin.json'))['version'])")
if grep -q "^## $v_json " "$PLUGIN_DIR/CHANGELOG.md"; then
  ok "CHANGELOG.md에 plugin.json 버전 $v_json 항목 존재"
else
  bad "CHANGELOG.md" "plugin.json 버전 $v_json 항목이 없다"
fi

echo
echo "────────────────────────────────────────"
echo "PASS $PASS / FAIL $FAIL / SKIP $SKIP"
[ "$FAIL" -eq 0 ] && { echo "ALL PASS"; exit 0; } || { echo "FAILED"; exit 1; }
