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
        {page === "test" && <Test learned={learned} />}
        {page === "grammar" && <ComingSoon title="Grammar" />}
        {page === "reading" && <ComingSoon title="Reading" />}
        {page === "writing" && <ComingSoon title="Writing" />}
      </main>
    </div>
  );
}
