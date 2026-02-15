import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, API_BASE_URL } from '../services/api'
import { AnalysisResult, RiskItem, RiskLevel, RiskCategory, RiskSource } from '../types'
import './ResultsComponent.css'

const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  high: '高',
  medium: '中',
  low: '低',
  none: 'なし',
}

const RISK_CATEGORY_LABELS: Record<RiskCategory, string> = {
  aggressiveness: '攻撃性',
  discrimination: '差別性',
  misleading: '誤解を招く表現',
  public_nuisance: '迷惑行為',
}

const RISK_SOURCE_LABELS: Record<RiskSource, string> = {
  audio: '音声',
  ocr: 'テキスト',
  video: '映像',
}

function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  const secsStr = secs.toFixed(2)
  const secsFormatted = Number(secsStr) < 10 ? `0${secsStr}` : secsStr
  return `${mins.toString().padStart(2, '0')}:${secsFormatted}`
}

function RiskLevelBadge({ level }: { level: RiskLevel }) {
  return (
    <span className={`risk-level-badge ${level}`}>
      {RISK_LEVEL_LABELS[level]}
    </span>
  )
}

function RiskItemCard({
  item,
  onSeek,
}: {
  item: RiskItem
  onSeek: (timestamp: number) => void
}) {
  return (
    <div className={`risk-item-card ${item.level}`}>
      <div className="risk-item-header">
        <button
          className="timestamp-button"
          onClick={() => onSeek(item.timestamp)}
        >
          {formatTimestamp(item.timestamp)} - {formatTimestamp(item.end_timestamp)}
        </button>
        <div className="risk-badges">
          <RiskLevelBadge level={item.level} />
          <span className="risk-category-badge">
            {RISK_CATEGORY_LABELS[item.category]}
          </span>
          <span className="risk-source-badge">
            {RISK_SOURCE_LABELS[item.source]}
          </span>
        </div>
      </div>

      <div className="risk-item-body">
        <div className="risk-subcategory">
          <strong>種別:</strong> {item.subcategory}
        </div>
        <div className="risk-evidence">
          <strong>該当箇所:</strong> {item.evidence}
        </div>
        <div className="risk-rationale">
          <strong>リスク根拠:</strong> {item.rationale}
        </div>
        <div className="risk-score">
          <strong>リスクスコア:</strong> {item.score.toFixed(0)}点
        </div>
      </div>
    </div>
  )
}

type SortOption = 'timestamp' | 'score'

export function ResultsComponent() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const videoRef = useRef<HTMLVideoElement>(null)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<SortOption>('timestamp')
  const [videoUrl, setVideoUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return

    const fetchResults = async () => {
      try {
        const data = await api.get<AnalysisResult>(`/api/jobs/${id}/results`)
        setResult(data)
        if (data.video_url) {
          // Convert relative URL to absolute URL if needed
          const absoluteUrl = data.video_url.startsWith('http')
            ? data.video_url
            : `${API_BASE_URL}${data.video_url}`
          setVideoUrl(absoluteUrl)
        }
      } catch (err) {
        setError('結果の取得に失敗しました')
      }
    }

    fetchResults()
  }, [id])

  const handleSeek = (timestamp: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp
      videoRef.current.play()
    }
  }

  const sortedRisks = result?.assessment.risks.slice().sort((a, b) => {
    if (sortBy === 'score') {
      return b.score - a.score
    }
    return a.timestamp - b.timestamp
  })

  if (error) {
    return (
      <div className="results-container">
        <div className="error-state">
          <h2>エラーが発生しました</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/')}>トップに戻る</button>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="results-container">
        <div className="loading-state">
          <p>読み込み中...</p>
        </div>
      </div>
    )
  }

  const { job, assessment } = result

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>解析結果</h2>
        <p className="video-name">{job.video_name}</p>
      </div>

      <div className="overall-assessment">
        <div className="overall-score">
          <span className="score-label">総合リスクスコア</span>
          <span className={`score-value ${assessment.risk_level}`}>
            {assessment.overall_score.toFixed(0)}
          </span>
        </div>
        <div className="overall-level">
          <span className="level-label">リスクレベル</span>
          <RiskLevelBadge level={assessment.risk_level} />
        </div>
      </div>

      <div className="video-preview">
        <video
          ref={videoRef}
          controls
          src={videoUrl || undefined}
          poster=""
        >
          <p>動画プレビューは利用できません</p>
        </video>
      </div>

      <div className="risks-section">
        <div className="risks-header">
          <h3>検出されたリスク ({assessment.risks.length}件)</h3>
          <div className="sort-controls">
            <label>並び替え:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
            >
              <option value="timestamp">タイムコード順</option>
              <option value="score">スコア順</option>
            </select>
          </div>
        </div>

        {assessment.risks.length === 0 ? (
          <div className="no-risks">
            <p>リスクは検出されませんでした</p>
          </div>
        ) : (
          <div className="risks-list">
            {sortedRisks?.map((risk) => (
              <RiskItemCard
                key={risk.id}
                item={risk}
                onSeek={handleSeek}
              />
            ))}
          </div>
        )}
      </div>

      <div className="results-actions">
        <button
          className="secondary-button"
          onClick={() => navigate('/jobs')}
        >
          ジョブ一覧へ
        </button>
        <button
          className="secondary-button"
          onClick={() => navigate('/')}
        >
          新規解析
        </button>
        <button
          className="primary-button"
          onClick={() => navigate(`/jobs/${job.id}/editor`)}
        >
          タイムライン編集へ
        </button>
      </div>
    </div>
  )
}
