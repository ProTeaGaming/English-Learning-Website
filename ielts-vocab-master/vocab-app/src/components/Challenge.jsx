import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA } from "../data/vocab-data";
import { CHALLENGE_COUNTS, shuffle, buildHybridQuestion } from "../utils/quiz";
import { DEFAULT_TOPIC_FILTERS, matchesFilters } from "../utils/filters";
import TopicCefrFilter from "./TopicCefrFilter";
import GapSentence from "./GapSentence";

function resultMessage(pct) {
  if (pct === 100) return "Perfect score! You're ready for anything the exam throws at you.";
  if (pct >= 80) return "Excellent — a strong, well-rounded command of these words.";
  if (pct >= 60) return "Good effort — a bit more practice across modes and you'll nail it.";
  return "Keep practising — try the Word List and Quiz pages to build confidence.";
}

export default function Challenge({ learned }) {
  const [count, setCount] = useState(20);
  const [filters, setFilters] = useState(DEFAULT_TOPIC_FILTERS);
  const [stage, setStage] = useState("setup");
  const [questions, setQuestions] = useState([]);
  const [idx, setIdx] = useState(0);
  const [score, setScore] = useState(0);
  const [answer, setAnswer] = useState(null);
  const cardRef = useRef(null);
  const scoreRef = useRef(null);

  const pool = useMemo(
    () => VOCAB_DATA.filter((w) => matchesFilters(w, filters, learned)),
    [filters, learned]
  );

  const start = () => {
    if (!pool.length) return;
    const n = count === "all" ? pool.length : Math.min(count, pool.length);
    const qs = shuffle(pool).slice(0, n).map(buildHybridQuestion);
    setQuestions(qs);
    setIdx(0);
    setScore(0);
    setAnswer(null);
    setStage("play");
  };

  const handleAnswer = (opt) => {
    if (answer !== null) return;
    setAnswer(opt);
    if (opt === questions[idx].correct) setScore((s) => s + 1);
  };

  const next = () => {
    if (idx + 1 < questions.length) {
      setIdx((i) => i + 1);
      setAnswer(null);
    } else {
      setStage("result");
    }
  };

  useEffect(() => {
    if (stage === "play" && cardRef.current) {
      gsap.fromTo(cardRef.current, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out" });
    }
  }, [idx, stage]);

  useEffect(() => {
    if (stage === "result" && scoreRef.current) {
      gsap.to({ val: 0 }, {
        val: score,
        duration: 1,
        ease: "power1.out",
        onUpdate() {
          scoreRef.current.textContent = Math.round(this.targets()[0].val);
        },
      });
    }
  }, [stage, score]);

  if (stage === "setup") {
    return (
      <section>
        <PageHead title="Challenge" desc="The jack-of-all-trades test: definitions, synonyms, antonyms, word recall and fill-the-gap, all mixed into one round." />
        <div className="setup-card">
          <h2 className="text-[1.4rem] mb-2">Ready for the Challenge?</h2>
          <p className="text-muted text-[.92rem] mb-6">Every question can be any type — choose your topic, level and length, then go.</p>
          <div className="count-row">
            {CHALLENGE_COUNTS.map((c) => (
              <button
                key={c}
                className={"chip" + (count === c ? " active" : "")}
                onClick={() => setCount(c)}
              >
                {c === "all" ? "All words" : `${c} questions`}
              </button>
            ))}
          </div>
          <TopicCefrFilter
            filters={filters}
            setFilters={setFilters}
            resultLabel={`${pool.length} word${pool.length !== 1 ? "s" : ""} match`}
          />
          {pool.length === 0 ? (
            <p className="text-c2 text-[.85rem] mb-4">No words match these filters — try widening your selection.</p>
          ) : null}
          <button className="btn" onClick={start} disabled={!pool.length}>Start Challenge</button>
        </div>
      </section>
    );
  }

  if (stage === "play") {
    const q = questions[idx];
    const isGap = q.type === "gap";
    const fullEx = q.word.ex.replace(/<\/?em>/g, "");
    return (
      <section>
        <PageHead title="Challenge" desc="The jack-of-all-trades test: definitions, synonyms, antonyms, word recall and fill-the-gap, all mixed into one round." />
        <div className="quiz-wrap">
          <div className="progress-bar"><div className="progress-fill" style={{ width: `${(idx / questions.length) * 100}%` }} /></div>
          <div className="flex justify-between text-[.85rem] text-muted mb-3.5 font-semibold">
            <span>Question {idx + 1} of {questions.length}</span>
            <span>Score: {score}</span>
          </div>
          <div className="q-card" ref={cardRef}>
            <div className="text-[.85rem] text-muted uppercase tracking-wider font-bold mb-2.5">
              {isGap ? "Choose the word that correctly completes the sentence" : q.prompt}
            </div>
            <div className="text-[1.25rem] font-bold font-sora mb-6 leading-relaxed">
              {isGap ? <GapSentence gap={q.gap} /> : q.text}
            </div>
            <div className="flex flex-col gap-2.5">
              {q.options.map((opt) => {
                let cls = "q-opt";
                if (answer !== null) {
                  if (opt === q.correct) cls += " correct";
                  else if (opt === answer) cls += " wrong";
                }
                return (
                  <button key={opt} className={cls} disabled={answer !== null} onClick={() => handleAnswer(opt)}>
                    {opt}
                  </button>
                );
              })}
            </div>
            {answer !== null && (
              <>
                <div className="mt-4 text-[.88rem] text-muted">
                  {isGap ? (
                    <>
                      <b className="text-ink">{answer === q.correct ? "Correct!" : `Not quite. The answer is "${q.correct}"`}</b>{" "}
                      — {q.word.def}
                      <br />
                      {fullEx}
                    </>
                  ) : (
                    <>
                      <b className="text-ink">{answer === q.correct ? "Correct!" : "Not quite."}</b>{" "}
                      {q.word.w} — {q.word.def}
                    </>
                  )}
                </div>
                <div className="flex justify-end mt-4">
                  <button className="btn" onClick={next}>
                    {idx + 1 === questions.length ? "See Results" : "Next Question"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>
    );
  }

  const pct = Math.round((score / questions.length) * 100);
  return (
    <section>
      <PageHead title="Challenge" desc="The jack-of-all-trades test: definitions, synonyms, antonyms, word recall and fill-the-gap, all mixed into one round." />
      <div className="result-card">
        <h2 className="text-[1.3rem] text-muted mb-2">Challenge Complete</h2>
        <div className="result-score" ref={scoreRef}>0</div>
        <div className="text-muted mb-7 text-[.95rem]">
          You scored {score} out of {questions.length} ({pct}%). {resultMessage(pct)}
        </div>
        <div className="flex gap-2.5 justify-center flex-wrap">
          <button className="btn" onClick={start}>Try Again</button>
          <button className="btn secondary" onClick={() => setStage("setup")}>Change Setup</button>
        </div>
      </div>
    </section>
  );
}

function PageHead({ title, desc }) {
  return (
    <div className="mb-5">
      <h1 className="text-[1.7rem] font-extrabold mb-1">{title}</h1>
      <p className="text-muted text-[.95rem]">{desc}</p>
    </div>
  );
}
