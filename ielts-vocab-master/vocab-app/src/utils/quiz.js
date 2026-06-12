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

export const QUIZ_COUNTS = [10, 20, 30, "all"];
export const GAP_COUNTS = [10, 20, 30, "all"];
export const CHALLENGE_COUNTS = [10, 20, 30, "all"];

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

export function buildGapQuestion(word) {
  const others = VOCAB_DATA.filter((w) => w.w !== word.w);
  const samePos = others.filter((w) => w.pos === word.pos);
  const distractorPool = samePos.length >= 3 ? samePos : others;
  const options = buildOptions(word.w, distractorPool, (w) => w.w);
  return { gap: word.gap, options, correct: word.w, word };
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
