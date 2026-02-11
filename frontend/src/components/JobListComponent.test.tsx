import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import { JobListComponent } from './JobListComponent'

// --- mocks ---------------------------------------------------------------

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../services/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue([
      {
        id: 'job-1',
        status: 'completed',
        video_name: 'completed-video.mp4',
        created_at: '2026-01-01T00:00:00Z',
        completed_at: '2026-01-01T01:00:00Z',
      },
      {
        id: 'job-2',
        status: 'processing',
        video_name: 'processing-video.mp4',
        created_at: '2026-01-02T00:00:00Z',
        completed_at: null,
      },
    ]),
  },
}))

// --- helpers -------------------------------------------------------------

function renderJobList() {
  return render(
    <MemoryRouter>
      <JobListComponent />
    </MemoryRouter>
  )
}

// --- tests ---------------------------------------------------------------

describe('JobListComponent - エディタ導線 (Task 13.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('完了済みジョブにエディタへの編集ボタンが表示される', async () => {
    renderJobList()
    const editButton = await screen.findByLabelText('編集')
    expect(editButton).toBeInTheDocument()
  })

  it('編集ボタンクリックでエディタページへ遷移する', async () => {
    renderJobList()
    const editButton = await screen.findByLabelText('編集')
    fireEvent.click(editButton)
    expect(mockNavigate).toHaveBeenCalledWith('/jobs/job-1/editor')
  })

  it('処理中ジョブには編集ボタンが表示されない', async () => {
    renderJobList()
    await screen.findByText('completed-video.mp4')
    // processing-video.mp4の行には編集ボタンがない
    const editButtons = screen.getAllByLabelText('編集')
    expect(editButtons).toHaveLength(1)
  })
})
