import { useMemo } from "react";
import { CATEGORIES, SECTION_ORDER, VOCAB_DATA, CEFR_SECTION, CEFR_CATEGORIES } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";
import ExpandableChips from "./ExpandableChips";
import CategoryCard from "./CategoryCard";

const ALL_SECTIONS = [...SECTION_ORDER, CEFR_SECTION];

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

export default function VocabBrowser({ filters, setFilters, learned, onSelectCategory }) {
  const upd = (patch) => setFilters(f => ({ ...f, ...patch }));

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

  const isDirty = filters.search || filters.section !== "all" || filters.cefr !== "all";

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-[1.7rem] font-extrabold font-sora mb-1">Vocabulary</h1>
        <p className="text-muted text-[.95rem]">
          {VOCAB_DATA.length} words across {CATEGORIES.length} categories · {learned.size} learned
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
          <span className="filter-label">Sort by CEFR</span>
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
          {isDirty && (
            <button
              className="clear-btn"
              onClick={() => setFilters({ search: "", section: "all", cefr: "all" })}
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Sections + category cards */}
      <div className="flex flex-col gap-10">
        {sectionsData.length === 0 && (
          <p className="text-muted text-[.95rem] py-12 text-center">No categories match the current filters.</p>
        )}
        {sectionsData.map(({ section, cats }) => {
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
                  const learnedCnt = words.filter(w => learned.has(w.w)).length;
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
    </div>
  );
}
