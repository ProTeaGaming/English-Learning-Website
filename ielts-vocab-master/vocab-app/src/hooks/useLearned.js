import { useCallback, useState } from "react";

const LEARNED_KEY = "ivm_learned_words";

function load() {
  try {
    return new Set(JSON.parse(localStorage.getItem(LEARNED_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

export function useLearned() {
  const [learned, setLearned] = useState(load);

  const toggle = useCallback((word, value) => {
    setLearned((prev) => {
      const next = new Set(prev);
      if (value) next.add(word);
      else next.delete(word);
      localStorage.setItem(LEARNED_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  return { learned, toggle };
}
