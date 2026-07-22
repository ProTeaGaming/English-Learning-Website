# Fixes needed — VocabLarry Professional Environment

Source of truth: `D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry\vocablarry.html`
(also live at https://vocablarry.pythonanywhere.com). Every issue below was found
by direct comparison against that file — confirm each fix against it, don't just
make something that looks plausible.

**Ground rule:** "identical design and functionality" is about the OUTCOME, not
the method. Real Django templates (`{% extends %}`, `{% include %}`, `{% for %}`
loops over querysets, context variables) are fine and encouraged — that's better
architecture than the original's single static file. What's NOT fine: dropping
CSS rules, dropping HTML sections, or reimplementing a feature in a simplified
form that behaves differently. If you change how something is built, verify the
result still matches `vocablarry.html` before checking it off — don't assume
"close enough."

Check items off as you fix them. Verify against the real site before moving to
the next one.

## Functionally broken (not just unstyled)

- [ ] **1. Sign-in modal missing.** Currently a plain `<a href="{% url 'account_login' %}">`
      — full page reload to django-allauth's bare default page. The original has
      a JS-driven MODAL (`id="authOverlay"`) that stays on the current page, with
      steps for login/signup/MFA/password-reset and 5 social login buttons
      (Google, Facebook, GitHub, Microsoft, Apple). Rebuild as a real modal,
      using the original's HTML/CSS/JS as reference (search `vocablarry.html`
      for `authOverlay`).

- [ ] **2. `allauth.headless` missing from `INSTALLED_APPS`** in `config/settings.py`.
      Without it, every `/_allauth/browser/v1/...` call the auth JS makes has
      nowhere to go — login doesn't just look wrong, it's broken. Add it back.

- [ ] **3. GitHub login provider missing.** `allauth.socialaccount.providers.github`
      absent from `INSTALLED_APPS`, and no `'github'` entry in
      `SOCIALACCOUNT_PROVIDERS`. The GitHub button shows but does nothing. Add both.

- [ ] **4. `HEADLESS_FRONTEND_URLS` missing** from `config/settings.py` (needed so
      email verification / password reset links route back into the app
      correctly). Original has:
      ```python
      HEADLESS_FRONTEND_URLS = {
          'account_confirm_email': '/verify-email/{key}',
          'account_reset_password_from_key': '/reset-password/{key}',
      }
      ```

- [ ] **5. `/_allauth/` route missing** from `config/urls.py`. Add:
      `path('_allauth/', include('allauth.headless.urls'))`

- [ ] **6. Language dropdown has no menu markup at all** — just a bare globe icon
      button. The original has a full dropdown: 11 languages (English + Tiếng
      Việt active, 9 marked "Soon"), scrollable panel, hover states on each row.
      Rebuild from `vocablarry.html`'s `lang-menu`/`langMenu` markup and its
      `.lang-chip`/`.lang-menu`/`.mode-picker-row` CSS.

## Specific CSS bug — exact fix known

- [x] **7. Vocabulary/Grammar nav dropdown (Category/Word/Quiz submenu) is wider
      than its trigger button and overhangs to the side.**

      Current buggy CSS:
      ```css
      .nav-dropdown{
        display: none; position: absolute; top: calc(100% + 8px); left: 0;
        min-width: 160px; ... border-radius: 16px;
      }
      ```

      Original CSS (dropdown width must equal the button's width, sit flush
      underneath it, no gap, only bottom corners rounded):
      ```css
      .nav-dropdown{
        display:none; position:absolute; left:0; top:100%; width:100%; z-index:60;
        background: rgba(22,26,35,.94); backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgb(var(--violet) / .22); border-top:none;
        border-radius: 0 0 14px 14px; box-shadow: 0 16px 48px rgba(0,0,0,.5);
        overflow:hidden;
      }
      ```

      Replace `min-width:160px` with `width:100%`, remove the top gap
      (`top:100%` not `calc(100% + 8px)`), and fix `border-radius` to
      `0 0 14px 14px`. If Vietnamese is supported, also port these two rules so
      long labels don't overflow:
      ```css
      html[lang="vi"] .nav-group[data-section="vocabulary"] .tab{min-width:96px; text-align:center;}
      html[lang="vi"] .nav-group[data-section="vocabulary"] .nav-dropdown{min-width:96px;}
      ```

## Missing sections/styling

- [ ] **8. Home page missing the CEFR Breakdown section** entirely (progress bar
      per level, A1→C2). Port the `.home-cefr-row`/`-track`/`-fill`/`-pct`/`-badge`
      CSS and the corresponding HTML block from `vocablarry.html`'s `page-home`
      section.

- [ ] **9. Home page missing "Coming soon" badges** on the Reading/Writing/
      Listening/Speaking cards. Port `.home-sec-pill`/`.home-sec-status`/
      `.home-sec-footer` CSS and matching HTML.

- [ ] **10. Vocabulary filter pills (Basic/Intermediate/Advanced/CEFR) have no
      color-coding when active** — the CSS only exists for Grammar's equivalent
      (`data-grammar-stage`), not Vocabulary's (`data-headline` / `data-word-headline`).
      Port these rules from `vocablarry.html`:
      ```css
      .headline-btn.active[data-headline="basic"],.headline-btn.active[data-word-headline="basic"]{background:var(--a2); border-color:var(--a2); color:#064e3b;}
      .headline-btn.active[data-headline="intermediate"],.headline-btn.active[data-word-headline="intermediate"]{background:var(--b2); border-color:var(--b2); color:#fff;}
      .headline-btn.active[data-headline="advanced"],.headline-btn.active[data-word-headline="advanced"]{background:var(--c1); border-color:var(--c1); color:#1c1917;}
      .headline-btn.active[data-headline="cefr"],.headline-btn.active[data-word-headline="cefr"]{background:var(--c2p); border-color:var(--c2p); color:#fff;}
      .headline-btn.active[data-headline="all"],.headline-btn.active[data-word-headline="all"]{background:var(--accent); border-color:var(--accent); color:#fff;}
      ```

## Verify — don't assume styling means it works

- [ ] **11. JS logic parity unconfirmed.** Total JS across all static/js files is
      a small fraction of the original's single script (which drives quiz
      generation, the learned/unsure toggle, live filter clicks, hybrid question
      randomization). CSS looking right doesn't mean this logic exists or works.
      Actually click through:
      - Mark a word as learned and reload — does it persist?
      - Run a vocabulary quiz to completion — do questions generate correctly?
      - Click every filter chip — does the list actually filter?

      Report anything that's styled but non-functional instead of assuming parity.

---

After each fix, open the running site and https://vocablarry.pythonanywhere.com
side by side and confirm they match before checking off the item.
