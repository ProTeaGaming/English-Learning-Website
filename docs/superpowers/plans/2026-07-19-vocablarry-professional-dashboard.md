# VocabLarry Professional Environment — Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the already-fully-built `dashboard` staff CRUD app into VocabLarry Professional Environment and verify it works end-to-end against this repo's real data — no new dashboard functionality, this is integration and verification of proven-in-production code.

**Architecture:** One `include()` line mounts `dashboard.urls` at `/dashboard/` (required exact prefix — `dashboard/base.html` has hardcoded absolute links). One staff/admin-gated `<li>` added to VLPE's own site nav. No changes anywhere under `dashboard/` unless live verification surfaces a real, confirmed bug.

**Tech Stack:** Django (existing app, existing views/forms/templates, zero new code beyond wiring), pytest + pytest-django, real browser click-through for the CRUD flows.

## Global Constraints

- No new models, no new migrations, no new backend logic, no new templates under `dashboard/`. The app is reused wholesale.
- URL prefix must be exactly `/dashboard/` — `dashboard/base.html`'s own nav has hardcoded absolute links (`/dashboard/words/`, etc.), not `{% url %}` tags.
- Every dashboard view is already `@role_required('staff')` except `user_list`/`user_detail`, which are `@role_required('admin')` — this is existing, unmodified code; do not add or change any access-control decorator.
- The new nav link is gated at the `staff` OR `admin` level (`user.role == 'staff' or user.role == 'admin'`), matching the majority of the app's views — not the narrower `admin`-only Users section.
- The nav link uses `{% url 'dashboard_index' %}`, matching every other `<li>` in `nav.html`, not a hardcoded href.
- `dashboard/base.html`'s own separate Bootstrap styling/layout is not touched — it stays exactly as copied.
- Do not preemptively patch `dashboard/forms.py`'s JSON-field handling — verify live first (see Task 2) and only fix if a real bug is confirmed.
- `regular_user`/`staff_user`/`admin_user` fixtures already exist in `conftest.py` — reuse them directly, do not redefine.

---

### Task 1: Wire the dashboard app and verify access control

**Files:**
- Modify: `config/urls.py`
- Modify: `templates/partials/nav.html`
- Test: `tests/test_dashboard_pages.py`

**Interfaces:**
- Produces: the `dashboard` app becomes reachable at `/dashboard/` and its 27 already-existing URL names (`dashboard_index`, `dashboard_word_list`, etc. — see `dashboard/urls.py`) resolve.
- Consumes: `dashboard.urls` (existing, unmodified), `accounts.decorators.role_required` (existing, unmodified), `CustomUser.role` (existing field).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dashboard_pages.py`:

```python
import pytest
from django.test import Client


@pytest.mark.django_db
def test_dashboard_index_requires_login():
    c = Client()
    r = c.get('/dashboard/')
    assert r.status_code == 302
    assert '/accounts/login/' in r.url


@pytest.mark.django_db
def test_dashboard_index_forbidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_index_allowed_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/')
    assert r.status_code == 200
    assert 'Dashboard' in r.content.decode()


@pytest.mark.django_db
def test_dashboard_word_list_forbidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/words/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_word_list_allowed_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/words/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_users_forbidden_for_staff_non_admin(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_users_allowed_for_admin(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_nav_dashboard_link_visible_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/')
    assert 'href="/dashboard/"' in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_visible_for_admin(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/')
    assert 'href="/dashboard/"' in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_hidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    assert 'href="/dashboard/"' not in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_hidden_for_guest():
    c = Client()
    r = c.get('/')
    assert 'href="/dashboard/"' not in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_dashboard_pages.py -v
```

Expected: all 11 FAIL — `/dashboard/` doesn't resolve yet (404), so none of the status-code assertions match, and the nav link doesn't exist yet.

- [ ] **Step 3: Wire the URL include**

In `config/urls.py`, replace:

```python
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

with:

```python
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 4: Add the nav link**

In `templates/partials/nav.html`, replace:

```html
    <li><a href="{% url 'grammar_test_setup' %}" data-i18n="nav.grammarTest">Grammar Test</a></li>
  </ul>
```

with:

```html
    <li><a href="{% url 'grammar_test_setup' %}" data-i18n="nav.grammarTest">Grammar Test</a></li>
    {% if user.role == 'staff' or user.role == 'admin' %}
    <li><a href="{% url 'dashboard_index' %}">Dashboard</a></li>
    {% endif %}
  </ul>
```

(No `data-i18n` on this link, matching the target audience — staff/admin tooling, not learner-facing chrome; this codebase's i18n system covers learner-facing chrome only, and the `dashboard` app itself has no i18n at all.)

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_dashboard_pages.py -v
```

Expected: all 11 PASS.

- [ ] **Step 6: Run the full suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES.

- [ ] **Step 7: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

As a logged-out guest, visit `/dashboard/` directly — confirm it redirects to the login page. Log in as a regular (non-staff) user and visit `/dashboard/` — confirm a plain "Access denied." 403 page, and confirm no "Dashboard" link appears anywhere in the site nav for this user. Log in as a staff user (use Django admin at `/django-admin/` or the shell to set a test account's `role` to `staff` if you don't already have one — `python manage.py shell -c "from django.contrib.auth import get_user_model; u = get_user_model().objects.get(email='<your test email>'); u.role='staff'; u.save()"`) — confirm the "Dashboard" nav link now appears, click it, confirm you land on `/dashboard/` showing the real stat cards (word/category/grammar/color/user counts matching this repo's actual seeded data — 47 grammar topics, ~5000 words). Click into Words, Categories, Colors, CEFR Levels, Grammar — confirm each list page renders real data with no errors. Try visiting `/dashboard/users/` directly as this staff (non-admin) account — confirm 403. Promote the account to `role='admin'` the same way, reload, confirm the "Users" link now appears in `dashboard/base.html`'s own internal nav and `/dashboard/users/` now loads. Stop the server (Ctrl+C) when done.

- [ ] **Step 8: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/urls.py" "VocabLarry Professional Environment/templates/partials/nav.html" "VocabLarry Professional Environment/tests/test_dashboard_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): wire the staff dashboard app into VLPE's URL routing

dashboard/ was already fully built (views, forms, Bootstrap templates)
and copied byte-for-byte from production during Foundation, but never
mounted at a URL. One include() line at the required /dashboard/
prefix (dashboard/base.html has hardcoded absolute links pinning this)
makes the whole app reachable; no code under dashboard/ changed. New
staff/admin-gated nav link, matching the app's own existing
staff-vs-admin access split (role_required('staff') for most views,
role_required('admin') for user management).
EOF
)"
```

---

### Task 2: Verify CRUD flows and the JSON-field form risk

**Files:**
- Modify: `tests/test_dashboard_pages.py`
- Modify: `dashboard/forms.py` (only if Step 8's live check finds a real bug)

**Interfaces:**
- Consumes: `WordForm`, `CategoryForm`, `GrammarTopicForm`, `GrammarLessonBlockForm`, `GrammarQuestionForm` (all existing, unmodified unless Step 8 finds a bug).
- Produces: no new interfaces — this is the last task in this sub-project.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_dashboard_pages.py`:

```python
import json
from vocab.models import Word, Category, CEFRLevel, GrammarTopic, GrammarLessonBlock, GrammarQuestion


@pytest.fixture
def cefr_a1(db):
    return CEFRLevel.objects.create(code='A1', name='Beginner', order=1)


@pytest.fixture
def category_animals(db, cefr_a1):
    return Category.objects.create(slug='animals', name='Animals', cefr_level=cefr_a1, order=1)


@pytest.mark.django_db
def test_dashboard_word_add_creates_word(staff_user, category_animals):
    c = Client()
    c.force_login(staff_user)
    r = c.post('/dashboard/words/add/', {
        'word': 'Cat', 'pos': 'noun', 'definition': 'A small domesticated feline.',
        'example': '', 'gap': '', 'category': category_animals.pk, 'cefr_level': '',
        'order': 0, 'synonyms_text': 'feline, kitty', 'antonyms_text': '',
    })
    assert r.status_code == 302
    word = Word.objects.get(word='Cat')
    assert word.definition == 'A small domesticated feline.'
    assert word.synonyms == ['feline', 'kitty']


@pytest.mark.django_db
def test_dashboard_word_edit_updates_word(staff_user, category_animals):
    word = Word.objects.create(word='Dog', definition='A domesticated canine.', category=category_animals)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/words/{word.pk}/edit/', {
        'word': 'Dog', 'pos': 'noun', 'definition': 'A loyal domesticated canine.',
        'example': '', 'gap': '', 'category': category_animals.pk, 'cefr_level': '',
        'order': 0, 'synonyms_text': '', 'antonyms_text': '',
    })
    assert r.status_code == 302
    word.refresh_from_db()
    assert word.definition == 'A loyal domesticated canine.'


@pytest.mark.django_db
def test_dashboard_word_delete_removes_word(staff_user, category_animals):
    word = Word.objects.create(word='Bird', definition='x', category=category_animals)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/words/{word.pk}/delete/')
    assert r.status_code == 302
    assert not Word.objects.filter(pk=word.pk).exists()


@pytest.mark.django_db
def test_dashboard_category_delete_blocked_when_words_exist(staff_user, category_animals):
    Word.objects.create(word='Cat', definition='x', category=category_animals)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/categories/{category_animals.pk}/delete/')
    assert r.status_code == 302
    assert Category.objects.filter(pk=category_animals.pk).exists()


@pytest.mark.django_db
def test_dashboard_grammar_topic_add_creates_topic(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.post('/dashboard/grammar/add/', {
        'slug': 'test-topic', 'title': 'Test Topic', 'tag': 'Testing',
        'cefr_label': 'A1', 'blurb': 'A topic for testing.', 'stage': 'beginner', 'order': 0,
    })
    assert r.status_code == 302
    assert GrammarTopic.objects.filter(slug='test-topic').exists()


@pytest.mark.django_db
def test_dashboard_grammar_topic_delete_cascades_blocks_and_questions(staff_user):
    topic = GrammarTopic.objects.create(slug='t0', title='T0', tag='X', cefr_label='A1', stage='beginner')
    GrammarLessonBlock.objects.create(topic=topic, type='intro', body='<p>x</p>', order=0)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/grammar/{topic.pk}/delete/')
    assert r.status_code == 302
    assert not GrammarTopic.objects.filter(pk=topic.pk).exists()
    assert not GrammarLessonBlock.objects.filter(topic_id=topic.pk).exists()


@pytest.mark.django_db
def test_dashboard_grammar_block_add_with_table_data(staff_user):
    topic = GrammarTopic.objects.create(slug='t1', title='T1', tag='X', cefr_label='A1', stage='beginner')
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/grammar/{topic.pk}/blocks/add/', {
        'type': 'table', 'title': 'Quick map', 'body': '',
        'data': json.dumps({'head': ['Use', 'Tense'], 'rows': [['Fact', 'Present simple']]}),
        'order': 0,
    })
    assert r.status_code == 302
    block = GrammarLessonBlock.objects.get(topic=topic)
    assert block.data == {'head': ['Use', 'Tense'], 'rows': [['Fact', 'Present simple']]}


@pytest.mark.django_db
def test_dashboard_grammar_question_add_mcq(staff_user):
    topic = GrammarTopic.objects.create(slug='t2', title='T2', tag='X', cefr_label='A1', stage='beginner')
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'mcq', 'prompt': 'Water ___ at 100C.',
        'options': json.dumps(['boils', 'boil', 'is boiling', 'boiled']),
        'answers': json.dumps([0]), 'why': 'Scientific fact takes present simple.', 'order': 0,
    })
    assert r.status_code == 302
    q = GrammarQuestion.objects.get(topic=topic)
    assert q.answers == [0]


@pytest.mark.django_db
def test_dashboard_category_list_smoke(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/categories/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_color_list_smoke(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/colors/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_cefr_list_smoke(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/cefr-levels/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_user_list_smoke(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_dashboard_pages.py -v -k "word_add or word_edit or word_delete or category_delete or grammar_topic or grammar_block or grammar_question or category_list_smoke or color_list_smoke or cefr_list_smoke or user_list_smoke"
```

Expected: all FAIL with 404s (same reason as Task 1 — this only matters if Task 1 hasn't merged yet in whatever execution order is used; if Task 1 is already merged, these fail instead because the DB rows/behavior being asserted don't exist yet, which is the expected TDD-red state either way).

- [ ] **Step 3: Run tests to verify they now pass (no code changes needed yet)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_dashboard_pages.py -v
```

Expected: all PASS — this task's tests exercise only already-existing, unmodified `dashboard` code (per the Global Constraints, no new dashboard code is written unless Step 8 below finds a real bug). If any of these tests fail, investigate before proceeding — a failure here means either a real latent bug in the reused code, or the test itself has a mistaken assumption about the form's field names/behavior; do not "fix" a test by weakening its assertion without first confirming which case it is.

- [ ] **Step 4: Run the full suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES.

- [ ] **Step 5: Manually verify every CRUD section in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Logged in as a staff (or admin) account, click through and exercise each section at least once with a real add → edit → delete cycle: **Words** (add a throwaway word with synonyms/antonyms, edit its definition, delete it), **Categories** (add one, edit it, then try deleting a real category that has words in it — confirm the "Cannot delete" error message from `category_delete`'s existing guard, then delete your throwaway empty one instead), **Colors** (add one using the color-picker inputs, edit it), **CEFR Levels** (edit an existing level's name inline via the list page's own form), **Grammar Topics** (add one, then click into its "Lesson blocks" and "Questions" sub-pages and add one of each — a `table`-type block and an `mcq`-type question — then delete the whole topic and confirm its blocks/questions are gone too via the cascade).

- [ ] **Step 6: Confirm blank required-field submissions fail gracefully, not with a 500**

This is the specific risk named in the design spec: `GrammarLessonBlockForm.data` and `GrammarQuestionForm.options`/`answers` are `JSONField`s rendered as plain `Textarea`s. On the "Add Lesson Block" form, select type `table` and submit with the `data` field left completely blank. On the "Add Question" form, select type `mcq` and submit with `options`/`answers` left blank. In both cases:

- **If you see a normal Django form validation error** (the page re-renders with a red error message under the field, HTTP 200, no stack trace) — this is correct, expected Django behavior for a required field left blank, and confirms no bug exists here. No code change needed.
- **If you see a 500 error page** — this is the confirmed bug. Fix it the same way `api/write_views.py`'s `_jsonfield_safe` already fixed the equivalent problem for the write API: in `dashboard/forms.py`, override `clean_data`/`clean_options`/`clean_answers` (or a shared `clean()` override) on the relevant form(s) so a blank/missing JSON field is treated as `{}`/`[]` before Django's empty-value coercion runs, rather than crashing. Write a regression test for whichever specific case broke, matching this file's existing test style, before moving on.

- [ ] **Step 7: If Step 6 found a real bug, re-run the full suite**

Only if you made a code change in Step 6:

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES, including your new regression test.

- [ ] **Step 8: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/tests/test_dashboard_pages.py"
```

If Step 6 found and fixed a real bug, also add the changed file(s) under `dashboard/` and describe the fix in the commit message. Otherwise:

```bash
git commit -m "$(cat <<'EOF'
test(vlpe): verify dashboard CRUD flows against real VLPE data

Full add/edit/delete round-trips for Words and Grammar (topic + a
table-type lesson block + an mcq question, exercising the JSONField
forms directly), plus category-delete's existing words-still-assigned
guard and grammar-topic-delete's cascade, plus smoke coverage for
Categories/Colors/CEFR/Users. Manually verified every section works
against this repo's real seeded data (47 grammar topics, ~5000 words)
and confirmed a blank JSONField submission fails gracefully rather
than 500ing.
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** exact `/dashboard/` prefix (Task 1 Step 3); no new dashboard code unless a real bug is found (Task 2's entire framing, Step 6's explicit branch); staff/admin nav gating matching the app's own split (Task 1 Step 4); `{% url 'dashboard_index' %}` not a hardcoded href (Task 1 Step 4); access-control matrix including the `admin`-only Users boundary (Task 1 Step 1's 11 tests); CRUD round-trips for the two richest sections plus the category-delete guard and grammar cascade (Task 2 Step 1); JSON-field risk investigated live, not preemptively patched (Task 2 Step 6); reuses existing `regular_user`/`staff_user`/`admin_user` fixtures, no redefinition anywhere.
- **Placeholder scan:** no TBD/TODO; every step has complete, exact code; the one genuinely-conditional step (Task 2 Step 6/7/8's bug-fix branch) is written as an explicit if/else with a concrete example of what the fix should look like, not a vague "handle edge cases" placeholder.
- **Type consistency:** URL names used in tests (`/dashboard/`, `/dashboard/words/`, `/dashboard/words/add/`, etc.) match `dashboard/urls.py`'s actual registered patterns exactly (verified by reading the file directly, not assumed). Form field names in Task 2's POST payloads (`word`/`pos`/`definition`/`example`/`gap`/`category`/`cefr_level`/`order`/`synonyms_text`/`antonyms_text` for `WordForm`; `slug`/`title`/`tag`/`cefr_label`/`blurb`/`stage`/`order` for `GrammarTopicForm`; `type`/`title`/`body`/`data`/`order` for `GrammarLessonBlockForm`; `qtype`/`prompt`/`options`/`answers`/`why`/`order` for `GrammarQuestionForm`) match `dashboard/forms.py`'s actual `Meta.fields` lists exactly.
