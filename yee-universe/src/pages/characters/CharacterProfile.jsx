import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Crown, Calendar, Skull } from 'lucide-react'
import { characters } from '../../data/characters'
import { CharacterRelations, DeceasedMark } from './shared'

export default function CharacterProfile() {
  const { slug } = useParams()
  const c = characters[slug]

  if (!c) {
    return (
      <div className="max-w-2xl">
        <h1 className="font-display font-extrabold text-4xl tracking-tight mb-4">Character Not Found</h1>
        <p className="text-muted mb-8">No record of this individual exists in the Yee Universe archives.</p>
        <Link to="/characters" className="inline-flex items-center gap-2 text-sm font-medium text-primary-light hover:text-primary transition">
          <ArrowLeft className="h-4 w-4" /> Back to Characters
        </Link>
      </div>
    )
  }

  const isProtagonist = c.label === 'Protagonist'
  const backTo = isProtagonist ? '/characters/protagonists' : '/characters/side-characters'
  const backLabel = isProtagonist ? 'Back to Protagonists' : 'Back to Side Characters'

  return (
    <div>
      <Link to={backTo} className="inline-flex items-center gap-2 text-sm text-muted hover:text-primary transition lift-on-hover mb-10">
        <ArrowLeft className="h-4 w-4" /> {backLabel}
      </Link>

      <div className="glass rounded-3xl p-6 sm:p-10">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {isProtagonist && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-accent/15 border border-accent/30 px-3 py-1 text-xs font-mono uppercase tracking-[0.2em] text-accent">
              <Crown className="h-3.5 w-3.5" /> {c.label}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-[0.2em] text-muted">
            <Calendar className="h-3.5 w-3.5" /> Introduced · {c.introduced}
          </span>
          {c.status === 'deceased' && (
            <span className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-[0.2em] text-red-400">
              <Skull className="h-3.5 w-3.5" /> Died · {c.died}
            </span>
          )}
        </div>

        <h1 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight mb-2 inline-flex items-center gap-3">
          {c.name}
          {c.status === 'deceased' && <DeceasedMark className="text-3xl" />}
        </h1>
        <p className="font-mono text-sm text-muted mb-8">{c.title}</p>

        <p className="text-muted leading-relaxed mb-10 max-w-3xl text-[15px]">{c.bio}</p>

        <CharacterRelations character={c} />
      </div>
    </div>
  )
}
