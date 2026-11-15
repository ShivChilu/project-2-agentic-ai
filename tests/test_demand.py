"""Unit tests for Demand Agent and Demand Statistics Tool."""

import pytest
from tools.demand_statistics import (
    calculate_demand_score,
    classify_demand,
    lookup_circulation_history,
    MAX_CHECKOUTS,
    MAX_RESERVATIONS
)
from agents.demand_agent import DemandAgent
from memory.shared_memory import SharedMemoryService


def test_demand_score_formula():
    # 90 checkouts -> 90.0, 27 reservations -> 27/30*100 = 90.0
    # 90 * 0.7 + 90 * 0.3 = 90.0
    score = calculate_demand_score(90, 27)
    assert score == 90.0

    # 50 checkouts -> 50.0, 15 reservations -> 15/30*100 = 50.0
    # 50 * 0.7 + 50 * 0.3 = 50.0
    score = calculate_demand_score(50, 15)
    assert score == 50.0

    # Capped at 100
    score_over = calculate_demand_score(150, 45)
    assert score_over == 100.0


def test_demand_classification_thresholds():
    assert classify_demand(85.0) == "HIGH"
    assert classify_demand(70.0) == "HIGH"
    assert classify_demand(69.9) == "MEDIUM"
    assert classify_demand(40.0) == "MEDIUM"
    assert classify_demand(39.9) == "LOW"
    assert classify_demand(10.0) == "LOW"


def test_circulation_lookup_found():
    data = lookup_circulation_history("Artificial Intelligence")
    assert data is not None
    assert data["checkouts"] == 90
    assert data["reservations"] == 27
    assert data["demand_score"] == 90.0
    assert data["demand_level"] == "HIGH"


def test_circulation_lookup_missing():
    data = lookup_circulation_history("NonExistentUnrecordedBook12345")
    assert data is None


def test_demand_agent_with_existing_book():
    agent = DemandAgent()
    req = {
        "request_id": "REQ_DEM_01",
        "book_title": "Data Structures",
        "category": "Computer Science"
    }
    findings = agent.evaluate_demand(req)
    assert findings["demand_level"] == "HIGH"
    assert findings["demand_score"] >= 70.0
    assert findings["data_status"] == "VERIFIED"


def test_demand_agent_with_missing_book(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    agent = DemandAgent(memory_service=memory)

    req = {
        "request_id": "REQ_DEM_UNKNOWN",
        "book_title": "Mystery Title Never Published",
        "category": "Obscure"
    }
    findings = agent.evaluate_demand(req)
    assert findings["data_status"] == "INSUFFICIENT_DATA"
    assert findings["demand_level"] == "LOW"
    assert memory.demand_findings["REQ_DEM_UNKNOWN"]["data_status"] == "INSUFFICIENT_DATA"
