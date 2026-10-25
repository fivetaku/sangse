---
name: sangse
description: Korean e-commerce detail page builder - turns product facts (text, file, URL) into an image cut sheet ordered by the 8 questions a customer asks before paying (10~20 vertical cuts in the Kurly / Coupang / Smart Store convention, copy inside the image), verifies it through three gates, generates the cut images via /pumasi:image and assembles an HTML draft. Also triggers when a feature-list product blurb must be rewritten in customer language, even without the word "detail page". Not for image-spec questions, proofreading finished copy, or single-image requests. Korean triggers: "/sangse", "상세 만들어줘", "상세페이지 만들어줘", "상세페이지 써줘", "랜딩페이지 카피 써줘", "스마트스토어 상세 만들어줘", "세일즈 페이지 만들어줘", "이 제품 소개 페이지 써줘", "상세페이지 다시 써줘". English triggers: "sangse", "detail page", "make a detail page", "product page copy", "sales page copy", "landing page copy".
---

<!-- first-run setup: idempotent, non-blocking, self-skips after first run -->
**Step 0 - run once, silently, before anything else:** `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" >/dev/null 2>&1 || true` - do not narrate or comment on it, then continue.

# sangse - 상세페이지 제작

> 예쁘기만 하고 결제가 안 나는 페이지는 "예쁜 쓰레기"다. 상세페이지는 설명서가 아니라 **고객이 결제 전에 조용히 던지는 8가지 질문에 순서대로 답하는 영업사원**이어야 한다. 이 스킬은 창업자가 준 정보를 그 8질문 구조의 고객 언어로 번역하고, 실제 커머스 상세 해부(`references/reference-patterns.md`)에 맞춘 이미지 컷 시트로 만든다. 8질문 정본은 `references/framework.md`.

## Iron Law

**입력에 없는 사례·수치·후기·환불 조건·기한은 만들지 않는다.** 없는 슬롯은 `[자료 필요: …]` 플레이스홀더로 드러낸다. 이유: 상세페이지 문구는 실제 결제·환불·광고 표시와 연결되고, 지어낸 근거 하나가 페이지 전체의 신뢰를 무너뜨린다. 지킬 수 있는 약속을 후킹되게 쓰는 것이 기술이고, 과장은 단기 전환율만 올린다.

| 합리화 | 현실 |
|---|---|
| "사례 하나쯤 예시로 넣어도 되겠지" | 사용자는 그걸 그대로 퍼블리시한다. 플레이스홀더로 두고 무엇을 준비할지 알려준다 |
| "기한 할인을 넣어야 Q8이 살지" | 가짜 긴급성은 첫 구매자에게 들통난다. Q8은 CTA만으로도 성립한다 |
| "타겟이 '모두'라니 그대로 쓰자" | Q1이 성립하지 않는다. 장면 3개를 추정 제시해 하나를 고르게 한다 |
| "카피랑 이미지를 한 번에 뽑으면 빠르지" | 카피 방향이 틀리면 이미지 8장이 전부 버려진다. 카피 승인 뒤에만 이미지 |

## 산출물 위치

프로젝트 루트(git root, 없으면 cwd)에 `sangse/{slug}/`를 만든다. slug는 제품명 영문 kebab-case.

```
sangse/{slug}/
├── raw-input.md          # 수집한 원자료 (출처 추적의 기준)
├── intake-checklist.md   # 필수 4종 + 슬롯 10개 채움 현황
├── offer-check.md        # 오퍼 선행 점검
├── cuts.md               # 컷 시트: 컷 10~20개, 각 컷 = 템플릿·Q·헤드·서브·본문·비주얼·bg·image (references/cut-sheet.md)
├── legal.md              # HTML로 남기는 법정·거래 블록 (주의사항·상세정보 표·영양표·원료·환불·고시)
├── review-log.md         # 번역/삭제 문장 로그 = A/B 가설 목록
├── images/c01.png …      # 컷 이미지 (생성 원본, JPEG면 c01.jpg, 폭 1000)
├── refs/                 # Step 1-1 레퍼런스 수집본 (candidates.md·manifest.json·images/) — 참고 전용
├── qa/                   # 검증 게이트 산출물
└── index.html            # 컷 세로 나열 + legal HTML
```

형식의 근거는 `references/reference-patterns.md` - 컬리·쿠팡·정관장몰 실제 상세는 폭 1000 이미지 컷의 세로 나열이고 카피는 이미지 안에 있다. 텍스트 문단형 랜딩은 삼성·LG 같은 글로벌 브랜드 사이트 문법이라 국내 커머스에는 맞지 않는다. `copy.md` 문단 형식은 웹 랜딩 전용 호환 모드로만 남긴다.

## 워크플로우

### Step 0. 의존성 확인 (항상 맨 먼저)
**타입**: script

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/check_deps.sh --install
```

처음부터 `--install`로 돌려 빠진 것을 바로 채운다. 필수 플러그인은 `plugin.json`의 `dependencies`와 같다 — `pumasi`(`/pumasi:image`, 컷 이미지), `insane-research` 2.11.0 이상(`insane-research-refs`, Step 1-1 레퍼런스 수집), `insane-search`(차단 페이지 열기). 신규 설치는 Claude Code가 함께 깔고, 업데이트로 들어온 사용자는 이 단계가 설치·업데이트한다. 그 밖에 마켓플레이스 등록, Codex `image_generation` 플래그, Node+Playwright(게이트 3), python3를 점검한다. 방금 설치·업데이트한 플러그인이 있으면 **세션 재시작이 필요하다고 사용자에게 알린다**(재시작 전에는 새 스킬이 로드되지 않는다). 그래도 남은 MISSING은 출력된 명령을 보여준다. pumasi가 없으면 컷 이미지 없이 카피·legal·텍스트 플레이스홀더 시안까지만 만들고, insane-research가 없으면 Step 1-1 폴백을 따른다. 둘 다 첫 보고에 적는다.

### Step 1. 정보 수집 → `raw-input.md`
**타입**: prompt (+ WebFetch)

텍스트는 그대로, 파일은 Read로 발췌, URL은 WebFetch(차단 시 insane-search 스킬)로 수집해 한 파일에 병합한다. 경쟁사 URL은 참고용으로만 표시하고 그쪽 수치·후기를 우리 것으로 옮기지 않는다. 기존 상세페이지가 있으면 창업자 언어 문장(스펙·경력·"AI 기반")을 따로 뽑아 "번역 대상" 목록으로 둔다.

### Step 1-1. 레퍼런스 이미지 수집 (매 실행) → `refs/`
**타입**: api_mcp(Skill `insane-research:insane-research-refs`) + Agent(백그라운드)

카테고리가 이미 해부돼 있어도 **매번** 같은 제품군의 지금 판매 중인 상세를 모은다. 레퍼런스 찾기는 insane-research가 정본이다 — 이 스킬 안에서 검색·크롤링을 즉석으로 짜지 않는다.

1. raw-input에서 카테고리·판매 채널·가격대를 뽑아 args를 만든다: `주제={카테고리} 상세페이지, 채널={판매 채널 + 큐레이션몰·자사몰}, pages=5, out=sangse/{slug}/refs`. 사용자가 레퍼런스 URL을 줬으면 `함께 넣을 URL`로 넘긴다(건너뛰지 않고 후보에 합친다).
2. **에이전트 1개를 백그라운드로** 띄워 Skill `insane-research:insane-research-refs`를 그 args로 호출하고, 끝나면 `REFS:` 줄과 후보 표만 돌려받는다. 메인 세션은 그동안 Step 2 인터뷰를 한다. 결과는 Step 2-1 전에 수거한다.
3. 수집본은 **참고 전용**이다. 같은 제품군의 컷 순서·배경 전환·텍스트 밀도·법정 블록 위치를 보는 데 쓰고(Step 2-1, Step 4), 문장·수치·후기·이미지를 옮기지 않는다. 이미지는 판매처 저작물이므로 `pumasi:image`의 `--ref`나 결과물에 넣지 않는다.
4. 수거하면 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/check_refs.py "sangse/{slug}"`로 다시 판정한다. 수집기의 `ok`는 "페이지를 열고 이미지를 받았다"일 뿐 긴 상세 이미지를 받았다는 뜻이 아니다(2026-10-20 E2E: 올리브영 2페이지가 `ok`였지만 1000×1000 썸네일뿐). 보고·판단에는 `상세 원본 n/N`과 페이지별 `partial:*`을 쓰고, `ok` 개수를 수집 성공으로 쓰지 않는다. 상세 원본이 0이어도(exit 1) 그 사실을 첫 보고에 적고 진행한다(레퍼런스는 막는 단계가 아니다).
5. **insane-research가 없을 때**(Step 0 이후에도 MISSING): 즉석 검색으로 대신하지 않는다. 설치 명령과 재시작 안내를 보여주고, Step 2 1라운드에 "레퍼런스 상세 URL 2~3개" 문항을 넣어 사용자 URL을 받는다. 받은 URL은 `refs/candidates.md`에 `사용자 제공`으로 적는다.

### Step 2. 제품 인터뷰 → `intake-checklist.md`
**타입**: rag(`references/intake-checklist.md`, `references/interview.md`) + review (AskUserQuestion)

카피를 쓰기 전에 **요청에 남은 불확실성만** 묻는다. 스타일 팩 1문항(`interview.md` Q-스타일 팩 - 추천 1개 선표시, `references/style-packs.md` §3 규칙)은 플랫폼 문항과 같은 라운드에 넣는다. 절차: ① 필수 4종(무엇·누구에게·가격·고객이 얻는 변화)과 슬롯 10개를 대조해 각 항목을 `확정 / 추론 가능(디폴트) / 불명` 으로 분류한다 ② `불명`만 `interview.md`의 질문 은행에서 우선순위(타겟 → 변화 → 플랫폼 → 증거 → 가격·환불 → 규제 업종 → 산출물·톤) 순으로 골라 **AskUserQuestion 최대 4문항 × 최대 2라운드**로 묻는다. 텍스트 질문·A/B/C 나열은 금지, 선택지는 5개 안팎에 창의적 대안 1~2개와 "자동 판단" 안전망을 넣는다 ③ 타겟이 "모두"거나 불명이면 M1·M4에서 **가장 아픈 고객 장면 3개를 추정해 선택지로** 제시한다 ④ 규제 업종 신호(식품·건기식·화장품·의료기기·금융)가 보이면 규제 질문을 1라운드에 넣는다. 추론 가능한 항목은 묻지 않고 디폴트로 진행하되 첫 보고 서두에 "가정: X"로 선언한다. 2라운드에도 안 풀린 것은 플레이스홀더로 진행한다. 같은 질문은 두 번 하지 않는다. 답변 출처는 `인터뷰 R1-Q2` 형태로 체크리스트에 기록한다. 가상·연습 상품이면 인터뷰를 생략하고 Claude가 설정한 값을 "가상 설정"으로 기록한다.

### Step 2-1. (조건부) 레퍼런스 해부
**타입**: script + Agent + rag(`references/reference-capture.md`)

카테고리·채널의 컷 패턴이 `references/reference-patterns.md` 상단 "해부된 카테고리" 목록에 없으면, `refs/candidates.md`에서 채널이 겹치지 않게 2~3개를 골라 해부한다. `check_refs.py`가 `detail`로 판정한 페이지는 그 원본을 바로 조각내고, `needs_capture`인 페이지(`partial:*`·`no_large_images`·`blocked`)만 `scripts/capture_reference.js`로 캡처한다. 해부 에이전트 결과로 템플릿을 `assets/cut-templates.json`에 추가한다. 목록에 있으면 건너뛰고 수집본은 Step 4 참고로만 쓴다.

### Step 3. 오퍼 선행 점검 → `offer-check.md`
**타입**: prompt

카피를 고치기 전에 오퍼를 본다. 오퍼는 가격표가 아니라 "고객이 받는 것 + 줄어드는 불안 + 지금 선택해야 하는 이유"의 전체 약속이다. 세 줄로 판정한다: ① 받는 것이 정보 나열(50강, PDF 20장)인지 불안 해소 장치(상담 질문지, 첫 고객 마케팅 설계)인지 ② 결제 직전 불안(내가 해도 될까, 실패하면, 얼마나 걸리나)에 답하는 구성품이 있는지 ③ 지금 이유가 있는지. 오퍼가 정보 나열이면 **구성품 재해석 제안**을 1개 이상 쓴다 - 단, 없는 구성품을 추가하는 게 아니라 있는 것을 고객 불안 순서로 다시 묶는다. 오퍼가 결정적으로 약하면(받는 것이 불명확) 카피로 넘어가기 전에 그 사실을 사용자에게 한 줄로 알린다. 카피만 바꾸면 클릭은 오르고 결제는 안 나기 때문이다.

### Step 4. 컷 시트 → `cuts.md` + `legal.md`
**타입**: prompt + rag(`references/framework.md`, `references/cut-sheet.md`, `references/style-packs.md`, `references/reference-patterns.md`)

**스타일 팩이 시퀀스를 정한다.** Step 2에서 고른(또는 `--style`로 받은) 팩 id를 `cuts.md` 헤더 `style:`에 적고, `assets/style-packs/{id}.json`의 `sequence`대로 컷을 편성한다(`optional: true` 컷은 입력에 재료가 없으면 생략, 템플릿 한도는 `cut-templates.json`). 팩의 `grammar`(배경 교차·무카피 사진 컷·각주·사이즈 3중 제시·오퍼는 클로징)를 편성에 반영하고, `typography.body_lines_max`·`tone_default`를 카피 상한으로 쓴다. 팩을 못 정했으면 `checkpoint`. 아래 14컷 기본 시퀀스는 팩이 없을 때의 폴백이다.

8질문 순서를 **컷 10~20장**으로 편성한다. 문법·기본 시퀀스(건기식 14컷: K2 히어로 → K3 페르소나 → K4 TPO → K5 목차 → K6 Point 1 → K7 기능성 → K8/L4 근거 → K6 Point 3 → K9 STEP → K10 추천 대상 → K11 구성 → L1 스펙 → C1 보증 → C2 CTA/L2 FAQ)은 `cut-sheet.md`, 템플릿별 슬롯 한도는 `assets/cut-templates.json`. 컷당 헤드 1개(4~17자, 2행이면 행당 5~9자) + 서브 1줄 + 본문 3줄(마지막 줄 볼드) + 비주얼 지시 + 배경색. 텍스트 10줄 이하, 줄당 24자 이하, 이미지 안 글자는 폭 1000 기준 서브 40px·본문 36px·각주 30px 이상에 명암비 4.5:1 이상(회색 본문 금지, `image-briefs.md` §5 — 390px 화면에서 14px). 가격·전화번호·심의번호·영양 수치·차트 값은 이미지에 넣지 않고 `legal.md`(주의사항·상세정보 표·영양표·원료명·환불·고시)로 보낸다. 웹 랜딩 전용으로 문단형 `copy.md`가 필요할 때만 `## Q1`~`## Q8` 헤딩 형식을 쓴다.

각 컷이 답하는 질문의 임무는 framework.md 표를 따른다. 특히:
- **Q1**은 제품명·브랜드·"AI 기반"으로 시작하지 않는다. 고객이 오늘 겪는 고민의 장면 한 컷으로 시작한다. 배제되는 고객이 있을 만큼 좁게.
- **Q2**는 "성공하세요"가 아니라 눈앞에 잡히는 도착 장면. 수치는 입력에 있는 것만.
- **Q3**에서만 기능이 등장한다 - 기존 방식의 한계 → 우리 메커니즘 → 그것을 가능케 한 기능. 모든 기능 문장은 `[기능] 덕분에 [겪던 장면]이 [결과]로 바뀝니다` 꼴로 쓸 수 있어야 한다.
- **Q4**는 후기보다 "실제 받아보는 화면". 사용자가 준 스크린샷·샘플을 최우선으로 배치하고, 없으면 `[자료 필요: 실제 결과물 화면 1장]`.
- **Q6**은 목록이 아니라 여정 순서: 먼저 받는 것 → 하는 것 → 막힐 때 지원 → 최종 결과물.
- **Q7**은 환불·피드백 범위를 정책 그대로. 환불 불가면 그대로 쓰고 샘플·미리보기·FAQ로 리스크를 줄인다.
- **Q8**은 기한·할인이 입력에 있을 때만. 없으면 CTA와 `[선택: …]` 안내.

리서치로 보완된 규칙(근거는 `references/evidence.md`): Q6 아래 **사양 표**(성분·용량·규격)를 둔다. 물성 상품·스마트스토어·펀딩이면 Q7 아래 **FAQ 선택 블록**(실제 문의 기반 3~5문항, 배송·교환·AS·호환)을 켠다. 컷 모드에서는 해당 컷과 legal에, 문단형에서는 Q6 표와 Q7 `### FAQ`에 반영한다. **문단형 레거시 모드에서만** 같은 CTA를 Q1 끝·Q2·Q4·Q8에 반복하고 첫 실제 CTA가 두 화면 안에 있는지 계측한다. 검색 유입이면 Q1에 카테고리 키워드와 가까운 가격을 둔다. **컷 모드에서는** 선택한 팩의 클로징·오퍼 배치를 따른다. 가격은 legal 또는 플랫폼 UI에 두며, 이미지 안 CTA의 위치·가독성은 직접 검수한다. Q7/Q8 컷의 존재를 클릭 가능한 CTA나 첫 두 화면 내 CTA의 증거로 쓰지 않는다. 규제 업종이면 `references/compliance.md`를 초안부터 적용한다. 기능성 문구는 고시 문구 그대로, 질병·의약품 용어 금지, 후기로 효능 암시 금지.

플랫폼이 스마트스토어·크몽이면 모바일 세로 스크롤을 전제로 문장을 더 짧게 끊는다.

편성 전에 `refs/candidates.md`의 같은 제품군 상세 1~2개를 Read로 훑어 컷 순서·배경 전환·텍스트 밀도를 비교하고, 크게 다르면 그 이유(팩 선택·입력 재료)를 review-log에 한 줄 남긴다. 레퍼런스의 문장·수치·후기는 옮기지 않는다.

### Step 4-1. 윤문 - GPT가 사람답게 재생성 → `cuts.humanized.md`, `qa/humanize.json`
**타입**: script(외부 모델) + rag(`references/humanize.md`)

같은 모델이 쓰고 같은 모델이 고치면 같은 습관이 남는다. Step 4의 카피(headline·sub·body·footnote·cta)를 **Codex CLI(GPT)** 에게 넘겨 컷마다 "이 컷이 하려는 말"을 한 문장으로 해석한 뒤 그 의미를 사람이 쓴 문장으로 다시 쓰게 한다. 규칙은 humanize-korean의 AI 티 분류(번역투·광고 상투구·대구 공식·리듬 균일·hedging·접속사)를 커머스 카피용으로 추린 시스템 프롬프트(`humanize.md` §4)다. 게이트 1 **앞**에서 한다 - 윤문 결과도 카피이므로 그 뒤에 검사한다.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/humanize_cuts.py "sangse/{slug}" --category {common|food|health_food|cosmetics}
```

코드가 컷별로 가드한다. 원본에 없던 숫자 유입·플레이스홀더 소실·템플릿 슬롯 초과·카테고리 금지어 유입이면 그 컷은 원문 유지(`qa/humanize.json`의 `rejected`). template·Q·h·bg·visual·image·tags는 원본에서 그대로 복사된다. 결과를 보는 순서: ① `meanings`의 해석이 Step 4의 의도와 같은 컷만 인정 ② 채택된 컷의 diff 확인 ③ 아래 명령으로 **저장된 해시 검증 프리뷰만 적용**. 새 GPT 호출은 없고 최초 원본은 `cuts.original.md`로 보존된다. 적용 명령에는 `--category`·`--model`·`--timeout`·`--dry-run`·`--from-json`을 붙이지 않는다. 원본이나 프리뷰가 바뀌면 새 프리뷰와 검토가 필요하다. `cuts.humanized.md`를 수동으로 옮기거나 해시를 고쳐 검증을 우회하지 않는다. 거부 문장을 고쳤을 때도 새 프리뷰를 검토하며 숫자·금지어 위반은 채택하지 않는다. codex가 없으면(exit 3) 이 단계를 건너뛰고 "윤문 생략(codex 없음)"을 보고한다. Step 7 승인 요약에 "윤문: 채택 n/총 컷, 거부 m(사유)"를 넣는다. `/sangse humanize <dir>`로 이 단계만 다시 돌릴 수 있다.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/humanize_cuts.py "sangse/{slug}" --apply
```

### Step 4-2. 정량 문장 출처 승인 → `intake-checklist.md`
**타입**: review + rag(`references/numerical-provenance.md`)

게이트 1 전에 `cuts.md`와 `legal.md`의 정량 문장을 원자료와 대조한다. 입력의 완전한 문장과 정확히 일치하지 않는 재서술은 intake의 `quantitative-facts` JSON에 `at`(예: `C07.body`, `legal:제품 상세정보`), `claim`(필드 전체, 본문은 줄바꿈 포함 또는 법정 표의 행 전체), `sources`(`file`과 실제 존재하는 `quote`)로 승인한다. 출처 파일은 `raw-input.md`와 `intake-checklist.md`만 허용하며, 인용문은 승인 블록 밖에 있어야 한다. 숫자가 다른 곳에 있다는 이유로 승인하지 않는다. 대상·속성·수량·단위·섭취 기준·조건·기간이 같은지 사람이 확인한다.

파생 단가·총량·기간은 원래 피연산자와 계산식, 단위, 반올림 기준을 출처에 남기고 사람이 계산과 문장 의미를 검토한다. T5는 정확한 출처 연결과 승인 무결성을 검사할 뿐 **산술·의미·실제 사실을 자동 검증하지 않는다**. 카피나 출처가 바뀌면 해당 승인을 재검토한다. 실패한 문장을 승인 목록에 복사해 통과시키지 않는다.

### Step 5. 검증 게이트 1 - 자동 검사 → `qa/check_cuts.json`
**타입**: script + rag(`references/verification.md`)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/check_cuts.py "sangse/{slug}" --category {common|food|health_food|cosmetics} --platform {web|smartstore|kmong}
```

인자를 생략하면 cuts.md 헤더의 `category:`·`platform:`을 쓴다. 재실행마다 조건이 달라지지 않게 헤더에 적어 두는 것을 기본으로 한다.

코드가 판정한다: 컷 헤딩 문법·템플릿 존재·높이 범위, 헤드라인 행 수·행당 글자 수·본문 줄 수·줄당 글자 수(템플릿 한도), 컷 수 10~20과 Q1~Q8 커버리지·순서, 앵커 컷·배경색·K4 각주·K7 고시 문구, **cuts.md+legal.md 정량 문장의 정확한 출처 또는 위치별 검토 승인 연결**(T5, `numerical-provenance.md`; 계산 자체는 사람 검토), 카테고리 금지어(`assets/banned-words.json`), legal 필수 블록, 이미지 실존·폭≥900. exit 0이 아니면 다음으로 가지 않는다. 지목된 것만 고치고 재실행한다. 문단형 레거시 copy.md는 `check_copy.py`이며 T5와 같은 계약으로 해석하지 않는다.

### Step 6. 검증 게이트 2 - 고객 시뮬레이션 리뷰 → `qa/sim-review-r{n}.md`
**타입**: review (Agent 4개 병렬) + rag(`references/verification.md` §2·§5)

카피를 쓴 Claude가 스스로 검사하지 않는다. **별도 에이전트 4개를 한 메시지에 동시 스폰**한다. 의심 많은 타겟 고객(intake M2 페르소나로 Q1~Q8마다 네/아니오 + 걸린 문장 인용 + 원하는 문장), 규제 심사관(compliance.md 기준 위반 열거), CRO 리뷰어(evidence.md 기준 6항목 채점), 경쟁사 마케터(가격 비교로 끌어갈 틈 3개 + 방어 문장)다. 각 리뷰어는 컷 모드에서 **cuts.md·legal.md·raw-input.md·intake-checklist.md**를 읽고 `VERDICT: PASS|FAIL`로 끝낸다. 문단형 레거시 모드에서만 cuts.md 대신 copy.md를 읽는다. 보고마다 읽은 파일 경로·SHA-256·모드·플러그인/스크립트 버전·검토 일시를 기록한다. 이는 해당 텍스트 스냅샷의 리뷰이며 이미지 검수 결과가 아니다.

통과 기준은 **고객 8/8 네 + 규제 위반 0건**. 미달이면 지목 문장만 고쳐 최대 2라운드 재리뷰(전면 재작성 금지), 고친 문장은 `review-log.md`에 `원문 → 수정문 (리뷰어)`로 남긴다. 2라운드 뒤에도 남은 "아니오"는 사용자에게 결정을 넘긴다. 리뷰를 마치면 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/review_stamp.py "sangse/{slug}" record --review qa/sim-review-r{n}-regulator.md`로 리뷰한 카피에 스탬프를 찍는다. 이 게이트가 "맞지만 안 팔리는" 카피를 잡는다.

### Step 7. 카피 승인 게이트
**타입**: review (AskUserQuestion 1콜)

컷 모드에서는 cuts.md+legal.md 요약(팩·컷 순서·첫 컷 헤드라인·법정/거래 조건·플레이스홀더·번역/삭제 건수)을 raw-input.md·intake-checklist.md의 근거와 함께 보여준다. copy.md 요약은 문단형 레거시 모드에만 쓴다. 승인 파일 경로·SHA-256·버전·일시를 기록하고 묻는다: ① 이대로 이미지·HTML 진행 (추천) ② 카피 수정할 부분 있음 ③ 카피만 받고 이미지는 생략. 인자에 `카피만`이 있었으면 ③을 추천으로 올리고 ①은 "범위 확장"이라고 표시한다 — 사용자가 이 자리에서 ①을 고르면 그 답이 인자보다 우선한다. 게이트 1·2 스코어를 함께 보여준다. 이 게이트 없이 이미지를 만들지 않는다.

**마지막 수정은 반드시 다시 리뷰한다.** 사용자가 고른 수정, 이 자리에서 반영한 문장, 이후 legal.md 형식 수정까지 모두 카피 변경이다. 반영 뒤 `review_stamp.py "sangse/{slug}" verify`가 바뀐 컷·legal 섹션을 나열하면, 그 단위만 규제 심사관과 의심 많은 고객 2명에게 다시 보여 주는 **델타 리뷰**(`qa/sim-review-delta-{n}.md`, 바뀐 문장 전후 대조 + `VERDICT`)를 돌리고 다시 `record`한다. 델타 리뷰는 Step 6의 2라운드 상한에 세지 않는다. `verify`가 FRESH가 아니면 Step 8로 가지 않고, Step 9 `--final`도 막힌다(2026-10-20 E2E: Step 7 사용자 선택 4건과 legal 형식 수정이 재리뷰 없이 이미지·HTML로 갔다).

"이미지 없이 카피만"이면 이미지 생성을 생략하고 Step 9에서 텍스트 플레이스홀더 시안을 조립한다. 텍스트 초안 승인은 이미지 검수나 게시 승인이 아니다.

### Step 8. 컷 이미지 생성 → `pumasi:image` 호출
**타입**: prompt + api_mcp(Skill `pumasi:image`) + rag(`references/image-briefs.md`)

`cuts.md`의 컷 하나가 브리프 하나다. **앵커(cuts.md `anchor:` 컷 — 기본 시퀀스는 C01, 팩이 고민 장면으로 시작하면 첫 제품 히어로)를 먼저 생성해 Read로 텍스트와 제품 물리 상태를 확인**한 뒤 나머지를 `--ref 앵커`로 생성한다. 제품당 에이전트 1개(포그라운드 생성, 있는 컷은 건너뜀)로 맡기고 메인 세션은 그동안 다른 작업을 한다. 장수(보통 14)와 예상 시간(앵커 2분 + 13컷 × 1~1.5분)을 알린다. 모든 컷에 텍스트가 있으므로 생성 후 **전수 Read 검수**(자모·잘림 + 미개봉·내용물 노출·포장 결합·개수·손가락).

호출 규칙:
1. **Skill 도구로 `pumasi:image`만 호출**한다. codex exec·imagen.sh 직접 호출 금지 - 프록시 우회와 실패 사유 표면화가 그 스킬 안에 있다.
2. args에 **`코덱스로` + 비율 키워드 + `고품질` + 레이아웃·배경·텍스트 문장**(`image-briefs.md` §3 골격, 레이아웃은 `cut-templates.json`의 `layout`)을 넣는다. 이 키워드가 있으면 그 스킬의 백엔드·비율·퀄리티 질문이 스킵돼 14장에 70문항이 뜨는 사태를 막는다.
3. **앵커 우선**: `anchor:` 컷을 먼저 만들고 `path:`를 받은 뒤 나머지를 전부 `--ref {앵커 경로}`로 물린다. 참조가 있으면 스타일 서술을 걷어내고 "첨부 이미지의 색·조명·재질 유지 + 레이아웃·텍스트만" 쓴다. 배경색은 `bg:`대로 컷마다 바꾼다.
4. 이미지 안 텍스트는 cuts.md의 헤드·서브·본문·태그·각주 **그대로**(고시 문구·각주는 한 글자도 바꾸지 않는다). 가격·전화번호·심의번호·차트 값은 넣지 않는다. 한글이 깨지면 "굵은 고딕, 대형, 정확한 자모"를 명시해 1~2회 재생성. HTML 후합성으로 도피하지 않는다.
5. 사용자가 실물 스크린샷·후기를 줬으면 K8/L4 컷에 실물을 쓴다. 가짜 후기·가짜 실명·식별 가능한 얼굴은 어떤 컷에도 넣지 않는다(얼굴 없는 라인 일러스트·손만).
6. 실패한 컷은 `image: [이미지 생성 실패 - 재시도 필요]`로 두고 다음 컷으로. 조립기가 텍스트 플레이스홀더로 렌더하므로 파이프라인이 막히지 않는다.
7. 결과 경로를 `cuts.md`의 해당 컷 `image:`에 기록한다(`sangse/{slug}/images/c{nn}.png` 또는 원본 JPEG의 `c{nn}.jpg`). 확장자는 실제 형식에 맞추고 재인코딩·리사이즈하지 않는다.
8. 이미지 검수 보고에 승인 텍스트와 원자료·intake·legal의 경로/SHA-256, 이미지별 경로/SHA-256, 검토 일시·도구 버전을 남긴다. 이미지나 카피가 바뀌면 관련 검수와 렌더를 다시 한다. 이전 카피 QA나 다른 이미지의 PASS를 새 이미지에 승계하지 않는다. 외부 생성 장애는 차단 사유와 복구 대기로 보고한다.

### Step 9. HTML 조립 → `index.html`
**타입**: script

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/assemble_html.py "sangse/{slug}" --platform web|smartstore|kmong
```

`cuts.md`가 있으면 **컷 모드**: 각 컷 이미지를 폭 100%로 여백 없이 세로 나열하고(스마트스토어 860·웹 720), 이미지가 없는 컷은 배경색·헤드·본문 텍스트 플레이스홀더 블록으로 렌더하며, 끝에 `legal.md`를 HTML 표·불릿으로 붙인다. `[자료 필요: …]`는 노란 박스로 노출한다(숨기지 않는다). stdout JSON의 `missing_images`·`placeholders`·`placeholder_items`를 보고에 반영한다. (`copy.md` 문단형은 구 모드로 그대로 지원.)

조립기는 같은 자료 요청을 묶은 **차단 체크리스트** `qa/placeholders.md`(자료별 위치, 라벨 없는 `[자료 필요]`는 표 행 이름)를 남긴다. `fillable_from_input`에 항목이 있으면 raw-input·intake에 값이 있는데 자리표시로 둔 것이다 — 원문을 확인해 채우고(Step 4-2 출처 승인 포함) 다시 조립한다. 나머지는 사용자에게 체크리스트로 넘긴다. 게시용 최종 렌더는 `assemble_html.py "sangse/{slug}" --final`이며, 자리표시·누락 이미지가 남거나 리뷰 스탬프가 현재 카피와 다르면 `BLOCKED:`와 exit 1이다. 자료가 오기 전 시안은 `--final` 없이 조립해 "시안"으로만 보고한다.

### Step 10. 검증 게이트 3 - 렌더 검증 + 5초 테스트 → `qa/render-*.png`, `qa/five-second.md`
**타입**: review (브라우저 도구) + rag(`references/verification.md` §3)

`python3 ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/render_check.py "sangse/{slug}" --widths 390,860 --full`로 Playwright가 **390px와 860px** viewport에서 index.html을 실제로 열어 첫 화면·전체 스크린샷을 `qa/`에 저장하고 가로 스크롤·헤드라인 위치·CTA 위치·깨진 이미지를 계측한다(헤드리스 Chrome CLI는 최소 창 폭 500px라 쓰지 않는다). 게이트는 HTML 글자의 크기(14px 미만)·명암비(4.5:1, 큰 글자 3:1 미만)를 FAIL로 잡고, 이미지 컷마다 `cutImageScale.px1000For14`(이 폭에서 14px가 되는 폭 1000 환산 px — 브리프 단위)와 `sourcePxFor14`(원본 px)를 남긴다. 스크린샷을 Read로 직접 보고 첫 컷/헤드라인의 가독성(이미지 안 서브·본문이 그 값보다 작거나 회색·연한 색이면 그 컷 재생성), 가로 스크롤 없음, 이미지 안 한글과 제품 물리 상태, 플레이스홀더 노출을 확인한다. 문단형 레거시 모드는 실제 CTA가 첫 두 화면 안에 있어야 한다. 컷 모드의 `closingCutPresent`·`closingCutTop`은 Q7/Q8 보증·클로징 컷의 존재·위치일 뿐 클릭 가능한 CTA의 증거가 아니다. DOM `.cta`가 없으면 `ctaPositionStatus: manual_review`, `firstCtaTop: null`, `ctaInFirstTwoViewports: null`이며 이미지 내부 헤드라인·CTA는 직접 검수한다. DOM CTA가 있으면 `ctaPositionStatus: measured`와 실제 위치를 기록한다. 컷 모드에 문단형의 조기 CTA 배치를 강제하지 않는다. 그다음 **5초 테스트** - 첫 화면 스크린샷 1장만 새 에이전트에 주고 "무엇을 파나 / 누구를 위한 건가 / 사면 뭐가 달라지나"를 답하게 한다. 세 답이 intake M1·M2·M4와 맞아야 통과. 틀리면 Q1 헤드라인이나 히어로 이미지 텍스트를 고치고 재렌더한다. 스크린샷을 안 본 렌더 검증은 검증이 아니다.

### Step 11. 완료 보고
**타입**: generate

보고에 반드시 넣는다: ⓪ 적용한 스타일 팩 id·표시명과 게이트 1 T8 결과, 레퍼런스 수집 결과(`check_refs.py`의 상세 원본 n/N·`partial` 페이지·저장/발견 이미지 수·해부 여부) ① 산출물 경로 ② **검증 스코어카드**(`verification.md` §4 형식 - 게이트 1 fail/warn 수, 게이트 2 고객 네 수·규제 위반·CRO 점수·경쟁 반박 방어 수·라운드 수, 게이트 3 렌더·5초 결과) ③ **채우면 완성되는 항목 표**(플레이스홀더) ④ review-log 요약(번역/삭제 건수 + 대표 예 2개) ⑤ 경고 한 줄 "가격·환불·기한 문구는 실제 결제·법적 책임과 연결됩니다. 퍼블리시 전 직접 확인하세요." ⑥ 첫 A/B 가설 1개(상단 섹션부터) - 게이트 2에서 의견이 갈린 문장이 첫 후보다. "매출이 오른다"는 성과 약속을 보고 어디에도 쓰지 않는다 - 검증 불가능한 주장이고 그 자체가 과장 광고의 문법이다.

보고의 상태는 **텍스트 초안 PASS / 이미지 검수 / 게시 준비**로 나눈다. 자동 검사 통과나 HTML 조립만으로 이미지 검수·게시 준비를 PASS로 쓰지 않는다. 미생성·교체 대기·미검수 이미지, 남은 자료와 규제 확인을 각각 표시한다. 모든 리뷰의 파일 경로·SHA-256·모드·버전·일시를 붙여 무엇을 검수했는지 식별한다. 가상 상품은 시연용이며 실제 인증·효능·심의가 검증됐거나 게시 준비가 끝났다고 표시하지 않는다.

## Red Flags - 이 생각이 들면 멈춘다

- "예시 수치라도 넣어야 그림이 살지" → Iron Law 위반. 플레이스홀더.
- "이 기능이 자랑스러우니 Q1에 넣자" → 기능은 Q3. Q1은 고객 장면.
- "질문 4개로 부족하니 더 묻자" → 묻지 않고 플레이스홀더로 진행 후 보고에 표로.
- "이미지부터 뽑아 보여주면 반응이 좋을 텐데" → Step 7 승인 전 이미지 금지.
- "내가 쓴 카피니까 내가 검수하면 되지" → 게이트 2는 별도 에이전트 4개. 작성자 자기 검수는 검증이 아니다.
- "HTML 조립됐으니 끝" → 게이트 3 스크린샷을 실제로 보기 전엔 완료가 아니다.
- "글자만 맞으면 통과" → 컷 검수는 텍스트 + 제품 물리 상태(미개봉·내용물·포장 결합·개수·손가락). 매실 앵커에서 젤리가 밀려 나온 채 통과된 실측 사례가 있다.
- "이미지 생성은 백그라운드로 띄우고 에이전트는 끝내자" → 에이전트는 포그라운드로 생성·검수·기록까지. 백그라운드는 메인 세션의 몫이다.
- "이 카테고리 레퍼런스는 없으니 감으로" → Step 1-1 수집본으로 Step 2-1 해부를 먼저 한다(`references/reference-capture.md`). 텍스트 랜딩을 만들어 놓고 상세페이지라 부른 실측 사례가 이 스킬의 v0.1이다.
- "레퍼런스 몇 개는 WebSearch로 내가 바로 찾지" → 레퍼런스 찾기는 `insane-research:insane-research-refs`가 정본이다. 없으면 사용자 URL을 받는다.
- "레퍼런스 이미지를 --ref로 물리면 비슷하게 나오겠지" → 판매처 저작물이다. 참고로만 보고 생성 입력에 넣지 않는다.
- "pumasi:image 질문이 귀찮으니 imagen.sh를 직접" → 스킬 경유 원칙 위반.
- "환불 불가라니 '만족 보장'이라고 부드럽게" → 정책 그대로. 다른 리스크 감소 장치로.

## Spirit vs Letter

규칙의 정신은 하나다 - **주인공은 구매를 망설이는 고객이고, 그 고객에게 지킬 수 있는 약속만 선명하게 한다.** 8섹션 헤딩 형식이나 12자 제한은 이 정신을 지키는 도구다. 플랫폼 특성상 섹션을 합치거나 순서를 미세 조정해야 하면(예: 크몽은 Q6 구성을 상단에) 정신을 지키는 쪽으로 판단하고 review-log에 이유를 남긴다. 반대로 형식을 다 지켰는데 Q1이 여전히 제품 자랑이면 통과가 아니다.

## Settings

| 설정 | 기본값 | 변경 방법 |
|---|---|---|
| 플랫폼 | 웹 랜딩 (16:9 히어로, 720px) | 착수 시 "스마트스토어용"/"크몽용" 또는 Step 2 질문 |
| 컷 수 | 14컷 (건기식 기본 시퀀스) | 10~20 사이에서 조정. "카피만" → 이미지 0장(텍스트 플레이스홀더 시안) |
| 이미지 톤 | 브랜드 주색 1 + 뉴트럴 3(탄·크림·연회색) + 포인트 1, 컷마다 배경 전환 | 착수 시 색·분위기·기존 로고 경로 제공 |
| 이미지 퀄리티 | 고품질 | "시안으로" → 초안 퀄리티 |

## References

- `references/framework.md` - 8질문 프레임워크 정본: 원칙 9개, 안티패턴, 섹션별 임무·재료·이미지 역할, 카피 작성 규칙
- `references/intake-checklist.md` - 필수 입력 4종, 슬롯 10개, 플레이스홀더 규칙, 타겟 좁히기 절차
- `references/interview.md` - 불확실성 기반 제품 인터뷰: 우선순위, 질문 은행(옵션 설계), 스킵 규칙, 1라운드 예시 JSON
- `references/review-checklist.md` - 문장 단위 검수법, 구조 체크 C1~C10, 이미지·HTML 검수 항목
- `references/verification.md` - 검증 3중 게이트: 자동 검사 항목표, 고객 시뮬 리뷰어 4인 프롬프트 골격과 통과 기준, 렌더·5초 테스트 절차, 스코어카드 형식
- `references/evidence.md` - 8질문을 뒷받침·보완하는 외부 근거(A~C등급만): 표준 anatomy, 인식 단계, 첫 화면 데이터, VoC 실측, 프레임워크 대응표. 카피 인용용이 아니라 "왜 이 규칙인가" 설명용
- `references/compliance.md` - 규제 업종 표현 필터: 식품표시광고법 금지 유형, 건강기능식품 고시 문구·심의·필수 표시, 일반식품 기능성 표시 조건
- `references/humanize.md` - Step 4-1 윤문: GPT(codex)용 시스템 프롬프트 정본(humanize-korean AI 티 분류 차용), 컷별 가드 규칙, 결과 판독법
- `references/numerical-provenance.md` - T5 정량 문장 출처 계약, 위치별 승인 형식, 사람 검토와 자동 검사의 경계
- `references/style-packs.md` - 스타일 팩 6종(story-first/checkpoint/proof-first/lookbook/spec-showcase/offer-first): 해부 실측 사실 7개, 추천 규칙, 팩이 파이프라인에 주는 것, 공통 문법, 신규 템플릿 P1~P5·X1~X10
- `references/cut-sheet.md` - 컷 시트 문법(cuts.md·legal.md), 기본 14컷 시퀀스, 텍스트 안전 규칙, 앵커 규칙
- `references/reference-patterns.md` - 컬리·쿠팡·정관장몰·삼성·LG 실제 상세 5종 해부: 형식 결론, 타이포·여백·색 실측, 초기 컷 템플릿 카탈로그(현재 전체 44종은 assets/cut-templates.json), 8질문↔컷 매핑, 법정 표시 배치, 채널별 차이
- `references/image-briefs.md` - 컷 이미지 생성 규격: 앵커→--ref 순서, 포그라운드·재개 규칙, 텍스트+물리 정합성 검수, 질문 스킵 키워드, 컷 프롬프트 골격, 저장 경로
- `references/reference-capture.md` - 레퍼런스 수집(Step 1-1, insane-research-refs 호출 계약)과 새 카테고리·채널 상세 해부 절차: 후보 고르기, 캡처 스크립트, 채널별 차단 함정(스마트스토어 로그인 벽·쿠팡 paseo 우회), 조각·해부 에이전트 프롬프트, 템플릿 등록

## Scripts

- `scripts/check_cuts.py` - 검증 게이트 1(컷 시트). 컷 문법·템플릿 슬롯 한도·Q 커버리지·앵커·법정 가드·숫자 출처·금지어·legal 블록·이미지 실존, `qa/check_cuts.json`, FAIL이면 exit 1
- `scripts/humanize_cuts.py` - Step 4-1 윤문. cuts.md 카피를 codex(GPT)가 재생성 → 숫자·플레이스홀더·슬롯·금지어 가드 통과 컷만 치환, `cuts.humanized.md`+`qa/humanize.json`, `--apply`/`--dry-run`/`--from-json`
- `scripts/check_copy.py` - 게이트 1(문단형 copy.md 호환 모드)
- `scripts/assemble_html.py` - cuts.md + legal.md → index.html 컷 조립. 문단형 레거시 모드에서는 copy.md + images.json(문단·불릿·표·CTA·플레이스홀더). 표준 라이브러리만. 누락 섹션·이미지·플레이스홀더를 JSON으로 보고
- `scripts/check_deps.sh` - Step 0 의존성 점검·자동 설치·업데이트(gptaku-plugins 마켓·pumasi·insane-research 2.11.0+·insane-search·codex 플래그·playwright·python3)
- `scripts/capture_reference.js` - 레퍼런스 상세페이지 헤드풀 Chrome 전체 캡처 + 큰 이미지 인벤토리(Node+Playwright)
- `scripts/render_check.py` - 검증 게이트 3. Playwright(Node)로 viewport 에뮬레이션 스크린샷 + 가로 스크롤·헤드라인·CTA·이미지 계측 + HTML 글자 크기·명암비 검사와 컷 이미지 표시 배율, `qa/render_check.json`
- `scripts/check_refs.py` - Step 1-1 수집 검증. manifest의 `ok`를 긴 상세 이미지 유무로 다시 판정(`detail`/`partial:*`), `refs/refs_check.json`
- `scripts/review_stamp.py` - 리뷰한 카피의 컷·legal 섹션 해시 기록(`record`)과 이후 변경 탐지(`verify`), `qa/review-stamp.json`

## Assets

- `assets/cut-templates.json` - 컷 템플릿 44종 규격(높이 범위·슬롯 글자 한도·Q·영문 레이아웃 서술). check_cuts.py와 이미지 프롬프트가 읽는다
- `assets/humanize-schema.json` - humanize_cuts.py가 프롬프트에 인라인하는 GPT 응답 스키마(컷 id·meaning·바뀐 필드)
- `assets/style-packs/*.json` - 스타일 팩 정본(`_schema.json`). `sequence`·`typography`·`layout`·`emphasis`·`visual_mode`·`image_prompt_style`·`grammar`·`fits`. 브랜드·사이트명 금지(tests가 검사)
- `assets/channel-presets.json` - 채널별 export 폭·최대 높이·용량·이미지 내 텍스트 정책(status verified/unverified - 미확정 규격은 보고에 표기)
- `assets/banned-words.json` - 카테고리별(common/q1_hero/food/health_food/cosmetics) 금지·경고 정규식
- `assets/template.html` - 모바일 우선 단일 파일 HTML 템플릿. `{{TITLE}}` `{{WIDTH}}` `{{PLATFORM}}` `{{SECTIONS}}` 치환
