import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import { EditorPage } from './EditorPage'

// --- hoisted mocks -------------------------------------------------------

const {
  mockNavigate,
  mockAddAction,
  mockReplaceActions,
  mockUndo,
  mockApiGet,
  mockGetVideoUrl,
  mockGetEditSession,
  mockUpdateEditSession,
  mockStartExport,
  mockGetExportStatus,
  mockGetExportDownload,
  mockSessionState,
} = vi.hoisted(() => {
  const state = {
    session: null as null,
    actions: [] as never[],
    loading: false,
    saving: false,
    error: null as string | null,
    canUndo: false,
  }
  return {
    mockNavigate: vi.fn(),
    mockAddAction: vi.fn(),
    mockReplaceActions: vi.fn(),
    mockUndo: vi.fn(),
    mockApiGet: vi.fn(),
    mockGetVideoUrl: vi.fn(),
    mockGetEditSession: vi.fn(),
    mockUpdateEditSession: vi.fn(),
    mockStartExport: vi.fn(),
    mockGetExportStatus: vi.fn(),
    mockGetExportDownload: vi.fn(),
    mockSessionState: state,
  }
})

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../hooks/useEditSession', () => ({
  useEditSession: () => ({
    ...mockSessionState,
    reload: vi.fn(),
    addAction: mockAddAction,
    updateAction: vi.fn(),
    removeAction: vi.fn(),
    replaceActions: mockReplaceActions,
    undo: mockUndo,
  }),
}))

vi.mock('../../services/api', () => ({
  api: { get: (...args: unknown[]) => mockApiGet(...args) },
}))

vi.mock('../../services/editorApi', () => ({
  editorApi: {
    getVideoUrl: (...args: unknown[]) => mockGetVideoUrl(...args),
    getEditSession: (...args: unknown[]) => mockGetEditSession(...args),
    updateEditSession: (...args: unknown[]) => mockUpdateEditSession(...args),
    startExport: (...args: unknown[]) => mockStartExport(...args),
    getExportStatus: (...args: unknown[]) => mockGetExportStatus(...args),
    getExportDownload: (...args: unknown[]) => mockGetExportDownload(...args),
  },
}))

// --- test data -----------------------------------------------------------

const analysisResult = {
  job: {
    id: 'job-1',
    status: 'completed',
    video_name: 'test.mp4',
    metadata: { purpose: 'test', platform: 'twitter', target_audience: 'general' },
    created_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T01:00:00Z',
    error_message: null,
  },
  assessment: {
    overall_score: 75,
    risk_level: 'high',
    risks: [
      {
        id: 'risk-1',
        timestamp: 10,
        end_timestamp: 15,
        category: 'aggressiveness',
        subcategory: 'hostile',
        score: 0.85,
        level: 'high',
        rationale: 'テストリスク理由',
        source: 'audio',
        evidence: 'テスト証拠',
      },
    ],
  },
  video_url: 'https://example.com/video.mp4',
}

// --- helpers -------------------------------------------------------------

function renderEditor() {
  return render(
    <MemoryRouter initialEntries={['/jobs/job-1/editor']}>
      <Routes>
        <Route path="/jobs/:id/editor" element={<EditorPage />} />
      </Routes>
    </MemoryRouter>
  )
}

// --- tests ---------------------------------------------------------------

describe('EditorPage 統合テスト (Task 13.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSessionState.session = null
    mockSessionState.actions = []
    mockSessionState.loading = false
    mockSessionState.saving = false
    mockSessionState.error = null
    mockSessionState.canUndo = false

    mockApiGet.mockResolvedValue(analysisResult)
    mockGetVideoUrl.mockResolvedValue({
      url: 'https://example.com/video.mp4',
      expires_at: '2026-01-01T02:00:00Z',
    })
    mockGetExportStatus.mockRejectedValue(new Error('404'))
  })

  // ---- 編集アクション追加→保存 ----

  describe('編集アクション追加→保存', () => {
    it('提案カードの「適用」ボタンでaddActionが呼ばれる', async () => {
      renderEditor()

      const applyButtons = await screen.findAllByText('適用')
      fireEvent.click(applyButtons[0])

      expect(mockAddAction).toHaveBeenCalledWith(
        expect.objectContaining({
          risk_item_id: 'risk-1',
          type: 'cut',
          start_time: 10,
          end_time: 15,
        })
      )
    })

    it('「すべての提案を適用」ボタンでreplaceActionsが呼ばれる', async () => {
      renderEditor()

      const applyAllButtons = await screen.findAllByText('すべての提案を適用')
      fireEvent.click(applyAllButtons[0])

      expect(mockReplaceActions).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            risk_item_id: 'risk-1',
            type: 'cut',
          }),
        ])
      )
    })

    it('「保存」ボタンでreplaceActionsが呼ばれる', async () => {
      renderEditor()

      const saveButton = await screen.findByLabelText('保存')
      fireEvent.click(saveButton)

      expect(mockReplaceActions).toHaveBeenCalled()
    })

    it('「Undo」ボタンでundoが呼ばれる', async () => {
      mockSessionState.canUndo = true
      renderEditor()

      const undoButton = await screen.findByLabelText('元に戻す')
      fireEvent.click(undoButton)

      expect(mockUndo).toHaveBeenCalled()
    })
  })

  // ---- エクスポート実行→進捗表示→ダウンロード ----

  describe('エクスポート実行→進捗表示→ダウンロード', () => {
    it('エクスポートボタンクリックでstartExportが呼ばれる', async () => {
      mockStartExport.mockResolvedValue({
        export_id: 'e1',
        status: 'pending',
      })

      renderEditor()

      const exportButton = await screen.findByLabelText('エクスポート')
      await act(async () => {
        fireEvent.click(exportButton)
      })

      expect(mockStartExport).toHaveBeenCalledWith('job-1')
    })

    it('エクスポート状況がpendingの場合、進捗バーが表示される', async () => {
      mockGetExportStatus.mockResolvedValue({
        export_id: 'e1',
        status: 'pending',
        progress: 0,
      })

      renderEditor()

      await waitFor(() => {
        expect(screen.getByText(/エクスポート状況/i)).toBeInTheDocument()
      })
    })

    it('エクスポート完了時にダウンロードリンクと「結果に戻る」が表示される', async () => {
      mockGetExportStatus.mockResolvedValue({
        export_id: 'e1',
        status: 'completed',
        progress: 100,
      })
      mockGetExportDownload.mockResolvedValue({
        url: 'https://example.com/edited.mp4',
        expires_at: '2026-01-01T03:00:00Z',
      })

      renderEditor()

      const downloadButton = await screen.findByText('ダウンロード')
      expect(downloadButton).toBeInTheDocument()
      expect(downloadButton.tagName).toBe('BUTTON')

      const backButton = await screen.findByText('結果に戻る')
      expect(backButton).toBeInTheDocument()
    })

    it('「結果に戻る」クリックで結果ページへ遷移する', async () => {
      mockGetExportStatus.mockResolvedValue({
        export_id: 'e1',
        status: 'completed',
        progress: 100,
      })
      mockGetExportDownload.mockResolvedValue({
        url: 'https://example.com/edited.mp4',
        expires_at: '',
      })

      renderEditor()

      const backButton = await screen.findByText('結果に戻る')
      fireEvent.click(backButton)

      expect(mockNavigate).toHaveBeenCalledWith('/jobs/job-1/results')
    })
  })

  // ---- エラーハンドリング ----

  describe('エラーハンドリング', () => {
    it('解析結果取得失敗時にエラーメッセージが表示される', async () => {
      mockApiGet.mockRejectedValue(new Error('Network error'))
      mockGetVideoUrl.mockRejectedValue(new Error('Network error'))

      renderEditor()

      const errorMsg = await screen.findByText(/解析結果の取得に失敗しました/i)
      expect(errorMsg).toBeInTheDocument()
    })

    it('解析結果取得失敗時にジョブ一覧への導線が表示される', async () => {
      mockApiGet.mockRejectedValue(new Error('Network error'))
      mockGetVideoUrl.mockRejectedValue(new Error('Network error'))

      renderEditor()

      const jobListButton = await screen.findByText('ジョブ一覧へ')
      expect(jobListButton).toBeInTheDocument()
      fireEvent.click(jobListButton)
      expect(mockNavigate).toHaveBeenCalledWith('/jobs')
    })

    it('エクスポート失敗時にエラーと再試行ボタンが表示される', async () => {
      mockGetExportStatus.mockResolvedValue({
        export_id: 'e1',
        status: 'failed',
        progress: 0,
        error_message: 'FFmpegエラー',
      })

      renderEditor()

      const retryButton = await screen.findByText('再試行')
      expect(retryButton).toBeInTheDocument()

      const errorMsg = await screen.findByText('FFmpegエラー')
      expect(errorMsg).toBeInTheDocument()
    })

    it('エクスポート開始失敗時にエラーメッセージが表示される', async () => {
      mockStartExport.mockRejectedValue(
        new Error('エクスポート開始に失敗しました')
      )
      mockGetExportStatus.mockRejectedValue(new Error('404'))

      renderEditor()

      const exportButton = await screen.findByLabelText('エクスポート')
      await act(async () => {
        fireEvent.click(exportButton)
      })

      await waitFor(() => {
        expect(
          screen.getByText(/エクスポート開始に失敗しました/i)
        ).toBeInTheDocument()
      })
    })
  })
})
