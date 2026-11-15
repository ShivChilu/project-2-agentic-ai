"""Automated test verifying the 10-case evaluation against ground truth baseline."""

from decimal import Decimal
import pytest
from evaluation.evaluate import run_evaluation


def test_ten_case_evaluation_accuracy_and_budget():
    df, summary = run_evaluation(reset_state=True)

    # 1. Total count
    assert summary["total_cases"] == 10
    assert summary["passed_cases"] == 10
    assert summary["failed_cases"] == 0
    assert summary["accuracy_percent"] == 100.0

    # 2. Decision breakdown
    assert summary["buy_count"] == 5
    assert summary["defer_count"] == 3
    assert summary["reject_count"] == 2

    # 3. Financial calculations
    assert summary["total_approved_expenditure"] == "₹16800.00"
    assert summary["final_remaining_budget"] == "₹3200.00"
    assert summary["budget_integrity_valid"] is True
    assert summary["matches_ground_truth"] is True

    # 4. Sequential check: R08 must be deferred due to insufficient budget
    r08_row = df[df["request_id"] == "R08"].iloc[0]
    assert r08_row["actual_decision"] == "DEFER"
    assert r08_row["status"] == "PASS"

    # 5. R09 must be approved after R08
    r09_row = df[df["request_id"] == "R09"].iloc[0]
    assert r09_row["actual_decision"] == "BUY"
    assert r09_row["status"] == "PASS"
    assert r09_row["budget_after"] == "₹3200.00"
