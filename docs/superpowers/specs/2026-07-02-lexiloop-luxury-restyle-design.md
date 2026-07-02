# LexiLoop Luxury Restyle

**Date:** 2026-07-02
**Scope:** `ielts-vocab-master/Python/Django/vocab-master.html` only. No functional changes.
**Reference:** webpath project's editorial style (light gallery, numbered heroes, serif italics, mono eyebrows, resource cards, tag pills).

## Direction

Both themes polished equally:
- **Light "gallery"** — warm off-white `#f6f5f2` base, ink text, white cards, hairline borders, 20–24px radii.
- **Dark "velvet"** — near-black `#0b0d12` base, low-alpha violet hairlines, soft radial glows.
- **Grain** — fixed SVG-noise overlay ~3% opacity over both themes + soft gradients.
- **Gold** — champagne `#d4af6a` reserved for achievements only (mastered categories, trophies).

## Typography

- Add **Fraunces italic** for taglines/section descriptions; keep Plus Jakarta Sans (headings) and JetBrains Mono (micro-labels).
- Home hero: mono eyebrow, larger airier title, serif-italic subtitle.
- Page heads: mono eyebrow + serif italic description.
- Category section blocks: editorial numbered headers (01, 02, …) with serif sub.

## Cards

- Category cards → webpath resource-card language: soft surface, hairline border, large radius, CEFR colored tag pill, mono word-count footer, floating status pill (`● MASTERED` gold / `● IN PROGRESS` violet).
- Hairline progress bars (2–3px) with mono % labels, everywhere (cards, section blocks, footer dash, CEFR breakdown).

## Motion

- Scroll reveals via IntersectionObserver + GSAP (once, fade/rise) on home sections and section blocks.
- Hover states: slower easing `cubic-bezier(.22,1,.36,1)`, lift + long soft shadow.
- Page transitions: cross-fade + upward settle ~0.5s.

## Out of scope

Functionality, nav structure, brand/mark, streak emoji, other backends, shared data.

## Verification

Load app in both themes; check Home, Category (sections + cards), Word, Test, footer; confirm reveals fire once, hovers smooth, pills correct per progress state.
