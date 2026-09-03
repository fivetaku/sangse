# Changelog

> 릴리스 절차(버전 bump → GitHub 릴리스 → 마켓 서브모듈 포인터 → 캐시)는 gptaku_plugins의 [PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md)를 따른다. bump 전 `bash tests/test-gates.sh` PASS 필수.

## 0.7.0 — 2026-09-04
- **스타일 팩 신설** — 사용자가 "어떻게 설득하는가"를 고른다. `assets/style-packs/` 6종(story-first 고민 장면 스토리형 / checkpoint 핵심 포인트 체크리스트형 / proof-first 근거·수치 우선형 / lookbook 룩북형 / spec-showcase 스펙 쇼케이스형 / offer-first 혜택·구성 프로모션형). 팩이 컷 시퀀스·타이포 상한·배경 전략·강조 시그니처·비주얼 모드·이미지 프롬프트 스타일 줄·문체를 정하고, 카테고리(법정 블록·금지어)와 채널 규격은 직교 축으로 남는다. 팩 이름·설명·프롬프트에 브랜드·사이트명 없음(tests가 검사). 가이드 `references/style-packs.md`.
- 근거: 국내 자사몰·플랫폼 상세 17페이지 해부(기존 7건 포함). 리드는 대부분 "히어로 → 즉시 근거" 하이브리드, 오퍼는 클로징 모듈, 근거는 권위→다수 이중 적재, 배경색이 내비게이션.
- 템플릿 15종 추가(총 44): P1 근거 히어로·P2 인증 배지 그리드·P3 대조군 계측 카드·P4 Before/After·P5 리뷰 그리드·X1 컬러 매트릭스·X2 사이즈 3중 제시·X3 선제 FAQ·X4 다크 배너·X5 무카피 사진·X6 STEP 라인아트·X7 계산식 표·X8 구성품 그리드·X9 고객 목소리 오프너·X10 계단식 가격표.
- 배선: `cuts.md` 헤더 `style:`, 인터뷰 Q-스타일 팩(추천 1개 선표시), `/sangse --style <id>`, 게이트 1 **T8**(팩 시퀀스 이탈 WARN·미존재 팩 FAIL, 앵커 규칙 팩 인식), 이미지 프롬프트 스타일 줄, 윤문 tone 폴백.
- 실험: 같은 홍삼 입력을 3팩으로 편성 → 첫 3컷 전부 상이, 체크리스트형은 밝은 배경·중앙 정렬만, 기존 예시 대비 시퀀스 유사도 0.48~0.58 (`examples/style-pack-variants/`).
- tests 30 assertions(팩 스키마·템플릿 ID·브랜드명 0건·T8 WARN/FAIL).

## 0.6.0 — 2026-09-03
- **Step 4-1 윤문(humanize) 신설** — Claude가 쓴 컷 카피(headline·sub·body·footnote·cta)를 Codex CLI(GPT)에게 넘겨 컷마다 "이 컷이 하려는 말"을 해석한 뒤 사람이 쓴 문장으로 재생성한다(`scripts/humanize_cuts.py`, 규칙 정본 `references/humanize.md` — humanize-korean의 AI 티 분류를 커머스 카피용으로 차용). 게이트 1 앞에서 실행.
- 컷별 가드(코드 판정): 원본에 없던 숫자 유입·플레이스홀더 소실·템플릿 슬롯 초과·카테고리 금지어 유입이면 그 컷은 원문 유지. `cuts.humanized.md` + `qa/humanize.json`(채택/거부/해석/변경률), `--apply`로 치환(원본은 `cuts.original.md`). `/sangse humanize <dir>` 라우트.
- 실측 함정: codex `--output-schema`는 opencodex류 로컬 프록시에서 스트림이 끊긴다 → 스키마를 프롬프트에 인라인. env 프록시는 codex 호출에서만 우회.
- `tests/test-gates.sh`에 윤문 가드 5건 추가(네트워크 없음, 24 assertions).

## 0.5.2 — 2026-09-03
- 전용 대표 이미지 `assets/sangse-hero-01.png` 생성(/pumasi:image, 시리즈 일러스트 톤) — 예시 컷 재활용본 제거.
- README 5개 언어를 마켓 표준 구조(PLUGIN_STANDARD §13: 태그라인·Quick Start·Why·How it works·Features·Commands·Requirements·클로징)로 재작성. 크몽은 지원 채널 중 하나로만 언급.
- `commands/sangse.md`에 언어 정책(output_lang 잠금, AskUserQuestion 라벨 번역)과 질문 정책(불확실 슬롯만) 인라인. SKILL description을 영어 본문 + 한/영 트리거로 교체(frontmatter 정책 v2.1).
- `.gitattributes` 추가(LF 고정·바이너리 표시), 마켓 루트 README "무엇을 쓸까" 표에 sangse 등재.

## 0.5.1 — 2026-09-03
- 마켓플레이스 표준 정합: README 일본어·스페인어·중국어 추가(5개 언어 상호 토글), 대표 이미지 `assets/sangse-hero.png`.
- `tests/test-gates.sh` 신설 — examples 3종에 게이트 1(`check_cuts.py`) PASS·조립기 컷 모드 스모크·`check_deps.sh`·프런트매터 계약을 고정.
- `.gitignore`의 `sangse/`(사용자 산출물 폴더)가 `skills/sangse/` 신규 파일까지 무시하던 결함 수정 → `/sangse/`.
- CHANGELOG 한국어화(VERSIONING.md 규칙).

## 0.5.0 — 2026-09-02
- gptaku-plugins 플러그인 구조로 재편(`.claude-plugin/plugin.json`, `commands/sangse.md`, `skills/sangse/`, `setup/`).
- README를 상세페이지 제작 플러그인 기준으로 영/한 재작성, 영상 분석 프레이밍 제거.
- 패션 컷 템플릿 F1~F8·패션 컷 시퀀스(무신사 해부), 크몽(서비스) 해부 기록.
- Step 0 의존성 점검(`scripts/check_deps.sh`, `--install`).

## 0.4.1 — 2026-09-02
- 컷 이미지 검수에 텍스트 정확도 외 제품 물리 정합성(미개봉 포장·개수·손가락) 추가.
- 이미지 생성 에이전트는 imagen을 포그라운드로 실행하고 기존 컷에서 재개.

## 0.4.0 — 2026-09-02
- **이미지 컷 시트 형식**: `cuts.md`(14컷) + `legal.md`, 컬리·쿠팡·브랜드몰·삼성·LG 해부에서 실측한 템플릿 21종(`references/reference-patterns.md`).
- `check_cuts.py`(게이트 1, 컷 모드), 조립기·렌더 검증 컷 모드.
- 레퍼런스 캡처 절차와 스크립트(`reference-capture.md`, `capture_reference.js`).

## 0.3.0 — 2026-09-02
- 3중 검증 게이트: 결정론 체커, 분리된 리뷰어 에이전트 4인, Playwright 렌더 + 5초 테스트.

## 0.2.0 — 2026-09-02
- `sangse`로 개명. 제품 인터뷰(불확실 슬롯만, 4문항 × 2라운드 이하), 리서치 근거 규칙(FAQ 블록·스펙 표·유입 경로 변수·CTA 반복), 식품·건강기능식품 `compliance.md`.

## 0.1.0 — 2026-09-02
- 첫 버전: 8질문 카피 프레임워크, Iron Law, 문단형 카피 + 섹션 이미지 4장.
