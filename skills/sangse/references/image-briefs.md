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

### 제품 사양 일치 — 필수 통과 기준

생성 전에 raw-input·intake·legal에서 해당 컷에 보이는 제품의 개수, 구획 수,
용량, 구성품, 라벨 표시, 보관 조건을 확인한다. 이 항목은 장식이 아니라
구매 약속이다. 다음 중 하나라도 다르면 FAIL이며 “소소한 편차”로 승인하지 않는다.

- 30칸 체크 카드는 실제로 셀 30개가 보여야 한다. 5열×6행처럼 셀을 셀 수 있는
  정면 구도로 생성한다. 36칸 격자를 30칸이라고 표기하면 실패다.
- 7일 케이스는 서로 구분되는 수납칸 7개가 보여야 한다. 원근·가림 때문에 셀 수
  없으면 `미검증`으로 남기고 구도를 바꾼다. 5칸·6칸을 허용하지 않는다.
- 구성 컷에는 입력에 약속한 구성품을 빠짐없이 표시한다. 소개 리플릿이나
  체크 카드도 상품 구성에 포함되어 있으면 생략할 수 없다.
- 라벨의 함량·인증을 증거로 제시한다면 실제 제공된 라벨 자료가 그 내용을
  보여야 한다. 생성한 무문자 라벨을 실제 증빙으로 설명하지 않는다.
- 상온 보관을 고온의 차량·여름 가방 보관까지 확대하거나, 섭취 편의를
  즉각적인 각성·효과로 바꾸지 않는다. 카피와 이미지 모두 같은 조건을 지킨다.

검수 기록에는 `기대 사양 / 관찰한 사양 / PASS·FAIL·미검증 / 이미지 경로·해시`를
남긴다. 실패한 이미지는 최종본으로 교체하지 않는다. 재생성 후 같은 항목을 다시
확인하며, 해결하지 못했으면 미완성 컷으로 보고한다. 가상 예제는 실제 제품·인증의
증거가 아니며, 원자료와 최종 예제 안내에 가상 설정임을 표시한다.

## 1-1. 스타일 팩이 프롬프트에 주는 것

`cuts.md` 헤더 `style:`의 팩(`assets/style-packs/<id>.json`)을 읽어 앵커 프롬프트에 넣는다: `image_prompt_style`(스타일 줄), `layout.align`(좌/중앙), `emphasis`(형광 박스·콜아웃·큰 숫자·영문 라벨 중 그 컷에 맞는 1~2개), `visual_mode`(실사/라이프스타일/일러스트/모델/렌더), `color_strategy`(배경 교차·단색·화이트+포인트). 참조(`--ref`)가 있는 컷은 스타일 줄을 걷어내고 팩의 `emphasis`만 남긴다. 팩 문장에 브랜드·사이트명은 없다 — 있으면 버그다.

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
[참조 없음(앵커)] 스타일: {style-pack.image_prompt_style — cuts.md `style:` 팩의 문장. 팩이 없으면 "사실적 제품 사진(DSLR 룩) + 정갈한 편집 디자인"}. 정렬 {style-pack.layout.align}, 강조 {style-pack.emphasis 중 1~2}. 브랜드 주색 {primary}, 뉴트럴 {neutral}, 포인트 {accent}. 조명 {방향·색온도}.

Layout: {cut-templates.json[tpl].layout}
Background: {bg}
Visual: {visual}

Text Integration (render exactly, Korean, bold sans-serif unless noted):
- Headline (65~75px equivalent at 1000px width, {text_pos}): "{headline 행1}" / "{headline 행2}"
- Sub (at least 40px, medium weight, same ink as body): "{sub}"
- Body (at least 36px, {줄 수} lines, last line bold): "{body 줄1}" / "{body 줄2}" / "{body 줄3}"
- Label/tags (at least 36px): "{tags}"
- Footnote (at least 30px, dark grey #444 or darker, bottom): "{footnote}"
Text color: near-black (#222~#333) on light backgrounds, pure white on dark backgrounds; contrast at least 4.5:1 for every line. No light-grey or pastel body text. Text never sits directly on a busy photo area — put it on a flat background zone or a solid panel.
No other text. No prices, phone numbers, chart values or small print. Leave 60px safe margin on both sides; nothing important within 40px of top/bottom edges.

Anti-patterns: floating product on plain white with a generic shadow; splash effects; neural-network or hexagon motifs; faces with identifiable features (use faceless line illustrations or hands only); text smaller than 36px (footnote 30px) at 1000px width; grey or low-contrast sub/body text; English placeholder text.
Technical: {높이 힌트 — Vertical 3:4 portrait composition 등}, High quality refined detail, PNG, deliver raw as-is.
```

- `headline`의 `|`는 행 구분으로 풀어 쓴다. 각 행을 따옴표로 묶어 **그대로** 넣는다.
- 고시 기능성 문구(K7)·각주(K4)는 한 글자도 바꾸지 않는다.
- K8 근거 카드: 차트 영역은 "blank framed chart panel, no bars or numbers"로 비워 두고 수치는 HTML로.
- 가격·할인은 C2 CTA 컷에서만, 그것도 플랫폼이 이미지 안 가격을 허용할 때만.

## 4. 저장·기록

- 저장 경로: `sangse/{slug}/images/c{nn}.png` (pumasi:image의 target 인자로 직접 지정. 기본 `images/{날짜}/`가 아니라 산출물 폴더 안에 둔다 — 예시 배포·상대경로 유지 목적. 재인코딩·리사이즈 금지). 백엔드 원본이 JPEG이면 실제 `path:`의 `.jpg` 또는 `.jpeg`를 그대로 사용한다. JPEG를 `.png`로 이름만 바꾸지 않는다.
- `cuts.md` 각 컷의 `image:`에 상대경로 기록. `check_cuts.py`가 실존·폭≥900을 검사한다.
- 스마트스토어 등록 시 860 폭으로 줄여야 하면 등록 단계에서 플랫폼이 축소하도록 두고 원본은 유지한다.

## 5. 텍스트 렌더 한계 (gpt-image-2, 2026-05 기준)

- 할 수 있다: 16pt 이상 굵은 한글·영문 헤드라인, 숫자 단순 표기, 헤드+서브+태그 한 컷 통합.
- 약하다: 8pt 이하 본문, 50자 이상 단락, 가격·전화번호·날짜 정확성, 손글씨 한글, 차트 값.
- **최소 글자 크기는 모바일 표시 크기에서 거꾸로 잡는다.** 폭 1000 이미지는 390px 화면에서 0.39배로 줄어든다. 원본 24px 본문은 9px, 20px 각주는 8px가 돼 읽히지 않는다(2026-10-20 E2E 5초 테스트 가독성 지적 4건의 원인). 그래서 서브 40px·본문·태그 36px·각주 30px 이상(폭 1000 기준, 390에서 약 14px), 글자색은 밝은 배경에 #222~#333·어두운 배경에 흰색, 명암비 4.5:1 이상이다. 회색 본문·밝은 배경 위 연한 서브는 검수 FAIL. `render_check.py`가 컷마다 `cutImageScale.px1000For14`(이 폭에서 14px가 되는 폭 1000 환산 px — 이 문서의 단위)와 `sourcePxFor14`(원본 px)를 남기므로 이미지 검수는 그 값과 대조한다.
- **알약 모양 해시태그 칩 안 글자는 잘 커지지 않는다.** 2026-10-25 E2E에서 "36px 이상" → "46px 크게" → "서브 줄과 같은 크기" 세 번 지시해도 칩 안 글자가 원본 34~37px(폭 1254, 390에서 약 12px)에 머물렀다. 본문·서브·말풍선은 같은 지시로 16px 이상이 나왔다. 태그가 390에서 14px가 안 나오면 재시도를 늘리지 말고 "이미지 검수 미완"으로 남기거나 칩을 빼고 일반 텍스트 줄로 바꾸는 구도 변경을 시도한다.
- 따라서 컷당 텍스트 10줄 이하, 줄당 24자 이하. 본문 길면 두 컷으로 나눈다. 첫 결과가 깨지면 "굵은 고딕, 대형, 정확한 자모"를 명시해 재생성.
