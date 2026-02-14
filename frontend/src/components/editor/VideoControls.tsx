import { useMemo, useState } from 'react'
import './VideoControls.css'

interface VideoControlsProps {
  currentTime: number
  duration: number
  isPlaying: boolean
  onPlayPause: () => void
  onSeek: (time: number) => void
  onToggleMute?: (muted: boolean) => void
  onToggleFullscreen?: (fullscreen: boolean) => void
}

export function VideoControls({
  currentTime,
  duration,
  isPlaying,
  onPlayPause,
  onSeek,
  onToggleMute,
  onToggleFullscreen,
}: VideoControlsProps) {
  const [muted, setMuted] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)

  const formattedCurrent = useMemo(() => formatTime(currentTime), [currentTime])
  const formattedDuration = useMemo(() => formatTime(duration), [duration])

  const handleSeek = (value: number) => {
    const clamped = Math.min(Math.max(value, 0), duration || 0)
    onSeek(clamped)
  }

  const handleSkip = (delta: number) => {
    handleSeek(currentTime + delta)
  }

  const toggleMute = () => {
    const next = !muted
    setMuted(next)
    onToggleMute?.(next)
  }

  const toggleFullscreen = () => {
    const next = !fullscreen
    setFullscreen(next)
    onToggleFullscreen?.(next)
  }

  return (
    <div className="video-controls">
      <div className="video-controls__buttons">
        <button
          type="button"
          className="video-controls__button"
          onClick={() => handleSkip(-5)}
          aria-label="5 seconds back"
        >
          -5
        </button>
        <button
          type="button"
          className="video-controls__button video-controls__button--primary"
          onClick={onPlayPause}
          aria-label="Play or pause"
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button
          type="button"
          className="video-controls__button"
          onClick={() => handleSkip(5)}
          aria-label="5 seconds forward"
        >
          +5
        </button>
      </div>

      <div className="video-controls__timeline">
        <span className="video-controls__time">{formattedCurrent}</span>
        <input
          className="video-controls__range"
          type="range"
          min={0}
          max={duration || 0}
          step={0.1}
          value={Math.min(currentTime, duration || 0)}
          onChange={(event) => handleSeek(Number(event.target.value))}
        />
        <span className="video-controls__time">{formattedDuration}</span>
      </div>

      <div className="video-controls__buttons">
        <button
          type="button"
          className="video-controls__button"
          onClick={toggleMute}
          aria-label="Toggle mute"
        >
          {muted ? 'Unmute' : 'Mute'}
        </button>
        <button
          type="button"
          className="video-controls__button"
          onClick={toggleFullscreen}
          aria-label="Toggle fullscreen"
        >
          {fullscreen ? 'Exit' : 'Full'}
        </button>
      </div>
    </div>
  )
}

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds)) {
    return '0:00'
  }
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
