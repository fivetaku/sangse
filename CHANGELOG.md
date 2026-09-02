# Changelog

## 0.5.0 — 2026-09-02
- Restructured as a gptaku-plugins plugin (`.claude-plugin/plugin.json`, `commands/sangse.md`, `skills/sangse/`, `setup/`).
- README rewritten in English and Korean as a detail-page builder; video-analysis framing removed.
- Fashion cut templates F1~F8 and fashion cut sequence (Musinsa dissection); Kmong (services) dissection recorded.
- Step 0 dependency check (`scripts/check_deps.sh`, `--install`).

## 0.4.1 — 2026-09-02
- Cut image inspection now checks product physical plausibility (sealed packaging, counts, fingers) in addition to text.
- Image-generation agents run imagen in the foreground and resume from existing cuts.

## 0.4.0 — 2026-09-02
- **Image cut sheet format**: `cuts.md` (14 cuts) + `legal.md`, 21 templates measured from Kurly / Coupang / brand mall / Samsung / LG dissections (`references/reference-patterns.md`).
- `check_cuts.py` (gate 1, cut mode), assembler and render check cut modes.
- Reference capture procedure and script (`reference-capture.md`, `capture_reference.js`).

## 0.3.0 — 2026-09-02
- Three-gate verification: deterministic checker, four separate reviewer agents, Playwright render + 5-second test.

## 0.2.0 — 2026-09-02
- Renamed to `sangse`; product interview (uncertainty-driven, ≤4 questions × 2 rounds); research-backed rules (FAQ block, spec table, traffic-source variable, CTA repetition); `compliance.md` for food / health functional food.

## 0.1.0 — 2026-09-02
- First version: 8-question copy framework, Iron Law, paragraph-style copy with four section images.
