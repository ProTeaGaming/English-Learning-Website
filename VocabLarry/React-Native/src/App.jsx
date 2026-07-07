import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA } from "./data/vocab-data";
import { useLearned } from "./hooks/useLearned";
import { useTheme } from "./hooks/useTheme";
import Navbar from "./components/Navbar";
import WordList from "./components/WordList";
import Examples from "./components/Examples";
import Test from "./components/Test";
import ComingSoon from "./components/ComingSoon";
import WordModal from "./components/WordModal";

export default function App() {
  const [page, setPage] = useState("list");
  const { learnMap, cycle, learnedCount } = useLearned();
  const { theme, toggle: toggleTheme } = useTheme();
  const [modalWord, setModalWord] = useState(null);
  const pageRef = useRef(null);

  useEffect(() => {
    if (pageRef.current) {
      gsap.fromTo(pageRef.current, { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.3, ease: "power2.out" });
    }
  }, [page]);

  return (
    <div className="min-h-screen">
      <Navbar
        page={page}
        setPage={setPage}
        learnedCount={learnedCount}
        total={VOCAB_DATA.length}
        theme={theme}
        toggleTheme={toggleTheme}
      />
      <main className="max-w-[1100px] mx-auto px-5 py-7" ref={pageRef}>
        {page === "list"     && <WordList learnMap={learnMap} onCycle={cycle} openModal={setModalWord} />}
        {page === "examples" && <Examples learnMap={learnMap} openModal={setModalWord} />}
        {page === "test"     && <Test learnMap={learnMap} />}
        {page === "grammar"   && <ComingSoon title="Grammar" num="02" />}
        {page === "reading"   && <ComingSoon title="Reading" num="03" />}
        {page === "writing"   && <ComingSoon title="Writing" num="04" />}
        {page === "listening" && <ComingSoon title="Listening" num="05" />}
        {page === "speaking"  && <ComingSoon title="Speaking" num="06" />}
      </main>
      <WordModal
        word={modalWord}
        onClose={() => setModalWord(null)}
        learnMap={learnMap}
        onCycle={cycle}
      />
    </div>
  );
}
