import { Link } from 'react-router-dom'
import { Calendar, Skull, ArrowRight } from 'lucide-react'
import { characters } from '../../data/characters'
import { PageHeader, CharacterRelations, DeceasedMark, sideCharacterSlugs } from './shared'

export default function SideCharacters() {
  return (
    <div>
      <PageHeader
        eyebrow="Allies, Rivals & Everyone Between"
        title="Side Characters"
        description="The crew, the chasers, and the in-between — every relationship marked current or former at a glance."
      />

      <div className="space-y-8">
        {sideCharacterSlugs.map((slug) => {
          const c = characters[slug]
          return (
            <article key={slug} className="glass rounded-3xl p-6 sm:p-8">
              <div className="flex flex-wrap items-center gap-3 mb-4 text-xs font-mono uppercase tracking-[0.2em] text-muted">
                <span className="inline-flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" /> Introduced · {c.introduced}
                </span>
                {c.status === 'deceased' && (
                  <span className="inline-flex items-center gap-1.5 text-red-400">
                    <Skull className="h-3.5 w-3.5" /> Died · {c.died}
                  </span>
                )}
              </div>

              <Link to={`/characters/profile/${c.slug}`} className="inline-block group">
                <h2 className="font-display font-extrabold text-2xl sm:text-3xl tracking-tight mb-1 group-hover:text-primary-light transition inline-flex items-center gap-2">
                  {c.name}
                  {c.status === 'deceased' && <DeceasedMark />}
                </h2>
              </Link>
              <p className="font-mono text-sm text-muted mb-5">{c.title}</p>

              <p className="text-muted leading-relaxed mb-6 max-w-3xl line-clamp-3">{c.bio}</p>

              <Link
                to={`/characters/profile/${c.slug}`}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-light hover:text-primary transition mb-8"
              >
                Read full profile <ArrowRight className="h-3.5 w-3.5" />
              </Link>

              <CharacterRelations character={c} />
            </article>
          )
        })}
      </div>
    </div>
  )
}
