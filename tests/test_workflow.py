"""Integration tests for Microsoft Agent Framework Acquisition Workflow."""

import pytest
from workflows.acquisition_workflow import AcquisitionWorkflow
from memory.shared_memory import SharedMemoryService
from tools.budget_calculator import BudgetCalculator, INITIAL_BUDGET
from agents.acquisition_manager import AcquisitionsManager


def test_complete_workflow_buy_decision(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    calc = BudgetCalculator(initial_budget=INITIAL_BUDGET)
    workflow = AcquisitionWorkflow(memory_service=memory, calculator=calc)

    req = {
        "request_id": "WF_TEST_BUY",
        "book_title": "Artificial Intelligence",
        "requester": "CSE Dept",
        "price": 2500.0,
        "category": "Computer Science"
    }

    result = workflow.run(req)

    assert result["decision"] == "BUY"
    assert result["policy_clause"] == "CLAUSE-SCOPE-1.1"
    assert result["demand_level"] == "HIGH"
    assert result["remaining_budget"] == "17500.00"
    assert memory.get_remaining_budget() == calc.get_remaining_budget()


def test_complete_workflow_reject_duplicate(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    calc = BudgetCalculator(initial_budget=INITIAL_BUDGET)
    workflow = AcquisitionWorkflow(memory_service=memory, calculator=calc)

    req = {
        "request_id": "WF_TEST_DUP",
        "book_title": "Existing Database Systems Duplicate",
        "requester": "Student Council",
        "price": 2200.0,
        "category": "Computer Science"
    }

    result = workflow.run(req)

    assert result["decision"] == "REJECT"
    assert "CLAUSE-DUP" in result["policy_clause"]
    # Verify budget unchanged
    assert result["remaining_budget"] == "20000.00"


def test_complete_workflow_defer_budget(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    # Give small budget of ₹5000
    calc = BudgetCalculator(initial_budget=INITIAL_BUDGET)
    calc.deduct_purchase("PREV", "Existing Spending", "15000.00")
    workflow = AcquisitionWorkflow(memory_service=memory, calculator=calc)

    # Book costs 7000 but only 5000 remains
    req = {
        "request_id": "WF_TEST_ROBO",
        "book_title": "Robotics Research",
        "requester": "Robotics Club",
        "price": 7000.0,
        "category": "Robotics & Automation"
    }

    result = workflow.run(req)

    assert result["decision"] == "DEFER"
    assert "CLAUSE-BUD" in result["policy_clause"]
    # No deduction for DEFER
    assert result["remaining_budget"] == "5000.00"


def test_missing_or_failed_specialist_yields_defer(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    calc = BudgetCalculator()
    manager = AcquisitionsManager(memory_service=memory, calculator=calc)

    # Pass None for policy findings
    res = manager.make_decision(
        request_data={"request_id": "ERR01", "book_title": "AI Book", "price": "2500.00"},
        policy_findings=None,
        demand_findings={"demand_level": "HIGH", "demand_score": 85.0},
        budget_findings={"affordable": True}
    )

    assert res["decision"] == "DEFER"
    assert "incomplete" in res["decision_reason"].lower()
    # Ensure money was not deducted
    assert calc.get_remaining_budget() == INITIAL_BUDGET
