import { CATEGORIES, SECTION_ORDER } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";

export default function TopicCefrFilter({ filters, setFilters, resultLabel }) {
  const visibleCats = CATEGORIES.filter(
    (c) => filters.section === "all" || c.section === filters.section
  );

  const update = (patch) => setFilters((f) => ({ ...f, ...patch }));

  return (
    <div className="flex flex-col gap-3 mb-6 text-left">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="text-[.78rem] font-bold text-muted uppercase tracking-wider">Topic &amp; Level</span>
        {resultLabel && <span className="text-[.85rem] text-muted">{resultLabel}</span>}
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <button
          className={"chip" + (filters.section === "all" ? " active" : "")}
          onClick={() => update({ section: "all", cat: "all" })}
        >
          All Sections
        </button>
        {SECTION_ORDER.map((sec) => (
          <button
            key={sec}
            className={"chip" + (filters.section === sec ? " active" : "")}
            onClick={() => update({ section: sec, cat: "all" })}
          >
            {sec}
          </button>
        ))}
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <button
          className={"chip" + (filters.cat === "all" ? " active" : "")}
          onClick={() => update({ cat: "all" })}
        >
          All Categories
        </button>
        {visibleCats.map((c) => (
          <button
            key={c.id}
            className={`chip t-${c.theme}` + (filters.cat === c.id ? " active" : "")}
            onClick={() => update({ cat: c.id })}
          >
            {c.icon} {c.name}
          </button>
        ))}
      </div>

      <div className="flex gap-2 flex-wrap items-center">
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
          onClick={() => update({ section: "all", cat: "all", cefr: "all" })}
        >
          Clear filters
        </button>
      </div>
    </div>
  );
}
