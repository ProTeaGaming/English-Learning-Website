import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA } from "../data/vocab-data";
import {
  TEST_MODE_ORDER,
  TEST_MODE_META,
  TEST_COUNTS,
  QUIZ_MODES,
  GAP_POOL,
  shuffle,
  buildQuestion,
  buildGapQuestion,
  buildHybridQuestion,
  randomMixedMode,
} from "../utils/quiz";
import { DEFAULT_TOPIC_FILTERS, matchesFilters } from "../utils/filters";
import TopicCefrFilter from "./TopicCefrFilter";
import GapSentence from "./GapSentence";

export default function Test({ learnMap }) {
  const [testMode, setTestMode] = useState("quiz");
  const [quizMode, setQuizMode] = useState("definition");
  const [count, setCount] = useState(10);
  const [filters, setFilters] = useState(DEFAULT_TOPIC_FILTERS);
  const [stage, setStage] = useState("setup");
  const [questions, setQuestions] = useState([]);
  const [idx, setIdx] = useState(0);
  const [score, setScore] = useState(0);
  const [answer, setAnswer] = useState(null);
  const cardRef = useRef(null);
  const scoreRef = useRef(null);

  const meta = TEST_MODE_META[testMode];

  const pool = useMemo(() => {
    if (testMode === "gap") {
      return GAP_POOL.filter((w) => matchesFilters(w, filters, learnMap));
    }
    let p = VOCAB_DATA.filter((w) => matchesFilters(w, filters, learnMap));
    if (testMode === "quiz") {
      if (quizMode === "synonym") p = p.filter((w) => w.syn?.length);
      if (quizMode === "antonym") p = p.filter((w) => w.ant?.length);
    }
    return p;
  }, [filters, testMode, quizMode, learned]);

  const cycleMode = (dir) => {
    const i = TEST_MODE_ORDER.indexOf(testMode);
    setTestMode(TEST_MODE_ORDER[(i + dir + TEST_MODE_ORDER.length) % TEST_MODE_ORDER.length]);
  };

  const buildTestQuestion = (word) => {
    if (testMode === "gap") return { type: "gap", ...buildGapQuestion(word) };
    if (testMode === "challenge") return buildHybridQuestion(word);
    const qm = quizMode === "mixed" ? randomMixedMode(word) : quizMode;
    return { type: "quiz", ...buildQuestion(word, qm) };
  };

  const start = () => {
    if (!pool.length) return;
    const n = count === "all" ? pool.length : Math.min(count, pool.length);
    const qs = shuffle(pool).slice(0, n).map(buildTestQuestion);
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
      const tween = gsap.fromTo(cardRef.current, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out" });
      return () => tween.kill();
    }
  }, [idx, stage]);

  useEffect(() => {
    if (stage === "result" && scoreRef.current) {
      const tween = gsap.to({ val: 0 }, {
        val: score,
        duration: 1,
        ease: "power1.out",
        onUpdate() {
          if (scoreRef.current) {
            scoreRef.current.textContent = Math.round(this.targets()[0].val);
          }
        },
      });
      return () => tween.kill();
    }
  }, [stage, score]);

  if (stage === "setup") {
    return (
      <section>
        <PageHead title={meta.pageTitle} desc={meta.pageDesc} />
        <div className="setup-card mb-6">
          <div className="mode-toggle-row">
            <button className="mode-toggle-btn" onClick={() => cycleMode(-1)} aria-label="Previous test mode">‹</button>
            <span className="mode-toggle-label">{meta.toggleLabel}</span>
            <button className="mode-toggle-btn" onClick={() => cycleMode(1)} aria-label="Next test mode">›</button>
          </div>
          <h2 className="text-[1.4rem] mb-2">{meta.setupTitle}</h2>
          <p className="text-muted text-[.92rem] mb-6">{meta.setupSub}</p>
          {testMode === "quiz" && (
            <div className="option-grid">
              {QUIZ_MODES.map((m) => (
                <div
                  key={m.id}
                  className={"mode-card" + (quizMode === m.id ? " active" : "")}
                  onClick={() => setQuizMode(m.id)}
                >
                  <h3 className="text-[.95rem] mb-1 font-sora">{m.name}</h3>
                  <p className="text-[.78rem] text-muted leading-snug">{m.desc}</p>
                </div>
              ))}
            </div>
          )}
          <div className="count-row mb-0">
            {TEST_COUNTS.map((c) => (
              <button
                key={c}
                className={"chip" + (count === c ? " active" : "")}
                onClick={() => setCount(c)}
              >
                {meta.countLabel(c)}
              </button>
            ))}
          </div>
        </div>
        <div className="max-w-[680px] mx-auto">
          <TopicCefrFilter
            filters={filters}
            setFilters={setFilters}
            resultLabel={`${pool.length} ${meta.poolUnit}${pool.length !== 1 ? "s" : ""} match`}
          />
          {pool.length === 0 ? (
            <p className="text-c2 text-[.85rem] mb-4">No {meta.poolUnit}s match these filters — try widening your selection.</p>
          ) : null}
          <button className="btn w-full" onClick={start} disabled={!pool.length}>{meta.startLabel}</button>
        </div>
      </section>
    );
  }

  if (stage === "play") {
    const q = questions[idx];
    const isGap = q.type === "gap";
    const fullEx = isGap ? q.word.ex.replace(/<\/?em>/g, "") : null;
    const noun = testMode === "gap" ? "Sentence" : "Question";
    return (
      <section>
        <PageHead title={meta.pageTitle} desc={meta.pageDesc} />
        <div className="quiz-wrap">
          <div className="progress-bar"><div className="progress-fill" style={{ width: `${((idx + 1) / questions.length) * 100}%` }} /></div>
          <div className="flex justify-between text-[.85rem] text-muted mb-3.5 font-semibold">
            <span>{noun} {idx + 1} of {questions.length}</span>
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
                    {idx + 1 === questions.length ? "See Results" : `Next ${noun}`}
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
      <PageHead title={meta.pageTitle} desc={meta.pageDesc} />
      <div className="result-card">
        <h2 className="text-[1.3rem] text-muted mb-2">{meta.resultTitle}</h2>
        <div className="result-score" ref={scoreRef}>0</div>
        <div className="text-muted mb-7 text-[.95rem]">
          You scored {score} out of {questions.length} ({pct}%). {meta.resultMessage(pct)}
        </div>
        <div className="flex gap-2.5 justify-center flex-wrap">
          <button className="btn" onClick={start}>Try Again</button>
          {meta.secondaryButtonLabel && (
            <button className="btn secondary" onClick={() => setStage("setup")}>{meta.secondaryButtonLabel}</button>
          )}
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
