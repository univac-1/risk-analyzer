export type Platform = 'twitter' | 'instagram' | 'youtube' | 'tiktok' | 'other'

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type PhaseStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type RiskCategory = 'aggressiveness' | 'discrimination' | 'misleading' | 'public_nuisance'

export type RiskLevel = 'high' | 'medium' | 'low' | 'none'

export type RiskSource = 'audio' | 'ocr' | 'video'

export interface VideoMetadata {
  purpose: string
  platform: Platform
  target_audience: string
}

export interface AnalysisJob {
  id: string
  status: JobStatus
  video_name: string
  metadata: VideoMetadata
  created_at: string
  completed_at: string | null
  error_message: string | null
}

export interface AnalysisJobSummary {
  id: string
  status: JobStatus
  video_name: string
  created_at: string
  completed_at: string | null
}

export interface PhaseProgress {
  status: PhaseStatus
  progress: number
}

export interface ProgressStatus {
  job_id: string
  status: JobStatus
  overall: number
  phases: Record<string, PhaseProgress>
  estimated_remaining_seconds: number | null
}

export interface RiskItem {
  id: string
  timestamp: number
  end_timestamp: number
  category: RiskCategory
  subcategory: string
  score: number
  level: RiskLevel
  rationale: string
  source: RiskSource
  evidence: string
}

export interface RiskAssessment {
  overall_score: number
  risk_level: RiskLevel
  risks: RiskItem[]
}

export interface AnalysisResult {
  job: AnalysisJob
  assessment: RiskAssessment
  video_url: string | null
}

export type EditActionType = 'cut' | 'mute' | 'mosaic' | 'telop' | 'skip'

export type EditSessionStatus = 'draft' | 'exporting' | 'completed'

export type ExportJobStatus = 'none' | 'pending' | 'processing' | 'completed' | 'failed'

export interface MosaicOptions {
  x: number
  y: number
  width: number
  height: number
  blur_strength: number
}

export interface TelopOptions {
  text: string
  x: number
  y: number
  font_size: number
  font_color: string
  background_color?: string | null
}

export interface EditActionInput {
  id?: string
  risk_item_id?: string | null
  type: EditActionType
  start_time: number
  end_time: number
  options?: MosaicOptions | TelopOptions | null
}

export interface EditActionResponse extends EditActionInput {
  id: string
  created_at: string
}

export interface EditSessionUpdate {
  actions: EditActionInput[]
}

export interface EditSessionResponse {
  id: string
  job_id: string
  status: EditSessionStatus
  actions: EditActionResponse[]
  created_at: string
  updated_at: string
}

export interface ExportResponse {
  export_id: string
  status: ExportJobStatus
}

export interface ExportStatusResponse {
  export_id: string | null
  status: ExportJobStatus
  progress: number
  error_message?: string | null
}

export interface VideoUrlResponse {
  url: string
  expires_at: string
}

export interface DownloadUrlResponse {
  url: string
  expires_at: string
}
