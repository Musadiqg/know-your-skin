import { motion } from 'framer-motion'
import { useCallback } from 'react'
import { DemoVideo } from './components/DemoVideo'
import { SiteHeader } from './components/SiteHeader'
import { LandingStory } from './sections/LandingStory'

const easeOut = [0.22, 1, 0.36, 1] as const

export default function App() {
  const scrollDemo = useCallback(() => {
    document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const scrollOverview = useCallback(() => {
    document.getElementById('problem')?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  return (
    <>
      <SiteHeader onViewDemo={scrollDemo} onOverview={scrollOverview} />
      <div className="page">
        <section className="lp-section lp-section--hero" aria-label="Introduction">
          <div className="lp-inner lp-hero-grid">
            <motion.div
              className="lp-hero-copy"
              initial={{ opacity: 0, y: 32 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.75, ease: easeOut }}
            >
              <p className="lp-eyebrow">AI · Skincare · Open source</p>
              <h1 className="lp-hero-title">
                Know
                <br />
                your <em>skin.</em>
              </h1>
              <p className="lp-hero-lede">
                Dermatology-grade skin analysis on Google Cloud — so any skincare brand can offer routines that match
                how skin actually behaves.
              </p>
              <div className="lp-chips" aria-label="Topics">
                <span className="lp-chip lp-chip--solid">AI skin analysis</span>
                <span className="lp-chip">Google Cloud</span>
                <span className="lp-chip">Open source</span>
              </div>
              <div className="hero-actions" style={{ marginTop: 28 }}>
                <button type="button" className="btn-primary" onClick={scrollDemo}>
                  View demo
                </button>
                <button type="button" className="btn-ghost" onClick={scrollOverview}>
                  How it works
                </button>
              </div>
            </motion.div>
            <motion.div
              className="lp-hero-art"
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.85, ease: easeOut, delay: 0.08 }}
              aria-hidden
            >
              <svg viewBox="0 0 180 180" className="lp-hero-svg" fill="none">
                <circle cx="90" cy="90" r="78" stroke="var(--border)" strokeWidth="1" />
                <circle cx="90" cy="90" r="60" fill="var(--bg2)" />
                <circle cx="90" cy="90" r="44" fill="#e8d9d0" />
                <circle cx="90" cy="90" r="28" fill="var(--warm)" />
                <circle cx="90" cy="90" r="14" fill="var(--deep)" />
                <line x1="12" y1="90" x2="168" y2="90" stroke="var(--warm)" strokeWidth="0.8" strokeDasharray="3 5" opacity="0.45" />
                <line x1="90" y1="12" x2="90" y2="168" stroke="var(--warm)" strokeWidth="0.8" strokeDasharray="3 5" opacity="0.45" />
                <path d="M20 36 L20 20 L36 20" stroke="var(--warm)" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M160 36 L160 20 L144 20" stroke="var(--warm)" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M20 144 L20 160 L36 160" stroke="var(--warm)" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M160 144 L160 160 L144 160" stroke="var(--warm)" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </motion.div>
          </div>
        </section>

        <LandingStory />

        <section className="lp-section lp-section--bg lp-demo-wrap" id="demo" aria-labelledby="demo-title">
          <div className="lp-inner">
            <motion.div
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.65, ease: easeOut }}
            >
              <p className="lp-eyebrow" id="demo-title">
                Demo
              </p>
              <h2 className="lp-title">See it in motion</h2>
              <p className="lp-lede lp-lede-after-title">
                Replace <code className="lp-code">public/demo.mp4</code> whenever you ship a new recording.
              </p>
            </motion.div>
            <DemoVideo />
          </div>
        </section>

        <footer className="site-footer">Know Your Skin · Open source on GitHub</footer>
      </div>
    </>
  )
}
