import { motion } from 'framer-motion'

type Props = {
  onViewDemo: () => void
  onOverview: () => void
}

export function SiteHeader({ onViewDemo, onOverview }: Props) {
  return (
    <motion.header
      className="site-header"
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="site-header-inner">
        <button type="button" className="wordmark-link" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <span className="wordmark-serif">Know Your Skin</span>
          <span className="wordmark-sub">AI skincare analysis</span>
        </button>
        <nav className="site-header-nav">
          <button type="button" className="btn-ghost" onClick={onOverview}>
            How it works
          </button>
          <button type="button" className="btn-primary" onClick={onViewDemo}>
            View demo
          </button>
        </nav>
      </div>
    </motion.header>
  )
}
