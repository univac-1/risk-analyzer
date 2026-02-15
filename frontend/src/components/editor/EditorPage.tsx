import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Download,
  Plus,
  Save,
  Undo2,
  ArrowLeft,
} from 'lucide-react'

import { api, API_BASE_URL } from '../../services/api'
import { editorApi } from '../../services/editorApi'
import type { AnalysisResult, EditActionInput } from '../../types'
import { useEditSession } from '../../hooks/useEditSession'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { VideoPreview } from './VideoPreview'
import { VideoControls } from './VideoControls'
import { RiskGraph } from './RiskGraph'
import { Timeline } from './Timeline'
import { EditingSuggestions } from './EditingSuggestions'

interface SuggestionItem {
  id: string
  startTime: number
  endTime: number
  riskLevel: number
  reason: string
}

export function EditorPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(
    null
  )
  const [exportStatus, setExportStatus] = useState<string | null>(null)
  const [exportProgress, setExportProgress] = useState(0)
  const [exportError, setExportError] = useState<string | null>(null)
  const [pageError, setPageError] = useState<string | null>(null)
  const [isSuggestionsExpanded, setIsSuggestionsExpanded] = useState(true)
  const videoRef = useRef<HTMLVideoElement>(null)

  const {
    actions,
    loading,
    saving,
    error: sessionError,
    addAction,
    replaceActions,
    canUndo,
    undo,
  } = useEditSession(id ?? null)

  useEffect(() => {
    if (!id) {
      return
    }
    setExportStatus(null)
    setExportProgress(0)
    setExportError(null)

    const fetchData = async () => {
      try {
        const [resultData, videoData] = await Promise.all([
          api.get<AnalysisResult>(`/api/jobs/${id}/results`),
          editorApi.getVideoUrl(id),
        ])
        setResult(resultData)
        setVideoUrl(videoData.url)
        setPageError(null)
      } catch {
        setPageError('解析結果の取得に失敗しました')
      }
    }

    fetchData().catch(() => undefined)
  }, [id])

  useEffect(() => {
    if (!id) {
      return
    }

    const loadExportStatus = async () => {
      try {
        const status = await editorApi.getExportStatus(id)
        setExportStatus(status.status)
        setExportProgress(status.progress)
        if (status.status === 'failed') {
          setExportError(status.error_message ?? 'エクスポートに失敗しました')
        }
      } catch (err) {
        if (err instanceof Error && err.message.includes('404')) {
          return
        }
        setExportError('エクスポート状況の取得に失敗しました')
      }
    }

    loadExportStatus().catch(() => undefined)
  }, [id])

  useEffect(() => {
    if (!id || !exportStatus || exportStatus === 'completed' || exportStatus === 'failed') {
      return
    }

    const interval = window.setInterval(async () => {
      try {
        const status = await editorApi.getExportStatus(id)
        setExportStatus(status.status)
        setExportProgress(status.progress)
        if (status.status === 'failed') {
          setExportError(status.error_message ?? 'エクスポートに失敗しました')
        }
      } catch {
        setExportError('エクスポート状況の取得に失敗しました')
      }
    }, 2000)

    return () => window.clearInterval(interval)
  }, [id, exportStatus])

  const handleDownload = async () => {
    if (!id) return
    const response = await fetch(`${API_BASE_URL}/api/jobs/${id}/export/file`)
    if (!response.ok) return
    const blob = await response.blob()
    const objectUrl = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = 'edited_video.mp4'
    anchor.click()
    URL.revokeObjectURL(objectUrl)
  }

  const suggestions = useMemo<SuggestionItem[]>(() => {
    const risks = result?.assessment.risks ?? []
    return risks
      .map((risk) => ({
        id: risk.id,
        startTime: risk.timestamp,
        endTime: risk.end_timestamp,
        riskLevel: normalizeRiskScore(risk.score),
        reason: risk.rationale,
      }))
  }, [result])

  const suggestionCount = suggestions.length

  const riskData = useMemo(
    () =>
      (result?.assessment.risks ?? []).map((risk) => ({
        timestamp: risk.timestamp,
        riskLevel: normalizeRiskScore(risk.score),
      })),
    [result]
  )

  const effectiveDuration = useMemo(() => {
    if (duration > 0) {
      return duration
    }
    if (!result) {
      return 1
    }
    const maxEnd = Math.max(
      ...result.assessment.risks.map((risk) => risk.end_timestamp),
      0
    )
    return maxEnd || 1
  }, [duration, result])

  const cutRanges = useMemo(
    () =>
      actions
        .filter((action) => action.type === 'cut')
        .map((action) => ({
          start: action.start_time,
          end: action.end_time,
        })),
    [actions]
  )

  const handleApplyAction = async (
    suggestionId: string,
    type: EditActionInput['type'],
    options?: EditActionInput['options']
  ) => {
    const suggestion = suggestions.find((item) => item.id === suggestionId)
    if (!suggestion) {
      return
    }
    await addAction({
      risk_item_id: suggestionId,
      type,
      start_time: suggestion.startTime,
      end_time: suggestion.endTime,
      options: options ?? null,
    })
  }

  const handleApplyAll = async () => {
    const nextActions: EditActionInput[] = suggestions.map((suggestion) => ({
      risk_item_id: suggestion.id,
      type: 'cut',
      start_time: suggestion.startTime,
      end_time: suggestion.endTime,
      options: null,
    }))
    await replaceActions(nextActions)
  }

  const handleSave = async () => {
    await replaceActions(
      actions.map((action) => ({
        id: action.id,
        risk_item_id: action.risk_item_id,
        type: action.type,
        start_time: action.start_time,
        end_time: action.end_time,
        options: action.options ?? null,
      }))
    )
  }

  const handleExport = async () => {
    if (!id) {
      return
    }
    setExportError(null)
    try {
      const response = await editorApi.startExport(id)
      setExportStatus(response.status)
      setExportProgress(0)
    } catch (err) {
      setExportError(
        err instanceof Error ? err.message : 'エクスポート開始に失敗しました'
      )
    }
  }

  const handleRetryExport = async () => {
    await handleExport()
  }

  const handleToggleMute = (muted: boolean) => {
    if (videoRef.current) {
      videoRef.current.muted = muted
    }
  }

  const handleToggleFullscreen = (fullscreen: boolean) => {
    const element = videoRef.current
    if (fullscreen) {
      element?.requestFullscreen?.().catch(() => undefined)
      return
    }
    if (document.fullscreenElement) {
      document.exitFullscreen?.().catch(() => undefined)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex flex-col gap-3 border-b border-border bg-card px-3 py-3 md:flex-row md:items-center md:justify-between md:px-6">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="bg-transparent"
              onClick={() => navigate('/jobs')}
            >
              <ArrowLeft className="h-4 w-4" />
              ジョブ一覧
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="bg-transparent"
              onClick={() => navigate('/')}
            >
              <Plus className="h-4 w-4" />
              新規解析
            </Button>
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-mono text-base font-semibold md:text-lg">
                Timeline Editor
              </h1>
              <Badge variant="warning" className="text-[10px] md:text-xs">
                EDIT
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground md:text-sm">
              {result?.job.video_name ?? '読み込み中...'}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="bg-transparent"
            onClick={handleSave}
            disabled={saving}
          >
            <Save className="h-4 w-4" />
            保存
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="bg-transparent"
            onClick={() => void undo()}
            disabled={!canUndo || saving}
          >
            <Undo2 className="h-4 w-4" />
            Undo
          </Button>
          <Button size="sm" onClick={handleExport}>
            <Download className="h-4 w-4" />
            エクスポート
          </Button>
        </div>
      </header>

      {(loading || sessionError || pageError) && (
        <div className="flex flex-wrap gap-3 px-4 py-2 text-sm text-muted-foreground md:px-6">
          {loading && <span>読み込み中...</span>}
          {sessionError && <span className="text-destructive">{sessionError}</span>}
          {pageError && <span className="text-destructive">{pageError}</span>}
        </div>
      )}

      {pageError && (
        <div className="mx-4 mt-2 grid gap-3 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive md:mx-6">
          <p>ジョブ一覧から編集対象を選び直してください。</p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate('/jobs')}>ジョブ一覧へ</Button>
            <Button variant="outline" onClick={() => navigate('/')}>
              新規解析へ
            </Button>
          </div>
        </div>
      )}

      {(exportStatus || exportError) && (
        <div className="flex flex-wrap items-center gap-4 border-b border-border bg-card/70 px-4 py-3 text-sm md:px-6">
          {exportStatus && (
            <>
              <div>
                <strong>エクスポート状況:</strong> {exportStatus}
              </div>
              <div className="flex items-center gap-2">
                <span>{exportProgress.toFixed(0)}%</span>
                <div className="h-1.5 w-40 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary"
                    style={{ width: `${exportProgress}%` }}
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {exportStatus === 'completed' && (
                  <Button onClick={handleDownload}>ダウンロード</Button>
                )}
                {exportStatus === 'completed' && (
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/jobs/${id}/results`)}
                  >
                    結果に戻る
                  </Button>
                )}
                {exportStatus === 'failed' && (
                  <Button variant="outline" onClick={handleRetryExport}>
                    再試行
                  </Button>
                )}
              </div>
            </>
          )}
          {exportError && <span className="text-destructive">{exportError}</span>}
        </div>
      )}

      <div className="flex flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden">
        <div className="flex flex-1 flex-col md:overflow-hidden">
          {!result && !pageError && (
            <div className="px-4 py-3 text-sm text-muted-foreground md:px-6">
              解析結果を読み込み中です。処理が完了していない場合はジョブ一覧から確認できます。
            </div>
          )}
          <div className="flex-shrink-0 border-b border-border bg-card/50 p-2 md:flex-1 md:p-6">
            <VideoPreview
              currentTime={currentTime}
              isPlaying={isPlaying}
              onTimeUpdate={setCurrentTime}
              cutRanges={cutRanges}
              videoUrl={videoUrl}
              onDurationChange={(nextDuration) => setDuration(nextDuration)}
              videoRef={videoRef}
            />
          </div>

          <div className="flex-shrink-0 border-b border-border bg-card md:hidden">
            <button
              type="button"
              className="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-accent/50"
              onClick={() => setIsSuggestionsExpanded((prev) => !prev)}
            >
              <div className="flex items-center gap-2 text-sm font-semibold">
                <AlertTriangle className="h-4 w-4 text-warning" />
                編集提案 ({suggestionCount}件)
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
                  suggestions={suggestions}
                  selectedSuggestion={selectedSuggestion}
                  onSelectSuggestion={setSelectedSuggestion}
                  onSeekTo={setCurrentTime}
                  onApplyAction={handleApplyAction}
                  onApplyAll={handleApplyAll}
                />
              </div>
            )}
          </div>

          <div className="h-56 flex-shrink-0 border-b border-border bg-card p-3 md:h-64 md:p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold md:text-sm">
                タイムライン & リスク分析
              </h2>
              <div className="hidden items-center gap-4 text-xs text-muted-foreground md:flex">
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-success" />
                  低リスク (0-30%)
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-warning" />
                  中リスク (31-70%)
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-destructive" />
                  高リスク (71-100%)
                </span>
              </div>
            </div>
            <div className="relative h-full">
              <RiskGraph
                riskData={
                  riskData.length ? riskData : [{ timestamp: 0, riskLevel: 0 }]
                }
                currentTime={currentTime}
                duration={effectiveDuration}
              />
              <Timeline
                duration={effectiveDuration}
                currentTime={currentTime}
                onSeek={setCurrentTime}
                cutRanges={cutRanges}
                suggestions={suggestions.map((item) => ({
                  id: item.id,
                  startTime: item.startTime,
                  endTime: item.endTime,
                  riskLevel: item.riskLevel,
                }))}
                selectedSuggestion={selectedSuggestion}
                onSelectSuggestion={setSelectedSuggestion}
              />
            </div>
          </div>

          <div className="flex-shrink-0 border-b border-border bg-card px-3 py-2 md:px-6 md:py-4">
            <VideoControls
              currentTime={currentTime}
              duration={effectiveDuration}
              isPlaying={isPlaying}
              onPlayPause={() => setIsPlaying((prev) => !prev)}
              onSeek={setCurrentTime}
              onToggleMute={handleToggleMute}
              onToggleFullscreen={handleToggleFullscreen}
            />
          </div>
        </div>

        <aside className="hidden w-80 flex-shrink-0 border-l border-border bg-card md:block">
          <EditingSuggestions
            suggestions={suggestions}
            selectedSuggestion={selectedSuggestion}
            onSelectSuggestion={setSelectedSuggestion}
            onSeekTo={setCurrentTime}
            onApplyAction={handleApplyAction}
            onApplyAll={handleApplyAll}
          />
        </aside>
      </div>
    </div>
  )
}

function normalizeRiskScore(score: number) {
  if (score <= 1) {
    return Math.round(score * 100)
  }
  return Math.round(score)
}
