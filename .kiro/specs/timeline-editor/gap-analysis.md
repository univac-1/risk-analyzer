# Gap Analysis: Timeline Editor

## 概要

タイムラインエディタ機能の実装にあたり、既存コードベースとの差分を分析しました。

### 分析サマリー

- **既存UI**: モック（`mock/`）と本番フロントエンド（`frontend/`）が別々に存在
- **動画再生**: ResultsComponentに動画プレーヤーがあるが、`videoUrl`が未設定で動作しない
- **FFmpeg**: 音声抽出・フレーム抽出に使用済み、編集機能は未実装
- **データモデル**: 編集セッション・編集アクション用のモデルが未定義
- **推奨アプローチ**: ハイブリッド（既存拡張 + 新規コンポーネント）

---

## 1. 現状調査

### 1.1 フロントエンド構造

| パス | 説明 | 状態 |
|------|------|------|
| `frontend/src/components/ResultsComponent.tsx` | 結果表示・動画プレーヤー | ✅ 存在（動画URL未設定） |
| `frontend/src/components/` | Upload, JobList, Progress | ✅ 存在 |
| `frontend/src/types/index.ts` | 型定義 | ✅ 存在（編集用型なし） |
| `frontend/src/services/api.ts` | APIクライアント | ✅ 存在 |
| `mock/components/video-editor.tsx` | タイムラインエディタUI | ✅ モック存在 |
| `mock/components/timeline.tsx` | タイムラインコンポーネント | ✅ モック存在 |

### 1.2 バックエンド構造

| パス | 説明 | 状態 |
|------|------|------|
| `backend/app/api/routes/jobs.py` | ジョブAPI | ✅ 存在 |
| `backend/app/services/storage.py` | S3/MinIO操作 | ✅ 存在（presigned URLあり） |
| `backend/app/services/progress.py` | 進捗管理（Redis） | ✅ 存在 |
| `backend/app/models/job.py` | DB モデル | ✅ 存在（編集用なし） |
| `backend/app/tasks/analyze.py` | Celeryタスク | ✅ 存在 |

### 1.3 FFmpeg使用状況

| ファイル | 用途 | 編集機能 |
|----------|------|----------|
| `audio_analyzer.py` | 音声抽出（PCM変換） | ❌ なし |
| `video_analyzer.py` | フレーム抽出（JPEG） | ❌ なし |

**FFmpegコマンド（現状）**:
```python
# 音声抽出
ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {output_path}

# フレーム抽出
ffmpeg -i {video_path} -vf fps=1/{interval} {output_pattern}
```

### 1.4 データフロー

```
[Upload] → [S3保存] → [Celeryタスク] → [分析] → [結果DB保存]
                                                     ↓
[Results画面] ← [GET /api/jobs/{id}/results] ← [DB読み取り]
```

**問題点**: Results APIが動画URLを返却しない

---

## 2. 要件実現可能性分析

### 2.1 要件とアセットのマッピング

| 要件 | 既存アセット | ギャップ |
|------|-------------|----------|
| Req1: 動画プレビュー | ResultsComponent（動画要素あり） | Missing: 動画URL取得 |
| Req2: 再生コントロール | ResultsComponent（基本コントロール） | Missing: 5秒スキップ、音量 |
| Req3: リスクスコアグラフ | mock/risk-graph.tsx | Missing: 本番移植 |
| Req4: タイムライン | mock/timeline.tsx | Missing: 本番移植 |
| Req5: 編集提案パネル | mock/editing-suggestions.tsx | Missing: 本番移植、RiskItem連携 |
| Req6: 編集アクション拡張 | なし | Missing: 全て新規 |
| Req7: ヘッダーアクション | mock/video-editor.tsx（UI） | Missing: 保存・エクスポートAPI |
| Req8: 動画編集処理 | FFmpeg（インストール済み） | Missing: 編集コマンド実装 |
| Req9: レスポンシブ | mock（対応済み） | Constraint: モック踏襲 |

### 2.2 技術的ニーズ

**データモデル（新規必要）**:
```typescript
// 編集セッション
interface EditSession {
  id: string
  jobId: string
  actions: EditAction[]
  status: 'draft' | 'exporting' | 'completed'
  createdAt: string
  updatedAt: string
}

// 編集アクション
interface EditAction {
  id: string
  riskItemId?: string
  type: 'cut' | 'mute' | 'mosaic' | 'telop' | 'skip'
  startTime: number
  endTime: number
  options?: MosaicOptions | TelopOptions
}
```

**API（新規必要）**:
```
GET    /api/jobs/{id}/video-url      # 動画署名付きURL
POST   /api/jobs/{id}/edit-session   # セッション作成
GET    /api/jobs/{id}/edit-session   # セッション取得
PUT    /api/jobs/{id}/edit-session   # セッション更新
POST   /api/jobs/{id}/export         # エクスポート開始
GET    /api/jobs/{id}/export/status  # エクスポート進捗
GET    /api/jobs/{id}/export/download # ダウンロードURL
```

**FFmpegコマンド（新規必要）**:
```bash
# カット
ffmpeg -i input.mp4 -vf "select='not(between(t,10,20))'" -af "aselect='not(between(t,10,20))'" output.mp4

# ミュート
ffmpeg -i input.mp4 -af "volume=enable='between(t,10,20)':volume=0" output.mp4

# モザイク
ffmpeg -i input.mp4 -vf "delogo=x=100:y=100:w=200:h=200:enable='between(t,10,20)'" output.mp4

# テロップ
ffmpeg -i input.mp4 -vf "drawtext=text='テキスト':enable='between(t,10,20)'" output.mp4
```

### 2.3 複雑性シグナル

| 領域 | 複雑性 | 理由 |
|------|--------|------|
| モックUI移植 | 中 | 既存コード流用、API連携追加 |
| 動画URL取得 | 低 | storage.pyにpresigned_url実装済み |
| 編集セッション管理 | 中 | 新規モデル・API、状態管理 |
| FFmpeg編集処理 | 高 | 複数編集統合、エラーハンドリング |
| リアルタイム進捗 | 低 | 既存SSEパターン流用 |

---

## 3. 実装アプローチ選択肢

### Option A: 既存コンポーネント拡張

**概要**: ResultsComponentを拡張してタイムラインエディタ機能を追加

**対象ファイル**:
- `frontend/src/components/ResultsComponent.tsx` → 大幅拡張
- `backend/app/api/routes/jobs.py` → エンドポイント追加
- `backend/app/models/job.py` → EditSession, EditAction追加

**トレードオフ**:
- ✅ ファイル数が少ない
- ✅ 既存ルーティング活用
- ❌ ResultsComponentが肥大化（現在229行→推定1000行以上）
- ❌ 責務の混在（結果表示 + 編集）

**評価**: 推奨しない（コンポーネント肥大化リスク）

---

### Option B: 新規コンポーネント作成

**概要**: モックUIを新規ページ・コンポーネントとして本番実装

**対象ファイル**:
```
frontend/src/
├── components/
│   └── editor/
│       ├── TimelineEditor.tsx        (メインコンポーネント)
│       ├── VideoPreview.tsx          (動画プレビュー)
│       ├── Timeline.tsx              (タイムライン)
│       ├── RiskGraph.tsx             (リスクグラフ)
│       ├── EditingSuggestions.tsx    (編集提案)
│       ├── VideoControls.tsx         (再生コントロール)
│       └── types.ts                  (エディタ用型)
├── pages/
│   └── EditorPage.tsx                (新規ルート)
└── hooks/
    └── useEditSession.ts             (編集セッション管理)

backend/app/
├── api/routes/
│   └── editor.py                     (新規ルーター)
├── models/
│   └── edit_session.py               (新規モデル)
├── schemas/
│   └── editor.py                     (新規スキーマ)
├── services/
│   └── video_editor.py               (FFmpeg編集)
└── tasks/
    └── export.py                     (エクスポートタスク)
```

**トレードオフ**:
- ✅ 責務の明確な分離
- ✅ テスト容易性
- ✅ モックからの移植が直接的
- ❌ ファイル数が多い
- ❌ 既存コードとの重複可能性

**評価**: 推奨（クリーンアーキテクチャ）

---

### Option C: ハイブリッドアプローチ

**概要**: 既存拡張（API・モデル）+ 新規作成（UIコンポーネント）

**対象ファイル**:
```
# 既存拡張
backend/app/api/routes/jobs.py      → video-url, edit-session追加
backend/app/models/job.py           → EditSession, EditAction追加

# 新規作成
frontend/src/components/editor/     → モックUI移植
frontend/src/pages/EditorPage.tsx   → 新規ルート
backend/app/services/video_editor.py → FFmpeg編集
backend/app/tasks/export.py         → エクスポートタスク
```

**トレードオフ**:
- ✅ バランスの取れたアプローチ
- ✅ 既存ルーターの再利用（jobsルーター）
- ✅ UIは独立して開発可能
- ❌ jobs.pyの責務が拡大
- ❌ 判断ポイントが多い

**評価**: 妥協案として許容可能

---

## 4. 工数・リスク評価

| 領域 | 工数 | リスク | 根拠 |
|------|------|--------|------|
| UI移植（モック→本番） | M (3-7日) | Low | モック実装済み、API連携追加 |
| 動画URL API | S (1-3日) | Low | storage.pyに実装済み |
| 編集セッション管理 | M (3-7日) | Medium | 新規モデル・API、状態管理 |
| FFmpeg編集処理 | L (1-2週間) | High | 複合編集、エラー処理、テスト |
| エクスポートタスク | M (3-7日) | Medium | Celery既存パターン流用 |
| 全体 | **L (1-2週間)** | **Medium** | 並列開発可能部分あり |

---

## 5. 設計フェーズへの推奨事項

### 推奨アプローチ: **Option B（新規コンポーネント作成）**

**理由**:
1. モックUIが独立して完成しており、直接移植可能
2. 編集機能は結果表示と責務が異なる
3. 将来の機能拡張（波形表示、4トラック等）に対応しやすい

### 設計フェーズでの調査項目

| 項目 | 内容 |
|------|------|
| FFmpeg複合編集 | 複数編集アクションの統合方法、フィルターチェーン設計 |
| モザイク領域指定 | UI/UXパターン、座標データの保存形式 |
| テロップ配置 | フォント、位置、スタイル指定のUI設計 |
| 進捗表示 | FFmpegの進捗取得方法（`-progress`オプション） |
| 音声波形表示 | Web Audio API vs サーバーサイド生成 |

### 優先実装順序

1. **Phase 1**: 動画URL API + UI基盤（モック移植）
2. **Phase 2**: 編集セッション管理 + カット機能
3. **Phase 3**: ミュート・モザイク・テロップ機能
4. **Phase 4**: エクスポート・ダウンロード機能

---

## 6. 次のステップ

```
/kiro:spec-design timeline-editor
```

設計フェーズでは以下を詳細化:
- データモデル定義
- API仕様
- コンポーネント設計
- FFmpegコマンド仕様
