import { CAT_MAP } from "../data/vocab-data";

export const DEFAULT_FILTERS = { search: "", section: "all", cat: "all", cefr: "all", learned: "all" };
export const DEFAULT_TOPIC_FILTERS = { section: "all", cat: "all", cefr: "all", learned: "all" };

export function matchesFilters(word, f, learnedSet) {
  const cat = CAT_MAP[word.cat];
  if (f.section !== "all" && cat.section !== f.section) return false;
  if (f.cat !== "all" && word.cat !== f.cat) return false;
  if (f.cefr !== "all" && word.cefr !== f.cefr) return false;
  if (f.learned === "learned" && !learnedSet?.has(word.w)) return false;
  if (f.learned === "unlearned" && learnedSet?.has(word.w)) return false;
  if (f.search) {
    const q = f.search.toLowerCase();
    const hay = [word.w, word.def, ...(word.syn || []), ...(word.ant || [])].join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}
