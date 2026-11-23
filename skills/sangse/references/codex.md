# Codex에서 실행할 때 (sangse)

SKILL.md 절차는 그대로 따르고, 아래 차이만 적용한다. `${CLAUDE_PLUGIN_ROOT}`는 이 플러그인 루트(SKILL.md에서 두 단계 위)로 바꿔 읽는다.

## 질문 = 질문 도구 (이번 세션 도구 목록으로 판단)

1. `request_user_input_async`가 있으면 AskUserQuestion 1콜 = 이 도구 1콜(문항 ≤4).
   - 형식: `{"questions":[{"title":"헤더 — 질문","options":["추천안 (추천) — 설명","대안 — 설명"]}]}`
   - 문항에는 `title`·`options`만. `question`·`header`·`id`를 넣으면 파싱 오류가 난다. 추천안을 맨 앞에, "기타" 옵션은 넣지 않는다.
   - 부른 뒤 "위 질문에 답해 주시면 이어서 진행합니다" 한 줄만 쓰고 턴을 끝낸다. 답을 추측해 진행하지 않는다.
2. Plan 모드에서 `request_user_input`만 있으면 1콜 3문항까지(넘으면 나눈다). `header`(12자 이내)·`question`·`id`(snake_case), 선택지 2~3개, 추천 라벨 끝에 `(Recommended)`.
3. 둘 다 없으면 채팅에 번호 블록(`Q1. …` / `1. 추천안 (추천) — …` / `2. 대안 — …` / `3. 문장으로 직접 수정 요청`)으로 내고 "Q1-1, Q2-2"처럼 받는다. 모르면 1번으로 진행한다고 덧붙인다.
4. `codex exec`처럼 사람이 답할 수 없는 실행이면 묻지 않고 추천안·디폴트로 진행하고 가정을 `intake-checklist.md`에 기록한다.

질문이 나오는 곳: 인자 없을 때 입력 형태, Step 2 제품 인터뷰(최대 4문항×2라운드), Step 7 카피 승인 게이트, `pumasi:image`의 질문(args 키워드로 스킵). 선택지 프리뷰는 없다.

## 다른 스킬·도구 대응 (한 줄씩)

- `insane-research:insane-research-refs`(Step 1-1) → insane-research 플러그인의 insane-research-refs SKILL.md를 열어 그 절차를 따른다. 없으면 SKILL.md 5항대로 사용자에게 레퍼런스 URL 2~3개를 받는다.
- `pumasi:image`(Step 8) → pumasi 플러그인의 image SKILL.md를 열어 따른다. args 키워드(`코덱스로`·비율·`고품질`)는 그대로 쓰고 codex exec·imagen.sh 직접 호출 금지 원칙도 같다.
- `insane-search` 스킬(차단 페이지) → insane-search의 SKILL.md를 열어 따른다. 없으면 차단 사실을 보고하고 사용자에게 내용을 받는다.
- Agent 백그라운드(Step 1-1, Step 8) → `spawn_agent`가 있으면 쓰고, 없으면 메인에서 순차 실행한다.
- Agent 4개 병렬 리뷰(Step 6 게이트 2) → `spawn_agent`로 4명을 띄운다. 없으면 리뷰어 4명을 한 명씩 새 관점으로 순차 실행하되 작성자 자기 검수가 되지 않게 각 프롬프트·산출물(`qa/sim-review-r{n}-*.md`)을 분리한다.
- WebFetch(Step 1 URL) → Codex의 웹 도구나 `curl`을 쓴다. 막히면 insane-search로 넘긴다.
- Step 10 렌더 검증은 스크립트(`render_check.py`, Playwright)라 그대로 돌린다.

## 그 밖의 차이

- 첫 실행 설정(`setup/setup.sh`)과 명령의 STAR_ASK·AUTOUPDATE 질문은 Claude Code 전용이다. Codex에서는 실행하지 않는다.
- Step 0 `check_deps.sh --install`의 플러그인 설치는 Claude Code 기준이다. Codex에서는 `codex plugin add pumasi@gptaku-plugins` 등으로 설치돼 있는지만 확인하고, 없는 것은 출력된 안내를 보여준다.
