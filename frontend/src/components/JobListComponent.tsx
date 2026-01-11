import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { AnalysisJobSummary, JobStatus } from '../types'
import './JobListComponent.css'

const STATUS_LABELS: Record<JobStatus, string> = {
  pending: '待機中',
  processing: '処理中',
  completed: '完了',
  failed: '失敗',
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span className={`status-badge ${status}`}>
      {STATUS_LABELS[status]}
    </span>
  )
}

export function JobListComponent() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<AnalysisJobSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const data = await api.get<AnalysisJobSummary[]>('/api/jobs')
        setJobs(data)
      } catch (err) {
        setError('ジョブ一覧の取得に失敗しました')
      } finally {
        setIsLoading(false)
      }
    }

    fetchJobs()
  }, [])

  const handleJobClick = (job: AnalysisJobSummary) => {
    if (job.status === 'completed') {
      navigate(`/jobs/${job.id}/results`)
    } else if (job.status === 'processing' || job.status === 'pending') {
      navigate(`/jobs/${job.id}/progress`)
    }
  }

  if (isLoading) {
    return (
      <div className="job-list-container">
        <div className="loading-state">
          <p>読み込み中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="job-list-container">
        <div className="error-state">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>再読み込み</button>
        </div>
      </div>
    )
  }

  return (
    <div className="job-list-container">
      <div className="job-list-header">
        <h2>解析ジョブ一覧</h2>
        <button
          className="new-job-button"
          onClick={() => navigate('/')}
        >
          新規解析
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="empty-state">
          <p>まだ解析ジョブがありません</p>
          <button onClick={() => navigate('/')}>動画をアップロード</button>
        </div>
      ) : (
        <div className="job-list">
          {jobs.map((job) => (
            <div
              key={job.id}
              className={`job-item ${job.status}`}
              onClick={() => handleJobClick(job)}
            >
              <div className="job-info">
                <span className="job-name">{job.video_name}</span>
                <span className="job-date">{formatDate(job.created_at)}</span>
              </div>
              <StatusBadge status={job.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
