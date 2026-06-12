import { useState } from "react";
import { CAT_MAP } from "../data/vocab-data";

export default function WordCard({ word, learned, onToggleLearned }) {
  const cat = CAT_MAP[word.cat];
  const [revealed, setRevealed] = useState(false);

  return (
    <div
      className={`word-card t-${cat.theme}` + (learned ? " learned" : "") + (revealed ? " revealed" : "")}
      onClick={() => setRevealed((r) => !r)}
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
        <label className="learn-row" onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={learned}
            onChange={(e) => onToggleLearned(word.w, e.target.checked)}
          />
          Mark as learned
        </label>
      </div>
    </div>
  );
}
