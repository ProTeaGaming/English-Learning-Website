import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA, CATEGORIES, SECTION_ORDER, CAT_MAP } from "../data/vocab-data";
import {
  TEST_MODE_ORDER,
  TEST_MODE_META,
  TEST_COUNTS,
  QUIZ_MODES,
  GAP_MODES,
  GAP_POOL,
  shuffle,
  buildQuestion,
  buildGapQuestion,
  buildHybridQuestion,
  randomMixedMode,
} from "../utils/quiz";
import { DEFAULT_TOPIC_FILTERS, matchesFilters } from "../utils/filters";
import { cefrColor } from "../utils/cefr";
import TopicCefrFilter from "./TopicCefrFilter";
import GapSentence from "./GapSentence";

const WORD_PICKER_PER_PAGE = 25;

const WORD_HEADLINES = [
  ["all", "All"],
  ["basic", "🌱 Basic"],
  ["intermediate", "📈 Intermediate"],
  ["advanced", "🎓 Advanced"],
];

const WORD_CEFR_LEVELS = ["A1","A1+","A2","A2+","B1","B1+","B2","B2+","C1","C1+","C2","C2+"];
const WORD_CEFR_COLOR = {
  "A1":"#10b981","A1+":"#eab308","A2":"#06b6d4","A2+":"#f97316",
  "B1":"#6366f1","B1+":"#ec4899","B2":"#3b82f6","B2+":"#1e40af",
  "C1":"#f59e0b","C1+":"#f43f5e","C2":"#ef4444","C2+":"#a855f7",
};

function wordHeadlineMatch(cefr, hl) {
  if (hl === "all") return true;
  if (hl === "basic") return ["A1","A1+","A2","A2+"].includes(cefr);
  if (hl === "intermediate") return ["B1","B1+","B2"].includes(cefr);
  if (hl === "advanced") return ["C1","C1+","C2","C2+"].includes(cefr);
  return true;
}

function pageWindows(cur, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [1];
  const lo = Math.max(2, cur - 2);
  const hi = Math.min(total - 1, cur + 2);
  if (lo > 2) pages.push("...");
  for (let i = lo; i <= hi; i++) pages.push(i);
  if (hi < total - 1) pages.push("...");
  pages.push(total);
  return pages;
}

export default function Test({ learnMap }) {
  const [testMode, setTestMode] = useState("quiz");
  const [quizMode, setQuizMode] = useState("definition");
  const [gapMode, setGapMode] = useState("context");
  const [count, setCount] = useState(10);
  const [filters, setFilters] = useState(DEFAULT_TOPIC_FILTERS);
  const [stage, setStage] = useState("setup");
  const [questions, setQuestions] = useState([]);
  const [idx, setIdx] = useState(0);
  const [score, setScore] = useState(0);
  const [answer, setAnswer] = useState(null);
  const [sourceMode, setSourceMode] = useState("category");
  const [selectedWords, setSelectedWords] = useState(new Set());
  const [wordSearch, setWordSearch] = useState("");
  const [wordPage, setWordPage] = useState(1);
  const [wordHeadline, setWordHeadline] = useState("all");
  const [wordCefr, setWordCefr] = useState("all");
  const [wordSection, setWordSection] = useState("all");
  const [wordCat, setWordCat] = useState("all");
  const [wordLearned, setWordLearned] = useState("all");
  const cardRef = useRef(null);
  const scoreRef = useRef(null);

  const meta = TEST_MODE_META[testMode];

  const pickerWords = useMemo(() => {
    const q = wordSearch.toLowerCase().trim();
    return VOCAB_DATA.filter(w => {
      if (!wordHeadlineMatch(w.cefr, wordHeadline)) return false;
      if (wordCefr !== "all" && w.cefr !== wordCefr) return false;
      const cat = CAT_MAP[w.cat];
      if (wordSection !== "all" && (!cat || cat.section !== wordSection)) return false;
      if (wordCat !== "all" && w.cat !== wordCat) return false;
      const ws = learnMap?.get ? (learnMap.get(w.w) || null) : null;
      if (wordLearned === "learned" && ws !== "learned") return false;
      if (wordLearned === "unlearned" && ws !== null) return false;
      if (!q) return true;
      const hay = [w.w, w.def, ...(w.syn || []), ...(w.ant || [])].join(" ").toLowerCase();
      return hay.includes(q);
    });
  }, [wordSearch, wordHeadline, wordCefr, wordSection, wordCat, wordLearned, learnMap]);

  const pickerTotalPages = Math.max(1, Math.ceil(pickerWords.length / WORD_PICKER_PER_PAGE));
  const safeWordPage = Math.min(wordPage, pickerTotalPages);
  const pagePickerWords = pickerWords.slice((safeWordPage - 1) * WORD_PICKER_PER_PAGE, safeWordPage * WORD_PICKER_PER_PAGE);

  const pool = useMemo(() => {
    if (sourceMode === "words") {
      let p = VOCAB_DATA.filter(w => selectedWords.has(w.w));
      if (testMode === "gap") p = p.filter(w => w.gap && w.gap.includes("___"));
      if (testMode === "quiz" && quizMode === "synonym") p = p.filter(w => w.syn?.length);
      if (testMode === "quiz" && quizMode === "antonym") p = p.filter(w => w.ant?.length);
      return p;
    }
    if (testMode === "gap") return GAP_POOL.filter(w => matchesFilters(w, filters, learnMap));
    let p = VOCAB_DATA.filter(w => matchesFilters(w, filters, learnMap));
    if (testMode === "quiz") {
      if (quizMode === "synonym") p = p.filter(w => w.syn?.length);
      if (quizMode === "antonym") p = p.filter(w => w.ant?.length);
    }
    return p;
  }, [filters, testMode, quizMode, learnMap, sourceMode, selectedWords]);

  const toggleWord = (w) => {
    setSelectedWords(prev => {
      const next = new Set(prev);
      if (next.has(w.w)) next.delete(w.w);
      else next.add(w.w);
      return next;
    });
  };

  const selectAllResults = () => {
    setSelectedWords(prev => {
      const next = new Set(prev);
      pickerWords.forEach(w => next.add(w.w));
      return next;
    });
  };

  const cycleMode = (dir) => {
    const i = TEST_MODE_ORDER.indexOf(testMode);
    setTestMode(TEST_MODE_ORDER[(i + dir + TEST_MODE_ORDER.length) % TEST_MODE_ORDER.length]);
  };

  const buildTestQuestion = (word) => {
    if (testMode === "gap") return { type: "gap", ...buildGapQuestion(word, gapMode) };
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
    if (opt === questions[idx].correct) setScore(s => s + 1);
  };

  const next = () => {
    if (idx + 1 < questions.length) {
      setIdx(i => i + 1);
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
          if (scoreRef.current) scoreRef.current.textContent = Math.round(this.targets()[0].val);
        },
      });
      return () => tween.kill();
    }
  }, [stage, score]);

  if (stage === "setup") {
    const noMatchMsg = sourceMode === "words"
      ? selectedWords.size === 0
        ? "No words selected — pick some words above to start."
        : `None of your selected words work for ${testMode} mode — try a different mode or select more words.`
      : `No ${meta.poolUnit}s match these filters — try widening your selection.`;

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
              {QUIZ_MODES.map(m => (
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
          {testMode === "gap" && (
            <div className="option-grid">
              {GAP_MODES.map(m => (
                <div
                  key={m.id}
                  className={"mode-card" + (gapMode === m.id ? " active" : "")}
                  onClick={() => setGapMode(m.id)}
                >
                  <h3 className="text-[.95rem] mb-1 font-sora">{m.name}</h3>
                  <p className="text-[.78rem] text-muted leading-snug">{m.desc}</p>
                </div>
              ))}
            </div>
          )}
          <div className="count-row mb-0">
            {TEST_COUNTS.map(c => (
              <button key={c} className={"chip" + (count === c ? " active" : "")} onClick={() => setCount(c)}>
                {meta.countLabel(c)}
              </button>
            ))}
          </div>
        </div>

        <div className="max-w-[680px] mx-auto">
          {/* Source toggle */}
          <div className="browse-bar mb-4">
            <div className="flex gap-2 items-center">
              <span className="filter-label">Source</span>
              <button
                className={"chip" + (sourceMode === "category" ? " active" : "")}
                onClick={() => setSourceMode("category")}
              >By Category</button>
              <button
                className={"chip" + (sourceMode === "words" ? " active" : "")}
                onClick={() => setSourceMode("words")}
              >By Words</button>
            </div>
          </div>

          {sourceMode === "category" ? (
            <TopicCefrFilter
              filters={filters}
              setFilters={setFilters}
              resultLabel={`${pool.length} ${meta.poolUnit}${pool.length !== 1 ? "s" : ""} match`}
            />
          ) : (
            <>
              <div className="headline-bar">
                {WORD_HEADLINES.map(([hl, label]) => {
                  const isActive = wordHeadline === hl;
                  const hlColors = {
                    basic:        { background: "#06b6d4", borderColor: "#06b6d4", color: "#064e3b" },
                    intermediate: { background: "#3b82f6", borderColor: "#3b82f6", color: "#fff" },
                    advanced:     { background: "#f59e0b", borderColor: "#f59e0b", color: "#1c1917" },
                  };
                  return (
                    <button
                      key={hl}
                      className={"headline-btn" + (isActive ? " active" : "")}
                      style={isActive && hlColors[hl] ? hlColors[hl] : undefined}
                      onClick={() => { setWordHeadline(hl); setWordPage(1); }}
                    >{label}</button>
                  );
                })}
              </div>
              <div className="browse-bar">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <span className="filter-label">Select Words</span>
                  <span className="text-[.85rem] text-muted">
                    {selectedWords.size} selected · {pool.length} {meta.poolUnit}{pool.length !== 1 ? "s" : ""} match
                  </span>
                </div>
                <div className="relative">
                  <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[.85rem] opacity-50">🔍</span>
                  <input
                    type="search"
                    value={wordSearch}
                    onChange={e => { setWordSearch(e.target.value); setWordPage(1); }}
                    placeholder="Search words, definitions, synonyms…"
                    className="w-full appearance-none bg-surface2 border border-line text-ink pl-10 pr-4 py-2.5 rounded-xl text-[.95rem] focus:outline-none focus:border-accent [&::-webkit-search-decoration]:appearance-none [&::-webkit-search-cancel-button]:appearance-none"
                  />
                </div>
                <div className="flex gap-2 flex-wrap items-center">
                  <span className="filter-label">Section</span>
                  <button
                    className={"chip" + (wordSection === "all" ? " active" : "")}
                    onClick={() => { setWordSection("all"); setWordCat("all"); setWordPage(1); }}
                  >All Sections</button>
                  {SECTION_ORDER.map(sec => (
                    <button
                      key={sec}
                      className={"chip" + (wordSection === sec ? " active" : "")}
                      onClick={() => { setWordSection(sec); setWordCat("all"); setWordPage(1); }}
                    >{sec}</button>
                  ))}
                </div>
                <div className="flex gap-2 flex-wrap items-center">
                  <span className="filter-label">Category</span>
                  <button
                    className={"chip" + (wordCat === "all" ? " active" : "")}
                    onClick={() => { setWordCat("all"); setWordPage(1); }}
                  >All</button>
                  {(wordSection === "all" ? CATEGORIES : CATEGORIES.filter(c => c.section === wordSection)).map(c => (
                    <button
                      key={c.id}
                      className={`chip t-${c.theme}` + (wordCat === c.id ? " active" : "")}
                      onClick={() => { setWordCat(c.id); setWordPage(1); }}
                    >{c.icon} {c.name}</button>
                  ))}
                </div>
                <div className="flex gap-2 flex-wrap items-center">
                  <span className="filter-label">CEFR Level</span>
                  <button
                    className={"chip" + (wordCefr === "all" ? " active" : "")}
                    onClick={() => { setWordCefr("all"); setWordPage(1); }}
                  >All</button>
                  {WORD_CEFR_LEVELS.map(lvl => (
                    <button
                      key={lvl}
                      className={"chip" + (wordCefr === lvl ? " active" : "")}
                      style={wordCefr === lvl ? { background: WORD_CEFR_COLOR[lvl], color: "#fff", borderColor: "transparent" } : undefined}
                      onClick={() => { setWordCefr(lvl); setWordPage(1); }}
                    >{lvl}</button>
                  ))}
                </div>
                <div className="flex gap-2 flex-wrap items-center">
                  <span className="filter-label">Progress</span>
                  <button
                    className={"chip" + (wordLearned === "all" ? " active" : "")}
                    onClick={() => { setWordLearned("all"); setWordPage(1); }}
                  >All</button>
                  <button
                    className={"chip" + (wordLearned === "learned" ? " active" : "")}
                    onClick={() => { setWordLearned("learned"); setWordPage(1); }}
                  >Learned</button>
                  <button
                    className={"chip" + (wordLearned === "unlearned" ? " active" : "")}
                    onClick={() => { setWordLearned("unlearned"); setWordPage(1); }}
                  >Not Learned</button>
                </div>
                <div className="flex gap-2 flex-wrap items-center">
                  <button className="chip" onClick={selectAllResults}>Select all results</button>
                  {selectedWords.size > 0 && (
                    <button className="clear-btn" onClick={() => setSelectedWords(new Set())}>Clear selection</button>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {pagePickerWords.map(w => {
                    const sel = selectedWords.has(w.w);
                    const color = cefrColor(w.cefr);
                    return (
                      <button
                        key={w.w}
                        className={"chip" + (sel ? " active" : "")}
                        onClick={() => toggleWord(w)}
                      >
                        {w.w}
                        <span
                          className="inline-block ml-1.5 text-[.65rem] font-bold px-1.5 py-px rounded"
                          style={sel
                            ? { background: "rgba(255,255,255,.25)", color: "#fff" }
                            : { background: color + "22", color }}
                        >{w.cefr}</span>
                      </button>
                    );
                  })}
                </div>
                {pickerTotalPages > 1 && (
                  <div className="pagination" style={{ paddingTop: 0 }}>
                    <button className="page-btn" disabled={safeWordPage === 1} onClick={() => setWordPage(p => p - 1)}>«</button>
                    {pageWindows(safeWordPage, pickerTotalPages).map((p, i) =>
                      p === "..." ? (
                        <span key={`e${i}`} className="page-btn ellipsis">…</span>
                      ) : (
                        <button
                          key={p}
                          className={"page-btn" + (p === safeWordPage ? " active" : "")}
                          onClick={() => setWordPage(p)}
                        >{p}</button>
                      )
                    )}
                    <button className="page-btn" disabled={safeWordPage === pickerTotalPages} onClick={() => setWordPage(p => p + 1)}>»</button>
                  </div>
                )}
              </div>
            </>
          )}

          {pool.length === 0 && (
            <p className="text-c2 text-[.85rem] mb-4">{noMatchMsg}</p>
          )}
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
              {q.prompt}
            </div>
            <div className="text-[1.25rem] font-bold font-sora mb-6 leading-relaxed">
              {isGap ? <GapSentence gap={q.gap} /> : q.text}
            </div>
            <div className="flex flex-col gap-2.5">
              {q.options.map(opt => {
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
