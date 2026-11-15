"""Unit tests for Request Intake Agent."""

import pytest
from agents.intake_agent import RequestIntakeAgent
from memory.shared_memory import SharedMemoryService


def test_valid_request():
    agent = RequestIntakeAgent()
    req = {
        "request_id": "REQ001",
        "book_title": "Artificial Intelligence",
        "requester": "CSE Department",
        "price": 2500,
        "category": "Computer Science"
    }
    result = agent.process_request(req)
    assert result["request_id"] == "REQ001"
    assert result["book_title"] == "Artificial Intelligence"
    assert result["requester"] == "CSE Department"
    assert result["price"] == "2500.00"
    assert result["status"] == "VALIDATED"


def test_missing_title():
    agent = RequestIntakeAgent()
    req = {
        "requester": "CSE Department",
        "price": 2500
    }
    with pytest.raises(ValueError, match="Book title is mandatory"):
        agent.process_request(req)


def test_empty_title():
    agent = RequestIntakeAgent()
    req = {
        "book_title": "   ",
        "requester": "CSE Department",
        "price": 2500
    }
    with pytest.raises(ValueError, match="Book title is mandatory"):
        agent.process_request(req)


def test_missing_requester():
    agent = RequestIntakeAgent()
    req = {
        "book_title": "Algorithms",
        "price": 2500
    }
    with pytest.raises(ValueError, match="Requester name or department is mandatory"):
        agent.process_request(req)


def test_invalid_price_zero_or_negative():
    agent = RequestIntakeAgent()
    req = {
        "book_title": "Algorithms",
        "requester": "Faculty",
        "price": 0
    }
    with pytest.raises(ValueError, match="Price must be greater than zero"):
        agent.process_request(req)

    req["price"] = -500
    with pytest.raises(ValueError, match="Price must be greater than zero"):
        agent.process_request(req)


def test_invalid_price_format():
    agent = RequestIntakeAgent()
    req = {
        "book_title": "Algorithms",
        "requester": "Faculty",
        "price": "not-a-number"
    }
    with pytest.raises(ValueError, match="Invalid price value"):
        agent.process_request(req)


def test_intake_stores_in_shared_memory(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    agent = RequestIntakeAgent(memory_service=memory)
    
    req = {
        "request_id": "TEST_REQ_99",
        "book_title": "Quantum Computing",
        "requester": "Physics Dept",
        "price": 3200
    }
    agent.process_request(req)
    
    stored = memory.validated_requests.get("TEST_REQ_99")
    assert stored is not None
    assert stored["book_title"] == "Quantum Computing"
    assert stored["status"] == "VALIDATED"
