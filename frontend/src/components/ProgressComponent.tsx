import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { ProgressStatus, PhaseProgress } from "../types";
import "./ProgressComponent.css";

const PHASE_LABELS: Record<string, string> = {
  audio: "音声解析",
  video: "映像解析",
  risk: "リスク評価",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "待機中",
  processing: "処理中",
  completed: "完了",
  failed: "失敗",
};

function formatTime(seconds: number | null): string {
  if (seconds === null || seconds <= 0) return "計算中...";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins > 0) {
    return `約${mins}分${secs}秒`;
  }
  return `約${secs}秒`;
}

function PhaseProgressBar({
  phase,
  data,
}: {
  phase: string;
  data: PhaseProgress;
}) {
  const label = PHASE_LABELS[phase] || phase;
  const statusLabel = STATUS_LABELS[data.status] || data.status;

  return (
    <div className={`phase-progress ${data.status}`}>
      <div className="phase-header">
        <span className="phase-label">{label}</span>
        <span className="phase-status">{statusLabel}</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${data.progress}%` }} />
      </div>
      <span className="progress-percent">{data.progress.toFixed(0)}%</span>
    </div>
  );
}

export function ProgressComponent() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [progress, setProgress] = useState<ProgressStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchProgress = async () => {
      try {
        const data = await api.get<ProgressStatus>(`/api/jobs/${id}/progress`);
        setProgress(data);

        if (data.status === "completed") {
          navigate(`/jobs/${id}/results`);
        } else if (data.status === "failed") {
          setError("解析処理でエラーが発生しました");
        }
      } catch (err) {
        setError("進捗の取得に失敗しました");
      }
    };

    fetchProgress();
    const interval = setInterval(fetchProgress, 2000);

    return () => clearInterval(interval);
  }, [id, navigate]);

  if (error) {
    return (
      <div className="progress-container">
        <div className="error-state">
          <h2>エラーが発生しました</h2>
          <p>{error}</p>
          <div className="error-state__actions">
            <button className="primary-button" onClick={() => navigate("/jobs")}>ジョブ一覧へ</button>
            <button className="ghost-button" onClick={() => navigate("/")}>新規解析</button>
          </div>
        </div>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="progress-container">
        <div className="loading-state">
          <p>読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="progress-container">
      <div className="progress-header">
        <h2>解析中</h2>
        <p className="overall-status">
          全体進捗: <strong>{progress.overall.toFixed(0)}%</strong>
        </p>
        <p className="remaining-time">
          推定残り時間: {formatTime(progress.estimated_remaining_seconds)}
        </p>
      </div>

      <div className="overall-progress">
        <div className="progress-bar large">
          <div
            className="progress-fill"
            style={{ width: `${progress.overall}%` }}
          />
        </div>
      </div>

      <div className="phases-progress">
        {Object.entries(progress.phases)
          .filter(([phase]) => phase !== 'ocr')
          .map(([phase, data]) => (
            <PhaseProgressBar key={phase} phase={phase} data={data} />
          ))}
      </div>

      <div className="progress-note">
        <p>
          解析完了後、自動的に結果画面に遷移します。
          <br />
          このページを閉じても解析は継続されます。
        </p>
      </div>
    </div>
  );
}
