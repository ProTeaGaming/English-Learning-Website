import { CAT_MAP } from "../data/vocab-data";

export default function WordCard({ word, learnState, openModal, onCycle }) {
  const cat = CAT_MAP[word.cat];
  const isLearned = learnState === "learned";
  const isLittle = learnState === "little";
  const stateLabel = isLearned ? "Learned" : isLittle ? "Little Bit" : "Not Learned";

  return (
    <div
      className={`word-card t-${cat.theme}` + (isLearned ? " learned" : isLittle ? " little" : "")}
      onClick={() => openModal(word)}
    >
      <div className="flex justify-between items-start gap-2">
        <div>
          <div className="word text-[1.15rem] font-bold font-sora">{word.w}</div>
          <div className="text-[.75rem] text-muted mt-0.5 italic">{word.pos}</div>
        </div>
        <span className={`cefr-badge ${word.cefr}`}>{word.cefr}</span>
      </div>

      <div className="reveal">
        <div className="rdef">{word.def}</div>
        {word.syn?.length > 0 && (
          <div className="rrow"><b>Synonyms:</b> {word.syn.join(", ")}</div>
        )}
        {word.ant?.length > 0 && (
          <div className="rrow"><b>Antonyms:</b> {word.ant.join(", ")}</div>
        )}
        <div className="rex" dangerouslySetInnerHTML={{ __html: word.ex }} />
        <div className="learn-state-row" onClick={(e) => e.stopPropagation()}>
          <span className="learn-state-label">Progress:</span>
          <button
            className="learn-state-btn"
            data-state={learnState || "none"}
            onClick={() => onCycle(word.w)}
          >
            {stateLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
