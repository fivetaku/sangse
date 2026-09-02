[English](README.md) | 한국어 | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md)

# 상세 (sangse)

<p align="center">
  <img src="assets/sangse-hero-01.png" alt="sangse" width="320">
</p>

> **제품을 팔리는 상세페이지로 — 스펙 나열이 아니라 검증된 이미지 컷 시트.**

제품 정보만 주면, 국내 커머스가 실제로 쓰는 형식 그대로 돌아옵니다: 카피가 이미지 안에 들어간 세로 컷 12~20장 + HTML 법정 표시 블록. 모든 주장은 입력에서 출처를 추적합니다.

[빠른 시작](#빠른-시작) • [왜 sangse인가](#왜-sangse인가-이런-분을-위한-도구입니다) • [작동 방식](#작동-방식) • [주요 기능](#주요-기능) • [요구사항](#요구사항)

라이브 예시(가상 건강기능식품 3종): https://fivetaku.github.io/sangse/

---

## 빠른 시작

### 1. 마켓플레이스 추가 (최초 1회)

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. 설치

```
/plugin install sangse
/plugin install pumasi          # 이미지 생성 백엔드 (/pumasi:image)
```

설치 후 Claude Code를 재시작합니다.

### 3. 이미지 백엔드 켜기

```bash
codex features enable image_generation
```

### 4. 실행

```
/sangse <제품 정보 텍스트, 파일 경로, URL>
/sangse 카피만 <제품 정보>          # 카피 승인까지만, 이미지 없이
/sangse check sangse/<slug>         # 기존 폴더에 검증 게이트만 다시 실행
```

말로 해도 됩니다 — "상세페이지 만들어줘", "이 제품 소개 페이지 써줘".

---

## 왜 sangse인가 (이런 분을 위한 도구입니다)

- **제품은 만들었는데 팔리는 페이지가 없는 분** — 기능 나열이 아니라 결제가 나는 상세페이지가 필요한 1인 창업가·바이브코더.
- **컬리·쿠팡·네이버 스마트스토어에서 파는 분** — 그 채널이 실제로 쓰는 이미지 컷 시트를 업로드 규격(스마트스토어 860px / 웹 720px)으로 바로 받습니다.
- **카피·이미지·법정 블록을 한 번에 검증받고 싶은 분** — 3중 게이트가 템플릿 초과, 출처 없는 숫자, 금지 표현, 필수 표시 누락을 퍼블리시 전에 잡습니다.
- **지어낸 주장을 용납하지 않는 분** — Iron Law: 입력에 없는 것은 쓰지 않습니다. 빈 자리는 `[자료 필요: …]` 플레이스홀더와 준비 목록으로 남깁니다.

---

## 작동 방식

```
제품 정보 (텍스트 / 파일 / URL)
        │
        ▼
Step 0  의존성 점검               check_deps.sh  (--install)
Step 1  제품 인터뷰               불확실한 슬롯만 · 최대 4문항 × 2라운드
Step 2  오퍼 점검                 고객이 받는 것 + 줄어드는 불안 + 지금 이유
Step 3  컷 시트                   cuts.md (기본 14컷) + legal.md
Step 3½ 윤문                      humanize_cuts.py — GPT(Codex CLI)가 컷마다 하려는 말을 해석해 사람 문장으로 재생성, 컷별 가드로 숫자·플레이스홀더·슬롯 한도 보존
        │
        ├─ 게이트 1  check_cuts.py      결정론: 슬롯 한도 · Q 커버리지 · 모든 숫자 출처 · 금지어 · legal 블록
        ├─ 게이트 2  리뷰어 에이전트 4인   의심 많은 고객 · 규제 심사관 · CRO 리뷰어 · 경쟁사 마케터
        └─ 카피 승인
        │
Step 4  컷 이미지                 /pumasi:image — 앵커 컷 먼저, 나머지는 --ref 체인, 텍스트 + 물리 정합성 검수
Step 5  HTML 조립                 assemble_html.py — 컷을 여백 없이 세로로, 아래에 legal 블록
        │
        └─ 게이트 3  render_check.py    Playwright 실제 렌더 390 / 860px + 첫 화면 5초 테스트
        │
        ▼
sangse/<slug>/  cuts.md · legal.md · images/ · index.html · qa/ · 스코어카드
```

컷은 **고객이 결제 전에 조용히 던지는 8가지 질문** 순서를 따릅니다: 나를 위한 건가 → 뭘 얻나 → 왜 이 방식 → 나도 될까 → 얼마나 힘든가 → 정확히 뭘 받나 → 실패하면 → 왜 지금.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 이미지 컷 시트 형식 | 폭 1000px 컷 12~20장, 카피는 이미지 안. 가격·전화번호·영양표·법정 표시는 HTML로 남김 |
| 실측 템플릿 29종 | 실제 페이지 해부에서 도출 — 컬리·쿠팡·브랜드 자사몰·삼성·LG·무신사(패션)·크몽(서비스) |
| 불확실성 기반 인터뷰 | 입력에서 추론 불가한 것만 묻는다. 최대 4문항 × 2라운드 |
| 오퍼 선행 점검 | 오퍼가 약하면 카피 한 줄 쓰기 전에 알린다 |
| GPT 윤문 | 다른 모델(Codex CLI)이 컷마다 하려는 말을 해석한 뒤 AI 티(번역투·광고 상투구·리듬 균일·hedging — humanize-korean 규칙 차용) 없이 다시 쓴다. 숫자 유입·플레이스홀더 소실·슬롯 초과·금지어 유입 컷은 코드가 거부하고 원문 유지 |
| 게이트 1 — 결정론 체커 | `check_cuts.py`: 템플릿 슬롯 한도, Q1~Q8 커버리지, 모든 숫자의 입력 출처, 카테고리 금지어, 필수 legal 블록, 이미지 실존 |
| 게이트 2 — 리뷰어 4인 | 작성자와 분리. 통과 = 고객 8/8 "네" + 규제 위반 0건, 최대 2라운드 |
| 게이트 3 — 실제 렌더 | `render_check.py`: Playwright 390 / 860px 렌더 + 첫 화면 5초 테스트 |
| 컷 이미지 + 검수 | `/pumasi:image` 앵커 → `--ref` 체인. 모든 컷을 텍스트 정확도 **와** 제품 물리 상태(미개봉 포장·개수·손가락)로 검수 |
| 컴플라이언스 필터 | `references/compliance.md`: 식품·건강기능식품 상세 규칙(식품표시광고법 8조, 고시 기능성 문구, 사전 심의, 필수 표시)과 화장품·의료기기·금융·교육·부동산·전자제품 법령 인덱스 — 업종별 상세 필터는 작성 중 |
| Iron Law | 사례·수치·후기·환불 조건·기한을 지어내지 않는다 — 플레이스홀더로 남긴다 |

법률 자문이 아니며 최종 문구는 심의기관 확인을 전제로 합니다.

---

## 명령어

| 명령어 | 설명 |
|--------|------|
| `/sangse <제품 정보>` | 전 과정: 인터뷰 → 컷 시트 → 게이트 → 이미지 → HTML → 스코어카드 |
| `/sangse 카피만 <제품 정보>` | 카피만 — 카피 승인 게이트에서 멈춤 |
| `/sangse 스마트스토어 <제품 정보>` | 플랫폼 선지정(`웹`, `크몽`도 가능), 해당 인터뷰 질문 생략 |
| `/sangse check <dir>` | 기존 `sangse/<slug>` 폴더에 검증 게이트만 실행 |
| `/sangse humanize <dir>` | 기존 폴더에 GPT 윤문만 실행하고 채택·거부 내역을 보여준다 |

### 자연어 트리거

- "상세페이지 만들어줘", "스마트스토어 상세 만들어줘", "세일즈 페이지 써줘", "이 제품 소개 페이지 써줘"
- "make a detail page", "product page copy", "sales page copy", "landing page copy"

---

## 구성요소

| 경로 | 역할 |
|---|---|
| `commands/sangse.md` | 단일 진입점(`/sangse`), 인자 라우팅 |
| `skills/sangse/SKILL.md` | 워크플로우(Step 0 → 인터뷰 → 오퍼 점검 → 컷 시트 → 3 게이트 → 이미지 → HTML → 보고), Iron Law, Red Flags |
| `skills/sangse/references/` | `framework.md`(8질문), `cut-sheet.md`, `reference-patterns.md`(실제 페이지 7종 해부, 템플릿 29종), `interview.md`, `humanize.md`(GPT 윤문 프롬프트·가드), `compliance.md`, `verification.md`, `evidence.md`, `image-briefs.md`, `reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`, `humanize_cuts.py`, `check_cuts.py`, `check_copy.py`, `assemble_html.py`, `render_check.py`, `capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`, `banned-words.json`, `humanize-schema.json`, `template.html` |
| `setup/` | 최초 실행 셋업(gptaku 표준) |
| `tests/test-gates.sh` | 회귀: 예시 3종 게이트 1 PASS, 조립기 스모크, 윤문 가드, 의존성 점검, 프런트매터 계약 |
| `examples/` | 가상 상품 3종의 전 과정 산출물 + `qa/` 결과 |

---

## 요구사항

- gptaku-plugins 마켓플레이스가 등록된 [Claude Code](https://docs.anthropic.com/claude-code) CLI
- 컷 이미지용 `pumasi` 플러그인(선택 — 없으면 카피 + HTML 플레이스홀더까지만)
- `image_generation`이 켜진 [Codex CLI](https://github.com/openai/codex) 로그인(이미지 백엔드)
- python3 — 게이트·조립기는 표준 라이브러리만 사용
- (선택) 게이트 3 렌더 계측용 Node + Playwright. `~/.insane-search/node/node_modules`를 자동 탐색
- `bash skills/sangse/scripts/check_deps.sh --install`이 위를 점검·설치

---

## 변경 이력

[CHANGELOG.md](CHANGELOG.md) 참조. 릴리스 절차(버전 bump → GitHub 릴리스 → 마켓 서브모듈 포인터 → 캐시)는 gptaku_plugins의 [PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md)를 따르고, bump 전에 `tests/test-gates.sh`가 PASS해야 합니다.

---

## 라이선스

MIT — [LICENSE](LICENSE), [DISCLAIMER.md](DISCLAIMER.md).

---

<div align="center">

**제품 정보를 넣으면, 지어낸 것 없이 팔리는 상세페이지가 나온다.**

</div>
