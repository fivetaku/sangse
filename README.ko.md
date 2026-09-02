[English](README.md) | 한국어

# sangse (상세) — 상세페이지 제작 플러그인

제품 정보를 던지면 **검증된 이미지 컷 시트**를 만드는 Claude Code 플러그인입니다. 컬리·쿠팡·네이버 스마트스토어·브랜드 자사몰이 실제로 쓰는 형식 — 폭 1000px 세로 컷 12~20장, 카피는 이미지 안, 법정 표시는 HTML 블록 — 그대로입니다.

라이브 예시(가상 건강기능식품 3종): https://fivetaku.github.io/sangse/

## 하는 일

1. **의존성 점검** — gptaku-plugins 마켓플레이스, `pumasi`(`/pumasi:image`, Codex 이미지 생성), Playwright, python3를 확인하고 `--install`로 설치를 시도합니다.
2. **제품 인터뷰** — 정말 불확실한 슬롯만 묻습니다(타겟·플랫폼·유입 경로·증거 자료·환불 정책·규제 업종). 최대 4문항 × 2라운드.
3. **오퍼 선행 점검** — 오퍼는 "고객이 받는 것 + 줄어드는 불안 + 지금 이유"입니다. 오퍼가 약하면 카피를 쓰기 전에 알립니다.
4. **컷 시트**(`cuts.md` + `legal.md`) — 기본 14컷. 고객이 결제 전에 조용히 던지는 8가지 질문 순서(나를 위한 건가 → 뭘 얻나 → 왜 이 방식 → 나도 될까 → 얼마나 힘든가 → 정확히 뭘 받나 → 실패하면 → 왜 지금)로 편성합니다. 컷 하나 = 메시지 하나: 헤드 17자 이내, 본문 3줄, 배경색, 비주얼 지시. 실제 페이지에서 실측한 템플릿 29종(건기식·패션·서비스). 가격·전화번호·영양표·법정 표시는 HTML로 남깁니다.
5. **검증 3중 게이트**
   - 게이트 1 `check_cuts.py` — 결정론적: 템플릿 슬롯 한도, Q 커버리지, **모든 숫자의 입력 출처 추적**, 카테고리 금지어, legal 블록, 이미지 실존.
   - 게이트 2 — 작성자와 분리된 리뷰어 에이전트 4인(의심 많은 타겟 고객·규제 심사관·CRO 리뷰어·경쟁사 마케터). 고객 8/8 "네" + 규제 위반 0건까지 최대 2라운드.
   - 게이트 3 `render_check.py` — Playwright 실제 렌더(390/860px) + 첫 화면 5초 테스트.
6. **컷 이미지** — `/pumasi:image`로 앵커 컷 먼저, 나머지는 `--ref` 체인. 모든 컷을 텍스트 정확도 **와** 제품 물리 상태(미개봉 포장·개수·손가락)로 검수합니다.
7. **HTML 조립** — 컷을 여백 없이 세로로 쌓고 아래에 legal 블록. 스마트스토어 860px / 웹 720px.

**Iron Law**: 입력에 없는 것은 만들지 않습니다 — 사례·수치·후기·환불 조건·기한. 빈 자리는 `[자료 필요: …]`로 남기고 보고서에 표로 정리합니다.

## 이런 분을 위한 도구입니다

- 제품은 만들었는데 스펙 나열이 아니라 팔리는 상세페이지가 필요한 1인 창업가·바이브코더
- 카피·이미지·법정 블록을 한 번에 만들고 검증까지 받고 싶은 스마트스토어·쿠팡·크몽 셀러
- 기능 나열형 소개글을 근거 없는 주장 없이 고객 언어로 바꿔야 하는 분

## 요구사항

- gptaku-plugins 마켓플레이스가 등록된 Claude Code, 컷 이미지용 `pumasi` 플러그인(없으면 카피·HTML 플레이스홀더까지만)
- `image_generation`이 켜진 Codex CLI(이미지 백엔드)
- python3(게이트·조립기는 표준 라이브러리만)
- Node + Playwright(게이트 3 렌더 계측, 선택 — `~/.insane-search/node/node_modules`를 자동 탐색)
- `bash skills/sangse/scripts/check_deps.sh --install`이 위를 점검·설치

## 설치

```bash
claude plugin marketplace add fivetaku/gptaku_plugins
claude plugin install sangse@gptaku-plugins
claude plugin install pumasi@gptaku-plugins     # 이미지 생성 백엔드
codex features enable image_generation
```

설치 후 Claude Code 세션을 재시작합니다. 그다음:

```
/sangse <제품 정보 텍스트, 파일 경로, URL>
/sangse 카피만 …        # 카피 승인까지만, 이미지 없이
```

"상세페이지 만들어줘"라고 말해도 자동으로 실행됩니다.

## 컴플라이언스

`references/compliance.md`에 **식품·건강기능식품** 상세 필터(식품표시광고법 8조, 고시 기능성 문구, 사전 심의, 필수 표시, 일반식품 기능성 표시 규정)와 화장품·의료기기·금융·교육·부동산·전자제품의 법령 인덱스가 있습니다. 업종별 상세 필터는 작성 중입니다. 법률 자문이 아니며 최종 문구는 심의기관 확인을 전제로 합니다.

## 레퍼런스 해부

형식은 실제 상세페이지를 헤드풀 브라우저로 캡처해 컷 단위로 해부한 결과입니다: 컬리·쿠팡·브랜드 자사몰(같은 건기식 3채널), 삼성닷컴, LG전자, 무신사(패션), 크몽(서비스). 실측치·템플릿 29종은 `references/reference-patterns.md`, 캡처 절차와 채널별 함정(스마트스토어 로그인 벽, 쿠팡 봇 차단)은 `references/reference-capture.md`와 `scripts/capture_reference.js`에 있습니다.

## 구성요소

```
sangse/
├── .claude-plugin/plugin.json
├── commands/sangse.md                 # 진입점
├── skills/sangse/
│   ├── SKILL.md                       # 워크플로우·Iron Law·Red Flags
│   ├── references/                    # framework, cut-sheet, reference-patterns, interview,
│   │                                  # compliance, verification, evidence, image-briefs, reference-capture
│   ├── scripts/                       # check_deps.sh, check_cuts.py, check_copy.py, assemble_html.py,
│   │                                  # render_check.py, capture_reference.js
│   └── assets/                        # cut-templates.json, banned-words.json, template.html
├── setup/                             # 최초 실행 셋업(gptaku 표준)
├── examples/                          # 가상 상품 3종 전 과정 산출물 + qa/
└── index.html                         # GitHub Pages 인덱스
```

## 변경 이력

[CHANGELOG.md](CHANGELOG.md) 참조.

## 라이선스

MIT — [LICENSE](LICENSE), [DISCLAIMER.md](DISCLAIMER.md).
