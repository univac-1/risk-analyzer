import { Routes, Route, Link } from 'react-router-dom'
import { UploadComponent } from './components/UploadComponent'
import { ProgressComponent } from './components/ProgressComponent'
import { ResultsComponent } from './components/ResultsComponent'
import { JobListComponent } from './components/JobListComponent'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h1>Video Risk Analyzer</h1>
        </Link>
        <p>SNS投稿前の炎上リスクチェック支援ツール</p>
        <nav className="app-nav">
          <Link to="/">アップロード</Link>
          <Link to="/jobs">ジョブ一覧</Link>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<UploadComponent />} />
          <Route path="/jobs" element={<JobListComponent />} />
          <Route path="/jobs/:id/progress" element={<ProgressComponent />} />
          <Route path="/jobs/:id/results" element={<ResultsComponent />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
