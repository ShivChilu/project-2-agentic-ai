"""Unit tests for Policy Retrieval Agent and Local RAG."""

import pytest
from rag.retrieval import PolicyRetriever
from agents.policy_agent import PolicyRetrievalAgent
from memory.shared_memory import SharedMemoryService


@pytest.fixture
def retriever():
    return PolicyRetriever()


def test_relevant_policy_retrieval(retriever):
    result = retriever.retrieve(title="Artificial Intelligence", category="Computer Science")
    assert result.document_id == "POL-001"
    assert "CLAUSE-SCOPE" in result.policy_clause
    assert result.policy_status == "COMPLIANT"
    assert result.relevance_score > 0.12


def test_duplicate_policy_retrieval(retriever):
    result = retriever.retrieve(title="Existing Database Systems Duplicate", category="Computer Science")
    assert result.document_id == "POL-002"
    assert "CLAUSE-DUP" in result.policy_clause
    assert result.policy_status == "VIOLATION"


def test_out_of_scope_policy_violation(retriever):
    result = retriever.retrieve(title="Unrelated Cooking Collection", category="Culinary Arts")
    assert result.document_id == "POL-003"
    assert "CLAUSE-EXCL" in result.policy_clause
    assert result.policy_status == "VIOLATION"


def test_rare_reference_policy(retriever):
    result = retriever.retrieve(title="Rare Academic Reference", category="Reference & Archives")
    assert result.document_id == "POL-010"
    assert result.policy_clause == "CLAUSE-REF-10.1"
    assert result.policy_status == "RESTRICTED"


def test_low_confidence_retrieval(retriever):
    result = retriever.retrieve(title="Xylophone Zookeeper Wandering", category="Acrobatics")
    assert result.policy_status == "INSUFFICIENT_EVIDENCE"
    assert result.confidence == "LOW"


def test_policy_agent_records_to_memory(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    agent = PolicyRetrievalAgent(memory_service=memory)

    req = {
        "request_id": "REQ_POL_01",
        "book_title": "Cloud Computing",
        "category": "Infrastructure & Cloud",
        "price": "6000.00"
    }
    findings = agent.evaluate_policy(req)
    assert findings["policy_document_id"] == "POL-008"
    assert findings["policy_status"] == "COMPLIANT"
    assert memory.policy_findings["REQ_POL_01"]["policy_clause"] == "CLAUSE-CLOUD-8.1"
