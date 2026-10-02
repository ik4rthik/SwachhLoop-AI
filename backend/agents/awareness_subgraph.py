"""
SwachhLoop AI — Public Awareness & RAG Subgraph
===============================================
Specialized LangGraph workflow for retrieving civic waste management
guidance, handling multilingual English and Malayalam citizen queries,
and generating grounded civic awareness responses.
"""

from datetime import datetime, timezone
import logging
from langgraph.graph import StateGraph, START, END

from backend.agents.state import SwachhLoopState, AwarenessOutput
from backend.services.knowledge_service import get_knowledge_service

logger = logging.getLogger(__name__)


async def retrieve_knowledge_node(state: SwachhLoopState) -> dict:
    """Retrieve relevant civic knowledge articles based on citizen query."""
    audit = list(state.get("audit_trail") or [])
    query = state.get("query_text") or ""

    service = get_knowledge_service()
    retrieved = await service.retrieve(query, top_k=3)

    audit.append({
        "step_id": f"step_rag_retrieval_{len(audit)+1}",
        "node_name": "retrieve_knowledge_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "detail": f"Retrieved {len(retrieved)} knowledge articles for query: '{query[:50]}'",
    })

    return {
        "current_node": "retrieve_knowledge_node",
        "_retrieved_articles": retrieved,
        "audit_trail": audit,
    }


async def generate_response_node(state: SwachhLoopState) -> dict:
    """Generate grounded, language-specific civic response using retrieved articles."""
    audit = list(state.get("audit_trail") or [])
    query = state.get("query_text") or ""
    req_lang = state.get("language")

    service = get_knowledge_service()
    rag_resp = await service.answer_query(query, language=req_lang)

    output = AwarenessOutput(
        query=rag_resp.query,
        language=rag_resp.language,
        answer=rag_resp.answer,
        sources=rag_resp.source_articles,
        found=rag_resp.found_knowledge,
    )

    audit.append({
        "step_id": f"step_rag_generate_{len(audit)+1}",
        "node_name": "generate_response_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS" if rag_resp.found_knowledge else "REVIEW_REQUIRED",
        "detail": f"Generated answer in {rag_resp.language}. Found in KB: {rag_resp.found_knowledge}",
    })

    return {
        "current_node": "generate_response_node",
        "awareness_result": output.model_dump(),
        "requires_human_review": not rag_resp.found_knowledge,
        "review_reason": "Query not found in civic knowledge base; citizen may need direct staff guidance." if not rag_resp.found_knowledge else None,
        "status": "COMPLETED",
        "audit_trail": audit,
    }


def build_awareness_subgraph():
    """Build and compile the public awareness StateGraph."""
    workflow = StateGraph(SwachhLoopState)
    workflow.add_node("retrieve_knowledge", retrieve_knowledge_node)
    workflow.add_node("generate_response", generate_response_node)

    workflow.add_edge(START, "retrieve_knowledge")
    workflow.add_edge("retrieve_knowledge", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()
