import { motion } from 'framer-motion'
import type { ReactNode } from 'react'

const easeOut = [0.22, 1, 0.36, 1] as const

const reveal = {
  hidden: { opacity: 0, y: 36 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.72, ease: easeOut },
  },
}

const stagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.1, delayChildren: 0.08 },
  },
}

const item = {
  hidden: { opacity: 0, y: 22 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: easeOut } },
}

const line = {
  hidden: { scaleX: 0, originX: 0 },
  show: { scaleX: 1, transition: { duration: 0.85, ease: easeOut } },
}

function SectionShell({ id, className, children }: { id?: string; className?: string; children: ReactNode }) {
  return (
    <motion.section
      id={id}
      className={`lp-section ${className ?? ''}`}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.22 }}
      variants={reveal}
    >
      {children}
    </motion.section>
  )
}

export function LandingStory() {
  return (
    <>
      <SectionShell id="problem" className="lp-section--cream">
        <div className="lp-accent" aria-hidden />
        <div className="lp-inner lp-split">
          <div>
            <p className="lp-eyebrow">The problem</p>
            <h2 className="lp-title">
              Generic advice doesn&apos;t <em>fit</em> anyone.
            </h2>
            <motion.span className="lp-rule" variants={line} initial="hidden" whileInView="show" viewport={{ once: true }} />
            <p className="lp-lede">
              No two customers share the same skin — yet most brands offer the same recommendations to all of them.
            </p>
          </div>
          <motion.div className="lp-bars" variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.4 }}>
            {[28, 44, 60, 40, 52, 32, 56, 36].map((h, i) => (
              <motion.span
                key={i}
                className="lp-bar"
                variants={item}
                style={{ height: h, opacity: [0.3, 0.5, 0.7, 0.45, 0.6, 0.35, 0.65, 0.4][i] }}
              />
            ))}
          </motion.div>
        </div>
      </SectionShell>

      <SectionShell className="lp-section--deep">
        <div className="lp-accent lp-accent--on-dark" aria-hidden />
        <div className="lp-inner">
          <p className="lp-eyebrow lp-eyebrow--muted">The solution</p>
          <h2 className="lp-title lp-title--light">
            AI skin analysis built for <em>any</em> skincare brand.
          </h2>
          <motion.span className="lp-rule lp-rule--soft" variants={line} initial="hidden" whileInView="show" viewport={{ once: true }} />
          <p className="lp-lede lp-lede--muted">
            Upload your product catalog. Every customer gets a personalised routine — matched to their actual skin.
          </p>
        </div>
      </SectionShell>

      <SectionShell id="process" className="lp-section--bg">
        <div className="lp-inner lp-center">
          <p className="lp-eyebrow">The process</p>
          <h2 className="lp-title lp-title--center">Four steps. One photo.</h2>
          <motion.div className="lp-flow" variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.25 }}>
            {[
              {
                t: 'Photo',
                s: 'Customer uploads a skin image',
                icon: (
                  <svg viewBox="0 0 30 30" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
                    <path d="M28 22a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2h4l2.5-3.5h7L20 8h4a2 2 0 0 1 2 2z" />
                    <circle cx="15" cy="16" r="4.5" />
                  </svg>
                ),
              },
              {
                t: 'AI reads',
                s: 'Derm Foundation analysis',
                icon: (
                  <svg viewBox="0 0 30 30" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
                    <circle cx="15" cy="6" r="2.5" />
                    <circle cx="6" cy="22" r="2.5" />
                    <circle cx="24" cy="22" r="2.5" />
                    <circle cx="15" cy="16" r="2" fill="currentColor" stroke="none" />
                    <line x1="15" y1="8.5" x2="15" y2="14" />
                    <line x1="15" y1="14" x2="7.5" y2="20" />
                    <line x1="15" y1="14" x2="22.5" y2="20" />
                    <line x1="8.5" y1="22" x2="21.5" y2="22" />
                  </svg>
                ),
              },
              {
                t: 'Detects',
                s: 'Six skin dimensions scored',
                icon: (
                  <svg viewBox="0 0 30 30" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
                    <rect x="4" y="4" width="9" height="9" rx="1.5" />
                    <rect x="17" y="4" width="9" height="9" rx="1.5" />
                    <rect x="4" y="17" width="9" height="9" rx="1.5" />
                    <rect x="17" y="17" width="9" height="9" rx="1.5" />
                  </svg>
                ),
              },
              {
                t: 'Routine',
                s: 'Your products, matched',
                icon: (
                  <svg viewBox="0 0 30 30" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
                    <path d="M15 4 L16.5 12 L24 15 L16.5 18 L15 26 L13.5 18 L6 15 L13.5 12 Z" />
                  </svg>
                ),
              },
            ].map((step) => (
              <motion.div key={step.t} className="lp-flow-node" variants={item}>
                <div className="lp-flow-icon">{step.icon}</div>
                <span className="lp-flow-title">{step.t}</span>
                <span className="lp-flow-sub">{step.s}</span>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </SectionShell>

      <SectionShell className="lp-section--cream">
        <div className="lp-inner lp-grid-2">
          <div>
            <p className="lp-eyebrow">Step 01 — Upload</p>
            <h2 className="lp-title">
              The customer takes a <em>photo.</em>
            </h2>
            <p className="lp-note">
              Single image or multi-angle session — the system averages across uploads for higher accuracy.
            </p>
          </div>
          <motion.div className="lp-visual-ring" initial={{ opacity: 0, scale: 0.92 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ duration: 0.65, ease: easeOut }}>
            <svg viewBox="0 0 80 80" width="88" height="88" fill="none" stroke="var(--deep)" strokeWidth="1.5" aria-hidden>
              <path d="M74 60a5 5 0 0 1-5 5H11a5 5 0 0 1-5-5V26a5 5 0 0 1 5-5h11L28 13h24l6 8h5a5 5 0 0 1 5 5z" />
              <circle cx="40" cy="42" r="13" />
              <circle cx="40" cy="42" r="8" stroke="var(--warm)" />
              <circle cx="62" cy="28" r="3" fill="var(--warm)" stroke="none" />
            </svg>
          </motion.div>
        </div>
      </SectionShell>

      <SectionShell className="lp-section--bg">
        <div className="lp-inner">
          <p className="lp-eyebrow">Step 02 — AI reads</p>
          <h2 className="lp-title">
            Google <em>Derm Foundation</em> reads their skin.
          </h2>
          <p className="lp-lede" style={{ maxWidth: 560 }}>
            A medical-grade dermatology model generates a 6,144-dimensional skin signature — the same class of models used in clinical research.
          </p>
          <div className="lp-badge">
            <span className="lp-badge-dot" aria-hidden />
            <span>Powered by Google Derm Foundation · Vertex AI</span>
          </div>
          <motion.div className="lp-embed-row" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: 0.12, duration: 0.6 }}>
            <span className="lp-embed-label">Skin signature</span>
            <div className="lp-embed-dots" aria-hidden>
              {Array.from({ length: 48 }, (_, i) => (
                <span key={i} className="lp-embed-dot" />
              ))}
            </div>
          </motion.div>
        </div>
      </SectionShell>

      <SectionShell className="lp-section--bg2">
        <div className="lp-inner">
          <p className="lp-eyebrow">Step 03 — Detected</p>
          <h2 className="lp-title">
            Six dimensions. One <em>photo.</em>
          </h2>
          <motion.div className="lp-detect-grid" variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.15 }}>
            {[
              { label: 'Skin type', val: 'Oily · Dry · Combo · Normal', path: 'M12 2C12 2 5 10.5 5 15a7 7 0 0 0 14 0C19 10.5 12 2 12 2Z' },
              { label: 'Concerns', val: 'Acne · Pigment · Redness…', path: '', extra: 'alert' },
              { label: 'Skin tone', val: 'Fitzpatrick · Monk scale', path: '', extra: 'tone' },
              { label: 'Texture', val: 'Smooth · Rough · Uneven', path: 'M12 2L2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5' },
              { label: 'Aging signs', val: 'Fine lines · Volume loss', path: '', extra: 'clock' },
              { label: 'Skin age', val: 'Estimated biological age', path: '', extra: 'cal' },
            ].map((c) => (
              <motion.div key={c.label} className="lp-detect-card" variants={item}>
                <div className="lp-detect-icon" aria-hidden>
                  {c.extra === 'alert' && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <circle cx="12" cy="16" r="0.5" fill="currentColor" />
                    </svg>
                  )}
                  {c.extra === 'tone' && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <circle cx="12" cy="12" r="9" />
                      <circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" opacity="0.45" />
                    </svg>
                  )}
                  {c.extra === 'clock' && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                  )}
                  {c.extra === 'cal' && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <rect x="3" y="4" width="18" height="18" rx="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                  )}
                  {!c.extra && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d={c.path} />
                    </svg>
                  )}
                </div>
                <div>
                  <div className="lp-detect-label">{c.label}</div>
                  <div className="lp-detect-val">{c.val}</div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </SectionShell>

      <SectionShell className="lp-section--darkest">
        <div className="lp-accent lp-accent--warm" aria-hidden />
        <div className="lp-inner">
          <p className="lp-eyebrow lp-eyebrow--muted">Step 04 — Output</p>
          <h2 className="lp-title lp-title--light">
            A personalised routine from <em>your</em> catalog.
          </h2>
          <motion.div className="lp-routine-grid" variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.2 }}>
            {[
              { tag: 'Cleanser', name: 'Matched to skin type and concerns' },
              { tag: 'Treatment', name: 'Targeted to the active concern' },
              { tag: 'Moisturiser', name: 'Supports barrier and texture' },
              { tag: 'SPF', name: 'Tone-appropriate sun protection' },
            ].map((r) => (
              <motion.div key={r.tag} className="lp-routine-card" variants={item}>
                <span className="lp-routine-tag">{r.tag}</span>
                <p className="lp-routine-name">{r.name}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </SectionShell>

      <SectionShell className="lp-section--bg">
        <div className="lp-inner">
          <p className="lp-eyebrow">For brands</p>
          <h2 className="lp-title">
            Plug in. <em>Power up.</em>
          </h2>
          <motion.span className="lp-rule" variants={line} initial="hidden" whileInView="show" viewport={{ once: true }} />
          <motion.ul className="lp-brand-list" variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.2 }}>
            {[
              {
                title: 'Upload your product catalog',
                text: 'Concern-to-product mapping is auto-generated. No manual tagging.',
              },
              {
                title: 'Embed in your app or site',
                text: 'REST API, Docker-ready. Live in days, not months.',
              },
              {
                title: 'Your brand, fully customisable',
                text: 'Copy, tone, product copy — white-label ready.',
              },
            ].map((b) => (
              <motion.li key={b.title} className="lp-brand-item" variants={item}>
                <span className="lp-brand-dot" aria-hidden />
                <div>
                  <strong>{b.title}</strong>
                  <span>{b.text}</span>
                </div>
              </motion.li>
            ))}
          </motion.ul>
        </div>
      </SectionShell>

      <SectionShell id="opensource" className="lp-section--deep">
        <div className="lp-accent lp-accent--on-dark" aria-hidden />
        <div className="lp-inner">
          <p className="lp-eyebrow lp-eyebrow--muted">Open source</p>
          <h2 className="lp-title lp-title--light">
            Built in public. <em>Open</em> to collaborate.
          </h2>
          <motion.span className="lp-rule lp-rule--soft" variants={line} initial="hidden" whileInView="show" viewport={{ once: true }} />
          <motion.div className="lp-cta-row" variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true }}>
            <motion.a className="lp-cta" href="https://github.com/musadiqg/know-your-skin" target="_blank" rel="noreferrer" variants={item}>
              <span className="lp-cta-label">Repository</span>
              <span className="lp-cta-main">github.com/musadiqg/know-your-skin</span>
              <span className="lp-cta-sub">Source, training scripts, architecture</span>
            </motion.a>
            <motion.a className="lp-cta" href="https://linkedin.com/in/musadiqgilal" target="_blank" rel="noreferrer" variants={item}>
              <span className="lp-cta-label">Connect</span>
              <span className="lp-cta-main">linkedin.com/in/musadiqgilal</span>
              <span className="lp-cta-sub">Collaborations and conversations</span>
            </motion.a>
          </motion.div>
        </div>
      </SectionShell>
    </>
  )
}
