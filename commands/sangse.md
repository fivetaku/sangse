---
name: sangse
description: "제품 정보를 이미지 컷 시트 상세페이지로 — 8질문 카피, 컴플라이언스, 3중 검증"
argument-hint: "[제품 정보 텍스트·파일 경로·URL | 카피만 | 스마트스토어용]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - Agent
  - Skill
---

<!-- first-run setup: idempotent, non-blocking, self-skips after first run -->
**Step 0 — run once at the very start, before anything else:** run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" ask`. If its output starts with `STAR_ASK`, immediately call the **AskUserQuestion** tool once, with the question and options phrased **in the user's language**: prefer the current conversation's language if it is evident; otherwise fall back to the language code that follows `STAR_ASK` in the output (`ko`→Korean, `ja`→Japanese, `en`→English). Never default to Korean blindly.
- header: a short localized "GitHub Star" label
- question: ask whether they'd like to give this plugin (and the gptaku-plugins marketplace) a GitHub ⭐ to support it — note it is optional and every feature works either way
- options: exactly two — (1) yes, star it → then run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" star yes`; (2) no thanks → then run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" star no`

If the output is empty, just continue silently. (AskUserQuestion must NOT be in frontmatter allowed-tools.) Do not narrate beyond the question itself.

# /sangse

> **Language (shared/language-policy.md)**: lock `output_lang` to the language of the request text (or, if none, the conversation so far) before reading anything else. Every user-facing output — replies, AskUserQuestion `question`/`header`/`label`/`description`, and files written to disk (`cuts.md`, `legal.md`, the report) — follows `output_lang`. The JSON below is a template: translate its labels, never emit it verbatim in another language. Identifiers, file names, commands and the `[자료 필요: …]` token are not translated. Do not default to Korean because the plugin was made in Korea.
>
> **Questioning (shared/questioning-policy.md)**: ask only slots that cannot be inferred from the input (target, platform, traffic source, proof, refund policy, regulated category); at most 4 questions per round, 2 rounds. If the input already answers a slot, do not ask it.

Build a Korean e-commerce detail page as an **image cut sheet**: 12~20 vertically stacked cuts (headline, sub, body inside the image, Kurly/Coupang/Smart Store convention) plus an HTML legal block, following the "8 questions a customer silently asks before paying" order.

## Parse Arguments

Inspect `$ARGUMENTS`:

| Argument pattern | Action |
|---|---|
| product info (text, file path, URL) | Run the `sangse` skill from Step 0 (dependency check) → Step 1 (collect) |
| contains `카피만` / `copy only` | Same, but stop after the copy approval gate — no image generation |
| contains `스마트스토어` / `크몽` / `웹` | Pre-set the platform, skip that interview question |
| `check <dir>` | Run only the verification gates on an existing `sangse/{slug}` folder (check_cuts.py → render_check.py) |
| (no argument) | Ask for product info with AskUserQuestion — see below |

## No argument

**EXECUTE:** call AskUserQuestion once:

```json
{
  "questions": [
    {
      "question": "어떤 제품·서비스의 상세페이지를 만들까요? 정보를 어떤 형태로 주실 수 있나요?",
      "header": "입력 형태",
      "options": [
        {"label": "텍스트로 붙여넣을게요 (추천)", "description": "제품·타겟·가격·구성·환불 정책을 메모 형태로 그대로 주시면 됩니다"},
        {"label": "파일이 있어요", "description": "PDF·마크다운·기획서 경로를 알려주세요"},
        {"label": "기존 페이지 URL이 있어요", "description": "지금 쓰는 상세·경쟁 페이지 링크. 창업자 언어를 고객 언어로 번역합니다"},
        {"label": "가상 상품으로 연습", "description": "인터뷰 없이 Claude가 설정한 가상 상품으로 전체 흐름을 시연합니다"}
      ],
      "multiSelect": false
    }
  ]
}
```

## Execute

Follow `${CLAUDE_PLUGIN_ROOT}/skills/sangse/SKILL.md` exactly — Step 0 dependency check, product interview (only the uncertain slots), offer check, cut sheet (`cuts.md` + `legal.md`), gate 1 (`check_cuts.py`), gate 2 (4 simulated reviewers), copy approval, cut images via `/pumasi:image` (anchor → `--ref` chain, text + physical-plausibility inspection), HTML assembly, gate 3 (render + 5-second test), scorecard report. Never invent facts that are not in the input; leave `[자료 필요: …]` placeholders.
