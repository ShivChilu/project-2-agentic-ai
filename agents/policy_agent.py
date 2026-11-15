"""Agent 2: Collection Policy Retrieval Agent.

Responsibilities:
- Retrieve relevant acquisition policies using RAG.
- Search the local policy document collection.
- Identify relevant policy clauses.
- Check academic relevance and collection scope.
- Identify duplicate restrictions.
- Return supporting evidence and document references.
- Identify policy violations.
- Report insufficient evidence when retrieval confidence is low.
- Store its findings in shared memory.
"""

from typing import Dict, Any, Optional
from rag.retrieval import PolicyRetriever, RetrievalResult
from memory.shared_memory import SharedMemoryService
from .llm_client import llm_manager


class PolicyRetrievalAgent:
    """Agent responsible for checking library acquisition policies via Local RAG."""

    def __init__(
        self,
        retriever: Optional[PolicyRetriever] = None,
        memory_service: Optional[SharedMemoryService] = None
    ):
        self.name = "Collection Policy Retrieval Agent"
        self.retriever = retriever or PolicyRetriever()
        self.memory_service = memory_service

    def evaluate_policy(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve applicable policy clauses and assess compliance."""
        title = request_data.get("book_title", "")
        category = request_data.get("category", "")
        price = float(request_data.get("price", 0.0))
        request_id = request_data.get("request_id", "UNKNOWN")

        # 1. RAG Retrieval from local corpus
        retrieval: RetrievalResult = self.retriever.retrieve(title=title, category=category, price=price)

        # 2. Synthesize grounded explanation
        sys_prompt = (
            "You are a Senior Library Policy Officer. State clearly how the retrieved policy clause "
            "applies to this book acquisition request. Do not hallucinate or invent rules not in the policy."
        )
        user_prompt = (
            f"Book Request: '{title}' (Category: {category}, Price: ₹{price})\n"
            f"Retrieved Policy: {retrieval.document_title} ({retrieval.document_id})\n"
            f"Policy Clause: {retrieval.policy_clause}\n"
            f"Retrieved Explanation: {retrieval.explanation}\n"
            f"Status: {retrieval.policy_status}\n"
            f"Provide a concise 1-sentence regulatory policy assessment."
        )
        
        explanation = llm_manager.generate_explanation(
            prompt=user_prompt,
            system_prompt=sys_prompt,
            fallback=retrieval.explanation
        )

        findings = {
            "agent": self.name,
            "request_id": request_id,
            "policy_document_id": retrieval.document_id,
            "policy_document_title": retrieval.document_title,
            "policy_clause": retrieval.policy_clause,
            "relevance_score": retrieval.relevance_score,
            "policy_status": retrieval.policy_status,
            "retrieval_confidence": retrieval.confidence,
            "evidence": retrieval.explanation,
            "explanation": explanation
        }

        # Store in shared memory
        if self.memory_service:
            self.memory_service.store_policy_findings(request_id, findings)

        return findings
