import pytest
import json
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock

# 新旧のアナライザーとリスク評価サービスをインポート
from app.services.video_analyzer import VideoAnalyzerService as NewAnalyzer
from app.services.old_risk_evaluator import VideoAnalyzerService as OldAnalyzer
from app.services.risk_evaluator import RiskEvaluatorService

from tests.evaluation_logic import calculate_metrics

# --- 定数定義 ---
EVALUATION_DATA_DIR = Path(__file__).parent / "evaluation_data"
VIDEO_DIR = EVALUATION_DATA_DIR / "videos"
ANNOTATION_DIR = EVALUATION_DATA_DIR / "annotations"
IOU_THRESHOLD = 0.5  # TPと判定するIoUの閾値

# --- フィクスチャ定義 ---
# scopeをfunction（デフォルト）にして、テストごとにインスタンスが生成されるようにする
@pytest.fixture
def new_analyzer():
    """新しい動画分析サービスのインスタンスを提供"""
    return NewAnalyzer()

@pytest.fixture
def old_analyzer():
    """古い静止画ベースの分析サービスのインスタンスを提供"""
    return OldAnalyzer()

@pytest.fixture
def risk_evaluator():
    """リスク評価サービスのインスタンスを提供"""
    return RiskEvaluatorService()

@pytest.fixture
def mock_storage_service():
    """StorageServiceをモックし、download_fileの挙動を書き換える"""
    def mock_download(file_path, destination):
        # S3キーとして渡されるはずのfile_pathをローカルパスとして扱い、
        # 指定のdestinationにコピーすることでダウンロードを模倣する
        print(f"Mocking download: {file_path} -> {destination}")
        shutil.copyfile(file_path, destination)

    # new_analyzerとold_analyzerの両方が使うStorageServiceをパッチする
    with patch("app.services.video_analyzer.StorageService") as mock_new, \
         patch("app.services.old_risk_evaluator.StorageService") as mock_old:
        
        mock_service_instance = MagicMock()
        mock_service_instance.download_file.side_effect = mock_download
        
        mock_new.return_value = mock_service_instance
        mock_old.return_value = mock_service_instance
        yield

# --- テスト対象の動画ファイルを定義 ---
video_files = [
    "risk_video_01.mp4",
    "no_risk_video_01.mp4",
]

# --- テスト関数 ---
@pytest.mark.parametrize("video_file", video_files)
# mock_storage_serviceを先に評価させるために引数の順番を変更
def test_evaluate_risk_analysis(mock_storage_service, new_analyzer, old_analyzer, risk_evaluator, video_file):
    """
    指定された動画ファイルに対して、新旧両方の分析手法の精度を評価する。
    """
    # モックを使うため、StorageServiceには実際のローカルファイルパスを渡す
    video_path = str(VIDEO_DIR / video_file)
    annotation_path = ANNOTATION_DIR / f"{Path(video_file).stem}.json"

    print(f"--- Evaluating: {video_file} ---")

    # 1. 正解ラベルを読み込む
    with open(annotation_path, "r") as f:
        true_annotation = json.load(f)
    true_risks = true_annotation.get("risks", [])

    # 2. 新手法（動画直接分析）の評価
    print("\n[Executing] New Analyzer (Direct Video Analysis)")
    new_analysis_result = new_analyzer.analyze(video_path)
    
    # new_analysis_resultをRiskEvaluatorServiceに渡して最終評価を取得
    assessment_new = risk_evaluator.evaluate(
        transcription=None,
        ocr=None,
        video_analysis=new_analysis_result,
        metadata={},
    )
    predicted_risks_new = [
        {
            "timestamp_start": risk.timestamp,
            "timestamp_end": risk.end_timestamp,
        }
        for risk in assessment_new.risks
    ]
    metrics_new = calculate_metrics(predicted_risks_new, true_risks, IOU_THRESHOLD)
    print(f"[Result] New Analyzer Metrics: {metrics_new}")

    # 3. 旧手法（静止画ベース分析）の評価
    print("\n[Executing] Old Analyzer (Frame-based Analysis)")
    # 旧手法も同じくローカルパスを渡す
    old_analysis_result = old_analyzer.analyze(video_path)
    predicted_risks_old = convert_old_result_to_risks(old_analysis_result, old_analyzer, risk_evaluator)
    
    metrics_old = calculate_metrics(predicted_risks_old, true_risks, IOU_THRESHOLD)
    print(f"[Result] Old Analyzer Metrics: {metrics_old}")

    # 4. 簡単なアサーション（テストが失敗しないことを確認）
    assert "f1_score" in metrics_new
    assert "f1_score" in metrics_old
    print("\n--- Evaluation Finished ---")


def convert_old_result_to_risks(result, old_analyzer, risk_evaluator) -> list:
    """
    旧手法の分析結果をリスク時間帯リストに変換する。
    """
    # 1. 旧アナライザーの結果を辞書に変換
    video_analysis_dict = old_analyzer.result_to_dict(result)

    # 2. リスク評価サービスを実行
    # メタデータは空で、映像解析結果のみ渡す
    assessment = risk_evaluator.evaluate(
        transcription=None,
        ocr=None,
        video_analysis=video_analysis_dict,
        metadata={},
    )

    # 3. 評価結果をメトリクス計算用のフォーマットに変換
    predicted_risks = [
        {
            "timestamp_start": risk.timestamp,
            "timestamp_end": risk.end_timestamp,
        }
        for risk in assessment.risks
    ]
    
    return predicted_risks
