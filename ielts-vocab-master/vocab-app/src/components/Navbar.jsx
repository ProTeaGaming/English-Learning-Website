const TABS = [
  { id: "list", label: "Word List" },
  { id: "examples", label: "Examples" },
  { id: "quiz", label: "Quiz" },
  { id: "gap", label: "Fill the Gap" },
  { id: "challenge", label: "Challenge" },
];

export default function Navbar({ page, setPage, learnedCount, total }) {
  return (
    <header className="sticky top-0 z-10 bg-bg/90 backdrop-blur border-b border-line">
      <div className="max-w-[1100px] mx-auto px-5 py-4 flex items-center justify-between gap-4 flex-wrap">
        <div className="font-sora font-extrabold text-lg flex items-center gap-2">
          <span>📚</span> IELTS Vocab Master
        </div>
        <nav className="flex gap-1.5 flex-wrap">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={"tab" + (page === tab.id ? " active" : "")}
              onClick={() => setPage(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="text-[.85rem] text-muted font-semibold">
          Learned: {learnedCount}/{total}
        </div>
      </div>
    </header>
  );
}
