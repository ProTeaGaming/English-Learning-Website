import { useMemo, useRef, useEffect, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA, CAT_MAP } from "../data/vocab-data";
import { DEFAULT_FILTERS, matchesFilters } from "../utils/filters";
import Filters from "./Filters";

export default function Examples({ learned }) {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const listRef = useRef(null);

  const words = useMemo(
    () => VOCAB_DATA.filter((w) => matchesFilters(w, filters, learned)),
    [filters, learned]
  );

  useEffect(() => {
    if (listRef.current) {
      gsap.fromTo(
        listRef.current.children,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.35, ease: "power2.out", stagger: 0.01 }
      );
    }
  }, [words]);

  return (
    <section>
      <div className="mb-5">
        <h1 className="text-[1.7rem] font-extrabold mb-1">Word</h1>
        <p className="text-muted text-[.95rem]">See every word used correctly in a full sentence.</p>
      </div>

      <Filters
        filters={filters}
        setFilters={setFilters}
        resultLabel={`${words.length} word${words.length !== 1 ? "s" : ""}`}
        searchPlaceholder="Search words, definitions, synonyms…"
      />

      <div ref={listRef} className="flex flex-col gap-2.5">
        {words.map((word) => {
          const cat = CAT_MAP[word.cat];
          return (
            <div key={`${word.cat}-${word.w}`} className={`ex-item t-${cat.theme}`}>
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="ex-word">{word.w}</span>
                <span className="ex-pos">{word.pos}</span>
                <span className={`cefr-badge ${word.cefr}`}>{word.cefr}</span>
              </div>
              <div className="ex-sentence" dangerouslySetInnerHTML={{ __html: word.ex }} />
            </div>
          );
        })}
      </div>
    </section>
  );
}
