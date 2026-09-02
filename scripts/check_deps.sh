#!/usr/bin/env bash
# sangse 의존성 점검 — Step 0에서 가장 먼저 실행한다.
# usage: bash check_deps.sh [--install]   (--install: 누락된 gptaku 플러그인을 claude plugin CLI로 설치 시도)
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

# 2) 필수 플러그인: pumasi (/pumasi:image)
P=$(plugin_dir pumasi)
if [[ -n "$P" && -f "$P/skills/image/scripts/imagen.sh" ]]; then
  ok "plugin pumasi" "$(basename "$P") — /pumasi:image 사용 가능"
else
  if (( INSTALL )); then
    claude plugin install "pumasi@$MARKET" >/dev/null 2>&1 && P=$(plugin_dir pumasi)
  fi
  if [[ -n "$P" && -f "$P/skills/image/scripts/imagen.sh" ]]; then ok "plugin pumasi" "방금 설치 $(basename "$P")"
  else miss "plugin pumasi" "claude plugin install pumasi@$MARKET   (컷 이미지 생성에 필수. 없으면 카피·HTML까지만)"; fi
fi

# 3) 선택 플러그인: insane-search (URL 차단 우회), skillers-suda(스킬 개선용)
for pl in insane-search; do
  D=$(plugin_dir "$pl")
  if [[ -n "$D" ]]; then ok "plugin $pl (선택)" "$(basename "$D")"
  else
    (( INSTALL )) && claude plugin install "$pl@$MARKET" >/dev/null 2>&1 && D=$(plugin_dir "$pl")
    [[ -n "$D" ]] && ok "plugin $pl (선택)" "방금 설치" || opt "plugin $pl (선택)" "claude plugin install $pl@$MARKET   (경쟁사 URL이 403일 때만 필요)"
  fi
done

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
if (( missing )); then
  echo "MISSING 항목이 있습니다. 위 명령을 실행하거나  bash $(basename "$0") --install  로 자동 설치를 시도하세요. 플러그인 설치 후에는 Claude Code 세션을 재시작해야 스킬이 로드됩니다."
  exit 1
else
  echo "필수 의존성 OK."
fi
