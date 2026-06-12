// ════════════════════════════════════════════════════════
// VOCAB MASTER DATA — merged from data-part1..5
// 35 categories × 12 words = 420 words total
// ════════════════════════════════════════════════════════
import { PART1 } from "./data-part1.js";
import { PART2 } from "./data-part2.js";
import { PART3 } from "./data-part3.js";
import { PART4 } from "./data-part4.js";
import { PART5 } from "./data-part5.js";

// Section groupings — used to organise the category picker into themed blocks
const SECTIONS = {
  "neg-intensity": "Negative Qualities & Criticism",
  "deception-falsehood": "Negative Qualities & Criticism",
  "judgment-criticism": "Negative Qualities & Criticism",
  "weakness-deterioration": "Negative Qualities & Criticism",

  "approval-excellence": "Positive Qualities & Strength",
  "strength-persistence": "Positive Qualities & Strength",
  "support-agreement": "Positive Qualities & Strength",
  "ethics-morality": "Positive Qualities & Strength",

  "emotions-psych": "Mind, Emotion & Description",
  "appearance-character": "Mind, Emotion & Description",
  "tone-atmosphere": "Mind, Emotion & Description",
  "thinking-intelligence": "Mind, Emotion & Description",

  "scope-scale": "Scale, Change & Society",
  "magnitude-impact": "Scale, Change & Society",
  "change-transformation": "Scale, Change & Society",
  "society-politics": "Scale, Change & Society",

  "clarity-certainty": "Academic Writing Toolkit",
  "academic-stance": "Academic Writing Toolkit",
  "connectors-transitions": "Academic Writing Toolkit",
  "linking-words": "Academic Writing Toolkit",

  "professional-register": "Formal English & Fixed Expressions",
  "abstract-nouns": "Formal English & Fixed Expressions",
  "phrasal-verbs": "Formal English & Fixed Expressions",
  "collocations": "Formal English & Fixed Expressions",

  "trends-data": "IELTS Writing Themes I",
  "opinion-argument": "IELTS Writing Themes I",
  "education-learning": "IELTS Writing Themes I",
  "work-career": "IELTS Writing Themes I",

  "environment-sustainability": "IELTS Writing Themes II",
  "technology-modern-life": "IELTS Writing Themes II",
  "travel-society-culture": "IELTS Writing Themes II",
  "health-lifestyle": "IELTS Writing Themes II",

  "precision-upgrades": "Mind, Emotion & Description",
  "essay-power-words": "Academic Writing Toolkit",
  "society-mind-rhetoric": "Scale, Change & Society",
};

const ALL_PARTS = [...PART1, ...PART2, ...PART3, ...PART4, ...PART5];

export const CATEGORIES = ALL_PARTS.map(({ id, name, icon, theme }) => ({
  id,
  name,
  icon,
  theme,
  section: SECTIONS[id] || "Other",
}));

export const VOCAB_DATA = ALL_PARTS.flatMap((cat) =>
  cat.words.map((word) => ({ ...word, cat: cat.id }))
);

export const CAT_MAP = Object.fromEntries(CATEGORIES.map((c) => [c.id, c]));

export const SECTION_ORDER = [
  "Negative Qualities & Criticism",
  "Positive Qualities & Strength",
  "Mind, Emotion & Description",
  "Scale, Change & Society",
  "Academic Writing Toolkit",
  "Formal English & Fixed Expressions",
  "IELTS Writing Themes I",
  "IELTS Writing Themes II",
];
