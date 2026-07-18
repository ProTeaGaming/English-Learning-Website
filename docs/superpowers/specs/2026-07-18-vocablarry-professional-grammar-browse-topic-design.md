# VocabLarry Professional Environment — Grammar Browse + Topic (design)

## Context

This is the first Grammar sub-project of the VocabLarry Professional
Environment rebuild (see `docs/superpowers/specs/2026-07-17-vocablarry-professional-foundation-design.md`
for parent context and locked-in architecture decisions). Foundation, Vocab
Browse + Word, and the full Vocab Quiz/Gap/Challenge trio are merged to
`main`. Grammar has been a disabled "coming soon" nav entry since
Foundation.

Unlike every prior Vocab sub-project, **the backend for Grammar already
exists in full** — `GrammarTopic`, `GrammarLessonBlock`, and
`GrammarQuestion` models are byte-for-byte identical ports from production
(same fields, same choices, same relations), and a read-only JSON endpoint
(`/api/grammar/`) already serializes topics nested with their lesson blocks
and quiz questions. No model or backend work is needed anywhere in this
sub-project — only templates, a view, and a URL route are missing. There
are 47 `GrammarTopic` rows already loaded in the dev DB.

Production's Grammar section (`VocabLarry/vocablarry.html`) has three
layers: a section-grouped topic browse (`renderGrammarHome`), a topic
detail page with lesson content plus a per-topic practice quiz
(`openGrammarTopic`), and a separate cross-topic "Grammar Test" mode with
its own mode/topic-picker setup screen (already speced for the *other*
product in `docs/superpowers/specs/2026-07-11-grammar-test-mode-design.md`,
which targets `VocabLarry/vocab-master.html`, not this rebuild). This spec
covers **only the browse + topic-detail layer, read-only, no quiz/practice
interaction at all** — mirroring how Vocab Browse + Word shipped before
any quiz engine existed. The per-topic practice quiz and the cross-topic
Grammar Test are both separate, later sub-projects.

Production groups topics into 12 thematic sections via a **hardcoded,
per-topic-slug JS lookup table** (`GRAMMAR_SECTIONS`, 47 entries) — not a
database field. The `tag` field on `GrammarTopic` looks similar (e.g.
`"Tenses"`, `"Sentence"`, `"Word Building"`) but is confirmed **not** the
same value production actually groups by (e.g. the `question-forms` topic
has `tag="Sentence"` in the DB, but production's real section map assigns
it to `"Questions & Reported Speech"` instead) — production only falls
back to `tag` for topics missing from its hand-authored map. This is the
exact same shape of problem the Vocab Browse + Word sub-project already
hit and deferred (a hardcoded `slug → sectionName` map, there covering 75
sections over ~5,000 words). This spec makes the same call for Grammar.

## Decisions

- **No new backend, no new models, no new migrations.** `GrammarTopic`/
  `GrammarLessonBlock` already exist with every field this sub-project
  needs. The existing `/api/grammar/` endpoint is left untouched and
  unused by this sub-project — server-rendered pages query the ORM
  directly (`GrammarTopic.objects...`, `topic.blocks.order_by('order')`),
  matching the convention already established in Vocab Browse + Word
  ("Don't have a Django view call its own JSON API over HTTP").
- **Flat topic grid, no section grouping** — same call as Vocab Browse +
  Word, for the same reason (the real grouping is a hardcoded slug lookup
  table, not a DB field, and `tag` is confirmed unreliable as a substitute
  since it disagrees with production's actual section assignments for at
  least one topic checked). `tag` is still shown on each topic's card as a
  flavor label (useful, curated metadata), just not used for grouping or
  filtering. Deferred, not rejected — a future sub-project could port the
  real 47-entry section map if section-grouped browsing turns out to be
  wanted, the same way Vocab's 75-section layer remains a documented,
  deferred possibility.
- **Filters: title search + `stage` dropdown.** `stage` (`beginner`/
  `independent`/`expert`, i.e. Basic/Intermediate/Advanced) is the
  model's own clean 3-value choices field, used here the same role Vocab
  Browse's CEFR-level filter played — a level filter fits naturally
  alongside a text search over `title`. `cefr_label` (a free-text field
  like `"A1"`/`"A1+"`, not FK'd to `CEFRLevel`) is shown on the topic
  card as a pill but is not a separate filter in this pass.
- **No progress/mastery UI anywhere in this sub-project.** Production
  shows per-section and per-topic progress bars/medals, all driven by
  quiz-completion tracking (`grammar_map`) that doesn't exist yet in this
  rebuild. Since there is no quiz in this sub-project, there is nothing to
  track — no progress bar, no medal, no "X/Y mastered" anywhere. This
  isn't a simplification decision so much as a direct consequence of
  scope: the data this UI would show doesn't exist yet.
- **Topic detail renders lesson blocks in `order`, one visual treatment
  per `type`:**
  - `intro` / `tip`: `body` (a `TextField` containing admin-authored HTML
    — confirmed via sample data, e.g. `<p>...<b>...</b>...<em>...</em></p>`)
    rendered with Django's `|safe` filter. This is the same trust
    boundary already established for word definitions/examples in Vocab
    Browse + Word — curated, `@staff_required`-gated content, not user
    input. `tip` gets a distinct highlighted-box treatment; `intro` renders
    plain.
  - `rule`: `title` + `body` (safe HTML), rendered **inline, in lesson
    order**, with its own highlighted-box treatment — explicitly **not**
    production's scroll-pinned/rotating-background-image "stage card"
    effect (`grammarRuleCardHtml`), which is out of scope for this pass.
    A `rule` block here looks like a slightly-styled `intro`/`tip` block,
    not a separate UI region.
  - `table`: `data` is confirmed to always have the shape
    `{ head: string[], rows: string[][] }` — rendered as a plain HTML
    `<table>` (`<th>` per `head` entry, one `<tr>` of `<td>`s per `rows`
    entry).
  - `examples`: `data` is confirmed to always have the shape
    `{ items: [{ en: string, note?: string }] }` — rendered as a simple
    list, one entry per item, `note` shown only when present (not every
    item has one, per sample data).
- **No "Practice" button, no quiz link on the topic detail page** — this
  page is lesson content only, matching this sub-project's read-only
  scope.
- **Nav and home CTA both go live.** The nav's "Grammar" entry stops being
  disabled and links to `/grammar/` (mirrors Vocab's nav entry going live
  in Vocab Browse + Word). The home page's "Practice Grammar" hero CTA
  also starts pointing at `/grammar/` — same "enabled and useful beats
  disabled and literally accurate to its current label" call the Vocab
  Browse + Word sub-project made for its own hero CTA; copy can be
  revisited once an actual practice/quiz mode exists.
- **404 on an unknown topic slug** — matches the existing convention from
  Vocab's category/word detail pages.
- **No dialect substitution, no Vietnamese content translation** — same
  exclusions as every prior Vocab sub-project; lesson content renders
  whatever its stored fields say.

## Architecture

```
config/
  urls.py            (add 2 routes under /grammar/)
  views_grammar.py   (new file — 2 view functions; mirrors views_vocab.py's
                       one-file-per-section pattern)
templates/
  grammar/
    browse.html        (topic grid, search + stage filter)
    topic_detail.html  (lesson blocks by type)
  partials/
    nav.html            (enable "Grammar" entry)
  home.html              (enable "Practice Grammar" CTA)
static/
  css/grammar.css      (new file, mirrors vocab.css's per-section pattern —
                         topic grid/cards, filter form, lesson block styles)
```

Routes:

```python
path('grammar/', grammar_browse, name='grammar_browse'),
path('grammar/topic/<slug:slug>/', grammar_topic_detail, name='grammar_topic_detail'),
```

## Components

- **`grammar_browse` view** — queries `GrammarTopic.objects.order_by('order')`,
  applies an optional `?q=` title-icontains filter and an optional
  `?stage=` exact filter (both via querystring, GET-submitted form, no
  new JS — matches Vocab Browse's search+filter form pattern exactly),
  renders `grammar/browse.html` with the filtered queryset and the 3
  `stage` choices for the filter dropdown.
- **`grammar_topic_detail` view** — `get_object_or_404(GrammarTopic, slug=slug)`,
  fetches `topic.blocks.order_by('order')`, renders `grammar/topic_detail.html`.
- **`templates/grammar/browse.html`** — search input + stage `<select>`
  (GET form, page reloads on submit — matches Vocab Browse's existing
  filter UX, no client-side JS), then a CSS grid of topic cards (title,
  tag label, `cefr_label` pill, blurb), each linking to its detail page.
- **`templates/grammar/topic_detail.html`** — topic header (title, CEFR
  pill, blurb), then an `{% for block in blocks %}` loop with a
  `{% if block.type == ... %}` branch per type rendering the shapes
  described in Decisions.
- **`static/css/grammar.css`** — topic grid/card styles (reusing the CSS
  custom properties already established in `base.css`, same approach
  Vocab's stylesheets already take), filter-form styles (can likely reuse
  Vocab Browse's existing `.vocab-quiz-field`-style patterns rather than
  reinventing), and lesson-block styles (highlighted boxes for
  rule/tip, table styling, examples list styling).

## Data flow

`GET /grammar/` (optionally with `?q=`/`?stage=`) → `grammar_browse` query
+ filter → rendered grid → user clicks a topic card → `GET
/grammar/topic/<slug>/` → `grammar_topic_detail` fetches the topic + its
ordered blocks → rendered lesson page. No JS-driven interactivity
anywhere in this sub-project — every page transition is a full server
round-trip, consistent with Vocab Browse + Word's own (pre-quiz-engine)
pages.

## Error handling

Unknown topic slug → Django's standard 404 page (via `get_object_or_404`),
matching the existing convention from `vocab_word_detail`/`vocab_category`.
No other error states exist in this sub-project — there's no external data
fetch, no client-side JS, nothing that can fail asynchronously.

## Testing

Fully Python-testable, unlike any Quiz/Gap/Challenge sub-project — this is
server-rendered content with real DB queries and zero client-side JS.
Tests cover: browse page renders and lists topic titles; the `?q=` search
filters by title; the `?stage=` filter narrows correctly; topic detail
renders each of the 5 block types with their correct shape (an `intro`
block's HTML content appears unescaped, a `table` block's `head`/`rows`
render as real `<th>`/`<td>` cells, an `examples` block's `note` appears
only when present); an unknown slug 404s; the nav "Grammar" link and the
home page's "Practice Grammar" CTA both point at `/grammar/`.

## Explicitly out of scope for this phase

The per-topic practice quiz (mcq/gap/transform question types, already
modeled via `GrammarQuestion` but not touched by this sub-project), the
cross-topic Grammar Test mode (separate future sub-project, setup screen
+ topic picker), the 12-section grouping layer, progress/mastery tracking
and any UI depending on it, production's scroll-pinned "rule" stage-card
effect, Vietnamese content translation, dialect-based content
substitution. These are deferred, not rejected — the per-topic quiz and
cross-topic Grammar Test each get their own design/plan cycle once this
architecture is proven, the same pattern Vocab followed.
