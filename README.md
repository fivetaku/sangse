English | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md)

# sangse (상세)

<p align="center">
  <img src="assets/sangse-hero-01.png" alt="sangse" width="320">
</p>

> **Turn a product into a detail page that sells — a verified image cut sheet, not a spec sheet.**

Give it the product facts. Get back the format Korean commerce actually uses: 12~20 vertically stacked image cuts with the copy inside the image, plus an HTML legal block — every claim traced to your input.

[Quick Start](#quick-start) • [Why sangse?](#why-sangse-이런-분을-위한-도구입니다) • [How it works](#how-it-works) • [Features](#features) • [Requirements](#requirements-요구사항)

Live examples (fictional health-food products): https://fivetaku.github.io/sangse/

---

## Quick Start

### 1. Add the marketplace (once)

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. Install

```
/plugin install sangse
/plugin install pumasi          # image generation backend (/pumasi:image)
```

Restart Claude Code after installation.

### 3. Enable the image backend

```bash
codex features enable image_generation
```

### 4. Run

```
/sangse <product info as text, a file path, or a URL>
/sangse 카피만 <product info>        # stop after copy approval, no images
/sangse check sangse/<slug>          # re-run the verification gates on an existing folder
```

Or just say it — "상세페이지 만들어줘", "make a detail page for this product".

---

## Why sangse? (이런 분을 위한 도구입니다)

- **You built a product, not a sales page** — solo founders and vibe-coders who need a detail page that converts, not a feature list.
- **You sell on Kurly, Coupang or Naver Smart Store** — the output is the image cut sheet those channels actually use, sized for upload (Smart Store 860 px / web 720 px).
- **You need copy, images and the legal block verified together** — three gates catch template overflow, untraceable numbers, banned claims and missing mandatory labels before you publish.
- **You will not accept invented claims** — the Iron Law: nothing that is not in the input gets written. Gaps become `[자료 필요: …]` placeholders and a to-do table.

---

## How it works

```
product facts (text / file / URL)
        │
        ▼
Step 0  dependency check          check_deps.sh  (--install)
Step 1  product interview         only the uncertain slots · ≤4 questions × 2 rounds
Step 2  offer check               what the customer gets + which anxiety it removes + why now
Step 3  cut sheet                 cuts.md (14 cuts by default) + legal.md
Step 3½ humanize                  humanize_cuts.py — GPT (Codex CLI) re-reads each cut's meaning and rewrites the copy like a person; per-cut guards keep numbers, placeholders, slot limits
        │
        ├─ Gate 1  check_cuts.py       deterministic: slot limits · Q coverage · every number traced · banned words · legal blocks
        ├─ Gate 2  4 reviewer agents   sceptical customer · regulatory examiner · CRO reviewer · competitor marketer
        └─ copy approval
        │
Step 4  cut images                /pumasi:image — anchor cut first, the rest chained with --ref, text + physical plausibility inspected
Step 5  HTML assembly             assemble_html.py — cuts stacked edge to edge, legal block below
        │
        └─ Gate 3  render_check.py     Playwright render at 390 / 860 px + a 5-second test on the first screen
        │
        ▼
sangse/<slug>/  cuts.md · legal.md · images/ · index.html · qa/ · scorecard
```

The cuts follow the **8 questions a customer silently asks before paying**: Is this for me → What do I get → Why this way → Can I do it → How hard is it → What exactly do I receive → What if it fails → Why now.

---

## Features

| Feature | Description |
|---------|-------------|
| Image cut sheet format | 12~20 cuts, width 1000 px, copy rendered inside the image; prices, phone numbers, nutrition tables and legal notices stay in HTML |
| 29 measured cut templates | Dissected from real pages — Kurly, Coupang, a brand mall, Samsung, LG, Musinsa (fashion), Kmong (services) |
| Uncertainty-driven interview | Asks only what cannot be inferred from the input; at most 4 questions × 2 rounds |
| Offer check before copy | Weak offers are flagged before a single line of copy is written |
| GPT humanize pass | A second model (Codex CLI) interprets what each cut is trying to say and rewrites it without AI tells (translation-ese, ad clichés, uniform rhythm, hedging — rules borrowed from humanize-korean); code guards reject any cut that adds a number, drops a placeholder, overflows a slot or introduces a banned word |
| Gate 1 — deterministic checker | `check_cuts.py`: template slot limits, Q1~Q8 coverage, every number traced to the input, category banned words, mandatory legal blocks, image existence |
| Gate 2 — four reviewer agents | Separate from the writer; pass = customer answers "yes" on all 8 questions and zero regulatory violations, max 2 rounds |
| Gate 3 — real render | `render_check.py`: Playwright render at 390 / 860 px plus a 5-second first-screen test |
| Cut images with inspection | `/pumasi:image` anchor → `--ref` chain; every cut checked for text accuracy **and** product plausibility (sealed packaging, counts, fingers) |
| Compliance filters | `references/compliance.md`: detailed rules for food and health functional food (Food Labeling and Advertising Act art. 8, approved functional claims, pre-review, mandatory labels) and a legal index for cosmetics, medical devices, finance, education, real estate and electronics — category-specific filters for those are in progress |
| Iron Law | No invented cases, numbers, reviews, refund terms or deadlines — placeholders instead |

Nothing here is legal advice; final wording is subject to the relevant review body.

---

## Commands

| Command | Description |
|---------|-------------|
| `/sangse <product info>` | Full run: interview → cut sheet → gates → images → HTML → scorecard |
| `/sangse 카피만 <product info>` | Copy only — stops after the copy approval gate |
| `/sangse 스마트스토어 <product info>` | Pre-set the platform (also `웹`, `크몽`), skip that interview question |
| `/sangse check <dir>` | Run only the verification gates on an existing `sangse/<slug>` folder |
| `/sangse humanize <dir>` | Run only the GPT humanize pass on an existing folder and show what was accepted or rejected |

### Natural language triggers

- "상세페이지 만들어줘", "스마트스토어 상세 만들어줘", "세일즈 페이지 써줘", "이 제품 소개 페이지 써줘"
- "make a detail page", "product page copy", "sales page copy", "landing page copy"

---

## Components (구성요소)

| Path | Role |
|---|---|
| `commands/sangse.md` | Single entry point (`/sangse`), argument routing |
| `skills/sangse/SKILL.md` | Workflow (Step 0 → interview → offer check → cut sheet → 3 gates → images → HTML → report), Iron Law, red flags |
| `skills/sangse/references/` | `framework.md` (8 questions), `cut-sheet.md`, `reference-patterns.md` (7 real pages dissected, 29 templates), `interview.md`, `humanize.md` (GPT rewrite prompt + guards), `compliance.md`, `verification.md`, `evidence.md`, `image-briefs.md`, `reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`, `humanize_cuts.py`, `check_cuts.py`, `check_copy.py`, `assemble_html.py`, `render_check.py`, `capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`, `banned-words.json`, `humanize-schema.json`, `template.html` |
| `setup/` | First-run setup (gptaku standard) |
| `tests/test-gates.sh` | Regression: gate 1 PASS on the three examples, assembler smoke, humanize guards, dependency check, frontmatter contract |
| `examples/` | Three fictional products with the full artefact trail and `qa/` results |

---

## Requirements (요구사항)

- [Claude Code](https://docs.anthropic.com/claude-code) CLI with the gptaku-plugins marketplace
- `pumasi` plugin for cut images (optional — without it the run stops at copy + HTML placeholders)
- [Codex CLI](https://github.com/openai/codex) logged in with `image_generation` enabled (image backend)
- python3 — gates and assembler use the standard library only
- (optional) Node + Playwright for gate 3 render checks; `~/.insane-search/node/node_modules` is picked up automatically
- `bash skills/sangse/scripts/check_deps.sh --install` checks and installs the above

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Release procedure (version bump → GitHub release → marketplace submodule pointer → cache) follows [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md); `tests/test-gates.sh` must pass before every bump.

---

## License (라이선스)

MIT — see [LICENSE](LICENSE) and [DISCLAIMER.md](DISCLAIMER.md).

---

<div align="center">

**Product facts in. A detail page that sells — with nothing made up.**

</div>
