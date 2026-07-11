import { useEffect } from "react";
import { CAT_MAP } from "../data/vocab-data";

const CEFR_THEME = { B1: "te", B2: "tb", C1: "ta", C2: "tr", "C2+": "tpurp" };

export default function WordModal({ word, onClose, learnMap, onCycle }) {
  useEffect(() => {
    if (!word) return;
    document.body.style.overflow = "hidden";
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [word, onClose]);

  if (!word) return null;

  const cat = CAT_MAP[word.cat];
  const ws = learnMap.get(word.w) || null;
  const stateLabel = ws === "learned" ? "Learned" : ws === "little" ? "Little Bit" : "Not Learned";

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className={`modal-card t-${CEFR_THEME[word.cefr] || "tb"}`}>
        <div className="modal-header">
          <div>
            <div className="modal-word">{word.w}</div>
            <div className="modal-pos">{word.pos}</div>
          </div>
          <span className={`cefr-badge ${word.cefr}`}>{word.cefr}</span>
        </div>
        <div className="modal-body">
          <div className="modal-def">{word.def}</div>
          {word.syn?.length > 0 && (
            <div className="modal-row"><b>Synonyms:</b> {word.syn.join(", ")}</div>
          )}
          {word.ant?.length > 0 && (
            <div className="modal-row"><b>Antonyms:</b> {word.ant.join(", ")}</div>
          )}
          <div className="modal-ex" dangerouslySetInnerHTML={{ __html: word.ex }} />
          {cat && <div className="modal-cat"><b>Category:</b> {cat.name}</div>}
          <div className="learn-state-row">
            <span className="learn-state-label">Progress:</span>
            <button
              className="learn-state-btn"
              data-state={ws || "none"}
              onClick={() => onCycle(word.w)}
            >
              {stateLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
