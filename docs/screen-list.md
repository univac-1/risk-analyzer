# 画面一覧

このドキュメントはフロントエンドの画面とルーティングをまとめたものです。

| 画面 | URL | コンポーネント | 補足 |
| --- | --- | --- | --- |
| アップロード | `/` | `frontend/src/components/UploadComponent.tsx` | 動画アップロードの入口 |
| ジョブ一覧 | `/jobs` | `frontend/src/components/JobListComponent.tsx` | 解析ジョブの一覧表示 |
| 進捗 | `/jobs/:id/progress` | `frontend/src/components/ProgressComponent.tsx` | 解析の進捗表示 |
| 結果 | `/jobs/:id/results` | `frontend/src/components/ResultsComponent.tsx` | 解析結果の表示 |
| エディタ | `/jobs/:id/editor` | `frontend/src/components/editor/EditorPage.tsx` | タイムライン編集 |

## 画面遷移

- アップロード -> 進捗: 「解析を開始」成功時に `/jobs/:id/progress` へ遷移
- 進捗 -> 結果: 解析完了ステータス検知で `/jobs/:id/results` に自動遷移
- 進捗（エラー時）-> ジョブ一覧/アップロード: 「ジョブ一覧へ」/「新規解析」ボタン
- ジョブ一覧 -> 結果/進捗: ジョブ行クリックで状態に応じて遷移
- ジョブ一覧 -> エディタ: 完了ジョブの「編集」ボタン
- ジョブ一覧 -> アップロード: 「新規解析」ボタン
- 結果 -> エディタ/ジョブ一覧/アップロード: 「タイムライン編集へ」(primary)/「ジョブ一覧へ」(secondary)/「新規解析」(secondary)
- エディタ -> ジョブ一覧: ヘッダー左「← ジョブ一覧」ボタン
- エディタ -> アップロード: ヘッダー右「新規解析」ボタン
- エディタ -> 結果: エクスポート完了時の「結果に戻る」ボタン
- グローバルナビ（エディタ以外）: ヘッダーの「アップロード」「ジョブ一覧」リンク

## API一覧（フロントエンド）

APIのベースURLは `VITE_API_URL` または `http://localhost:8000` です。`/jobs/:id` の `:id` はジョブIDに置き換えます。

| 画面 | メソッド | パス | 用途 | レスポンス主要フィールド |
| --- | --- | --- | --- | --- |
| アップロード | POST (multipart) | `/api/videos` | 動画アップロードと解析ジョブ作成 | `id`, `status`, `video_name`, `metadata`, `created_at` |
| ジョブ一覧 | GET | `/api/jobs` | ジョブ一覧取得 | `id`, `status`, `video_name`, `created_at`, `completed_at` |
| 進捗 | GET | `/api/jobs/:id/progress` | 解析進捗の取得（定期ポーリング） | `job_id`, `status`, `overall`, `phases`, `estimated_remaining_seconds` |
| 結果 | GET | `/api/jobs/:id/results` | 解析結果取得（動画URL含む） | `job`, `assessment`, `video_url` |
| エディタ | GET | `/api/jobs/:id/results` | 解析結果取得（編集提案の元データ） | `job`, `assessment`, `video_url` |
| エディタ | GET | `/api/jobs/:id/video-url` | 編集用動画URL取得 | `url`, `expires_at` |
| エディタ | GET | `/api/jobs/:id/edit-session` | 編集セッション取得 | `id`, `job_id`, `status`, `actions`, `updated_at` |
| エディタ | PUT | `/api/jobs/:id/edit-session` | 編集アクション保存 | `id`, `job_id`, `status`, `actions`, `updated_at` |
| エディタ | POST | `/api/jobs/:id/export` | エクスポート開始 | `export_id`, `status` |
| エディタ | GET | `/api/jobs/:id/export/status` | エクスポート進捗取得 | `export_id`, `status`, `progress`, `error_message` |
| エディタ | GET | `/api/jobs/:id/export/file` | エクスポート済み動画のダウンロード | バイナリ（MP4） |
| エディタ | GET | `/api/jobs/:id/export/download` | エクスポート済み動画URL取得 | `url`, `expires_at` |
