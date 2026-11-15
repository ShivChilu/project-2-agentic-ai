"""Microsoft Agent Framework Acquisition Workflow.

Implements genuine multi-agent orchestration with fan-out to independent specialist
executors and fan-in synchronization before the Acquisitions Manager decision.

Graph Topology:
                 [ IntakeWorkflowExecutor ]
                             | (fan-out)
            +----------------+----------------+
            |                |                |
            v                v                v
     [ PolicyExecutor ] [ DemandExecutor ] [ BudgetExecutor ]
            |                |                |
            +----------------+----------------+
                             | (fan-in)
                             v
                 [ ManagerWorkflowExecutor ]
"""

import asyncio
import time
from typing import Dict, Any, List, Optional

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

from agents.intake_agent import RequestIntakeAgent
from agents.policy_agent import PolicyRetrievalAgent
from agents.demand_agent import DemandAgent
from agents.budget_agent import BudgetAgent
from agents.acquisition_manager import AcquisitionsManager
from memory.shared_memory import SharedMemoryService
from tools.budget_calculator import BudgetCalculator


class IntakeWorkflowExecutor(Executor):
    """Workflow executor for Request Intake Agent."""

    def __init__(self, agent: RequestIntakeAgent, id: str = "intake_executor"):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def handle_request(self, raw_input: Dict[str, Any], ctx: WorkflowContext[Dict[str, Any]]) -> None:
        """Validate input request and broadcast structured payload to specialists."""
        validated = self.agent.process_request(raw_input)
        await ctx.send_message(validated)


class PolicyWorkflowExecutor(Executor):
    """Workflow executor for Policy Retrieval Agent."""

    def __init__(self, agent: PolicyRetrievalAgent, id: str = "policy_executor"):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def handle_policy(self, request_data: Dict[str, Any], ctx: WorkflowContext[Dict[str, Any]]) -> None:
        """Retrieve applicable policies via RAG and send findings."""
        findings = self.agent.evaluate_policy(request_data)
        await ctx.send_message({
            "agent_type": "policy",
            "findings": findings,
            "request_data": request_data
        })


class DemandWorkflowExecutor(Executor):
    """Workflow executor for Demand Agent."""

    def __init__(self, agent: DemandAgent, id: str = "demand_executor"):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def handle_demand(self, request_data: Dict[str, Any], ctx: WorkflowContext[Dict[str, Any]]) -> None:
        """Evaluate reader demand statistics and send findings."""
        findings = self.agent.evaluate_demand(request_data)
        await ctx.send_message({
            "agent_type": "demand",
            "findings": findings,
            "request_data": request_data
        })


class BudgetWorkflowExecutor(Executor):
    """Workflow executor for Budget Agent."""

    def __init__(self, agent: BudgetAgent, id: str = "budget_executor"):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def handle_budget(self, request_data: Dict[str, Any], ctx: WorkflowContext[Dict[str, Any]]) -> None:
        """Evaluate affordability and send findings."""
        findings = self.agent.evaluate_budget(request_data)
        await ctx.send_message({
            "agent_type": "budget",
            "findings": findings,
            "request_data": request_data
        })


class ManagerWorkflowExecutor(Executor):
    """Workflow executor for Acquisitions Manager (Fan-In point)."""

    def __init__(self, manager: AcquisitionsManager, id: str = "manager_executor"):
        super().__init__(id=id)
        self.manager = manager

    @handler
    async def handle_fan_in(self, specialist_results: List[Dict[str, Any]], ctx: WorkflowContext) -> None:
        """Aggregate specialist findings after fan-in barrier and decide outcome."""
        policy_res = None
        demand_res = None
        budget_res = None
        request_data = None

        for item in specialist_results:
            atype = item.get("agent_type")
            if atype == "policy":
                policy_res = item.get("findings")
                request_data = item.get("request_data")
            elif atype == "demand":
                demand_res = item.get("findings")
                if not request_data:
                    request_data = item.get("request_data")
            elif atype == "budget":
                budget_res = item.get("findings")
                if not request_data:
                    request_data = item.get("request_data")

        if not request_data:
            request_data = {"request_id": "UNKNOWN", "book_title": "Unknown Book", "price": "0.00"}

        # Execute manager decision logic
        final_record = self.manager.make_decision(
            request_data=request_data,
            policy_findings=policy_res,
            demand_findings=demand_res,
            budget_findings=budget_res
        )

        # Output final result from the workflow
        await ctx.yield_output(final_record)


def build_acquisition_workflow(
    intake_agent: RequestIntakeAgent,
    policy_agent: PolicyRetrievalAgent,
    demand_agent: DemandAgent,
    budget_agent: BudgetAgent,
    manager_agent: AcquisitionsManager
):
    """Assemble Microsoft Agent Framework workflow graph using WorkflowBuilder."""
    intake_exec = IntakeWorkflowExecutor(intake_agent, id="intake")
    policy_exec = PolicyWorkflowExecutor(policy_agent, id="policy")
    demand_exec = DemandWorkflowExecutor(demand_agent, id="demand")
    budget_exec = BudgetWorkflowExecutor(budget_agent, id="budget")
    manager_exec = ManagerWorkflowExecutor(manager_agent, id="manager")

    workflow = (
        WorkflowBuilder(start_executor=intake_exec)
        # 1. Fan-out: Intake broadcasts validated request to all 3 specialists concurrently
        .add_fan_out_edges(intake_exec, [policy_exec, demand_exec, budget_exec])
        # 2. Fan-in: Manager waits until all 3 specialist executors have finished
        .add_fan_in_edges([policy_exec, demand_exec, budget_exec], manager_exec)
        .build()
    )

    return workflow, {
        "intake": intake_exec,
        "policy": policy_exec,
        "demand": demand_exec,
        "budget": budget_exec,
        "manager": manager_exec
    }


class AcquisitionWorkflow:
    """High-level system orchestrator combining all 5 agents and shared memory."""

    def __init__(
        self,
        memory_service: Optional[SharedMemoryService] = None,
        calculator: Optional[BudgetCalculator] = None
    ):
        self.memory = memory_service or SharedMemoryService()
        self.calculator = calculator or BudgetCalculator()
        
        # Instantiate 5 agents
        self.intake_agent = RequestIntakeAgent(memory_service=self.memory)
        self.policy_agent = PolicyRetrievalAgent(memory_service=self.memory)
        self.demand_agent = DemandAgent(memory_service=self.memory)
        self.budget_agent = BudgetAgent(calculator=self.calculator, memory_service=self.memory)
        self.manager_agent = AcquisitionsManager(memory_service=self.memory, calculator=self.calculator)

        # Build Microsoft Agent Framework Workflow
        self.workflow, self.executors = build_acquisition_workflow(
            intake_agent=self.intake_agent,
            policy_agent=self.policy_agent,
            demand_agent=self.demand_agent,
            budget_agent=self.budget_agent,
            manager_agent=self.manager_agent
        )

    async def run_async(self, raw_request: Dict[str, Any]) -> Dict[str, Any]:
        """Run workflow asynchronously."""
        start_time = time.time()
        run_res = await self.workflow.run(raw_request)
        outputs = run_res.get_outputs()
        elapsed = round(time.time() - start_time, 3)

        if outputs:
            final_record = outputs[0]
            final_record["execution_time_seconds"] = elapsed
            return final_record

        raise RuntimeError("Workflow failed: No output yielded by Acquisitions Manager.")

    def run(self, raw_request: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for notebooks, Streamlit, and scripts."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, self.run_async(raw_request)).result()
