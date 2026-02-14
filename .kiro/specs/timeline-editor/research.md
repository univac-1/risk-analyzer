# Research & Design Decisions: Timeline Editor

## Summary
- **Feature**: timeline-editor
- **Discovery Scope**: Extension（既存Video Risk Analyzerへの編集機能追加）
- **Key Findings**:
  - FFmpegのフィルターチェーンで複合編集（カット/ミュート/モザイク/テロップ）が可能
  - 既存storage.pyにpresigned_url実装済み、動画URL取得は低コスト
  - モックUIが完成しており、本番移植が直接的に可能

## Research Log

### FFmpegフィルターチェーン
- **Context**: 複数の編集アクションを1つの動画に統合適用する方法
- **Sources Consulted**:
  - [FFmpeg Filters Documentation](https://ffmpeg.org/ffmpeg-filters.html)
  - [FFmpeg FilteringGuide](https://trac.ffmpeg.org/wiki/FilteringGuide)
- **Findings**:
  - フィルターはカンマ区切りで連結、複数チェーンはセミコロン区切り
  - `enable='between(t,start,end)'`で時間範囲指定が可能
  - 映像フィルター(-vf)と音声フィルター(-af)は別々に指定
- **Implications**:
  - 編集アクションごとにフィルター式を生成し、連結する設計が適切
  - カット処理は`select`/`aselect`フィルターで実現

### モザイク処理
- **Context**: 動画内の特定領域をぼかす方法
- **Sources Consulted**:
  - [FFmpeg Boxblur Filter](https://ottverse.com/blur-a-video-using-ffmpeg-boxblur/)
- **Findings**:
  - `crop` + `boxblur` + `overlay`の組み合わせで領域指定ぼかしが可能
  - `boxblur=10:enable='between(t,4,7)'`で時間範囲指定
  - `delogo`フィルターも領域指定+時間指定に対応
- **Implications**:
  - モザイク領域は`{x, y, width, height}`で保存
  - boxblurの強度は固定値（10）で十分

### テロップ処理
- **Context**: 日本語テキストを動画に合成する方法
- **Sources Consulted**:
  - [FFmpeg Drawtext Filter](https://ffmpeg.org/ffmpeg-filters.html)
  - [FFmpeg Drawtext with Native Language](https://medium.com/@abdullah.farwees/ffmpegs-drawtext-filter-with-native-language-texts-b9b49721808a)
- **Findings**:
  - `drawtext`フィルターで`fontfile`に日本語フォント指定が必要
  - Noto Sans JPなどのフリーフォントが利用可能
  - `x=(w-text_w)/2`で中央配置、`y=h-50`で下部配置
- **Implications**:
  - Dockerイメージに日本語フォントを含める必要あり
  - テロップ設定は`{text, x, y, fontSize, fontColor}`で保存

### 既存コードベース統合
- **Context**: 既存APIパターンとの整合性
- **Sources Consulted**: `backend/app/api/routes/jobs.py`, `backend/app/services/storage.py`
- **Findings**:
  - `generate_presigned_url`が既に実装済み（有効期限指定可能）
  - Celeryタスクパターンが確立（`analyze.py`参照）
  - Redis進捗管理パターンが確立（`progress.py`参照）
- **Implications**:
  - 既存パターンを踏襲し、editor用の新規ルーター/タスクを作成

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| A: 既存拡張 | ResultsComponent拡張 | ファイル数少 | コンポーネント肥大化 | 非推奨 |
| B: 新規作成 | 独立したeditorモジュール | 責務分離、テスト容易 | ファイル数多 | **採用** |
| C: ハイブリッド | API既存拡張+UI新規 | バランス | 判断複雑 | 妥協案 |

**採用: Option B** - モックUIが独立して完成しており、編集機能は結果表示と責務が異なるため

## Design Decisions

### Decision: 編集セッションのデータモデル設計
- **Context**: 編集状態を永続化し、中断・再開を可能にする
- **Alternatives Considered**:
  1. フロントエンドのみで状態管理（localStorage）
  2. バックエンドDBに保存
- **Selected Approach**: バックエンドDBに保存
- **Rationale**: ブラウザを閉じても編集状態を復元可能、複数デバイスからのアクセス対応
- **Trade-offs**: API呼び出しのオーバーヘッド発生 vs 永続性・信頼性向上
- **Follow-up**: 自動保存の頻度を検討（現時点では手動保存のみ）

### Decision: FFmpegコマンド生成方式
- **Context**: 複数の編集アクションを効率的に適用する方法
- **Alternatives Considered**:
  1. 編集アクションごとに順次FFmpeg実行
  2. 全アクションを1つのフィルターチェーンに統合
- **Selected Approach**: 全アクションを1つのフィルターチェーンに統合
- **Rationale**: 再エンコード回数を1回に抑え、品質劣化と処理時間を最小化
- **Trade-offs**: コマンド生成の複雑化 vs 処理効率向上
- **Follow-up**: フィルター順序の最適化（カット→モザイク→テロップの順）

### Decision: エクスポート進捗の取得方法
- **Context**: FFmpeg処理中の進捗をリアルタイム表示する
- **Alternatives Considered**:
  1. FFmpegの`-progress`オプションでパイプ出力
  2. 出力ファイルサイズを定期監視
- **Selected Approach**: `-progress`オプションでパイプ出力
- **Rationale**: 正確なフレーム数ベースの進捗取得が可能
- **Trade-offs**: 出力パース処理が必要 vs 高精度な進捗表示
- **Follow-up**: 進捗更新頻度は1秒間隔

## Risks & Mitigations
- **FFmpeg複合フィルターの互換性** — 各編集タイプの組み合わせテストを実施
- **大容量動画の処理時間** — 進捗表示とバックグラウンド処理で対応
- **日本語フォントの文字化け** — Noto Sans JPをDockerイメージに含める

## References
- [FFmpeg Filters Documentation](https://ffmpeg.org/ffmpeg-filters.html)
- [FFmpeg FilteringGuide](https://trac.ffmpeg.org/wiki/FilteringGuide)
- [FFmpeg Boxblur Filter](https://ottverse.com/blur-a-video-using-ffmpeg-boxblur/)
- [FFmpeg Drawtext Filter](https://medium.com/@abdullah.farwees/ffmpegs-drawtext-filter-with-native-language-texts-b9b49721808a)
