import { useMemo, useRef, useEffect, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA, CAT_MAP } from "../data/vocab-data";
import { matchesFilters } from "../utils/filters";
import { cefrColor } from "../utils/cefr";
import Filters from "./Filters";

const EX_PER_PAGE = 25;
const CEFR_OPTIONS = [
  { value: "all", label: "All" },
  { value: "B1",  label: "B1",  color: "#22c55e" },
  { value: "B2",  label: "B2",  color: "#3b82f6" },
  { value: "C1",  label: "C1",  color: "#f59e0b" },
  { value: "C2",  label: "C2",  color: "#ef4444" },
  { value: "C2+", label: "C2+", color: "#a855f7" },
];

const DEFAULT_FILTERS = { search: "", section: "all", cat: "all", cefr: "all", learned: "all" };

function pageWindows(current, total) {
  if (total <= 7) return [...Array(total)].map((_, i) => i + 1);
  const pages = [1];
  const lo = Math.max(2, current - 2);
  const hi = Math.min(total - 1, current + 2);
  if (lo > 2) pages.push("...");
  for (let i = lo; i <= hi; i++) pages.push(i);
  if (hi < total - 1) pages.push("...");
  pages.push(total);
  return pages;
}

export default function Examples({ learnMap, openModal }) {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [gotoVal, setGotoVal] = useState("");
  const listRef = useRef(null);
  const topRef = useRef(null);

  const allWords = useMemo(
    () => VOCAB_DATA.filter((w) => matchesFilters(w, filters, learnMap)),
    [filters, learnMap]
  );

  const totalPages = Math.max(1, Math.ceil(allWords.length / EX_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const words = allWords.slice((safePage - 1) * EX_PER_PAGE, safePage * EX_PER_PAGE);

  const goToPage = (p) => {
    const clamped = Math.max(1, Math.min(totalPages, p));
    setPage(clamped);
    topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const updateFilter = (patch) => {
    setFilters((f) => ({ ...f, ...patch }));
    setPage(1);
  };

  useEffect(() => {
    if (listRef.current && listRef.current.children.length) {
      gsap.fromTo(
        listRef.current.children,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.35, ease: "power2.out", stagger: { amount: 0.3, from: "start" } }
      );
    }
  }, [words]);

  const paginationPages = pageWindows(safePage, totalPages);

  return (
    <section>
      <div className="mb-5" ref={topRef}>
        <h1 className="text-[1.7rem] font-extrabold font-sora mb-1">Word</h1>
        <p className="text-muted text-[.95rem]">
          See every word used correctly in a full sentence.
        </p>
      </div>

      {/* Headline CEFR quick-filter bar */}
      <div className="headline-bar">
        {CEFR_OPTIONS.map(({ value, label, color }) => (
          <button
            key={value}
            className={"headline-btn" + (filters.cefr === value ? " active" : "")}
            style={filters.cefr === value && color ? { background: color, borderColor: color } : undefined}
            onClick={() => updateFilter({ cefr: value, section: "all", cat: "all" })}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Filter bar — hideCefrRow since headline handles it */}
      <Filters
        filters={filters}
        setFilters={(patch) => { setFilters(patch); setPage(1); }}
        resultLabel={`${allWords.length} word${allWords.length !== 1 ? "s" : ""}`}
        searchPlaceholder="Search words, definitions, synonyms…"
        hideCefrRow
      />

      {/* Word list */}
      <div ref={listRef} className="flex flex-col gap-2.5">
        {words.map((word) => {
          const cat = CAT_MAP[word.cat];
          return (
            <div
              key={`${word.cat}-${word.w}`}
              className={`ex-item t-${cat.theme} interactive`}
              onClick={() => openModal(word)}
            >
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="ex-word">{word.w}</span>
                <span className="ex-pos">{word.pos}</span>
                <span className={`cefr-badge ${word.cefr}`}>{word.cefr}</span>
              </div>
              <div className="ex-sentence" dangerouslySetInnerHTML={{ __html: word.ex }} />
              <div className="ex-reveal">
                <div className="rdef">{word.def}</div>
                {word.syn?.length > 0 && (
                  <div className="rrow"><b>Synonyms:</b> {word.syn.join(", ")}</div>
                )}
                {word.ant?.length > 0 && (
                  <div className="rrow"><b>Antonyms:</b> {word.ant.join(", ")}</div>
                )}
              </div>
            </div>
          );
        })}
        {words.length === 0 && (
          <p className="text-muted text-[.95rem] py-12 text-center">No words match the current filters.</p>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="page-btn"
            disabled={safePage === 1}
            onClick={() => goToPage(safePage - 1)}
          >‹</button>

          {paginationPages.map((p, i) =>
            p === "..." ? (
              <span key={`ellipsis-${i}`} className="page-btn ellipsis">…</span>
            ) : (
              <button
                key={p}
                className={"page-btn" + (p === safePage ? " active" : "")}
                onClick={() => goToPage(p)}
              >{p}</button>
            )
          )}

          <button
            className="page-btn"
            disabled={safePage === totalPages}
            onClick={() => goToPage(safePage + 1)}
          >›</button>

          <div className="goto-wrap">
            <span className="goto-label">Go to</span>
            <input
              type="number"
              className="goto-input"
              min={1}
              max={totalPages}
              value={gotoVal}
              placeholder={safePage}
              onChange={(e) => setGotoVal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  const n = parseInt(gotoVal, 10);
                  if (!isNaN(n)) goToPage(n);
                  setGotoVal("");
                }
              }}
              onBlur={() => {
                const n = parseInt(gotoVal, 10);
                if (!isNaN(n)) goToPage(n);
                setGotoVal("");
              }}
            />
          </div>
        </div>
      )}
    </section>
  );
}
