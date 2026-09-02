# Changelog

> 릴리스 절차(버전 bump → GitHub 릴리스 → 마켓 서브모듈 포인터 → 캐시)는 gptaku_plugins의 [PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md)를 따른다. bump 전 `bash tests/test-gates.sh` PASS 필수.

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
