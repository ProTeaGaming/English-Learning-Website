import { useEffect, useRef, useState } from "react";

const SECTIONS = [
  {
    id: "vocabulary",
    label: "Vocabulary",
    pages: [
      { id: "list", label: "Word List" },
      { id: "examples", label: "Examples" },
    ],
  },
  {
    id: "reading",
    label: "Reading",
    pages: [
      { id: "quiz", label: "Quiz" },
      { id: "gap", label: "Fill the Gap" },
      { id: "challenge", label: "Challenge" },
    ],
  },
];

export default function Navbar({ page, setPage, learnedCount, total, theme, toggleTheme }) {
  const [openSection, setOpenSection] = useState(null);
  const navRef = useRef(null);

  useEffect(() => {
    function handlePointerDown(e) {
      if (navRef.current && !navRef.current.contains(e.target)) setOpenSection(null);
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  return (
    <header className="sticky top-0 z-10 bg-bg/90 backdrop-blur border-b border-line">
      <div className="max-w-[1100px] mx-auto px-5 py-4 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-6 flex-wrap">
          <div className="font-sora font-extrabold text-lg flex items-center gap-2">
            <span>📚</span> IELTS Vocab Master
          </div>
          <nav className="flex gap-1.5 flex-wrap" ref={navRef}>
            {SECTIONS.map((section) => {
              const isActive = section.pages.some((p) => p.id === page);
              const isOpen = openSection === section.id;
              return (
                <div
                  key={section.id}
                  className="relative"
                  onMouseEnter={() => setOpenSection(section.id)}
                  onMouseLeave={() => setOpenSection((s) => (s === section.id ? null : s))}
                >
                  <button
                    className={"tab" + (isActive ? " active" : "")}
                    onClick={() => {
                      if (isActive) {
                        setOpenSection((s) => (s === section.id ? null : section.id));
                      } else {
                        setPage(section.pages[0].id);
                        setOpenSection(null);
                      }
                    }}
                  >
                    {section.label} <span className="nav-caret">▾</span>
                  </button>
                  {isOpen && (
                    <div className="nav-dropdown">
                      {section.pages.map((p) => (
                        <button
                          key={p.id}
                          className={"nav-dropdown-item" + (page === p.id ? " active" : "")}
                          onClick={() => {
                            setPage(p.id);
                            setOpenSection(null);
                          }}
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3.5">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
          <div className="text-[.85rem] text-muted font-semibold">
            Learned: {learnedCount}/{total}
          </div>
        </div>
      </div>
    </header>
  );
}
