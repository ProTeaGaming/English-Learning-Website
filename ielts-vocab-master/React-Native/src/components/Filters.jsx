import { CATEGORIES, SECTION_ORDER } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";
import ExpandableChips from "./ExpandableChips";

export default function Filters({ filters, setFilters, resultLabel, searchPlaceholder, hideCefrRow }) {
  const visibleCats = CATEGORIES.filter(
    (c) => filters.section === "all" || c.section === filters.section
  );

  const update = (patch) => setFilters((f) => ({ ...f, ...patch }));

  return (
    <div className="flex flex-col gap-3.5 mb-6 bg-surface border border-line rounded-2xl px-5 py-4">
      <div className="flex flex-col sm:flex-row gap-2.5 sm:items-center">
        <div className="relative flex-1 min-w-0 sm:min-w-[200px]">
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[.85rem] opacity-50">🔍</span>
          <input
            type="search"
            value={filters.search}
            onChange={(e) => update({ search: e.target.value })}
            placeholder={searchPlaceholder}
            className="w-full appearance-none bg-surface2 border border-line text-ink pl-10 pr-4 py-2.5 rounded-xl text-[.95rem] focus:outline-none focus:border-accent [&::-webkit-search-decoration]:appearance-none [&::-webkit-search-cancel-button]:appearance-none"
          />
        </div>
        <span className="text-[.85rem] text-muted whitespace-nowrap">{resultLabel}</span>
      </div>

      <div className="flex gap-2 flex-wrap items-center">
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
        <button
          className={"chip" + (filters.cat === "all" ? " active" : "")}
          onClick={() => update({ cat: "all" })}
        >
          All Categories
        </button>
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
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <span className="text-[.78rem] font-bold text-muted uppercase tracking-wider mr-1">Progress</span>
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
          className={"chip" + (filters.learned === "little" ? " active" : "")}
          onClick={() => update({ learned: "little" })}
        >
          Little Bit
        </button>
        <button
          className={"chip" + (filters.learned === "unlearned" ? " active" : "")}
          onClick={() => update({ learned: "unlearned" })}
        >
          Not Learned
        </button>
      </div>

      {!hideCefrRow && <div className="flex gap-2 flex-wrap items-center">
        <span className="text-[.78rem] font-bold text-muted uppercase tracking-wider mr-1">CEFR Level</span>
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
          onClick={() => update({ search: "", section: "all", cat: "all", cefr: "all", learned: "all" })}
        >
          Clear filters
        </button>
      </div>}
    </div>
  );
}
