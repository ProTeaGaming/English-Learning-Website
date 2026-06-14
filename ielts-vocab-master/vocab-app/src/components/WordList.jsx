import { useMemo, useRef, useEffect, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA } from "../data/vocab-data";
import { DEFAULT_FILTERS, matchesFilters } from "../utils/filters";
import Filters from "./Filters";
import WordCard from "./WordCard";

export default function WordList({ learned, toggleLearned }) {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const gridRef = useRef(null);

  const words = useMemo(
    () => VOCAB_DATA.filter((w) => matchesFilters(w, filters, learned)),
    [filters, learned]
  );

  useEffect(() => {
    if (gridRef.current) {
      gsap.fromTo(
        gridRef.current.children,
        { opacity: 0, y: 14 },
        { opacity: 1, y: 0, duration: 0.4, ease: "power2.out", stagger: 0.015 }
      );
    }
  }, [words]);

  return (
    <section>
      <div className="mb-5">
        <h1 className="text-[1.7rem] font-extrabold mb-1">Word List</h1>
        <p className="text-muted text-[.95rem]">
          1000 essential words for IELTS fluency. Hover (or tap) a card to reveal its definition, synonyms, antonyms and an example sentence.
        </p>
      </div>

      <Filters
        filters={filters}
        setFilters={setFilters}
        resultLabel={`${words.length} word${words.length !== 1 ? "s" : ""}`}
        searchPlaceholder="Search words, definitions, synonyms…"
      />

      <div ref={gridRef} className="grid gap-3.5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))" }}>
        {words.map((word) => (
          <WordCard
            key={`${word.cat}-${word.w}`}
            word={word}
            learned={learned.has(word.w)}
            onToggleLearned={toggleLearned}
          />
        ))}
      </div>
    </section>
  );
}
