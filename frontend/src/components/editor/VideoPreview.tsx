import { useEffect, useRef, type RefObject } from 'react'
import './VideoPreview.css'

interface CutRange {
  start: number
  end: number
}

interface VideoPreviewProps {
  currentTime: number
  isPlaying: boolean
  onTimeUpdate: (time: number) => void
  cutRanges: CutRange[]
  videoUrl?: string | null
  onDurationChange?: (duration: number) => void
  videoRef?: RefObject<HTMLVideoElement>
}

export function VideoPreview({
  currentTime,
  isPlaying,
  onTimeUpdate,
  cutRanges,
  videoUrl,
  onDurationChange,
  videoRef,
}: VideoPreviewProps) {
  const localRef = useRef<HTMLVideoElement>(null)
  const resolvedRef = videoRef ?? localRef

  useEffect(() => {
    if (!resolvedRef.current) {
      return
    }
    if (Math.abs(resolvedRef.current.currentTime - currentTime) > 0.1) {
      resolvedRef.current.currentTime = currentTime
    }
  }, [currentTime, resolvedRef])

  useEffect(() => {
    if (!resolvedRef.current) {
      return
    }
    if (isPlaying) {
      resolvedRef.current.play().catch(() => undefined)
    } else {
      resolvedRef.current.pause()
    }
  }, [isPlaying, resolvedRef])

  const handleVideoTimeUpdate = () => {
    if (resolvedRef.current) {
      onTimeUpdate(resolvedRef.current.currentTime)
    }
  }

  const currentCutRange = cutRanges.find(
    (range) => currentTime >= range.start && currentTime <= range.end
  )

  return (
    <div className="video-preview">
      <div className="video-preview__frame">
        {videoUrl ? (
          <video
            ref={resolvedRef}
            className="video-preview__video"
            onTimeUpdate={handleVideoTimeUpdate}
            onLoadedMetadata={() => {
              if (resolvedRef.current && onDurationChange) {
                onDurationChange(resolvedRef.current.duration)
              }
            }}
          >
            <source src={videoUrl} type="video/mp4" />
            お使いのブラウザは動画タグをサポートしていません。
          </video>
        ) : (
          <div className="video-preview__placeholder">
            <div className="video-preview__placeholder-icon">🎬</div>
            <p className="video-preview__placeholder-title">動画プレビューエリア</p>
            <p className="video-preview__placeholder-subtitle">
              動画をアップロードするとプレビューが表示されます
            </p>
          </div>
        )}

        {currentCutRange && (
          <div className="video-preview__cut-overlay">
            <div className="video-preview__cut-title">この部分はカットされます</div>
            <div className="video-preview__cut-range">
              {formatTime(currentCutRange.start)} - {formatTime(currentCutRange.end)}
            </div>
          </div>
        )}

        <div className="video-preview__time">{formatTime(currentTime)}</div>
      </div>
    </div>
  )
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 10)
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`
}
