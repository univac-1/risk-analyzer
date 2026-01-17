# Google Cloud 認証セットアップ手順

## 前提条件

- Google Cloud アカウントを持っていること
- プロジェクト「agentic-ai-hackathon-vol4」へのアクセス権限があること

## 認証方式

このプロジェクトは **Application Default Credentials (ADC)** を使用します。サービスアカウントキーファイル（JSON）は使用しません。

| 環境 | 認証方式 |
|------|---------|
| ローカル開発 | `gcloud auth application-default login` |
| Docker開発 | ADC をコンテナにマウント |
| Cloud Run | デフォルトサービスアカウント（自動） |

## 1. gcloud CLI のインストール

### Linux/macOS

```bash
# ダウンロード
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz

# 展開
tar -xzf google-cloud-cli-linux-x86_64.tar.gz

# インストール
./google-cloud-sdk/install.sh --quiet --path-update true

# シェルを再起動するか、パスを読み込み
source ~/google-cloud-sdk/path.bash.inc

# ダウンロードファイルを削除
rm google-cloud-cli-linux-x86_64.tar.gz
```

### Windows

[Google Cloud SDK インストーラー](https://cloud.google.com/sdk/docs/install?hl=ja) をダウンロードして実行してください。

インストール確認：

```bash
gcloud --version
```

## 2. gcloud CLI の認証

```bash
# ブラウザが開き、Google アカウントでログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project agentic-ai-hackathon-vol4
```

## 3. Application Default Credentials (ADC) の設定

### ローカル開発（Docker なし）

```bash
gcloud auth application-default login
```

ブラウザが開き、Google アカウントでログインすると、認証情報が自動的に保存されます：

- Linux/macOS: `~/.config/gcloud/application_default_credentials.json`
- Windows: `%APPDATA%\gcloud\application_default_credentials.json`

Google Cloud SDK は自動的にこのファイルを検出して使用します。

### Docker 開発環境

`docker-compose.yml` で ADC ディレクトリを自動マウントしています。

**Linux/macOS の場合:**

```bash
# ADC を取得（初回のみ）
gcloud auth application-default login

# Docker Compose を起動
docker-compose up
```

**Windows の場合:**

```powershell
# ADC を取得（初回のみ）
gcloud auth application-default login

# ADC パスを設定して Docker Compose を起動
$env:GOOGLE_ADC_PATH="$env:APPDATA\gcloud"
docker-compose up
```

または `.env.local` に追加：

```
GOOGLE_ADC_PATH=C:\Users\YourName\AppData\Roaming\gcloud
```

## 4. Cloud Run デプロイ

Cloud Run では、サービスに紐付けられたサービスアカウントが自動的に使用されます。

```bash
# デプロイ時にサービスアカウントを指定
gcloud run deploy video-risk-analyzer \
    --image gcr.io/agentic-ai-hackathon-vol4/video-risk-analyzer \
    --service-account video-analyzer@agentic-ai-hackathon-vol4.iam.gserviceaccount.com \
    --region us-central1
```

**キーファイルは不要です。** Cloud Run のメタデータサービスが認証を自動処理します。

## 5. サービスアカウントの設定（Cloud Run 用）

Cloud Run で使用するサービスアカウントを作成・設定します。

### サービスアカウントの作成

```bash
# サービスアカウント一覧を確認
gcloud iam service-accounts list

# 新規作成する場合
gcloud iam service-accounts create video-analyzer \
    --display-name="Video Risk Analyzer Service Account" \
    --description="Service account for Video Risk Analyzer application"
```

### 権限の付与

```bash
SA_EMAIL="video-analyzer@agentic-ai-hackathon-vol4.iam.gserviceaccount.com"

# Vertex AI ユーザー権限
gcloud projects add-iam-policy-binding agentic-ai-hackathon-vol4 \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/aiplatform.user"

# Cloud Storage 権限（動画アップロード用）
gcloud projects add-iam-policy-binding agentic-ai-hackathon-vol4 \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin"

# Speech-to-Text 権限
gcloud projects add-iam-policy-binding agentic-ai-hackathon-vol4 \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/speech.client"

# Video Intelligence 権限
gcloud projects add-iam-policy-binding agentic-ai-hackathon-vol4 \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/videointelligence.admin"
```

## トラブルシューティング

### ADC が見つからないエラー

```
Could not automatically determine credentials
```

**解決方法:**

```bash
# ADC を再取得
gcloud auth application-default login
```

### Docker で ADC がマウントされない

**Windows の場合:**

```powershell
# パスを確認
echo $env:APPDATA\gcloud

# 環境変数を設定
$env:GOOGLE_ADC_PATH="$env:APPDATA\gcloud"
docker-compose up
```

### 権限エラーが出る場合

```bash
# 自分のアカウントの権限を確認
gcloud projects get-iam-policy agentic-ai-hackathon-vol4 \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:YOUR_EMAIL"
```

### ADC の情報を確認

```bash
# 現在の ADC 設定を確認
gcloud auth application-default print-access-token
```

## 非推奨: サービスアカウントキーファイル

> **注意**: サービスアカウントキーファイル（JSON）の使用は非推奨です。
> キーファイルは漏洩リスクがあり、定期的なローテーションが必要です。
> 可能な限り ADC を使用してください。

やむを得ずキーファイルが必要な場合（CI/CD パイプライン等）は、以下の手順でSecret Manager 等を使用してください：

```bash
# キーを Secret Manager に保存
gcloud secrets create gcp-service-account-key \
    --data-file=./credentials/service-account.json

# CI/CD でシークレットを取得
gcloud secrets versions access latest --secret=gcp-service-account-key > /tmp/key.json
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/key.json
```
