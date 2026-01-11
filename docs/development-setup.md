# 開発環境セットアップガイド

このドキュメントでは、ローカル環境での開発セットアップ手順を説明します。

## 前提条件

以下のツールがインストールされていること：

- [Docker](https://docs.docker.com/engine/install/ubuntu/)（インフラサービス用）
- [Python 3.12](https://www.python.org/downloads/) + [Poetry](https://python-poetry.org/docs/#installation)
- [Node.js 20](https://nodejs.org/) + npm
- [gcloud CLI](./gcloud-service-account-setup.md)
- ffmpeg（動画処理用）

### ffmpeg のインストール

```bash
sudo apt-get update && sudo apt-get install ffmpeg
```

## クイックスタート

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd risk-analyzer
```

### 2. 環境変数ファイルを作成

```bash
cp .env.example .env.local
```

必要に応じて `.env.local` を編集してください。

### 3. Google Cloud 認証

```bash
gcloud auth application-default login
```

ブラウザが開くので、Google アカウントでログインしてください。
詳細は [Google Cloud 認証設定](./gcloud-service-account-setup.md) を参照してください。

### 4. インフラサービスを起動

PostgreSQL、Redis、MinIO を Docker Compose で起動します：

```bash
docker compose up -d db redis minio
```

### 5. Backend のセットアップ

```bash
cd backend

# 依存関係をインストール
poetry install

# データベースマイグレーションを実行
poetry run alembic upgrade head

# 開発サーバーを起動
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Celery Worker を起動（別ターミナル）

```bash
cd backend
poetry run celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### 7. Frontend のセットアップ（別ターミナル）

```bash
cd frontend

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

## 開発環境の構成

### 必要なツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Python | 3.12 | バックエンド開発 |
| Poetry | latest | Python パッケージ管理 |
| Node.js | 20.x | フロントエンド開発 |
| npm | latest | Node.js パッケージ管理 |
| gcloud CLI | latest | Google Cloud 操作 |
| ffmpeg | latest | 動画処理 |
| Docker | latest | インフラサービス |

### サービス

| サービス | ポート | 説明 |
|----------|--------|------|
| Frontend (Vite) | 5173 | React 開発サーバー |
| Backend (FastAPI) | 8000 | API サーバー |
| PostgreSQL | 5432 | データベース |
| Redis | 6379 | キャッシュ / Celery ブローカー |
| MinIO | 9000 | S3 互換オブジェクトストレージ |
| MinIO Console | 9001 | MinIO 管理画面 |

## 環境変数

開発時の環境変数は `.env.local` で設定します。

```bash
# .env.local の例
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/video_risk_analyzer
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=videos
GOOGLE_CLOUD_PROJECT=agentic-ai-hackathon-vol4
```

## Google Cloud 認証

### 開発時（Application Default Credentials）

```bash
gcloud auth application-default login
```

### 本番用（サービスアカウントキー）

1. サービスアカウントキーを取得（[手順](./gcloud-service-account-setup.md)）
2. `credentials/service-account.json` として配置
3. 環境変数を設定：

```bash
export GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
```

## Docker Compose で全サービスを起動

すべてのサービスを Docker で起動する場合：

```bash
docker compose up -d
```

この場合、ローカルで Backend/Frontend を起動する必要はありません。

## よくあるトラブルシューティング

### ポートが既に使用されている

```bash
# 使用中のポートを確認
lsof -i :5173
lsof -i :8000

# プロセスを終了
kill -9 <PID>
```

### 依存関係のエラー

```bash
# Backend
cd backend
poetry install

# Frontend
cd frontend
rm -rf node_modules
npm install
```

### データベース接続エラー

```bash
# PostgreSQL が起動しているか確認
docker compose ps db

# マイグレーションを再実行
cd backend
poetry run alembic upgrade head
```

### Docker コンテナの再起動

```bash
# サービスを再起動
docker compose restart db redis minio

# ログを確認
docker compose logs -f db
```
