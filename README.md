English | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md)

# sangse (상세) — Korean e-commerce detail page builder

<p align="center">
  <img src="assets/sangse-hero.png" alt="sangse — example anchor cut (fictional product)" width="320">
</p>

A Claude Code plugin that turns product facts into a **verified image cut sheet** — the format real Korean commerce detail pages actually use (Kurly, Coupang, Naver Smart Store, brand malls): 12~20 vertically stacked image cuts with the copy rendered inside the image, plus an HTML legal block.

Live examples (fictional health-food products): https://fivetaku.github.io/sangse/

## What it does

1. **Dependency check** — verifies the gptaku-plugins marketplace, `pumasi` (`/pumasi:image`, Codex image generation), Playwright and python3; offers `--install`.
2. **Product interview** — asks only the slots that are genuinely uncertain (target, platform, traffic source, proof, refund policy, regulated category), max 4 questions × 2 rounds.
3. **Offer check before copy** — an offer is what the customer receives + which anxiety it removes + why now. Weak offers are flagged before any copy is written.
4. **Cut sheet** (`cuts.md` + `legal.md`) — 14 cuts by default, ordered by the 8 questions a customer silently asks before paying (Is this for me → What do I get → Why this way → Can I do it → How hard → What exactly → What if it fails → Why now). Each cut = one message: headline ≤17 chars, ≤3 body lines, background colour, visual brief. 29 cut templates measured from real pages (health food, fashion, service). Prices, phone numbers, nutrition tables and legal notices stay in HTML.
5. **Verification, three gates**
   - Gate 1 `check_cuts.py` — deterministic: template slot limits, Q coverage, **every number traced to the input**, category banned words, legal blocks, image existence.
   - Gate 2 — four separate reviewer agents (sceptical target customer, regulatory examiner, CRO reviewer, competitor marketer). Pass = customer answers "yes" on all 8 questions and zero regulatory violations; max 2 rounds.
   - Gate 3 `render_check.py` — real Playwright render at 390/860 px plus a 5-second test on the first screen.
6. **Cut images** via `/pumasi:image` — anchor cut first, the rest chained with `--ref`, every cut inspected for text accuracy **and** product plausibility (sealed packaging, counts, fingers).
7. **HTML assembly** — cuts stacked edge to edge, legal block below, Smart Store 860 px / web 720 px.

**Iron Law**: nothing that is not in the input gets invented — no cases, numbers, reviews, refund terms or deadlines. Gaps are left as `[자료 필요: …]` placeholders and listed in the report.

## Who this is for (이런 분을 위한 도구입니다)

- Solo founders and vibe-coders who built a product and now need a detail page that sells rather than a spec sheet.
- Smart Store / Coupang / Kmong sellers who want the copy, images and legal block generated and verified together.
- Anyone who has to rewrite a feature-list product page into customer language without inventing claims.

## Requirements (요구사항)

- Claude Code with the gptaku-plugins marketplace; `pumasi` plugin for image cuts (optional — without it the skill stops at copy + HTML placeholders)
- Codex CLI logged in with `image_generation` enabled (image backend)
- python3 (gates and assembler use the standard library only)
- Node + Playwright for gate 3 render checks (optional; `~/.insane-search/node/node_modules` is picked up automatically)
- `bash skills/sangse/scripts/check_deps.sh --install` checks and installs the above

## Install

```bash
claude plugin marketplace add fivetaku/gptaku_plugins
claude plugin install sangse@gptaku-plugins
claude plugin install pumasi@gptaku-plugins     # image generation backend
codex features enable image_generation
```

Restart the Claude Code session after installing. Then:

```
/sangse <product info as text, a file path, or a URL>
/sangse 카피만 …        # stop after copy approval, no images
```

Or just say "상세페이지 만들어줘" — the skill auto-triggers.

## Components (구성요소)

| Path | Role |
|---|---|
| `commands/sangse.md` | Single entry point (`/sangse`), argument routing |
| `skills/sangse/SKILL.md` | Workflow (Step 0 dependency check → interview → offer check → cut sheet → 3 gates → images → HTML → report), Iron Law, red flags |
| `skills/sangse/references/` | `framework.md` (8 questions), `cut-sheet.md`, `reference-patterns.md` (7 real pages dissected, 29 templates), `interview.md`, `compliance.md`, `verification.md`, `evidence.md`, `image-briefs.md`, `reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`, `check_cuts.py`, `check_copy.py`, `assemble_html.py`, `render_check.py`, `capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`, `banned-words.json`, `template.html` |
| `setup/` | First-run setup (gptaku standard) |
| `examples/` | Three fictional products with the full artefact trail and `qa/` results |

## Compliance

`references/compliance.md` carries detailed filters for **food and health functional food** (Food Labeling and Advertising Act art. 8, approved functional claim wording, pre-review, mandatory labels, general-food functional claim rules) and a legal index for cosmetics, medical devices, finance, education, real estate and electronics. Category-specific filters for those are in progress. Nothing here is legal advice; final wording is subject to the relevant review body.

## Reference dissection

The format was derived by capturing real detail pages in a headful browser and dissecting them cut by cut: Kurly, Coupang and a brand mall (same health-food product across three channels), Samsung.com, LG.com, Musinsa (fashion) and Kmong (services). Findings, measurements and 29 templates are in `references/reference-patterns.md`; the capture procedure and channel-specific traps (Smart Store login wall, Coupang bot block) are in `references/reference-capture.md` with `scripts/capture_reference.js`.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Release procedure (version bump → GitHub release → marketplace submodule pointer → cache) follows [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md); `tests/test-gates.sh` must pass before every bump.

## License (라이선스)

MIT — see [LICENSE](LICENSE) and [DISCLAIMER.md](DISCLAIMER.md).
