"""Evaluation Engine for Exactly 10 Synthetic Library Acquisition Requests.

Processes the 10 test cases sequentially, tracks sequential budget deductions,
verifies against expected baseline outcomes, and calculates accuracy.
"""

import json
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

from memory.shared_memory import SharedMemoryService
from tools.budget_calculator import BudgetCalculator, to_decimal, INITIAL_BUDGET
from workflows.acquisition_workflow import AcquisitionWorkflow


def evaluate_single_request(
    workflow: AcquisitionWorkflow,
    test_case: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a single test case through the multi-agent workflow and evaluate result."""
    budget_before = str(workflow.calculator.get_remaining_budget())
    
    result = workflow.run({
        "request_id": test_case["request_id"],
        "book_title": test_case["book_title"],
        "requester": test_case["requester"],
        "price": test_case["price"],
        "category": test_case["category"]
    })
    
    actual_decision = result["decision"]
    expected_decision = test_case["expected_decision"]
    is_pass = (actual_decision == expected_decision)
    budget_after = result["remaining_budget"]

    return {
        "request_id": test_case["request_id"],
        "book_title": test_case["book_title"],
        "category": test_case["category"],
        "price": f"₹{test_case['price']}",
        "expected_decision": expected_decision,
        "actual_decision": actual_decision,
        "status": "PASS" if is_pass else "FAIL",
        "budget_before": f"₹{budget_before}",
        "budget_after": f"₹{budget_after}",
        "policy_clause": result.get("policy_clause", "N/A"),
        "demand_score": result.get("demand_score", 0.0),
        "demand_level": result.get("demand_level", "N/A"),
        "decision_reason": result.get("decision_reason", "")
    }


def run_evaluation(
    test_cases_file: str = None,
    reset_state: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run sequential evaluation of all 10 standard test cases."""
    if test_cases_file is None:
        test_cases_file = str(Path(__file__).resolve().parent / "test_cases.json")

    with open(test_cases_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # Initialize clean workflow and shared memory
    memory = SharedMemoryService()
    calculator = BudgetCalculator(initial_budget=INITIAL_BUDGET)
    if reset_state:
        memory.reset()
        calculator.reset()

    workflow = AcquisitionWorkflow(memory_service=memory, calculator=calculator)

    rows: List[Dict[str, Any]] = []
    correct_count = 0

    for case in cases:
        row = evaluate_single_request(workflow, case)
        if row["status"] == "PASS":
            correct_count += 1
        rows.append(row)

    df = pd.DataFrame(rows)
    total_cases = len(cases)
    accuracy = (correct_count / total_cases) * 100.0 if total_cases > 0 else 0.0

    total_expenditure = workflow.calculator.get_total_approved_expenditure()
    remaining_budget = workflow.calculator.get_remaining_budget()
    integrity = workflow.calculator.validate_budget_integrity()

    buy_count = sum(1 for r in rows if r["actual_decision"] == "BUY")
    defer_count = sum(1 for r in rows if r["actual_decision"] == "DEFER")
    reject_count = sum(1 for r in rows if r["actual_decision"] == "REJECT")

    summary = {
        "total_cases": total_cases,
        "passed_cases": correct_count,
        "failed_cases": total_cases - correct_count,
        "accuracy_percent": round(accuracy, 2),
        "buy_count": buy_count,
        "defer_count": defer_count,
        "reject_count": reject_count,
        "initial_budget": f"₹{INITIAL_BUDGET}",
        "total_approved_expenditure": f"₹{total_expenditure}",
        "final_remaining_budget": f"₹{remaining_budget}",
        "budget_integrity_valid": integrity["is_valid"],
        "expected_expenditure": "₹16800.00",
        "expected_remaining": "₹3200.00",
        "matches_ground_truth": (
            accuracy == 100.0
            and total_expenditure == Decimal("16800.00")
            and remaining_budget == Decimal("3200.00")
        )
    }

    return df, summary


if __name__ == "__main__":
    df, summary = run_evaluation()
    print("=" * 80)
    print("EVALUATION RESULTS (10 TEST CASES)")
    print("=" * 80)
    print(df[["request_id", "book_title", "price", "expected_decision", "actual_decision", "status", "budget_after"]].to_string(index=False))
    print("-" * 80)
    print(f"Accuracy: {summary['accuracy_percent']}% ({summary['passed_cases']}/{summary['total_cases']})")
    print(f"BUY: {summary['buy_count']}, DEFER: {summary['defer_count']}, REJECT: {summary['reject_count']}")
    print(f"Total Approved Expenditure: {summary['total_approved_expenditure']} (Expected: {summary['expected_expenditure']})")
    print(f"Final Remaining Budget: {summary['final_remaining_budget']} (Expected: {summary['expected_remaining']})")
    print(f"Matches Ground Truth: {summary['matches_ground_truth']}")
    print("=" * 80)
