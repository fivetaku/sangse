# Changelog

> 릴리스 절차(버전 bump → GitHub 릴리스 → 마켓 서브모듈 포인터 → 캐시)는 gptaku_plugins의 [PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md)를 따른다. bump 전 `bash tests/test-gates.sh` PASS 필수.

## 0.9.1 — 2026-10-20
가상 무기자차 선크림(스마트스토어) E2E에서 드러난 스크립트 결함을 고쳤다.
- **게이트 1이 cuts.md 헤더를 읽는다.** `check_cuts.py`는 `--category`·`--platform`을 생략하면 헤더의 `category:`·`platform:`을 쓴다. 카테고리가 common뿐이면 안내를 출력한다. 재실행 때 인자를 빠뜨리면 화장품 경고어 12건이 0건으로 바뀌던 문제를 막는다. `cut-sheet.md` 헤더 문법에 `category:`(선택)를 추가했다.
- **조립기 플레이스홀더 집계를 바로잡았다.** `assemble_html.py`의 `placeholders`가 이미지 컷에 구운 문구와 legal 불릿·표 안의 `[자료 필요: …]`를 세지 않아 35개를 1개로 보고하던 문제를 고쳤다. 이제 게이트 1 `P` 집계와 같다.
- **legal.md 서두 처리.** 첫 `##` 앞의 `# 제목`은 숨기고 `> ` 줄은 안내문(blockquote)으로 렌더한다. 전에는 `#`·`>`가 기호째 고객 화면에 나왔다. 판매자 메모는 `[자료 필요: …]`로 쓰라고 `cut-sheet.md` §2에 적었다.
- **윤문 용량 초과 대응.** `humanize_cuts.py`는 모델이 `at capacity`면 `SANGSE_HUMANIZE_FALLBACK_MODELS`(기본 `gpt-6-sol`)로 한 번씩 재시도하고, 실제 쓴 모델을 `qa/humanize.json`에 남긴다. GPT 응답은 `qa/humanize-response.json`에 보존해 검토 후 `--from-json`으로 다시 쓸 수 있다.
- **SKILL.md 문구.** Step 7은 인자에 `카피만`이 있으면 "카피만"을 추천으로 올리고 이미지 진행을 "범위 확장"으로 표시한다(그 자리 답이 인자보다 우선). Step 8 앵커는 C01 고정이 아니라 `anchor:` 컷이다(story-first는 고민 장면으로 시작하므로 첫 제품 히어로).
- 회귀: test-gates 48 PASS(헤더 폴백·플레이스홀더 집계·legal 서두 3건 추가), pytest 40 passed(용량 초과 폴백·무재시도 2건 추가).

## 0.9.0 — 2026-10-20
- **레퍼런스 이미지 수집을 매 실행 단계로(Step 1-1).** 같은 제품군의 지금 판매 중인 상세를 `insane-research:insane-research-refs`(insane-research 2.11.0 라이트 모드)로 모아 `refs/`(candidates.md·manifest.json·images/)에 남긴다. 백그라운드 에이전트가 돌리고 메인 세션은 그동안 인터뷰를 한다. 사용자가 준 URL은 건너뛰지 않고 후보에 합친다. 검색·크롤링은 sangse에 따로 두지 않는다 — 고치면 insane-research 한 곳에서 고쳐진다.
- 수집본은 참고 전용이다. 컷 순서·배경 전환·텍스트 밀도 비교(Step 4)와 해부(Step 2-1)에만 쓰고, 이미지는 판매처 저작물이라 `pumasi:image --ref`·결과물에 넣지 않는다(Red Flags 추가).
- **레퍼런스 해부를 Step 0-1에서 Step 2-1로 옮겼다.** 수집본에 상세 원본이 있으면 바로 조각내고, 못 받은 페이지만 `capture_reference.js`로 캡처한다. 건너뛰기 기준을 `reference-patterns.md` 상단 "해부된 카테고리" 목록 한 곳으로 모았다(패션 포함, 낡은 "건기식·가전" 문구 정리).
- **의존성 필수화.** `plugin.json` `dependencies`에 `pumasi`·`insane-research`·`insane-search`를 추가했다. Step 0은 처음부터 `check_deps.sh --install`로 돌며, 없으면 설치하고 구버전(예: insane-research 2.10.x, refs 스킬 없음)이면 업데이트한 뒤 세션 재시작을 안내한다.
- **이전 버전에서 바뀐 계약**: insane-research 2.11.0 이상이 필요하다. 없으면 Step 1-1은 즉석 검색 대신 사용자 URL을 받는다.

## 0.8.1 — 2026-10-13
- **gptaku-core 라우팅 적용.** `gptaku-core`를 의존성으로 선언하고 `routing.json`을 추가해, 이 플러그인 스킬에 맞는 요청이 오면 직접 처리하거나 기본 도구를 쓰기 전에 이 스킬을 먼저 쓰게 했다. 기존 사용자는 업데이트 후 `/reload-plugins`를 실행하거나 플러그인을 다시 설치해야 gptaku-core가 함께 설치된다. 끄기: `GPTAKU_ROUTER=off`.

## 0.8.0 — 2026-09-06
- 정량 검증 계약 강화: 숫자 존재 여부 대신 문장·항목·단위·조건의 원문 일치 또는 위치별 검토 출처를 대조한다. `numerical-provenance.md`에 승인 형식과 의미·산술 검증의 한계를 명시했다.
- 윤문 금지어를 정규식으로 검사한다. `<폴더> --apply`는 원본·결과 SHA-256을 확인한 저장 미리보기만 적용하며, 모델을 재호출하지 않는다. 변경된 미리보기·원본, 추가 인자는 거부하고 최초 백업을 보존한다.
- 컷 이미지에 문단형의 400px 제한이 적용되던 CSS를 수정했다. 렌더 검사는 모든 컷과 내부 이미지 폭을 확인하며, 이미지 로딩은 고정 대기 대신 이벤트로 기다린다.
- 클로징 컷 존재와 실제 CTA 위치 계측을 분리했다. 이미지 속 CTA는 `manual_review`와 null 위치로 표시하며, 자동 PASS를 게시 준비 완료로 해석하지 않는다.
- 스타일 변형 예제에 독립 입력을 추가하고 테스트의 숨은 입력 복사를 제거했다. 컷 모드 리뷰 입력·승인·해시 기록과 다국어 안내를 현재 계약에 맞췄다.
- 기존 제품 예제의 오류 8컷을 검수한 원본 JPEG로 교체했다. 30칸 카드·7칸 케이스·누락 구성품·근거보다 강한 표현을 수정하고 역사적 PNG와 검수 기록을 구분했다.
- `examples/reference-offer-first/`에 최신 워크플로우 기준 예제를 추가했다. 가상 입력의 출처를 명시하고 실제 윤문, 독립 리뷰 4종, 11컷 이미지, HTML, 390/860px 렌더와 첫 화면 이해도 결과를 포함한다.
- 회귀 검증: 통합 37항목 PASS, 실패·스킵 0건. 세부 숫자 18개·윤문 12개·브라우저 8개 테스트를 포함한다.
- **이전 버전에서 변경된 계약**: 수치 재서술은 intake의 `quantitative-facts` 출처 연결이 필요하다. 해시가 없는 예전 윤문 미리보기는 다시 생성·검토해야 하며, 적용 명령에는 `--category` 등 생성 옵션을 함께 쓰지 않는다.

## 0.7.2 — 2026-09-04
- 팩 6종 전부 `verified` — 비식품 가상 입력(린넨 셔츠·무선 가습기·클래스 랜딩)으로 lookbook·spec-showcase·offer-first 편성 실험 추가. 6팩 쌍별 시퀀스 유사도 최대 0.67, 대부분 0.1~0.4. `examples/style-pack-variants/`에 6팩 시트 + 입력 수록.
- 게이트 1 T3: 랜딩 전용 팩(`offer_position: lead`)은 Q8 오퍼 히어로로 시작 허용.
- 해부 2건 추가(리빙 플랫폼 본상품, 강의 랜딩 히어로 재확인 → offer-first에 "고정 오퍼 바 + 실제 기한 카운트다운" 문법). 표본 20페이지.
- tests: 6팩 변형 예시 게이트 1 + T8 회귀(36 assertions).

## 0.7.1 — 2026-09-04
- `assets/channel-presets.json` 신설 — 채널 10종의 export 폭·최대 높이·용량·이미지 내 텍스트 정책. 공식 2조직 확인은 `verified`, 단일 조직·상충 규격은 `unverified`(보고에 미확정 표기). 팩과 직교.
- 오픈마켓 상세 본문 1건 해부 추가(브라우저 에이전트 경유) → `checkpoint` 팩에 "포인트마다 즉시 증빙" 문법 반영. 해부 표본 18페이지.

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
