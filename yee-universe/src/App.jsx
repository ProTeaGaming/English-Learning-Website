import { useState, useEffect, useRef, useLayoutEffect } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  Orbit, Menu, X, Play, ArrowUpRight, ArrowRight, Globe2, Users, GitBranch, Cpu,
  Swords, UsersRound, SquarePlay, MessageCircle, MessageSquare, Music2, Gamepad2,
  ShoppingBag, Gem, KeyRound, Coins, Shirt, BookOpen, Sparkles, Send,
  CheckCircle2, Radar, Compass, Shield,
} from 'lucide-react'

gsap.registerPlugin(ScrollTrigger)

function CountUp({ end, suffix = '', duration = 1800 }) {
  const ref = useRef(null)
  const [value, setValue] = useState(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    let started = false
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !started) {
        started = true
        const start = performance.now()
        const tick = (now) => {
          const progress = Math.min((now - start) / duration, 1)
          const eased = 1 - Math.pow(1 - progress, 3)
          setValue(Math.round(end * eased))
          if (progress < 1) requestAnimationFrame(tick)
        }
        requestAnimationFrame(tick)
        observer.disconnect()
      }
    }, { threshold: 0.4 })
    observer.observe(el)
    return () => observer.disconnect()
  }, [end, duration])

  return <span ref={ref}>{value}{suffix}</span>
}

function useReveal(selector, vars = {}) {
  useEffect(() => {
    const els = gsap.utils.toArray(selector)
    const triggers = els.map((el) =>
      gsap.fromTo(
        el,
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 1,
          ease: 'power3.out',
          scrollTrigger: { trigger: el, start: 'top 85%' },
          ...vars,
        }
      )
    )
    return () => triggers.forEach((t) => t.scrollTrigger && t.scrollTrigger.kill())
  }, [selector])
}

function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    onScroll()
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const links = [
    { label: 'Lore', href: '#lore' },
    { label: 'Gameplay', href: '#gameplay' },
    { label: 'Content', href: '#content' },
    { label: 'Shop', href: '#shop' },
    { label: 'Community', href: '#community' },
  ]

  return (
    <header className={`fixed top-0 inset-x-0 z-50 transition-all duration-500 ${scrolled ? 'py-3' : 'py-5'}`}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className={`flex items-center justify-between rounded-full px-4 sm:px-6 py-3 transition-all duration-500 ${scrolled ? 'glass' : 'bg-transparent'}`}>
          <a href="#top" className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary ring-pulse">
              <Orbit className="h-5 w-5 text-white" strokeWidth={2.4} />
            </span>
            <span className="font-display font-bold tracking-tight text-lg text-ink">Yee Universe</span>
          </a>

          <nav className="hidden lg:flex items-center gap-8">
            {links.map((l) => (
              <a key={l.label} href={l.href} className="text-sm font-medium text-muted hover:text-ink transition lift-on-hover">
                {l.label}
              </a>
            ))}
            <Link to="/characters" className="text-sm font-medium text-muted hover:text-ink transition lift-on-hover">
              Characters
            </Link>
          </nav>

          <div className="hidden lg:block">
            <a href="#wishlist" className="magnetic-btn inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-bold text-deep">
              Wishlist on Steam
            </a>
          </div>

          <button onClick={() => setOpen(true)} className="lg:hidden flex items-center justify-center h-10 w-10 rounded-full glass text-ink" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 bg-deep/95 backdrop-blur-xl flex flex-col">
          <div className="flex items-center justify-between px-6 py-5">
            <a href="#top" className="flex items-center gap-2" onClick={() => setOpen(false)}>
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary">
                <Orbit className="h-5 w-5 text-white" strokeWidth={2.4} />
              </span>
              <span className="font-display font-bold tracking-tight text-lg text-ink">Yee Universe</span>
            </a>
            <button onClick={() => setOpen(false)} className="flex items-center justify-center h-10 w-10 rounded-full glass text-ink" aria-label="Close menu">
              <X className="h-5 w-5" />
            </button>
          </div>
          <nav className="flex flex-col items-center justify-center flex-1 gap-8">
            {links.map((l) => (
              <a key={l.label} href={l.href} onClick={() => setOpen(false)} className="font-display text-3xl font-bold text-ink hover:text-primary transition">
                {l.label}
              </a>
            ))}
            <Link to="/characters" onClick={() => setOpen(false)} className="font-display text-3xl font-bold text-ink hover:text-primary transition">
              Characters
            </Link>
            <a href="#wishlist" onClick={() => setOpen(false)} className="magnetic-btn mt-4 inline-flex items-center gap-2 rounded-full bg-accent px-8 py-3 text-base font-bold text-deep">
              Wishlist on Steam
            </a>
          </nav>
        </div>
      )}
    </header>
  )
}

function Hero() {
  const ref = useRef(null)

  useLayoutEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })
    tl.fromTo('.hero-eyebrow', { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8 })
      .fromTo('.hero-title', { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 1 }, '-=0.5')
      .fromTo('.hero-sub', { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8 }, '-=0.6')
      .fromTo('.hero-cta', { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, stagger: 0.15 }, '-=0.5')
      .fromTo('.hero-stat', { opacity: 0 }, { opacity: 1, duration: 1, stagger: 0.1 }, '-=0.4')
  }, [])

  return (
    <section id="top" ref={ref} className="relative min-h-dvh flex items-center overflow-hidden">
      <div className="absolute inset-0">
        <img
          src="https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2400&auto=format&fit=crop"
          alt="A vivid nebula scattered with stars"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-background/75 to-background" />
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/30 to-transparent" />
      </div>

      <div className="absolute top-28 right-6 sm:right-16 lg:right-24 hidden sm:block pointer-events-none">
        <div className="relative h-64 w-64">
          <span className="absolute h-2 w-2 rounded-full bg-accent shadow-[0_0_12px_2px_rgba(242,193,78,0.8)]" style={{ top: '10%', left: '20%', animation: 'float 7s ease-in-out infinite' }} />
          <span className="absolute h-1.5 w-1.5 rounded-full bg-primary-light shadow-[0_0_10px_2px_rgba(216,180,254,0.8)]" style={{ top: '40%', left: '70%', animation: 'float 9s ease-in-out infinite 1s' }} />
          <span className="absolute h-1 w-1 rounded-full bg-white" style={{ top: '70%', left: '35%', animation: 'float 6s ease-in-out infinite 2s' }} />
          <span className="absolute h-2 w-2 rounded-full bg-primary shadow-[0_0_14px_3px_rgba(168,85,247,0.7)]" style={{ top: '55%', left: '10%', animation: 'float 8s ease-in-out infinite 0.5s' }} />
        </div>
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-6 sm:px-10 lg:px-16 pt-32 pb-20 w-full">
        <p className="hero-eyebrow font-mono text-xs sm:text-sm uppercase tracking-[0.3em] text-primary-light mb-6">
          Open-World Sci-Fi · Coming to Steam
        </p>
        <h1 className="hero-title font-display font-extrabold tracking-tight text-5xl sm:text-7xl lg:text-8xl leading-[1.05] max-w-4xl text-balance">
          Two Fates.<br /><span className="gradient-text">One Cosmos.</span>
        </h1>
        <p className="hero-sub mt-6 max-w-xl text-lg text-muted leading-relaxed">
          Step into the Frontier as <span className="text-ink font-semibold">Kade Orin</span> and{' '}
          <span className="text-ink font-semibold">Vex Solenne</span> — two strangers bound by a signal from
          beyond the stars, racing to uncover the secrets of the universe before three warring powers tear it apart.
        </p>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          <a href="#wishlist" className="hero-cta magnetic-btn inline-flex items-center gap-2 rounded-full bg-accent px-7 py-3.5 text-sm font-bold text-deep">
            Wishlist on Steam <ArrowUpRight className="h-4 w-4" />
          </a>
          <a href="#content" className="hero-cta magnetic-btn glass inline-flex items-center gap-2 rounded-full px-7 py-3.5 text-sm font-bold text-ink">
            <Play className="h-4 w-4 fill-current" /> Watch Trailer
          </a>
        </div>

        <div className="mt-16 flex flex-wrap items-center gap-x-10 gap-y-4">
          <div className="hero-stat">
            <p className="font-display font-extrabold text-3xl text-ink"><CountUp end={40} suffix="+" /></p>
            <p className="text-xs uppercase tracking-[0.2em] text-muted mt-1">Star Systems</p>
          </div>
          <div className="h-10 w-px bg-divider hidden sm:block" />
          <div className="hero-stat">
            <p className="font-display font-extrabold text-3xl text-ink"><CountUp end={120} suffix="+" /></p>
            <p className="text-xs uppercase tracking-[0.2em] text-muted mt-1">Hours of Story</p>
          </div>
          <div className="h-10 w-px bg-divider hidden sm:block" />
          <div className="hero-stat">
            <p className="font-display font-extrabold text-3xl text-ink"><CountUp end={3} /></p>
            <p className="text-xs uppercase tracking-[0.2em] text-muted mt-1">Powers at War</p>
          </div>
        </div>
      </div>
    </section>
  )
}

function ProtagonistShuffler() {
  const [active, setActive] = useState(0)
  const protagonists = [
    {
      name: 'Kade Orin',
      role: 'Frontier Engineer & Pilot',
      tag: 'Tech · Wayfinder-class ship',
      desc: 'Raised in the salvage yards of the Outer Reach, Kade can rebuild a derelict cruiser from scrap — and fly it straight into a warzone.',
    },
    {
      name: 'Vex Solenne',
      role: 'Threshold-Touched Scout',
      tag: 'Psi · Threshold sense',
      desc: 'Marked by an ancient signal that rewired her mind, Vex feels the pulse of the Threshold — and the things that live beyond it.',
    },
  ]

  useEffect(() => {
    const id = setInterval(() => setActive((a) => (a + 1) % protagonists.length), 4000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="relative h-56 sm:h-64 rounded-3xl overflow-hidden border border-divider bg-surface p-5">
      {protagonists.map((p, i) => (
        <div
          key={p.name}
          className="absolute inset-5 transition-all duration-700 ease-out"
          style={{
            opacity: i === active ? 1 : 0,
            transform: i === active ? 'translateY(0) scale(1)' : 'translateY(16px) scale(0.98)',
            pointerEvents: i === active ? 'auto' : 'none',
          }}
        >
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-primary-light">{p.tag}</p>
          <h4 className="font-display font-bold text-2xl mt-2">{p.name}</h4>
          <p className="text-sm text-muted mt-1">{p.role}</p>
          <p className="text-sm text-muted/90 mt-3 leading-relaxed">{p.desc}</p>
        </div>
      ))}
      <div className="absolute bottom-4 left-5 flex gap-2">
        {protagonists.map((p, i) => (
          <button
            key={p.name}
            onClick={() => setActive(i)}
            className={`h-1.5 rounded-full transition-all duration-300 ${i === active ? 'w-8 bg-accent' : 'w-3 bg-divider'}`}
            aria-label={`Show ${p.name}`}
          />
        ))}
      </div>
    </div>
  )
}

function SectorScan() {
  const comets = useRef(
    Array.from({ length: 16 }, (_, i) => ({
      id: i,
      left: Math.round(Math.random() * 100),
      delay: (Math.random() * 5).toFixed(2),
      duration: (2.5 + Math.random() * 2.5).toFixed(2),
      size: (1 + Math.random() * 1.6).toFixed(2),
    }))
  ).current

  return (
    <div className="relative h-56 sm:h-64 rounded-3xl overflow-hidden border border-divider bg-deep">
      <div className="absolute inset-0 grid-bg opacity-30" />
      <div className="absolute inset-x-0 top-0 h-1/3 bg-gradient-to-b from-primary/15 to-transparent" />
      {comets.map((c) => (
        <span
          key={c.id}
          className="comet"
          style={{
            left: `${c.left}%`,
            animationDelay: `${c.delay}s`,
            animationDuration: `${c.duration}s`,
            '--comet-size': c.size,
          }}
        />
      ))}
      <div className="absolute bottom-5 left-5 right-5 flex items-end justify-between">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-primary-light">Sector Scan</p>
          <h4 className="font-display font-bold text-xl mt-1">Live Stardust Tracking</h4>
        </div>
        <Radar className="h-8 w-8 text-primary/70 animate-pulse-slow" />
      </div>
    </div>
  )
}

function TechTreeCard() {
  const [hovered, setHovered] = useState(null)
  const nodes = [
    { id: 'core', label: 'Wayfinder Core', x: 50, y: 78, icon: Cpu },
    { id: 'nav', label: 'Slip-Drive Nav', x: 18, y: 46, icon: Compass },
    { id: 'arms', label: 'Arc Plating', x: 82, y: 46, icon: Shield },
    { id: 'sig', label: 'Threshold Relay', x: 50, y: 16, icon: Sparkles },
  ]
  const edges = [['core', 'nav'], ['core', 'arms'], ['nav', 'sig'], ['arms', 'sig']]

  return (
    <div className="relative h-56 sm:h-64 rounded-3xl overflow-hidden border border-divider bg-surface p-5">
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        {edges.map(([a, b], i) => {
          const na = nodes.find((n) => n.id === a)
          const nb = nodes.find((n) => n.id === b)
          const isActive = hovered === a || hovered === b
          return (
            <line
              key={i}
              x1={na.x} y1={na.y} x2={nb.x} y2={nb.y}
              stroke={isActive ? '#F2C14E' : '#2C2240'}
              strokeWidth={isActive ? 0.6 : 0.4}
              className="transition-all duration-300"
            />
          )
        })}
      </svg>
      {nodes.map((n) => {
        const Icon = n.icon
        const isActive = hovered === n.id
        return (
          <button
            key={n.id}
            onMouseEnter={() => setHovered(n.id)}
            onMouseLeave={() => setHovered(null)}
            className="absolute flex flex-col items-center gap-1.5 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${n.x}%`, top: `${n.y}%` }}
          >
            <span className={`flex h-9 w-9 items-center justify-center rounded-full border transition-all duration-300 ${isActive ? 'bg-accent border-accent scale-110' : 'bg-background border-divider'}`}>
              <Icon className={`h-4 w-4 ${isActive ? 'text-deep' : 'text-primary-light'}`} />
            </span>
            <span className={`text-[10px] font-mono uppercase tracking-wider whitespace-nowrap transition-opacity duration-300 ${isActive ? 'opacity-100 text-ink' : 'opacity-0'}`}>
              {n.label}
            </span>
          </button>
        )
      })}
      <div className="absolute bottom-5 left-5">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-primary-light">Tech Tree</p>
        <h4 className="font-display font-bold text-xl mt-1">Forge Across Timelines</h4>
      </div>
    </div>
  )
}

function Features() {
  useReveal('.feature-card', { stagger: 0.15 })
  return (
    <section id="introduction" className="relative py-24 sm:py-32 px-6 sm:px-10 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-4">Introduction</p>
          <h2 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight text-balance">
            A living universe, <span className="font-serif italic font-medium text-primary-light">built to explore</span>
          </h2>
          <p className="mt-5 text-muted leading-relaxed text-lg">
            Yee Universe is an open-world sci-fi adventure where every star system tells a story. Switch between
            two protagonists, push technology forward across branching timelines, and decide the fate of three
            powers locked in a struggle for the Threshold.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="feature-card">
            <ProtagonistShuffler />
            <h3 className="font-display font-bold text-xl mt-5">Dual Protagonists</h3>
            <p className="text-sm text-muted mt-2 leading-relaxed">
              Swap between Kade and Vex at will — each with unique skills, ships, and a perspective on the same unfolding story.
            </p>
          </div>
          <div className="feature-card">
            <SectorScan />
            <h3 className="font-display font-bold text-xl mt-5">Sector Scan</h3>
            <p className="text-sm text-muted mt-2 leading-relaxed">
              Chart unexplored sectors as stardust streams reveal hidden anomalies, derelicts, and Threshold rifts.
            </p>
          </div>
          <div className="feature-card">
            <TechTreeCard />
            <h3 className="font-display font-bold text-xl mt-5">Tech Tree</h3>
            <p className="text-sm text-muted mt-2 leading-relaxed">
              Hover the nodes to trace how Wayfinder tech evolves — research, salvage, and ancient relics all feed the tree.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

function Pillars() {
  useReveal('.pillar', { stagger: 0.15 })
  const pillars = [
    { value: 40, suffix: '+', label: 'Star Systems to Explore', desc: 'From sunbaked salvage belts to frozen Threshold rifts.' },
    { value: 120, suffix: '+', label: 'Hours of Story & Side Content', desc: 'Main campaign, faction arcs, and side stories for both leads.' },
    { value: 3, suffix: '', label: 'Powers at War', desc: 'The Sundered Concord, the Veyrun Hegemony, and the Frontier Free Worlds.' },
  ]
  return (
    <section className="relative py-20 sm:py-28 px-6 sm:px-10 lg:px-16 border-y border-divider bg-surface/40">
      <div className="mx-auto max-w-6xl grid grid-cols-1 sm:grid-cols-3 gap-10 sm:gap-6 text-center sm:text-left">
        {pillars.map((p) => (
          <div key={p.label} className="pillar">
            <p className="font-display font-extrabold text-5xl sm:text-6xl gradient-text">
              <CountUp end={p.value} suffix={p.suffix} />
            </p>
            <p className="mt-3 font-display font-bold text-lg">{p.label}</p>
            <p className="mt-2 text-sm text-muted leading-relaxed">{p.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function Lore() {
  const containerRef = useRef(null)

  useEffect(() => {
    const cards = gsap.utils.toArray('.lore-card')
    const triggers = []
    cards.forEach((card, i) => {
      if (i === cards.length - 1) return
      const next = cards[i + 1]
      triggers.push(
        ScrollTrigger.create({
          trigger: next,
          start: 'top bottom',
          end: 'top top',
          scrub: true,
          onUpdate: (self) => {
            gsap.set(card, {
              scale: 1 - self.progress * 0.08,
              filter: `blur(${self.progress * 6}px)`,
              opacity: 1 - self.progress * 0.5,
            })
          },
        })
      )
    })
    return () => triggers.forEach((t) => t.kill())
  }, [])

  const eras = [
    {
      tag: 'Era I',
      title: 'The Discovery',
      img: 'https://images.unsplash.com/photo-1419833173245-f59e1b93f9ee?q=80&w=1600&auto=format&fit=crop',
      desc: 'A research vessel intercepts an impossible signal from beyond charted space — the first whisper of the Threshold, and the spark that sets Kade and Vex on a collision course.',
    },
    {
      tag: 'Era II',
      title: 'The Convergence',
      img: 'https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?q=80&w=1600&auto=format&fit=crop',
      desc: 'As Threshold technology spreads, three powers race to control it — the Sundered Concord, the Veyrun Hegemony, and the Frontier Free Worlds — each rewriting history along the way.',
    },
    {
      tag: 'Era III',
      title: 'The Reckoning',
      img: 'https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?q=80&w=1600&auto=format&fit=crop',
      desc: 'Something on the other side of the Threshold has noticed. Native uprisings, foreign incursions, and a presence older than any star now converge on the Frontier.',
    },
  ]

  const protagonists = [
    {
      name: 'Kade Orin',
      tag: 'The Engineer',
      desc: "A salvager from the Outer Reach with a gift for coaxing dead tech back to life. Kade's Wayfinder-class ship is half-myth among scrappers — and the only thing fast enough to outrun what's coming.",
    },
    {
      name: 'Vex Solenne',
      tag: 'The Touched',
      desc: 'Once a cartographer for the Concord, Vex was exposed to a Threshold signal that left her able to sense rifts before they open. The Hegemony wants her. The Concord fears her.',
    },
  ]

  return (
    <section id="lore" ref={containerRef} className="relative px-6 sm:px-10 lg:px-16 py-24 sm:py-32">
      <div className="mx-auto max-w-6xl mb-16">
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-4">Lore</p>
        <h2 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight text-balance max-w-2xl">
          Three eras shape the <span className="font-serif italic font-medium text-primary-light">Frontier</span>
        </h2>
      </div>

      <div className="relative">
        {eras.map((era, i) => (
          <div key={era.tag} className="lore-card sticky top-20 mb-6" style={{ zIndex: i + 1 }}>
            <div className="mx-auto max-w-5xl rounded-3xl overflow-hidden border border-divider glass-dark min-h-[420px] sm:min-h-[460px] grid sm:grid-cols-2">
              <div className="relative h-56 sm:h-auto">
                <img src={era.img} alt="" className="absolute inset-0 h-full w-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-deep/80 via-transparent to-transparent sm:bg-gradient-to-r sm:from-transparent sm:to-deep/30" />
              </div>
              <div className="p-8 sm:p-10 flex flex-col justify-center">
                <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent mb-3">{era.tag}</p>
                <h3 className="font-display font-bold text-3xl sm:text-4xl">{era.title}</h3>
                <p className="mt-4 text-muted leading-relaxed">{era.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mx-auto max-w-6xl mt-24">
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-8">The Protagonists</p>
        <div className="grid sm:grid-cols-2 gap-6">
          {protagonists.map((p) => (
            <div key={p.name} className="rounded-3xl border border-divider bg-surface p-8">
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-accent mb-2">{p.tag}</p>
              <h3 className="font-display font-bold text-2xl">{p.name}</h3>
              <p className="mt-3 text-muted leading-relaxed text-[15px]">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Gameplay() {
  useReveal('.gameplay-tile', { stagger: 0.08 })
  const tiles = [
    { icon: Globe2, title: 'Open-World Star Systems', desc: 'Free-roam across 40+ handcrafted systems, from derelict shipyards to living gas giants.' },
    { icon: Users, title: 'Dual-Protagonist Campaign', desc: 'Switch between Kade and Vex mid-mission — their choices ripple across the same timeline.' },
    { icon: GitBranch, title: 'Branching Timelines', desc: 'Decisions echo forward and backward through Threshold rifts, reshaping entire eras.' },
    { icon: Cpu, title: 'Tech & Ship Customization', desc: 'Salvage, research, and forge upgrades for the Wayfinder and its crew.' },
    { icon: Swords, title: 'Faction Diplomacy & Conflict', desc: 'Negotiate, betray, or go to war with the Concord, the Hegemony, and the Free Worlds.' },
    { icon: UsersRound, title: 'Drop-in Co-op', desc: 'Bring a friend along as the second protagonist for any mission, any time.' },
  ]
  return (
    <section id="gameplay" className="relative px-6 sm:px-10 lg:px-16 py-24 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl mb-14">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-4">Gameplay</p>
          <h2 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight text-balance">
            Systems built for <span className="font-serif italic font-medium text-primary-light">discovery</span>
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px rounded-3xl overflow-hidden border border-divider bg-divider">
          {tiles.map((tile) => {
            const Icon = tile.icon
            return (
              <div key={tile.title} className="gameplay-tile group bg-surface hover:bg-background transition-colors duration-300 p-8 min-h-[220px] flex flex-col justify-between">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary-light group-hover:bg-primary group-hover:text-white transition-colors duration-300">
                  <Icon className="h-5 w-5" />
                </span>
                <div className="mt-6">
                  <h3 className="font-display font-bold text-lg">{tile.title}</h3>
                  <p className="mt-2 text-sm text-muted leading-relaxed">{tile.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function Content() {
  useReveal('.content-card', { stagger: 0.1 })
  const videos = [
    {
      type: 'Trailer',
      title: 'Yee Universe — Announcement Trailer',
      platform: 'YouTube',
      icon: SquarePlay,
      img: 'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?q=80&w=1200&auto=format&fit=crop',
      wide: true,
    },
    {
      type: 'Devlog #03',
      title: 'Building the Wayfinder',
      platform: 'YouTube',
      icon: SquarePlay,
      img: 'https://images.unsplash.com/photo-1517976487492-5750f3195933?q=80&w=1200&auto=format&fit=crop',
      wide: true,
    },
    {
      type: 'Clip',
      title: 'Threshold rift VFX test',
      platform: 'TikTok',
      icon: Music2,
      img: 'https://images.unsplash.com/photo-1543872084-c7bd3822856f?q=80&w=900&auto=format&fit=crop',
      wide: false,
    },
    {
      type: 'Clip',
      title: 'Vex vs. Hegemony patrol',
      platform: 'TikTok',
      icon: Music2,
      img: 'https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=900&auto=format&fit=crop',
      wide: false,
    },
  ]

  return (
    <section id="content" className="relative px-6 sm:px-10 lg:px-16 py-24 sm:py-32 bg-surface/40 border-y border-divider">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl mb-14">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-4">Content</p>
          <h2 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight text-balance">
            Watch the Frontier <span className="font-serif italic font-medium text-primary-light">come to life</span>
          </h2>
          <p className="mt-5 text-muted leading-relaxed text-lg">
            Trailers, devlogs, and behind-the-scenes clips — follow development on YouTube and TikTok as Yee Universe
            takes shape.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {videos.map((v) => {
            const Icon = v.icon
            return (
              <a
                key={v.title}
                href="#community"
                className={`content-card group relative rounded-3xl overflow-hidden border border-divider lift-on-hover ${v.wide ? 'lg:col-span-2 aspect-video' : 'aspect-[9/16]'}`}
              >
                <img src={v.img} alt="" className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-deep/90 via-deep/20 to-deep/10" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="flex h-14 w-14 items-center justify-center rounded-full bg-white/10 border border-white/30 backdrop-blur-sm transition-transform duration-300 group-hover:scale-110">
                    <Play className="h-5 w-5 text-white fill-current" />
                  </span>
                </div>
                <div className="absolute top-4 left-4 inline-flex items-center gap-1.5 rounded-full glass-dark px-3 py-1.5 text-[11px] font-mono uppercase tracking-[0.15em] text-primary-light">
                  <Icon className="h-3.5 w-3.5" /> {v.platform}
                </div>
                <div className="absolute bottom-4 left-4 right-4">
                  <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-accent mb-1">{v.type}</p>
                  <h3 className="font-display font-bold text-base sm:text-lg leading-tight">{v.title}</h3>
                </div>
              </a>
            )
          })}
        </div>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          <a href="#community" className="magnetic-btn glass inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-bold text-ink">
            <SquarePlay className="h-4 w-4" /> Subscribe on YouTube
          </a>
          <a href="#community" className="magnetic-btn glass inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-bold text-ink">
            <Music2 className="h-4 w-4" /> Follow on TikTok
          </a>
        </div>
      </div>
    </section>
  )
}

function ShopCard({ icon: Icon, name, desc, price }) {
  return (
    <div className="shop-card rounded-3xl border border-divider bg-surface p-6 hover:border-primary/40 transition-colors duration-300 lift-on-hover">
      <div className="flex items-center justify-between">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary-light">
          <Icon className="h-5 w-5" />
        </span>
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted px-2.5 py-1 rounded-full border border-divider">
          Pre-launch
        </span>
      </div>
      <h4 className="font-display font-bold text-lg mt-5">{name}</h4>
      <p className="text-sm text-muted mt-2 leading-relaxed">{desc}</p>
      <div className="mt-5 flex items-center justify-between">
        <span className="font-display font-bold text-primary-light">{price}</span>
        <span className="text-xs font-bold uppercase tracking-wider text-muted">Notify Me</span>
      </div>
    </div>
  )
}

function Shop() {
  useReveal('.shop-card', { stagger: 0.08 })
  const inGame = [
    { icon: Gem, name: 'Stardust Tokens', desc: 'Premium currency for cosmetic gear, ship skins, and gacha pulls.', price: 'From $4.99' },
    { icon: KeyRound, name: 'Relic Keys', desc: 'Unlock Threshold caches scattered across the Frontier.', price: 'From $2.99' },
    { icon: Coins, name: 'Founder Bundle', desc: 'Bonus currency, an exclusive ship skin, and an early-access pass.', price: '$19.99' },
  ]
  const merch = [
    { icon: Shirt, name: 'Wayfinder Crew Tee', desc: 'Premium cotton tee with the Wayfinder crest.', price: '$28.00' },
    { icon: Sparkles, name: 'Vex Solenne Plushie', desc: 'Soft plush of Vex in her signature flight suit.', price: '$32.00' },
    { icon: BookOpen, name: 'Frontier Art Book', desc: 'Concept art, lore notes, and timeline maps from the Discovery era to now.', price: '$24.00' },
  ]

  return (
    <section id="shop" className="relative px-6 sm:px-10 lg:px-16 py-24 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl mb-14">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-4">Shop</p>
          <h2 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight text-balance">
            Gear up for <span className="font-serif italic font-medium text-primary-light">launch</span>
          </h2>
          <p className="mt-5 text-muted leading-relaxed text-lg">
            The Yee Universe store opens alongside our Steam launch — in-game currencies, keys, and cosmetics, plus
            real-world merch for the Frontier faithful. Sign up below to be notified the moment it goes live.
          </p>
        </div>

        <div className="mb-14">
          <h3 className="font-display font-bold text-xl mb-6 flex items-center gap-2">
            <ShoppingBag className="h-5 w-5 text-primary-light" /> In-Game Store
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {inGame.map((item) => (
              <ShopCard key={item.name} {...item} />
            ))}
          </div>
        </div>

        <div>
          <h3 className="font-display font-bold text-xl mb-6 flex items-center gap-2">
            <Shirt className="h-5 w-5 text-primary-light" /> Merch
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {merch.map((item) => (
              <ShopCard key={item.name} {...item} />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function Community() {
  useReveal('.community-card', { stagger: 0.1 })
  const channels = [
    { icon: MessageCircle, name: 'Discord', desc: 'Chat with the dev team, share theories, and get early build access.', stat: '12,000+ members', cta: 'Join Server' },
    { icon: MessageSquare, name: 'Reddit', desc: 'r/YeeUniverse — lore threads, fan art, and dev AMAs.', stat: '8,400+ members', cta: 'Join Subreddit' },
    { icon: SquarePlay, name: 'YouTube', desc: 'Trailers, devlogs, and deep dives into the Frontier.', stat: '25,000+ subscribers', cta: 'Subscribe' },
    { icon: Music2, name: 'TikTok', desc: 'Quick looks at combat, ships, and Threshold VFX.', stat: '40,000+ followers', cta: 'Follow' },
    { icon: Gamepad2, name: 'Steam', desc: 'Wishlist now and get notified the moment Yee Universe launches.', stat: 'Wishlist today', cta: 'Wishlist' },
  ]

  return (
    <section id="community" className="relative px-6 sm:px-10 lg:px-16 py-24 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl mb-14">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-4">Community</p>
          <h2 className="font-display font-extrabold text-4xl sm:text-5xl tracking-tight text-balance">
            Join the <span className="font-serif italic font-medium text-primary-light">Frontier</span>
          </h2>
          <p className="mt-5 text-muted leading-relaxed text-lg">
            Theories, fan art, dev chats, and early looks — the Yee Universe community is already exploring the
            Frontier. Come find your crew.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {channels.map((c) => {
            const Icon = c.icon
            return (
              <a key={c.name} href="#wishlist" className="community-card group rounded-3xl border border-divider bg-surface p-6 hover:border-primary/40 transition-colors duration-300 lift-on-hover">
                <div className="flex items-center justify-between">
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary-light group-hover:bg-primary group-hover:text-white transition-colors duration-300">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted">{c.stat}</span>
                </div>
                <h3 className="font-display font-bold text-xl mt-5">{c.name}</h3>
                <p className="text-sm text-muted mt-2 leading-relaxed">{c.desc}</p>
                <div className="mt-5 inline-flex items-center gap-1.5 text-sm font-bold text-primary-light">
                  {c.cta} <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
                </div>
              </a>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function Newsletter() {
  const [status, setStatus] = useState('idle')
  const [email, setEmail] = useState('')
  const [protagonist, setProtagonist] = useState('both')
  const [platforms, setPlatforms] = useState({ pc: true, ps5: false, xbox: false })

  const togglePlatform = (key) => setPlatforms((p) => ({ ...p, [key]: !p[key] }))

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!email) return
    setStatus('sending')
    setTimeout(() => setStatus('sent'), 1400)
  }

  return (
    <section id="wishlist" className="relative px-6 sm:px-10 lg:px-16 py-24 sm:py-32">
      <div className="mx-auto max-w-3xl rounded-3xl border border-divider glass-dark p-8 sm:p-12 relative overflow-hidden">
        <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-primary/20 blur-3xl pointer-events-none" />
        <div className="relative">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary-light mb-4">Stay in the loop</p>
          <h2 className="font-display font-extrabold text-3xl sm:text-4xl tracking-tight text-balance max-w-lg">
            Get launch news <span className="font-serif italic font-medium text-primary-light">first</span>
          </h2>
          <p className="mt-4 text-muted leading-relaxed max-w-lg">
            Sign up for development updates, beta invites, and the Steam launch date — straight to your inbox.
          </p>

          {status === 'sent' ? (
            <div className="mt-8 flex items-center gap-3 rounded-2xl border border-primary/30 bg-primary/10 px-6 py-5">
              <CheckCircle2 className="h-6 w-6 text-primary-light flex-shrink-0" />
              <div>
                <p className="font-display font-bold">You're on the list.</p>
                <p className="text-sm text-muted mt-0.5">Watch your inbox for transmissions from the Frontier.</p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-8 space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-[0.2em] text-muted mb-2">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full rounded-xl bg-background border border-divider px-4 py-3 text-sm text-ink placeholder:text-muted/60 focus:outline-none focus:border-primary transition"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-[0.2em] text-muted mb-3">Favorite protagonist</label>
                <div className="flex flex-wrap gap-3">
                  {['kade', 'vex', 'both'].map((id) => (
                    <button
                      type="button"
                      key={id}
                      onClick={() => setProtagonist(id)}
                      className={`rounded-full px-4 py-2 text-sm font-medium border transition ${protagonist === id ? 'bg-primary border-primary text-white' : 'border-divider text-muted hover:text-ink'}`}
                    >
                      {id === 'kade' ? 'Kade Orin' : id === 'vex' ? 'Vex Solenne' : 'Both'}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-[0.2em] text-muted mb-3">Platforms you're interested in</label>
                <div className="flex flex-wrap gap-3">
                  {[['pc', 'PC'], ['ps5', 'PlayStation 5'], ['xbox', 'Xbox Series X|S']].map(([key, label]) => (
                    <label
                      key={key}
                      className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium border cursor-pointer transition ${platforms[key] ? 'bg-primary/15 border-primary text-ink' : 'border-divider text-muted hover:text-ink'}`}
                    >
                      <input type="checkbox" checked={platforms[key]} onChange={() => togglePlatform(key)} className="hidden" />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={status === 'sending'}
                className="magnetic-btn w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-full bg-accent px-8 py-3.5 text-sm font-bold text-deep disabled:opacity-60"
              >
                {status === 'sending' ? 'Sending...' : (<>Notify Me <Send className="h-4 w-4" /></>)}
              </button>
            </form>
          )}
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="relative px-6 sm:px-10 lg:px-16 pt-20 pb-10 border-t border-divider">
      <div className="mx-auto max-w-6xl">
        <h2 className="font-display font-extrabold text-4xl sm:text-6xl tracking-tight max-w-2xl text-balance">
          Two Fates. <span className="gradient-text">One Cosmos.</span>
        </h2>

        <div className="mt-14 grid grid-cols-2 sm:grid-cols-4 gap-10">
          <div className="col-span-2 sm:col-span-1">
            <a href="#top" className="flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary">
                <Orbit className="h-5 w-5 text-white" strokeWidth={2.4} />
              </span>
              <span className="font-display font-bold tracking-tight text-lg">Yee Universe</span>
            </a>
            <p className="mt-4 text-sm text-muted leading-relaxed max-w-xs">
              An open-world sci-fi adventure across the Frontier. Currently in development.
            </p>
            <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-divider px-3 py-1.5">
              <span className="h-2 w-2 rounded-full bg-accent ring-pulse" />
              <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted">In Development</span>
            </div>
          </div>

          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted mb-4">Explore</p>
            <ul className="space-y-3 text-sm">
              <li><a href="#lore" className="text-muted hover:text-ink transition">Lore</a></li>
              <li><a href="#gameplay" className="text-muted hover:text-ink transition">Gameplay</a></li>
              <li><a href="#content" className="text-muted hover:text-ink transition">Content</a></li>
              <li><a href="#shop" className="text-muted hover:text-ink transition">Shop</a></li>
              <li><a href="#community" className="text-muted hover:text-ink transition">Community</a></li>
            </ul>
          </div>

          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted mb-4">Connect</p>
            <ul className="space-y-3 text-sm">
              <li><a href="#community" className="text-muted hover:text-ink transition">Discord</a></li>
              <li><a href="#community" className="text-muted hover:text-ink transition">Reddit</a></li>
              <li><a href="#community" className="text-muted hover:text-ink transition">YouTube</a></li>
              <li><a href="#community" className="text-muted hover:text-ink transition">TikTok</a></li>
            </ul>
          </div>

          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted mb-4">Legal</p>
            <ul className="space-y-3 text-sm">
              <li><Link to="/privacy" className="text-muted hover:text-ink transition">Privacy Policy</Link></li>
              <li><Link to="/terms" className="text-muted hover:text-ink transition">Terms of Use</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-16 pt-8 border-t border-divider flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted">© 2026 Yee Universe. All rights reserved.</p>
          <p className="text-xs text-muted font-mono uppercase tracking-[0.2em]">Built for the Frontier</p>
        </div>
      </div>
    </footer>
  )
}

function App() {
  return (
    <div className="bg-background text-ink min-h-screen">
      <div className="noise-overlay" />
      <Navbar />
      <Hero />
      <Features />
      <Pillars />
      <Lore />
      <Gameplay />
      <Content />
      <Shop />
      <Community />
      <Newsletter />
      <Footer />
    </div>
  )
}

export default App
