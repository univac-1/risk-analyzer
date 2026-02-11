# 障害分析レポート: タイムラインエディタ機能 デプロイ時障害

- **発生日時**: 2026-02-11
- **環境**: Google Cloud Run (asia-northeast1)
- **ブランチ**: `agentic-feature` (timeline-editor 機能)
- **ステータス**: 未修正

## 障害概要

タイムラインエディタ機能を Google Cloud Run にデプロイ後、エディタページで 2 件の API エラーが発生。

## 障害一覧

### BUG-1: 動画URL取得 500 Internal Server Error

| 項目 | 内容 |
| --- | --- |
| エンドポイント | `GET /api/jobs/{job_id}/video-url` |
| ステータス | 500 Internal Server Error |
| 影響 | エディタの動画プレビューが表示されない |
| 重大度 | **Critical** - エディタ機能が使用不可 |

**リクエスト例:**

```
GET https://risk-analyzer-backend-344159057124.asia-northeast1.run.app/api/jobs/0a6b5ace-a909-4b63-9d55-a5118cd84099/video-url
```

### BUG-2: エクスポート状況取得 404 Not Found

| 項目 | 内容 |
| --- | --- |
| エンドポイント | `GET /api/jobs/{job_id}/export/status` |
| ステータス | 404 Not Found |
| 影響 | コンソールにエラーが表示される（機能的影響は軽微） |
| 重大度 | **Low** - フロントエンドで 404 をハンドリング済みだが、不要なエラーリクエストが発生 |

**リクエスト例:**

```
GET https://risk-analyzer-backend-344159057124.asia-northeast1.run.app/api/jobs/d9d97958-1f53-42ec-9eee-cfca71161147/export/status
```

## 原因分析

### BUG-1: GCS 署名付き URL 生成の `access_token` 未指定

**根本原因:** Cloud Run 環境ではサービスアカウントの秘密鍵を直接持たないため、GCS の `blob.generate_signed_url()` は IAM signBlob API を使って署名する必要がある。現在のコードは `service_account_email` のみ渡しており、API 呼び出しに必要な `access_token` を渡していない。

**該当コード:** `backend/app/services/storage.py:198-232` (`GCSStorageService.generate_presigned_url`)

```python
# 現在のコード（不具合あり）
return blob.generate_signed_url(
    version="v4",
    expiration=timedelta(seconds=expiration),
    method="GET",
    service_account_email=service_account_email,
    # access_token が未指定 → Cloud Run で失敗
)
```

**ローカル/MinIO 環境で発生しなかった理由:**

- ローカル開発では `use_gcs=False` で `S3StorageService`（MinIO）を使用
- `GCSStorageService.generate_presigned_url()` は今回のデプロイで初めて本番実行された

**影響するエンドポイント:**

| エンドポイント | 用途 |
| --- | --- |
| `GET /api/jobs/{job_id}/video-url` | エディタの動画プレビュー URL 取得 |
| `GET /api/jobs/{job_id}/export/download` | エクスポート済み動画のダウンロード URL 取得 |

**修正方針:**

```python
# 修正: credentials を refresh して access_token を取得し渡す
credentials, _ = google.auth.default()
auth_request = google.auth.transport.requests.Request()
credentials.refresh(auth_request)

return blob.generate_signed_url(
    version="v4",
    expiration=timedelta(seconds=expiration),
    method="GET",
    service_account_email=service_account_email,
    access_token=credentials.token,  # これが必要
)
```

**前提条件:** Cloud Run サービスアカウントに `iam.serviceAccounts.signBlob` 権限（`roles/iam.serviceAccountTokenCreator`）が必要。

### BUG-2: エクスポート未実行時の不要な 404 レスポンス

**根本原因:** フロントエンドのエディタページはマウント時に必ず `GET /export/status` を呼び出す設計になっている。エクスポートが一度も実行されていない場合、バックエンドは以下の順でチェックし、該当しない段階で 404 を返す。

```
1. ジョブ存在確認 → 404 "ジョブが見つかりません"
2. 編集セッション確認 → 404 "編集セッションが見つかりません"
3. エクスポートジョブ確認 → 404 "エクスポートジョブが見つかりません"
```

**該当コード:**

- バックエンド: `backend/app/api/routes/editor.py:163-211`
- フロントエンド: `frontend/src/components/editor/EditorPage.tsx:84-105`

**フロントエンド側のハンドリング:**

```typescript
// 404 は無視する設計（EditorPage.tsx:97-98）
catch (err) {
  if (err instanceof Error && err.message.includes('404')) {
    return  // 無視
  }
  setExportError('エクスポート状況の取得に失敗しました')
}
```

**問題点:**

- 機能的には正常動作する（404 はフロントエンドでハンドリング済み）
- ただし、毎回不要な HTTP リクエストが発生し、ブラウザコンソールにエラーが表示される
- API 設計として「リソースが存在しない」状態を 404 で返すのは REST 的には正しいが、エディタページの初期表示で必ず発生するのは非効率

**修正方針（2案）:**

**案A: バックエンド - 未実行時は空ステータスを返す（推奨）**

```python
# エクスポートジョブが存在しない場合、404 ではなく空ステータスを返す
if not export_job:
    return ExportStatusResponse(
        export_id=None,
        status="none",
        progress=0.0,
        error_message=None,
    )
```

**案B: フロントエンド - edit-session 取得後に条件付きで呼ぶ**

```typescript
// edit-session のレスポンスにエクスポート有無の情報を含め、
// エクスポートが存在する場合のみ status を取得する
```

## 影響範囲

| 機能 | BUG-1 影響 | BUG-2 影響 |
| --- | --- | --- |
| エディタ: 動画プレビュー | 表示不可 | - |
| エディタ: エクスポートダウンロード | ダウンロード不可 | - |
| エディタ: エクスポート状況表示 | - | コンソールエラー（機能影響なし） |
| アップロード | なし | なし |
| ジョブ一覧 | なし | なし |
| 解析進捗 | なし | なし |
| 解析結果 | なし | なし |

## master ブランチとの関係

- master には `/api/jobs/{job_id}/video-url`, `/export/status`, `/export/download` エンドポイントが存在しない
- これらは全て timeline-editor 機能（`agentic-feature` ブランチ）で追加されたエンドポイント
- `GCSStorageService.generate_presigned_url()` のコード自体は master にも存在するが、呼び出すコードパスがないため問題が顕在化していなかった

## 修正の優先順位

| 優先度 | バグ | 修正内容 |
| --- | --- | --- |
| **P0** | BUG-1 | `access_token` を `generate_signed_url` に渡す |
| **P2** | BUG-2 | エクスポート未実行時の 404 を空ステータスレスポンスに変更 |
