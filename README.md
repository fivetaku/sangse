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

흐름: 정보 수집 → **제품 인터뷰**(불확실한 것만, 최대 4문항 × 2라운드) → 오퍼 점검 → 8섹션 카피 → 의심 많은 고객 눈 검수 → **카피 승인** → 이미지(필수 4장) → HTML 조립 → 보고.

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
├── scripts/assemble_html.py      # copy.md + images.json → index.html (표준 라이브러리만)
├── assets/template.html          # 모바일 우선 단일 파일 템플릿
└── examples/                     # 가상 상품 예시
```

## 라이선스

MIT
