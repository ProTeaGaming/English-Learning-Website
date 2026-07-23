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

- [x] **1. Sign-in modal missing.** Currently a plain `<a href="{% url 'account_login' %}">`
      — full page reload to django-allauth's bare default page. The original has
      a JS-driven MODAL (`id="authOverlay"`) that stays on the current page, with
      steps for login/signup/MFA/password-reset and 5 social login buttons
      (Google, Facebook, GitHub, Microsoft, Apple). Rebuild as a real modal,
      using the original's HTML/CSS/JS as reference (search `vocablarry.html`
      for `authOverlay`).
      Built (2026-07-22): full modal with login/signup/MFA/forgot/reset steps,
      wired to `allauth.headless`. Verified end-to-end in a real browser:
      signup -> verify-email link -> sign in; forgot-password -> reset link ->
      new password -> sign in; MFA (TOTP) code entry; Google social-login
      redirect reaching the real provider endpoint.

- [x] **2. `allauth.headless` missing from `INSTALLED_APPS`** in `config/settings.py`.
      Without it, every `/_allauth/browser/v1/...` call the auth JS makes has
      nowhere to go — login doesn't just look wrong, it's broken. Add it back.

- [x] **3. ~~GitHub login provider missing.~~ Corrected: production has no GitHub
      provider at all** (verified directly against `vocablarry.html` and its
      settings — no GitHub button, no `allauth.socialaccount.providers.github`,
      no `SOCIALACCOUNT_PROVIDERS['github']` entry anywhere). This item was based
      on inaccurate information. Built the real 4 providers instead — Google,
      Facebook, Microsoft, Apple — matching production exactly.

- [x] **4. `HEADLESS_FRONTEND_URLS` missing** from `config/settings.py` (needed so
      email verification / password reset links route back into the app
      correctly). Original has:
      ```python
      HEADLESS_FRONTEND_URLS = {
          'account_confirm_email': '/verify-email/{key}',
          'account_reset_password_from_key': '/reset-password/{key}',
      }
      ```

- [x] **5. `/_allauth/` route missing** from `config/urls.py`. Add:
      `path('_allauth/', include('allauth.headless.urls'))`

- [x] **6. Language dropdown has no menu markup at all** — just a bare globe icon
      button. The original has a full dropdown: 11 languages (English + Tiếng
      Việt active, 9 marked "Soon"), scrollable panel, hover states on each row.
      Rebuild from `vocablarry.html`'s `lang-menu`/`langMenu` markup and its
      `.lang-chip`/`.lang-menu`/`.mode-picker-row` CSS.
      Built (2026-07-23): full dropdown ported into `nav.html` with the
      `.lang-chip`/`.lang-menu`/`.mode-picker-row` CSS family, wired to the
      existing en/vi `applyLang()` mechanism in `i18n.js` (open/close +
      row-click-to-select + outside-click-to-close, active-row highlight).
      Note: direct comparison against the current `vocablarry.html` found 12
      languages (2 active + 10 "Soon"), not the 11/9 this item's own summary
      text says — built to match the actual file, not the stale prose.
      Verified live in a real browser: opens, switches language, persists
      across reload, closes on selection.

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

- [x] **8. Home page missing the CEFR Breakdown section** entirely (progress bar
      per level, A1→C2). Port the `.home-cefr-row`/`-track`/`-fill`/`-pct`/`-badge`
      CSS and the corresponding HTML block from `vocablarry.html`'s `page-home`
      section.
      Built (2026-07-23): `config/views.py`'s `home()` now computes a
      per-level (A1/A2/B1/B2/C1/C2) learned-word percentage server-side and
      `templates/home.html` renders the 6-row bar section. Real bug caught by
      live-browser verification (not by the automated tests, which don't
      exercise the real ~5000-word dataset): the first implementation
      iterated every real `CEFRLevel` row, which is actually the full
      12-value scale (A1/A1+/A2/A2+/…/C2+) in this dataset, not 6 as the
      model's `max_length=2` field misleadingly suggested (SQLite doesn't
      enforce that length) — rendered 12 rows instead of production's 6.
      Fixed by bucketing on `cefr_level__code__startswith` against a fixed
      6-item base-level list, matching `vocablarry.html`'s own
      `w.cefr.startsWith(lvl.replace("+",""))` grouping exactly (a "+"
      variant folds into its base level, e.g. C1+ counts toward C1).

- [x] **9. Home page missing "Coming soon" badges** on the Reading/Writing/
      Listening/Speaking cards. Port `.home-sec-pill`/`.home-sec-status`/
      `.home-sec-footer` CSS and matching HTML.
      Built (2026-07-23): the whole "Explore Sections" card grid didn't
      exist on the home page at all yet (not just missing badges) — added
      all 6 cards (Vocabulary/Grammar as Live, Reading/Writing/Listening/
      Speaking as Coming soon) plus the `.home-sec-footer`/`-status`/`-pill`
      CSS. Added the missing `i-headphones` icon symbol to `base.html`'s
      sprite (only Listening needed it; it wasn't previously referenced
      anywhere in VLPE).

- [x] **10. Vocabulary filter pills (Basic/Intermediate/Advanced/CEFR) have no
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
      Built (2026-07-23), adapted rather than copied literally per this
      file's own "outcome not method" ground rule: VLPE never built a
      `.headline-btn`/`data-headline` element — its Vocabulary Tier filter
      (Category browse page) and Stage filter (Word page) are plain `.chip`
      elements with their own `data-browse-tier`/`data-word-tier` attributes
      (added here), matching the sibling `data-browse-cefr`/`data-word-cefr`
      convention already established for the CEFR chip row. Colored
      basic/intermediate/advanced identically to production
      (`--a2`/`--b2`/`--c1`). Skipped porting production's "cefr"/"all"
      pill-color variants — those belong to production's single combined
      Stage bar, which VLPE deliberately split into two separate filter
      rows (Tier + CEFR level) in an earlier sub-project, so there is no
      VLPE element those two rules would apply to.

## Verify — don't assume styling means it works

- [x] **11. JS logic parity unconfirmed.** Total JS across all static/js files is
      a small fraction of the original's single script (which drives quiz
      generation, the learned/unsure toggle, live filter clicks, hybrid question
      randomization). CSS looking right doesn't mean this logic exists or works.
      Actually click through:
      - Mark a word as learned and reload — does it persist?
      - Run a vocabulary quiz to completion — do questions generate correctly?
      - Click every filter chip — does the list actually filter?

      Report anything that's styled but non-functional instead of assuming parity.
      Verified (2026-07-23) with a real account (`verifytester`, allauth
      email-verified) against a real dev server: marked "be" learned on
      `core-action-verbs` (Little Bit → Learned cycle), reloaded — persisted;
      home page's Words Learned/Categories Started stats updated to 1/1
      correctly. Ran a full 10-question Definition Match quiz to completion
      via `/vocabulary/quiz/` → results page tallied 5/10 correctly (verified
      by cross-checking "Review Answers" against each question's actual
      correct/incorrect option). Clicked Tier chips (Basic/Intermediate/
      Advanced) on both the Category browse and Word pages — filtering,
      URL params, and the new item-10 color-coding all worked. No console
      errors observed. Nothing found styled-but-non-functional.

---

## Found in the 2026-07-23 fresh comparison pass

Items 1-4 below are one connected cluster — all reuse the same already-built
`allauth.headless`/`accounts` backend from the items 1-5 auth-modal work, and
should likely be built together.

- [x] **12. Authenticated-user topbar is a plain username + Sign Out link.**
      Production has a `.user-chip` with avatar + a `.user-menu` dropdown:
      name/username/email, "Edit profile", "Reset progress", "Sign out",
      "Delete account" (search `vocablarry.html` for `userChip`/`userMenu`).
      VLPE's `templates/partials/nav.html` has none of this — just
      `{{ user.username }}` and a direct link to `account_logout`.
      Built (2026-07-23): user-chip with avatar (picture-or-initials
      fallback), name/username/email display, wired to new Django context
      processor `config/context_processors.py:user_progress_stats` computing
      authenticated-user stats. User-menu dropdown markup in
      `templates/partials/nav.html` with buttons for Edit profile/Reset
      progress/Sign out/Delete account. Verified in real browser: avatar
      renders, menu opens/closes on click, all links route correctly.

- [x] **13. Live "Learned: X / Y" stat + "N to review" button missing from the
      topbar.** Production's `.stats` block (next to the lang/theme toggles)
      shows a running `learnedCount`/`totalCount` and, when the user has any
      "little bit" words, a `reviewLittleBtn` linking to a filtered review
      view. VLPE has no equivalent anywhere in the nav.
      Built (2026-07-23): live stats section shows "Learned: X / Y" counter
      via `user_progress_stats` context processor in `templates/partials/nav.html`.
      "N to review" link (routing to `/vocabulary/word/?progress=little`)
      appears only when user has "little bit" words marked. Verified: stats
      update when marking words as learned, link appears/disappears
      dynamically as expected.

- [x] **14. Edit Profile modal missing entirely.** Production's `#profileOverlay`
      (avatar upload, name, username, US/UK vocabulary-dialect toggle,
      connected-social-accounts list). The Django backend already exists and
      is already called once, during signup —
      `accounts/views.py:update_profile` (name/username/picture validation,
      already handles the "username taken"/"image too big" cases) and
      `accounts/urls.py:update-profile/` — it's just never exposed as an
      editable UI afterward. The connected-accounts list needs no new
      backend: production drives it off allauth.headless's own
      `/account/providers` endpoint (search `vocablarry.html` for
      `profileConnectionsList`), which the items-1-5 work already wired up
      for the rest of the auth flow.
      Built (2026-07-23): Edit Profile modal in
      `templates/partials/account_modals.html` (avatar upload with live
      preview, full name and username fields, connected-social-accounts list
      with Connect/Disconnect for Google/Facebook/Microsoft/Apple). Wired in
      `static/js/account-modals.js` to existing `POST /auth/update-profile/`
      endpoint for profile updates and allauth's `/account/providers` endpoint
      for social-accounts. Note: US/UK dialect toggle deliberately skipped
      (no `dialect` field on User model, VLPE word data has no spelling variants).
      Verified: avatar upload persists with live preview, name/username changes
      save, social-accounts list loads with real data, Connect/Disconnect
      endpoints function correctly.

- [x] **15. Delete Account modal missing entirely.** Production's
      `#deleteOverlay` (password-confirm, then delete). Backend already
      built and correct — `accounts/views.py:delete_account` (already
      handles Google-only accounts with no usable password) and
      `accounts/urls.py:delete-account/` — just no frontend to call it.
      Built (2026-07-23): Delete Account modal in same
      `templates/partials/account_modals.html` partial with password-confirm
      flow. Password field only shown/required when account has a usable
      password (hidden for Google-only accounts). Wired in
      `static/js/account-modals.js` to existing `POST /auth/delete-account/`
      endpoint. Verified: password-required branch fully tested with real
      database deletion confirmed; no-password branch UI confirmed showing/hiding
      password field correctly for social-login-only accounts.

- [x] **16. Reset Progress feature missing — no backend, no UI.** Production's
      `resetProgressBtn` clears `learn_map`/`grammar_map`(/streak, N/A here)
      and reloads. VLPE has neither an endpoint to clear a user's
      `learn_map`/`grammar_map` server-side nor a button anywhere to trigger it.
      Built (2026-07-23): new `POST /auth/reset-progress/` endpoint added
      (`accounts/views.py`/`accounts/urls.py`) clearing user's `learn_map` and
      `grammar_map` (streak skipped as VLPE has no activity-tracking data).
      Custom confirm overlay UI added to `static/js/account-modals.js` (not
      native browser `confirm()`, consistent with VLPE's modal architecture).
      Verified: Cancel button leaves data untouched, Confirm button clears
      learned-word count and all "little bit" progress markers as expected.

- [x] **17. Sitewide footer missing entirely.** Production's `<footer
      class="site-footer">` (search `vocablarry.html` for `siteFooter`)
      renders on every page: logo/tagline plus a small live dashboard (total
      words, learned %, categories started). It also has a day-streak widget
      with a weekly activity calendar — per the established precedent from
      the home page's 4th stat card (see items 8-9's history), that part
      should stay deferred since VLPE has no activity-tracking data to back
      it. Build the footer, skip the streak widget.
      Built (2026-07-23): new `templates/partials/footer.html`, included
      from `base.html` on every page (unlike the account modals, not
      gated behind authentication — matches production, which shows the
      footer with zeroed stats for guests too). New
      `site_footer_stats` context processor computes total words/learned/
      %/categories-started server-side; extracted a shared
      `categories_started_count()` helper into `vocab/services.py` (was
      duplicated inline in `config/views.py:home` before this). Streak
      widget correctly not built. Verified in a real browser on both the
      home page and a non-home page (`/vocabulary/category/`) — footer
      renders identically on both with live-computed values.

- [x] **18. Reading/Writing/Listening/Speaking stub pages are missing the
      "Under construction" card.** Production's stub pages aren't just an
      eyebrow+h1+p — they also have a `.setup-card` with a hard-hat icon and
      "This section is being built — check back soon." copy. Cheap fix —
      `.setup-card` CSS already exists in `vocab.css`, reusable as-is.
      Built (2026-07-23): added the `.setup-card` block (hard-hat icon +
      copy) to all 4 stub templates, each now loading `vocab.css` via
      `extra_head` (they previously loaded no stylesheet at all). Also
      ported the missing `.setup-card h2`/`.setup-card .sub` CSS rules
      themselves — only the outer `.setup-card` panel style existed in
      VLPE before this. Verified in a real browser on `/reading/` and
      `/speaking/`.

---

## Found in the second fresh comparison pass (re-verified against the current
`D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry\vocablarry.html`, not the stale
zip copy items 1-11 were partly checked against — the two disputed corrections
from items 3 and 6 were independently re-verified against this fresh copy and
confirmed accurate: no GitHub provider anywhere in production, and the language
dropdown really does have 12 rows, not 11)

- [ ] **19. Staff/debug inline-edit mode missing entirely.** Production has a
      staff-only "Debug mode" toggle (search `vocablarry.html` for
      `debugToggle`) that, when on, lets staff/admin accounts edit or delete a
      word directly from its detail view (`modalEditWordBtn`,
      `modalDeleteWordBtn`, `dbgAddWordBtn`). Zero mentions of any of this
      anywhere in VLPE — no toggle, no inline edit/delete UI, no staff-gating.

- [ ] **20. Home page CTAs skip the intent-picker modal.** In production,
      clicking "Start Learning" or "Quick Test" opens a modal
      (`modePickerOverlay`/`openModePicker()`) asking which skill — Vocabulary
      or Grammar — before proceeding. VLPE's "Start Learning" button just
      hard-links straight to `{% url 'vocabulary_category_list' %}`, so a user
      wanting Grammar or a quiz from the home page gets routed into Vocabulary
      browsing regardless of intent.

- [x] **21. Four icon symbols missing from the sprite** — `i-butterfly`,
      `i-heart`, `i-rose`, `i-waves` exist in production's SVG sprite (93 total
      symbols) but not VLPE's (89 total). Same class of bug as the
      `i-headphones` one already caught and fixed in item 9 — whichever
      category or word maps to one of these four will silently fall back to
      the generic book icon instead of its real one. Diff the two `<symbol id="i-...">`
      lists to find any others as new content gets added later.
      Built (2026-07-23): added all 4 `<symbol>` defs to `base.html`'s
      sprite. Also found and fixed a second, related gap while here:
      `vocab_extras.py`'s `EMOJI_ICON_MAP` — despite its own comment
      claiming to be "transcribed verbatim" from production — was missing
      the 4 emoji keys (🌊/🦋/💙/🌹) that actually map to these icons, so
      even with the symbols added, nothing could have reached them yet.
      Added those 4 map entries too, so the fix is actually reachable, not
      just latent. No current VLPE category/word data uses these emoji
      yet (confirmed by grep) — this closes the gap for whenever one does.

- [ ] **22. Word quick-view is a full page, not an in-place popup.** Production
      opens word details in a lightweight modal (`#word-modal`) over the
      current browse grid — stays in place, closes on backdrop click,
      preserves scroll/filter state. VLPE built it as a full separate page
      instead (`vocab/word_detail.html`). May be an intentional page-vs-modal
      call, but it changes the actual interaction: browsing a list and peeking
      at several words now requires navigating away and back each time instead
      of a quick popup. Flag for a decision rather than assuming either way.

---

After each fix, open the running site and https://vocablarry.pythonanywhere.com
side by side and confirm they match before checking off the item.
