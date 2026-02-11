import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import { EditorPage } from './EditorPage'

// --- mocks ---------------------------------------------------------------

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../hooks/useEditSession', () => ({
  useEditSession: () => ({
    session: null,
    actions: [],
    loading: false,
    saving: false,
    error: null,
    canUndo: false,
    reload: vi.fn(),
    addAction: vi.fn(),
    updateAction: vi.fn(),
    removeAction: vi.fn(),
    replaceActions: vi.fn(),
    undo: vi.fn(),
  }),
}))

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({
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
            rationale: 'テストリスク',
            source: 'audio',
            evidence: 'テスト証拠',
          },
        ],
      },
      video_url: 'https://example.com/video.mp4',
    }),
  },
}))

vi.mock('../../services/editorApi', () => ({
  editorApi: {
    getVideoUrl: vi.fn().mockResolvedValue({ url: 'https://example.com/video.mp4', expires_at: '' }),
    getEditSession: vi.fn().mockResolvedValue({ id: 's1', job_id: 'job-1', status: 'draft', actions: [], created_at: '', updated_at: '' }),
    updateEditSession: vi.fn().mockResolvedValue({ id: 's1', job_id: 'job-1', status: 'draft', actions: [], created_at: '', updated_at: '' }),
    startExport: vi.fn().mockResolvedValue({ export_id: 'e1', status: 'pending' }),
    getExportStatus: vi.fn().mockResolvedValue({ export_id: null, status: 'none', progress: 0 }),
    getExportDownload: vi.fn().mockResolvedValue({ url: '', expires_at: '' }),
  },
}))

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

describe('EditorPage - レスポンシブ対応 (Task 12.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('モバイルアコーディオンのトグルボタンが表示される', async () => {
    renderEditor()
    const toggle = await screen.findByText(/編集提案.*件/i)
    expect(toggle.closest('button')).toHaveClass('editor-mobile-suggestions__toggle')
  })

  it('トグルクリックでアコーディオン内にEditingSuggestionsコンテンツが表示される', async () => {
    renderEditor()
    const toggle = await screen.findByText(/編集提案.*件/i)
    fireEvent.click(toggle)

    // アコーディオン展開後、EditingSuggestions内のヘッダーテキストが表示される
    const headers = await screen.findAllByText(/高リスク箇所が検出されました/i)
    // モバイルアコーディオン内に表示されること（サイドバーとは別）
    expect(headers.length).toBeGreaterThanOrEqual(2)
  })

  it('アコーディオン再クリックでコンテンツが閉じる', async () => {
    renderEditor()
    const toggle = await screen.findByText(/編集提案.*件/i)

    // 開く
    fireEvent.click(toggle)
    await screen.findAllByText(/高リスク箇所が検出されました/i)

    // 閉じる
    fireEvent.click(toggle)
    const mobileContent = document.querySelector('.editor-mobile-suggestions__content')
    expect(mobileContent).toBeNull()
  })

  it('ハンバーガーメニューボタンが存在する', async () => {
    renderEditor()
    const menuButton = await screen.findByLabelText('編集提案を開閉')
    expect(menuButton).toBeInTheDocument()
  })

  it('ヘッダーのボタンにアイコンとラベルの両方が含まれる', async () => {
    renderEditor()
    const saveButton = await screen.findByLabelText('保存')
    expect(saveButton).toBeInTheDocument()
    expect(saveButton.querySelector('.editor-header__label')).toHaveTextContent('保存')
    expect(saveButton.querySelector('.editor-header__icon')).toBeInTheDocument()
  })
})
