import { useState, DragEvent, ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { Platform, AnalysisJob } from '../types'
import './UploadComponent.css'

const PLATFORMS: { value: Platform; label: string }[] = [
  { value: 'twitter', label: 'Twitter/X' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'other', label: 'その他' },
]

const MAX_FILE_SIZE_MB = 100

export function UploadComponent() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [purpose, setPurpose] = useState('')
  const [platform, setPlatform] = useState<Platform>('twitter')
  const [targetAudience, setTargetAudience] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFile = (file: File): string | null => {
    if (!file.name.toLowerCase().endsWith('.mp4')) {
      return 'mp4形式のファイルを選択してください'
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return `ファイルサイズが上限（${MAX_FILE_SIZE_MB}MB）を超えています`
    }
    return null
  }

  const handleFileSelect = (selectedFile: File) => {
    const validationError = validateFile(selectedFile)
    if (validationError) {
      setError(validationError)
      setFile(null)
    } else {
      setError(null)
      setFile(selectedFile)
    }
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSelect(selectedFile)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!file) {
      setError('動画ファイルを選択してください')
      return
    }

    if (!purpose.trim()) {
      setError('用途を入力してください')
      return
    }

    if (!targetAudience.trim()) {
      setError('想定ターゲットを入力してください')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('purpose', purpose)
      formData.append('platform', platform)
      formData.append('target_audience', targetAudience)

      const response = await api.upload<AnalysisJob>('/api/videos', formData)
      navigate(`/jobs/${response.id}/progress`)
    } catch (err) {
      setError('アップロードに失敗しました。もう一度お試しください。')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="upload-container">
      <form onSubmit={handleSubmit} className="upload-form">
        <div
          className={`drop-zone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="video/mp4,.mp4"
            onChange={handleFileChange}
            className="file-input"
            id="video-input"
          />
          <label htmlFor="video-input" className="drop-zone-label">
            {file ? (
              <div className="file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-size">
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
            ) : (
              <div className="drop-zone-text">
                <p>ここに動画をドラッグ&ドロップ</p>
                <p>または クリックしてファイルを選択</p>
                <p className="file-hint">対応形式: mp4（最大{MAX_FILE_SIZE_MB}MB）</p>
              </div>
            )}
          </label>
        </div>

        <div className="form-group">
          <label htmlFor="purpose">用途</label>
          <textarea
            id="purpose"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder="例: 新製品の紹介動画、キャンペーン告知など"
            rows={3}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="platform">投稿先媒体</label>
          <select
            id="platform"
            value={platform}
            onChange={(e) => setPlatform(e.target.value as Platform)}
            required
          >
            {PLATFORMS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="target-audience">想定ターゲット</label>
          <textarea
            id="target-audience"
            value={targetAudience}
            onChange={(e) => setTargetAudience(e.target.value)}
            placeholder="例: 20-30代の女性、IT業界の技術者など"
            rows={2}
            required
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <button
          type="submit"
          className="submit-button"
          disabled={isUploading || !file}
        >
          {isUploading ? '解析を開始中...' : '解析を開始'}
        </button>
      </form>
    </div>
  )
}
