import { Link, NavLink, Outlet } from 'react-router-dom'
import { Orbit, ArrowLeft, Users, Swords, UsersRound } from 'lucide-react'
import { characters, teams } from '../../data/characters'

export const protagonistSlugs = Object.values(characters)
  .filter((c) => c.label === 'Protagonist')
  .map((c) => c.slug)

export const sideCharacterSlugs = Object.values(characters)
  .filter((c) => c.label !== 'Protagonist')
  .map((c) => c.slug)

export function DeceasedMark({ className = '' }) {
  return (
    <span title="Deceased" className={`text-red-400 text-base leading-none font-bold select-none ${className}`}>
      ✝
    </span>
  )
}

const RELATION_TONES = {
  companion: 'bg-primary/10 border-primary/30 text-primary-light hover:bg-primary/20',
  enemy: 'bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20',
  team: 'bg-accent/10 border-accent/30 text-accent hover:bg-accent/20',
  former: 'bg-divider/40 border-divider text-muted hover:bg-divider/60',
}

export function CharacterChip({ slug, tone, formerLabel }) {
  const char = characters[slug]
  if (!char) return null
  const isFormer = !!formerLabel
  return (
    <Link
      to={`/characters/profile/${slug}`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition lift-on-hover ${RELATION_TONES[isFormer ? 'former' : tone]}`}
    >
      {isFormer && <span className="text-[10px] font-mono uppercase tracking-wider opacity-70">{formerLabel}</span>}
      <span>{char.name}</span>
      {char.status === 'deceased' && <DeceasedMark />}
    </Link>
  )
}

export function TeamChip({ slug, formerLabel }) {
  const team = teams[slug]
  if (!team) return null
  const isFormer = !!formerLabel
  return (
    <Link
      to={`/characters/teams#${slug}`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition lift-on-hover ${RELATION_TONES[isFormer ? 'former' : 'team']}`}
    >
      {isFormer && <span className="text-[10px] font-mono uppercase tracking-wider opacity-70">{formerLabel}</span>}
      <span>{team.name}</span>
    </Link>
  )
}

export function RelationRow({ icon: Icon, label, current = [], former = [], tone, formerLabel, kind = 'character' }) {
  if (current.length === 0 && former.length === 0) return null
  const Chip = kind === 'team' ? TeamChip : CharacterChip
  return (
    <div>
      <div className="flex items-center gap-2 mb-3 text-xs font-mono uppercase tracking-[0.2em] text-muted">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="flex flex-wrap gap-2">
        {current.map((slug) => (
          <Chip key={slug} slug={slug} tone={tone} />
        ))}
        {former.map((slug) => (
          <Chip key={slug} slug={slug} tone={tone} formerLabel={formerLabel} />
        ))}
      </div>
    </div>
  )
}

export function CharacterRelations({ character }) {
  return (
    <div className="grid sm:grid-cols-3 gap-6">
      <RelationRow
        icon={Users} label="Companions" tone="companion" formerLabel="Former Companion"
        current={character.companions} former={character.formerCompanions}
      />
      <RelationRow
        icon={Swords} label="Enemies" tone="enemy" formerLabel="Former Enemy"
        current={character.enemies} former={character.formerEnemies}
      />
      <RelationRow
        icon={UsersRound} label="Teams" tone="team" formerLabel="Former Team" kind="team"
        current={character.teams} former={character.formerTeams}
      />
    </div>
  )
}

const TEAM_STATUS_STYLES = {
  active: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
  inactive: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
  disbanded: 'bg-red-500/10 border-red-500/30 text-red-400',
}

const TEAM_STATUS_LABELS = {
  active: 'Active',
  inactive: 'Inactive',
  disbanded: 'Disbanded',
}

export function TeamStatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-mono uppercase tracking-[0.15em] ${TEAM_STATUS_STYLES[status] || TEAM_STATUS_STYLES.active}`}>
      {TEAM_STATUS_LABELS[status] || status}
    </span>
  )
}

const MEMBER_STATUS_STYLES = {
  active: 'bg-primary/10 border-primary/30 text-primary-light hover:bg-primary/20',
  former: 'bg-divider/40 border-divider text-muted hover:bg-divider/60',
  deceased: 'bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20',
}

const MEMBER_STATUS_LABELS = {
  former: 'Former',
  deceased: 'Deceased',
}

export function MemberChip({ slug, status }) {
  const char = characters[slug]
  if (!char) return null
  const label = MEMBER_STATUS_LABELS[status]
  return (
    <Link
      to={`/characters/profile/${slug}`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition lift-on-hover ${MEMBER_STATUS_STYLES[status] || MEMBER_STATUS_STYLES.active}`}
    >
      {label && <span className="text-[10px] font-mono uppercase tracking-wider opacity-70">{label}</span>}
      <span>{char.name}</span>
      {char.status === 'deceased' && <DeceasedMark />}
    </Link>
  )
}

export function PageHeader({ eyebrow, title, description }) {
  return (
    <div className="max-w-2xl mb-12">
      {eyebrow && (
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent mb-3">{eyebrow}</p>
      )}
      <h1 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight mb-4 text-balance">{title}</h1>
      {description && <p className="text-muted leading-relaxed">{description}</p>}
    </div>
  )
}

const TABS = [
  { label: 'Overview', to: '/characters', end: true },
  { label: 'Protagonists', to: '/characters/protagonists' },
  { label: 'Side Characters', to: '/characters/side-characters' },
  { label: 'Teams', to: '/characters/teams' },
]

export function CharactersLayout() {
  return (
    <div className="min-h-screen bg-background text-ink font-body">
      <div className="noise-overlay" />
      <header className="sticky top-0 z-50 glass-dark border-b border-divider/60">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary ring-pulse">
              <Orbit className="h-5 w-5 text-white" strokeWidth={2.4} />
            </span>
            <span className="font-display font-bold tracking-tight text-lg">Yee Universe</span>
          </Link>

          <nav className="flex items-center gap-1 sm:gap-2 overflow-x-auto scrollbar-hide">
            {TABS.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition ${
                    isActive ? 'bg-primary text-white' : 'text-muted hover:text-ink hover:bg-surface'
                  }`
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>

          <Link to="/" className="hidden sm:inline-flex items-center gap-2 text-sm text-muted hover:text-primary transition lift-on-hover">
            <ArrowLeft className="h-4 w-4" /> Back to Home
          </Link>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-6xl px-4 sm:px-6 py-12 sm:py-16">
        <Outlet />
      </main>
    </div>
  )
}
