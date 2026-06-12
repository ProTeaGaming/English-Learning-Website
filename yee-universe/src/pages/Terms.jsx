import { Link } from 'react-router-dom'
import { Orbit, ArrowLeft } from 'lucide-react'

export default function Terms() {
  return (
    <div className="min-h-screen bg-background text-ink font-body px-6 sm:px-10 lg:px-16 py-16">
      <div className="max-w-3xl mx-auto">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted hover:text-primary transition lift-on-hover mb-12">
          <ArrowLeft className="h-4 w-4" /> Back to Yee Universe
        </Link>

        <div className="flex items-center gap-2 mb-8">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary">
            <Orbit className="h-5 w-5 text-white" strokeWidth={2.4} />
          </span>
          <span className="font-display font-bold tracking-tight text-lg">Yee Universe</span>
        </div>

        <h1 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight mb-2">
          Terms of Use
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted mb-12">
          Last updated · 2026
        </p>

        <div className="space-y-8 text-muted leading-relaxed text-[15px]">
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">Pre-release information</h2>
            <p>
              Yee Universe is currently in development. Screenshots, footage, gameplay systems, release dates,
              and store items shown on this site are works in progress and subject to change without notice.
            </p>
          </section>
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">Site usage</h2>
            <p>
              This site is provided for informational purposes related to Yee Universe. You may browse, link to,
              and share pages on this site. All trademarks, character names, lore, and artwork related to Yee
              Universe are the property of their respective owners.
            </p>
          </section>
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">Store &amp; wishlist links</h2>
            <p>
              Links to Steam and other storefronts redirect to third-party platforms governed by their own terms
              of service. In-game currencies, keys, and merchandise referenced on this site are not yet available
              for purchase and will be sold once the relevant store goes live.
            </p>
          </section>
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">Community conduct</h2>
            <p>
              Our Discord, Reddit, and social channels follow their own community guidelines. Be respectful,
              avoid spoilers outside designated channels, and have fun exploring the Frontier with us.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
