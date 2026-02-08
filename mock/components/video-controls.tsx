"use client"

import { Button } from "./ui/button"
import { Slider } from "./ui/slider"
import { Play, Pause, SkipBack, SkipForward, Volume2, Maximize } from "lucide-react"

interface VideoControlsProps {
  currentTime: number
  duration: number
  isPlaying: boolean
  onPlayPause: () => void
  onSeek: (time: number) => void
}

export function VideoControls({ currentTime, duration, isPlaying, onPlayPause, onSeek }: VideoControlsProps) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => onSeek(Math.max(0, currentTime - 5))}>
          <SkipBack className="h-4 w-4" />
        </Button>
        <Button variant="default" size="icon" onClick={onPlayPause}>
          {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
        </Button>
        <Button variant="ghost" size="icon" onClick={() => onSeek(Math.min(duration, currentTime + 5))}>
          <SkipForward className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex flex-1 items-center gap-3">
        <span className="text-sm tabular-nums text-foreground">{formatTime(currentTime)}</span>
        <Slider
          value={[currentTime]}
          max={duration}
          step={0.1}
          onValueChange={([value]) => onSeek(value)}
          className="flex-1"
        />
        <span className="text-sm tabular-nums text-muted-foreground">{formatTime(duration)}</span>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon">
          <Volume2 className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon">
          <Maximize className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
