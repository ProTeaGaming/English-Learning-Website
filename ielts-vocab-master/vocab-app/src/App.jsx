import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { VOCAB_DATA } from "./data/vocab-data";
import { useLearned } from "./hooks/useLearned";
import { useTheme } from "./hooks/useTheme";
import Navbar from "./components/Navbar";
import WordList from "./components/WordList";
import Examples from "./components/Examples";
import Quiz from "./components/Quiz";
import FillGap from "./components/FillGap";
import Challenge from "./components/Challenge";

export default function App() {
  const [page, setPage] = useState("list");
  const { learned, toggle } = useLearned();
  const { theme, toggle: toggleTheme } = useTheme();
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
        learnedCount={learned.size}
        total={VOCAB_DATA.length}
        theme={theme}
        toggleTheme={toggleTheme}
      />
      <main className="max-w-[1100px] mx-auto px-5 py-7" ref={pageRef}>
        {page === "list" && <WordList learned={learned} toggleLearned={toggle} />}
        {page === "examples" && <Examples learned={learned} />}
        {page === "quiz" && <Quiz learned={learned} />}
        {page === "gap" && <FillGap learned={learned} />}
        {page === "challenge" && <Challenge learned={learned} />}
      </main>
    </div>
  );
}
