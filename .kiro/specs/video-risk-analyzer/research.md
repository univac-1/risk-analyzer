# Research & Design Decisions

## Summary
- **Feature**: `video-risk-analyzer`
- **Discovery Scope**: New Feature（グリーンフィールド開発）
- **Hackathon Constraint**: 第4回 Agentic AI Hackathon with Google Cloud（Google Cloud必須）
- **Key Findings**:
  - Google Cloud Speech-to-Text API（Chirp 2）が話者分離付き音声文字起こしをサポート
  - Google Cloud Video Intelligence API が動画フレームからのOCRテキスト抽出に対応
  - Gemini API（Vertex AI）がマルチモーダルコンテンツモデレーションとリスクレベル分類を提供

## Research Log

### 音声文字起こしと話者分離

- **Context**: 要件2.4「複数話者の発言を区別して記録」を実現するための技術調査
- **Sources Consulted**:
  - [Google Cloud Speech-to-Text Documentation](https://cloud.google.com/speech-to-text/docs)
  - [Speaker Diarization](https://cloud.google.com/speech-to-text/docs/multiple-voices)
- **Findings**:
  - Google Cloud Speech-to-Text API が Speaker Diarization（話者分離）をネイティブサポート
  - Chirp 2 モデルが高精度な日本語音声認識を提供
  - `enable_speaker_diarization` と `diarization_speaker_count` で話者分離を有効化
  - タイムスタンプ付きの word-level 結果を取得可能
  - 長時間音声も streaming/batch で対応可能
- **Implications**:
  - Google Cloud Speech-to-Text API を音声文字起こしの主要技術として採用（ハッカソン要件）
  - Chirp 2 モデルで高精度な日本語認識を実現

### 動画フレームからのテキスト抽出（OCR）

- **Context**: 要件3「画面内テキスト抽出」を実現するための技術調査
- **Sources Consulted**:
  - [Google Cloud Video Intelligence API - Text Detection](https://cloud.google.com/video-intelligence/docs/text-detection)
  - [Cloud Vision API OCR Documentation](https://docs.cloud.google.com/vision/docs/ocr)
- **Findings**:
  - Google Cloud Video Intelligence API が動画からのOCRテキスト検出をネイティブサポート
  - TEXT_DETECTION と DOCUMENT_TEXT_ANNOTATION の2種類のアノテーション機能
  - 精度97%以上の高精度テキスト認識
  - Cloud Vision API でフレーム単位のOCR処理も可能（OpenCVでフレーム抽出後に送信）
  - EU内データ処理オプションあり（GDPR対応）
- **Implications**:
  - Google Cloud Video Intelligence API を動画テキスト抽出に採用
  - 代替案としてフレーム抽出 + Cloud Vision API の組み合わせも検討

### 映像内容解析とリスク評価

- **Context**: 要件4「映像内容解析」と要件5「炎上リスク評価」を実現するための技術調査
- **Sources Consulted**:
  - [Gemini API Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/overview)
  - [Vertex AI Multimodal](https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/overview)
  - [ICCV 2025 MLLMs Content Moderation Research](https://arxiv.org/html/2508.05527v1)
- **Findings**:
  - Gemini API がマルチモーダル入力（画像・動画・テキスト）を統合解析可能
  - Gemini 1.5 Pro/Flash が動画フレームの直接解析をサポート（最大1時間の動画）
  - コンテンツモデレーションを複数リスクレベルで柔軟に設計可能
  - Vertex AI 経由で利用することでエンタープライズグレードのセキュリティを確保
  - 2025年ICCV研究でGemini含むMLLMsの動画コンテンツモデレーション精度が検証済み
- **Implications**:
  - Gemini API（Vertex AI）をリスク評価の中核エンジンとして採用（ハッカソン要件）
  - 高リスク: 警告表示、中リスク: 注意喚起という階層設計
  - Gemini のマルチモーダル機能で映像内容を直接評価

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| パイプライン型 | 解析フェーズを直列に実行 | 実装がシンプル、デバッグ容易 | 処理時間が長い、並列化できない | 小規模向け |
| 並列パイプライン | 音声・OCR・映像解析を並列実行し最後に統合 | 処理時間短縮、スケーラブル | 結果統合の複雑さ、エラーハンドリング | **採用** |
| イベント駆動 | 各解析をイベントでトリガー | 疎結合、拡張性高い | オーバーエンジニアリングのリスク | 将来の拡張候補 |

## Design Decisions

### Decision: 並列パイプラインアーキテクチャの採用

- **Context**: 動画解析は音声・OCR・映像の3種類の解析を行う必要があり、処理時間の最適化が重要
- **Alternatives Considered**:
  1. 直列パイプライン — シンプルだが処理時間が長い
  2. 並列パイプライン — 3解析を並列実行し、完了後に統合
  3. イベント駆動 — 疎結合だがMVPには過剰
- **Selected Approach**: 並列パイプライン（Option 2）
- **Rationale**:
  - 3つの解析処理に依存関係がない
  - 処理時間を最大1/3に短縮可能
  - 各解析の独立性を保ちつつ、結果統合で一貫したリスク評価が可能
- **Trade-offs**: 結果統合ロジックの複雑さ増加、並列実行のエラーハンドリング必要
- **Follow-up**: 各解析のタイムアウト設計、部分失敗時のグレースフルデグラデーション

### Decision: Google Cloud 統一構成（ハッカソン要件）

- **Context**: 第4回 Agentic AI Hackathon with Google Cloud の必須要件を満たす必要がある
- **Hackathon Requirements**:
  - アプリ実行系: Cloud Run / App Engine / GKE / Cloud Functions 等から1つ以上
  - AI技術: Vertex AI / Gemini API / Speech-to-Text / Vision 等から1つ以上
- **Selected Approach**: Google Cloud 統一構成
  - アプリ実行: Cloud Run（FastAPI デプロイ）
  - 音声文字起こし: Google Cloud Speech-to-Text API（Chirp 2モデル）
  - OCR: Google Cloud Video Intelligence API
  - 映像解析・リスク評価: Gemini API（Vertex AI経由）
  - ストレージ: Google Cloud Storage + Cloud SQL
- **Rationale**:
  - ハッカソン必須要件を満たす
  - Google Cloud エコシステム内で統一することで認証・課金・運用が簡素化
  - Gemini API のマルチモーダル機能が映像解析に適している
- **Trade-offs**: 特定ベンダーへの依存、一部機能で他サービス（OpenAI Whisper等）より精度が劣る可能性
- **Follow-up**: Google Cloud 無料枠の活用、コスト最適化

### Decision: Python + FastAPI によるバックエンド実装

- **Context**: バックエンドフレームワークの選定
- **Alternatives Considered**:
  1. Node.js + Express — JavaScript エコシステム、フロントエンドとの統一
  2. Python + FastAPI — 非同期サポート、型ヒント、AI/ML ライブラリとの親和性
  3. Go + Gin — 高性能だが AI ライブラリが少ない
- **Selected Approach**: Python 3.12 + FastAPI（Cloud Run デプロイ）
- **Rationale**:
  - Google Cloud の公式 Python SDK（google-cloud-speech, google-cloud-videointelligence, vertexai）が充実
  - asyncio による並列解析処理の実装が容易
  - Pydantic による型安全なリクエスト/レスポンス定義
  - Cloud Run との相性が良い（コンテナ化が容易）
- **Trade-offs**: Node.js と比較して若干のパフォーマンス低下の可能性
- **Follow-up**: Cloud Run へのデプロイ構成、Dockerfile 作成

### Decision: 複数リスクレベル方式の採用

- **Context**: 炎上リスク評価の結果をどのように分類するか
- **Alternatives Considered**:
  1. 二値分類（リスクあり/なし）— シンプルだが過敏/鈍感になりやすい
  2. 複数リスクレベル（高/中/低/なし）— 柔軟な対応が可能
  3. 確率スコアのみ — 解釈が難しい
- **Selected Approach**: 複数リスクレベル + 数値スコア
- **Rationale**: Gemini API のプロンプトエンジニアリングで柔軟なリスク分類が可能、高リスクは警告、中リスクは注意喚起として対応
- **Trade-offs**: 閾値設計が必要、ユーザーの理解コスト
- **Follow-up**: リスクレベルの閾値チューニング、ユーザーフィードバックによる改善

## Risks & Mitigations

- **API レート制限**: 大量動画処理時にレート制限に達する可能性 — キューイングと再試行ロジックで対応
- **処理コスト**: 長時間動画の解析コストが高額になる可能性 — 事前見積もり表示、フレームサンプリング間隔の最適化
- **精度のばらつき**: 各APIの精度が入力品質に依存 — 信頼度スコアの表示、低精度時の警告
- **ベンダー依存**: 特定APIの仕様変更や障害の影響 — 抽象化レイヤーの導入、フォールバック機構の検討

## References

- [Google Cloud Speech-to-Text API](https://cloud.google.com/speech-to-text/docs) — 音声文字起こしと話者分離の公式ドキュメント
- [Google Cloud Video Intelligence API](https://cloud.google.com/video-intelligence/docs/text-detection) — 動画テキスト検出の公式ドキュメント
- [Gemini API / Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/overview) — マルチモーダルAI解析の公式ドキュメント
- [Cloud Run](https://cloud.google.com/run/docs) — サーバーレスコンテナ実行環境
- [第4回 Agentic AI Hackathon with Google Cloud](https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4) — ハッカソン要件
