#!/usr/bin/env bash
# sangse 의존성 점검 — Step 0에서 가장 먼저 실행한다.
# usage: bash check_deps.sh [--install]   (--install: 누락·구버전 gptaku 플러그인을 claude plugin CLI로 설치·업데이트)
# 출력: 항목별 OK/MISSING/OPTIONAL + 설치 명령. 필수 항목이 하나라도 MISSING이면 exit 1.
set -uo pipefail
INSTALL=0; [[ "${1:-}" == "--install" ]] && INSTALL=1
MARKET="gptaku-plugins"; MARKET_SRC="fivetaku/gptaku_plugins"
CACHE="$HOME/.claude/plugins/cache/$MARKET"
missing=0; notes=()

ok()   { printf "✅ %-28s %s\n" "$1" "$2"; }
miss() { printf "❌ %-28s %s\n" "$1" "$2"; missing=1; }
opt()  { printf "⚠️  %-28s %s\n" "$1" "$2"; }

plugin_dir() { ls -d "$CACHE/$1"/*/ 2>/dev/null | sort -V | tail -1; }

# 1) 마켓플레이스
if [[ -f "$HOME/.claude/plugins/known_marketplaces.json" ]] && grep -q "\"$MARKET\"" "$HOME/.claude/plugins/known_marketplaces.json"; then
  ok "marketplace $MARKET" "등록됨"
else
  if (( INSTALL )); then
    claude plugin marketplace add "$MARKET_SRC" >/dev/null 2>&1 && ok "marketplace $MARKET" "방금 등록" || miss "marketplace $MARKET" "claude plugin marketplace add $MARKET_SRC"
  else
    miss "marketplace $MARKET" "claude plugin marketplace add $MARKET_SRC"
  fi
fi

# 2) 필수 플러그인 — plugin.json dependencies와 같은 목록. 신규 설치는 Claude Code가 함께 깔고,
#    업데이트로 들어온 기존 사용자는 여기서 채운다(첫 실행 Step 0이 --install로 부른다).
#    marker: 그 기능이 실제로 있는지 확인하는 파일(구버전이면 디렉터리는 있어도 marker가 없다).
need_plugin() {  # name marker note
  local name="$1" marker="$2" note="$3" D
  D=$(plugin_dir "$name")
  if [[ -n "$D" && -e "$D/$marker" ]]; then ok "plugin $name" "$(basename "$D")"; return; fi
  if (( INSTALL )); then
    if [[ -n "$D" ]]; then claude plugin update "$name@$MARKET" >/dev/null 2>&1
    else claude plugin install "$name@$MARKET" >/dev/null 2>&1; fi
    D=$(plugin_dir "$name")
    if [[ -n "$D" && -e "$D/$marker" ]]; then ok "plugin $name" "방금 설치 $(basename "$D")"; notes+=("$name"); return; fi
  fi
  if [[ -n "$D" ]]; then miss "plugin $name" "claude plugin update $name@$MARKET   (구버전 $(basename "$D") — $note)"
  else miss "plugin $name" "claude plugin install $name@$MARKET   ($note)"; fi
}
need_plugin pumasi          "skills/image/scripts/imagen.sh"            "컷 이미지 생성. 없으면 카피·HTML까지만"
need_plugin insane-research "skills/insane-research-refs/SKILL.md"      "Step 1-1 레퍼런스 이미지 수집 — 2.11.0 이상"
need_plugin insane-search   "skills/insane-search/engine"               "차단 페이지 열기 — 레퍼런스 수집·URL 수집이 쓴다"

# 4) Codex CLI + 이미지 생성 플래그 (pumasi:image 백엔드)
# 주의: pipefail 아래서 `codex … | grep -q`는 grep이 먼저 닫혀 codex가 SIGPIPE로 죽고 파이프가 실패로 잡힌다 → 출력을 변수에 먼저 담는다
flag_on() { local out; out=$(codex features list 2>/dev/null || true); grep -qE "^image_generation[[:space:]]+[^[:space:]]+[[:space:]]+true" <<<"$out"; }
if command -v codex >/dev/null 2>&1; then
  if flag_on; then ok "codex image_generation" "true"
  else
    if (( INSTALL )); then codex features enable image_generation >/dev/null 2>&1 || true; fi
    flag_on && ok "codex image_generation" "방금 활성화" || miss "codex image_generation" "codex features enable image_generation"
  fi
else
  miss "codex CLI" "npm i -g @openai/codex && codex login   (pumasi:image 백엔드)"
fi

# 5) 렌더 검증(게이트 3): Node + playwright
if command -v node >/dev/null 2>&1 && { [[ -d "$HOME/.insane-search/node/node_modules/playwright" ]] || [[ -d "${SANGSE_NODE_MODULES:-/nonexistent}/playwright" ]] || node -e "require('playwright')" >/dev/null 2>&1; }; then
  ok "node + playwright (게이트 3)" "render_check.py 사용 가능"
else
  opt "node + playwright (게이트 3)" "mkdir -p ~/.insane-search/node && cd ~/.insane-search/node && npm i playwright   (없으면 렌더 계측 생략·스크린샷 수동)"
fi

# 6) Python 3 (게이트 1·조립기는 표준 라이브러리만)
command -v python3 >/dev/null 2>&1 && ok "python3" "$(python3 --version 2>&1)" || miss "python3" "필수: check_cuts.py·assemble_html.py"

echo
(( ${#notes[@]} )) && echo "방금 설치·업데이트: ${notes[*]} — 세션을 재시작해야 새 스킬이 로드됩니다."
if (( missing )); then
  echo "MISSING 항목이 있습니다. 위 명령을 실행하거나  bash $(basename "$0") --install  로 자동 설치를 시도하세요. 플러그인 설치 후에는 Claude Code 세션을 재시작해야 스킬이 로드됩니다."
  exit 1
else
  echo "필수 의존성 OK."
fi
