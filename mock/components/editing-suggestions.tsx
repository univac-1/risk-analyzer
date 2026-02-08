"use client"

import { Button } from "./ui/button"
import { Card } from "./ui/card"
import { Badge } from "./ui/badge"
import { AlertTriangle, Scissors, Eye } from "lucide-react"
import { cn } from "@/lib/utils"

interface Suggestion {
  id: number
  startTime: number
  endTime: number
  riskLevel: number
  reason: string
}

interface EditingSuggestionsProps {
  suggestions: Suggestion[]
  selectedSuggestion: number | null
  onSelectSuggestion: (id: number | null) => void
  onApplyCut: (startTime: number, endTime: number) => void
  onSeekTo: (time: number) => void
}

export function EditingSuggestions({
  suggestions,
  selectedSuggestion,
  onSelectSuggestion,
  onApplyCut,
  onSeekTo,
}: EditingSuggestionsProps) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const getRiskColor = (level: number) => {
    if (level >= 70) return "destructive"
    if (level >= 30) return "warning"
    return "success"
  }

  return (
    <div className="flex h-full flex-col">
      <div className="hidden border-b border-border p-4 md:block">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <AlertTriangle className="h-4 w-4 text-warning" />
          編集提案
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">{suggestions.length}件の高リスク箇所が検出されました</p>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto p-3 md:space-y-3 md:p-4">
        {suggestions.map((suggestion) => (
          <Card
            key={suggestion.id}
            className={cn(
              "cursor-pointer p-3 transition-all hover:border-primary md:p-4",
              selectedSuggestion === suggestion.id && "border-primary bg-primary/5",
            )}
            onClick={() => onSelectSuggestion(selectedSuggestion === suggestion.id ? null : suggestion.id)}
          >
            <div className="mb-2 flex items-start justify-between md:mb-3">
              <div>
                <Badge variant={getRiskColor(suggestion.riskLevel)} className="text-xs">
                  リスク {suggestion.riskLevel}%
                </Badge>
              </div>
              <span className="text-xs text-muted-foreground">
                {formatTime(suggestion.startTime)} - {formatTime(suggestion.endTime)}
              </span>
            </div>

            <p className="mb-2 text-xs text-foreground md:mb-3 md:text-sm">{suggestion.reason}</p>

            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="flex-1 bg-transparent text-xs"
                onClick={(e) => {
                  e.stopPropagation()
                  onSeekTo(suggestion.startTime)
                }}
              >
                <Eye className="mr-1 h-3 w-3 md:mr-2" />
                プレビュー
              </Button>
              <Button
                size="sm"
                className="flex-1 text-xs"
                onClick={(e) => {
                  e.stopPropagation()
                  onApplyCut(suggestion.startTime, suggestion.endTime)
                }}
              >
                <Scissors className="mr-1 h-3 w-3 md:mr-2" />
                カット適用
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <div className="border-t border-border p-3 md:p-4">
        <Button className="w-full text-xs md:text-sm" size="sm">
          すべての提案を適用
        </Button>
      </div>
    </div>
  )
}
