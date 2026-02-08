import { api } from './api'
import {
  DownloadUrlResponse,
  EditSessionResponse,
  EditSessionUpdate,
  ExportResponse,
  ExportStatusResponse,
  VideoUrlResponse,
} from '../types'

export const editorApi = {
  getVideoUrl: (jobId: string) =>
    api.get<VideoUrlResponse>(`/api/jobs/${jobId}/video-url`),

  getEditSession: (jobId: string) =>
    api.get<EditSessionResponse>(`/api/jobs/${jobId}/edit-session`),

  updateEditSession: (jobId: string, payload: EditSessionUpdate) =>
    api.put<EditSessionResponse>(`/api/jobs/${jobId}/edit-session`, payload),

  startExport: (jobId: string) =>
    api.post<ExportResponse>(`/api/jobs/${jobId}/export`),

  getExportStatus: (jobId: string) =>
    api.get<ExportStatusResponse>(`/api/jobs/${jobId}/export/status`),

  getExportDownload: (jobId: string) =>
    api.get<DownloadUrlResponse>(`/api/jobs/${jobId}/export/download`),
}
