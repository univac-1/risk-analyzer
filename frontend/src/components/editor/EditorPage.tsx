import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { api } from '../../services/api'
import { editorApi } from '../../services/editorApi'
import type { AnalysisResult, EditActionInput } from '../../types'
import { useEditSession } from '../../hooks/useEditSession'
import { VideoPreview } from './VideoPreview'
import { VideoControls } from './VideoControls'
import { RiskGraph } from './RiskGraph'
import { Timeline } from './Timeline'
import { EditingSuggestions } from './EditingSuggestions'
import './EditorPage.css'

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
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [pageError, setPageError] = useState<string | null>(null)
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
    setDownloadUrl(null)
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
        if (status.status === 'completed') {
          const download = await editorApi.getExportDownload(id)
          setDownloadUrl(download.url)
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
        if (status.status === 'completed') {
          const download = await editorApi.getExportDownload(id)
          setDownloadUrl(download.url)
        }
      } catch {
        setExportError('エクスポート状況の取得に失敗しました')
      }
    }, 2000)

    return () => window.clearInterval(interval)
  }, [id, exportStatus])

  const suggestions = useMemo<SuggestionItem[]>(() => {
    const risks = result?.assessment.risks ?? []
    return risks
      .filter((risk) => risk.level === 'high')
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
    setDownloadUrl(null)
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
    <div className="editor-page">
      <header className="editor-header">
        <div>
          <h1>Timeline Editor</h1>
          <p>{result?.job.video_name ?? '読み込み中...'}</p>
        </div>
        <div className="editor-header__actions">
          <button
            type="button"
            className="ghost-button editor-header__button editor-header__menu"
            onClick={() => setSidebarOpen((prev) => !prev)}
            aria-label="編集提案を開閉"
          >
            <span className="editor-header__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path
                  d="M4 6h16v2H4V6zm0 5h16v2H4v-2zm0 5h16v2H4v-2z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <span className="editor-header__label">提案</span>
          </button>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="ghost-button editor-header__button"
            aria-label="動画をアップロード"
          >
            <span className="editor-header__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path
                  d="M12 4l4 4h-3v6h-2V8H8l4-4zm-6 12h12v2H6v-2z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <span className="editor-header__label">動画をアップロード</span>
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="ghost-button editor-header__button"
            disabled={saving}
            aria-label="保存"
          >
            <span className="editor-header__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path
                  d="M5 4h10l4 4v12H5V4zm2 2v4h8V6H7zm0 6v6h10v-8H7z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <span className="editor-header__label">保存</span>
          </button>
          <button
            type="button"
            onClick={() => void undo()}
            className="ghost-button editor-header__button"
            disabled={!canUndo || saving}
            aria-label="元に戻す"
          >
            <span className="editor-header__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path
                  d="M12 5a7 7 0 0 1 7 7h-2a5 5 0 0 0-5-5H8.8l2.6 2.6L10 11 5 6l5-5 1.4 1.4L8.8 5H12z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <span className="editor-header__label">Undo</span>
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="primary-button editor-header__button"
            aria-label="エクスポート"
          >
            <span className="editor-header__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path
                  d="M12 20l-4-4h3V8h2v8h3l-4 4zm-6-14h12v2H6V6z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <span className="editor-header__label">エクスポート</span>
          </button>
        </div>
      </header>

      {(loading || sessionError || pageError) && (
        <div className="editor-status">
          {loading && <span>読み込み中...</span>}
          {sessionError && <span className="error">{sessionError}</span>}
          {pageError && <span className="error">{pageError}</span>}
        </div>
      )}

      {pageError && (
        <div className="editor-error-panel">
          <p>ジョブ一覧から編集対象を選び直してください。</p>
          <div className="editor-error-panel__actions">
            <button
              type="button"
              className="ghost-button"
              onClick={() => navigate('/jobs')}
            >
              ジョブ一覧へ
            </button>
            <button
              type="button"
              className="primary-button"
              onClick={() => navigate('/')}
            >
              新規解析へ
            </button>
          </div>
        </div>
      )}

      {(exportStatus || exportError) && (
        <div className="editor-export">
          {exportStatus && (
            <>
              <div>
                <strong>エクスポート状況:</strong> {exportStatus}
              </div>
              <div className="editor-export__progress">
                <span>{exportProgress.toFixed(0)}%</span>
                <div className="editor-export__bar">
                  <div
                    className="editor-export__fill"
                    style={{ width: `${exportProgress}%` }}
                  />
                </div>
              </div>
              <div className="editor-export__actions">
                {downloadUrl && (
                  <a className="primary-button" href={downloadUrl}>
                    ダウンロード
                  </a>
                )}
                {exportStatus === 'completed' && (
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={() => navigate(`/jobs/${id}/results`)}
                  >
                    結果に戻る
                  </button>
                )}
                {exportStatus === 'failed' && (
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={handleRetryExport}
                  >
                    再試行
                  </button>
                )}
              </div>
            </>
          )}
          {exportError && <span className="error">{exportError}</span>}
        </div>
      )}

      <div className="editor-body">
        <section className="editor-main">
          {!result && !pageError && (
            <div className="editor-empty">
              解析結果を読み込み中です。処理が完了していない場合はジョブ一覧から確認できます。
            </div>
          )}
          <div className="editor-panel">
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
          <div className="editor-mobile-suggestions">
            <button
              type="button"
              className="editor-mobile-suggestions__toggle"
              onClick={() => setSidebarOpen((prev) => !prev)}
            >
              編集提案 ({suggestionCount}件)
              <span aria-hidden="true">{sidebarOpen ? '▲' : '▼'}</span>
            </button>
            {sidebarOpen && (
              <div className="editor-mobile-suggestions__content">
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
          <div className="editor-panel">
            <RiskGraph
              riskData={riskData.length ? riskData : [{ timestamp: 0, riskLevel: 0 }]}
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
          <div className="editor-panel">
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
        </section>

        <aside className={`editor-sidebar${sidebarOpen ? ' is-open' : ''}`}>
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
