import { useMemo, useRef, useEffect, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";
import WordCard from "./WordCard";
import VocabBrowser from "./VocabBrowser";

const DEFAULT_BROWSE = { search: "", section: "all", cefr: "all" };
const DEFAULT_CAT = { search: "", cefr: "all", learned: "all" };
const CAT_PER_PAGE = 25;

function getWordsForCategory(cat) {
  if (cat.cefrLevel) return VOCAB_DATA.filter((w) => w.cefr === cat.cefrLevel);
  return VOCAB_DATA.filter((w) => w.cat === cat.id);
}

function pageWindows(cur, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [1];
  const lo = Math.max(2, cur - 2);
  const hi = Math.min(total - 1, cur + 2);
  if (lo > 2) pages.push("...");
  for (let i = lo; i <= hi; i++) pages.push(i);
  if (hi < total - 1) pages.push("...");
  pages.push(total);
  return pages;
}

export default function WordList({ learnMap, onCycle, openModal }) {
  const [activeCategory, setActiveCategory] = useState(null);
  const [browseFilters, setBrowseFilters] = useState(DEFAULT_BROWSE);
  const [catFilters, setCatFilters] = useState(DEFAULT_CAT);
  const [catPage, setCatPage] = useState(1);
  const [gotoVal, setGotoVal] = useState("");
  const gridRef = useRef(null);
  const topRef = useRef(null);

  const handleSelectCategory = (cat) => {
    setActiveCategory(cat);
    setCatFilters(DEFAULT_CAT);
    setCatPage(1);
    setGotoVal("");
  };

  const allCategoryWords = useMemo(
    () => (activeCategory ? getWordsForCategory(activeCategory) : []),
    [activeCategory]
  );

  const filteredWords = useMemo(() => {
    return allCategoryWords.filter((w) => {
      if (catFilters.cefr !== "all" && w.cefr !== catFilters.cefr) return false;
      const ws = learnMap.get(w.w) || null;
      if (catFilters.learned === "learned" && ws !== "learned") return false;
      if (catFilters.learned === "little" && ws !== "little") return false;
      if (catFilters.learned === "unlearned" && ws !== null) return false;
      if (catFilters.search) {
        const q = catFilters.search.toLowerCase();
        const hay = [w.w, w.def, ...(w.syn || []), ...(w.ant || [])].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [allCategoryWords, catFilters, learnMap]);

  const totalPages = Math.max(1, Math.ceil(filteredWords.length / CAT_PER_PAGE));
  const safePage = Math.min(catPage, totalPages);
  const pageWords = filteredWords.slice((safePage - 1) * CAT_PER_PAGE, safePage * CAT_PER_PAGE);

  const upd = (patch) => { setCatFilters((f) => ({ ...f, ...patch })); setCatPage(1); setGotoVal(""); };

  const goTo = (p) => {
    const clamped = Math.max(1, Math.min(totalPages, p));
    setCatPage(clamped);
    topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  useEffect(() => {
    if (gridRef.current && pageWords.length > 0) {
      gsap.fromTo(
        gridRef.current.children,
        { opacity: 0, y: 14 },
        { opacity: 1, y: 0, duration: 0.4, ease: "power2.out", stagger: 0.015 }
      );
    }
  }, [pageWords]);

  if (!activeCategory) {
    return (
      <VocabBrowser
        filters={browseFilters}
        setFilters={setBrowseFilters}
        learnMap={learnMap}
        onSelectCategory={handleSelectCategory}
      />
    );
  }

  const catIsDirty = catFilters.search || catFilters.cefr !== "all" || catFilters.learned !== "all";

  return (
    <section>
      <div ref={topRef} className="cat-view-header">
        <button className="back-btn" onClick={() => setActiveCategory(null)}>
          ← All Sections
        </button>
        <div className="cat-view-title-row">
          <div className={`cat-view-icon t-${activeCategory.theme}`}>{activeCategory.icon}</div>
          <div>
            <h1 className="cat-view-name">{activeCategory.name}</h1>
            <p className="text-muted text-[.88rem] mt-0.5">
              {filteredWords.length === allCategoryWords.length
                ? `${allCategoryWords.length} words`
                : `${filteredWords.length} of ${allCategoryWords.length} words`}
            </p>
          </div>
        </div>
      </div>

      <div className="cat-filter-bar">
        <div className="relative">
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[.85rem] opacity-50">🔍</span>
          <input
            type="search"
            value={catFilters.search}
            onChange={(e) => upd({ search: e.target.value })}
            placeholder="Search words, definitions, synonyms…"
            className="w-full appearance-none bg-surface2 border border-line text-ink pl-10 pr-4 py-2.5 rounded-xl text-[.95rem] focus:outline-none focus:border-accent [&::-webkit-search-decoration]:appearance-none [&::-webkit-search-cancel-button]:appearance-none"
          />
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          <span className="filter-label">CEFR</span>
          <button className={"chip" + (catFilters.cefr === "all" ? " active" : "")} onClick={() => upd({ cefr: "all" })}>All</button>
          {CEFR_LEVELS.map((lvl) => (
            <button
              key={lvl}
              className={"chip" + (catFilters.cefr === lvl ? " active" : "")}
              style={catFilters.cefr === lvl ? { background: cefrColor(lvl), color: "#fff", borderColor: "transparent" } : undefined}
              onClick={() => upd({ cefr: lvl })}
            >{lvl}</button>
          ))}
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          <span className="filter-label">Progress</span>
          {[["all", "All"], ["learned", "Learned"], ["little", "Little Bit"], ["unlearned", "Not Learned"]].map(([val, label]) => (
            <button key={val} className={"chip" + (catFilters.learned === val ? " active" : "")} onClick={() => upd({ learned: val })}>{label}</button>
          ))}
          {catIsDirty && (
            <button className="clear-btn" onClick={() => { setCatFilters(DEFAULT_CAT); setCatPage(1); setGotoVal(""); }}>Clear</button>
          )}
        </div>
      </div>

      <div
        ref={gridRef}
        className="grid gap-3.5"
        style={{ gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))" }}
      >
        {pageWords.map((word) => (
          <WordCard
            key={`${word.cat}-${word.w}`}
            word={word}
            learnState={learnMap.get(word.w) || null}
            onCycle={onCycle}
            openModal={openModal}
          />
        ))}
        {filteredWords.length === 0 && (
          <p className="text-muted text-[.95rem] col-span-full py-10 text-center">
            No words match the current filters.
          </p>
        )}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button className="page-btn" disabled={safePage === 1} onClick={() => goTo(safePage - 1)}>«</button>

          {pageWindows(safePage, totalPages).map((p, i) =>
            p === "..." ? (
              <span key={`e${i}`} className="page-btn ellipsis">…</span>
            ) : (
              <button
                key={p}
                className={"page-btn" + (p === safePage ? " active" : "")}
                onClick={() => goTo(p)}
              >{p}</button>
            )
          )}

          <button className="page-btn" disabled={safePage === totalPages} onClick={() => goTo(safePage + 1)}>»</button>

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
                  if (!isNaN(n)) goTo(n);
                  setGotoVal("");
                }
              }}
              onBlur={() => {
                const n = parseInt(gotoVal, 10);
                if (!isNaN(n)) goTo(n);
                setGotoVal("");
              }}
            />
          </div>
        </div>
      )}
    </section>
  );
}
