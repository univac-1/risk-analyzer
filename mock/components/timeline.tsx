"use client"

import type React from "react"

import { useRef, useState } from "react"
import { cn } from "@/lib/utils"

interface TimelineProps {
  duration: number
  currentTime: number
  onSeek: (time: number) => void
  cutRanges: Array<{ start: number; end: number }>
  suggestions: Array<{
    id: number
    startTime: number
    endTime: number
    riskLevel: number
  }>
  selectedSuggestion: number | null
  onSelectSuggestion: (id: number | null) => void
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

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true)
    updateTime(e)
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDragging) {
      updateTime(e)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const updateTime = (e: React.MouseEvent<HTMLDivElement>) => {
    if (timelineRef.current) {
      const rect = timelineRef.current.getBoundingClientRect()
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
      const time = (x / rect.width) * duration
      onSeek(time)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <div className="absolute bottom-0 left-0 right-0">
      {/* タイムマーカー */}
      <div className="mb-2 flex justify-between px-1 text-xs text-muted-foreground">
        {Array.from({ length: 10 }).map((_, i) => (
          <span key={i}>{formatTime((duration / 9) * i)}</span>
        ))}
      </div>

      {/* タイムラインバー */}
      <div
        ref={timelineRef}
        className="relative h-12 cursor-pointer rounded bg-muted/30"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* カット範囲の表示 */}
        {cutRanges.map((range, index) => (
          <div
            key={index}
            className="absolute top-0 h-full bg-destructive/40"
            style={{
              left: `${(range.start / duration) * 100}%`,
              width: `${((range.end - range.start) / duration) * 100}%`,
            }}
          />
        ))}

        {/* 提案範囲の表示 */}
        {suggestions.map((suggestion) => (
          <div
            key={suggestion.id}
            className={cn(
              "absolute top-0 h-full cursor-pointer border-2 transition-all",
              selectedSuggestion === suggestion.id
                ? "border-primary bg-warning/60"
                : "border-warning/50 bg-warning/30 hover:bg-warning/50",
            )}
            style={{
              left: `${(suggestion.startTime / duration) * 100}%`,
              width: `${((suggestion.endTime - suggestion.startTime) / duration) * 100}%`,
            }}
            onClick={(e) => {
              e.stopPropagation()
              onSelectSuggestion(selectedSuggestion === suggestion.id ? null : suggestion.id)
            }}
          />
        ))}

        {/* 現在時刻のインジケーター */}
        <div
          className="absolute top-0 h-full w-0.5 bg-primary shadow-lg"
          style={{ left: `${(currentTime / duration) * 100}%` }}
        >
          <div className="absolute -top-1 left-1/2 h-3 w-3 -translate-x-1/2 rounded-full bg-primary shadow-lg" />
          <div className="absolute -bottom-1 left-1/2 h-3 w-3 -translate-x-1/2 rounded-full bg-primary shadow-lg" />
        </div>
      </div>
    </div>
  )
}
