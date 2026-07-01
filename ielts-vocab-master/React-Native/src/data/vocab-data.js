// ════════════════════════════════════════════════════════
// VOCAB MASTER DATA — merged from data-part1..11
// 85 categories, 1000 words total
// ════════════════════════════════════════════════════════
import { PART1 } from "./data-part1.js";
import { PART2 } from "./data-part2.js";
import { PART3 } from "./data-part3.js";
import { PART4 } from "./data-part4.js";
import { PART5 } from "./data-part5.js";
import { PART6 } from "./data-part6.js";
import { PART7 } from "./data-part7.js";
import { PART8 } from "./data-part8.js";
import { PART9 } from "./data-part9.js";
import { PART10 } from "./data-part10.js";
import { PART11 } from "./data-part11.js";

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

  "hedging-likelihood": "Academic Writing Toolkit II",
  "cause-consequence": "Academic Writing Toolkit II",
  "connectors-time-sequence": "Academic Writing Toolkit II",
  "difficulty-risk": "Academic Writing Toolkit II",

  "proactive-action": "Vivid Description & Communication",
  "quantity-degree": "Vivid Description & Communication",
  "vivid-everyday": "Vivid Description & Communication",
  "communication-disclosure": "Vivid Description & Communication",

  "cognitive-verbs": "Cognition, Logic & Research",
  "research-inquiry": "Cognition, Logic & Research",
  "critical-reasoning": "Cognition, Logic & Research",
  "memory-perception": "Cognition, Logic & Research",

  "academic-connectors-iii": "Academic Connectors III",
  "emphasis-contrast": "Academic Connectors III",
  "cause-purpose": "Academic Connectors III",
  "summary-conclusion": "Academic Connectors III",

  "business-finance": "Career, Business & Leadership",
  "workplace-communication": "Career, Business & Leadership",
  "leadership-management": "Career, Business & Leadership",
  "career-growth": "Career, Business & Leadership",

  "work-tasks": "Workplace Tasks & Formal Language",
  "general-useful-verbs": "Workplace Tasks & Formal Language",
  "formal-register-ii": "Workplace Tasks & Formal Language",

  "governance-law": "Governance, Economy & Society",
  "economy-trade": "Governance, Economy & Society",
  "social-justice": "Governance, Economy & Society",
  "growth-expansion": "Governance, Economy & Society",

  "personality-traits-ii": "Personality, Relationships & Conflict",
  "interpersonal-relationships": "Personality, Relationships & Conflict",
  "conflict-resolution": "Personality, Relationships & Conflict",
  "decision-making": "Personality, Relationships & Conflict",

  "everyday-idioms": "Everyday Life, Money & Idioms",
  "money-shopping": "Everyday Life, Money & Idioms",
  "food-health": "Everyday Life, Money & Idioms",

  "tech-digital-life": "Science, Tech & Innovation",
  "science-innovation": "Science, Tech & Innovation",
  "digital-communication": "Science, Tech & Innovation",
  "ai-automation": "Science, Tech & Innovation",

  "climate-weather": "Nature, Climate & Energy",
  "nature-wildlife": "Nature, Climate & Energy",
  "energy-resources-ii": "Nature, Climate & Energy",

  "travel-experiences": "Travel, Culture & Urban Life",
  "cultural-diversity": "Travel, Culture & Urban Life",
  "urban-development": "Travel, Culture & Urban Life",

  "lifestyle-habits": "Lifestyle, Leisure & Wellbeing",
  "leisure-hobbies": "Lifestyle, Leisure & Wellbeing",
  "health-wellbeing-ii": "Lifestyle, Leisure & Wellbeing",
  "motivation-ambition": "Lifestyle, Leisure & Wellbeing",

  "storytelling-narrative": "Storytelling, Humour & Persuasion",
  "humor-wit": "Storytelling, Humour & Persuasion",
  "persuasion-rhetoric-ii": "Storytelling, Humour & Persuasion",

  "size-shape": "Description: Size, Sound & Movement",
  "sound-light": "Description: Size, Sound & Movement",
  "movement-action": "Description: Size, Sound & Movement",

  "comparison-contrast": "Habits, Comparison & Politeness",
  "habits-routines": "Habits, Comparison & Politeness",
  "risk-caution": "Habits, Comparison & Politeness",
  "politeness-formality": "Habits, Comparison & Politeness",
};

const ALL_PARTS = [...PART1, ...PART2, ...PART3, ...PART4, ...PART5, ...PART6, ...PART7, ...PART8, ...PART9, ...PART10, ...PART11];

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
  "Academic Writing Toolkit II",
  "Vivid Description & Communication",
  "Cognition, Logic & Research",
  "Academic Connectors III",
  "Career, Business & Leadership",
  "Workplace Tasks & Formal Language",
  "Governance, Economy & Society",
  "Personality, Relationships & Conflict",
  "Everyday Life, Money & Idioms",
  "Science, Tech & Innovation",
  "Nature, Climate & Energy",
  "Travel, Culture & Urban Life",
  "Lifestyle, Leisure & Wellbeing",
  "Storytelling, Humour & Persuasion",
  "Description: Size, Sound & Movement",
  "Habits, Comparison & Politeness",
];

export const CEFR_SECTION = "CEFR Levels";

export const CEFR_CATEGORIES = [
  { id: "cefr-B1", name: "B1", icon: "🌱", theme: "te", cefrLevel: "B1", section: CEFR_SECTION },
  { id: "cefr-B2", name: "B2", icon: "⚡", theme: "tb", cefrLevel: "B2", section: CEFR_SECTION },
  { id: "cefr-C1", name: "C1", icon: "🔥", theme: "ta", cefrLevel: "C1", section: CEFR_SECTION },
  { id: "cefr-C2", name: "C2", icon: "💎", theme: "tr", cefrLevel: "C2", section: CEFR_SECTION },
  { id: "cefr-C2+", name: "C2+", icon: "👑", theme: "tpurp", cefrLevel: "C2+", section: CEFR_SECTION },
];
