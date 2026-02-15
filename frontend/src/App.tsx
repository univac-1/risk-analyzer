import { Routes, Route, Link, NavLink, useLocation } from 'react-router-dom'
import { UploadComponent } from './components/UploadComponent'
import { ProgressComponent } from './components/ProgressComponent'
import { ResultsComponent } from './components/ResultsComponent'
import { JobListComponent } from './components/JobListComponent'
import { EditorPage } from './components/editor/EditorPage'
function App() {
  const location = useLocation()
  const isEditorPage = /^\/jobs\/[^/]+\/editor$/.test(location.pathname)

  if (isEditorPage) {
    return (
      <Routes>
        <Route path="/jobs/:id/editor" element={<EditorPage />} />
      </Routes>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h1>Video Risk Analyzer</h1>
        </Link>
        <p>SNS投稿前の炎上リスクチェック支援ツール</p>
        <nav className="app-nav">
          <NavLink to="/" end>
            アップロード
          </NavLink>
          <NavLink to="/jobs">
            ジョブ一覧
          </NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<UploadComponent />} />
          <Route path="/jobs" element={<JobListComponent />} />
          <Route path="/jobs/:id/progress" element={<ProgressComponent />} />
          <Route path="/jobs/:id/results" element={<ResultsComponent />} />
          <Route path="/jobs/:id/editor" element={<EditorPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
