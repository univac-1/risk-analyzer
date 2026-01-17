# Video Risk Analyzer

SNS投稿前の動画コンテンツに対する炎上リスクチェック支援ツール

## 概要

動画をアップロードすると、AI が以下の3つの観点でリスクを自動検出します：

- **攻撃性**: 匿名性を利用した攻撃的表現、過激な表現など
- **差別性**: 人種・性別・性的指向などへの偏見に基づく表現
- **誤解を招く表現**: 断定的・誇張・ステレオタイプに基づく表現

## 技術スタック

| レイヤー | 技術 |
|----------|------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python 3.12 + FastAPI |
| Task Queue | Celery 5.x + Redis 7 |
| Database | PostgreSQL 15 |
| Storage | MinIO (ローカル) / GCS (本番) |
| AI/ML | Google Cloud Speech-to-Text, Video Intelligence API, Gemini API |

## 必要条件

- Docker & Docker Compose
- gcloud CLI
- Google Cloud プロジェクト（API有効化済み）
  - Cloud Speech-to-Text API
  - Video Intelligence API
  - Vertex AI API (Gemini)

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd risk-analyzer
```

### 2. 環境変数の設定

```bash
# .env.localファイルを作成
cp .env.example .env.local
```

`.env.local` を編集して、Google Cloud プロジェクトIDを入力：

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
```

### 3. Google Cloud 認証の設定

Application Default Credentials (ADC) を使用します。

```bash
# gcloud CLI で認証（ブラウザが開きます）
gcloud auth application-default login

# プロジェクトを設定
gcloud config set project your-project-id
```

**Windows の場合**は、追加で環境変数を設定：

```powershell
# .env.local に追加
GOOGLE_ADC_PATH=C:\Users\YourName\AppData\Roaming\gcloud
```

詳細は [docs/gcloud-service-account-setup.md](docs/gcloud-service-account-setup.md) を参照してください。

## 実行方法

### 開発環境の起動

```bash
# 初回起動（イメージのビルド含む）
docker-compose up --build

# バックグラウンドで起動
docker-compose up -d

# 起動確認
docker-compose ps
```

### アクセスURL

| サービス | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API ドキュメント | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

### サービスの停止

```bash
# 停止
docker-compose down

# データも含めて完全削除
docker-compose down -v
```

## 使い方

1. http://localhost:3000 にアクセス
2. 「動画をアップロード」エリアにmp4ファイルをドラッグ&ドロップ
3. メタ情報を入力
   - 用途（例: 新製品紹介動画）
   - 投稿先媒体（Twitter, Instagram, YouTube, TikTok, その他）
   - 想定ターゲット（例: 20-30代の女性）
4. 「解析を開始」をクリック
5. 解析完了後、リスク箇所が一覧表示される

## 開発

### ログの確認

```bash
# 全サービスのログ
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend
```

### データベースマイグレーション

```bash
# マイグレーション実行
docker-compose exec backend alembic upgrade head

# 新しいマイグレーション作成
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### テスト実行

```bash
# バックエンドテスト
docker-compose exec backend pytest tests/ -v

# カバレッジ付きテスト
docker-compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing
```

## API エンドポイント

| メソッド | エンドポイント | 説明 |
|----------|----------------|------|
| POST | `/api/videos` | 動画アップロード・解析開始 |
| GET | `/api/jobs` | ジョブ一覧取得 |
| GET | `/api/jobs/:id` | ジョブ詳細取得 |
| GET | `/api/jobs/:id/progress` | 進捗状況取得 |
| GET | `/api/jobs/:id/results` | 解析結果取得 |
| GET | `/api/jobs/:id/events` | SSEによるリアルタイム進捗 |

詳細は http://localhost:8000/docs を参照

## トラブルシューティング

### MinIOバケットが作成されない

初回起動時、MinIOのバケットを手動で作成する必要がある場合：

```bash
# MinIO CLIでバケット作成
docker-compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker-compose exec minio mc mb local/videos
```

または MinIO Console (http://localhost:9001) から作成

### Google Cloud API エラー

1. ADC が正しく設定されているか確認
   ```bash
   gcloud auth application-default print-access-token
   ```

2. 必要なAPIが有効化されているか確認

3. アカウントに適切な権限があるか確認
   ```bash
   # 必要な権限
   # - Speech-to-Text: roles/speech.client
   # - Video Intelligence: roles/videointelligence.admin
   # - Vertex AI: roles/aiplatform.user
   ```

4. Docker で ADC がマウントされない場合（Windows）
   ```powershell
   $env:GOOGLE_ADC_PATH="$env:APPDATA\gcloud"
   docker-compose up
   ```

### ポートが使用中

他のサービスがポートを使用している場合、`docker-compose.yml` でポート番号を変更：

```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # 3000 -> 3001 に変更
```

## ライセンス

MIT License
