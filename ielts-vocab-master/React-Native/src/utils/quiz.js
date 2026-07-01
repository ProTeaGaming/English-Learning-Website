import { VOCAB_DATA } from "../data/vocab-data";

export function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function buildOptions(correct, others, getValue) {
  const opts = new Set([correct]);
  const pool = shuffle([...others]);
  let i = 0;
  while (opts.size < 4 && i < pool.length) {
    const candidate = getValue(pool[i]);
    if (candidate && !opts.has(candidate)) opts.add(candidate);
    i++;
  }
  return shuffle([...opts]);
}

export const QUIZ_MODES = [
  { id: "definition", name: "Definition Match", desc: "See a word — choose its correct definition." },
  { id: "word", name: "Word from Definition", desc: "Read a definition — choose the matching word." },
  { id: "synonym", name: "Synonym Match", desc: "See a word — choose a word with a similar meaning." },
  { id: "antonym", name: "Antonym Match", desc: "See a word — choose a word with the opposite meaning." },
  { id: "mixed", name: "Mixed Review", desc: "A random mix of every question type." },
];

export const GAP_MODES = [
  { id: "context",     name: "Contextual Definition", desc: "The sentence provides context clues — use them to find the missing word." },
  { id: "nuance",      name: "Lexical Nuance",        desc: "Near-synonyms are the distractors — only one word is precisely correct." },
  { id: "collocation", name: "Collocation & Idiom",   desc: "The blank requires a specific fixed word partnership or collocation." },
  { id: "connotation", name: "Connotation Match",     desc: "Choose the word whose tone — positive, negative or formal — fits the sentence." },
  { id: "mixed",       name: "Mixed Review",          desc: "A random mix of all four gap fill types." },
];

export const TEST_MODE_ORDER = ["quiz", "gap", "challenge"];
export const TEST_COUNTS = [10, 20, 30, "all"];

export const TEST_MODE_META = {
  quiz: {
    toggleLabel: "Quiz",
    pageTitle: "Quiz",
    pageDesc: "Test your knowledge with multiple question types.",
    setupTitle: "Choose a quiz mode",
    setupSub: "Pick a question style, choose how many questions, then start.",
    poolUnit: "word",
    countLabel: (c) => (c === "all" ? "All words" : `${c} questions`),
    startLabel: "Start Quiz",
    resultTitle: "Quiz Complete",
    resultMessage: (pct) => {
      if (pct === 100) return "Perfect score! Outstanding vocabulary mastery.";
      if (pct >= 80) return "Excellent work — you know these words well.";
      if (pct >= 60) return "Good effort — a bit more practice and you'll nail it.";
      return "Keep practising — review the word list and try again.";
    },
    secondaryButtonLabel: "Change Mode",
  },
  gap: {
    toggleLabel: "Fill the Gap",
    pageTitle: "Fill the Gap",
    pageDesc: "Choose the word that correctly completes each sentence.",
    setupTitle: "Choose a gap fill mode",
    setupSub: "Pick a question style, choose how many sentences, then start.",
    poolUnit: "sentence",
    countLabel: (c) => (c === "all" ? "All sentences" : `${c} sentences`),
    startLabel: "Start Exercise",
    resultTitle: "Exercise Complete",
    resultMessage: (pct) => {
      if (pct === 100) return "Flawless! Every gap filled correctly.";
      if (pct >= 80) return "Great job — your usage is on point.";
      if (pct >= 60) return "Solid attempt — review the examples page for tricky words.";
      return "Keep practising — re-reading the example sentences will help.";
    },
    secondaryButtonLabel: "Change Mode",
  },
  challenge: {
    toggleLabel: "Challenge",
    pageTitle: "Challenge",
    pageDesc: "The jack-of-all-trades test: definitions, synonyms, antonyms, word recall and fill-the-gap, all mixed into one round.",
    setupTitle: "Ready for the Challenge?",
    setupSub: "Every question can be any type — choose your topic, level and length, then go.",
    poolUnit: "word",
    countLabel: (c) => (c === "all" ? "All words" : `${c} questions`),
    startLabel: "Start Challenge",
    resultTitle: "Challenge Complete",
    resultMessage: (pct) => {
      if (pct === 100) return "Perfect score! You're ready for anything the exam throws at you.";
      if (pct >= 80) return "Excellent — a strong, well-rounded command of these words.";
      if (pct >= 60) return "Good effort — a bit more practice across modes and you'll nail it.";
      return "Keep practising — try the Category and Quiz pages to build confidence.";
    },
    secondaryButtonLabel: "Change Setup",
  },
};

export const GAP_POOL = VOCAB_DATA.filter((w) => w.gap && w.gap.includes("___"));

export function randomMixedMode(word) {
  const options = ["definition", "word"];
  if (word.syn && word.syn.length) options.push("synonym");
  if (word.ant && word.ant.length) options.push("antonym");
  return options[Math.floor(Math.random() * options.length)];
}

export function buildQuestion(word, mode) {
  const others = VOCAB_DATA.filter((w) => w.w !== word.w);
  let prompt, text, correct, options;
  switch (mode) {
    case "word":
      prompt = "Which word matches this definition?";
      text = word.def;
      correct = word.w;
      options = buildOptions(correct, others, (w) => w.w);
      break;
    case "synonym":
      prompt = "Choose the closest synonym";
      text = `${word.w} (${word.pos})`;
      correct = capitalize(word.syn[Math.floor(Math.random() * word.syn.length)]);
      options = buildOptions(correct, others.filter((w) => w.w !== correct), (w) => w.w);
      break;
    case "antonym":
      prompt = "Choose the word with the opposite meaning";
      text = `${word.w} (${word.pos})`;
      correct = capitalize(word.ant[Math.floor(Math.random() * word.ant.length)]);
      options = buildOptions(correct, others.filter((w) => w.w !== correct), (w) => w.w);
      break;
    default:
      prompt = "Choose the correct definition";
      text = `${word.w} (${word.pos})`;
      correct = word.def;
      options = buildOptions(correct, others, (w) => w.def);
  }
  return { prompt, text, options, correct, word };
}

export function buildGapQuestion(word, gapMode = "context") {
  const others = VOCAB_DATA.filter((w) => w.w !== word.w);
  const samePos = others.filter((w) => w.pos === word.pos);
  let distractorPool, prompt;

  if (gapMode === "mixed") {
    const concrete = ["context", "nuance", "collocation", "connotation"];
    return buildGapQuestion(word, concrete[Math.floor(Math.random() * concrete.length)]);
  }

  switch (gapMode) {
    case "nuance": {
      const synSet = new Set((word.syn || []).map((s) => s.toLowerCase()));
      const synPool = others.filter(
        (w) => w.syn && w.syn.some((s) => synSet.has(s.toLowerCase()))
      );
      distractorPool = synPool.length >= 3 ? synPool : samePos;
      prompt = "Near-synonyms are the distractors — choose the most precise word";
      break;
    }
    case "collocation": {
      const sameCat = others.filter((w) => w.cat === word.cat);
      distractorPool = sameCat.length >= 3 ? sameCat : samePos;
      prompt = "Choose the word that completes the fixed expression";
      break;
    }
    case "connotation": {
      const antSet = new Set((word.ant || []).map((a) => a.toLowerCase()));
      const antPool = others.filter((w) => antSet.has(w.w.toLowerCase()));
      distractorPool =
        antPool.length >= 2
          ? [...antPool, ...samePos.filter((w) => !antSet.has(w.w.toLowerCase()))]
          : samePos;
      prompt = "Choose the word that matches the sentence's tone";
      break;
    }
    default: {
      distractorPool = samePos.length >= 3 ? samePos : others;
      prompt = "Use the sentence context to identify the missing word";
    }
  }

  const options = buildOptions(word.w, distractorPool, (w) => w.w);
  return { gap: word.gap, options, correct: word.w, word, prompt };
}

// Hybrid "Challenge" question: randomly picks the fill-the-gap exercise or
// one of the quiz modes (weighted toward modes the word actually supports).
export function buildHybridQuestion(word) {
  const modes = ["gap", "definition", "word"];
  if (word.syn && word.syn.length) modes.push("synonym");
  if (word.ant && word.ant.length) modes.push("antonym");
  const pick = modes[Math.floor(Math.random() * modes.length)];
  if (pick === "gap") return { type: "gap", ...buildGapQuestion(word) };
  return { type: "quiz", ...buildQuestion(word, pick) };
}
