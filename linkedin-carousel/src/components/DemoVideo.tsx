import { motion } from 'framer-motion'
import { useCallback, useRef, useState } from 'react'

const DEMO_SRC = `${import.meta.env.BASE_URL}demo.mp4`

export function DemoVideo() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(false)

  const toggle = useCallback(() => {
    const v = videoRef.current
    if (!v) return
    if (v.paused) {
      void v.play()
      setPlaying(true)
    } else {
      v.pause()
      setPlaying(false)
    }
  }, [])

  return (
    <motion.div
      className="demo-shell"
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="demo-chrome">
        <div className="demo-chrome-top">
          <span className="demo-dot" />
          <span className="demo-dot" />
          <span className="demo-dot" />
          <span className="demo-title">Product demo</span>
        </div>
        <div className="demo-stage">
          <video
            ref={videoRef}
            className="demo-video"
            src={DEMO_SRC}
            playsInline
            controls={false}
            preload="metadata"
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={() => setPlaying(false)}
          />
          <button type="button" className="demo-play-overlay" onClick={toggle} aria-label={playing ? 'Pause' : 'Play'}>
            {!playing && (
              <span className="demo-play-icon" aria-hidden>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </span>
            )}
          </button>
          <div className="demo-bottom-bar">
            <button type="button" className="demo-mini-btn" onClick={toggle} aria-label={playing ? 'Pause' : 'Play'}>
              {playing ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
