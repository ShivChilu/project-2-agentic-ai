"""Agent 4: Budget Agent.

Responsibilities:
- Read the available library budget.
- Calculate whether the requested purchase is affordable.
- Use a separate arithmetic tool.
- Track approved expenditure.
- Check the current remaining budget.
- Prevent overspending.
- Store its budget assessment in shared memory.

The agent must NOT independently approve a purchase or deduct money before
the final BUY decision is validated by the Acquisitions Manager.
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from tools.budget_calculator import BudgetCalculator, to_decimal
from memory.shared_memory import SharedMemoryService
from .llm_client import llm_manager


class BudgetAgent:
    """Agent responsible for checking fund availability and affordability constraints."""

    def __init__(
        self,
        calculator: Optional[BudgetCalculator] = None,
        memory_service: Optional[SharedMemoryService] = None
    ):
        self.name = "Budget Agent"
        self.calculator = calculator or BudgetCalculator()
        self.memory_service = memory_service

    def evaluate_budget(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess purchase affordability without deducting funds."""
        title = request_data.get("book_title", "")
        raw_price = request_data.get("price", "0.00")
        request_id = request_data.get("request_id", "UNKNOWN")
        price = to_decimal(raw_price)

        # Get current balance from calculator if present, or memory
        if self.calculator:
            current_balance = self.calculator.get_remaining_budget()
        elif self.memory_service:
            current_balance = self.memory_service.get_remaining_budget()
        else:
            current_balance = INITIAL_BUDGET

        affordability = self.calculator.check_affordability(price, current_balance)
        affordable = affordability["affordable"]
        remaining_projected = affordability["projected_remaining"]
        deficit = affordability["deficit"]

        # Explanation
        if affordable:
            default_explanation = (
                f"Requested book cost of ₹{price} is fully affordable within available budget of ₹{current_balance}. "
                f"Projected remaining balance if approved: ₹{remaining_projected}."
            )
        else:
            default_explanation = (
                f"Requested book cost of ₹{price} exceeds available budget of ₹{current_balance} "
                f"by a deficit of ₹{deficit}. Insufficient funds for acquisition."
            )

        sys_prompt = (
            "You are a Library Financial Comptroller. Provide a concise 1-sentence statement on "
            "the fiscal affordability of this book purchase based solely on the provided figures."
        )
        user_prompt = (
            f"Book: '{title}'\n"
            f"Price: ₹{price}\n"
            f"Current Balance: ₹{current_balance}\n"
            f"Affordable: {affordable}\n"
            f"Projected Balance After Purchase: ₹{remaining_projected}\n"
            f"State fiscal status in 1 sentence."
        )

        explanation = llm_manager.generate_explanation(
            prompt=user_prompt,
            system_prompt=sys_prompt,
            fallback=default_explanation
        )

        findings = {
            "agent": self.name,
            "request_id": request_id,
            "requested_price": str(price),
            "current_balance": str(current_balance),
            "affordable": affordable,
            "projected_remaining": str(remaining_projected),
            "deficit": str(deficit),
            "explanation": explanation
        }

        # Store in shared memory
        if self.memory_service:
            self.memory_service.store_budget_findings(request_id, findings)

        return findings
