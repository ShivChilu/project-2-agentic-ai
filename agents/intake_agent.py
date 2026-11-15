"""Agent 1: Request Intake Agent.

Responsibilities:
- Accept a book request.
- Extract and validate book title.
- Identify the requester.
- Extract requested book price.
- Accept an optional subject or category.
- Validate required fields.
- Reject invalid or incomplete requests.
- Generate a unique request ID.
- Produce a structured request object.
- Store the validated request in shared memory.
"""

from decimal import Decimal
from typing import Dict, Any, Optional
import uuid

from memory.shared_memory import SharedMemoryService
from tools.budget_calculator import to_decimal


class RequestIntakeAgent:
    """Agent responsible for parsing, validating, and registering book requests."""

    def __init__(self, memory_service: Optional[SharedMemoryService] = None):
        self.name = "Request Intake Agent"
        self.memory_service = memory_service

    def process_request(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input fields and produce structured request object."""
        if not isinstance(raw_input, dict):
            raise ValueError("Invalid request format: input must be a dictionary.")

        # 1. Validate Book Title
        title = str(raw_input.get("book_title") or raw_input.get("title") or "").strip()
        if not title:
            raise ValueError("Validation failed: Book title is mandatory and cannot be empty.")

        # 2. Validate Requester
        requester = str(raw_input.get("requester") or "").strip()
        if not requester:
            raise ValueError("Validation failed: Requester name or department is mandatory.")

        # 3. Validate Price
        raw_price = raw_input.get("price")
        if raw_price is None:
            raise ValueError("Validation failed: Price is mandatory.")
        try:
            price = to_decimal(raw_price)
        except Exception as exc:
            raise ValueError(f"Validation failed: Invalid price value '{raw_price}'.") from exc

        if price <= Decimal("0.00"):
            raise ValueError("Validation failed: Price must be greater than zero.")

        # 4. Optional Category
        category = str(raw_input.get("category") or "General").strip()

        # 5. Request ID
        request_id = str(raw_input.get("request_id") or f"REQ-{uuid.uuid4().hex[:6].upper()}").strip()

        # Structured output
        validated_request = {
            "request_id": request_id,
            "book_title": title,
            "requester": requester,
            "price": str(price),
            "category": category,
            "status": "VALIDATED"
        }

        # Store in shared memory
        if self.memory_service:
            self.memory_service.store_validated_request(validated_request)

        return validated_request
