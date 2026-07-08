# Site Debug Mode — Design

**Date:** 2026-07-08
**Product:** Django only (`VocabLarry/Python/Django/`)
**Status:** Approved by user (conversation, 2026-07-08)

## Purpose

Let staff/admin users manage site content (vocab + grammar) directly on the
main website instead of only through `/dashboard/` or `/django-admin/`. The
site stays the "original website" experience; a **Debug** toggle reveals
inline add / edit / delete controls.

## Decisions (settled with user)

- **Lives on the main site** (`vocab-master.html` SPA), not the dashboard or
  Django admin.
- **Staff/admin only.** Toggle visible only to staff accounts; server
  enforces staff on every write endpoint regardless of UI state.
- **Scope: vocab + grammar content** — Word, Category, GrammarTopic,
  GrammarLessonBlock, GrammarQuestion. CEFR levels and colors stay
  dashboard-only.
- **Editing is inline** via modals on the site, backed by new staff-only
  JSON write endpoints (plain function-based views in the `api` app — no
  DRF, matching the existing API style).

## Access & toggle

- `GET /auth/session/` gains `"isStaff": bool` — true when
  `user.is_staff` or `user.role in ('staff', 'admin')`.
- When `isStaff`, the profile menu shows a **Debug** toggle.
- Toggle state in `sessionStorage` (`debugMode`), default **off** each new
  browser session; survives SPA navigation.
- While on, a small fixed amber "DEBUG" ribbon is visible so the mode is
  never ambiguous.
- The toggle is cosmetic only; authorization lives server-side.

## Debug UI (per surface)

| Surface | Controls |
|---|---|
| Category cards (vocab home) | ✎ edit, ✕ delete per card; "+ Add category" ghost card at the end of each section |
| Word page rows + word detail modal | ✎ / ✕ per word; "+ Add word" button in the browse bar |
| Grammar topic cards | ✎ / ✕ per card; "+ Add topic" ghost card per section |
| Grammar lesson view | hover ✎ / ✕ per lesson block; "+ Add block"; "Manage questions" list with ✎ / ✕ / + per question |

Controls render only when Debug is on; zero DOM footprint otherwise.

## Edit modals

- Styled like the existing word-detail modal (blurred backdrop, themed
  border, Escape/backdrop dismiss).
- Fields mirror the dashboard `ModelForm`s exactly, including raw JSON
  textareas for `GrammarLessonBlock.data` and
  `GrammarQuestion.options`/`answers`, with the same placeholder hints.
- Save → `fetch` with `X-CSRFToken` (SPA already reads the `csrftoken`
  cookie via `getCsrf`) → on success, re-fetch the affected dataset and
  re-render in place.
- Validation errors (400) render under the offending field.
- Delete: confirm dialog "Delete X? This cannot be undone." Topic deletes
  additionally warn that blocks and questions cascade.

## Write API

New endpoints in `api/` (function-based, same idiom as existing views):

```
POST   /api/words/                 create
PATCH  /api/words/<pk>/            update
DELETE /api/words/<pk>/            delete
```

…and the same triple for `categories`, `grammar/topics`,
`grammar/blocks`, `grammar/questions` (blocks and questions take/carry
their `topic` FK).

- `@staff_required` decorator: 403 JSON (`{"error": "staff only"}`) when
  the requester is not staff (same staff test as `isStaff` above).
- Validation delegates to the existing dashboard forms (`WordForm`,
  `CategoryForm`, `GrammarTopicForm`, `GrammarLessonBlockForm`,
  `GrammarQuestionForm`) so inline edits obey identical rules to
  dashboard edits — including the grammar JSON shape checks.
- Success responses return the object as JSON (same field shapes the read
  API already uses); DELETE returns `{"ok": true}`.
- CSRF protected (session auth, standard Django middleware).

## Testing

Extend the existing pytest suite (`python -m pytest tests`):

- every write endpoint returns 403 for anonymous and non-staff users;
- staff can create / update / delete each of the five models;
- invalid payloads (bad grammar block JSON, MCQ without 4 options, etc.)
  return 400 with field errors;
- `session` endpoint reports `isStaff` correctly for user/staff/admin.

## Out of scope (YAGNI)

- CEFR level / color editing on the site
- Undo / edit history
- Drag-to-reorder (order remains a numeric form field)
- Flask / PHP / React ports
