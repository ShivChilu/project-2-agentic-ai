"""Shared Memory Service for Multi-Agent Collaboration.

Provides a thread-safe, persistent application-level blackboard memory where all five
agents record their findings, execution traces, budget state, and final decisions.
"""

import json
import threading
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Optional

from tools.budget_calculator import to_decimal, INITIAL_BUDGET


class SharedMemoryService:
    """Thread-safe persistent shared memory blackboard."""

    def __init__(self, persistence_path: Optional[str] = None, initial_budget: Optional[Decimal] = None):
        self._lock = threading.RLock()
        
        if persistence_path is None:
            persistence_path = str(Path(__file__).resolve().parent.parent / "data" / "memory_state.json")
        self.persistence_path = Path(persistence_path)
        
        self.initial_budget = to_decimal(initial_budget if initial_budget is not None else INITIAL_BUDGET)
        
        # State containers
        self.validated_requests: Dict[str, Dict[str, Any]] = {}
        self.policy_findings: Dict[str, Dict[str, Any]] = {}
        self.demand_findings: Dict[str, Dict[str, Any]] = {}
        self.budget_findings: Dict[str, Dict[str, Any]] = {}
        self.final_decisions: List[Dict[str, Any]] = []
        self.approved_purchases: List[Dict[str, Any]] = []
        self.agent_execution_logs: List[Dict[str, Any]] = []
        
        # Try loading existing persistent memory if present
        if self.persistence_path.exists():
            try:
                self.load_from_disk()
            except Exception:
                # If corrupt, initialize fresh
                self.save_to_disk()
        else:
            self.save_to_disk()

    def store_validated_request(self, request_data: Dict[str, Any]) -> None:
        """Store validated request from Request Intake Agent."""
        with self._lock:
            req_id = request_data["request_id"]
            self.validated_requests[req_id] = request_data
            self._log_agent_action("Request Intake Agent", req_id, "VALIDATED", request_data)
            self.save_to_disk()

    def store_policy_findings(self, request_id: str, findings: Dict[str, Any]) -> None:
        """Store findings from Collection Policy Retrieval Agent."""
        with self._lock:
            self.policy_findings[request_id] = findings
            self._log_agent_action("Collection Policy Retrieval Agent", request_id, findings.get("policy_status", "PROCESSED"), findings)
            self.save_to_disk()

    def store_demand_findings(self, request_id: str, findings: Dict[str, Any]) -> None:
        """Store findings from Demand Agent."""
        with self._lock:
            self.demand_findings[request_id] = findings
            self._log_agent_action("Demand Agent", request_id, findings.get("demand_level", "PROCESSED"), findings)
            self.save_to_disk()

    def store_budget_findings(self, request_id: str, findings: Dict[str, Any]) -> None:
        """Store findings from Budget Agent."""
        with self._lock:
            self.budget_findings[request_id] = findings
            status = "AFFORDABLE" if findings.get("affordable") else "UNAVAILABLE"
            self._log_agent_action("Budget Agent", request_id, status, findings)
            self.save_to_disk()

    def store_final_decision(self, decision: Dict[str, Any]) -> None:
        """Store final decision from Acquisitions Manager."""
        with self._lock:
            req_id = decision["request_id"]
            
            # Avoid duplicate final decision records for same request ID
            self.final_decisions = [d for d in self.final_decisions if d.get("request_id") != req_id]
            self.final_decisions.append(decision)
            
            # If decision is BUY, record approved purchase
            if decision.get("decision") == "BUY":
                if not any(p.get("request_id") == req_id for p in self.approved_purchases):
                    self.approved_purchases.append({
                        "request_id": req_id,
                        "book_title": decision.get("book_title", ""),
                        "price": str(to_decimal(decision.get("price", "0.00"))),
                        "decision_reason": decision.get("decision_reason", "")
                    })
                    
            self._log_agent_action("Acquisitions Manager", req_id, decision.get("decision", "DECIDED"), decision)
            self.save_to_disk()

    def get_remaining_budget(self) -> Decimal:
        """Calculate current remaining budget from approved purchases."""
        with self._lock:
            spent = Decimal("0.00")
            for p in self.approved_purchases:
                spent += to_decimal(p["price"])
            remaining = self.initial_budget - spent
            return max(Decimal("0.00"), remaining)

    def get_total_approved_expenditure(self) -> Decimal:
        """Calculate total money spent on approved BUY decisions."""
        with self._lock:
            spent = Decimal("0.00")
            for p in self.approved_purchases:
                spent += to_decimal(p["price"])
            return spent

    def get_context_for_manager(self, request_id: str) -> Dict[str, Any]:
        """Retrieve aggregated findings for Acquisitions Manager review."""
        with self._lock:
            return {
                "request": self.validated_requests.get(request_id),
                "policy": self.policy_findings.get(request_id),
                "demand": self.demand_findings.get(request_id),
                "budget": self.budget_findings.get(request_id),
                "current_remaining_budget": str(self.get_remaining_budget())
            }

    def _log_agent_action(self, agent_name: str, request_id: str, status: str, details: Dict[str, Any]) -> None:
        """Record structured trace entry."""
        self.agent_execution_logs.append({
            "agent_name": agent_name,
            "request_id": request_id,
            "status": status,
            "details": details
        })

    def reset(self) -> None:
        """Reset all memory states back to initial clean state."""
        with self._lock:
            self.validated_requests.clear()
            self.policy_findings.clear()
            self.demand_findings.clear()
            self.budget_findings.clear()
            self.final_decisions.clear()
            self.approved_purchases.clear()
            self.agent_execution_logs.clear()
            self.save_to_disk()

    def save_to_disk(self) -> None:
        """Persist state to JSON file."""
        with self._lock:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "initial_budget": str(self.initial_budget),
                "remaining_budget": str(self.get_remaining_budget()),
                "total_expenditure": str(self.get_total_approved_expenditure()),
                "validated_requests": self.validated_requests,
                "policy_findings": self.policy_findings,
                "demand_findings": self.demand_findings,
                "budget_findings": self.budget_findings,
                "final_decisions": self.final_decisions,
                "approved_purchases": self.approved_purchases,
                "agent_execution_logs": self.agent_execution_logs[-100:]  # keep recent 100
            }
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def load_from_disk(self) -> None:
        """Load state from persistent JSON file."""
        with self._lock:
            if not self.persistence_path.exists():
                return
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.initial_budget = to_decimal(data.get("initial_budget", INITIAL_BUDGET))
            self.validated_requests = data.get("validated_requests", {})
            self.policy_findings = data.get("policy_findings", {})
            self.demand_findings = data.get("demand_findings", {})
            self.budget_findings = data.get("budget_findings", {})
            self.final_decisions = data.get("final_decisions", [])
            self.approved_purchases = data.get("approved_purchases", [])
            self.agent_execution_logs = data.get("agent_execution_logs", [])
