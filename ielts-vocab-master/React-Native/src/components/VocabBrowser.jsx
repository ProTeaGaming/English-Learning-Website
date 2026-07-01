import { useMemo, useState, useRef } from "react";
import { CATEGORIES, SECTION_ORDER, VOCAB_DATA, CEFR_SECTION, CEFR_CATEGORIES } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";
import ExpandableChips from "./ExpandableChips";
import CategoryCard from "./CategoryCard";

const ALL_SECTIONS = [...SECTION_ORDER, CEFR_SECTION];
const BROWSE_PER_PAGE = 10;

// Pre-compute at module load — runs once, avoids repeated filtering on every render
const CAT_WORDS = (() => {
  const map = {};
  for (const cat of CATEGORIES) {
    map[cat.id] = VOCAB_DATA.filter(w => w.cat === cat.id);
  }
  for (const cat of CEFR_CATEGORIES) {
    map[cat.id] = VOCAB_DATA.filter(w => w.cefr === cat.cefrLevel);
  }
  return map;
})();

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

export default function VocabBrowser({ filters, setFilters, learnMap, onSelectCategory }) {
  const [browsePage, setBrowsePage] = useState(1);
  const [gotoVal, setGotoVal] = useState("");
  const topRef = useRef(null);

  const upd = (patch) => { setFilters(f => ({ ...f, ...patch })); setBrowsePage(1); setGotoVal(""); };

  const sectionsData = useMemo(() => {
    const toShow = filters.section === "all" ? ALL_SECTIONS : [filters.section];

    return toShow.map(section => {
      let cats = section === CEFR_SECTION
        ? CEFR_CATEGORIES
        : CATEGORIES.filter(c => c.section === section);

      if (filters.search) {
        const q = filters.search.toLowerCase();
        cats = cats.filter(c => c.name.toLowerCase().includes(q));
      }

      if (filters.cefr !== "all") {
        cats = [...cats].sort((a, b) => {
          const aCnt = CAT_WORDS[a.id].filter(w => w.cefr === filters.cefr).length;
          const bCnt = CAT_WORDS[b.id].filter(w => w.cefr === filters.cefr).length;
          return bCnt - aCnt;
        });
      }

      return { section, cats };
    }).filter(({ cats }) => cats.length > 0);
  }, [filters]);

  const totalPages = Math.max(1, Math.ceil(sectionsData.length / BROWSE_PER_PAGE));
  const safePage = Math.min(browsePage, totalPages);
  const pageSections = sectionsData.slice((safePage - 1) * BROWSE_PER_PAGE, safePage * BROWSE_PER_PAGE);

  const goTo = (p) => {
    const clamped = Math.max(1, Math.min(totalPages, p));
    setBrowsePage(clamped);
    topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const isDirty = filters.search || filters.section !== "all" || filters.cefr !== "all";

  return (
    <div>
      <div ref={topRef} className="mb-6">
        <h1 className="text-[1.7rem] font-extrabold font-sora mb-1">Vocabulary</h1>
        <p className="text-muted text-[.95rem]">
          {VOCAB_DATA.length} words across {CATEGORIES.length} categories · {[...learnMap.values()].filter(v => v === "learned").length} learned
        </p>
      </div>

      {/* Browse filter bar */}
      <div className="browse-bar">
        <div className="relative">
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[.85rem] opacity-50">🔍</span>
          <input
            type="search"
            value={filters.search}
            onChange={e => upd({ search: e.target.value })}
            placeholder="Search categories…"
            className="w-full appearance-none bg-surface2 border border-line text-ink pl-10 pr-4 py-2.5 rounded-xl text-[.95rem] focus:outline-none focus:border-accent [&::-webkit-search-decoration]:appearance-none [&::-webkit-search-cancel-button]:appearance-none"
          />
        </div>

        <div className="flex gap-2 flex-wrap items-center">
          <span className="filter-label">Section</span>
          <button
            className={"chip" + (filters.section === "all" ? " active" : "")}
            onClick={() => upd({ section: "all" })}
          >
            All Sections
          </button>
          <ExpandableChips
            items={ALL_SECTIONS}
            renderItem={(sec) => (
              <button
                key={sec}
                className={"chip" + (filters.section === sec ? " active" : "")}
                onClick={() => upd({ section: sec })}
              >
                {sec}
              </button>
            )}
          />
        </div>

        <div className="flex gap-2 flex-wrap items-center">
          <span className="filter-label">CEFR Level</span>
          <button
            className={"chip" + (filters.cefr === "all" ? " active" : "")}
            onClick={() => upd({ cefr: "all" })}
          >
            All
          </button>
          {CEFR_LEVELS.map(lvl => (
            <button
              key={lvl}
              className={"chip" + (filters.cefr === lvl ? " active" : "")}
              style={filters.cefr === lvl
                ? { background: cefrColor(lvl), color: "#fff", borderColor: "transparent" }
                : undefined}
              onClick={() => upd({ cefr: lvl })}
            >
              {lvl}
            </button>
          ))}
        </div>

        <div className="flex justify-end">
          <button
            className="clear-btn"
            onClick={() => { setFilters({ search: "", section: "all", cefr: "all" }); setBrowsePage(1); setGotoVal(""); }}
          >
            Clear filters
          </button>
        </div>
      </div>

      {/* Sections + category cards */}
      <div className="flex flex-col gap-10">
        {sectionsData.length === 0 && (
          <p className="text-muted text-[.95rem] py-12 text-center">No categories match the current filters.</p>
        )}
        {pageSections.map(({ section, cats }) => {
          const sectionWordCount = cats.reduce((s, c) => s + CAT_WORDS[c.id].length, 0);
          return (
            <div key={section}>
              <div className="section-header">
                <h2 className="section-title">{section}</h2>
                <div className="section-rule" />
                <span className="section-meta">
                  {cats.length} {cats.length === 1 ? "category" : "categories"} · {sectionWordCount} words
                </span>
              </div>
              <div className="cat-grid">
                {cats.map(cat => {
                  const words = CAT_WORDS[cat.id];
                  const learnedCnt = words.filter(w => learnMap.get(w.w) === "learned").length;
                  const cefrCnt = filters.cefr !== "all"
                    ? words.filter(w => w.cefr === filters.cefr).length
                    : null;
                  return (
                    <CategoryCard
                      key={cat.id}
                      cat={cat}
                      wordCount={words.length}
                      learnedCount={learnedCnt}
                      cefrCount={cefrCnt}
                      cefrLabel={filters.cefr !== "all" ? filters.cefr : null}
                      onClick={() => onSelectCategory(cat)}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
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
    </div>
  );
}
