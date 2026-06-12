import { Link } from 'react-router-dom'
import { Crown } from 'lucide-react'
import { characters } from '../../data/characters'
import { PageHeader, CharacterRelations, protagonistSlugs } from './shared'

export default function Protagonists() {
  return (
    <div>
      <PageHeader
        eyebrow="Two Fates, One Cosmos"
        title="Protagonists"
        description="The Wayfinder crew's two leads — neither has fallen, and the cosmos isn't finished with either of them yet."
      />

      <div className="space-y-10">
        {protagonistSlugs.map((slug) => {
          const c = characters[slug]
          return (
            <article key={slug} className="glass rounded-3xl p-6 sm:p-8">
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-accent/15 border border-accent/30 px-3 py-1 text-xs font-mono uppercase tracking-[0.2em] text-accent">
                  <Crown className="h-3.5 w-3.5" /> {c.label}
                </span>
                <span className="text-xs font-mono uppercase tracking-[0.2em] text-muted">
                  Introduced · {c.introduced}
                </span>
              </div>

              <Link to={`/characters/profile/${c.slug}`} className="inline-block group">
                <h2 className="font-display font-extrabold text-3xl sm:text-4xl tracking-tight mb-1 group-hover:text-primary-light transition">
                  {c.name}
                </h2>
              </Link>
              <p className="font-mono text-sm text-muted mb-6">{c.title}</p>

              <p className="text-muted leading-relaxed mb-8 max-w-3xl">{c.bio}</p>

              <CharacterRelations character={c} />
            </article>
          )
        })}
      </div>
    </div>
  )
}
