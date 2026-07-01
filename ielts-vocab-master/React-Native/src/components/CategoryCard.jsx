import { cefrColor } from "../utils/cefr";

export default function CategoryCard({ cat, wordCount, learnedCount, cefrCount, cefrLabel, onClick }) {
  const pct = wordCount > 0 ? (learnedCount / wordCount) * 100 : 0;

  return (
    <div
      className={`cat-card t-${cat.theme}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
    >
      <div className="cat-card-row">
        <div className="cat-icon-box">{cat.icon}</div>
        <div className="cat-info">
          <div className="cat-name">{cat.name}</div>
          <div className="cat-stats-row">
            <span className="cat-wcount">{wordCount} words</span>
            {cefrCount != null && cefrCount > 0 && (
              <span
                className="cat-cefr-pill"
                style={{ background: cefrColor(cefrLabel) }}
              >
                {cefrCount} {cefrLabel}
              </span>
            )}
          </div>
        </div>
        <div className="cat-chevron">›</div>
      </div>
      <div className="cat-pbar-row">
        <div className="cat-pbar">
          <div className="cat-pfill" style={{ width: `${pct}%` }} />
        </div>
        <span className="cat-plabel">{learnedCount} / {wordCount}</span>
      </div>
    </div>
  );
}
