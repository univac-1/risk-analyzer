"use client"

import { useEffect, useRef } from "react"

interface VideoPreviewProps {
  currentTime: number
  isPlaying: boolean
  onTimeUpdate: (time: number) => void
  cutRanges: Array<{ start: number; end: number }>
  videoUrl?: string
}

export function VideoPreview({ currentTime, isPlaying, onTimeUpdate, cutRanges, videoUrl }: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current && Math.abs(videoRef.current.currentTime - currentTime) > 0.1) {
      videoRef.current.currentTime = currentTime
    }
  }, [currentTime])

  useEffect(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.play().catch((e) => console.error("Play error:", e))
      } else {
        videoRef.current.pause()
      }
    }
  }, [isPlaying])

  const handleVideoTimeUpdate = () => {
    if (videoRef.current) {
      onTimeUpdate(videoRef.current.currentTime)
    }
  }

  const isInCutRange = (time: number) => {
    return cutRanges.some((range) => time >= range.start && time <= range.end)
  }

  return (
    <div className="flex h-full items-center justify-center">
      <div className="relative aspect-video w-full max-w-4xl overflow-hidden rounded-lg bg-black shadow-2xl">
        {videoUrl ? (
          <video
            ref={videoRef}
            className="h-full w-full"
            onTimeUpdate={handleVideoTimeUpdate}
            onLoadedMetadata={() => {
              if (videoRef.current) {
                onTimeUpdate(0)
              }
            }}
          >
            <source src={videoUrl} type="video/mp4" />
            お使いのブラウザは動画タグをサポートしていません。
          </video>
        ) : (
          <div className="flex h-full items-center justify-center bg-gradient-to-br from-muted/20 to-muted/5">
            <div className="text-center">
              <div className="mb-4 text-6xl">🎬</div>
              <p className="mb-2 text-lg font-semibold text-foreground">動画プレビューエリア (MOCK)</p>
              <div className="mb-4 flex items-center justify-center gap-2">
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                <p className="font-mono text-sm text-muted-foreground">再生位置: {formatTime(currentTime)}</p>
              </div>
              <p className="text-xs text-muted-foreground">実際の動画をアップロードすると、ここに表示されます</p>
              <div className="mt-4 rounded-lg border border-warning/50 bg-warning/10 px-4 py-2 text-xs text-warning">
                現在はMOCKデータで動作確認中です
              </div>
            </div>
          </div>
        )}

        {/* カット範囲のオーバーレイ */}
        {isInCutRange(currentTime) && (
          <div className="absolute inset-0 flex items-center justify-center bg-destructive/80">
            <div className="text-center">
              <p className="text-lg font-semibold text-destructive-foreground">この部分はカットされます</p>
              <p className="mt-1 text-sm text-destructive-foreground/80">
                {formatTime(cutRanges.find((r) => currentTime >= r.start && currentTime <= r.end)?.start || 0)} -{" "}
                {formatTime(cutRanges.find((r) => currentTime >= r.start && currentTime <= r.end)?.end || 0)}
              </p>
            </div>
          </div>
        )}

        {/* 時刻表示オーバーレイ */}
        <div className="absolute bottom-4 right-4 rounded bg-black/70 px-3 py-1.5 font-mono text-sm text-white backdrop-blur-sm">
          {formatTime(currentTime)}
        </div>
      </div>
    </div>
  )
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 10)
  return `${mins}:${secs.toString().padStart(2, "0")}.${ms}`
}
