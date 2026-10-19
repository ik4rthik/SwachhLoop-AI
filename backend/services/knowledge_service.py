"""
SwachhLoop AI — Knowledge & Public Awareness Service (RAG)
==========================================================
Provides retrieval-augmented generation and guidance for civic waste
management queries, with bilingual English and Malayalam support
for Kalady Grama Panchayat.

Phase 5 Hardening:
  - Strict separation of retrieval and response generation.
  - Relevance score thresholding & explicit insufficient-context fallback.
  - Prompt-injection defense on queries and retrieved document text.
  - Grounding verification & context tracking to prevent hallucination.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import re

from backend.core.config import settings
from backend.core.guardrails import (
    validate_rag_query_input,
    sanitize_untrusted_text,
    evaluate_rag_groundedness,
)

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeArticle:
    id: str
    topic: str
    title_en: str
    title_ml: str
    content_en: str
    content_ml: str
    keywords: list[str] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class RAGResponse:
    query: str
    language: str  # "en" | "ml"
    answer: str
    source_articles: list[dict]
    found_knowledge: bool
    notes: str = ""
    grounding_score: float = 1.0


class KnowledgeRetrieverService(ABC):
    """Abstract interface for the RAG and civic knowledge retrieval service."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 3) -> list[KnowledgeArticle]:
        """Retrieve most relevant knowledge articles for a query."""
        raise NotImplementedError

    @abstractmethod
    async def generate_answer(
        self,
        query: str,
        retrieved: list[KnowledgeArticle],
        language: str | None = None,
    ) -> RAGResponse:
        """Generate a grounded public awareness answer using retrieved knowledge articles."""
        raise NotImplementedError

    @abstractmethod
    async def answer_query(self, query: str, language: str | None = None) -> RAGResponse:
        """End-to-end pipeline: retrieve relevant context then generate a grounded answer."""
        raise NotImplementedError


class LocalKnowledgeRetriever(KnowledgeRetrieverService):
    """
    Local file-based knowledge retriever using BM25-style keyword and
    token overlap matching across English and Malayalam text.
    """

    def __init__(self, knowledge_path: str = "data/knowledge_base.json"):
        self.knowledge_path = Path(knowledge_path)
        self.articles: list[KnowledgeArticle] = []
        self._load_knowledge()

    def _load_knowledge(self) -> None:
        if not self.knowledge_path.exists():
            logger.warning("Knowledge base file %s not found. RAG will report unconfigured.", self.knowledge_path)
            return

        try:
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.articles = [
                    KnowledgeArticle(
                        id=item.get("id", ""),
                        topic=item.get("topic", ""),
                        title_en=item.get("title_en", ""),
                        title_ml=item.get("title_ml", ""),
                        content_en=item.get("content_en", ""),
                        content_ml=item.get("content_ml", ""),
                        keywords=item.get("keywords", []),
                    )
                    for item in data
                ]
            logger.info("Loaded %d knowledge articles from %s", len(self.articles), self.knowledge_path)
        except Exception as err:
            logger.error("Failed to parse knowledge base: %s", err)
            self.articles = []

    def detect_language(self, text: str) -> str:
        """Detect whether text contains Malayalam script unicode range U+0D00 to U+0D7F."""
        if re.search(r"[\u0D00-\u0D7F]", text):
            return "ml"
        return "en"

    async def retrieve(self, query: str, top_k: int = 3) -> list[KnowledgeArticle]:
        if not self.articles or not query or not query.strip():
            return []

        # Validate input and sanitize
        validation = validate_rag_query_input(query)
        if "PROMPT_INJECTION_DETECTED" in validation.flags:
            logger.warning("RAG query contained prompt injection attempt: %s", validation.warning_or_error)
            return []

        clean_query = validation.sanitized_content if validation.is_valid else sanitize_untrusted_text(query)
        if not clean_query:
            return []

        civic_stopwords = {
            "kalady", "grama", "panchayat", "kerala", "how", "what", "where", "when",
            "which", "who", "why", "the", "and", "for", "with", "from", "near",
            "have", "has", "can", "should", "about", "your", "into", "apply", "does",
            "കാലടി", "ഗ്രാമ", "പഞ്ചായത്ത്", "എങ്ങനെ", "എവിടെ", "എന്ത്", "ആണ്"
        }

        lang = self.detect_language(clean_query)
        q_tokens = set(re.findall(r"[\w\u0D00-\u0D7F]+", clean_query.lower()))
        scored: list[tuple[float, KnowledgeArticle]] = []

        for art in self.articles:
            score = 0.0
            content = (art.content_ml if lang == "ml" else art.content_en).lower()
            title = (art.title_ml if lang == "ml" else art.title_en).lower()

            # Match against keywords
            for kw in art.keywords:
                if kw.lower() in clean_query.lower():
                    score += 2.5

            # Match specific, informative tokens
            for token in q_tokens:
                if len(token) > 2 and token not in civic_stopwords:
                    if token in title:
                        score += 3.0
                    elif token in content:
                        score += 1.0

            if score > 0.0:
                # Normalize score to [0.0, 1.0]
                norm_score = min(1.0, round(score / 10.0, 2))
                art_copy = KnowledgeArticle(
                    id=art.id,
                    topic=art.topic,
                    title_en=art.title_en,
                    title_ml=art.title_ml,
                    content_en=art.content_en,
                    content_ml=art.content_ml,
                    keywords=art.keywords,
                    relevance_score=norm_score,
                )
                scored.append((score, art_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    async def generate_answer(
        self,
        query: str,
        retrieved: list[KnowledgeArticle],
        language: str | None = None,
    ) -> RAGResponse:
        """
        Generate grounded response from retrieved articles, enforcing relevance thresholds
        and explicit fallback when insufficient context is available.
        """
        lang = language or self.detect_language(query)

        # Fallback messages
        not_found_ml = (
            "ക്ഷമിക്കണം, ഈ ചോദ്യത്തിനുള്ള ഔദ്യോഗിക വിവരങ്ങൾ പഞ്ചായത്ത് നോളഡ്ജ് ബേസിൽ ലഭ്യമല്ല. "
            "ദയവായി പഞ്ചായത്ത് ഓഫീസുമായി ബന്ധപ്പെടുക."
        )
        not_found_en = (
            "No matching civic guidance found in the Kalady municipal knowledge base for your inquiry. "
            "Please consult the Kalady Grama Panchayat Office."
        )

        if not retrieved:
            return RAGResponse(
                query=query,
                language=lang,
                answer=not_found_ml if lang == "ml" else not_found_en,
                source_articles=[],
                found_knowledge=False,
                notes="No articles matched query keywords.",
                grounding_score=0.0,
            )

        top_article = retrieved[0]
        # Check relevance threshold to avoid returning irrelevant snippets
        if top_article.relevance_score < settings.rag_relevance_threshold:
            return RAGResponse(
                query=query,
                language=lang,
                answer=not_found_ml if lang == "ml" else not_found_en,
                source_articles=[],
                found_knowledge=False,
                notes=f"Retrieved articles below relevance threshold ({top_article.relevance_score} < {settings.rag_relevance_threshold}).",
                grounding_score=0.0,
            )

        # Sanitize article content to neutralize any hostile prompt injection in external docs
        raw_answer = top_article.content_ml if lang == "ml" else top_article.content_en
        answer_text = sanitize_untrusted_text(raw_answer)

        sources = [
            {
                "id": a.id,
                "title": a.title_ml if lang == "ml" else a.title_en,
                "topic": a.topic,
                "relevance": a.relevance_score,
                "content": a.content_ml if lang == "ml" else a.content_en,
            }
            for a in retrieved
        ]

        # Verify grounding against retrieved sources
        is_grounded, grounding_score, g_note = evaluate_rag_groundedness(
            answer=answer_text,
            retrieved_sources=sources,
            language=lang,
        )

        return RAGResponse(
            query=query,
            language=lang,
            answer=answer_text,
            source_articles=sources,
            found_knowledge=True,
            notes=f"Retrieved from Kalady Grama Panchayat official knowledge base. {g_note}",
            grounding_score=grounding_score,
        )

    async def answer_query(self, query: str, language: str | None = None) -> RAGResponse:
        """Separable pipeline: retrieve first, then generate."""
        if not self.knowledge_path.exists() or not self.articles:
            return RAGResponse(
                query=query,
                language=language or "en",
                answer="Civic knowledge source is not configured or available for Kalady Panchayat.",
                source_articles=[],
                found_knowledge=False,
                notes="Knowledge base file is missing.",
                grounding_score=0.0,
            )

        retrieved = await self.retrieve(query, top_k=2)
        return await self.generate_answer(query, retrieved, language=language)


def get_knowledge_service() -> KnowledgeRetrieverService:
    """Factory to get the knowledge retriever service instance."""
    return LocalKnowledgeRetriever(knowledge_path=settings.rag_knowledge_path)
