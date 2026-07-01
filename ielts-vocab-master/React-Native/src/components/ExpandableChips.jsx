import { useState, useLayoutEffect, useRef } from "react";

export default function ExpandableChips({ items, renderItem, maxRows = 2 }) {
  const firstId = items.length > 0 ? (items[0]?.id ?? String(items[0])) : "";
  const currentKey = `${items.length}:${firstId}`;
  const [page, setPage] = useState(0);
  const [pageBreaks, setPageBreaks] = useState(null);
  const [prevKey, setPrevKey] = useState(currentKey);
  const measureRef = useRef(null);

  if (prevKey !== currentKey) {
    setPrevKey(currentKey);
    setPage(0);
    setPageBreaks(null);
  }

  useLayoutEffect(() => {
    if (pageBreaks !== null || !measureRef.current) return;

    const parent = measureRef.current.parentElement;
    if (!parent) { setPageBreaks([[0, items.length]]); return; }

    const chipEls = Array.from(measureRef.current.children);
    if (!chipEls.length) { setPageBreaks([[0, items.length]]); return; }

    const siblings = Array.from(parent.children);
    const wrapperIdx = siblings.indexOf(measureRef.current);
    const pinnedEl = wrapperIdx > 0 ? siblings[wrapperIdx - 1] : null;

    const parentStyles = getComputedStyle(parent);
    const tmp = document.createElement("div");
    tmp.style.cssText = [
      "position:fixed", "top:-9999px", "left:0",
      `width:${parent.getBoundingClientRect().width}px`,
      "display:flex", "flex-wrap:wrap",
      `gap:${parentStyles.gap}`,
      "align-items:center",
      "visibility:hidden", "pointer-events:none",
    ].join(";");
    document.body.appendChild(tmp);

    const breaks = [];
    let pageStart = 0;

    while (pageStart < chipEls.length) {
      tmp.innerHTML = "";
      if (pinnedEl) tmp.appendChild(pinnedEl.cloneNode(true));
      for (let i = pageStart; i < chipEls.length; i++) {
        tmp.appendChild(chipEls[i].cloneNode(true));
      }

      const clones = Array.from(tmp.children).slice(pinnedEl ? 1 : 0);
      let rowCount = 0, lastTop = null, pageEnd = chipEls.length;

      for (let i = 0; i < clones.length; i++) {
        const top = clones[i].getBoundingClientRect().top;
        if (lastTop === null || Math.abs(top - lastTop) > 4) { rowCount++; lastTop = top; }
        if (rowCount > maxRows) { pageEnd = pageStart + i; break; }
      }

      if (pageEnd <= pageStart) pageEnd = Math.min(pageStart + 1, chipEls.length);
      breaks.push([pageStart, pageEnd]);
      pageStart = pageEnd;
    }

    document.body.removeChild(tmp);
    setPageBreaks(breaks.length ? breaks : [[0, items.length]]);
  });

  if (pageBreaks === null) {
    return (
      <div ref={measureRef} style={{ display: "contents" }}>
        {items.map(renderItem)}
      </div>
    );
  }

  const totalPages = pageBreaks.length;
  const safePage = Math.min(page, totalPages - 1);
  const [start, end] = pageBreaks[safePage];

  return (
    <>
      {items.slice(start, end).map(renderItem)}
      {totalPages > 1 && (
        <div style={{ width: "100%", display: "flex", justifyContent: "center", alignItems: "center", gap: "8px", marginTop: "4px" }}>
          <button
            type="button"
            className="clear-btn"
            onClick={() => setPage(p => p - 1)}
            disabled={safePage === 0}
            style={safePage === 0 ? { opacity: 0.35, cursor: "default" } : undefined}
          >← Prev</button>
          <span style={{ fontSize: ".78rem", color: "var(--muted)", fontWeight: 600, whiteSpace: "nowrap" }}>
            Page {safePage + 1} / {totalPages}
          </span>
          <button
            type="button"
            className="clear-btn"
            onClick={() => setPage(p => p + 1)}
            disabled={safePage === totalPages - 1}
            style={safePage === totalPages - 1 ? { opacity: 0.35, cursor: "default" } : undefined}
          >Next →</button>
        </div>
      )}
    </>
  );
}
