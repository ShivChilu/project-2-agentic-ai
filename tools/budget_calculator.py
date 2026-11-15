"""Budget Calculator Tool.

Enforces financial integrity using Python Decimal for all monetary operations.
Prevents duplicate deductions, ensures non-negative balances, and recalculates
independent budget audits directly from approved transaction logs.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Set

INITIAL_BUDGET: Decimal = Decimal("20000.00")
TWO_PLACES: Decimal = Decimal("0.01")


def to_decimal(val: Any) -> Decimal:
    """Safely convert numerical or string input to Decimal with 2 decimal places."""
    if isinstance(val, Decimal):
        return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    try:
        clean_str = str(val).replace("₹", "").replace(",", "").strip()
        return Decimal(clean_str).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    except Exception as exc:
        raise ValueError(f"Invalid monetary value: {val}") from exc


class BudgetCalculator:
    """Manages acquisition fund balances and transactional deductions."""
    
    def __init__(self, initial_budget: Optional[Decimal] = None):
        self.initial_budget = to_decimal(initial_budget if initial_budget is not None else INITIAL_BUDGET)
        self.approved_purchases: List[Dict[str, Any]] = []
        self._approved_request_ids: Set[str] = set()
        
    def check_affordability(self, price: Any, current_balance: Optional[Decimal] = None) -> Dict[str, Any]:
        """Check whether the requested price can be afforded by the remaining budget."""
        dec_price = to_decimal(price)
        if current_balance is None:
            current_balance = self.get_remaining_budget()
        else:
            current_balance = to_decimal(current_balance)
            
        affordable = (dec_price <= current_balance) and (dec_price > Decimal("0.00"))
        remaining_after = current_balance - dec_price if affordable else current_balance
        
        return {
            "requested_price": str(dec_price),
            "current_balance": str(current_balance),
            "affordable": affordable,
            "projected_remaining": str(remaining_after),
            "deficit": str(max(Decimal("0.00"), dec_price - current_balance))
        }

    def deduct_purchase(self, request_id: str, title: str, price: Any) -> Dict[str, Any]:
        """Deduct an approved BUY purchase exactly once.
        
        Raises ValueError if funds are insufficient or if duplicate deduction is attempted.
        """
        dec_price = to_decimal(price)
        current_balance = self.get_remaining_budget()
        
        if request_id in self._approved_request_ids:
            return {
                "success": False,
                "already_approved": True,
                "request_id": request_id,
                "remaining_budget": str(current_balance),
                "message": f"Purchase for request {request_id} has already been deducted."
            }
            
        if dec_price > current_balance:
            raise ValueError(
                f"Cannot approve purchase: Price {dec_price} exceeds available budget {current_balance}."
            )
            
        self._approved_request_ids.add(request_id)
        record = {
            "request_id": request_id,
            "book_title": title,
            "price": str(dec_price),
            "balance_before": str(current_balance),
            "balance_after": str(current_balance - dec_price)
        }
        self.approved_purchases.append(record)
        
        return {
            "success": True,
            "already_approved": False,
            "request_id": request_id,
            "deducted_amount": str(dec_price),
            "remaining_budget": str(self.get_remaining_budget()),
            "record": record
        }

    def get_total_approved_expenditure(self) -> Decimal:
        """Calculate total expenditure by summing all approved transactions."""
        total = Decimal("0.00")
        for item in self.approved_purchases:
            total += to_decimal(item["price"])
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    def get_remaining_budget(self) -> Decimal:
        """Calculate remaining budget: Initial Budget - Total Approved Expenditure."""
        spent = self.get_total_approved_expenditure()
        remaining = self.initial_budget - spent
        return max(Decimal("0.00"), remaining).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    def validate_budget_integrity(self) -> Dict[str, Any]:
        """Independent mathematical audit verifying that budget state is correct and non-negative."""
        spent = self.get_total_approved_expenditure()
        calc_remaining = self.initial_budget - spent
        actual_remaining = self.get_remaining_budget()
        
        is_valid = (calc_remaining >= Decimal("0.00")) and (calc_remaining == actual_remaining)
        return {
            "initial_budget": str(self.initial_budget),
            "total_expenditure": str(spent),
            "remaining_budget": str(actual_remaining),
            "is_valid": is_valid,
            "transaction_count": len(self.approved_purchases)
        }

    def reset(self) -> None:
        """Reset budget tracker to initial state."""
        self.approved_purchases.clear()
        self._approved_request_ids.clear()
