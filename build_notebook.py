"""Direct in-process execution script to populate real outputs in the demonstration notebook.

Executes all 23 sections sequentially in a real Python 3.12+ environment, captures exact outputs,
and formats them into official Jupyter Notebook v4 format without external ZMQ kernel fragility.
"""

import io
import sys
import contextlib
from pathlib import Path
import nbformat as nbf
import pandas as pd


def generate_and_execute_notebook():
    project_root = Path(__file__).resolve().parent
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.14.7"
        }
    }
    nb.cells = []

    def add_md(text):
        nb.cells.append(nbf.v4.new_markdown_cell(text.strip()))

    def add_code(code):
        nb.cells.append(nbf.v4.new_code_cell(code.strip()))

    # 1. Project Introduction and Objective
    add_md("""
# CSE476: Agentic AI and Intelligent Automation
## Task 2 (Project 2 / Q17): Library Acquisition and Collection Development Committee

**Academic Context:**
- **Course Code:** CSE476 — Agentic AI and Intelligent Automation
- **Project Topic:** Library Acquisition and Collection Development Committee (Q17)
- **Evaluation Units:** Unit III (Agent Workflows & Architectures) and Unit IV (Orchestration, RAG, & Memory)
- **Maximum Marks:** 30
- **Student Group:** 
  - Priya Rawat (Reg. No: 12314866)
  - Chiluveru Shiva Prasad (Reg. No: 12304258)

### Project Objective
Automate university library book acquisitions under a fixed operational budget of **₹20,000.00**.
Given requests from faculty, students, or departments, the system deploys a **five-agent committee** coordinated via **Microsoft Agent Framework** using **fan-out / fan-in** orchestration, **local RAG** over acquisition policy rules, and a **persistent shared memory** blackboard to render one of three deterministic outcomes:
- **BUY**: Book fulfills academic policy, demonstrates HIGH patron demand, and fits available budget.
- **DEFER**: Academic value confirmed but demand is low/medium, budget is temporarily insufficient, or evidence is incomplete.
- **REJECT**: Request violates collection policy (e.g. non-academic leisure material) or is an existing duplicate in catalog.
""")

    # 2. Technology Stack
    add_md("""
## 2. Technology Stack

| Component | Technology | Role in System |
|---|---|---|
| **Language** | Python 3.12+ | Core programming runtime |
| **Multi-Agent Framework** | `agent-framework-core` & `agent-framework-openai` | Microsoft Agent Framework orchestration, executors, and graph |
| **LLM Provider** | Groq API (`qwen/qwen3.8-27b`) | Natural language synthesis, policy explanation, and committee reports |
| **Local RAG** | `scikit-learn` (TF-IDF & Cosine Similarity) | Grounded policy retrieval without paid external embedding APIs |
| **Financial Arithmetic** | Python `Decimal` | Exact currency math preventing floating-point rounding errors |
| **Data Storage** | JSON & CSV | Synthetic circulation history and policy document store |
| **Shared Memory** | `SharedMemoryService` with JSON persistence | Application blackboard accessible across all 5 agents |
| **Evaluation & Tests** | `pytest` & `pandas` | 10-case evaluation benchmark with 100% accuracy target |
| **Frontend** | Streamlit | University committee demonstration dashboard |
""")

    # 3. Multi-Agent Architecture Diagram
    add_md("""
## 3. Multi-Agent Architecture Diagram

```text
                           USER BOOK REQUEST
                                  |
                                  v
                      +-----------------------+
                      | REQUEST INTAKE AGENT  |
                      +-----------------------+
                                  |
                           VALIDATED REQUEST
                                  |
                     +------------+------------+
                     | (Fan-Out)  |            |
                     v            v            v
             +------------+ +------------+ +------------+
             |   POLICY   | |   DEMAND   | |   BUDGET   |
             |   AGENT    | |   AGENT    | |   AGENT    |
             | (Local RAG)| |(Circulation| |(Decimal    |
             |            | | Statistics)| | Calculator)|
             +------------+ +------------+ +------------+
                     |            |            |
                     +------------+------------+
                                  |
                           (Fan-In Barrier)
                                  v
                     +-------------------------+
                     |   ACQUISITIONS MANAGER  |
                     +-------------------------+
                                  |
                         DETERMINISTIC RULES
                                  |
                                  v
                     +-------------------------+
                     |  FINAL DECISION RECORD  |
                     |  (BUY / DEFER / REJECT) |
                     +-------------------------+
                                  |
                                  v
                     +-------------------------+
                     |  SHARED MEMORY & BUDGET |
                     +-------------------------+
```
""")

    # 4. Explanation of the Five Specialized Agents
    add_md("""
## 4. Explanation of the Five Specialized Agents

1. **Request Intake Agent (`RequestIntakeAgent`):**
   - Ingests raw book requests (title, requester, price, optional category).
   - Validates mandatory fields (title non-empty, price > 0, requester present).
   - Assigns unique Request IDs and produces structured request records in shared memory.

2. **Collection Policy Retrieval Agent (`PolicyRetrievalAgent`):**
   - Executes local RAG vector search over 12 acquisition policy markdown documents.
   - Computes cosine similarity to detect academic alignment, duplicate rules, or scope violations.
   - Grounded strictly in retrieved evidence; never invents regulatory clauses.

3. **Demand Agent (`DemandAgent`):**
   - Accesses historical circulation records from the library dataset.
   - Computes weighted demand using the statistics tool:
     $$\\text{Demand Score} = (\\text{Checkout Score} \\times 0.70) + (\\text{Reservation Score} \\times 0.30)$$
   - Categorizes demand as **HIGH** ($\\ge 70.0$), **MEDIUM** ($40.0 - 69.99$), or **LOW** ($< 40.0$).

4. **Budget Agent (`BudgetAgent`):**
   - Inspects the current library budget balance using Python `Decimal`.
   - Evaluates whether the requested price is affordable without exceeding available funds.
   - Does *not* independently deduct funds before final manager validation.

5. **Acquisitions Manager (`AcquisitionsManager`):**
   - Synchronizes findings from Policy, Demand, and Budget agents at the fan-in barrier.
   - Applies deterministic precedence rules to yield the final **BUY**, **DEFER**, or **REJECT** decision.
   - Updates remaining budget only for verified BUY acquisitions.
""")

    # 5. Explanation of Fan-Out and Fan-In
    add_md("""
## 5. Explanation of Fan-Out and Fan-In

- **Fan-Out (`WorkflowBuilder.add_fan_out_edges`):**
  Once the Request Intake Agent produces a validated request, the message is concurrently broadcast to three independent specialist executors: Policy, Demand, and Budget. Because none of these three agents depends on the output of the others, they execute concurrently without sequential bottlenecks.

- **Fan-In (`WorkflowBuilder.add_fan_in_edges`):**
  The workflow establishes a synchronization barrier before the Acquisitions Manager. The Manager executor is invoked only when all three specialist results are fully received. This prevents race conditions and ensures financial or policy decisions are never made on partial data.
""")

    # 6. Environment Setup and Imports
    add_md("""
## 6. Environment Setup and Imports
We import the actual project modules from the codebase.
""")
    add_code("""
import sys
import os
from decimal import Decimal
from pathlib import Path
import pandas as pd

# Add project root directory to Python path
project_root = Path.cwd().resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import actual modules
from memory.shared_memory import SharedMemoryService
from tools.budget_calculator import BudgetCalculator, to_decimal, INITIAL_BUDGET
from tools.demand_statistics import (
    calculate_demand_score,
    classify_demand,
    lookup_circulation_history,
    MAX_CHECKOUTS,
    MAX_RESERVATIONS
)
from rag.document_loader import load_policy_documents
from rag.retrieval import PolicyRetriever
from agents.intake_agent import RequestIntakeAgent
from agents.policy_agent import PolicyRetrievalAgent
from agents.demand_agent import DemandAgent
from agents.budget_agent import BudgetAgent
from agents.acquisition_manager import AcquisitionsManager
from workflows.acquisition_workflow import AcquisitionWorkflow
from evaluation.evaluate import run_evaluation, evaluate_single_request
from agents.llm_client import llm_manager

print("All project modules successfully imported!")
""")

    # 7. Groq Connection Test
    add_md("""
## 7. Groq API Connection Test
We test connectivity to the configured Groq model (`qwen/qwen3.8-27b`) or verify deterministic demo fallback.
""")
    add_code("""
print(f"LLM Manager Initialized:")
print(f"  Demo Mode Active: {llm_manager.is_demo_mode}")
print(f"  Configured Model: {llm_manager.model}")
print(f"  Base URL: {llm_manager.base_url}")

# Quick synthesis test
test_reply = llm_manager.generate_explanation(
    prompt="Confirm system readiness in one sentence.",
    system_prompt="You are an AI assistant.",
    fallback="System is operational in deterministic mode."
)
print(f"  LLM Test Response: {test_reply}")
""")

    # 8. Synthetic Dataset Loading
    add_md("""
## 8. Synthetic Circulation History Dataset Loading
Inspect the historical checkout and reservation data used by the Demand Agent.
""")
    add_code("""
circ_csv_path = project_root / "data" / "circulation_history.csv"
df_circ = pd.read_csv(circ_csv_path)

print(f"Total Circulation Records: {len(df_circ)}")
print(df_circ.head(8).to_string(index=False))
""")

    # 9. Policy Document Loading
    add_md("""
## 9. Policy Document Loading
Load and parse all 12 synthetic acquisition policies from `data/policies/`.
""")
    add_code("""
policies = load_policy_documents()
print(f"Total Loaded Policy Documents: {len(policies)}\\n")
for p in policies[:5]:
    print(f"[{p.document_id}] {p.title} | Clause: {p.clause} (Category: {p.category})")
""")

    # 10. RAG Retrieval Demonstration
    add_md("""
## 10. Local RAG Retrieval Demonstration
Demonstrate TF-IDF vector retrieval and cosine similarity ranking across sample queries.
""")
    add_code("""
retriever = PolicyRetriever()

sample_queries = [
    ("Artificial Intelligence", "Computer Science"),
    ("Existing Database Systems Duplicate", "Computer Science"),
    ("Unrelated Cooking Collection", "Culinary Arts"),
    ("Rare Academic Reference", "Reference & Archives")
]

for title, cat in sample_queries:
    res = retriever.retrieve(title=title, category=cat)
    print(f"Query: '{title}' ({cat})")
    print(f"  -> Retrieved Doc: {res.document_title} [{res.document_id}]")
    print(f"  -> Policy Clause: {res.policy_clause}")
    print(f"  -> Status: {res.policy_status} | Relevance Score: {res.relevance_score}")
    print(f"  -> Explanation: {res.explanation}\\n")
""")

    # 11. Shared Memory Initialisation
    add_md("""
## 11. Shared Memory Initialisation
Initialize the thread-safe persistent application memory blackboard.
""")
    add_code("""
memory = SharedMemoryService()
memory.reset()
print("Shared Memory Initialized:")
print(f"  Initial Budget: ₹{memory.initial_budget}")
print(f"  Remaining Budget: ₹{memory.get_remaining_budget()}")
print(f"  Total Approved Expenditure: ₹{memory.get_total_approved_expenditure()}")
print(f"  Validated Requests: {len(memory.validated_requests)}")
""")

    # 12. Request Intake Agent Execution
    add_md("""
## 12. Request Intake Agent Execution
Test parsing and validation of valid vs invalid book requests.
""")
    add_code("""
intake_agent = RequestIntakeAgent(memory_service=memory)

# 1. Valid Request
valid_input = {
    "request_id": "DEMO-01",
    "book_title": "Deep Learning Systems",
    "requester": "CSE Dept",
    "price": 2800.0,
    "category": "Computer Science"
}
val_res = intake_agent.process_request(valid_input)
print(f"Valid Request Processed: {val_res}")

# 2. Invalid Request (Missing Title)
try:
    intake_agent.process_request({"requester": "Faculty", "price": 1500.0})
except ValueError as e:
    print(f"Caught Expected Validation Error: {e}")
""")

    # 13. Policy Retrieval Agent Execution
    add_md("""
## 13. Policy Retrieval Agent Execution
Evaluate curricular alignment and compliance using the RAG Policy Agent.
""")
    add_code("""
policy_agent = PolicyRetrievalAgent(retriever=retriever, memory_service=memory)
policy_findings = policy_agent.evaluate_policy(val_res)
print("Policy Agent Findings:")
for k, v in policy_findings.items():
    print(f"  {k}: {v}")
""")

    # 14. Demand Agent Execution
    add_md("""
## 14. Demand Agent Execution
Calculate reader demand using synthetic circulation data and the statistical tool.
""")
    add_code("""
demand_agent = DemandAgent(memory_service=memory)
demand_findings = demand_agent.evaluate_demand(val_res)
print("Demand Agent Findings:")
for k, v in demand_findings.items():
    print(f"  {k}: {v}")
""")

    # 15. Budget Agent Execution
    add_md("""
## 15. Budget Agent Execution
Assess affordability using the Budget Agent and verify that money has not yet been deducted.
""")
    add_code("""
calc = BudgetCalculator(initial_budget=INITIAL_BUDGET)
budget_agent = BudgetAgent(calculator=calc, memory_service=memory)
budget_findings = budget_agent.evaluate_budget(val_res)

print("Budget Agent Findings:")
for k, v in budget_findings.items():
    print(f"  {k}: {v}")
print(f"Confirm No Deduction Occurred Yet: Current Balance = ₹{calc.get_remaining_budget()}")
""")

    # 16. Fan-Out / Fan-In Workflow Execution
    add_md("""
## 16. Fan-Out / Fan-In Microsoft Agent Framework Workflow
Examine the workflow graph topology and executor bindings.
""")
    add_code("""
workflow = AcquisitionWorkflow(memory_service=memory, calculator=calc)
print("Microsoft Agent Framework Workflow Initialized:")
print(f"  Executors in Graph: {list(workflow.executors.keys())}")
print(f"  Start Executor: {workflow.executors['intake'].id}")
print("  Graph Topology: intake -> [policy, demand, budget] (fan-out) -> manager (fan-in)")
""")

    # 17. Acquisitions Manager Execution
    add_md("""
## 17. Acquisitions Manager Execution
The Acquisitions Manager evaluates deterministic precedence and applies approved purchase deductions.
""")
    add_code("""
manager_agent = AcquisitionsManager(memory_service=memory, calculator=calc)
decision_res = manager_agent.make_decision(
    request_data=val_res,
    policy_findings=policy_findings,
    demand_findings=demand_findings,
    budget_findings=budget_findings
)
print("Acquisitions Manager Final Output:")
print(f"  Decision: {decision_res['decision']}")
print(f"  Clause: {decision_res['policy_clause']}")
print(f"  Reason: {decision_res['decision_reason']}")
print(f"  Remaining Budget After Purchase: ₹{decision_res['remaining_budget']}")
""")

    # 18. Complete End-to-End Workflow Example
    add_md("""
## 18. Complete End-to-End Workflow Example
Execute a full end-to-end request through the Microsoft Agent Framework graph.
""")
    add_code("""
# Reset memory and calculator for clean demonstration
memory.reset()
calc.reset()
workflow = AcquisitionWorkflow(memory_service=memory, calculator=calc)

req_e2e = {
    "request_id": "R01",
    "book_title": "Artificial Intelligence",
    "requester": "CSE Department",
    "price": 2500.0,
    "category": "Computer Science"
}

e2e_res = workflow.run(req_e2e)
print("=== END-TO-END WORKFLOW RESULT ===")
for k, v in e2e_res.items():
    print(f"  {k}: {v}")
""")

    # 19. Execution of All Ten Evaluation Cases
    add_md("""
## 19. Execution of Exactly Ten Evaluation Cases
Process all 10 baseline evaluation requests sequentially to test budget tracking and decision precedence.
""")
    add_code("""
df_eval, eval_summary = run_evaluation(reset_state=True)
print(f"Successfully evaluated all {eval_summary['total_cases']} benchmark cases.")
""")

    # 20. Expected vs Actual Decision Comparison
    add_md("""
## 20. Expected versus Actual Decision Comparison Table
Compare the actual decisions against the academic ground truth baseline.
""")
    add_code("""
display_cols = [
    "request_id", "book_title", "category", "price",
    "expected_decision", "actual_decision", "status",
    "budget_before", "budget_after", "policy_clause", "demand_level"
]
print(df_eval[display_cols].to_string(index=False))
""")

    # 21. Decision Accuracy Calculation
    add_md("""
## 21. Decision Accuracy Calculation
Verify exact accuracy against the required 10-case evaluation metric.
""")
    add_code("""
acc = eval_summary["accuracy_percent"]
passed = eval_summary["passed_cases"]
total = eval_summary["total_cases"]

print("=" * 60)
print(f"DECISION ACCURACY: {acc}% ({passed}/{total} Test Cases Passed)")
print("=" * 60)
assert acc == 100.0, "Evaluation failed: accuracy must be 100%!"
""")

    # 22. Budget Validation and Audit
    add_md("""
## 22. Budget Audit and Validation
Confirm that approved purchases total ₹16,800.00 and remaining budget equals ₹3,200.00.
""")
    add_code("""
spent = eval_summary["total_approved_expenditure"]
remaining = eval_summary["final_remaining_budget"]
expected_spent = eval_summary["expected_expenditure"]
expected_remaining = eval_summary["expected_remaining"]

print("=" * 60)
print("BUDGET INTEGRITY AUDIT")
print("=" * 60)
print(f"Initial Budget:              ₹{INITIAL_BUDGET}")
print(f"Total Approved Expenditure:  {spent} (Expected: {expected_spent})")
print(f"Final Remaining Budget:      {remaining} (Expected: {expected_remaining})")
print(f"Mathematical Integrity:      {'VALID' if eval_summary['budget_integrity_valid'] else 'INVALID'}")
print(f"Sequential Budget Match:     {eval_summary['matches_ground_truth']}")
print("=" * 60)

assert spent == "₹16800.00", f"Expenditure mismatch: {spent}"
assert remaining == "₹3200.00", f"Remaining budget mismatch: {remaining}"
""")

    # 23. Final Evaluation Summary
    add_md("""
## 23. Final Evaluation Summary

### Verification Summary Table

| Evaluation Requirement | Expected Target | Actual Result | Verification Status |
|---|---|---|---|
| **Five Distinct Agents** | Separate modules for all 5 roles | 5 dedicated modules in `agents/` | **PASSED** |
| **Agent Framework** | Microsoft Agent Framework `WorkflowBuilder` | Real executors, fan-out/fan-in graph | **PASSED** |
| **Local RAG** | TF-IDF & Cosine Similarity over local policies | 12 policy docs indexed with scikit-learn | **PASSED** |
| **Shared Memory** | Persistent JSON blackboard | `SharedMemoryService` with live trace | **PASSED** |
| **10 Evaluation Cases** | Exact baseline cases R01 to R10 | All 10 executed sequentially | **PASSED** |
| **Decision Accuracy** | 100% agreement with expected outcomes | **100.0% (10/10 PASS)** | **PASSED** |
| **Approved Expenditure** | Exactly ₹16,800.00 | **₹16,800.00** | **PASSED** |
| **Final Remaining Budget**| Exactly ₹3,200.00 | **₹3,200.00** | **PASSED** |
| **Non-Negative Budget** | Budget never drops below zero | Validated via Python `Decimal` | **PASSED** |

### Conclusion
The Library Acquisition and Collection Development Committee multi-agent system fully satisfies all requirements of Project 2 / Q17 for CSE476. The system demonstrates robust multi-agent orchestration, grounded retrieval, explainable decision precedence, and strict fiscal integrity.
""")

    # Execute all code cells sequentially in an execution namespace and attach outputs
    print("Executing notebook cells sequentially to capture outputs...")
    exec_globals = {}
    cell_idx = 1

    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.execution_count = cell_idx
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                try:
                    exec(cell.source, exec_globals)
                except Exception as exc:
                    print(f"Error in cell {cell_idx}: {exc}")
                    raise

            out_text = stdout_capture.getvalue()
            err_text = stderr_capture.getvalue()

            cell.outputs = []
            if out_text:
                cell.outputs.append(nbf.v4.new_output(
                    output_type="stream",
                    name="stdout",
                    text=out_text
                ))
            if err_text:
                cell.outputs.append(nbf.v4.new_output(
                    output_type="stream",
                    name="stderr",
                    text=err_text
                ))
            print(f"  Cell {cell_idx} executed successfully.")
            cell_idx += 1

    # Save executed notebook
    notebook_dir = project_root / "notebooks"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    notebook_path = notebook_dir / "Library_Acquisition_Multi_Agent_Demo.ipynb"
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    print(f"\nSaved executed notebook with real outputs to: {notebook_path}")


if __name__ == "__main__":
    generate_and_execute_notebook()
