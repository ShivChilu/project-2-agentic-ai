"""Agent 5: Acquisitions Manager.

Responsibilities:
- Coordinate the specialist agents.
- Receive results from Policy, Demand, and Budget agents.
- Read relevant findings from shared memory.
- Compare policy, demand, and budget results.
- Make the final BUY, DEFER, or REJECT decision following strict deterministic precedence.
- Deduct approved purchases from the budget tracker.
- Store the final validated decision in shared memory.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from memory.shared_memory import SharedMemoryService
from tools.budget_calculator import BudgetCalculator, to_decimal
from .llm_client import llm_manager


class AcquisitionsManager:
    """Acquisitions Committee Chair and Final Decision Authority."""

    def __init__(
        self,
        memory_service: Optional[SharedMemoryService] = None,
        calculator: Optional[BudgetCalculator] = None
    ):
        self.name = "Acquisitions Manager"
        self.memory_service = memory_service
        self.calculator = calculator or BudgetCalculator()

    def make_decision(
        self,
        request_data: Dict[str, Any],
        policy_findings: Optional[Dict[str, Any]],
        demand_findings: Optional[Dict[str, Any]],
        budget_findings: Optional[Dict[str, Any]],
        faculty_override: Optional[str] = None  # Add-on support: "APPROVE", "REJECT"
    ) -> Dict[str, Any]:
        """Apply deterministic decision rules over specialist agent findings."""
        request_id = request_data.get("request_id", "UNKNOWN")
        book_title = request_data.get("book_title", "")
        requester = request_data.get("requester", "")
        price = to_decimal(request_data.get("price", "0.00"))

        current_balance = (
            self.calculator.get_remaining_budget()
            if self.calculator
            else (self.memory_service.get_remaining_budget() if self.memory_service else to_decimal("20000.00"))
        )
        balance_before = current_balance

        # -------------------------------------------------------------
        # 1. Deterministic Decision Precedence Evaluation
        # -------------------------------------------------------------
        decision: str = "DEFER"
        reason: str = ""
        clause: str = "CLAUSE-NONE"

        # Check for missing specialist results
        if not policy_findings or not demand_findings or not budget_findings:
            decision = "DEFER"
            reason = "Specialist findings incomplete or unavailable; acquisition deferred for committee retry."
            clause = "CLAUSE-EXEC-4.0"

        # Precedence Rule 1, 2, 3: Confirmed Policy Violation / Duplicate / Out of Scope
        elif policy_findings.get("policy_status") == "VIOLATION":
            decision = "REJECT"
            clause = policy_findings.get("policy_clause", "CLAUSE-DUP-2.1")
            reason = (
                f"Policy violation detected ({clause}): {policy_findings.get('evidence', '')} "
                f"Title rejected per collection development guidelines."
            )

        # Precedence Rule 4 & 5: Inconclusive / Insufficient Policy Evidence
        elif policy_findings.get("policy_status") == "INSUFFICIENT_EVIDENCE":
            decision = "DEFER"
            clause = "CLAUSE-SCOPE-1.1"
            reason = "Policy retrieval returned insufficient evidence; deferred for faculty collection review."

        # Precedence Rule 6: Demand Below HIGH Threshold (< 70.0)
        elif demand_findings.get("demand_level") != "HIGH":
            decision = "DEFER"
            clause = policy_findings.get("policy_clause", "CLAUSE-DEM-4.1")
            score = demand_findings.get("demand_score", 0.0)
            level = demand_findings.get("demand_level", "LOW")
            reason = (
                f"Demand score ({score}/100, {level}) does not meet the mandatory HIGH demand threshold (>= 70.0). "
                f"Deferred for demand monitoring."
            )

        # Precedence Rule 7: Insufficient Remaining Budget
        elif not budget_findings.get("affordable", False) or price > current_balance:
            decision = "DEFER"
            clause = "CLAUSE-BUD-5.1"
            reason = (
                f"Sufficient demand exists, but book price (₹{price}) exceeds available remaining budget (₹{current_balance}). "
                f"Deferred pending fund replenishment."
            )

        # Precedence Rule 8: All Purchase Conditions Met -> BUY!
        else:
            decision = "BUY"
            clause = policy_findings.get("policy_clause", "CLAUSE-SCOPE-1.1")
            reason = (
                f"Compliant with {clause}, verified HIGH demand ({demand_findings.get('demand_score')}/100), "
                f"and fully affordable within remaining budget."
            )

        # Optional Faculty Recommendation Add-on Path
        if faculty_override:
            if faculty_override.upper() == "APPROVE" and decision == "DEFER" and price <= current_balance:
                decision = "BUY"
                reason = f"[Faculty Committee Approval]: {reason} Overridden by verified human faculty sponsorship."
            elif faculty_override.upper() == "REJECT":
                decision = "REJECT"
                reason = f"[Faculty Committee Rejection]: Overridden by faculty committee review."

        # -------------------------------------------------------------
        # 2. Financial Update: Deduct ONLY if validated BUY
        # -------------------------------------------------------------
        balance_after = balance_before
        if decision == "BUY":
            # Deduct once in calculator
            deduction = self.calculator.deduct_purchase(request_id, book_title, price)
            balance_after = self.calculator.get_remaining_budget()
            if self.memory_service:
                # Synchronize calculator state with memory
                balance_after = balance_before - price

        # -------------------------------------------------------------
        # 3. LLM Articulation (Structured Grounded Explanation)
        # -------------------------------------------------------------
        sys_prompt = (
            "You are the Library Acquisitions Committee Chair. State the final acquisition decision "
            "(BUY, DEFER, or REJECT), the supporting policy clause, and the concise reason."
        )
        user_prompt = (
            f"Decision: {decision}\n"
            f"Book Title: '{book_title}' (Requester: {requester}, Price: ₹{price})\n"
            f"Policy Clause: {clause}\n"
            f"Policy Finding: {policy_findings.get('policy_status') if policy_findings else 'N/A'}\n"
            f"Demand Score: {demand_findings.get('demand_score') if demand_findings else 'N/A'} ({demand_findings.get('demand_level') if demand_findings else 'N/A'})\n"
            f"Budget Before: ₹{balance_before}, After: ₹{balance_after}\n"
            f"Reason: {reason}\n"
            f"Summarize final decision in 1-2 professional sentences."
        )

        executive_summary = llm_manager.generate_explanation(
            prompt=user_prompt,
            system_prompt=sys_prompt,
            fallback=reason
        )

        final_record = {
            "request_id": request_id,
            "book_title": book_title,
            "requester": requester,
            "price": str(price),
            "policy_status": policy_findings.get("policy_status") if policy_findings else "MISSING",
            "policy_clause": clause,
            "policy_document_id": policy_findings.get("policy_document_id") if policy_findings else "NONE",
            "policy_evidence": policy_findings.get("evidence") if policy_findings else "",
            "demand_score": demand_findings.get("demand_score") if demand_findings else 0.0,
            "demand_level": demand_findings.get("demand_level") if demand_findings else "NONE",
            "demand_evidence": demand_findings.get("evidence") if demand_findings else "",
            "budget_available": str(balance_before),
            "decision": decision,
            "decision_reason": reason,
            "executive_summary": executive_summary,
            "remaining_budget": str(balance_after)
        }

        # Store in shared memory
        if self.memory_service:
            self.memory_service.store_final_decision(final_record)

        return final_record
