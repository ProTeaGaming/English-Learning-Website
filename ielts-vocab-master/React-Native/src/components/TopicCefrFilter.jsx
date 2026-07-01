import { useEffect, useState } from "react";
import { CATEGORIES, SECTION_ORDER } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";
import ExpandableChips from "./ExpandableChips";

export default function TopicCefrFilter({ filters, setFilters, resultLabel }) {
  const [catSearch, setCatSearch] = useState("");

  useEffect(() => {
    setCatSearch("");
  }, [filters.section]);

  const visibleCats = CATEGORIES.filter(
    (c) => filters.section === "all" || c.section === filters.section
  );

  const q = catSearch.toLowerCase();
  const filteredCats = q
    ? visibleCats.filter((c) => c.name.toLowerCase().includes(q))
    : visibleCats;

  const update = (patch) => setFilters((f) => ({ ...f, ...patch }));

  return (
    <div className="browse-bar text-left">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="filter-label">Topic &amp; Level</span>
        {resultLabel && <span className="text-[.85rem] text-muted">{resultLabel}</span>}
      </div>

      <div className="relative">
        <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[.85rem] opacity-50">🔍</span>
        <input
          type="search"
          value={catSearch}
          onChange={(e) => setCatSearch(e.target.value)}
          placeholder="Search categories…"
          className="w-full appearance-none bg-surface2 border border-line text-ink pl-10 pr-4 py-2.5 rounded-xl text-[.95rem] focus:outline-none focus:border-accent [&::-webkit-search-decoration]:appearance-none [&::-webkit-search-cancel-button]:appearance-none"
        />
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <span className="filter-label">Section</span>
        <button
          className={"chip" + (filters.section === "all" ? " active" : "")}
          onClick={() => update({ section: "all", cat: "all" })}
        >
          All Sections
        </button>
        <ExpandableChips
          items={SECTION_ORDER}
          renderItem={(sec) => (
            <button
              key={sec}
              className={"chip" + (filters.section === sec ? " active" : "")}
              onClick={() => update({ section: sec, cat: "all" })}
            >
              {sec}
            </button>
          )}
        />
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <span className="filter-label">Category</span>
        <button
          className={"chip" + (filters.cat === "all" ? " active" : "")}
          onClick={() => update({ cat: "all" })}
        >
          All
        </button>
        {catSearch ? (
          filteredCats.length > 0 ? (
            filteredCats.map((c) => (
              <button
                key={c.id}
                className={`chip t-${c.theme}` + (filters.cat === c.id ? " active" : "")}
                onClick={() => update({ cat: c.id })}
              >
                {c.icon} {c.name}
              </button>
            ))
          ) : (
            <span className="text-[.82rem] text-muted">No categories match</span>
          )
        ) : (
          <ExpandableChips
            items={visibleCats}
            renderItem={(c) => (
              <button
                key={c.id}
                className={`chip t-${c.theme}` + (filters.cat === c.id ? " active" : "")}
                onClick={() => update({ cat: c.id })}
              >
                {c.icon} {c.name}
              </button>
            )}
          />
        )}
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <span className="filter-label">Progress</span>
        <button
          className={"chip" + (filters.learned === "all" ? " active" : "")}
          onClick={() => update({ learned: "all" })}
        >
          All
        </button>
        <button
          className={"chip" + (filters.learned === "learned" ? " active" : "")}
          onClick={() => update({ learned: "learned" })}
        >
          Learned
        </button>
        <button
          className={"chip" + (filters.learned === "unlearned" ? " active" : "")}
          onClick={() => update({ learned: "unlearned" })}
        >
          Not Learned
        </button>
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <span className="filter-label">CEFR</span>
        <button
          className={"chip" + (filters.cefr === "all" ? " active" : "")}
          onClick={() => update({ cefr: "all" })}
        >
          All
        </button>
        {CEFR_LEVELS.map((lvl) => (
          <button
            key={lvl}
            className={"chip" + (filters.cefr === lvl ? " active" : "")}
            style={filters.cefr === lvl ? { background: cefrColor(lvl), color: "#fff", borderColor: "transparent" } : undefined}
            onClick={() => update({ cefr: lvl })}
          >
            {lvl}
          </button>
        ))}
        <button
          className="clear-btn"
          onClick={() => update({ section: "all", cat: "all", cefr: "all", learned: "all" })}
        >
          Clear filters
        </button>
      </div>
    </div>
  );
}
