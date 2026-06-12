import { Link } from 'react-router-dom'
import { Orbit, ArrowLeft } from 'lucide-react'

export default function PrivacyPolicy() {
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
          Privacy Policy
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted mb-12">
          Last updated · 2026
        </p>

        <div className="space-y-8 text-muted leading-relaxed text-[15px]">
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">Information we collect</h2>
            <p>
              When you wishlist Yee Universe, sign up for launch alerts, or join our community channels, we may collect
              your email address and any preferences you provide (such as platform or character preference). We do not
              collect payment information directly — all storefront purchases are handled by the relevant platform
              (e.g. Steam) under their own privacy policy.
            </p>
          </section>
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">How we use your information</h2>
            <p>
              We use your email solely to send updates about Yee Universe's development, launch date, and related
              announcements. You can unsubscribe at any time via the link in any email we send.
            </p>
          </section>
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">Third-party services</h2>
            <p>
              Links to Discord, Reddit, YouTube, TikTok, and Steam are provided for convenience. Each of these
              platforms has its own privacy policy governing your use of their services.
            </p>
          </section>
          <section>
            <h2 className="font-display font-bold text-xl text-ink mb-2">Data retention &amp; contact</h2>
            <p>
              We retain signup information only as long as needed to provide updates about the game. To request
              deletion of your data, contact us through any of our community channels linked in the footer.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
