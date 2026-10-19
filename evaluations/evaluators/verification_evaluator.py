"""
SwachhLoop AI — Cleanup Verification Service Evaluator
======================================================
Evaluates cleanup verification verdicts, change score calibration,
and identical-image rejection.
"""

import io
import json
from pathlib import Path
from typing import Any
from PIL import Image

from backend.services.cleanup_verifier import get_cleanup_verifier
from evaluations.evaluators.base import BaseEvaluator
from evaluations.metrics import compute_classification_metrics


def _make_image_bytes(color: list[int] | None) -> bytes:
    if not color:
        return b""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color=tuple(color))
    img.save(buf, format="JPEG")
    return buf.getvalue()


class VerificationEvaluator(BaseEvaluator):
    def __init__(self, dataset_path: str = "evaluations/datasets/verification_eval.json"):
        self.dataset_path = Path(dataset_path)

    @property
    def name(self) -> str:
        return "Cleanup Verification & Quality Audit Evaluation"

    async def evaluate(self) -> dict[str, Any]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        verifier = get_cleanup_verifier()
        y_true = []
        y_pred = []
        details = []

        for case in cases:
            is_empty = case.get("is_empty", False)
            if is_empty:
                before_bytes = b""
                after_bytes = b""
            else:
                before_bytes = _make_image_bytes(case.get("before_color"))
                after_bytes = _make_image_bytes(case.get("after_color"))

            result = await verifier.verify(before_bytes, after_bytes)
            status_val = result.status.value if hasattr(result.status, "value") else str(result.status)
            expected_status = case["expected_status"]

            y_true.append(expected_status)
            y_pred.append(status_val)

            details.append({
                "id": case["id"],
                "name": case["name"],
                "expected_status": expected_status,
                "pred_status": status_val,
                "match": expected_status == status_val,
                "change_score": result.change_score,
                "confidence": result.confidence,
                "notes": result.notes,
            })

        metrics = compute_classification_metrics(y_true, y_pred)

        return {
            "suite_name": self.name,
            "dataset_type": "offline_synthetic_fixtures",
            "sample_count": len(cases),
            "metrics": {
                "verification_accuracy": metrics["accuracy"],
                "macro_f1": metrics["macro_f1"],
                "macro_precision": metrics["macro_precision"],
                "macro_recall": metrics["macro_recall"],
            },
            "per_status_breakdown": metrics["per_class"],
            "details": details,
        }
