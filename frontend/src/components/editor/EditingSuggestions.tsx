import { useMemo, useState } from 'react'
import type { EditActionType, MosaicOptions, TelopOptions } from '../../types'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { cn } from '../../lib/utils'

interface SuggestionItem {
  id: string
  startTime: number
  endTime: number
  riskLevel: number
  reason: string
}

interface EditingSuggestionsProps {
  suggestions: SuggestionItem[]
  selectedSuggestion: string | null
  onSelectSuggestion: (id: string | null) => void
  onSeekTo: (time: number) => void
  onApplyAction: (id: string, action: EditActionType, options?: MosaicOptions | TelopOptions | null) => void
  onApplyAll?: () => void
}

const ACTIONS: { label: string; value: EditActionType }[] = [
  { label: 'カット', value: 'cut' },
  { label: 'ミュート', value: 'mute' },
  { label: 'モザイク', value: 'mosaic' },
  { label: 'テロップ', value: 'telop' },
  { label: '対応しない', value: 'skip' },
]

const DEFAULT_MOSAIC: MosaicOptions = {
  x: 0,
  y: 0,
  width: 120,
  height: 120,
  blur_strength: 10,
}

const DEFAULT_TELOP: TelopOptions = {
  text: '',
  x: 40,
  y: 40,
  font_size: 28,
  font_color: '#FFFFFF',
  background_color: null,
}

export function EditingSuggestions({
  suggestions,
  selectedSuggestion,
  onSelectSuggestion,
  onSeekTo,
  onApplyAction,
  onApplyAll,
}: EditingSuggestionsProps) {
  const [actionById, setActionById] = useState<Record<string, EditActionType>>({})
  const [mosaicById, setMosaicById] = useState<Record<string, MosaicOptions>>({})
  const [telopById, setTelopById] = useState<Record<string, TelopOptions>>({})

  const handleActionChange = (id: string, value: EditActionType) => {
    setActionById((prev) => ({ ...prev, [id]: value }))
    if (value === 'mosaic' && !mosaicById[id]) {
      setMosaicById((prev) => ({ ...prev, [id]: DEFAULT_MOSAIC }))
    }
    if (value === 'telop' && !telopById[id]) {
      setTelopById((prev) => ({ ...prev, [id]: DEFAULT_TELOP }))
    }
  }

  const handleApply = (id: string) => {
    const action = actionById[id] ?? 'cut'
    const options =
      action === 'mosaic'
        ? mosaicById[id] ?? DEFAULT_MOSAIC
        : action === 'telop'
        ? telopById[id] ?? DEFAULT_TELOP
        : null
    onApplyAction(id, action, options)
  }

  const suggestionCountLabel = useMemo(
    () => `${suggestions.length}件のリスク箇所が検出されました`,
    [suggestions.length]
  )

  return (
    <div className="flex h-full flex-col">
      <div className="hidden border-b border-border px-4 py-3 md:block">
        <h2 className="text-sm font-semibold">編集提案</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          {suggestionCountLabel}
        </p>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto p-3 md:space-y-3 md:p-4">
        {suggestions.map((suggestion) => {
          const isSelected = selectedSuggestion === suggestion.id
          const action = actionById[suggestion.id] ?? 'cut'
          const mosaicOptions = mosaicById[suggestion.id] ?? DEFAULT_MOSAIC
          const telopOptions = telopById[suggestion.id] ?? DEFAULT_TELOP

          return (
            <Card
              key={suggestion.id}
              className={cn(
                'cursor-pointer gap-3 p-3 transition-all hover:border-primary md:p-4',
                isSelected && 'border-primary bg-primary/5',
              )}
              onClick={() =>
                onSelectSuggestion(isSelected ? null : suggestion.id)
              }
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  onSelectSuggestion(isSelected ? null : suggestion.id)
                }
              }}
            >
              <div className="flex items-start justify-between text-xs">
                <Badge
                  variant={getRiskBadgeVariant(suggestion.riskLevel)}
                  className="text-[10px]"
                >
                  リスク {suggestion.riskLevel}%
                </Badge>
                <span className="text-muted-foreground">
                  {formatTime(suggestion.startTime)} -{' '}
                  {formatTime(suggestion.endTime)}
                </span>
              </div>

              <p className="text-xs text-foreground/90 md:text-sm">
                {suggestion.reason}
              </p>

              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="bg-transparent text-xs"
                  onClick={(event) => {
                    event.stopPropagation()
                    onSeekTo(suggestion.startTime)
                  }}
                >
                  プレビュー
                </Button>
                <Button
                  size="sm"
                  className="text-xs"
                  onClick={(event) => {
                    event.stopPropagation()
                    handleApply(suggestion.id)
                  }}
                >
                  適用
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {ACTIONS.map((item) => (
                  <Button
                    key={item.value}
                    type="button"
                    size="sm"
                    variant="outline"
                    className={cn(
                      'bg-transparent text-xs',
                      action === item.value &&
                        'border-primary text-primary hover:bg-primary/10',
                    )}
                    onClick={(event) => {
                      event.stopPropagation()
                      handleActionChange(suggestion.id, item.value)
                    }}
                  >
                    {item.label}
                  </Button>
                ))}
              </div>

              {action === 'mosaic' && (
                <div
                  className="grid gap-2 text-xs"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="grid grid-cols-2 gap-2">
                    <label className="grid gap-1">
                      X
                      <input
                        type="number"
                        min={0}
                        value={mosaicOptions.x}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              x: Number(event.target.value),
                            },
                          }))
                        }
                      />
                    </label>
                    <label className="grid gap-1">
                      Y
                      <input
                        type="number"
                        min={0}
                        value={mosaicOptions.y}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              y: Number(event.target.value),
                            },
                          }))
                        }
                      />
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="grid gap-1">
                      幅
                      <input
                        type="number"
                        min={1}
                        value={mosaicOptions.width}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              width: Number(event.target.value),
                            },
                          }))
                        }
                      />
                    </label>
                    <label className="grid gap-1">
                      高さ
                      <input
                        type="number"
                        min={1}
                        value={mosaicOptions.height}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              height: Number(event.target.value),
                            },
                          }))
                        }
                      />
                    </label>
                  </div>
                  <label className="grid gap-1">
                    強度
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={mosaicOptions.blur_strength}
                      className="w-full rounded-md border border-input bg-background px-2 py-1"
                      onChange={(event) =>
                        setMosaicById((prev) => ({
                          ...prev,
                          [suggestion.id]: {
                            ...mosaicOptions,
                            blur_strength: Number(event.target.value),
                          },
                        }))
                      }
                    />
                  </label>
                </div>
              )}

              {action === 'telop' && (
                <div
                  className="grid gap-2 text-xs"
                  onClick={(e) => e.stopPropagation()}
                >
                  <label className="grid gap-1">
                    テキスト
                    <input
                      type="text"
                      value={telopOptions.text}
                      className="w-full rounded-md border border-input bg-background px-2 py-1"
                      onChange={(event) =>
                        setTelopById((prev) => ({
                          ...prev,
                          [suggestion.id]: {
                            ...telopOptions,
                            text: event.target.value,
                          },
                        }))
                      }
                    />
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="grid gap-1">
                      X
                      <input
                        type="number"
                        min={0}
                        value={telopOptions.x}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setTelopById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...telopOptions,
                              x: Number(event.target.value),
                            },
                          }))
                        }
                      />
                    </label>
                    <label className="grid gap-1">
                      Y
                      <input
                        type="number"
                        min={0}
                        value={telopOptions.y}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setTelopById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...telopOptions,
                              y: Number(event.target.value),
                            },
                          }))
                        }
                      />
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="grid gap-1">
                      フォント
                      <input
                        type="number"
                        min={10}
                        max={200}
                        value={telopOptions.font_size}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setTelopById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...telopOptions,
                              font_size: Number(event.target.value),
                            },
                          }))
                        }
                      />
                    </label>
                    <label className="grid gap-1">
                      文字色
                      <input
                        type="text"
                        value={telopOptions.font_color}
                        className="w-full rounded-md border border-input bg-background px-2 py-1"
                        onChange={(event) =>
                          setTelopById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...telopOptions,
                              font_color: event.target.value,
                            },
                          }))
                        }
                      />
                    </label>
                  </div>
                  <label className="grid gap-1">
                    背景色
                    <input
                      type="text"
                      value={telopOptions.background_color ?? ''}
                      className="w-full rounded-md border border-input bg-background px-2 py-1"
                      onChange={(event) =>
                        setTelopById((prev) => ({
                          ...prev,
                          [suggestion.id]: {
                            ...telopOptions,
                            background_color: event.target.value || null,
                          },
                        }))
                      }
                    />
                  </label>
                </div>
              )}
            </Card>
          )
        })}
      </div>

      <div className="border-t border-border p-3 md:p-4">
        <Button className="w-full text-xs md:text-sm" onClick={onApplyAll}>
          すべての提案を適用
        </Button>
      </div>
    </div>
  )
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getRiskBadgeVariant(level: number) {
  if (level >= 70) return 'destructive'
  if (level >= 30) return 'warning'
  return 'success'
}
