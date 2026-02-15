import { useState, DragEvent, ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { AnalysisJob } from '../types'
import './UploadComponent.css'

const MAX_FILE_SIZE_MB = 100

export function UploadComponent() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingSample, setIsLoadingSample] = useState(false)
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

  const handleUseSample = async () => {
    setIsLoadingSample(true)
    setError(null)
    try {
      const response = await fetch('/sample-video.mp4')
      if (!response.ok) throw new Error('サンプル動画の読み込みに失敗しました')
      const blob = await response.blob()
      const sampleFile = new File([blob], 'sample-video.mp4', { type: 'video/mp4' })
      handleFileSelect(sampleFile)
    } catch {
      setError('サンプル動画の読み込みに失敗しました')
    } finally {
      setIsLoadingSample(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!file) {
      setError('動画ファイルを選択してください')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('purpose', '-')
      formData.append('platform', 'other')
      formData.append('target_audience', '-')

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

        <div className="sample-button-wrapper">
          <button
            type="button"
            className="sample-button"
            onClick={handleUseSample}
            disabled={isLoadingSample || isUploading}
          >
            {isLoadingSample ? '読み込み中...' : 'サンプル動画を使う'}
          </button>
          <span className="sample-button-hint">動画をお持ちでない方はこちら</span>
        </div>

        <div className="upload-notice">
          <span className="upload-notice-icon">⚠️</span>
          <span>アップロードした動画と解析結果は、全世界のユーザーから閲覧可能になります。個人情報や機密情報が含まれる動画のアップロードはご注意ください。</span>
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
