import Icon from "./Icon";

export default function ComingSoon({ title, num }) {
  return (
    <section>
      <div className="mb-8">
        {num && <span className="eyebrow block mb-2.5">Section {num} / {title}</span>}
        <h1 className="text-[2.3rem] font-extrabold tracking-tight mb-1">{title}</h1>
        <p className="text-muted text-[1.05rem] font-serif italic">Coming soon.</p>
      </div>
      <div className="setup-card">
        <h2 className="text-[1.4rem] mb-2 flex items-center justify-center gap-2">
          <Icon name="hard-hat" /> Under construction
        </h2>
        <p className="text-muted text-[.92rem]">This section is being built — check back soon.</p>
      </div>
    </section>
  );
}
