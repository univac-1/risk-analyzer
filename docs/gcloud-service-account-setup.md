# Google Cloud サービスアカウントキー取得手順

## 前提条件

- Google Cloud アカウントを持っていること
- プロジェクト「agentic-ai-hackathon-vol4」へのアクセス権限があること

## 1. gcloud CLI のインストール

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

## 3. Application Default Credentials（開発用）

ローカル開発では ADC（Application Default Credentials）を使用するのが簡単です：

```bash
gcloud auth application-default login
```

この方法では、ローカル開発用の一時的な認証情報が自動的に設定されます。

## 4. サービスアカウントの作成（必要な場合）

```bash
# サービスアカウント一覧を確認
gcloud iam service-accounts list

# 新規作成する場合（例: video-analyzer という名前で作成）
gcloud iam service-accounts create video-analyzer \
    --display-name="Video Risk Analyzer Service Account" \
    --description="Service account for Video Risk Analyzer application"
```

## 5. サービスアカウントに権限を付与

Vertex AI や Cloud Storage を使用する場合、以下の権限が必要です：

```bash
# サービスアカウントのメールアドレスを確認
SA_EMAIL="video-analyzer@agentic-ai-hackathon-vol4.iam.gserviceaccount.com"

# Vertex AI ユーザー権限
gcloud projects add-iam-policy-binding agentic-ai-hackathon-vol4 \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/aiplatform.user"

# Cloud Storage 権限（動画アップロード用）
gcloud projects add-iam-policy-binding agentic-ai-hackathon-vol4 \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin"
```

## 6. サービスアカウントキー（JSONファイル）の取得

```bash
# credentials ディレクトリを作成
mkdir -p credentials

# キーファイルを生成してダウンロード
gcloud iam service-accounts keys create ./credentials/service-account.json \
    --iam-account=video-analyzer@agentic-ai-hackathon-vol4.iam.gserviceaccount.com
```

**注意**: キーファイルは機密情報です。Git にコミットしないでください。

## 7. 環境変数の設定

取得したキーファイルを使用するため、環境変数を設定します：

```bash
export GOOGLE_APPLICATION_CREDENTIALS="./credentials/service-account.json"
```

または `.env.local` ファイルに追加：

```
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
```

## トラブルシューティング

### 権限エラーが出る場合

```bash
# 自分のアカウントの権限を確認
gcloud projects get-iam-policy agentic-ai-hackathon-vol4 \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:YOUR_EMAIL"
```

### サービスアカウントキーの再発行

```bash
# 既存のキーを一覧表示
gcloud iam service-accounts keys list \
    --iam-account=video-analyzer@agentic-ai-hackathon-vol4.iam.gserviceaccount.com

# 古いキーを削除（KEY_ID を指定）
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=video-analyzer@agentic-ai-hackathon-vol4.iam.gserviceaccount.com

# 新しいキーを作成
gcloud iam service-accounts keys create ./credentials/service-account.json \
    --iam-account=video-analyzer@agentic-ai-hackathon-vol4.iam.gserviceaccount.com
```

## Google Cloud Console（Web UI）での取得方法

CLI を使用しない場合は、以下の手順で Web UI から取得できます：

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクト「agentic-ai-hackathon-vol4」を選択
3. 左メニューから「IAM と管理」→「サービスアカウント」を選択
4. 使用するサービスアカウントをクリック
5. 「キー」タブを選択
6. 「鍵を追加」→「新しい鍵を作成」
7. 「JSON」を選択して「作成」
8. JSON ファイルが自動的にダウンロードされる
9. ダウンロードしたファイルを `credentials/service-account.json` として配置
