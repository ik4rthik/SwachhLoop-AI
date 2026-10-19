"""
SwachhLoop AI — Waste Detection Service Evaluator
=================================================
Evaluates waste detection presence, category classification, and bounding box constraints.
"""

import io
import json
from pathlib import Path
from typing import Any
from PIL import Image

from backend.services.waste_detector import get_waste_detector
from evaluations.evaluators.base import BaseEvaluator


def _make_fixture_image(size: list[int], color: list[int] | None = None) -> bytes:
    if not size or size[0] == 0 or size[1] == 0:
        return b""
    buf = io.BytesIO()
    c = tuple(color) if color else (128, 128, 128)
    img = Image.new("RGB", (size[0], size[1]), color=c)
    img.save(buf, format="JPEG")
    return buf.getvalue()


class WasteDetectionEvaluator(BaseEvaluator):
    def __init__(self, dataset_path: str = "evaluations/datasets/waste_detection_eval.json"):
        self.dataset_path = Path(dataset_path)

    @property
    def name(self) -> str:
        return "Computer Vision Waste Detection Evaluation"

    async def evaluate(self) -> dict[str, Any]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        detector = get_waste_detector()

        detected_matches = 0
        category_matches = 0
        category_evaluated = 0
        valid_box_count = 0
        total_boxes = 0
        confidences = []
        details = []

        for case in cases:
            is_corrupt = case.get("is_corrupt", False)
            if is_corrupt:
                img_bytes = b"not_an_image_corrupted_data_12345"
            else:
                img_bytes = _make_fixture_image(case.get("size", [100, 100]), case.get("color"))

            result = await detector.detect(img_bytes)
            expected_detected = case["expected_detected"]
            expected_cat = case.get("expected_category")

            is_det_match = result.detected == expected_detected
            if is_det_match:
                detected_matches += 1

            cat_match = False
            if expected_cat:
                category_evaluated += 1
                if expected_cat in result.waste_types:
                    category_matches += 1
                    cat_match = True

            # Validate bounding boxes
            for b in result.bounding_boxes:
                total_boxes += 1
                coords = b.get("box_2d", [])
                if len(coords) == 4 and coords[2] >= coords[0] and coords[3] >= coords[1]:
                    valid_box_count += 1

            confidences.append(result.confidence)

            details.append({
                "id": case["id"],
                "description": case["description"],
                "expected_detected": expected_detected,
                "pred_detected": result.detected,
                "detected_match": is_det_match,
                "expected_category": expected_cat,
                "pred_categories": result.waste_types,
                "category_match": cat_match,
                "confidence": result.confidence,
                "box_count": len(result.bounding_boxes),
            })

        det_acc = round(detected_matches / len(cases), 4) if cases else 1.0
        cat_acc = round(category_matches / category_evaluated, 4) if category_evaluated > 0 else 1.0
        box_validity_rate = round(valid_box_count / total_boxes, 4) if total_boxes > 0 else 1.0
        avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

        return {
            "suite_name": self.name,
            "dataset_type": "offline_synthetic_fixtures",
            "sample_count": len(cases),
            "metrics": {
                "detection_accuracy": det_acc,
                "category_accuracy": cat_acc,
                "bounding_box_validity_rate": box_validity_rate,
                "average_confidence": avg_conf,
            },
            "details": details,
        }
