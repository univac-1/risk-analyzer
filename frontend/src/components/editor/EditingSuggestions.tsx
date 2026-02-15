import { useMemo, useState } from 'react'
import type { EditActionType, MosaicOptions, TelopOptions } from '../../types'
import './EditingSuggestions.css'

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

  const readNumberInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = event.target
    if (value === '') {
      return null
    }
    const next = Number(value)
    return Number.isNaN(next) ? null : next
  }

  const clampNumber = (value: number, min: number, max?: number) => {
    const clampedMin = Math.max(value, min)
    if (max === undefined) {
      return clampedMin
    }
    return Math.min(clampedMin, max)
  }

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
    const telopText =
      action === 'telop' ? (telopById[id]?.text ?? DEFAULT_TELOP.text) : ''
    const options =
      action === 'mosaic'
        ? mosaicById[id] ?? DEFAULT_MOSAIC
        : action === 'telop'
        ? telopById[id] ?? DEFAULT_TELOP
        : null
    if (action === 'telop' && !telopText.trim()) {
      return
    }
    onApplyAction(id, action, options)
  }

  const suggestionCountLabel = useMemo(
    () => `${suggestions.length}件の高リスク箇所が検出されました`,
    [suggestions.length]
  )

  return (
    <div className="editing-suggestions">
      <div className="editing-suggestions__header">
        <div>
          <h2>編集提案</h2>
          <p>{suggestionCountLabel}</p>
        </div>
      </div>

      <div className="editing-suggestions__list">
        {suggestions.map((suggestion) => {
          const isSelected = selectedSuggestion === suggestion.id
          const action = actionById[suggestion.id] ?? 'cut'
          const mosaicOptions = mosaicById[suggestion.id] ?? DEFAULT_MOSAIC
          const telopOptions = telopById[suggestion.id] ?? DEFAULT_TELOP
          const isTelopInvalid = action === 'telop' && !telopOptions.text.trim()

          return (
            <div
              key={suggestion.id}
              className={`editing-suggestions__card${isSelected ? ' is-selected' : ''}`}
              onClick={() => {
                const nextId = isSelected ? null : suggestion.id
                onSelectSuggestion(nextId)
                if (nextId) {
                  onSeekTo(suggestion.startTime)
                }
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  const nextId = isSelected ? null : suggestion.id
                  onSelectSuggestion(nextId)
                  if (nextId) {
                    onSeekTo(suggestion.startTime)
                  }
                }
              }}
            >
              <div className="editing-suggestions__card-header">
                <span className={`risk-badge risk-${getRiskLevel(suggestion.riskLevel)}`}>
                  リスク {suggestion.riskLevel}%
                </span>
                <span className="editing-suggestions__range">
                  {formatTime(suggestion.startTime)} - {formatTime(suggestion.endTime)}
                </span>
              </div>

              <p className="editing-suggestions__reason">{suggestion.reason}</p>

              <div className="editing-suggestions__actions">
                <button
                  type="button"
                  className="ghost-button"
                  onClick={(event) => {
                    event.stopPropagation()
                    onSeekTo(suggestion.startTime)
                  }}
                >
                  プレビュー
                </button>
                <button
                  type="button"
                  className="primary-button"
                  disabled={isTelopInvalid}
                  onClick={(event) => {
                    event.stopPropagation()
                    handleApply(suggestion.id)
                  }}
                >
                  適用
                </button>
              </div>

              <div className="editing-suggestions__select">
                {ACTIONS.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    className={`chip${action === item.value ? ' chip--active' : ''}`}
                    onClick={(event) => {
                      event.stopPropagation()
                      handleActionChange(suggestion.id, item.value)
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {action === 'mosaic' && (
                <div className="editing-suggestions__options" onClick={(e) => e.stopPropagation()}>
                  <div className="field-row">
                    <label>
                      X
                      <input
                        type="number"
                        min={0}
                        value={mosaicOptions.x}
                        onChange={(event) => {
                          const nextValue = readNumberInput(event)
                          if (nextValue === null) {
                            return
                          }
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              x: clampNumber(nextValue, 0),
                            },
                          }))
                        }}
                      />
                    </label>
                    <label>
                      Y
                      <input
                        type="number"
                        min={0}
                        value={mosaicOptions.y}
                        onChange={(event) => {
                          const nextValue = readNumberInput(event)
                          if (nextValue === null) {
                            return
                          }
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              y: clampNumber(nextValue, 0),
                            },
                          }))
                        }}
                      />
                    </label>
                  </div>
                  <div className="field-row">
                    <label>
                      幅
                      <input
                        type="number"
                        min={1}
                        value={mosaicOptions.width}
                        onChange={(event) => {
                          const nextValue = readNumberInput(event)
                          if (nextValue === null) {
                            return
                          }
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              width: clampNumber(nextValue, 1),
                            },
                          }))
                        }}
                      />
                    </label>
                    <label>
                      高さ
                      <input
                        type="number"
                        min={1}
                        value={mosaicOptions.height}
                        onChange={(event) => {
                          const nextValue = readNumberInput(event)
                          if (nextValue === null) {
                            return
                          }
                          setMosaicById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...mosaicOptions,
                              height: clampNumber(nextValue, 1),
                            },
                          }))
                        }}
                      />
                    </label>
                  </div>
                  <label>
                    強度
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={mosaicOptions.blur_strength}
                      onChange={(event) => {
                        const nextValue = readNumberInput(event)
                        if (nextValue === null) {
                          return
                        }
                        setMosaicById((prev) => ({
                          ...prev,
                          [suggestion.id]: {
                            ...mosaicOptions,
                            blur_strength: clampNumber(nextValue, 1, 100),
                          },
                        }))
                      }}
                    />
                  </label>
                </div>
              )}

              {action === 'telop' && (
                <div className="editing-suggestions__options" onClick={(e) => e.stopPropagation()}>
                  <label>
                    テキスト
                    <input
                      type="text"
                      maxLength={500}
                      value={telopOptions.text}
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
                  <div className="field-row">
                    <label>
                      X
                      <input
                        type="number"
                        min={0}
                        value={telopOptions.x}
                        onChange={(event) => {
                          const nextValue = readNumberInput(event)
                          if (nextValue === null) {
                            return
                          }
                          setTelopById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...telopOptions,
                              x: clampNumber(nextValue, 0),
                            },
                          }))
                        }}
                      />
                    </label>
                    <label>
                      Y
                      <input
                        type="number"
                        min={0}
                        value={telopOptions.y}
                        onChange={(event) => {
                          const nextValue = readNumberInput(event)
                          if (nextValue === null) {
                            return
                          }
                          setTelopById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...telopOptions,
                              y: clampNumber(nextValue, 0),
                            },
                          }))
                        }}
                      />
                    </label>
                  </div>
                  <div className="field-row">
                    <label>
                      フォント
                      <input
                        type="number"
                        min={10}
                        max={200}
                        value={telopOptions.font_size}
                        onChange={(event) => {
                          const nextValue = readNumberInput(event)
                          if (nextValue === null) {
                            return
                          }
                          setTelopById((prev) => ({
                            ...prev,
                            [suggestion.id]: {
                              ...telopOptions,
                              font_size: clampNumber(nextValue, 10, 200),
                            },
                          }))
                        }}
                      />
                    </label>
                    <label>
                      文字色
                      <input
                        type="text"
                        value={telopOptions.font_color}
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
                  <label>
                    背景色
                    <input
                      type="text"
                      value={telopOptions.background_color ?? ''}
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
            </div>
          )
        })}
      </div>

      <div className="editing-suggestions__footer">
        <button type="button" className="primary-button" onClick={onApplyAll}>
          すべての提案を適用
        </button>
      </div>
    </div>
  )
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getRiskLevel(level: number) {
  if (level >= 70) return 'high'
  if (level >= 30) return 'medium'
  return 'low'
}
