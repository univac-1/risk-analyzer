import { useRef, useState } from 'react'
import './Timeline.css'

interface TimeRange {
  start: number
  end: number
}

interface SuggestionRange {
  id: string
  startTime: number
  endTime: number
  riskLevel: number
}

interface TimelineProps {
  duration: number
  currentTime: number
  onSeek: (time: number) => void
  cutRanges: TimeRange[]
  suggestions: SuggestionRange[]
  selectedSuggestion: string | null
  onSelectSuggestion: (id: string | null) => void
}

export function Timeline({
  duration,
  currentTime,
  onSeek,
  cutRanges,
  suggestions,
  selectedSuggestion,
  onSelectSuggestion,
}: TimelineProps) {
  const timelineRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const safeDuration = duration || 1

  const updateTime = (clientX: number) => {
    if (!timelineRef.current) {
      return
    }
    const rect = timelineRef.current.getBoundingClientRect()
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width))
    const time = (x / rect.width) * safeDuration
    onSeek(time)
  }

  const handleMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true)
    updateTime(event.clientX)
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (isDragging) {
      updateTime(event.clientX)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  return (
    <div className="timeline">
      <div className="timeline__markers">
        {Array.from({ length: 10 }).map((_, index) => (
          <span key={index}>{formatTime((safeDuration / 9) * index)}</span>
        ))}
      </div>

      <div
        ref={timelineRef}
        className="timeline__bar"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {cutRanges.map((range, index) => (
          <div
            key={`cut-${index}`}
            className="timeline__cut"
            style={{
              left: `${(range.start / safeDuration) * 100}%`,
              width: `${((range.end - range.start) / safeDuration) * 100}%`,
            }}
          />
        ))}

        {suggestions.map((suggestion) => {
          const isSelected = selectedSuggestion === suggestion.id
          return (
            <button
              type="button"
              key={suggestion.id}
              className={`timeline__suggestion${isSelected ? ' timeline__suggestion--selected' : ''}`}
              style={{
                left: `${(suggestion.startTime / safeDuration) * 100}%`,
                width: `${((suggestion.endTime - suggestion.startTime) / safeDuration) * 100}%`,
              }}
              onMouseDown={(event) => {
                event.stopPropagation()
              }}
              onClick={(event) => {
                event.stopPropagation()
                onSelectSuggestion(isSelected ? null : suggestion.id)
              }}
            />
          )
        })}

        <div
          className="timeline__cursor"
          style={{ left: `${(currentTime / safeDuration) * 100}%` }}
        >
          <span className="timeline__handle" />
          <span className="timeline__handle timeline__handle--bottom" />
        </div>
      </div>
    </div>
  )
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
