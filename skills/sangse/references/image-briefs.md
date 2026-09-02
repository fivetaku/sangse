# 컷 이미지 생성 — /pumasi:image 호출 규격 (컷 시트 모드)

> 이미지 생성은 **반드시 Skill 도구로 `pumasi:image`를 호출**한다(codex exec·imagen.sh 직접 호출 금지 — 프록시 우회·실패 사유 표면화가 그 안에 있다). 컷당 1장, `cuts.md`의 각 컷이 곧 브리프다. 레이아웃 서술은 `assets/cut-templates.json`의 `layout`을 그대로 가져온다.

## 1. 실행 순서

1. `cuts.md`가 검증 게이트 1·2와 카피 승인(Step 7)을 통과한 뒤에만 시작한다.
2. **앵커 먼저**: `anchor:`에 지정된 컷(보통 C01 제품명 히어로)을 생성 → Read로 헤드라인 글자·색·재질 확인 → 승인. 이 파일이 시리즈 전체의 스타일 기준이다.
3. 나머지 컷은 전부 `--ref {앵커 경로}`로 생성한다. 프롬프트에서 스타일·조명·색 서술을 걷어내고 "attached reference의 색·조명·재질·톤 유지 + 아래 레이아웃·텍스트만"으로 쓴다. 배경색은 컷마다 `bg:`대로 바꾼다.
4. 병렬화: 제품이 여럿이면 **제품당 에이전트 1개**가 안전하다(같은 앵커를 한 에이전트가 관리). 한 제품 안에서 3~4컷씩 병렬 에이전트로 나눌 수도 있다(각 에이전트가 같은 `--ref`). 총 14컷 ≈ 앵커 2분 + 13컷 × 1~1.5분.
   - **에이전트는 imagen.sh를 포그라운드로 실행**한다. 백그라운드로 띄우면 에이전트 턴이 "생성 중입니다"로 끝나 검수·기록 없이 유실된다(2026-09-02 실측).
   - **재개 규칙**: `images/cNN.png`가 이미 있으면 생성하지 않고 Read 검수만 한다. 사용자 인터럽트로 에이전트가 중단돼도 있는 컷부터 이어 간다.
   - 메인 세션은 생성 중에 다른 작업(스킬 갱신·문서)을 하고, 앵커가 나오면 즉시 Read로 확인한다 — 앵커 결함은 뒤 13컷이 전부 물려받는다.
5. 결과 `path:`를 `cuts.md`의 해당 컷 `image:`에 기록한다. 실패 컷은 `image: [이미지 생성 실패 — 재시도 필요]`로 두고 다음 컷으로(조립기는 텍스트 플레이스홀더로 렌더한다).
6. 텍스트가 든 컷은 전부 Read로 1회 검수(review 모드)한다 — 컷 시트는 모든 컷에 텍스트가 있으므로 전수 검수다. 검수 항목은 **텍스트 + 제품 물리 정합성** 둘 다:
   - 텍스트: 자모 오류, 잘림, 누락, 지시하지 않은 글자(영문 플레이스홀더·라벨 글자).
   - 물리 정합성: 포장이 **미개봉 상태**인가(사방 실링, 뜯긴 자국·내용물·액체 노출 없음 — 개봉 연출은 cuts.md `visual`에 명시한 컷만), 제품과 포장·소품이 한 덩어리로 붙지 않았는가, 개수가 카피와 맞는가(캡슐 2개, 스틱 30포), 손가락 개수·손 모양, 텍스트가 제품에 가려지지 않는가.
   - 위반 시 프롬프트에 구체적 제약("completely sealed sachet, no jelly visible, stick and pouch are separate objects")을 넣어 1~2회 재생성. 앵커 컷의 위반은 뒤 컷이 전부 물려받으므로 **앵커는 두 항목 모두 통과한 뒤에만** 체인을 시작한다. HTML 후합성으로 도피하지 않는다(사용자가 명시 요청할 때만).
   - 실측 사례(2026-09-02): 매실 젤리 앵커에서 스틱 끝이 뜯겨 젤리가 밀려 나온 채 렌더됐는데 텍스트 검수만 해서 통과됨 → 사용자가 발견. 물리 정합성 항목을 추가한 이유.

## 2. 질문 폭발 억제 — args 필수 키워드

| 스킵 대상 | 넣을 키워드 |
|---|---|
| 백엔드 | `코덱스로` |
| 비율 | `세로 {폭}:{높이}` 예: 폭 1000, h=1350 → `세로 20:27`. 단순화: h≤750 → `가로 4:3`, 750<h≤1100 → `정방형 1:1`, h>1100 → `세로 3:4`. 실측 픽셀은 생성 후 sips로 확인 |
| 퀄리티 | `고품질` |
| 의도 3개 | 스타일·배경·구도를 문장으로 명시(아래 골격) |

## 3. 프롬프트 골격 (컷 1장)

```
코덱스로 {비율 키워드} 고품질 — 상세페이지 컷 {Cnn} ({템플릿 이름}), 폭 1000px 기준.
[참조 있음] Keep the exact color palette, lighting, material rendering and typographic tone of the attached reference image. Change only the layout, subject arrangement and text below.
[참조 없음(앵커)] 스타일: 사실적 제품 사진(DSLR 룩) + 정갈한 편집 디자인. 브랜드 주색 {primary}, 뉴트럴 {neutral}, 포인트 {accent}. 조명 {방향·색온도}.

Layout: {cut-templates.json[tpl].layout}
Background: {bg}
Visual: {visual}

Text Integration (render exactly, Korean, bold sans-serif unless noted):
- Headline (65~75px equivalent at 1000px width, {text_pos}): "{headline 행1}" / "{headline 행2}"
- Sub (32px, thin weight): "{sub}"
- Body (24px, {줄 수} lines, last line bold): "{body 줄1}" / "{body 줄2}" / "{body 줄3}"
- Label/tags: "{tags}"
- Footnote (20px, grey, bottom): "{footnote}"
No other text. No prices, phone numbers, chart values or small print. Leave 60px safe margin on both sides; nothing important within 40px of top/bottom edges.

Anti-patterns: floating product on plain white with a generic shadow; splash effects; neural-network or hexagon motifs; faces with identifiable features (use faceless line illustrations or hands only); text smaller than 20px equivalent; English placeholder text.
Technical: {높이 힌트 — Vertical 3:4 portrait composition 등}, High quality refined detail, PNG, deliver raw as-is.
```

- `headline`의 `|`는 행 구분으로 풀어 쓴다. 각 행을 따옴표로 묶어 **그대로** 넣는다.
- 고시 기능성 문구(K7)·각주(K4)는 한 글자도 바꾸지 않는다.
- K8 근거 카드: 차트 영역은 "blank framed chart panel, no bars or numbers"로 비워 두고 수치는 HTML로.
- 가격·할인은 C2 CTA 컷에서만, 그것도 플랫폼이 이미지 안 가격을 허용할 때만.

## 4. 저장·기록

- 저장 경로: `sangse/{slug}/images/c{nn}.png` (pumasi:image의 target 인자로 직접 지정. 기본 `images/{날짜}/`가 아니라 산출물 폴더 안에 둔다 — 예시 배포·상대경로 유지 목적. 재인코딩·리사이즈 금지).
- `cuts.md` 각 컷의 `image:`에 상대경로 기록. `check_cuts.py`가 실존·폭≥900을 검사한다.
- 스마트스토어 등록 시 860 폭으로 줄여야 하면 등록 단계에서 플랫폼이 축소하도록 두고 원본은 유지한다.

## 5. 텍스트 렌더 한계 (gpt-image-2, 2026-05 기준)

- 할 수 있다: 16pt 이상 굵은 한글·영문 헤드라인, 숫자 단순 표기, 헤드+서브+태그 한 컷 통합.
- 약하다: 8pt 이하 본문, 50자 이상 단락, 가격·전화번호·날짜 정확성, 손글씨 한글, 차트 값.
- 따라서 컷당 텍스트 10줄 이하, 줄당 24자 이하, 최소 20px 상당. 본문 길면 두 컷으로 나눈다. 첫 결과가 깨지면 "굵은 고딕, 대형, 정확한 자모"를 명시해 재생성.
