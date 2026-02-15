# Requirements Document

## Introduction

本ドキュメントは、Video Risk Analyzerの後工程として実装する「タイムラインエディタ」機能の要件を定義します。既存のモックUI（`mock/`フォルダ）をベースに、リスク判定結果の可視化、AI編集提案、動画編集・エクスポート機能を実装します。

### 前提条件
- リスク判定は完了済み（RiskAssessment, RiskItemが存在）
- 既存モックUI（`mock/components/video-editor.tsx`等）がある
- 対象ユーザー: SaaSベンダーの広報担当者

### モック画面構成
```
┌─────────────────────────────────────────────────────────────┐
│ Header: [Video Risk Editor] [Upload] [Save] [Export]        │
├─────────────────────────────────────────┬───────────────────┤
│                                         │                   │
│         VideoPreview                    │  EditingSuggestions│
│         (動画プレビュー)                 │  (編集提案パネル)  │
│                                         │                   │
├─────────────────────────────────────────┤  - リスク箇所一覧  │
│         RiskGraph                       │  - プレビュー      │
│         (リスクスコアグラフ)             │  - カット適用      │
├─────────────────────────────────────────┤                   │
│         Timeline                        │                   │
│         (タイムライン)                   │                   │
├─────────────────────────────────────────┴───────────────────┤
│ VideoControls: [◄◄][▶][►►] ━━━━○━━━━ 0:24 / 1:30 [🔊][⛶]   │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

### Requirement 1: 動画プレビュー画面

**Objective:** As a 広報担当者, I want リスク判定済み動画をプレビューしたい, so that 問題箇所を視覚的に確認できる

#### Acceptance Criteria
1. When ユーザーが解析完了済みジョブを選択する, the Timeline Editor shall 動画プレビュー画面を表示する
2. The Timeline Editor shall 動画をアスペクト比を維持して中央に表示する
3. The Timeline Editor shall 現在の再生時刻をオーバーレイで表示する（形式: `M:SS.s`）
4. When 再生位置がカット範囲内にある, the Timeline Editor shall カット範囲のオーバーレイを表示し「この部分はカットされます」とカット時間範囲を表示する
5. When 動画URLが未設定の場合, the Timeline Editor shall プレースホルダー画面を表示する

### Requirement 2: 動画再生コントロール

**Objective:** As a 広報担当者, I want 動画の再生を操作したい, so that 任意の位置を確認できる

#### Acceptance Criteria
1. The Timeline Editor shall 再生/一時停止ボタンを提供する
2. The Timeline Editor shall 5秒戻る/5秒進むスキップボタンを提供する
3. The Timeline Editor shall シークバー（スライダー）で任意の位置にジャンプできる機能を提供する
4. The Timeline Editor shall 現在時刻と総再生時間を `M:SS / M:SS` 形式で表示する
5. The Timeline Editor shall 音量調整ボタンを提供する
6. The Timeline Editor shall フルスクリーン切替ボタンを提供する

### Requirement 3: リスクスコアグラフ

**Objective:** As a 広報担当者, I want 動画全体のリスク推移を確認したい, so that 高リスク箇所の分布を把握できる

#### Acceptance Criteria
1. The Timeline Editor shall 時間軸に沿ったリスクスコアグラフをSVGで表示する
2. The Timeline Editor shall リスクレベルに応じたグラデーション塗りつぶしを表示する（高:赤、中:黄、低:緑）
3. The Timeline Editor shall 高リスク区間（70%以上）を背景ハイライトで強調表示する
4. The Timeline Editor shall 現在再生位置を縦線インジケーターで表示する
5. The Timeline Editor shall 現在位置のリスクレベルを数値で表示する（例: 「現在: 85%」）
6. The Timeline Editor shall 0%と100%のラベルを軸に表示する
7. The Timeline Editor shall 30%と70%の位置に補助グリッド線を表示する

### Requirement 4: タイムライン

**Objective:** As a 広報担当者, I want タイムライン上でリスク区間と編集状態を確認したい, so that 編集対象を視覚的に把握できる

#### Acceptance Criteria
1. The Timeline Editor shall 動画の長さに応じたタイムマーカーを等間隔で表示する
2. The Timeline Editor shall クリック/ドラッグ操作で再生位置をシークできる機能を提供する
3. The Timeline Editor shall 現在の再生位置を再生ヘッド（縦線+上下の円形ハンドル）で表示する
4. The Timeline Editor shall カット適用済み範囲を赤色（destructive）で表示する
5. The Timeline Editor shall AI提案範囲を黄色（warning）で表示する
6. When ユーザーがAI提案範囲をクリックする, the Timeline Editor shall 該当提案を選択状態にする
7. When 提案が選択状態である, the Timeline Editor shall 該当範囲を強調表示する（border + 明るい背景色）

### Requirement 5: 編集提案パネル

**Objective:** As a 広報担当者, I want AI編集提案の一覧を確認したい, so that 各リスク箇所の詳細と推奨対応を把握できる

#### Acceptance Criteria
1. The Timeline Editor shall 編集提案パネルをサイドバーとして表示する（デスクトップ: 右側固定、モバイル: アコーディオン）
2. The Timeline Editor shall 検出された高リスク箇所の件数を表示する
3. The Timeline Editor shall 各提案をカード形式で表示する
4. The Timeline Editor shall 各提案カードに以下を表示する: リスクレベルバッジ、時間範囲、リスクの理由
5. When ユーザーが提案カードをクリックする, the Timeline Editor shall 該当提案を選択状態にしタイムライン上で強調表示する
6. The Timeline Editor shall 各提案カードに「プレビュー」ボタンを提供する
7. When ユーザーが「プレビュー」ボタンをクリックする, the Timeline Editor shall 該当時間位置にシークする
8. The Timeline Editor shall 各提案カードに「カット適用」ボタンを提供する
9. When ユーザーが「カット適用」ボタンをクリックする, the Timeline Editor shall 該当範囲をカット対象として登録する
10. The Timeline Editor shall 「すべての提案を適用」ボタンを提供する

### Requirement 6: 編集アクション拡張

**Objective:** As a 広報担当者, I want カット以外の編集オプションも選択したい, so that 状況に応じた適切な対応ができる

#### Acceptance Criteria
1. The Timeline Editor shall 以下の編集アクションを提供する: カット、ミュート、モザイク、テロップ、対応しない
2. When ユーザーが「ミュート」を選択する, the Timeline Editor shall 該当区間を音声無音化対象としてマークする
3. When ユーザーが「モザイク」を選択する, the Timeline Editor shall モザイク適用領域を指定するUIを表示する
4. When ユーザーが「テロップ」を選択する, the Timeline Editor shall テロップ内容を入力するUIを表示する
5. When ユーザーが「対応しない」を選択する, the Timeline Editor shall 該当リスク区間をスキップ済みとしてマークする
6. The Timeline Editor shall 編集アクションの取り消し（Undo）機能を提供する

### Requirement 7: ヘッダーアクション

**Objective:** As a 広報担当者, I want ナビゲーション・保存・エクスポートを行いたい, so that 編集ワークフローを完結できる

#### Acceptance Criteria
1. The Timeline Editor shall ヘッダー左にジョブ一覧への「← ジョブ一覧」ナビゲーションボタン（tertiary）を提供する
2. The Timeline Editor shall ヘッダー右にアップロード画面への「新規解析」ナビゲーションボタン（tertiary）を提供し、編集アクションボタン群とは縦線で区切る
3. The Timeline Editor shall ヘッダーに「保存」ボタン（ghost）を提供する
4. When ユーザーが「保存」ボタンをクリックする, the Timeline Editor shall 編集セッションの状態を保存する
5. The Timeline Editor shall ヘッダーに「エクスポート」ボタン（primary）を提供する
6. When ユーザーが「エクスポート」ボタンをクリックする, the Timeline Editor shall 編集内容を適用した動画の生成を開始する
7. The Timeline Editor shall グローバルナビゲーションを非表示にし、フルスクリーンレイアウトで表示する

### Requirement 8: 動画編集処理

**Objective:** As a システム, I want ユーザーが選択した編集内容を動画に適用したい, so that 編集済み動画を生成できる

#### Acceptance Criteria
1. When ユーザーがエクスポートを実行する, the Timeline Editor shall 編集ジョブをバックエンドに送信する
2. The Timeline Editor shall FFmpegを使用して以下の編集処理を実行する: カット、ミュート、モザイク、テロップ合成
3. While 編集処理が実行中である, the Timeline Editor shall 進捗状況を表示する
4. If 編集処理が失敗する, then the Timeline Editor shall エラー内容を表示し再試行オプションを提供する
5. When 編集処理が完了する, the Timeline Editor shall 編集済み動画のダウンロードリンクを表示する
6. The Timeline Editor shall 編集済み動画をmp4形式でエクスポートする

### Requirement 9: レスポンシブ対応

**Objective:** As a 広報担当者, I want モバイルデバイスでも編集画面を操作したい, so that 外出先でも確認・編集ができる

#### Acceptance Criteria
1. The Timeline Editor shall デスクトップとモバイルで異なるレイアウトを提供する
2. While モバイル表示である, the Timeline Editor shall 編集提案パネルをアコーディオン形式で表示する
3. While モバイル表示である, the Timeline Editor shall ハンバーガーメニューでサイドバーを切り替える
4. While モバイル表示である, the Timeline Editor shall ヘッダーのボタンラベルを非表示にしアイコンのみ表示する
5. The Timeline Editor shall タイムライン・リスクグラフエリアの高さをデバイスに応じて調整する（モバイル: h-48、デスクトップ: h-64）

