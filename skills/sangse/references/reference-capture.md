# 레퍼런스 수집·해부 절차 — 매 실행 수집, 새 카테고리·채널은 패턴으로 해부

> `reference-patterns.md`는 건기식(정관장 3채널) + 가전 2개 + 패션 1개를 해부한 결과다(상단 "해부된 카테고리" 목록). 다른 카테고리(뷰티·가구·강의·서비스)나 채널(올리브영·크몽)의 상세를 만들 때 패턴이 없으면 이 절차로 먼저 해부한다. 2026-09-02 실행에서 확인된 함정을 그대로 담았다.

## 0. 레퍼런스 수집 (Step 1-1, 매 실행)
후보 찾기와 이미지 수집은 insane-research가 정본이다. sangse는 이름으로 부르기만 하고 검색·크롤링 절차를 따로 두지 않는다.

- **호출**: Skill `insane-research:insane-research-refs`, args 예 — `주제=선크림 상세페이지, 채널=올리브영·컬리·자사몰, pages=5, out=sangse/{slug}/refs, 함께 넣을 URL=<사용자 URL>`. 백그라운드 에이전트 1개가 호출하고 `REFS:` 줄과 표만 돌려준다.
- **결과**: `refs/candidates.md`(도메인·제목·이미지 수·가장 긴 이미지·상태·선정 이유·URL), `refs/manifest.json`(이미지별 원본 URL·폭×높이·SHA-256), `refs/images/pNN/`.
- **상태 읽기**: 수집기의 `ok`는 긴 상세 이미지를 보장하지 않는다(썸네일만 받아도 `ok`). 먼저 `scripts/check_refs.py sangse/{slug}`로 다시 판정한다. `detail`(높이 1500px 이상 이미지 있음) → 상세 원본을 이미 받았다(§3으로 바로). `partial:thumbs`·`partial:empty` → 상세 미확보, §2 캡처 대상. `no_large_images` → HTML에 상세가 없다, JS 렌더가 필요하면 §2 캡처. `blocked:*` → 아래 채널별 함정 표를 본다.
- **없을 때**: insane-research가 설치돼 있지 않으면 즉석 검색으로 대신하지 않는다. 설치 명령(`claude plugin install insane-research@gptaku-plugins`)과 재시작을 안내하고, Step 2 인터뷰에서 사용자 URL 2~3개를 받아 `사용자 제공`으로 적는다.
- 수집본은 참고 전용이다. 이미지는 판매처 저작물이라 생성 입력(`--ref`)·결과물에 넣지 않는다.

## 1. 해부 대상 고르기 (Step 2-1, 패턴이 없는 카테고리만)
- `refs/candidates.md`에서 같은 제품군을 **채널 3개**(큐레이션 몰·오픈마켓·자사몰)로 잡으면 채널 문법 차이가 드러난다. 가능하면 같은 제품. 후보가 모자라면 2개로 한다.
- 판매 중인 상품인지 확인한다(단종·품절 상품은 상세 이미지가 비어 있거나 거래 정보만 남는다 — 쿠팡 첫 시도, LG Y320GB가 그랬다). 수집기는 판매 여부를 판정하지 않는다.

## 2. 캡처
```bash
cd sangse-작업폴더 && NODE_PATH=~/.insane-search/node/node_modules \
  node ${CLAUDE_PLUGIN_ROOT}/skills/sangse/scripts/capture_reference.js {slug} "{url}" ./captures
```
- 헤드풀 실제 Chrome(patchright → playwright 폴백)으로 모바일 390·데스크톱 1280 전체 캡처 + 폭 300 이상 이미지 인벤토리(`{slug}.json`).
- 수집본(`refs/`)에 상세 원본이 이미 있으면 이 단계를 건너뛴다.
- **상세 이미지 원본**이 핵심이다: json에서 `nh`(naturalHeight)가 수천 px인 `src`가 곧 상세 이미지 한 장(컬리 1010×18,468, 쿠팡 1000×24,750, 정관장몰 1000×27,647). `curl`/`urllib`로 Referer 붙여 다운로드한다.
- 캡처 스크린샷은 lazy 이미지 때문에 비어 있을 수 있다(컬리 모바일이 그랬다). 원본 이미지가 있으면 스크린샷보다 원본을 쓴다.

### 채널별 함정 (실측)
| 채널 | 증상 | 통하는 방법 |
|---|---|---|
| 네이버 스마트스토어·브랜드스토어 | 자동화 브라우저(헤드풀 포함) → `NAVER 로그인` 리다이렉트 | 미해결. 같은 형식인 컬리·쿠팡·자사몰로 대체하거나, 사용자가 로그인된 크롬에서 paseo `browser_evaluate`로 img 목록 추출 |
| 쿠팡 | Playwright·curl_cffi 격자 모두 `Access Denied` / 리스트 HTML만 | **paseo(사용자 크롬 세션) `browser_new_tab` → `browser_evaluate`**로 스크롤 후 `document.images` 계측 → `thumbnail.coupangcdn.com/.../retail/images/...` 원본 URL을 curl로 다운로드. 상세 본문은 1장(1000×N), 780으로 렌더됨 |
| 컬리 | 데스크톱은 정상, 모바일은 상세 미로드 | 데스크톱 캡처 + `product-image.kurly.com` 원본 |
| 자사몰(정관장몰 등) | 정상 | 본문 + 프로모션 보조 이미지가 분리돼 있으니 둘 다 받는다 |
| 삼성닷컴·LG전자 | 정상. HTML 컴포넌트형 | 전체 캡처가 3만px를 넘고 상단부가 반복 캡처될 수 있다(삼성 37,486 중 고유 16,380) — 해부 시 반복 구간을 제외 |

## 3. 조각내기
```python
from PIL import Image; Image.MAX_IMAGE_PIXELS=None
im=Image.open("captures/kurly-detail.jpg"); W,H=im.size
for n,y in enumerate(range(0,H,1400),1): im.crop((0,y,W,min(y+1400,H))).save(f"captures/kurly-cuts/kurly-{n:02d}_y{y}.jpg",quality=80)
```
1,400px 조각(원본 폭 1000 기준)이 에이전트 Read 1회에 텍스트까지 판독되는 상한이다. 모바일 스크린샷(390)은 2,000px.

## 4. 해부 에이전트 (레퍼런스당 1개, 동시 3개까지)
프롬프트에 반드시 넣을 것:
- 조각을 **순서대로 전부 Read**(건너뛰기 금지), 다른 파일 금지.
- **컷 인벤토리 표**: 컷 번호 | 시작 y | 높이 | 컷 유형 | 헤드라인 원문 | 글자 수 | 서브카피 | 줄 수 | 시각 요소 | 배경색 | 텍스트 위치 | 텍스트 면적 비율.
- **8질문 매핑을 정의와 함께**(Q1 나를 위한 건가 … Q8 왜 지금). 정의를 안 주면 에이전트가 자기 정의를 만든다(LG 해부가 그랬다).
- **타이포·레이아웃 실측**: 헤드 글자 수 범위·평균·글자 높이, 본문 높이, 컷당 줄 수, 좌우 여백, 컷 구분 방식, 강조, 숫자.
- **이미지 안 vs 밖**: 법정 표시가 어디에 어떤 크기로 있는지.
- **재사용 컷 템플릿 5~8개**: 이름 | 레이아웃(비율) | 텍스트 슬롯 | 언제.
- `## SOURCES`, `## EXPAND`.
- 응답은 파일 저장 + 5줄 요약만(본문 반복 금지 — 컨텍스트 보호).

## 5. 합치기
1. 해부 파일 5개에서 공통 규칙(컷 규격·타이포·강조·색·비주얼)과 채널 차이를 뽑아 `reference-patterns.md` 형식으로 쓴다.
2. 새 템플릿은 `assets/cut-templates.json`에 ID(카테고리 접두 + 번호), 높이 범위, 슬롯 한도, Q, 영문 `layout`으로 추가한다. `check_cuts.py`와 이미지 프롬프트가 그 파일을 읽는다.
3. 카테고리별 기본 컷 시퀀스를 `cut-sheet.md` §3에 추가한다.

## 6. 검증 안 된 것을 검증 안 됐다고 쓴다
- 수치는 육안 추정(±5px). "이 순서가 전환을 올린다"는 실험이 아니라 관찰이다.
- 1브랜드 3채널 관찰을 카테고리 전체로 일반화하지 않는다. 표본 수를 문서 상단에 적는다.
