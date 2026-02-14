"use client"

import { useState } from "react"
import { VideoPreview } from "./video-preview"
import { Timeline } from "./timeline"
import { RiskGraph } from "./risk-graph"
import { EditingSuggestions } from "./editing-suggestions"
import { VideoControls } from "./video-controls"
import { Button } from "./ui/button"
import { Upload, Save, Download, Menu, X, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react"

// サンプルデータ：バックエンドのVideo Intelligence APIから取得する想定
const mockRiskData = [
  { timestamp: 0, riskLevel: 12 },
  { timestamp: 3, riskLevel: 8 },
  { timestamp: 6, riskLevel: 15 },
  { timestamp: 9, riskLevel: 22 },
  { timestamp: 12, riskLevel: 18 },
  { timestamp: 15, riskLevel: 35 },
  { timestamp: 18, riskLevel: 58 },
  { timestamp: 21, riskLevel: 72 },
  { timestamp: 24, riskLevel: 85 },
  { timestamp: 27, riskLevel: 88 },
  { timestamp: 30, riskLevel: 78 },
  { timestamp: 33, riskLevel: 65 },
  { timestamp: 36, riskLevel: 42 },
  { timestamp: 39, riskLevel: 28 },
  { timestamp: 42, riskLevel: 18 },
  { timestamp: 45, riskLevel: 15 },
  { timestamp: 48, riskLevel: 12 },
  { timestamp: 51, riskLevel: 20 },
  { timestamp: 54, riskLevel: 38 },
  { timestamp: 57, riskLevel: 55 },
  { timestamp: 60, riskLevel: 68 },
  { timestamp: 63, riskLevel: 75 },
  { timestamp: 66, riskLevel: 82 },
  { timestamp: 69, riskLevel: 90 },
  { timestamp: 72, riskLevel: 87 },
  { timestamp: 75, riskLevel: 75 },
  { timestamp: 78, riskLevel: 58 },
  { timestamp: 81, riskLevel: 35 },
  { timestamp: 84, riskLevel: 22 },
  { timestamp: 87, riskLevel: 15 },
  { timestamp: 90, riskLevel: 10 },
]

const mockSuggestions = [
  {
    id: 1,
    startTime: 18,
    endTime: 33,
    riskLevel: 88,
    reason: "暴力的な表現や攻撃的な言葉が検出されました。視聴者の不快感を引き起こす可能性があります。",
  },
  {
    id: 2,
    startTime: 60,
    endTime: 75,
    riskLevel: 90,
    reason: "差別的な発言や炎上しやすい政治的・宗教的な内容が含まれています。強く削除を推奨します。",
  },
]

export function VideoEditor() {
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(90) // 90秒のサンプル動画
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedSuggestion, setSelectedSuggestion] = useState<number | null>(null)
  const [cutRanges, setCutRanges] = useState<Array<{ start: number; end: number }>>([])
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isSuggestionsExpanded, setIsSuggestionsExpanded] = useState(true)

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time)
  }

  const handleApplyCut = (startTime: number, endTime: number) => {
    setCutRanges([...cutRanges, { start: startTime, end: endTime }])
    setSelectedSuggestion(null)
    setIsSidebarOpen(false)
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* ヘッダー */}
      <header className="flex items-center justify-between border-b border-border bg-card px-3 py-2 md:px-6 md:py-3">
        <div className="flex items-center gap-2 md:gap-4">
          <h1 className="font-mono text-sm font-semibold text-foreground md:text-lg">Video Risk Editor</h1>
          <span className="hidden rounded bg-warning/20 px-2 py-0.5 text-xs text-warning md:block">
            MOCKデータ表示中
          </span>
        </div>
        <div className="flex items-center gap-1 md:gap-2">
          <Button
            variant="outline"
            size="sm"
            className="md:hidden bg-transparent"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            {isSidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
          <Button variant="outline" size="sm" className="hidden md:flex bg-transparent">
            <Upload className="mr-2 h-4 w-4" />
            動画をアップロード
          </Button>
          <Button variant="outline" size="sm">
            <Save className="mr-0 h-4 w-4 md:mr-2" />
            <span className="hidden md:inline">保存</span>
          </Button>
          <Button size="sm">
            <Download className="mr-0 h-4 w-4 md:mr-2" />
            <span className="hidden md:inline">エクスポート</span>
          </Button>
        </div>
      </header>

      <div className="flex flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden">
        {/* メインコンテンツ */}
        <div className="flex flex-1 flex-col md:overflow-hidden">
          {/* 動画プレビュー */}
          <div className="flex-shrink-0 border-b border-border bg-card/50 p-2 md:flex-1 md:p-6">
            <VideoPreview
              currentTime={currentTime}
              isPlaying={isPlaying}
              onTimeUpdate={handleTimeUpdate}
              cutRanges={cutRanges}
            />
          </div>

          <div className="flex-shrink-0 border-b border-border bg-card md:hidden">
            <button
              className="flex w-full items-center justify-between p-3 text-left hover:bg-accent/50"
              onClick={() => setIsSuggestionsExpanded(!isSuggestionsExpanded)}
            >
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-warning" />
                <h2 className="text-sm font-semibold text-foreground">編集提案 ({mockSuggestions.length}件)</h2>
              </div>
              {isSuggestionsExpanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
            {isSuggestionsExpanded && (
              <div className="max-h-80 overflow-y-auto">
                <EditingSuggestions
                  suggestions={mockSuggestions}
                  selectedSuggestion={selectedSuggestion}
                  onSelectSuggestion={setSelectedSuggestion}
                  onApplyCut={handleApplyCut}
                  onSeekTo={handleTimeUpdate}
                />
              </div>
            )}
          </div>

          {/* タイムライン・リスクグラフエリア */}
          <div className="h-48 flex-shrink-0 border-b border-border bg-card p-2 md:h-64 md:p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-foreground md:text-sm">タイムライン & リスク分析</h2>
              <div className="hidden items-center gap-4 text-xs text-muted-foreground md:flex">
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-success" />
                  低リスク (0-30%)
                </span>
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-warning" />
                  中リスク (31-70%)
                </span>
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-destructive" />
                  高リスク (71-100%)
                </span>
              </div>
            </div>
            <div className="relative h-full">
              <RiskGraph riskData={mockRiskData} currentTime={currentTime} />
              <Timeline
                duration={duration}
                currentTime={currentTime}
                onSeek={handleTimeUpdate}
                cutRanges={cutRanges}
                suggestions={mockSuggestions}
                selectedSuggestion={selectedSuggestion}
                onSelectSuggestion={setSelectedSuggestion}
              />
            </div>
          </div>

          {/* 動画コントロール */}
          <div className="flex-shrink-0 border-b border-border bg-card px-3 py-2 md:px-6 md:py-4">
            <VideoControls
              currentTime={currentTime}
              duration={duration}
              isPlaying={isPlaying}
              onPlayPause={() => setIsPlaying(!isPlaying)}
              onSeek={handleTimeUpdate}
            />
          </div>
        </div>

        <aside className="hidden w-80 flex-shrink-0 border-l border-border bg-card md:block">
          <EditingSuggestions
            suggestions={mockSuggestions}
            selectedSuggestion={selectedSuggestion}
            onSelectSuggestion={setSelectedSuggestion}
            onApplyCut={handleApplyCut}
            onSeekTo={handleTimeUpdate}
          />
        </aside>
      </div>
    </div>
  )
}
