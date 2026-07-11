import { CAT_MAP } from "../data/vocab-data";

export const DEFAULT_FILTERS = { search: "", section: "all", cat: "all", cefr: "all", learned: "all" };
export const DEFAULT_TOPIC_FILTERS = { section: "all", cat: "all", cefr: "all", learned: "all" };

export function matchesFilters(word, f, learnMap) {
  const cat = CAT_MAP[word.cat];
  if (f.section !== "all" && cat.section !== f.section) return false;
  if (f.cat !== "all" && word.cat !== f.cat) return false;
  if (f.cefr !== "all" && word.cefr !== f.cefr) return false;
  const ws = learnMap?.get ? (learnMap.get(word.w) || null) : null;
  if (f.learned === "learned" && ws !== "learned") return false;
  if (f.learned === "little" && ws !== "little") return false;
  if (f.learned === "unlearned" && ws !== null) return false;
  if (f.search) {
    const q = f.search.toLowerCase();
    const hay = [word.w, word.def, ...(word.syn || []), ...(word.ant || [])].join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}
