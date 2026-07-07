import { cefrColor } from "../utils/cefr";
import Icon from "./Icon";
import { iconForEmoji } from "../utils/iconMap";

export default function CategoryCard({ cat, wordCount, learnedCount, cefrCount, cefrLabel, onClick }) {
  const pct = wordCount > 0 ? (learnedCount / wordCount) * 100 : 0;
  const mastered = wordCount > 0 && learnedCount === wordCount;

  return (
    <div
      className={`cat-card t-${cat.theme}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
    >
      <div className="cat-card-top">
        <span className="cat-tag">
          <Icon name={iconForEmoji(cat.icon)} />
          {cefrCount != null && cefrCount > 0 ? `${cefrCount} ${cefrLabel}` : `${wordCount} words`}
        </span>
        {cefrLabel && (
          <span
            className="cat-cefr-pill"
            style={{
              background: `${cefrColor(cefrLabel)}1c`,
              border: `1px solid ${cefrColor(cefrLabel)}55`,
              color: cefrColor(cefrLabel),
            }}
          >
            {cefrLabel}
          </span>
        )}
        <Icon name="arrow-up-right" className="cat-arrow" />
      </div>
      <div className="cat-name">{cat.name}</div>
      <div className="cat-pbar-row">
        <div className="cat-pbar">
          <div
            className="cat-pfill"
            style={{ width: `${pct}%`, ...(mastered ? { background: "#10b981" } : {}) }}
          />
        </div>
        {mastered ? (
          <Icon name="medal" className="cat-medal" aria-label="Mastered" />
        ) : (
          <span className="cat-plabel">{learnedCount} / {wordCount}</span>
        )}
      </div>
    </div>
  );
}
