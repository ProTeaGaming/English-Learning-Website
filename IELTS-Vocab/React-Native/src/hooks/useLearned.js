import { useCallback, useMemo, useState } from "react";

const LEARN_KEY = "ivm_learned_words";

function load() {
  try {
    const raw = localStorage.getItem(LEARN_KEY);
    if (!raw) return new Map();
    const parsed = JSON.parse(raw);
    // Migrate from old boolean-Set format (array of strings)
    if (Array.isArray(parsed)) {
      return new Map(parsed.map((w) => [w, "learned"]));
    }
    return new Map(Object.entries(parsed));
  } catch {
    return new Map();
  }
}

function save(map) {
  try {
    localStorage.setItem(LEARN_KEY, JSON.stringify(Object.fromEntries(map)));
  } catch { /* storage unavailable */ }
}

const STATES = [null, "little", "learned"];

export function useLearned() {
  const [learnMap, setLearnMap] = useState(load);

  const cycle = useCallback((word) => {
    setLearnMap((prev) => {
      const next = new Map(prev);
      const current = next.get(word) || null;
      const newState = STATES[(STATES.indexOf(current) + 1) % STATES.length];
      if (newState === null) next.delete(word);
      else next.set(word, newState);
      save(next);
      return next;
    });
  }, []);

  const setWordState = useCallback((word, value) => {
    setLearnMap((prev) => {
      const next = new Map(prev);
      if (value === null) next.delete(word);
      else next.set(word, value);
      save(next);
      return next;
    });
  }, []);

  const learnedCount = useMemo(
    () => [...learnMap.values()].filter((v) => v === "learned").length,
    [learnMap]
  );

  return { learnMap, cycle, setWordState, learnedCount };
}
