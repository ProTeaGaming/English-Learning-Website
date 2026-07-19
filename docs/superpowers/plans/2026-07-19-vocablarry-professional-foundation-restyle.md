# VocabLarry Professional Environment — Foundation Restyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle VLPE's shared chrome (fonts, color tokens, texture, nav) and home page to match production's (`VocabLarry/vocablarry.html`) design system exactly — Fraunces italic accents, mono eyebrow labels, film grain + ambient glow, an icon sprite with pill-style nav, and a real "Your Progress" stat board — replacing the current generic system-font/plain-border starter styling.

**Architecture:** All shared visual changes (fonts, tokens, texture, nav, icons) live in `templates/base.html`/`templates/partials/nav.html`/`static/css/base.css`/`static/js/base.js` so every existing page inherits them automatically. `templates/home.html` and `config/views.py`'s `home()` get the hero + stat-board treatment specifically.

**Tech Stack:** Django templates, one existing CSS file extended, one existing JS file extended (icon swap only, no new client-side logic), pytest for server-rendered assertions, real browser comparison against production for visual fidelity (no automated visual-regression tooling in this codebase).

## Global Constraints

- Every color/font value below was extracted directly from `vocablarry.html`'s actual CSS/markup, not approximated — use them verbatim.
- **Do not rename the existing `--violet` custom property to `--vio`.** It's already used in 20 places across `base.css`/`vocab.css`/`grammar.css`; renaming it would silently break every one of them (an undefined custom property resolves to nothing, not an error). Keep the name `--violet`, only change its RGB triple value from `109 40 217` to production's `124 58 237`.
- No new CEFR/tag/gram tier color tokens (`--a1`/`--a2`/etc.), no new icon symbols beyond the 8 this phase's own markup references (`i-mark`, `i-moon`, `i-sun`, `i-globe`, `i-check-circle`, `i-folder`, `i-bar-chart`, `i-grad-cap`) — later restyle phases add their own tokens/icons when they need them, matching this whole rebuild's established YAGNI discipline.
- The "Your Progress" stat board shows exactly 3 stats (Words Learned, Categories Started, % Complete) — no day-streak card, per the explicit scope decision (streak needs new activity-tracking data, out of scope for a restyle).
- Stat definitions must match production's own `updateHome()` exactly: `words_learned` counts only `learn_map` entries with value `'learned'` (NOT `'little'`); `categories_started` counts categories with *any* `learn_map` entry regardless of state (`'learned'` OR `'little'` both count); `pct_complete` = `round(words_learned / total_words * 100)`, `0` if there are no words.
- The stat board renders unconditionally for every visitor (not auth-gated) — a guest's `learn_map` is `{}`, which naturally computes to `0`/`0`/`0%`, matching production's own behavior exactly rather than adding a separate hidden/shown branch.
- Copy for elements that already existed in VLPE (hero title/subtitle, the two CTA buttons) keeps VLPE's own existing English/Vietnamese text — only the visual treatment changes. Copy for genuinely new elements (the eyebrow badge, the 3 stat labels, "Your Progress") uses production's exact existing copy/translations, since there's no prior VLPE version to preserve.
- Dashboard (`dashboard/`) is explicitly excluded from this and every restyle phase — it keeps its own separate Bootstrap identity, per that sub-project's own decision.

---

### Task 1: Design tokens, fonts, icon sprite, and nav restyle

**Files:**
- Modify: `templates/base.html`
- Modify: `templates/partials/nav.html`
- Modify: `static/css/base.css`
- Modify: `static/js/base.js`
- Test: `tests/test_pages.py`

**Interfaces:**
- Produces: CSS custom properties `--violet` (updated value), `--surface`, `--gold`, `--gold-rgb`, `--serif`, `--ease-luxe` on `:root`/`[data-theme]` — consumed by Task 2's `.home-*` rules.
- Produces: icon symbols `#i-mark`, `#i-moon`, `#i-sun`, `#i-globe`, `#i-check-circle`, `#i-folder`, `#i-bar-chart`, `#i-grad-cap` in `base.html`'s sprite — the last 4 are consumed by Task 2's stat cards and hero badge.
- Produces: `.eyebrow`, `.tab`/`.tab.active`, `.icon-toggle`, `.ico`/`.ico-mark` CSS classes — reusable by any future restyle phase.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_pages.py`:

```python
@pytest.mark.django_db
def test_base_includes_fonts_and_icon_sprite():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'fonts.googleapis.com' in html
    assert 'Fraunces' in html
    assert 'id="i-mark"' in html


@pytest.mark.django_db
def test_nav_theme_and_lang_toggles_are_icon_only():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'data-theme-toggle' in html
    assert 'data-lang-toggle' in html
    assert '#i-moon' in html
    assert '#i-globe' in html


@pytest.mark.django_db
def test_nav_vocabulary_tab_active_on_vocab_browse():
    from django.test import Client
    c = Client()
    r = c.get('/vocab/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocab/" data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="tab" href="/vocab/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_quiz_tab_active_on_vocab_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocab/quiz/" data-i18n="nav.quiz">Quiz</a>' in html
    assert '<a class="tab" href="/vocab/" data-i18n="nav.vocabulary">Vocabulary</a>' in html


@pytest.mark.django_db
def test_nav_grammar_tab_active_on_grammar_browse():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/" data-i18n="nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_nav_grammar_test_tab_active_on_grammar_test_setup():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/test/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/test/" data-i18n="nav.grammarTest">Grammar Test</a>' in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v -k "sprite or icon_only or tab_active"
```

Expected: all 6 FAIL — none of this markup exists yet.

- [ ] **Step 3: Add fonts and the icon sprite to base.html**

Replace `templates/base.html`'s entire contents with:

```html
{% load static %}<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{% block title %}VocabLarry{% endblock %}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&family=Fraunces:ital,opsz,wght@1,9..144,400..600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{% static 'css/base.css' %}">
{% block extra_head %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
<svg style="display:none" aria-hidden="true">
  <symbol id="i-mark" viewBox="0 0 24 24"><path d="M3.4 18H12a8 8 0 0 0 8-8V7a4 4 0 0 0-7.28-2.3L2 20"/><path d="M20 7c1.5.3 2.1 1.9 1.1 3-.6.7-1.5 1-2.4.9"/><path d="M16 7h.01"/><path d="M10 18v3"/><path d="M14 17.75V21"/><path d="M7 18a6 6 0 0 0 3.84-10.61"/></symbol>
  <symbol id="i-moon" viewBox="0 0 24 24"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></symbol>
  <symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></symbol>
  <symbol id="i-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></symbol>
  <symbol id="i-check-circle" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></symbol>
  <symbol id="i-folder" viewBox="0 0 24 24"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></symbol>
  <symbol id="i-bar-chart" viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></symbol>
  <symbol id="i-grad-cap" viewBox="0 0 24 24"><path d="M22 10v6"/><path d="M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></symbol>
</svg>
{% include "partials/nav.html" %}
<main class="page-content">
{% if messages %}
  <ul class="site-messages">
    {% for message in messages %}<li{% if message.tags %} class="{{ message.tags }}"{% endif %}>{{ message }}</li>{% endfor %}
  </ul>
{% endif %}
{% block content %}{% endblock %}
</main>
<script src="{% static 'js/i18n.js' %}" defer></script>
<script src="{% static 'js/base.js' %}" defer></script>
{% block extra_body %}{% endblock %}
</body>
</html>
```

- [ ] **Step 4: Restyle the nav**

Replace `templates/partials/nav.html`'s entire contents with:

```html
<nav class="site-nav">
  <a class="brand" href="{% url 'home' %}"><svg class="ico ico-mark" aria-hidden="true"><use href="#i-mark"/></svg>Vocab<b>Larry</b></a>
  <ul class="nav-links">
    <li><a class="tab{% if request.resolver_match.url_name == 'vocab_browse' or request.resolver_match.url_name == 'vocab_category' or request.resolver_match.url_name == 'vocab_word_detail' %} active{% endif %}" href="{% url 'vocab_browse' %}" data-i18n="nav.vocabulary">Vocabulary</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'vocab_quiz_setup' or request.resolver_match.url_name == 'vocab_quiz_play' %} active{% endif %}" href="{% url 'vocab_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'grammar_browse' or request.resolver_match.url_name == 'grammar_topic_detail' or request.resolver_match.url_name == 'grammar_topic_quiz' %} active{% endif %}" href="{% url 'grammar_browse' %}" data-i18n="nav.grammar">Grammar</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'grammar_test_setup' or request.resolver_match.url_name == 'grammar_test_play' %} active{% endif %}" href="{% url 'grammar_test_setup' %}" data-i18n="nav.grammarTest">Grammar Test</a></li>
    {% if user.role == 'staff' or user.role == 'admin' %}
    <li><a href="{% url 'dashboard_index' %}">Dashboard</a></li>
    {% endif %}
  </ul>
  <div class="nav-actions">
    <button type="button" class="icon-toggle" data-lang-toggle aria-label="Switch language"><svg class="ico" aria-hidden="true"><use href="#i-globe"/></svg></button>
    <button type="button" class="icon-toggle" data-theme-toggle aria-label="Toggle theme"><svg class="ico" data-theme-icon aria-hidden="true"><use href="#i-moon"/></svg></button>
    {% if user.is_authenticated %}
      <span>{{ user.username }}</span>
      <a class="btn" href="{% url 'account_logout' %}" data-i18n="nav.signOut">Sign Out</a>
    {% else %}
      <a class="btn" href="{% url 'account_login' %}" data-i18n="nav.signIn">Sign In</a>
      <a class="btn btn-primary" href="{% url 'account_signup' %}" data-i18n="nav.signUp">Sign Up</a>
    {% endif %}
  </div>
</nav>
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v -k "sprite or icon_only or tab_active"
```

Expected: all 6 PASS.

- [ ] **Step 6: Restyle base.css — tokens, fonts, texture, nav**

Replace `static/css/base.css`'s entire contents with:

```css
:root{
  color-scheme: dark;
  --violet: 124 58 237;
  --bg: #0b0d12;
  --text: #eceef4;
  --muted: #98a0b3;
  --border: #232937;
  --card-bg: #12151d;
  --gold: #d4af6a;
  --gold-rgb: 212 175 106;
  --serif: 'Fraunces', Georgia, serif;
  --ease-luxe: cubic-bezier(.22,1,.36,1);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme]){
    --bg: #0b0d12;
    --text: #eceef4;
    --muted: #98a0b3;
    --border: #232937;
    --card-bg: #12151d;
    --gold: #d4af6a;
    --gold-rgb: 212 175 106;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --bg: #0b0d12;
  --text: #eceef4;
  --muted: #98a0b3;
  --border: #232937;
  --card-bg: #12151d;
  --gold: #d4af6a;
  --gold-rgb: 212 175 106;
}
:root[data-theme="light"]{
  color-scheme: light;
  --bg: #f6f5f2;
  --text: #16181d;
  --muted: #585d68;
  --border: #dcd7cc;
  --card-bg: #ffffff;
  --gold: #b08a3e;
  --gold-rgb: 176 138 62;
}

*{ box-sizing: border-box; }
body{
  margin: 0;
  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  transition: background-color .25s ease, color .25s ease;
}
h1,h2,h3,.brand,.btn{ font-family: 'Plus Jakarta Sans','Sora',sans-serif; }
a{ color: rgb(var(--violet)); }

/* ambient glow + film grain, global — every page inherits these */
body::before{
  content:""; position:fixed; inset:0; z-index:-1; pointer-events:none;
  background:
    radial-gradient(1100px 520px at 82% -8%, rgba(var(--violet),.09), transparent 60%),
    radial-gradient(900px 480px at -10% 30%, rgba(var(--violet),.05), transparent 55%);
}
body::after{
  content:""; position:fixed; inset:0; z-index:2147483000; pointer-events:none; opacity:.028;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

.eyebrow{
  font-family: 'JetBrains Mono', monospace;
  font-size: .66rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .32em;
  color: var(--muted);
}

.ico{
  width: 1em; height: 1em; display: inline-block; flex-shrink: 0; vertical-align: -.125em;
  fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round;
}
.ico-mark{ width: 1.3em; height: 1.3em; color: rgb(var(--violet)); margin-right: 6px; }

.site-nav{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.site-nav .brand{
  display: flex;
  align-items: center;
  font-weight: 800;
  font-size: 1.25rem;
  text-decoration: none;
  color: var(--text);
}
.site-nav .brand b{ color: rgb(var(--violet)); }
.nav-links{
  display: flex;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
  flex-wrap: wrap;
  align-items: center;
}
.nav-links a, .nav-links span{
  text-decoration: none;
  color: var(--text);
  font-weight: 600;
  font-size: 0.95rem;
}
.nav-links .disabled{ color: var(--muted); cursor: default; }
.nav-actions{ display: flex; align-items: center; gap: 12px; }

.tab{
  font-size: .88rem; font-weight: 600; color: var(--muted); background: transparent;
  border: 1px solid transparent; padding: 8px 12px; border-radius: 10px;
  display: inline-block;
  transition: background .18s ease, color .18s ease, box-shadow .18s ease, transform .2s cubic-bezier(.25,.46,.45,.94);
  white-space: nowrap;
}
.tab:hover{ color: var(--text); background: rgba(var(--violet),.1); border-color: rgba(var(--violet),.2); transform: translateY(-1px); }
.tab.active{ color: #fff; background: rgb(var(--violet)); box-shadow: 0 4px 14px rgba(var(--violet),.4); }

.icon-toggle{
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: 10px;
  border: 1px solid var(--border); background: transparent; color: var(--text);
  cursor: pointer; font-size: 1.1rem;
}
.icon-toggle:hover{ border-color: rgb(var(--violet)); background: rgba(var(--violet),.15); }

.btn{
  display: inline-block;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 700;
  text-decoration: none;
  border: 1px solid rgb(var(--violet));
  color: rgb(var(--violet));
  background: transparent;
  cursor: pointer;
  font-size: 0.95rem;
  font-family: 'Plus Jakarta Sans','Sora',sans-serif;
}
.btn-primary{
  background: rgb(var(--violet));
  color: #fff;
}
.btn.disabled{
  opacity: 0.5;
  pointer-events: none;
}

.page-content{ max-width: 1080px; margin: 0 auto; padding: 0 24px; }

.hero{
  padding: 72px 0 48px;
  text-align: center;
}
.hero h1{ font-size: 2.6rem; margin: 0 0 12px; }
.hero p{ color: var(--muted); font-size: 1.1rem; max-width: 560px; margin: 0 auto 28px; }
.hero-actions{ display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }

/* Auth pages (allauth's classic views rendered inside body_class="auth-page") */
.auth-page .page-content{
  max-width: 420px;
  padding-top: 48px;
}
.auth-page h1{ font-size: 1.6rem; margin-bottom: 8px; }
.auth-page form{
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 20px;
}
.auth-page form p{ margin: 0; display: flex; flex-direction: column; gap: 6px; }
.auth-page form label{ font-weight: 600; font-size: 0.9rem; }
.auth-page form input{
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 1rem;
}
.auth-page form button[type="submit"]{
  margin-top: 6px;
  padding: 11px 20px;
  border-radius: 8px;
  border: none;
  background: rgb(var(--violet));
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
}

/* django.contrib.messages, surfaced across all pages incl. allauth flows */
.site-messages{
  list-style: none;
  margin: 20px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.site-messages li{
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 0.9rem;
  font-weight: 600;
}
.site-messages li.success{
  border-color: rgb(var(--violet));
  color: rgb(var(--violet));
}
.site-messages li.error{
  border-color: #dc2626;
  color: #dc2626;
}
```

Note: `.hero`/`.hero-actions` are kept unchanged in this step (Task 2 replaces them once `home.html`'s markup no longer uses those classes).

- [ ] **Step 7: Add icon-swap logic to the theme toggle**

Replace `static/js/base.js`'s entire contents with:

```javascript
(function(){
  var STORAGE_KEY = "vlpe_theme";
  var root = document.documentElement;

  function currentTheme(){
    return root.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }

  function updateThemeIcon(){
    var use = document.querySelector("[data-theme-icon] use");
    if (!use) return;
    use.setAttribute("href", currentTheme() === "dark" ? "#i-sun" : "#i-moon");
  }

  function applyTheme(theme){
    if (theme === "dark" || theme === "light"){
      root.setAttribute("data-theme", theme);
    } else {
      root.removeAttribute("data-theme");
    }
    updateThemeIcon();
  }

  var saved = null;
  try { saved = localStorage.getItem(STORAGE_KEY); } catch(e) {}
  applyTheme(saved);

  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle){
    toggle.addEventListener("click", function(){
      var next = currentTheme() === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch(e) {}
    });
  }
})();
```

This adds `updateThemeIcon()` (swaps the theme toggle's `<use href>` between `#i-moon`/`#i-sun` — showing the icon for the mode a click would switch *to*, matching production's own `themeToggleBtn.innerHTML` logic exactly: sun shown while dark, moon shown while light) and calls it both on initial load and after every toggle. The `data-theme`/`localStorage` logic itself is unchanged from before.

- [ ] **Step 8: Run `node --check` and the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
node --check static/js/base.js
python -m pytest -v
```

Expected: `node --check` prints nothing. Every test PASSES — including the existing `test_home_page_has_nav_and_hero` (its loose `'hero' in body` check still passes since Task 1 hasn't touched `home.html`'s markup yet, and even after Task 2 does, `"home-hero"` still contains the substring `"hero"`).

- [ ] **Step 9: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Visit `/` and confirm: the page now uses the Plus Jakarta Sans/Inter font pairing (visibly different from the previous system-font look), a parrot mascot icon appears before "VocabLarry" in the nav, the nav links are now pill-shaped with the currently-active one filled solid violet with a glow (none should be active on `/` itself, since Home has no nav tab). Click through to `/vocab/`, `/vocab/quiz/`, `/grammar/`, `/grammar/test/` in turn — confirm each page's own nav link becomes the filled-violet active pill while the others stay plain. Visit `/vocab/category/<any-real-slug>/` and `/vocab/word/<any-real-id>/` — confirm the Vocabulary tab stays active on these sub-pages too. Click the theme toggle — confirm it now shows a moon/sun icon (not text) and the icon itself swaps between clicks, and the whole page still switches theme correctly. Click the language toggle — confirm it's now a globe icon (not "EN/VI" text) and still switches nav label language correctly. Look closely at the page background in both themes — confirm a very subtle grain texture and a faint violet glow are visible (most obvious in dark mode, in the upper-right area). Reload in dark mode, then light mode — confirm the font/nav/texture treatment holds up correctly in both. Stop the server (Ctrl+C) when done.

- [ ] **Step 10: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/templates/base.html" "VocabLarry Professional Environment/templates/partials/nav.html" "VocabLarry Professional Environment/static/css/base.css" "VocabLarry Professional Environment/static/js/base.js" "VocabLarry Professional Environment/tests/test_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): restyle shared chrome to match production's design system

Ports production's exact fonts (Plus Jakarta Sans/Sora/Inter/JetBrains
Mono/Fraunces), color tokens (--violet updated from 109 40 217 to
production's actual 124 58 237 — kept the existing property name since
it's already used in 20 places across 3 CSS files; a rename would have
silently broken all of them), film-grain + ambient-glow texture, and an
8-symbol icon sprite (mascot mark, theme/language toggle icons, 3 stat-
card icons for the next task, grad-cap for the home hero badge — not
production's full ~90-icon sprite, which serves surfaces this phase
doesn't touch yet). Nav becomes pill-tabs with a server-computed active
state per page (no client-side view-swapping the way production's SPA
tabs work, since VLPE has real per-page routing) and icon-only theme/
language toggles. No visual changes yet to any page's own content —
this is shared chrome only, consumed by every existing page
automatically via base.html/base.css.
EOF
)"
```

---

### Task 2: Home hero and "Your Progress" stat board

**Files:**
- Modify: `config/views.py`
- Modify: `templates/home.html`
- Modify: `static/css/base.css`
- Modify: `static/js/i18n.js`
- Test: `tests/test_pages.py`

**Interfaces:**
- Consumes: `--violet`, `--serif`, `--ease-luxe`, `.eyebrow`, icon symbols `#i-check-circle`/`#i-folder`/`#i-bar-chart`/`#i-grad-cap` (all from Task 1).
- Produces: no new interfaces — this is the last task in this sub-project.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_pages.py`:

```python
@pytest.mark.django_db
def test_home_stats_zero_for_guest():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<div class="home-stat-val">0</div>' in html
    assert '<div class="home-stat-val">0%</div>' in html


@pytest.mark.django_db
def test_home_stats_computed_for_authenticated_user(regular_user):
    from django.test import Client
    from vocab.models import Category, Word

    cat1 = Category.objects.create(slug='animals', name='Animals', order=1)
    cat2 = Category.objects.create(slug='colors', name='Colors', order=2)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat1, order=2)
    w3 = Word.objects.create(word='Red', definition='x', category=cat2, order=1)

    # w1 fully learned, w2 only "little" (counts toward categories-started
    # but NOT words-learned), w3 untouched.
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])

    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()

    from vocab.models import Word as WordModel
    total = WordModel.objects.count()
    expected_pct = round(1 / total * 100)

    assert '<div class="home-stat-val">1</div>' in html
    assert f'<div class="home-stat-val">{expected_pct}%</div>' in html
    # Both cat1 (via w1 AND w2) and cat2 (untouched) exist, but only cat1
    # has any learn_map entry — categories_started must be 1, not 2.
    assert '<div class="home-stat-val">2</div>' not in html


@pytest.mark.django_db
def test_home_badge_and_progress_heading_render():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'home.badge">IELTS Preparation' in html
    assert 'home.yourProgress">Your Progress' in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v -k "home_stats or home_badge"
```

Expected: all 3 FAIL — `home.html` doesn't have any of this markup yet, and `home()` computes no stats.

- [ ] **Step 3: Compute the stats in the home view**

Replace `config/views.py`'s entire contents with:

```python
from django.shortcuts import render

from vocab.models import Category, Word


def home(request):
    learn_map = request.user.learn_map if request.user.is_authenticated else {}
    learned_ids = [int(k) for k, v in learn_map.items() if v == 'learned']
    started_ids = [int(k) for k in learn_map.keys()]
    total_words = Word.objects.count()
    words_learned = len(learned_ids)
    pct_complete = round(words_learned / total_words * 100) if total_words else 0
    categories_started = Category.objects.filter(words__id__in=started_ids).distinct().count()
    return render(request, 'home.html', {
        'words_learned': words_learned,
        'categories_started': categories_started,
        'pct_complete': pct_complete,
    })
```

- [ ] **Step 4: Restyle the home page markup**

Replace `templates/home.html`'s entire contents with:

```html
{% extends "base.html" %}
{% block title %}VocabLarry{% endblock %}
{% block content %}
<section class="home-hero">
  <div class="home-grid-bg"></div>
  <div class="home-glow"></div>
  <div class="home-badge"><svg class="ico" aria-hidden="true"><use href="#i-grad-cap"/></svg> <span data-i18n="home.badge">IELTS Preparation · Band 5–9</span></div>
  <h1 class="home-title"><span data-i18n="home.title1">Master every word,</span><br><span class="home-grad" data-i18n="home.title2">say it till it stays.</span></h1>
  <p class="home-sub" data-i18n="hero.subtitle">Build vocabulary and grammar skills for IELTS, one focused session at a time.</p>
  <div class="home-hero-actions">
    <a class="btn btn-primary" href="{% url 'vocab_browse' %}" data-i18n="hero.start">Start Learning</a>
    <a class="home-btn-outline" href="{% url 'grammar_browse' %}" data-i18n="hero.grammar">Practice Grammar</a>
  </div>
</section>
<div class="home-content">
  <div>
    <div class="home-section-hd" data-i18n="home.yourProgress">Your Progress</div>
    <div class="home-stats">
      <div class="home-stat">
        <div class="home-stat-ico"><svg class="ico" aria-hidden="true"><use href="#i-check-circle"/></svg></div>
        <div class="home-stat-val">{{ words_learned }}</div>
        <div class="home-stat-lbl" data-i18n="home.wordsLearned">Words learned</div>
      </div>
      <div class="home-stat">
        <div class="home-stat-ico"><svg class="ico" aria-hidden="true"><use href="#i-folder"/></svg></div>
        <div class="home-stat-val">{{ categories_started }}</div>
        <div class="home-stat-lbl" data-i18n="home.categoriesStarted">Categories started</div>
      </div>
      <div class="home-stat">
        <div class="home-stat-ico"><svg class="ico" aria-hidden="true"><use href="#i-bar-chart"/></svg></div>
        <div class="home-stat-val">{{ pct_complete }}%</div>
        <div class="home-stat-lbl" data-i18n="home.complete">Complete</div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v -k "home_stats or home_badge"
```

Expected: all 3 PASS.

- [ ] **Step 6: Replace the old hero CSS with the home-hero + stat-card styles**

In `static/css/base.css`, replace:

```css
.hero{
  padding: 72px 0 48px;
  text-align: center;
}
.hero h1{ font-size: 2.6rem; margin: 0 0 12px; }
.hero p{ color: var(--muted); font-size: 1.1rem; max-width: 560px; margin: 0 auto 28px; }
.hero-actions{ display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
```

with:

```css
.home-hero{
  position: relative; overflow: hidden;
  padding: 104px 32px 92px; text-align: center;
  border-bottom: 1px solid rgba(var(--violet),.12);
}
.home-grid-bg{
  position: absolute; inset: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(var(--violet),.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--violet),.06) 1px, transparent 1px);
  background-size: 40px 40px;
}
.home-glow{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 700px; height: 420px; border-radius: 50%;
  background: radial-gradient(ellipse, rgba(var(--violet),.2) 0%, transparent 70%);
  pointer-events: none;
}
.home-badge{
  display: inline-flex; align-items: center; gap: 10px;
  font-family: 'JetBrains Mono', monospace; font-size: .68rem; font-weight: 700;
  color: var(--muted); letter-spacing: .34em; text-transform: uppercase;
  margin-bottom: 34px; position: relative;
}
.home-badge .ico{ color: rgb(var(--violet)); }
.home-title{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif;
  font-size: clamp(2.6rem,6vw,4.6rem); font-weight: 800; line-height: 1.06;
  letter-spacing: -.035em; margin-bottom: 26px; position: relative; color: var(--text);
}
.home-grad{
  font-family: var(--serif); font-style: italic; font-weight: 500;
  color: rgb(var(--violet)); letter-spacing: -.01em;
}
.home-sub{
  font-size: 1.18rem; color: var(--muted); max-width: 600px; margin: 0 auto 40px;
  line-height: 1.75; position: relative; font-family: var(--serif); font-style: italic;
}
.home-hero-actions{
  display: flex; align-items: center; justify-content: center; gap: 12px;
  flex-wrap: wrap; position: relative;
}
.home-btn-outline{
  background: transparent; border: 1px solid rgba(var(--violet),.35);
  color: var(--text); padding: 12px 24px; border-radius: 12px; font-size: .95rem;
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-weight: 700;
  cursor: pointer; text-decoration: none; display: inline-block;
  transition: background .15s, border-color .15s;
}
.home-btn-outline:hover{ background: rgba(var(--violet),.08); border-color: rgba(var(--violet),.6); }
.home-content{ max-width: 940px; margin: 0 auto; padding: 44px 32px; display: flex; flex-direction: column; gap: 44px; }
.home-section-hd{
  font-family: 'JetBrains Mono', monospace; font-size: .7rem; font-weight: 700;
  color: var(--muted); margin-bottom: 20px; display: flex; align-items: center; gap: 16px;
  text-transform: uppercase; letter-spacing: .3em;
}
.home-section-hd::after{ content:''; flex: 1; height: 1px; background: var(--border); }
.home-stats{ display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; }
@media (max-width: 640px){ .home-stats{ grid-template-columns: 1fr; } }
.home-stat{
  background: rgba(22,26,35,.78); border: 1px solid rgba(var(--violet),.18);
  border-radius: 18px; padding: 20px 18px; backdrop-filter: blur(14px);
  display: flex; flex-direction: column; align-items: flex-start; gap: 6px;
  transition: border-color .4s var(--ease-luxe), box-shadow .4s var(--ease-luxe), transform .4s var(--ease-luxe);
}
[data-theme="light"] .home-stat{ background: rgba(255,255,255,.86); }
.home-stat:hover{ border-color: rgba(var(--violet),.4); box-shadow: 0 16px 40px rgba(0,0,0,.15); transform: translateY(-2px); }
.home-stat-ico{
  font-size: 1.4rem; width: 40px; height: 40px; border-radius: 12px;
  background: rgba(var(--violet),.12); display: flex; align-items: center; justify-content: center;
  margin-bottom: 4px; color: rgb(var(--violet));
}
.home-stat-val{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-size: 2rem; font-weight: 800;
  color: var(--text); line-height: 1; letter-spacing: -.04em;
}
.home-stat-lbl{
  font-family: 'JetBrains Mono', monospace; font-size: .62rem; color: var(--muted);
  text-transform: uppercase; letter-spacing: .08em; font-weight: 700;
}
```

- [ ] **Step 7: Add the new i18n keys**

In `static/js/i18n.js`, replace:

```javascript
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
      "nav.grammarTest": "Grammar Test",
      "nav.comingSoon": "Coming soon",
      "nav.signIn": "Sign In",
      "nav.signOut": "Sign Out",
      "nav.signUp": "Sign Up",
      "hero.title": "Master every word, say it till it stays.",
      "hero.subtitle": "Build vocabulary and grammar skills for IELTS, one focused session at a time.",
      "hero.start": "Start Learning",
      "hero.grammar": "Practice Grammar",
    },
```

with:

```javascript
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
      "nav.grammarTest": "Grammar Test",
      "nav.comingSoon": "Coming soon",
      "nav.signIn": "Sign In",
      "nav.signOut": "Sign Out",
      "nav.signUp": "Sign Up",
      "hero.subtitle": "Build vocabulary and grammar skills for IELTS, one focused session at a time.",
      "hero.start": "Start Learning",
      "hero.grammar": "Practice Grammar",
      "home.badge": "IELTS Preparation · Band 5–9",
      "home.title1": "Master every word,",
      "home.title2": "say it till it stays.",
      "home.yourProgress": "Your Progress",
      "home.wordsLearned": "Words learned",
      "home.categoriesStarted": "Categories started",
      "home.complete": "Complete",
    },
```

(`hero.title` is removed — it's replaced by the two new `home.title1`/`home.title2` keys, since the hero now renders the tagline as two separately-styled spans, not one string.)

Then, still in the same file, replace:

```javascript
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
      "nav.grammarTest": "Kiểm tra ngữ pháp",
      "nav.comingSoon": "Sắp ra mắt",
      "nav.signIn": "Đăng nhập",
      "nav.signOut": "Đăng xuất",
      "nav.signUp": "Đăng ký",
      "hero.title": "Học từng từ, ghi nhớ mãi mãi.",
      "hero.subtitle": "Xây dựng vốn từ vựng và ngữ pháp cho IELTS, từng buổi học tập trung.",
      "hero.start": "Bắt đầu học",
      "hero.grammar": "Luyện ngữ pháp",
    },
```

with:

```javascript
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
      "nav.grammarTest": "Kiểm tra ngữ pháp",
      "nav.comingSoon": "Sắp ra mắt",
      "nav.signIn": "Đăng nhập",
      "nav.signOut": "Đăng xuất",
      "nav.signUp": "Đăng ký",
      "hero.subtitle": "Xây dựng vốn từ vựng và ngữ pháp cho IELTS, từng buổi học tập trung.",
      "hero.start": "Bắt đầu học",
      "hero.grammar": "Luyện ngữ pháp",
      "home.badge": "Luyện thi IELTS · Band 5–9",
      "home.title1": "Học từng từ,",
      "home.title2": "ghi nhớ mãi mãi.",
      "home.yourProgress": "Tiến độ của bạn",
      "home.wordsLearned": "Từ đã học",
      "home.categoriesStarted": "Danh mục đã bắt đầu",
      "home.complete": "Hoàn thành",
    },
```

(VLPE's own existing English/Vietnamese wording for the title/subtitle/buttons is preserved exactly — `home.title1`/`home.title2` are VLPE's own original single-string tagline split at its existing comma, not swapped for production's different phrasing. `home.badge`/`home.yourProgress`/`home.wordsLearned`/`home.categoriesStarted`/`home.complete` are genuinely new elements with no prior VLPE copy, so they use production's own exact copy/translations directly.)

- [ ] **Step 8: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v
```

Expected: every test in the file PASSES.

- [ ] **Step 9: Run the full suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES.

- [ ] **Step 10: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

As a guest, visit `/` — confirm: a grid-texture + glow background behind the hero, an eyebrow badge with a graduation-cap icon reading "IELTS Preparation · Band 5–9", a large two-line headline where the second line ("say it till it stays.") renders in italic Fraunces violet (visibly different font from the first line), an italic serif subtitle, a solid violet "Start Learning" button and an outlined "Practice Grammar" button, and below that a "Your Progress" section with 3 stat cards (icon chip, big number, mono label) all showing `0`/`0`/`0%`. Compare this side-by-side against the earlier production screenshot — the hero and stat-board sections should look essentially identical in layout and typography. Sign up or log in as a test account, mark a few words as "learned" and a few more as "little" across at least 2 categories via `/vocab/word/<id>/`, then reload `/` — confirm the 3 numbers update to real, correct values (spot-check the math: words-learned should count only the "learned" ones, categories-started should count both categories since "little" counts too). Toggle both themes and confirm the hero/stat-card treatment holds up in light mode too (the stat cards' translucent background is theme-aware). Stop the server (Ctrl+C) when done.

- [ ] **Step 11: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/views.py" "VocabLarry Professional Environment/templates/home.html" "VocabLarry Professional Environment/static/css/base.css" "VocabLarry Professional Environment/static/js/i18n.js" "VocabLarry Professional Environment/tests/test_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): restyle home page with real progress stats

home() now computes words_learned/categories_started/pct_complete
from the authenticated user's learn_map (or {} for a guest, naturally
producing 0/0/0% — matching production's own unconditional-render
behavior rather than adding a separate auth-gated branch), with
definitions verified against production's updateHome(): words_learned
counts only the 'learned' state (not 'little'), categories_started
counts either state. Hero gets the grid-texture/glow background, an
eyebrow badge, a two-line title with an italic Fraunces accent, and
pill CTA buttons; existing VLPE copy is preserved throughout, only new
elements (badge, stat labels) use production's own copy since there
was no prior VLPE version of them to preserve. No streak card, per
the explicit scope decision — that needs new activity-tracking data,
not just visual work.
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** `--violet` value updated without renaming (Task 1 Step 6, explicitly called out in Global Constraints and the commit message); fonts ported verbatim (Task 1 Step 3); grain+glow global via `body::before`/`body::after` (Task 1 Step 6); icon sprite scoped to exactly the 8 symbols this phase needs (Task 1 Step 3); nav pill active-state per the 4-tab mapping worked out during the design spec's own ambiguity fix (Task 1 Step 4); icon-only toggles with working icon-swap (Task 1 Steps 4 and 7); home hero + 3-stat board, no streak (Task 2 Steps 3–4); stat definitions matching production exactly including the `'learned'`-vs-`'little'` asymmetry (Task 2 Step 1's test explicitly exercises this); stats unconditional/not auth-gated (Task 2 Step 3's `{}` default); existing-copy-preserved vs new-copy-from-production split (Task 2 Step 7's inline comment explaining the distinction); Dashboard untouched (no task references it).
- **Placeholder scan:** no TBD/TODO; every step has complete, exact code; both manual-verification steps reference the concrete production screenshot already captured during brainstorming for a real side-by-side comparison, not a vague "looks right" check.
- **Type consistency:** `home(request)`'s new context keys (`words_learned`, `categories_started`, `pct_complete`) are used identically in Task 2's view and template — checked side by side. The icon sprite's 8 symbol IDs (`i-mark`/`i-moon`/`i-sun`/`i-globe`/`i-check-circle`/`i-folder`/`i-bar-chart`/`i-grad-cap`) are each referenced by exactly the markup that needs them (Task 1's nav for the first 4, Task 2's home page for the last 4) — no symbol is defined without a consumer or referenced without being defined. `data-theme-icon` is set once in Task 1 Step 4's nav markup and read once in Task 1 Step 7's `base.js` — verified the attribute name matches exactly between the two.
