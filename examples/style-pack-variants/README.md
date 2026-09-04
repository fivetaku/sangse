# style-pack-variants — 같은 제품, 다른 팩

`punggi-red-ginseng-stick` 입력(raw-input·intake·legal은 그 폴더 것을 그대로 사용)을 세 스타일 팩으로 편성한 컷 시트다. 이미지는 없다 — 팩이 시퀀스·팔레트·정렬을 어떻게 바꾸는지 카피 수준에서 비교하는 용도.

| 폴더 | 팩 | 첫 3컷 | 특징 |
|---|---|---|---|
| story-first/ | 고민 장면 스토리형 | X9 K2 K6 | 고객 목소리 말풍선 오프너, 다크·탄 배경 교차, 클로징 오퍼(X10) |
| checkpoint/ | 핵심 포인트 체크리스트형 | K2 K5 K6 | 밝은 배경만, 전부 중앙 정렬, 포인트 3 심화 + STEP 라인아트 + 구성품 그리드 |
| proof-first/ | 근거·수치 우선형 | P1 K2 P2 | 근거 히어로 → 인증·수상 배지 그리드 → 리뷰 그리드(자료 없는 칸은 [자료 필요]) |

세 시트 모두 `check_cuts.py --category health_food --platform smartstore` PASS, T8(팩 시퀀스) PASS. 실험 기록: 마켓 레포 `RESEARCH/sangse_style_pack_sources_20260903_210901/outputs/07_pack_experiment.md`.

## 비식품 3팩 (가상 입력 포함)

| 폴더 | 팩 | 입력 | 첫 3컷 | 특징 |
|---|---|---|---|---|
| lookbook/ | 룩북형 | 린넨 셔츠(common/web) | F1 F2 F3 | 무카피 컷 3, 좌측 정렬, 배경 3종, 헤드 평균 5자 |
| spec-showcase/ | 스펙 쇼케이스형 | 무선 미니 가습기(common/smartstore) | S1 S1 P3 | 네이비↔그레이 교차, 중앙 정렬, 좌우 비교·수치 카드 |
| offer-first/ | 혜택·구성 프로모션형 | 손글씨 클래스 랜딩(common/web) | C2 K10 K5 | 할인 숫자 히어로(랜딩 전용), 혜택 01~07, 계단식 가격표 |

각 폴더에 raw-input·intake·legal이 함께 있어 `check_cuts.py <폴더> --category common --platform web|smartstore`로 재검증할 수 있다. 6팩 쌍별 시퀀스 유사도 최대 0.67, 대부분 0.1~0.4.
