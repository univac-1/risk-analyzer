# Design Document

## Overview

**Purpose**: 本機能は、SNS投稿前の動画コンテンツに対する炎上リスクを事前検知し、広報担当者の投稿判断を支援する。

**Users**: SaaSベンダーの広報担当者が、投稿前チェックワークフローにおいて本ツールを使用する。動画をアップロードし、リスク箇所の確認と対処判断を行う。

**Impact**: 投稿前チェックを経験と勘から、AI解析に基づく客観的リスク評価へ移行させ、炎上リスクの軽減と担当者の心理的負担軽減を実現する。

### Goals
- 動画内の音声・テキスト・映像を並列解析し、炎上リスク箇所を自動検出
- リスク箇所をタイムコード・根拠・スコア付きで提示
- 攻撃性・差別性・誤解を招く表現の3観点でリスク評価
- 解析進捗のリアルタイム表示

### Non-Goals
- 動画の編集・修正機能
- SNSへの直接投稿機能
- リアルタイムストリーミング解析
- 多言語対応（初期リリースは日本語のみ）

## Architecture

### Architecture Pattern & Boundary Map

```mermaid
graph TB
    subgraph CloudRunFrontend[Cloud Run - Frontend]
        UI[Web UI - React]
    end

    subgraph CloudRunBackend[Cloud Run - Backend API]
        API[API Gateway]
    end

    subgraph TaskQueue[Task Queue]
        Redis[(Redis)]
    end

    subgraph CloudRunWorker[Cloud Run - Worker]
        CeleryWorker[Celery Worker]
        Orchestrator[Analysis Orchestrator]
        AudioAnalyzer[Audio Analyzer]
        OCRAnalyzer[OCR Analyzer]
        VideoAnalyzer[Video Analyzer]
        RiskEvaluator[Risk Evaluator]
        ResultAggregator[Result Aggregator]
    end

    subgraph GoogleCloudAI[Google Cloud AI]
        SpeechToText[Speech-to-Text API]
        VideoIntelligence[Video Intelligence API]
        GeminiAPI[Gemini API via Vertex AI]
    end

    subgraph GoogleCloudStorage[Google Cloud Storage]
        GCS[Cloud Storage]
    end

    subgraph GoogleCloudSQL[Cloud SQL]
        PostgreSQL[(PostgreSQL)]
    end

    UI --> API
    API -->|タスク登録| Redis
    Redis -->|タスク取得| CeleryWorker
    CeleryWorker --> Orchestrator
    Orchestrator --> AudioAnalyzer
    Orchestrator --> OCRAnalyzer
    Orchestrator --> VideoAnalyzer
    AudioAnalyzer --> SpeechToText
    OCRAnalyzer --> VideoIntelligence
    VideoAnalyzer --> GeminiAPI
    AudioAnalyzer --> RiskEvaluator
    OCRAnalyzer --> RiskEvaluator
    VideoAnalyzer --> RiskEvaluator
    RiskEvaluator --> GeminiAPI
    RiskEvaluator --> ResultAggregator
    ResultAggregator --> PostgreSQL
    CeleryWorker -->|進捗更新| Redis
    API -->|進捗取得| Redis
    API --> GCS
    API --> PostgreSQL
```

**Architecture Integration**:
- **Selected pattern**: 非同期タスクキュー + 並列パイプラインアーキテクチャ — 長時間処理をバックグラウンドで実行し、3種類の解析を並列実行
- **Domain boundaries**: API（リクエスト受付）、Worker（解析処理）、プレゼンテーション（UI）の3ドメインを分離
- **New components rationale**: Celery + Redisによる非同期タスク処理で、APIのレスポンス性能とスケーラビリティを確保
- **Async processing**: アップロード後即座にジョブIDを返却し、解析処理はWorkerで非同期実行

### Technology Stack

| Layer | Choice / Version | Role in Feature | Notes |
|-------|------------------|-----------------|-------|
| Frontend | React 18 + TypeScript | Web UI、ファイルアップロード、結果表示 | Vite でビルド |
| Backend API | Python 3.12 + FastAPI | API Gateway、リクエスト受付 | uvicorn |
| Task Queue | Celery 5.x + Redis 7 | 非同期タスク管理、進捗管理 | バックグラウンド処理 |
| Worker | Python 3.12 + Celery Worker | 解析処理の実行 | 複数ワーカー対応 |
| Data | PostgreSQL 15 | 解析結果、メタデータ永続化 | SQLAlchemy + Alembic |
| Cache/Broker | Redis 7 | タスクブローカー、進捗キャッシュ | ローカル/GCPともRedis |
| File Storage | Google Cloud Storage | 動画ファイル一時保存 | ローカルはMinIO（S3互換） |
| Container | Docker + docker-compose | ローカル開発環境 | マルチコンテナ構成 |
| External APIs | Google Cloud Speech-to-Text, Video Intelligence API, Gemini API (Vertex AI) | 音声・OCR・リスク評価 | ハッカソン必須要件 |

**ハッカソン制約対応**:
- アプリ実行: Cloud Run（必須）
- AI技術: Vertex AI / Gemini API / Speech-to-Text / Video Intelligence（必須）

**開発フェーズ目標**:
- **Phase 1（本開発の目標）**: ローカル環境での動作確認
- **Phase 2（将来）**: GCPへのデプロイ

### Deployment Architecture

#### ローカル開発環境（docker-compose）

```mermaid
graph TB
    subgraph DockerCompose[docker-compose]
        subgraph FrontendContainer[frontend]
            ReactApp[React App<br/>Port: 3000]
        end

        subgraph BackendContainer[backend]
            FastAPIApp[FastAPI App<br/>Port: 8000]
        end

        subgraph WorkerContainer[worker]
            CeleryWorker[Celery Worker]
        end

        subgraph RedisContainer[redis]
            Redis[(Redis<br/>Port: 6379)]
        end

        subgraph DBContainer[db]
            PostgreSQL[(PostgreSQL<br/>Port: 5432)]
        end

        subgraph StorageContainer[minio]
            MinIO[MinIO<br/>Port: 9000/9001]
        end
    end

    subgraph ExternalServices[Google Cloud APIs]
        SpeechToText[Speech-to-Text API]
        VideoIntelligence[Video Intelligence API]
        GeminiAPI[Gemini API]
    end

    ReactApp --> FastAPIApp
    FastAPIApp -->|タスク登録| Redis
    Redis -->|タスク取得| CeleryWorker
    FastAPIApp -->|進捗取得| Redis
    CeleryWorker -->|進捗更新| Redis
    FastAPIApp --> PostgreSQL
    FastAPIApp --> MinIO
    CeleryWorker --> PostgreSQL
    CeleryWorker --> MinIO
    CeleryWorker --> SpeechToText
    CeleryWorker --> VideoIntelligence
    CeleryWorker --> GeminiAPI
```

**ローカル環境構成**:

| Service | Image | Port | 役割 |
|---------|-------|------|------|
| frontend | Node 20 (dev server) | 3000 | React開発サーバー（Hot Reload対応） |
| backend | Python 3.12 | 8000 | FastAPI アプリケーション（API受付） |
| worker | Python 3.12 | - | Celery Worker（解析処理実行） |
| redis | redis:7 | 6379 | タスクブローカー、進捗キャッシュ |
| db | postgres:15 | 5432 | PostgreSQL データベース |
| minio | minio/minio | 9000, 9001 | S3互換オブジェクトストレージ |

**環境変数管理**:
- `.env.local` - ローカル開発用設定
- `.env.production` - 本番環境用設定（参照用）

#### GCPデプロイ環境（将来）

```mermaid
graph TB
    subgraph CloudRun[Cloud Run]
        FrontendService[Frontend Service<br/>React静的配信]
        BackendService[Backend Service<br/>FastAPI]
        WorkerService[Worker Service<br/>Celery Worker]
    end

    subgraph MemorystoreRedis[Memorystore for Redis]
        Redis[(Redis)]
    end

    subgraph CloudSQL[Cloud SQL]
        PostgreSQLManaged[(PostgreSQL 15)]
    end

    subgraph CloudStorage[Cloud Storage]
        GCS[Video Storage Bucket]
    end

    subgraph GoogleCloudAI[Google Cloud AI]
        SpeechToText[Speech-to-Text API]
        VideoIntelligence[Video Intelligence API]
        GeminiAPI[Gemini API]
    end

    Internet[Internet] --> FrontendService
    FrontendService --> BackendService
    BackendService -->|タスク登録| Redis
    Redis -->|タスク取得| WorkerService
    BackendService -->|進捗取得| Redis
    WorkerService -->|進捗更新| Redis
    BackendService --> PostgreSQLManaged
    BackendService --> GCS
    WorkerService --> PostgreSQLManaged
    WorkerService --> GCS
    WorkerService --> SpeechToText
    WorkerService --> VideoIntelligence
    WorkerService --> GeminiAPI
```

**GCP環境構成**:

| Service | GCP Resource | 設定 |
|---------|--------------|------|
| Frontend | Cloud Run | Nginxコンテナで静的ファイル配信 |
| Backend | Cloud Run | FastAPIコンテナ、min-instances: 0 |
| Worker | Cloud Run | Celery Workerコンテナ、min-instances: 1 |
| Redis | Memorystore for Redis | Basic tier、1GB |
| Database | Cloud SQL | PostgreSQL 15、db-f1-micro（開発）|
| Storage | Cloud Storage | Standard class、同一リージョン |

**環境差分対応**:

| 項目 | ローカル | GCP |
|------|----------|-----|
| Frontend | Vite dev server (port 3000) | Cloud Run + Nginx |
| Backend | uvicorn (port 8000) | Cloud Run |
| Worker | Celery Worker container | Cloud Run |
| Redis | Redis container | Memorystore for Redis |
| Database | PostgreSQL container | Cloud SQL |
| File Storage | MinIO container | Cloud Storage |
| 認証 | サービスアカウントキー（JSON） | Workload Identity |

## System Flows

### 動画アップロード・タスク登録フロー

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant Redis
    participant Storage
    participant DB

    User->>UI: 動画アップロード + メタ情報入力
    UI->>API: POST /api/videos (multipart/form-data)
    API->>API: ファイルバリデーション
    API->>Storage: 動画ファイル保存
    Storage-->>API: ファイルパス
    API->>DB: ジョブレコード作成 (status: pending)
    API->>Redis: Celeryタスク登録 (analyze_video)
    Redis-->>API: task_id
    API-->>UI: 202 Accepted + job_id
    UI-->>User: ジョブ受付完了、進捗画面へ遷移
```

### 非同期解析フロー（Worker側）

```mermaid
sequenceDiagram
    participant Redis
    participant Worker
    participant Orchestrator
    participant AudioAnalyzer
    participant OCRAnalyzer
    participant VideoAnalyzer
    participant RiskEvaluator
    participant DB

    Redis->>Worker: タスク取得 (analyze_video)
    Worker->>DB: ジョブステータス更新 (processing)
    Worker->>Redis: 進捗更新 (0%)
    Worker->>Orchestrator: 解析開始

    par 並列解析
        Orchestrator->>AudioAnalyzer: 音声解析開始
        AudioAnalyzer->>Redis: 進捗更新 (audio: processing)
        AudioAnalyzer-->>Orchestrator: 文字起こし結果
        AudioAnalyzer->>Redis: 進捗更新 (audio: completed)
    and
        Orchestrator->>OCRAnalyzer: OCR解析開始
        OCRAnalyzer->>Redis: 進捗更新 (ocr: processing)
        OCRAnalyzer-->>Orchestrator: テキスト抽出結果
        OCRAnalyzer->>Redis: 進捗更新 (ocr: completed)
    and
        Orchestrator->>VideoAnalyzer: 映像解析開始
        VideoAnalyzer->>Redis: 進捗更新 (video: processing)
        VideoAnalyzer-->>Orchestrator: 映像内容結果
        VideoAnalyzer->>Redis: 進捗更新 (video: completed)
    end

    Orchestrator->>RiskEvaluator: 統合リスク評価
    RiskEvaluator->>Redis: 進捗更新 (risk: processing)
    RiskEvaluator-->>Orchestrator: リスク評価結果
    RiskEvaluator->>Redis: 進捗更新 (risk: completed)

    Orchestrator->>DB: 結果保存
    Worker->>DB: ジョブステータス更新 (completed)
    Worker->>Redis: 進捗更新 (100%)
```

### 進捗確認・結果取得フロー

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant Redis
    participant DB

    loop ポーリング or SSE
        UI->>API: GET /api/jobs/{job_id}/progress
        API->>Redis: 進捗取得
        Redis-->>API: ProgressStatus
        API-->>UI: 進捗状況
        UI-->>User: 進捗表示更新
    end

    Note over UI,API: ジョブ完了時
    UI->>API: GET /api/jobs/{job_id}/results
    API->>DB: 結果取得
    DB-->>API: RiskAssessment
    API-->>UI: 解析結果
    UI-->>User: 結果画面表示
```

### ジョブ一覧・履歴確認フロー

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant DB

    User->>UI: ジョブ一覧画面アクセス
    UI->>API: GET /api/jobs
    API->>DB: ジョブ一覧取得
    DB-->>API: List[AnalysisJob]
    API-->>UI: ジョブ一覧
    UI-->>User: ジョブ一覧表示（ステータス付き）

    User->>UI: ジョブ選択
    alt ジョブ処理中
        UI->>API: GET /api/jobs/{job_id}/progress
        API-->>UI: 進捗状況
        UI-->>User: 進捗画面表示
    else ジョブ完了
        UI->>API: GET /api/jobs/{job_id}/results
        API-->>UI: 解析結果
        UI-->>User: 結果画面表示
    end
```

**Key Decisions**:
- 動画アップロード後、即座に202 AcceptedとジョブIDを返却（非同期処理）
- 解析処理はCelery Workerで実行し、ブラウザを閉じても継続
- 進捗状況はRedisにキャッシュし、ポーリングまたはSSEで取得
- 3つの解析を並列実行し、全完了後にリスク評価を実行
- ジョブ一覧から過去の解析結果を確認可能

## Requirements Traceability

| Requirement | Summary | Components | Interfaces | Flows |
|-------------|---------|------------|------------|-------|
| 1.1-1.5 | 動画アップロード | UploadComponent, API Gateway | VideoUploadRequest | アップロード・タスク登録フロー |
| 2.1-2.4 | 音声文字起こし | AudioAnalyzer, Worker | TranscriptionResult | 非同期解析フロー |
| 3.1-3.4 | 画面内テキスト抽出 | OCRAnalyzer, Worker | OCRResult | 非同期解析フロー |
| 4.1-4.4 | 映像内容解析 | VideoAnalyzer, Worker | VideoAnalysisResult | 非同期解析フロー |
| 5.1-5.7 | 炎上リスク評価 | RiskEvaluator, Worker | RiskAssessment | 非同期解析フロー |
| 6.1-6.6 | 結果表示 | ResultsComponent | AnalysisResult | 進捗確認・結果取得フロー |
| 7.1-7.4 | 解析進捗管理 | ProgressComponent, Redis | ProgressUpdate | 進捗確認・結果取得フロー |
| 8.1-8.6 | 非同期タスク処理 | Celery, Redis, JobListComponent | AnalysisJob | 全フロー |

## Components and Interfaces

| Component | Domain/Layer | Intent | Req Coverage | Key Dependencies | Contracts |
|-----------|--------------|--------|--------------|------------------|-----------|
| UploadComponent | UI | 動画アップロードUI | 1.1-1.5 | API Gateway (P0) | API |
| ProgressComponent | UI | 進捗表示UI | 7.1-7.4 | API Gateway (P0) | API |
| ResultsComponent | UI | 結果表示UI | 6.1-6.6 | API Gateway (P0) | API |
| JobListComponent | UI | ジョブ一覧UI | 8.3-8.5 | API Gateway (P0) | API |
| API Gateway | Backend | HTTPリクエスト処理、タスク登録 | All | Redis, Database (P0) | API |
| Celery Worker | Worker | 非同期タスク実行 | 8.1-8.2 | Redis, Orchestrator (P0) | Task |
| ProgressService | Backend | 進捗管理サービス | 7.1-7.4, 8.4 | Redis (P0) | Service |
| Orchestrator | Worker | 解析オーケストレーション | 2-5 | Analyzers (P0), RiskEvaluator (P0) | Service |
| AudioAnalyzer | Analysis | 音声文字起こし | 2.1-2.4 | Speech-to-Text API (P0) | Service |
| OCRAnalyzer | Analysis | テキスト抽出 | 3.1-3.4 | Video Intelligence API (P0) | Service |
| VideoAnalyzer | Analysis | 映像内容解析 | 4.1-4.4 | Gemini API (P0) | Service |
| RiskEvaluator | Risk | リスク評価統合 | 5.1-5.7 | Gemini API (P0) | Service |

### Backend

#### API Gateway

| Field | Detail |
|-------|--------|
| Intent | HTTPリクエストの受付、バリデーション、タスク登録、進捗・結果返却 |
| Requirements | 1.1-1.5, 6.1-6.6, 7.1-7.4, 8.1-8.6 |

**Responsibilities & Constraints**
- ファイルアップロードの受付とバリデーション（mp4形式、サイズ上限）
- メタ情報の検証（用途、投稿先媒体、想定ターゲット）
- Celeryタスクの登録（非同期処理開始）
- 進捗状況の取得（Redis経由）
- 解析結果の取得と返却
- ジョブ一覧の取得

**Dependencies**
- Outbound: Redis — タスク登録、進捗取得 (P0)
- Outbound: FileStorage — ファイル保存 (P0)
- Outbound: Database — ジョブ・結果取得 (P0)

**Contracts**: API [x]

##### API Contract

| Method | Endpoint | Request | Response | Errors |
|--------|----------|---------|----------|--------|
| POST | /api/videos | multipart/form-data | AnalysisJob (202) | 400, 413, 415, 500 |
| GET | /api/jobs | - | List[AnalysisJobSummary] | 500 |
| GET | /api/jobs/:id | - | AnalysisJob | 404, 500 |
| GET | /api/jobs/:id/progress | - | ProgressStatus | 404, 500 |
| GET | /api/jobs/:id/results | - | AnalysisResult | 404, 500 |
| GET | /api/jobs/:id/events | - | SSE Stream | 404, 500 |

```python
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class Platform(str, Enum):
    twitter = "twitter"
    instagram = "instagram"
    youtube = "youtube"
    tiktok = "tiktok"
    other = "other"

class VideoMetadata(BaseModel):
    purpose: str
    platform: Platform
    target_audience: str

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class AnalysisJob(BaseModel):
    id: str
    status: JobStatus
    video_name: str
    metadata: VideoMetadata
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None

class AnalysisJobSummary(BaseModel):
    id: str
    status: JobStatus
    video_name: str
    created_at: datetime
    completed_at: datetime | None

class PhaseStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class PhaseProgress(BaseModel):
    status: PhaseStatus
    progress: float

class ProgressStatus(BaseModel):
    job_id: str
    status: JobStatus
    overall: float
    phases: dict[str, PhaseProgress]  # audio, ocr, video, risk
    estimated_remaining_seconds: float | None
```

#### Celery Worker

| Field | Detail |
|-------|--------|
| Intent | 非同期タスクの実行、進捗更新 |
| Requirements | 8.1-8.2, 8.6 |

**Responsibilities & Constraints**
- Redisからタスクを取得して解析処理を実行
- 進捗状況をRedisに更新
- 処理完了/失敗時にDBステータスを更新
- 複数ワーカーでの並列処理対応

**Dependencies**
- Inbound: Redis — タスク取得 (P0)
- Outbound: Redis — 進捗更新 (P0)
- Outbound: Orchestrator — 解析処理実行 (P0)
- Outbound: Database — ステータス更新 (P0)

**Contracts**: Task [x]

##### Task Interface

```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def analyze_video(self, job_id: str, video_path: str, metadata: dict) -> dict:
    """
    動画解析タスク

    Args:
        job_id: 解析ジョブID
        video_path: 動画ファイルパス（Storage内）
        metadata: メタ情報（purpose, platform, target_audience）

    Returns:
        解析結果のサマリー

    Raises:
        タスク失敗時は自動リトライ後にfailed状態に更新
    """
    pass
```

#### ProgressService

| Field | Detail |
|-------|--------|
| Intent | 進捗状況の管理（Redis経由） |
| Requirements | 7.1-7.4, 8.4 |

**Responsibilities & Constraints**
- 進捗状況のRedisへの保存・取得
- フェーズ別進捗の集約
- 推定残り時間の計算

**Dependencies**
- Outbound: Redis — 進捗データ (P0)

**Contracts**: Service [x]

##### Service Interface

```python
from abc import ABC, abstractmethod

class ProgressServiceInterface(ABC):
    @abstractmethod
    async def update_progress(
        self,
        job_id: str,
        phase: str,
        status: PhaseStatus,
        progress: float
    ) -> None:
        """フェーズの進捗を更新"""
        pass

    @abstractmethod
    async def get_progress(self, job_id: str) -> ProgressStatus:
        """ジョブの進捗状況を取得"""
        pass

    @abstractmethod
    async def set_job_completed(self, job_id: str) -> None:
        """ジョブを完了状態に設定"""
        pass

    @abstractmethod
    async def set_job_failed(self, job_id: str, error: str) -> None:
        """ジョブを失敗状態に設定"""
        pass
```

#### Orchestrator

| Field | Detail |
|-------|--------|
| Intent | 解析パイプラインのオーケストレーション、並列実行制御 |
| Requirements | 2.1, 3.1, 4.1, 5.1 |

**Responsibilities & Constraints**
- 3つの解析器を並列起動し、完了を待機
- 進捗状況の集約とSSE通知
- 部分失敗時のグレースフルデグラデーション

**Dependencies**
- Inbound: API Gateway — 解析リクエスト (P0)
- Outbound: AudioAnalyzer, OCRAnalyzer, VideoAnalyzer — 解析実行 (P0)
- Outbound: RiskEvaluator — リスク評価実行 (P0)

**Contracts**: Service [x]

##### Service Interface

```python
from abc import ABC, abstractmethod

class OrchestratorService(ABC):
    @abstractmethod
    async def start_analysis(self, job_id: str, video_path: str, metadata: VideoMetadata) -> None:
        pass

    @abstractmethod
    def get_progress(self, job_id: str) -> ProgressStatus:
        pass

    @abstractmethod
    async def cancel_analysis(self, job_id: str) -> None:
        pass
```

### Analysis

#### AudioAnalyzer

| Field | Detail |
|-------|--------|
| Intent | Google Cloud Speech-to-Text APIを用いた音声文字起こしと話者分離 |
| Requirements | 2.1-2.4 |

**Responsibilities & Constraints**
- 動画から音声を抽出
- Google Cloud Speech-to-Text API（Chirp 2モデル）で文字起こし実行
- タイムコード付き話者別トランスクリプト生成（Speaker Diarization機能）

**Dependencies**
- External: Google Cloud Speech-to-Text API — 音声文字起こし (P0)

**Contracts**: Service [x]

##### Service Interface

```python
class TranscriptionSegment(BaseModel):
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: float

class TranscriptionResult(BaseModel):
    segments: list[TranscriptionSegment]
    has_audio: bool

class AudioAnalyzerService(ABC):
    @abstractmethod
    async def analyze(self, video_path: str) -> TranscriptionResult:
        pass
```

#### OCRAnalyzer

| Field | Detail |
|-------|--------|
| Intent | Google Cloud Video Intelligence APIを用いたテキスト抽出 |
| Requirements | 3.1-3.4 |

**Responsibilities & Constraints**
- 動画フレームからのテキスト検出
- タイムコード付きテキスト抽出結果生成

**Dependencies**
- External: Google Cloud Video Intelligence API — OCR処理 (P0)

**Contracts**: Service [x]

##### Service Interface

```python
class Vertex(BaseModel):
    x: float
    y: float

class BoundingBox(BaseModel):
    vertices: list[Vertex]

class TextAnnotation(BaseModel):
    text: str
    start_time: float
    end_time: float
    bounding_box: BoundingBox
    confidence: float

class OCRResult(BaseModel):
    text_annotations: list[TextAnnotation]
    has_text: bool

class OCRAnalyzerService(ABC):
    @abstractmethod
    async def analyze(self, video_path: str) -> OCRResult:
        pass
```

#### VideoAnalyzer

| Field | Detail |
|-------|--------|
| Intent | Gemini API（Vertex AI）を用いた映像内容解析 |
| Requirements | 4.1-4.4 |

**Responsibilities & Constraints**
- フレームサンプリングと画像抽出
- Gemini APIで人物・物体・行動・シーンを解析（マルチモーダル対応）

**Dependencies**
- External: Gemini API (Vertex AI) — 画像解析 (P0)

**Contracts**: Service [x]

##### Service Interface

```python
class PersonAttributes(BaseModel):
    expression: str
    gesture: str
    attire: str

class PersonDetection(BaseModel):
    bounding_box: BoundingBox
    attributes: PersonAttributes

class ObjectDetection(BaseModel):
    label: str
    bounding_box: BoundingBox
    confidence: float

class SceneClassification(BaseModel):
    location: str
    atmosphere: str
    context: str

class FrameAnalysis(BaseModel):
    timestamp: float
    persons: list[PersonDetection]
    objects: list[ObjectDetection]
    scene: SceneClassification

class VideoAnalysisResult(BaseModel):
    frames: list[FrameAnalysis]

class VideoAnalyzerService(ABC):
    @abstractmethod
    async def analyze(self, video_path: str) -> VideoAnalysisResult:
        pass
```

### Risk

#### RiskEvaluator

| Field | Detail |
|-------|--------|
| Intent | 解析結果を統合し、炎上リスクを評価 |
| Requirements | 5.1-5.7 |

**Responsibilities & Constraints**
- 音声・OCR・映像の解析結果を統合
- メタ情報（投稿先媒体・ターゲット）を考慮したリスク評価
- 攻撃性・差別性・誤解を招く表現の3観点で評価
- リスクスコアと根拠の生成

**Dependencies**
- Inbound: Orchestrator — 解析結果 (P0)
- External: Gemini API (Vertex AI) — リスク評価推論 (P0)

**Contracts**: Service [x]

##### Service Interface

```python
class RiskCategory(str, Enum):
    aggressiveness = "aggressiveness"
    discrimination = "discrimination"
    misleading = "misleading"

class RiskLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"

class RiskSource(str, Enum):
    audio = "audio"
    ocr = "ocr"
    video = "video"

class RiskItem(BaseModel):
    id: str
    timestamp: float
    end_timestamp: float
    category: RiskCategory
    subcategory: str
    score: float
    level: RiskLevel
    rationale: str
    source: RiskSource
    evidence: str

class RiskAssessment(BaseModel):
    overall_score: float
    risk_level: RiskLevel
    risks: list[RiskItem]

class RiskEvaluatorService(ABC):
    @abstractmethod
    async def evaluate(
        self,
        transcription: TranscriptionResult,
        ocr: OCRResult,
        video_analysis: VideoAnalysisResult,
        metadata: VideoMetadata
    ) -> RiskAssessment:
        pass
```

## Data Models

### Domain Model

```mermaid
erDiagram
    AnalysisJob ||--|| Video : contains
    AnalysisJob ||--o| TranscriptionResult : produces
    AnalysisJob ||--o| OCRResult : produces
    AnalysisJob ||--o| VideoAnalysisResult : produces
    AnalysisJob ||--o| RiskAssessment : produces
    RiskAssessment ||--o{ RiskItem : contains

    Video {
        string id PK
        string filePath
        string originalName
        int fileSize
        int duration
    }

    AnalysisJob {
        string id PK
        string videoId FK
        string status
        json metadata
        timestamp createdAt
        timestamp completedAt
    }

    RiskItem {
        string id PK
        string assessmentId FK
        float timestamp
        string category
        int score
        string rationale
    }
```

### Logical Data Model

**AnalysisJob**
- 動画解析ジョブの管理エンティティ
- ステータス遷移: pending → processing → completed/failed
- メタデータ（用途、投稿先、ターゲット）を保持

**RiskAssessment**
- 解析結果の集約エンティティ
- 総合スコアとリスクレベルを保持
- 複数のRiskItemを含む

**RiskItem**
- 個別のリスク検出結果
- タイムコード、カテゴリ、スコア、根拠を保持
- ソース（音声/OCR/映像）の識別

## Error Handling

### Error Categories and Responses

**User Errors (4xx)**
- 400: 無効なファイル形式 → mp4形式での再アップロードを促す
- 413: ファイルサイズ超過 → 上限サイズを表示
- 415: サポート外メディアタイプ → 対応形式を案内

**System Errors (5xx)**
- 500: 解析処理エラー → エラー内容表示、再試行オプション提供
- 503: 外部APIエラー → グレースフルデグラデーション、部分結果の表示

**Business Logic Errors (422)**
- 音声なし → 音声なしとして記録、他解析を継続
- テキストなし → テキストなしとして記録、他解析を継続

### Monitoring
- 各解析フェーズの処理時間メトリクス
- 外部APIのエラー率・レイテンシ監視
- リスク検出率の統計

## Testing Strategy

### Unit Tests
- AudioAnalyzer: モック音声データの文字起こし変換
- OCRAnalyzer: モックフレームのテキスト抽出
- RiskEvaluator: 各リスクカテゴリの評価ロジック
- バリデーション: ファイル形式・サイズ検証

### Integration Tests
- API Gateway → Orchestrator → Analyzers の連携
- 外部API統合（Speech-to-Text, Video Intelligence, Gemini API）
- SSE進捗通知の動作確認
- Cloud SQL永続化と取得

### E2E Tests
- 動画アップロードから結果表示までの一連フロー
- エラー時のUI表示
- 進捗表示のリアルタイム更新

## Security Considerations

- ファイルアップロード: Content-Type検証、マジックバイト検証
- 一時ファイル: 解析完了後の自動削除
- APIキー: 環境変数管理、ローテーション対応
- アクセス制御: 自身のジョブのみ参照可能

## Project Structure

```
video-risk-analyzer/
├── docker-compose.yml          # ローカル開発用マルチコンテナ定義
├── .env.local                  # ローカル環境変数（Git管理外）
├── .env.example                # 環境変数テンプレート
├── frontend/
│   ├── Dockerfile              # Frontend用Dockerfile
│   ├── Dockerfile.prod         # 本番用（Nginx）
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadComponent.tsx
│   │   │   ├── ProgressComponent.tsx
│   │   │   ├── ResultsComponent.tsx
│   │   │   └── JobListComponent.tsx    # ジョブ一覧
│   │   ├── hooks/
│   │   │   └── useJobProgress.ts       # 進捗ポーリング
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── public/
├── backend/
│   ├── Dockerfile              # Backend API用Dockerfile
│   ├── Dockerfile.worker       # Worker用Dockerfile
│   ├── pyproject.toml          # Poetry依存管理
│   ├── alembic/                # DBマイグレーション
│   │   └── versions/
│   ├── app/
│   │   ├── main.py             # FastAPIエントリポイント
│   │   ├── config.py           # 設定管理
│   │   ├── celery_app.py       # Celery設定
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── videos.py
│   │   │       └── jobs.py     # ジョブ管理API
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── analyze.py      # Celeryタスク定義
│   │   ├── services/
│   │   │   ├── orchestrator.py
│   │   │   ├── audio_analyzer.py
│   │   │   ├── ocr_analyzer.py
│   │   │   ├── video_analyzer.py
│   │   │   ├── risk_evaluator.py
│   │   │   └── progress.py     # 進捗管理サービス
│   │   ├── models/
│   │   │   └── database.py
│   │   └── schemas/
│   │       ├── video.py
│   │       └── job.py          # ジョブスキーマ
│   └── tests/
└── docs/
```

## Docker Compose Configuration

### docker-compose.yml（ローカル開発用）

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    command: npm run dev -- --host 0.0.0.0

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app
    env_file:
      - .env.local
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/video_risk_analyzer
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - STORAGE_ENDPOINT=http://minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
      - STORAGE_BUCKET=videos
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    volumes:
      - ./backend/app:/app/app
    env_file:
      - .env.local
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/video_risk_analyzer
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - STORAGE_ENDPOINT=http://minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
      - STORAGE_BUCKET=videos
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_started
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  db:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=video_risk_analyzer
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 起動コマンド

```bash
# 初回起動（ビルド含む）
docker-compose up --build

# バックグラウンド起動
docker-compose up -d

# ログ確認（API）
docker-compose logs -f backend

# ログ確認（Worker）
docker-compose logs -f worker

# 全サービスのログ
docker-compose logs -f

# 停止
docker-compose down

# データ含めて完全削除
docker-compose down -v
```

### 環境変数テンプレート（.env.example）

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# Database（ローカルはdocker-compose.ymlで上書き）
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/video_risk_analyzer

# Redis（ローカルはdocker-compose.ymlで上書き）
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Storage（ローカルはdocker-compose.ymlで上書き）
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=videos

# Application
MAX_FILE_SIZE_MB=100
ALLOWED_EXTENSIONS=mp4
```
