"""
SwachhLoop AI — Civic RAG Knowledge Service Evaluator
=====================================================
Evaluates bilingual (EN/ML) knowledge retrieval, answer groundedness,
citation accuracy, and fallback on out-of-domain / adversarial queries.
"""

import json
from pathlib import Path
from typing import Any

from backend.services.knowledge_service import get_knowledge_service
from evaluations.evaluators.base import BaseEvaluator
from evaluations.metrics import compute_rag_evaluation_metrics


class RAGEvaluator(BaseEvaluator):
    def __init__(self, dataset_path: str = "evaluations/datasets/rag_eval.json"):
        self.dataset_path = Path(dataset_path)

    @property
    def name(self) -> str:
        return "Civic Knowledge RAG Grounding & Relevance Evaluation"

    async def evaluate(self) -> dict[str, Any]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        service = get_knowledge_service()
        records: list[dict[str, Any]] = []

        for case in cases:
            query = case["query"]
            lang = case.get("language")
            is_in_domain = case.get("is_in_domain", True)
            expected_art_id = case.get("expected_article_id")

            resp = await service.answer_query(query, language=lang)
            retrieved_ids = [s.get("id") for s in resp.source_articles]

            top_relevance = resp.source_articles[0].get("relevance", 0.0) if resp.source_articles else 0.0

            records.append({
                "id": case["id"],
                "query": query,
                "language": resp.language,
                "is_in_domain": is_in_domain,
                "found_knowledge": resp.found_knowledge,
                "expected_article_id": expected_art_id,
                "retrieved_article_ids": retrieved_ids,
                "relevance_score": top_relevance,
                "grounding_score": getattr(resp, "grounding_score", 1.0),
                "answer_snippet": resp.answer[:60] + "..." if len(resp.answer) > 60 else resp.answer,
            })

        metrics = compute_rag_evaluation_metrics(records)

        return {
            "suite_name": self.name,
            "dataset_type": "offline_synthetic_fixtures",
            "sample_count": len(cases),
            "metrics": metrics,
            "details": records,
        }
