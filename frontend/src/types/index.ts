export type Platform = 'twitter' | 'instagram' | 'youtube' | 'tiktok' | 'other'

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type PhaseStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type RiskCategory = 'aggressiveness' | 'discrimination' | 'misleading'

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
}
