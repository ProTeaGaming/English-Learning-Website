export default function ComingSoon({ title }) {
  return (
    <section>
      <div className="mb-5">
        <h1 className="text-[1.7rem] font-extrabold mb-1">{title}</h1>
        <p className="text-muted text-[.95rem]">Coming soon.</p>
      </div>
      <div className="setup-card">
        <h2 className="text-[1.4rem] mb-2">🚧 Under construction</h2>
        <p className="text-muted text-[.92rem]">This section is being built — check back soon.</p>
      </div>
    </section>
  );
}
