# Grammar Section — Beginner to Advanced

**Date:** 2026-07-05
**Status:** Approved
**Scope:** Django product first (`ielts-vocab-master/Python/Django/vocab-master.html`); Flask/PHP/React ports in a follow-up effort.

## Summary

Replace the Grammar under-construction placeholder with a full grammar curriculum: 36 hand-authored topics across 3 CEFR-style stages (Beginner A1–A2, Independent B1–B2, Expert C1–C2), each topic pairing a lesson page with a 10-question practice quiz. Completion is tracked in localStorage; a topic is "done" at a best score ≥ 80%.

## Current Behaviour

`#page-grammar` is a static placeholder: page-head ("Section 02 / Grammar") plus an under-construction setup-card. The Grammar tab in the topbar navigates to it via the existing `data-section-btn` mechanism. No grammar data or logic exists.

## Architecture

All content lives in a single hand-authored `GRAMMAR` constant inside `vocab-master.html`, alongside the existing `SECTIONS` map. No backend models, migrations, or API endpoints — grammar is a fixed curriculum, not user data. Rendering is fully client-side. Only learning progress is dynamic, stored in localStorage.

Rationale: keeps the planned Flask/PHP (single-file) and React ports trivial — the data structure and render logic transplant verbatim, matching how previous features were ported.

## Data Model

```js
const GRAMMAR = [
  {
    id: "beginner",              // stage
    name: "Beginner",
    cefr: "A1–A2",
    topics: [
      {
        id: "articles",          // stable slug; localStorage key
        title: "Articles (a/an/the)",
        tag: "Determiners",      // card pill label
        cefr: "A1–A2",           // card chip
        blurb: "One-line teaser shown on the topic card",
        lesson: [                // ordered blocks, rendered top-to-bottom
          { type: "intro",    html: "..." },
          { type: "rule",     title: "Form", html: "..." },
          { type: "table",    title: "Tense map", head: ["...", "..."], rows: [["...", "..."]] },
          { type: "examples", items: [{ en: "...", note: "..." }] },
          { type: "tip",      html: "..." }   // IELTS usage tip callout
        ],
        quiz: [ /* 10 questions */ ]
      }
    ]
  }
];
```

### Question shapes

| type | Fields | Checking |
|---|---|---|
| `mcq` | `q`, `options` (4), `answer` (index), `why` | option click |
| `gap` | `q` (with `___`), `answers` (array of accepted strings), `why` | typed input; trim, collapse spaces, case-insensitive |
| `transform` | `prompt`, `given`, `answers` (accepted variants), `why` | typed input, same normalisation; used sparingly (≤2 per quiz) since free-text checking is strict |

Every question carries a `why` explanation line shown after answering.

## UI Flow

Three views inside `#page-grammar`, toggled with the same show/hide pattern as the Test page (`testSetup`/`testPlay`/`testResult`):

1. **Grammar home** (`#grammarHome`) — page-head, then 3 stage groups styled like the CEFR browse view: ghost numeral, stage name, CEFR range, and a per-stage progress bar ("3/12 topics"). Under each, a grid of resource-cards reusing the category-card look: tag pill, CEFR chip, ↗ arrow; green bar + medal treatment when the topic is done.
2. **Lesson view** (`#grammarLesson`) — breadcrumb back to Grammar home, topic title + CEFR chip, lesson blocks rendered per type (rule boxes, striped form tables, example list using ex-item styling, tip callout), ending with a "Practice — 10 questions" button.
3. **Quiz view** (`#grammarQuiz`) — reuses the quiz-wrap/result-card component styling from the Vocabulary Test: one question at a time, immediate right/wrong feedback with the `why` line, result card at the end with score, "Retry" and "Back to Grammar" actions.

Navigation state (which stage/topic/view is open) is in-memory only; landing on the Grammar tab always shows Grammar home.

## Progress

- localStorage key `grammarProgress` → `{ [topicId]: { best: <0–100>, done: <bool> } }`
- `done` becomes true when best score ≥ 80%; never reverts on later worse attempts (best is a high-water mark)
- Done topics get the mastered card treatment and count into stage progress bars
- The topbar "Learned x/5000" counter remains vocabulary-only
- The existing reset-progress button also clears `grammarProgress` (same confirm dialog)
- Malformed or missing `grammarProgress` JSON falls back to `{}` silently

## Quiz Behaviour & Edge Cases

- Questions presented in authored order (no shuffling in v1); MCQ options shown as authored
- Submitting an empty `gap`/`transform` input is blocked with a nudge message, not counted wrong
- Leaving mid-quiz (navigating away) discards the attempt; scores are only recorded on the result screen
- Score = correct/total as a percent, rounded to nearest integer

## Curriculum (36 topics, 12 per stage, ~360 questions)

**Beginner (A1–A2):** Present Simple & Continuous · Past Simple & Continuous · Future Forms (will / going to) · Question Forms & Short Answers · Word Forms (noun/verb/adj/adv) · Articles (a/an/the) · Nouns, Plurals & Countability · Quantifiers (some/any/much/many, there is/are) · Pronouns & Possessives · Comparatives & Superlatives · Prepositions of Time & Place · Adverbs & Word Order

**Independent (B1–B2):** Perfect Tenses (incl. continuous forms) · Passive & Active Voice · Reported Speech · Conditionals 0–3 · Relative Clauses (defining & non-defining) · Modal Verbs (ability, obligation, deduction) · Gerunds vs Infinitives · Used to / Would / Be used to · Wish & If only · Causatives (have/get something done) · Question Tags & Indirect Questions · Linking Words & Cohesion

**Expert (C1–C2):** Inversion & Emphasis · Cleft Sentences · Subjunctive & Unreal Past · Advanced Modality · Participle Clauses · Nominalisation · Hedging & Academic Tone · Mixed Conditionals · Ellipsis & Substitution · Dummy Subjects (it/there constructions) · Fronting & -ever Clauses · Gradable Adjectives & Intensifiers

Folded sub-points (no standalone topic): so/such/too/enough → Linking Words & Cohesion; -ed/-ing adjectives → Gradable Adjectives & Intensifiers; reduced relative clauses → Participle Clauses; imperatives → Question Forms & Short Answers; basic can/must → Modal Verbs; future perfect/continuous → Perfect Tenses.

Content style: hand-authored, IELTS-flavoured example sentences (band-style academic register where natural). Each topic: 1 intro block, 1–3 rule blocks, 0–2 tables, 1 examples block (4–6 items), 1 tip block, 10 quiz questions (mostly `mcq` + `gap`, ≤2 `transform`).

## Design Language

Follows the LexiLoop luxury/editorial system: mono eyebrow labels, Fraunces italic accents, ghost numerals on stage headers, resource-card topic cards, badge/chip components, both light "gallery" and dark "velvet" themes. All icons from the existing inline SVG sprite (no emoji).

## Testing / Verification

- Run the Django server; click through every stage → topic card → lesson → quiz → result
- Verify: progress persists across reload; reset button clears grammar progress; done topics show mastered treatment and stage bars update; empty-input nudge works; both themes render correctly
- Spot-check content accuracy per stage (a sample of rules/answers per topic)
