# sangse (상세) — 매출이 나는 상세페이지 제작 스킬

Claude Code 스킬. 제품·서비스 정보를 던지면 **"고객이 결제 전 조용히 던지는 8가지 질문"** 순서로 상세페이지 카피를 쓰고, 승인 뒤 섹션 이미지(`/pumasi:image`)와 HTML 시안까지 조립한다.

> 원전: 다크 파운더 「매출 떡상하는 상세페이지의 비밀, 지금까지 여러분은 예쁜 쓰레기를 만들고 있었습니다」 https://youtu.be/zJzdTyDxxi8

## 핵심

| 고객의 질문 | 섹션이 하는 일 |
|---|---|
| Q1 이게 나를 위한 건가? | 제품명 대신 **고객의 고민 장면**으로 시작. 좁은 타겟 |
| Q2 그래서 뭘 얻나? | 눈앞에 잡히는 **도착 장면** |
| Q3 왜 이 방식이어야 하나? | 기존 방식의 한계 → 우리 메커니즘. **기능은 여기서만** |
| Q4 정말 나도 가능할까? | 사례·**결과물 미리보기**·전후 |
| Q5 얼마나 힘들고 오래? | 단계 + 수고를 줄이는 장치 |
| Q6 정확히 뭘 받나? | 목록 아닌 **여정 순서** |
| Q7 실패하면? | 환불·보증을 **정책 그대로** |
| Q8 왜 지금? | 기한·한정 + CTA |

**Iron Law**: 입력에 없는 사례·수치·후기·환불·기한은 만들지 않는다. `[자료 필요: …]`로 드러낸다.

## 예시 (GitHub Pages)

지역 특산품 건강기능식품 가상 상품 3종: https://fivetaku.github.io/sangse/

- 풍기골 홍삼 데일리스틱 — 검색 유입형
- 광양골 매실 데일리젤리 — 광고 콜드 유입형
- 제주숲 녹차 카테킨 캡슐 — 환불 불가를 샘플팩으로 뒤집은 오퍼

세 상품·수치·인증은 전부 가상 설정이며, 노란 박스는 실제 자료가 들어와야 완성되는 자리다.

각 예시 폴더의 `qa/`에 검증 3중 게이트 산출물이 그대로 들어 있다: `check_copy.json`(자동 검사), `sim-review-r1/r2.md`(고객·규제·CRO·경쟁사 4인 리뷰, 홍삼만 실행), `render_check.json` + `render-390/860.png`(실제 렌더 계측), `five-second.md`(첫 화면 5초 테스트). 게이트가 실제로 잡아낸 것: Q1에 CTA가 없으면 모바일 첫 CTA가 두 화면 밖으로 밀림, 9:16 이미지가 데스크톱 폭에서 헤드라인을 첫 화면 밖으로 밀어냄, 사양 표 미렌더, 7 mg 함량의 맥락 부재, 후기 부재를 환불 정책으로만 메우려는 약점.

## 설치

```bash
git clone https://github.com/fivetaku/sangse ~/.claude/skills/sangse
```

이미지 생성을 쓰려면 [gptaku-plugins](https://github.com/gptaku/gptaku-plugins)의 `pumasi` 플러그인(`/pumasi:image`, Codex CLI 필요)이 설치돼 있어야 한다. 없으면 카피 + HTML까지만 만든다.

## 사용

```
/sangse 우리 제품 정보야: (텍스트·파일 경로·URL)
```

또는 "상세페이지 만들어줘", "스마트스토어 상세 써줘"라고 말하면 자동 트리거된다.

흐름: 정보 수집 → **제품 인터뷰**(불확실한 것만, 최대 4문항 × 2라운드) → 오퍼 점검 → 8섹션 카피 → **검증 게이트 1** 자동 검사(스크립트) → **게이트 2** 고객 시뮬레이션 리뷰(의심 많은 고객·규제 심사관·CRO·경쟁사 마케터 4인 병렬, 고객 8/8 네까지 최대 2라운드) → **카피 승인** → 이미지(필수 4장) → HTML 조립 → **게이트 3** 실제 렌더 + 5초 테스트 → 스코어카드 보고.

산출물은 프로젝트 루트 `sangse/{slug}/`에 쌓인다: `raw-input.md`, `intake-checklist.md`, `offer-check.md`, `copy.md`, `review-log.md`, `image-briefs.md`, `images.json`, `index.html`.

## 구조

```
sangse/
├── SKILL.md                      # 워크플로우·Iron Law·Red Flags
├── references/
│   ├── framework.md              # 8질문 정본, 원칙, 안티패턴, 카피 규칙
│   ├── interview.md              # 불확실성 기반 인터뷰 질문 은행
│   ├── intake-checklist.md       # 필수 입력·슬롯·플레이스홀더 규칙
│   ├── review-checklist.md       # 문장 검수·구조 체크·완료 보고
│   ├── image-briefs.md           # pumasi:image 호출 규격
│   ├── evidence.md               # 8질문을 뒷받침·보완하는 외부 근거(A~C등급)
│   └── compliance.md             # 규제 업종 표현 필터 (식품·건기식 상세, 그 외 법령 인덱스)
├── references/verification.md    # 검증 3중 게이트(자동 검사·고객 시뮬 리뷰·렌더/5초 테스트)
├── scripts/check_copy.py         # 게이트 1: 구조·숫자 출처·금지어·CTA·표·이미지 자동 판정
├── scripts/assemble_html.py      # copy.md + images.json → index.html (표준 라이브러리만)
├── scripts/render_check.py       # 게이트 3: Playwright 렌더 스크린샷 + 레이아웃 계측
├── assets/template.html          # 모바일 우선 단일 파일 템플릿
└── examples/                     # 가상 상품 예시
```

## 라이선스

MIT
