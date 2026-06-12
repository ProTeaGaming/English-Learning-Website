import { Link } from 'react-router-dom'
import { Crown, Users, UsersRound, ArrowRight } from 'lucide-react'
import { characters, teams } from '../../data/characters'
import { PageHeader, DeceasedMark, protagonistSlugs, sideCharacterSlugs } from './shared'

const sections = [
  {
    to: '/characters/protagonists',
    icon: Crown,
    title: 'Protagonists',
    description: 'The two Wayfinders at the center of it all — their companions, their enemies, and the cosmos caught between them.',
    count: `${protagonistSlugs.length} Protagonists`,
  },
  {
    to: '/characters/side-characters',
    icon: Users,
    title: 'Side Characters',
    description: 'Allies, rivals, and rivals-turned-allies across the Frontier, the Concord, and the Hegemony.',
    count: `${sideCharacterSlugs.length} Characters`,
  },
  {
    to: '/characters/teams',
    icon: UsersRound,
    title: 'Teams',
    description: 'Crews, divisions, and cadres — active, disbanded, and everything that came before.',
    count: `${Object.keys(teams).length} Teams`,
  },
]

export default function Characters() {
  return (
    <div>
      <PageHeader
        eyebrow="The Cast of Yee Universe"
        title="Characters"
        description="Every Wayfinder, ally, and adversary across the Threshold conflict — browse by role, or jump straight to a character's profile."
      />

      <div className="grid sm:grid-cols-3 gap-5 mb-16">
        {sections.map((s) => (
          <Link
            key={s.to}
            to={s.to}
            className="group glass rounded-3xl p-6 flex flex-col gap-4 transition lift-on-hover hover:border-primary/40"
          >
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/15 text-primary-light">
              <s.icon className="h-5 w-5" />
            </span>
            <div>
              <h2 className="font-display font-bold text-xl mb-1.5">{s.title}</h2>
              <p className="text-sm text-muted leading-relaxed">{s.description}</p>
            </div>
            <div className="mt-auto flex items-center justify-between pt-2">
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-accent">{s.count}</span>
              <ArrowRight className="h-4 w-4 text-muted group-hover:text-primary group-hover:translate-x-1 transition" />
            </div>
          </Link>
        ))}
      </div>

      <div>
        <h3 className="font-display font-bold text-2xl mb-6">Full Roster</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.values(characters).map((c) => (
            <Link
              key={c.slug}
              to={`/characters/profile/${c.slug}`}
              className="flex items-center gap-3 rounded-2xl border border-divider bg-surface/60 px-4 py-3 transition lift-on-hover hover:border-primary/40"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/15 font-display font-bold text-primary-light">
                {c.name.charAt(0)}
              </span>
              <span className="min-w-0">
                <span className="flex items-center gap-1.5">
                  <span className="font-medium text-ink truncate">{c.name}</span>
                  {c.status === 'deceased' && <DeceasedMark />}
                </span>
                <span className="block text-xs text-muted truncate">{c.label === 'Protagonist' ? 'Protagonist' : c.title}</span>
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
