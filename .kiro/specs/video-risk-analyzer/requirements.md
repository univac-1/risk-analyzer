# Requirements Document

## Introduction

本ドキュメントは、SNS投稿前の動画コンテンツに対する炎上リスクチェック支援ツール「Video Risk Analyzer」の要件を定義します。広報担当者が投稿前に動画を解析し、炎上リスクのある箇所をタイムコード・根拠・スコア付きで事前に把握できるようにすることで、投稿判断の精度向上と心理的負担の軽減を実現します。
本システムは、動画分析精度向上のため、Geminiのネイティブ動画解析機能を活用するアーキテクチャに刷新されました。これにより、テキスト抽出と映像内容解析がGeminiによる統合的な処理として行われます。
google-cloud-japan-ai-hackathon-vol4.mdに記載されている条件を満たしてシステムを構築します。

## Requirements

### Requirement 1: 動画アップロード

**Objective:** As a 広報担当者, I want 投稿予定の動画とメタ情報をアップロードしたい, so that システムがリスク解析を開始できる

#### Acceptance Criteria
1. When ユーザがmp4形式の動画ファイルを選択する, the Video Risk Analyzer shall ファイルをアップロード対象として受け付ける
2. When ユーザが動画をアップロードする, the Video Risk Analyzer shall 用途・投稿先媒体・想定ターゲットのメタ情報入力フォームを表示する
3. If アップロードされたファイルがmp4形式でない, then the Video Risk Analyzer shall エラーメッセージを表示し、正しい形式での再アップロードを促す
4. If ファイルサイズが上限を超える, then the Video Risk Analyzer shall ファイルサイズ超過エラーを表示する
5. When 動画とメタ情報が正常にアップロードされる, the Video Risk Analyzer shall 解析処理を開始し、進捗状況を表示する

### Requirement 2: 音声文字起こし解析

**Objective:** As a システム, I want 動画内の音声を文字に変換したい, so that 発言内容のリスク評価に利用できる

#### Acceptance Criteria
1. When 動画解析が開始される, the Video Risk Analyzer shall 動画内の音声を抽出し、文字起こし処理を実行する
2. The Video Risk Analyzer shall 文字起こし結果にタイムコードを付与する
3. If 音声が検出されない, then the Video Risk Analyzer shall 音声なしとして記録し、他の解析を継続する
4. The Video Risk Analyzer shall 複数話者の発言を区別して記録する

### Requirement 3: 画面内テキスト抽出

**Objective:** As a システム, I want 動画内に表示されるテキストを抽出したい, so that 表示文言のリスク評価に利用できる

#### Acceptance Criteria
1. When 動画解析が開始される, the Video Risk Analyzer shall Geminiの動画解析機能を利用し、動画内のテキスト領域を検出し、テキスト抽出処理を実行する
2. The Video Risk Analyzer shall 抽出されたテキストに該当タイムコードを付与する
3. The Video Risk Analyzer shall Geminiから提供されるテキストの信頼度を考慮し、閾値以下の低信頼度テキストはリスク評価から除外する
4. The Video Risk Analyzer shall 抽出されたテキストの日本語比率を考慮し、一定以下の比率のテキストはリスク評価から除外する
5. If テキストが検出されない, then the Video Risk Analyzer shall テキストなしとして記録し、他の解析を継続する

### Requirement 4: 映像内容解析

**Objective:** As a システム, I want 動画内の人物・行動・シーンを解析したい, so that 視覚的要素のリスク評価に利用できる

#### Acceptance Criteria
1. When 動画解析が開始される, the Video Risk Analyzer shall Geminiの動画解析機能を利用し、映像内の人物・物体・行動・シーンを検出・分類する
2. The Video Risk Analyzer shall 検出された要素にタイムコードを付与する
3. The Video Risk Analyzer shall 人物の表情・ジェスチャー・服装などの視覚的特徴を記録する (Geminiの出力に応じて調整)
4. The Video Risk Analyzer shall シーンの状況（場所・雰囲気・コンテキスト）を分類する (Geminiの出力に応じて調整)

### Requirement 5: 炎上リスク評価

**Objective:** As a システム, I want 解析結果を統合してリスク評価を行いたい, so that 炎上の可能性がある箇所を特定できる

#### Acceptance Criteria
1. When すべての解析処理が完了する, the Video Risk Analyzer shall 音声解析結果とGeminiによる統合動画解析結果を統合する
2. The Video Risk Analyzer shall ユーザが入力したメタ情報（投稿先媒体・想定ターゲット）を考慮してリスク評価を行う
3. The Video Risk Analyzer shall 各リスク箇所に対してスコア（重要度）を算出する
4. The Video Risk Analyzer shall リスクと判断した根拠を具体的に記述する
5. The Video Risk Analyzer shall 攻撃性の観点から、匿名性・拡散性・感情的反応・集団心理・個人攻撃などの炎上可能性を検出する
6. The Video Risk Analyzer shall 差別性の観点から、人種・性別・性的指向などへの偏見に基づく攻撃を助長する表現を検出する
7. The Video Risk Analyzer shall 誤解を招く表現の観点から、断定・曖昧・感情的・誇張・ステレオタイプ・誤解を招く言葉遣いを検出する
8. The Video Risk Analyzer shall 迷惑行為・不衛生行為の観点から、店舗、施設、公共の場所での不適切な行為や器物損壊、食品・商品への汚損などを検出する

### Requirement 6: 結果表示

**Objective:** As a 広報担当者, I want リスク評価結果を一覧で確認したい, so that 投稿前に問題箇所を把握し対処できる

#### Acceptance Criteria
1. When リスク評価が完了する, the Video Risk Analyzer shall 結果画面を表示する
2. The Video Risk Analyzer shall リスク箇所をタイムコード順に一覧表示する
3. The Video Risk Analyzer shall 各リスク箇所について、タイムコード・リスク根拠・炎上スコアを表示する
4. When ユーザがリスク箇所をクリックする, the Video Risk Analyzer shall 該当タイムコードの動画プレビューを表示する
5. The Video Risk Analyzer shall リスクスコアの高い順にソート表示するオプションを提供する
6. If リスク箇所が検出されない, then the Video Risk Analyzer shall リスクなしの旨を表示する

### Requirement 7: 解析進捗管理

**Objective:** As a 広報担当者, I want 解析の進捗状況を確認したい, so that 待ち時間の目安を把握できる

#### Acceptance Criteria
1. While 解析処理が実行中である, the Video Risk Analyzer shall 進捗状況をリアルタイムで表示する
2. The Video Risk Analyzer shall 各解析フェーズ（音声・Gemini統合解析）の進捗を個別に表示する
3. The Video Risk Analyzer shall 推定残り時間を表示する
4. If 解析処理がエラーで中断する, then the Video Risk Analyzer shall エラー内容を表示し、再試行オプションを提供する

### Requirement 8: 非同期タスク処理

**Objective:** As a 広報担当者, I want 動画アップロード後にブラウザを閉じても解析が継続されてほしい, so that 長時間の解析を待たずに他の作業ができる

#### Acceptance Criteria
1. When 動画がアップロードされる, the Video Risk Analyzer shall 即座にジョブIDを発行し、解析処理をバックグラウンドタスクとして開始する
2. The Video Risk Analyzer shall ブラウザを閉じても解析処理を継続する
3. When ユーザが再度アクセスする, the Video Risk Analyzer shall 過去の解析ジョブ一覧を表示する
4. The Video Risk Analyzer shall 各ジョブのステータス（待機中・処理中・完了・エラー）を表示する
5. When ユーザがジョブを選択する, the Video Risk Analyzer shall 該当ジョブの詳細（進捗または結果）を表示する
6. If 解析処理が失敗する, then the Video Risk Analyzer shall ジョブを失敗ステータスに更新し、エラー詳細を記録する

### Requirement 9: 動画削除

**Objective:** As a 広報担当者, I want 投稿した動画（解析ジョブ）を削除したい, so that 不要になった解析結果を一覧から除外できる

#### Acceptance Criteria
1. When ユーザがジョブ一覧で削除操作を行う, the Video Risk Analyzer shall 該当ジョブを論理削除する（deleted_atタイムスタンプを記録）
2. When ユーザが解析結果画面で削除操作を行う, the Video Risk Analyzer shall 該当ジョブを論理削除し、ジョブ一覧に遷移する
3. The Video Risk Analyzer shall 削除前に確認ダイアログを表示し、ユーザの意思を確認する
4. When ジョブが論理削除される, the Video Risk Analyzer shall ジョブ一覧・詳細取得・結果取得のAPIレスポンスから該当ジョブを除外する
5. The Video Risk Analyzer shall 論理削除されたジョブのデータ（動画ファイル・解析結果）をデータベース上に保持する
