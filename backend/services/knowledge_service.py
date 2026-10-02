"""
SwachhLoop AI — Knowledge & Public Awareness Service (RAG)
==========================================================
Provides retrieval-augmented generation and guidance for civic waste
management queries, with bilingual English and Malayalam support
for Kalady Grama Panchayat.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import re

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


class KnowledgeRetrieverService(ABC):
    """Abstract interface for the RAG and civic knowledge retrieval service."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 3) -> list[KnowledgeArticle]:
        """Retrieve most relevant knowledge articles for a query."""
        raise NotImplementedError

    @abstractmethod
    async def answer_query(self, query: str, language: str | None = None) -> RAGResponse:
        """Generate a grounded public awareness answer using retrieved knowledge."""
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
        if not self.articles or not query.strip():
            return []

        lang = self.detect_language(query)
        q_tokens = set(re.findall(r"[\w\u0D00-\u0D7F]+", query.lower()))
        scored: list[tuple[float, KnowledgeArticle]] = []

        for art in self.articles:
            score = 0.0
            content = (art.content_ml if lang == "ml" else art.content_en).lower()
            title = (art.title_ml if lang == "ml" else art.title_en).lower()

            # Match against keywords
            for kw in art.keywords:
                if kw.lower() in query.lower():
                    score += 2.5

            # Match individual tokens
            for token in q_tokens:
                if len(token) > 2:
                    if token in title:
                        score += 3.0
                    elif token in content:
                        score += 1.0

            if score > 0.0:
                # Normalize score
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

    async def answer_query(self, query: str, language: str | None = None) -> RAGResponse:
        if not self.knowledge_path.exists() or not self.articles:
            return RAGResponse(
                query=query,
                language=language or "en",
                answer="Civic knowledge source is not configured or available for Kalady Panchayat.",
                source_articles=[],
                found_knowledge=False,
                notes="Knowledge base file is missing.",
            )

        lang = language or self.detect_language(query)
        retrieved = await self.retrieve(query, top_k=2)

        if not retrieved:
            fallback_msg = (
                "ക്ഷമിക്കണം, ഈ ചോദ്യത്തിനുള്ള ഔദ്യോഗിക വിവരങ്ങൾ പഞ്ചായത്ത് നോളഡ്ജ് ബേസിൽ ലഭ്യമല്ല. ദയവായി പഞ്ചായത്ത് ഓഫീസുമായി ബന്ധപ്പെടുക."
                if lang == "ml"
                else "No matching civic guidance found in the Kalady municipal knowledge base for your inquiry. Please consult the Kalady Grama Panchayat Office."
            )
            return RAGResponse(
                query=query,
                language=lang,
                answer=fallback_msg,
                source_articles=[],
                found_knowledge=False,
                notes="No articles matched query keywords.",
            )

        top_article = retrieved[0]
        answer_text = top_article.content_ml if lang == "ml" else top_article.content_en

        sources = [
            {
                "id": a.id,
                "title": a.title_ml if lang == "ml" else a.title_en,
                "topic": a.topic,
                "relevance": a.relevance_score,
            }
            for a in retrieved
        ]

        return RAGResponse(
            query=query,
            language=lang,
            answer=answer_text,
            source_articles=sources,
            found_knowledge=True,
            notes="Retrieved from Kalady Grama Panchayat official knowledge base.",
        )


def get_knowledge_service() -> KnowledgeRetrieverService:
    """Factory to get the knowledge retriever service instance."""
    from backend.core.config import settings
    return LocalKnowledgeRetriever(knowledge_path=settings.rag_knowledge_path)
