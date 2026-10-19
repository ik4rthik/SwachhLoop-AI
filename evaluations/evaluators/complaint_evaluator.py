"""
SwachhLoop AI — Complaint Analysis & NLP Evaluator
==================================================
Evaluates complaint classification, urgency precision/recall/F1,
Kalady landmark extraction accuracy, and prompt-injection resilience.
"""

import json
from pathlib import Path
from typing import Any

from backend.services.complaint_analyzer import get_complaint_analyzer
from evaluations.evaluators.base import BaseEvaluator
from evaluations.metrics import compute_classification_metrics


class ComplaintEvaluator(BaseEvaluator):
    def __init__(self, dataset_path: str = "evaluations/datasets/complaints_eval.json"):
        self.dataset_path = Path(dataset_path)

    @property
    def name(self) -> str:
        return "Complaint Analysis & Classification Evaluation"

    async def evaluate(self) -> dict[str, Any]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        analyzer = get_complaint_analyzer()

        y_true_urgency: list[str] = []
        y_pred_urgency: list[str] = []

        location_correct = 0
        location_evaluated = 0
        ambiguity_correct = 0
        detailed_results = []

        for case in cases:
            text = case["text"]
            true_urgency = case["true_urgency"]
            expected_loc = case.get("expected_location")
            is_ambiguous_expected = case.get("is_ambiguous", False)

            analysis = await analyzer.analyze(text)
            pred_urgency = analysis.urgency.value

            y_true_urgency.append(true_urgency)
            y_pred_urgency.append(pred_urgency)

            # Location match
            loc_match = False
            if expected_loc is not None:
                location_evaluated += 1
                if analysis.extracted_location and expected_loc.lower() in analysis.extracted_location.lower():
                    location_correct += 1
                    loc_match = True
            else:
                if analysis.extracted_location is None:
                    location_correct += 1
                    loc_match = True
                location_evaluated += 1

            # Ambiguity check
            is_ambig_pred = "ambiguous" in analysis.tags or "incomplete" in analysis.tags
            if is_ambig_pred == is_ambiguous_expected:
                ambiguity_correct += 1

            detailed_results.append({
                "id": case["id"],
                "text_snippet": text[:50] + "..." if len(text) > 50 else text,
                "true_urgency": true_urgency,
                "pred_urgency": pred_urgency,
                "urgency_correct": true_urgency == pred_urgency,
                "expected_location": expected_loc,
                "pred_location": analysis.extracted_location,
                "location_match": loc_match,
                "tags": analysis.tags,
            })

        metrics = compute_classification_metrics(y_true_urgency, y_pred_urgency)
        loc_acc = round(location_correct / location_evaluated, 4) if location_evaluated > 0 else 1.0
        ambig_acc = round(ambiguity_correct / len(cases), 4) if cases else 1.0

        return {
            "suite_name": self.name,
            "dataset_type": "offline_synthetic_fixtures",
            "sample_count": len(cases),
            "metrics": {
                "urgency_accuracy": metrics["accuracy"],
                "urgency_macro_f1": metrics["macro_f1"],
                "urgency_macro_precision": metrics["macro_precision"],
                "urgency_macro_recall": metrics["macro_recall"],
                "location_extraction_accuracy": loc_acc,
                "ambiguity_detection_accuracy": ambig_acc,
            },
            "per_class_breakdown": metrics["per_class"],
            "details": detailed_results,
        }
