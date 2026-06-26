import { useState } from "react";

const DEFAULT_VISIBLE_COUNT = 5;

export default function ExpandableChips({ items, renderItem, visibleCount = DEFAULT_VISIBLE_COUNT }) {
  const [expanded, setExpanded] = useState(false);
  const showToggle = items.length > visibleCount;
  const visibleItems = showToggle && !expanded ? items.slice(0, visibleCount) : items;

  return (
    <>
      {visibleItems.map(renderItem)}
      {showToggle && (
        <button type="button" className="view-all-link" onClick={() => setExpanded((e) => !e)}>
          {expanded ? "Hide All" : "View All"}
        </button>
      )}
    </>
  );
}
