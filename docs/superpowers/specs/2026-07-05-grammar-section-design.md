# Grammar Section — Beginner to Advanced

**Date:** 2026-07-05
**Status:** Approved (rev 2 — database-backed, dashboard-managed)
**Scope:** Django product only (`ielts-vocab-master/Python/Django/`). Django is the main focus; Flask/PHP/React ports are out of scope for this effort (they can later consume the seed JSON as static data).

## Summary

Replace the Grammar under-construction placeholder with a full grammar curriculum: 36 hand-authored topics across 3 CEFR-style stages (Beginner A1–A2, Independent B1–B2, Expert C1–C2), each topic pairing a lesson page with a 10-question practice quiz. Content lives in Django models, is editable through the existing staff dashboard, is served by a new API endpoint, and ships pre-loaded via a seed JSON + management command. Learner progress is tracked in localStorage; a topic is "done" at a best score ≥ 80%.

## Current Behaviour

`#page-grammar` in `vocab-master.html` is a static placeholder: page-head ("Section 02 / Grammar") plus an under-construction setup-card. The Grammar tab navigates to it via the existing `data-section-btn` mechanism. No grammar data, models, or logic exist.

## Architecture

Follows the established three-app split:

- **Models** in the `vocab` app (alongside Word/Category/CEFRLevel)
- **Read-only JSON endpoint** in the `api` app (same style as `/api/words/`)
- **Staff CRUD** in the `dashboard` app (same list/form/delete pattern as Words)
- **Seeding** via a management command reading a repo JSON file (mirrors `import_vocab`)

The SPA fetches `/api/grammar/` once when the Grammar tab first opens (cached in memory for the session) and renders stages → topic cards → lesson → quiz entirely client-side. Only learner progress is dynamic, stored in localStorage — no server-side progress.

## Models (vocab/models.py)

```python
class GrammarTopic(models.Model):
    STAGES = [('beginner', 'Beginner'), ('independent', 'Independent'), ('expert', 'Expert')]
    slug       = models.SlugField(max_length=100, unique=True)   # stable id; localStorage key
    title      = models.CharField(max_length=200)
    tag        = models.CharField(max_length=50)                 # card pill label
    cefr_label = models.CharField(max_length=10)                 # card chip, e.g. "B1–B2"
    blurb      = models.CharField(max_length=300)                # card teaser line
    stage      = models.CharField(max_length=12, choices=STAGES)
    order      = models.PositiveSmallIntegerField(default=0)
    # Meta: ordering = ['stage', 'order']

class GrammarLessonBlock(models.Model):
    TYPES = [('intro', 'Intro'), ('rule', 'Rule'), ('table', 'Table'),
             ('examples', 'Examples'), ('tip', 'Tip')]
    topic = models.ForeignKey(GrammarTopic, on_delete=models.CASCADE, related_name='blocks')
    type  = models.CharField(max_length=10, choices=TYPES)
    title = models.CharField(max_length=200, blank=True)         # used by rule/table
    body  = models.TextField(blank=True)                         # HTML for intro/rule/tip
    data  = models.JSONField(default=dict, blank=True)           # table: {head:[], rows:[[]]}; examples: {items:[{en, note}]}
    order = models.PositiveSmallIntegerField(default=0)
    # Meta: ordering = ['order']

class GrammarQuestion(models.Model):
    QTYPES = [('mcq', 'Multiple choice'), ('gap', 'Fill the gap'), ('transform', 'Transformation')]
    topic   = models.ForeignKey(GrammarTopic, on_delete=models.CASCADE, related_name='questions')
    qtype   = models.CharField(max_length=10, choices=QTYPES)
    prompt  = models.TextField()                                 # mcq/gap question text ("___" marks the gap); transform: instruction + given sentence
    options = models.JSONField(default=list, blank=True)         # mcq only: 4 strings
    answers = models.JSONField(default=list)                     # mcq: [correct_index]; gap/transform: accepted strings
    why     = models.TextField()                                 # explanation shown after answering
    order   = models.PositiveSmallIntegerField(default=0)
    # Meta: ordering = ['order']
```

### Question checking (client-side)

| qtype | Checking |
|---|---|
| `mcq` | clicked option index equals `answers[0]` |
| `gap` | typed input vs `answers`: trim, collapse spaces, case-insensitive |
| `transform` | same normalisation vs accepted variants; used sparingly (≤2 per quiz) since free-text checking is strict |

## API (api/views.py)

`GET /api/grammar/` — `@require_GET`, JsonResponse, no auth (same as existing endpoints). Returns:

```json
[
  { "id": "beginner", "name": "Beginner", "cefr": "A1–A2",
    "topics": [
      { "slug": "articles", "title": "Articles (a/an/the)", "tag": "Determiners",
        "cefr": "A1–A2", "blurb": "...",
        "lesson": [ { "type": "rule", "title": "Form", "body": "...", "data": {} } ],
        "quiz":   [ { "qtype": "mcq", "prompt": "...", "options": ["..."], "answers": [2], "why": "..." } ]
      }
    ]
  }
]
```

Stage metadata (name, CEFR range) is a fixed mapping in the view — stages are structural, not editable rows. Uses `prefetch_related('blocks', 'questions')` to avoid N+1. Quiz answers being visible in the payload is accepted — this is a learning tool, consistent with the vocabulary test.

## Dashboard (staff-gated, mirrors Words CRUD)

- **Topics list** (`/dashboard/grammar/`) — table of topics with stage filter (like the word list's category/CEFR filters), block/question counts, add/edit/delete. Delete is guarded only by the standard confirm (blocks/questions cascade).
- **Topic form** — add/edit fields: slug, title, tag, cefr_label, blurb, stage, order. The edit page links to that topic's blocks and questions lists.
- **Blocks list + form** (`/dashboard/grammar/<pk>/blocks/…`) — per-topic, ordered; form fields: type, title, body (textarea, HTML allowed), data (JSON textarea), order.
- **Questions list + form** (`/dashboard/grammar/<pk>/questions/…`) — per-topic, ordered; form fields: qtype, prompt, options (JSON textarea), answers (JSON textarea), why, order.
- Dashboard index gains a "Grammar topics" count card.
- Forms validate JSON fields (options/answers/data) and enforce shape: mcq needs 4 options and one valid index; gap/transform need ≥1 accepted answer.

## Seeding

- `grammar-content.json` in the Django project root: the full authored curriculum (36 topics with blocks and questions), the single source of truth for initial content.
- `python manage.py import_grammar` (vocab app management command, mirrors `import_vocab`): idempotent upsert by topic slug — replaces each topic's blocks and questions from the file. Run once after migrating.

## UI Flow (vocab-master.html)

Three views inside `#page-grammar`, toggled with the same show/hide pattern as the Test page (`testSetup`/`testPlay`/`testResult`):

1. **Grammar home** (`#grammarHome`) — page-head, then 3 stage groups styled like the CEFR browse view: ghost numeral, stage name, CEFR range, and a per-stage progress bar ("3/12 topics"). Under each, a grid of resource-cards reusing the category-card look: tag pill, CEFR chip, ↗ arrow; green bar + medal treatment when the topic is done. While `/api/grammar/` loads, show the standard loading state; on fetch failure, show a retry message in place of the grid.
2. **Lesson view** (`#grammarLesson`) — breadcrumb back to Grammar home, topic title + CEFR chip, lesson blocks rendered per type (rule boxes, striped form tables, example list using ex-item styling, tip callout), ending with a "Practice — 10 questions" button.
3. **Quiz view** (`#grammarQuiz`) — reuses the quiz-wrap/result-card component styling from the Vocabulary Test: one question at a time, immediate right/wrong feedback with the `why` line, result card at the end with score, "Retry" and "Back to Grammar" actions.

Navigation state (which stage/topic/view is open) is in-memory only; landing on the Grammar tab always shows Grammar home.

## Progress

- localStorage key `grammarProgress` → `{ [topicSlug]: { best: <0–100>, done: <bool> } }`
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
- A topic whose quiz has 0 questions (possible via dashboard edits) hides the practice button and can't be marked done

## Curriculum (36 topics, 12 per stage, ~360 questions)

**Beginner (A1–A2):** Present Simple & Continuous · Past Simple & Continuous · Future Forms (will / going to) · Question Forms & Short Answers · Word Forms (noun/verb/adj/adv) · Articles (a/an/the) · Nouns, Plurals & Countability · Quantifiers (some/any/much/many, there is/are) · Pronouns & Possessives · Comparatives & Superlatives · Prepositions of Time & Place · Adverbs & Word Order

**Independent (B1–B2):** Perfect Tenses (incl. continuous forms) · Passive & Active Voice · Reported Speech · Conditionals 0–3 · Relative Clauses (defining & non-defining) · Modal Verbs (ability, obligation, deduction) · Gerunds vs Infinitives · Used to / Would / Be used to · Wish & If only · Causatives (have/get something done) · Question Tags & Indirect Questions · Linking Words & Cohesion

**Expert (C1–C2):** Inversion & Emphasis · Cleft Sentences · Subjunctive & Unreal Past · Advanced Modality · Participle Clauses · Nominalisation · Hedging & Academic Tone · Mixed Conditionals · Ellipsis & Substitution · Dummy Subjects (it/there constructions) · Fronting & -ever Clauses · Gradable Adjectives & Intensifiers

Folded sub-points (no standalone topic): so/such/too/enough → Linking Words & Cohesion; -ed/-ing adjectives → Gradable Adjectives & Intensifiers; reduced relative clauses → Participle Clauses; imperatives → Question Forms & Short Answers; basic can/must → Modal Verbs; future perfect/continuous → Perfect Tenses.

Content style: hand-authored, IELTS-flavoured example sentences (band-style academic register where natural). Each topic: 1 intro block, 1–3 rule blocks, 0–2 tables, 1 examples block (4–6 items), 1 tip block, 10 quiz questions (mostly `mcq` + `gap`, ≤2 `transform`).

## Design Language

Follows the LexiLoop luxury/editorial system: mono eyebrow labels, Fraunces italic accents, ghost numerals on stage headers, resource-card topic cards, badge/chip components, both light "gallery" and dark "velvet" themes. All icons from the existing inline SVG sprite (no emoji).

## Testing / Verification

- Migrations apply cleanly; `import_grammar` seeds 36 topics and is idempotent (second run changes nothing)
- `/api/grammar/` returns all stages/topics/blocks/questions with no N+1 queries
- Dashboard: create/edit/delete a topic, block, and question; JSON field validation rejects malformed input; stage filter works; index count card shows
- SPA: click through every stage → topic card → lesson → quiz → result; progress persists across reload; reset button clears grammar progress; done topics show mastered treatment and stage bars update; empty-input nudge works; fetch-failure retry state renders; both themes render correctly
- Spot-check content accuracy per stage (a sample of rules/answers per topic)
