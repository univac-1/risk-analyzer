以下は、指定ページ（Zennの「第4回 Agentic AI Hackathon with Google Cloud」）に載っている内容を、項目ごとに噛み砕いて整理した説明です。 ([Zenn][1])

---

## 1) ハッカソンの概要（何をするイベント？）

* イベント名：**第4回 Agentic AI Hackathon with Google Cloud** ([Zenn][1])
* 期間：**2025/12/10〜2026/2/15**（登録・提出の期間を含む） ([Zenn][1])
* 主催：**Zenn（クラスメソッド株式会社）**／協賛：**グーグル・クラウド・ジャパン合同会社（窓口：株式会社ボイスリサーチ）** ([Zenn][1])
* 方向性：従来の「Google Cloud AI ハッカソン」第4回で、今回は“自律的に考え行動するAI”の潮流を踏まえ、名称を**Agentic AI Hackathon**へリニューアル、と説明されています。 ([Zenn][1])
* 技術面の“目玉”として、ページ本文では「**Gemini 3**」や「AntiGravity などのツールを使った次世代のAIコーディング」への言及があります。 ([Zenn][1])
* 初心者/少人数でも参加しやすくする工夫として、**チームビルディング機会**・**学習機会（ハンズオン/Bootcamp）**・**奨励賞（5枠）新設**が挙げられています。 ([Zenn][1])

---

## 2) Google Cloudクレジット配布について（重要注意）

今回のハッカソンでは、**Google Cloudクレジット（クーポン）の配布はなし**と明記されています。一方で、Google Cloudの**無料枠（Always Free）**などは通常通り利用可能、という案内です。 ([Zenn][1])

---

## 3) 参加条件（参加できる人・できない人）

**参加できる人**

* **日本国内在住**かつ**18歳以上**の個人、または個人で構成されるチーム。 ([Zenn][1])

**参加できない人（例）**

* **政府機関の職員**
* **企業の意向で“会社代表”として選出された個人**
* 主催/スポンサーの従業員や関係者・家族、運営関与者 など ([Zenn][1])

※FAQでは「非常勤や兼業（フリーランス）でも政府機関の職員に該当するなら参加不可」と明言されています。 ([Zenn][2])

---

## 4) 全体スケジュール（いつ何がある？）

### ハッカソン本体

* 登録・提出期間：**2025/12/10〜2026/2/15**（※注記あり） ([Zenn][3])
* 1次審査：**2026/2/16〜2/23** ([Zenn][3])
* 2次審査：**2026/2/24〜3/2** ([Zenn][3])
* 受賞者/候補者通知：**2026/3/2** ([Zenn][3])
* 最終審査・発表：**2026/3/19**（Google Cloud Agentic AI Summit ’26 Spring 内で最終ピッチ＆表彰） ([Zenn][3])

### 締切の注記（要チェック）

* ページ本文の注記：**2/14までに参加登録**し、**2/15までに提出**で正式参加、という説明。 ([Zenn][3])
* 参加規約PDF本文でも、登録締切が2/14・提出締切が2/15と記載があります。 ([static.zenn.studio][4])
* ただし参加規約PDFの脚注（*1）部分に、**登録2/13まで／提出2/14まで**のように読める記載もあり、本文とズレています（おそらく脚注側の誤記の可能性）。最終的には、**このZennページと運営からの案内メールの“最新版”を優先**するのが安全です。 ([static.zenn.studio][4])

---

## 5) 関連イベント（チーム作り・相談・学習）

### オンラインオフィスアワー

* **2026/1/8(木) 18:00〜19:30**、Google Meetで実施
* Google Cloudエンジニア＋Zenn運営が、技術・事務の質問に回答
* 接続URLは**1/6のリマインドメール**で案内 ([Zenn][3])

### チームビルディング・アイディエーションイベント（現地）

* **2026/1/16(木) 19:00〜21:00**
* クラスメソッド 日比谷本社オフィス ([Zenn][3])

### ミニハッカソン（募集終了）

* **2026/1/24(土)・1/25(日)**（現地）
* **定員到達で募集終了**と更新情報に記載 ([Zenn][3])

### Google Cloud Agentic AI Bootcamp 2026 Winter

* **1/19〜1/30の期間に全10回セッション**（例：ADK、Firebase×AIエージェント、Cloud Run/Agent Engine、Gemini CLI/Code Assist など） ([Zenn][3])

---

## 6) ルールの要点（何を作ればOK？何を出せばOK？）

### 参加形態

* 個人/チームどちらでも可（チームは**全員参加登録が必要**）
* **複数プロジェクト参加も可**（チーム＋個人の両立もOK）
* 参加者交流・Q&A用に**Discordサーバー**を用意 ([Zenn][5])

### 開発プロジェクトの必須条件（“Google Cloudをこう使ってね”）

提出するプロジェクトは、少なくとも以下を満たす必要があります。 ([Zenn][5])

**(必須) アプリ実行系プロダクトを1つ以上**

* App Engine / Compute Engine / GKE / Cloud Run / Cloud Functions / Cloud TPU・GPU など ([Zenn][5])

**(必須) AI系（Google Cloud AI技術）を1つ以上**

* Vertex AI、Gemini API、Gemma、Imagen、Agent Builder、ADK、Speech、Vision、NLP、Translation など ([Zenn][5])

（任意）Flutter / Firebase / Veo などを使っている場合はフォームで申告、という扱いです。 ([Zenn][5])

### 提出物（提出に必要な3点）

1. **GitHubリポジトリURL（公開）**
2. **デプロイ済みURL（動作確認できる状態）**
3. **Zenn記事URL**（記事ルールあり） ([Zenn][5])

**GitHubに関する注意**

* 提出時点の状態を**2026/3/2まで保持**
* 提出後も開発継続したいなら、締切以前の状態に**タグを付け、そのタグURLを提出**
* 審査期間中（〜3/2）は**デプロイも動く状態を維持** ([Zenn][5])

### Zenn記事の作成ルール

* カテゴリ：**Idea**
* トピック：`gch4` を追加
* 記事に含める内容：

  1. プロジェクト概要（対象ユーザー／課題／特徴）
  2. システムアーキテクチャ図（画像でも可）
  3. デモ動画（約3分、YouTube公開して埋め込み） ([Zenn][5])

※デプロイURLは記事に載せなくてOK（公開する場合は費用など注意）。 ([Zenn][5])

---

## 7) 審査基準（評価ポイント）

審査基準は大きく3つ：

* **課題の新規性**（未解決で多くの人が抱える課題発見）
* **解決策の有効性**（課題に効いているか）
* **実装品質と拡張性**（ツール活用、運用しやすさ、費用対効果など） ([Zenn][5])

---

## 8) 賞金・プライズ（総額175万円）

* 最優秀賞：**50万円 ×1**
* 優秀賞：**25万円 ×3**
* 奨励賞：**10万円 ×5**（3つの審査基準のどれかが特に秀でているプロジェクトを想定） ([Zenn][6])

---

## 9) 審査員（掲載分）

ページに掲載されている審査員（2026/01時点の表示）：

* 佐藤 祥子（THE BIGLE株式会社 代表取締役） ([Zenn][7])
* 渡部 陽太（アクセンチュア株式会社／ゆめみCTO） ([Zenn][7])
* 李 碩根（松尾研究所 シニアデータサイエンティスト／SozoWorks代表取締役） ([Zenn][7])
* 伴野 智樹（一般社団法人MA 理事／フリーランス） ([Zenn][7])
* 「その他の審査員は近日公開予定」とも書かれています。 ([Zenn][7])

---

## 10) プロジェクト一覧タブ

現時点では「**掲載情報はありません**」と表示されています（提出後に掲載が始まる形式の可能性）。 ([Zenn][8])

---

## 11) 更新情報（アナウンス）

* **2025/12/25**：ミニハッカソン募集終了 ([Zenn][9])
* **2025/12/25**：オンラインオフィスアワー／AI Bootcamp情報を追加 ([Zenn][9])

---

## 12) FAQでよくある論点（要点だけ抜粋）

* 申込後にチーム結成OK（イベントやDiscordで募集可能） ([Zenn][2])
* チーム参加にスキル条件なし／複数プロジェクト参加OK ([Zenn][2])
* ローカルで動けばOKではなく、**Google Cloudへデプロイ必須** ([Zenn][2])
* ネイティブアプリでもOKだが、確認はデモ動画中心になる可能性 ([Zenn][2])
* リポジトリは原則Public、提出後の修正は避ける（戻すよう案内あり） ([Zenn][2])
* Firebase系の扱い：App Hostingは条件を満たす、Vertex AI in FirebaseでGemini利用も条件を満たす、Firebase Extensionだけでは満たさない、など ([Zenn][2])
* 期間前から進んでいたプロジェクトの提出は公平性の観点で控えるよう案内 ([Zenn][2])
* 締切は「当日23:59まで」という認識でOK ([Zenn][2])

---

## 13) 参加規約（PDF）の主要ポイント（ざっくり）

参加規約PDFでは、例えば以下が明文化されています：

* 参加登録で規約同意とみなす／スケジュールの定義 ([static.zenn.studio][4])
* 提出物は第三者権利を侵害しないこと、OSS利用時のライセンス遵守・明記 ([static.zenn.studio][4])
* **知的財産（著作権等）は参加者に帰属**する一方で、主催者・スポンサーに対し**審査/評価/プロモーション目的で無償利用できる権利**を付与（スクショや動画クリップ利用を含む） ([static.zenn.studio][4])
* 個人情報は運営・広報のために利用されることがある（主催者/スポンサー/Google Cloud Japan） ([static.zenn.studio][4])
* 免責、規約違反時の失格、準拠法・管轄（東京地裁）など ([static.zenn.studio][4])

※このPDFは本来スクリーンショットで確認すべきところ、こちらの環境ではPDFのスクリーンショット取得がエラーになったため、PDFのテキスト抽出結果を元に説明しています。 

---

## 問い合わせ先

ページ末尾に、問い合わせ先として **[zenn-support@classmethod.jp](mailto:zenn-support@classmethod.jp)（クラスメソッド Zenn 運営チーム）** が記載されています。 ([Zenn][1])

---

[1]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4 "第4回 Agentic AI Hackathon with Google Cloud"
[2]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=faq "第4回 Agentic AI Hackathon with Google Cloud"
[3]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=schedule "第4回 AI Agent Hackathon with Google Cloud"
[4]: https://static.zenn.studio/permanent/hackathon/google-cloud-japan-ai-hackathon-vol4/terms.pdf "251205第4回Agentic AI Hackathon with Google Cloud参加規約.docx"
[5]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=rule "第4回 Agentic AI Hackathon with Google Cloud"
[6]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=prize "第4回 AI Agent Hackathon with Google Cloud"
[7]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=judge "第4回 Agentic AI Hackathon with Google Cloud"
[8]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=projects "第4回 Agentic AI Hackathon with Google Cloud"
[9]: https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=updates "第4回 Agentic AI Hackathon with Google Cloud"
