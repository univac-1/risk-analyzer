# GCPデプロイガイド

このドキュメントでは、Risk AnalyzerアプリケーションをGoogle Cloud Platform (GCP) にデプロイする手順を説明します。

## 前提条件

- Google Cloud アカウント
- GCP プロジェクト（課金が有効）
- `gcloud` CLI がインストールされていること
- `terraform` CLI がインストールされていること（v1.5.0以上）
- GitHub リポジトリ

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Cloud Run   │  │  Cloud Run   │  │  Cloud Run   │       │
│  │  (Frontend)  │  │  (Backend)   │  │  (Worker)    │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         │      ┌──────────┴──────────┐      │                │
│         │      │    VPC Connector    │      │                │
│         │      └──────────┬──────────┘      │                │
│         │                 │                 │                │
│  ┌──────┴─────────────────┴─────────────────┴──────┐        │
│  │                  Private VPC                     │        │
│  │  ┌─────────────┐         ┌─────────────────┐    │        │
│  │  │ Memorystore │         │    Cloud SQL    │    │        │
│  │  │  (Redis)    │         │  (PostgreSQL)   │    │        │
│  │  └─────────────┘         └─────────────────┘    │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
│  ┌──────────────┐  ┌──────────────────────────────┐         │
│  │Cloud Storage │  │     Google Cloud APIs        │         │
│  │  (Videos)    │  │ Speech-to-Text, Video Intel, │         │
│  │              │  │         Vertex AI            │         │
│  └──────────────┘  └──────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## セットアップ手順

### 1. GCPプロジェクトの準備

```bash
# プロジェクトIDを設定
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-northeast1"

# gcloudにログイン
gcloud auth login
gcloud config set project ${GCP_PROJECT_ID}

# アプリケーションデフォルト認証情報を設定
gcloud auth application-default login
```

### 2. Terraformによるインフラストラクチャのセットアップ

#### 2.1 Terraform Stateバケットの作成

最初に、Terraformの状態ファイルを保存するGCSバケットを作成します：

```bash
cd terraform/scripts
chmod +x bootstrap.sh
./bootstrap.sh ${GCP_PROJECT_ID}
```

#### 2.2 Terraform設定ファイルの編集

`terraform/terraform.tfvars` を編集して、プロジェクト固有の値を設定します：

```hcl
# terraform/terraform.tfvars
project_id        = "your-project-id"    # ← 実際のプロジェクトIDに変更
region            = "asia-northeast1"
github_repository = "owner/repo"          # ← 実際のGitHubリポジトリに変更
```

`terraform/backend.tf` のバケット名も更新します：

```hcl
# terraform/backend.tf
terraform {
  backend "gcs" {
    bucket = "your-project-id-terraform-state"  # ← 実際のバケット名に変更
    prefix = "terraform/state"
  }
}
```

#### 2.3 Terraformの実行

```bash
cd terraform

# 初期化
terraform init

# 構成の検証
terraform validate

# 実行計画の確認
terraform plan

# インフラストラクチャの作成
terraform apply
```

このコマンドで以下のリソースが作成されます：

| リソース              | 説明                                                |
| --------------------- | --------------------------------------------------- |
| **APIs**              | Cloud Run, Artifact Registry, Cloud SQL, Redis など |
| **Artifact Registry** | Dockerイメージ保存（`risk-analyzer`）               |
| **VPC Connector**     | サーバーレスVPCアクセス（`10.8.0.0/28`）            |
| **Memorystore Redis** | タスクキュー（BASIC tier, 1GB）                     |
| **Cloud SQL**         | PostgreSQL 15データベース                           |
| **Cloud Storage**     | 動画ファイル保存（7日ライフサイクル）               |
| **Service Account**   | Cloud Run用サービスアカウント                       |
| **Workload Identity** | GitHub Actions認証用                                |
| **Secret Manager**    | DBパスワード自動生成・保存                          |

#### 2.4 出力値の確認

```bash
# GitHub Actions用のシークレット値を確認
terraform output github_actions_secrets
```

### 3. GitHub Secretsの設定

GitHubリポジトリの Settings → Secrets and variables → Actions で以下のシークレットを設定：

```bash
# Terraformの出力値を使用
terraform output github_actions_secrets
```

| シークレット名        | 説明                           |
| --------------------- | ------------------------------ |
| `GCP_PROJECT_ID`      | GCPプロジェクトID              |
| `GCP_PROJECT_NUMBER`  | GCPプロジェクト番号            |
| `WIF_PROVIDER`        | Workload Identity プロバイダー |
| `WIF_SERVICE_ACCOUNT` | サービスアカウントメール       |
| `DB_CONNECTION_NAME`  | Cloud SQL接続名                |
| `DB_NAME`             | データベース名                 |
| `DB_USER`             | データベースユーザー           |
| `DB_PASSWORD_SECRET`  | Secret Managerのシークレット名 |
| `REDIS_HOST`          | Redis IPアドレス               |
| `GCS_BUCKET`          | Cloud Storageバケット名        |

### 4. デプロイの実行

タグをプッシュすると、GitHub Actionsによりデプロイが実行されます。

```bash
# タグを作成してプッシュ
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions は以下のステップを実行します：
1. **Test**: バックエンド・フロントエンドのテスト実行
2. **Build**: Dockerイメージのビルドとプッシュ（タグ名がイメージタグになります）
3. **Deploy**: Cloud Runへのデプロイ

**タグの命名規則**: `v` で始まるタグ（例: `v1.0.0`, `v1.2.3-beta`）がデプロイ対象です。

### 5. 手動デプロイ（初回または緊急時）

必要に応じて手動でデプロイすることも可能です：

```bash
# Dockerイメージをビルド
docker build -t ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/risk-analyzer/frontend:latest \
    -f frontend/Dockerfile.prod frontend

docker build -t ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/risk-analyzer/backend:latest \
    -f backend/Dockerfile backend

docker build -t ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/risk-analyzer/worker:latest \
    -f backend/Dockerfile.worker backend

# Artifact Registryにプッシュ
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/risk-analyzer/frontend:latest
docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/risk-analyzer/backend:latest
docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/risk-analyzer/worker:latest

# Cloud Runにデプロイ
gcloud run deploy risk-analyzer-frontend \
    --image=${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/risk-analyzer/frontend:latest \
    --region=${GCP_REGION} \
    --platform=managed \
    --allow-unauthenticated
```

## Terraform CI/CD

Terraformの変更は GitHub Actions で自動的に管理されます。

### 自動実行

- **Pull Request**: `terraform plan` を実行し、結果をPRにコメント
- **masterマージ**: `terraform apply` を自動実行

### 手動実行

GitHub Actions の workflow_dispatch から手動実行も可能：

1. Actions タブ → "Terraform" ワークフロー
2. "Run workflow" をクリック
3. アクションを選択（plan / apply / destroy）

## デプロイ後の確認

### サービスURLの確認

```bash
# Frontend URL
gcloud run services describe risk-analyzer-frontend \
    --region=${GCP_REGION} \
    --format="value(status.url)"

# Backend URL
gcloud run services describe risk-analyzer-backend \
    --region=${GCP_REGION} \
    --format="value(status.url)"
```

### ログの確認

```bash
# Frontendログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=risk-analyzer-frontend" --limit=50

# Backendログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=risk-analyzer-backend" --limit=50

# Workerログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=risk-analyzer-worker" --limit=50
```

### ヘルスチェック

```bash
# Backend health check
curl https://risk-analyzer-backend-xxxxx.asia-northeast1.run.app/api/health

# Frontend health check
curl https://risk-analyzer-frontend-xxxxx.asia-northeast1.run.app/health
```

## トラブルシューティング

### Terraform関連

**問題**: `terraform init` でバックエンドエラー

**解決策**:
1. bootstrap.sh が正常に実行されたか確認
2. backend.tf のバケット名が正しいか確認
3. 認証情報が設定されているか確認

```bash
# 認証確認
gcloud auth application-default print-access-token

# バケット確認
gcloud storage buckets describe gs://${GCP_PROJECT_ID}-terraform-state
```

### 接続エラー

**問題**: BackendがRedisやCloud SQLに接続できない

**解決策**:
1. VPC Connectorが正しく設定されているか確認
2. サービスアカウントに必要な権限があるか確認
3. Cloud SQL接続名が正しいか確認

```bash
# VPC Connector状態確認
gcloud compute networks vpc-access connectors describe risk-analyzer-connector --region=${GCP_REGION}

# Cloud SQL接続テスト
gcloud sql connect risk-analyzer-db --user=postgres
```

### ビルドエラー

**問題**: Dockerイメージのビルドに失敗

**解決策**:
1. ローカルでビルドを試す
2. Dockerfileの構文を確認
3. 依存関係が正しくインストールされているか確認

```bash
# ローカルビルドテスト
docker build -f backend/Dockerfile backend
docker build -f frontend/Dockerfile.prod frontend
```

### パフォーマンス問題

**問題**: レスポンスが遅い

**解決策**:
1. Cloud Runのインスタンス数を増やす
2. メモリ/CPU割り当てを増やす
3. min-instancesを設定してコールドスタートを回避

```bash
gcloud run services update risk-analyzer-backend \
    --region=${GCP_REGION} \
    --min-instances=1 \
    --memory=2Gi \
    --cpu=2
```

## インフラストラクチャの削除

Terraformで作成したリソースを削除するには：

```bash
cd terraform
terraform destroy
```

**注意**: 削除前にデータのバックアップを取得してください。

## コスト最適化

- **開発時**: min-instances=0 でコスト削減
- **本番時**: min-instances=1 でコールドスタート回避
- **Cloud SQL**: db-f1-micro で十分（小規模利用の場合）
- **Redis**: BASIC tier で十分（開発段階）

## セキュリティチェックリスト

- [ ] Cloud SQL パスワードは Secret Manager で自動生成・管理
- [ ] VPC Connector でプライベートネットワークを使用
- [ ] Workload Identity Federation を使用（サービスアカウントキー不要）
- [ ] Cloud Run サービスに最小権限の原則を適用
- [ ] Cloud Storage に適切なIAMポリシーを設定

## Terraformファイル構成

```
terraform/
├── main.tf           # メイン設定（モジュール統合）
├── variables.tf      # 変数定義
├── terraform.tfvars  # 変数値（要編集）
├── outputs.tf        # 出力定義
├── backend.tf        # GCS state設定（要編集）
├── modules/
│   ├── apis/              # API有効化
│   ├── artifact-registry/ # Dockerリポジトリ
│   ├── networking/        # VPC Connector
│   ├── redis/             # Memorystore Redis
│   ├── cloudsql/          # Cloud SQL + Secret Manager
│   ├── storage/           # Cloud Storage
│   ├── iam/               # Service Account + IAM
│   └── workload-identity/ # GitHub Actions認証
└── scripts/
    └── bootstrap.sh       # Stateバケット初期作成
```
