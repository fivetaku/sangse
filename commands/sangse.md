---
name: sangse
description: "제품 정보를 이미지 컷 시트 상세페이지로 - 8질문 카피, 컴플라이언스, 3중 검증"
argument-hint: "[제품 정보 텍스트·파일 경로·URL | 카피만 | 스마트스토어용 | --style <pack> | check <dir> | humanize <dir>]"
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
**Step 0 - run once at the very start, before anything else:** run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" ask autoupdate`. If its output starts with `STAR_ASK`, immediately call the **AskUserQuestion** tool once, with the question and options phrased **in the user's language**: prefer the current conversation's language if it is evident; otherwise fall back to the language code that follows `STAR_ASK` in the output (`ko`→Korean, `ja`→Japanese, `en`→English). Never default to Korean blindly.
- header: a short localized "GitHub Star" label
- question: ask whether they'd like to give this plugin (and the gptaku-plugins marketplace) a GitHub ⭐ to support it - note it is optional and every feature works either way
- options: exactly two - (1) yes, star it → then run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" star yes`; (2) no thanks → then run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" star no`
- If the output contains a line `AUTOUPDATE_ASK <lang>`: ask the user ONCE with AskUserQuestion, written in the language the user is using in this conversation (fall back to <lang> — ko/ja/en — only if the conversation gives no signal). Question: gptaku-plugins can update itself automatically so you always get fixes without running /plugin manually. Turn on auto-update? Options (2): "Turn on auto-update" / "Not now".
  - "Turn on auto-update" → run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" autoupdate yes` (prints `AUTOUPDATE_SET <status>`; on `on`/`already` say it is enabled, otherwise say it could not be changed and point to /plugin → Marketplaces → gptaku-plugins → Turn on auto-update).
  - "Not now" → run `bash "${CLAUDE_PLUGIN_ROOT}/setup/setup.sh" autoupdate no`.
  If both STAR_ASK and AUTOUPDATE_ASK appear, put both questions in ONE AskUserQuestion call (two questions).

If the output is empty, just continue silently. (AskUserQuestion must NOT be in frontmatter allowed-tools.) Do not narrate beyond the question itself.

# /sangse

인자: `$ARGUMENTS`

`${CLAUDE_PLUGIN_ROOT}/skills/sangse/SKILL.md`를 Read로 끝까지 읽고 그 절차(인자 처리 표 → Step 0~11)를 그대로 따른다. 언어·질문 규칙(`shared/language-policy.md`, `shared/questioning-policy.md`)과 AskUserQuestion 호출 지시도 SKILL.md에 있다. 입력에 없는 사실은 만들지 않고 `[자료 필요: …]` 플레이스홀더로 둔다.
