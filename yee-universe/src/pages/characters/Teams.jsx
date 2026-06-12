import { UsersRound } from 'lucide-react'
import { teams } from '../../data/characters'
import { PageHeader, TeamStatusBadge, MemberChip } from './shared'

export default function Teams() {
  return (
    <div>
      <PageHeader
        eyebrow="Crews, Cadres & Divisions"
        title="Teams"
        description="Every banner the cast has flown under — who's still on the roster, who's gone, and who never made it home."
      />

      <div className="space-y-8">
        {Object.values(teams).map((team) => (
          <article key={team.slug} id={team.slug} className="glass rounded-3xl p-6 sm:p-8 scroll-mt-28">
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent/15 text-accent">
                <UsersRound className="h-5 w-5" />
              </span>
              <h2 className="font-display font-extrabold text-2xl sm:text-3xl tracking-tight">{team.name}</h2>
              <TeamStatusBadge status={team.status} />
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted">{team.type}</span>
            </div>

            <p className="text-muted leading-relaxed mb-6 max-w-3xl">{team.lore}</p>

            <div>
              <div className="text-xs font-mono uppercase tracking-[0.2em] text-muted mb-3">Members</div>
              <div className="flex flex-wrap gap-2">
                {team.members.map((m) => (
                  <MemberChip key={m.slug} slug={m.slug} status={m.status} />
                ))}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
