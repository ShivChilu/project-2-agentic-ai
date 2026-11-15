"""Unit tests for Budget Agent and Budget Calculator."""

from decimal import Decimal
import pytest
from tools.budget_calculator import BudgetCalculator, to_decimal, INITIAL_BUDGET
from agents.budget_agent import BudgetAgent
from agents.acquisition_manager import AcquisitionsManager
from memory.shared_memory import SharedMemoryService


def test_initial_budget_is_20000():
    calc = BudgetCalculator()
    assert calc.get_remaining_budget() == Decimal("20000.00")
    assert calc.get_total_approved_expenditure() == Decimal("0.00")


def test_affordable_purchase_check():
    calc = BudgetCalculator()
    agent = BudgetAgent(calculator=calc)
    res = agent.evaluate_budget({"book_title": "AI Book", "price": "2500.00"})
    assert res["affordable"] is True
    assert res["projected_remaining"] == "17500.00"
    # Verify NO deduction occurred during affordability check
    assert calc.get_remaining_budget() == Decimal("20000.00")


def test_insufficient_budget():
    calc = BudgetCalculator()
    agent = BudgetAgent(calculator=calc)
    res = agent.evaluate_budget({"book_title": "Super Rare Collection", "price": "25000.00"})
    assert res["affordable"] is False
    assert res["deficit"] == "5000.00"


def test_sequential_deductions_and_exact_budget():
    calc = BudgetCalculator(initial_budget=Decimal("5000.00"))
    
    # First purchase: 3000
    r1 = calc.deduct_purchase("REQ1", "Book A", "3000.00")
    assert r1["success"] is True
    assert calc.get_remaining_budget() == Decimal("2000.00")

    # Second purchase: 2000 (exact remaining budget)
    r2 = calc.deduct_purchase("REQ2", "Book B", "2000.00")
    assert r2["success"] is True
    assert calc.get_remaining_budget() == Decimal("0.00")

    # Third purchase: should fail because budget is 0
    with pytest.raises(ValueError, match="exceeds available budget"):
        calc.deduct_purchase("REQ3", "Book C", "100.00")


def test_prevent_duplicate_deductions():
    calc = BudgetCalculator()
    calc.deduct_purchase("REQ1", "AI Book", "2500.00")
    assert calc.get_remaining_budget() == Decimal("17500.00")

    # Second attempt with same request ID
    res = calc.deduct_purchase("REQ1", "AI Book", "2500.00")
    assert res["already_approved"] is True
    assert res["success"] is False
    # Budget must not be deducted twice
    assert calc.get_remaining_budget() == Decimal("17500.00")


def test_no_deduction_for_defer_or_reject(tmp_path):
    mem_path = tmp_path / "test_mem.json"
    memory = SharedMemoryService(persistence_path=str(mem_path))
    calc = BudgetCalculator()
    manager = AcquisitionsManager(memory_service=memory, calculator=calc)

    # 1. DEFER request
    manager.make_decision(
        request_data={"request_id": "DEF01", "book_title": "Niche Book", "price": "3000.00"},
        policy_findings={"policy_status": "COMPLIANT", "policy_clause": "CLAUSE-SCOPE-1.1"},
        demand_findings={"demand_level": "LOW", "demand_score": 20.0},
        budget_findings={"affordable": True}
    )
    assert calc.get_remaining_budget() == Decimal("20000.00")

    # 2. REJECT request
    manager.make_decision(
        request_data={"request_id": "REJ01", "book_title": "Duplicate Book", "price": "2200.00"},
        policy_findings={"policy_status": "VIOLATION", "policy_clause": "CLAUSE-DUP-2.1"},
        demand_findings={"demand_level": "HIGH", "demand_score": 85.0},
        budget_findings={"affordable": True}
    )
    assert calc.get_remaining_budget() == Decimal("20000.00")


def test_prevent_negative_remaining_budget():
    calc = BudgetCalculator(initial_budget=Decimal("1000.00"))
    with pytest.raises(ValueError):
        calc.deduct_purchase("REQ_OVER", "Expensive Book", "1001.00")
    assert calc.get_remaining_budget() == Decimal("1000.00")
