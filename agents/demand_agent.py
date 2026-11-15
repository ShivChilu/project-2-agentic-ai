"""Agent 3: Demand Agent.

Responsibilities:
- Evaluate book demand using synthetic circulation history.
- Read relevant circulation-history information.
- Use a separate statistics tool to calculate demand.
- Determine demand score and demand level.
- Provide supporting historical evidence.
- Explain the demand assessment.
- Store its findings in shared memory.
"""

from typing import Dict, Any, Optional
from tools.demand_statistics import (
    calculate_demand_score,
    classify_demand,
    lookup_circulation_history
)
from memory.shared_memory import SharedMemoryService
from .llm_client import llm_manager


class DemandAgent:
    """Agent responsible for assessing reader and course demand based on circulation records."""

    def __init__(
        self,
        circulation_csv: Optional[str] = None,
        memory_service: Optional[SharedMemoryService] = None
    ):
        self.name = "Demand Agent"
        self.circulation_csv = circulation_csv
        self.memory_service = memory_service

    def evaluate_demand(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute demand metrics from circulation statistics."""
        title = request_data.get("book_title", "")
        category = request_data.get("category", "")
        request_id = request_data.get("request_id", "UNKNOWN")

        # 1. Lookup in synthetic circulation records
        circ_data = lookup_circulation_history(
            title=title,
            category=category,
            csv_path=self.circulation_csv
        )

        if not circ_data:
            # Handle unknown or missing historical data safely
            findings = {
                "agent": self.name,
                "request_id": request_id,
                "demand_score": 0.0,
                "demand_level": "LOW",
                "checkouts": 0,
                "reservations": 0,
                "evidence": "No historical circulation or reservation records found in library catalog.",
                "data_status": "INSUFFICIENT_DATA",
                "explanation": "Insufficient circulation data to verify patron demand."
            }
            if self.memory_service:
                self.memory_service.store_demand_findings(request_id, findings)
            return findings

        checkouts = circ_data["checkouts"]
        reservations = circ_data["reservations"]
        score = circ_data["demand_score"]
        level = circ_data["demand_level"]
        notes = circ_data["evidence_notes"]

        # 2. Generate grounded explanation
        sys_prompt = (
            "You are a Library Circulation Analyst. Summarize reader demand for a requested book "
            "based strictly on provided checkout and reservation figures. Do not fabricate figures."
        )
        user_prompt = (
            f"Book: '{title}' (Category: {category})\n"
            f"Checkouts: {checkouts}/100, Reservations: {reservations}/30\n"
            f"Calculated Score: {score}/100, Level: {level}\n"
            f"Historical Evidence: {notes}\n"
            f"Summarize patron demand in one concise sentence."
        )

        default_explanation = (
            f"Calculated Demand Score is {score}/100 ({level}) based on {checkouts} historical checkouts "
            f"and {reservations} active reservations. {notes}"
        )

        explanation = llm_manager.generate_explanation(
            prompt=user_prompt,
            system_prompt=sys_prompt,
            fallback=default_explanation
        )

        findings = {
            "agent": self.name,
            "request_id": request_id,
            "demand_score": score,
            "demand_level": level,
            "checkouts": checkouts,
            "reservations": reservations,
            "evidence": notes,
            "data_status": "VERIFIED",
            "explanation": explanation
        }

        # Store in shared memory
        if self.memory_service:
            self.memory_service.store_demand_findings(request_id, findings)

        return findings
