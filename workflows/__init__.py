"""Workflows package for Microsoft Agent Framework Orchestration."""
from .acquisition_workflow import (
    AcquisitionWorkflow,
    IntakeWorkflowExecutor,
    PolicyWorkflowExecutor,
    DemandWorkflowExecutor,
    BudgetWorkflowExecutor,
    ManagerWorkflowExecutor,
    build_acquisition_workflow
)

__all__ = [
    "AcquisitionWorkflow",
    "IntakeWorkflowExecutor",
    "PolicyWorkflowExecutor",
    "DemandWorkflowExecutor",
    "BudgetWorkflowExecutor",
    "ManagerWorkflowExecutor",
    "build_acquisition_workflow",
]
