from typing import List, Dict, Any

def calculate_iou(pred_box: Dict[str, Any], true_box: Dict[str, Any]) -> float:
    """
    時間セグメントのIoU (Intersection over Union)を計算する。

    Args:
        pred_box: 予測された時間ボックス {"timestamp_start": float, "timestamp_end": float}
        true_box: 正解の時間ボックス {"timestamp_start": float, "timestamp_end": float}

    Returns:
        IoUスコア (0.0 ~ 1.0)
    """
    try:
        # 比較・計算の前に数値をfloatに変換して堅牢にする
        pred_start = float(pred_box["timestamp_start"])
        pred_end = float(pred_box["timestamp_end"])
        true_start = float(true_box["timestamp_start"])
        true_end = float(true_box["timestamp_end"])
    except (ValueError, TypeError):
        return 0.0 # 変換できない場合はIoU 0とする

    # intersectionの計算
    inter_start = max(pred_start, true_start)
    inter_end = min(pred_end, true_end)
    inter_duration = max(0, inter_end - inter_start)

    # unionの計算
    pred_duration = pred_end - pred_start
    true_duration = true_end - true_start
    union_duration = pred_duration + true_duration - inter_duration

    if union_duration == 0:
        return 0.0

    return inter_duration / union_duration


def calculate_metrics(
    predicted_risks: List[Dict[str, Any]],
    true_risks: List[Dict[str, Any]],
    iou_threshold: float = 0.5
) -> Dict[str, float]:
    """
    予測されたリスクと正解リスクから評価指標（再現率、適合率、F1スコア）を計算する。

    Args:
        predicted_risks: 予測されたリスクのリスト
        true_risks: 正解リスクのリスト
        iou_threshold: TPと判定するためのIoUの閾値

    Returns:
        評価指標を含む辞書
    """
    tp = 0  # True Positives
    fp = 0  # False Positives
    fn = 0  # False Negatives

    if not predicted_risks and not true_risks:
        return {"precision": 1.0, "recall": 1.0, "f1_score": 1.0}

    if not predicted_risks:
        fn = len(true_risks)
        return {"precision": 1.0, "recall": 0.0, "f1_score": 0.0, "tp": 0, "fp": 0, "fn": fn}
    
    if not true_risks:
        fp = len(predicted_risks)
        return {"precision": 0.0, "recall": 1.0, "f1_score": 0.0, "tp": 0, "fp": fp, "fn": 0}


    matched_true_indices = set()

    for pred_risk in predicted_risks:
        best_iou = 0
        best_match_idx = -1
        for i, true_risk in enumerate(true_risks):
            iou = calculate_iou(pred_risk, true_risk)
            if iou > best_iou:
                best_iou = iou
                best_match_idx = i

        if best_iou >= iou_threshold and best_match_idx not in matched_true_indices:
            tp += 1
            matched_true_indices.add(best_match_idx)
        else:
            fp += 1
    
    fn = len(true_risks) - len(matched_true_indices)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "tp": tp,
        "fp": fp,
        "fn": fn
    }
