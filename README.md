# Library Acquisition and Collection Development Committee Multi-Agent System

**Course:** CSE476 — Agentic AI and Intelligent Automation  
**Academic Task:** Task 2 (Project 2 / Q17)  
**Evaluation Scope:** Unit III (Agent Workflows & Architectures) & Unit IV (Orchestration, Grounded RAG, & Shared Memory)  
**Evaluation Target:** 30 Marks (Bloom's Taxonomy L4, L5, L6)  
**Student Team:**  
- **Priya Rawat** (Registration No: `12314866`)  
- **Chiluveru Shiva Prasad** (Registration No: `12304258`)  

---

## 1. Project Overview

The **Library Acquisition and Collection Development Committee** is an automated multi-agent governance platform designed to evaluate and decide on academic book purchases under a strictly constrained operational budget of **₹20,000.00**.

In academic institutions, libraries receive steady acquisition requests from faculty members, students, and academic departments. Evaluating these requests manually creates administrative bottlenecks, delayed procurement, potential collection duplication, and fiscal overspending. 

This system automates the decision pipeline by deploying a committee of **five specialized software agents** orchestrated with the **Microsoft Agent Framework (`agent-framework-core`)**. The committee enforces a genuine **fan-out / fan-in** coordination graph, performs local **Retrieval-Augmented Generation (RAG)** over university acquisition policies, analyzes historical patron demand through circulation data, and maintains non-negative fiscal solvency via Python `Decimal` arithmetic on an application-level **shared memory blackboard**.

For every requested title, the system renders one of three definitive verdicts:
1. **BUY**: Approved for immediate acquisition. Compliant with curricular policies, validated with HIGH patron demand, and fully covered by available funds.
2. **DEFER**: Academic alignment confirmed, but postponed due to moderate/low demand, insufficient remaining funds, or pending committee review.
3. **REJECT**: Confirmed collection policy violation (e.g., recreational/non-academic text) or confirmed duplicate of cataloged holdings.

---

## 2. Assignment Objective & Deliverables

As stipulated in the CSE476 Project 2 / Q17 specification:
- **Core Objective:** Design, build, and demonstrate a working prototype of a multi-agent system automating real-world library collection governance using Microsoft Agent Framework, grounded retrieval, shared memory, and collaborative task execution.
- **Five Specialized Agents:** Request Intake Agent, Collection Policy Retrieval Agent, Demand Agent, Budget Agent, Acquisitions Manager.
- **Architecture:** Coordinated via fan-out / fan-in topology.
- **Retrieval & Memory:** Local RAG over a 12-document policy corpus, plus a shared memory service tracking circulation history, budget state, and agent execution logs.
- **Expected Output:** Final decision per request (`BUY` / `DEFER` / `REJECT`), the supporting policy clause, and remaining budget balance.
- **Evaluation Benchmark:** Sequential execution across 10 defined evaluation requests (R01 through R10) achieving 100% accuracy, verifying non-negative balances, total approved spending of exactly ₹16,800.00, and final remaining balance of ₹3,200.00.
- **Add-on Feature (Group-of-3 add-on):** Faculty Recommendation review pathway routing high-cost proposals to human committee oversight.

---

## 3. Technology Stack

| Component | Technology | Version / Configuration | Purpose |
|---|---|---|---|
| **Language** | Python | 3.12+ (Tested on 3.14) | Base programming language |
| **Multi-Agent Framework** | Microsoft Agent Framework | `agent-framework-core 1.14.0`, `agent-framework-openai 1.13.0` | Agent construction, executors, and fan-out/fan-in workflow graph |
| **LLM Provider** | Groq API | Model: `qwen/qwen3.8-27b` via OpenAI-compatible endpoint | Natural language explanation synthesis and executive summaries |
| **Local RAG Retrieval** | `scikit-learn` | 1.9.1 (TF-IDF Vectorizer & Cosine Similarity) | Zero-cost grounded retrieval over synthetic markdown policies |
| **Numerical Processing** | `numpy`, `scipy` | 2.5.2, 1.18.0 | Vector computation and cosine similarity math |
| **Data Handling** | `pandas` | 3.0.5 | Tabular display of circulation history and evaluation tables |
| **Financial Arithmetic** | Python `Decimal` | Built-in | Exact 2-decimal monetary tracking preventing floating-point rounding errors |
| **Shared Memory** | Python `SharedMemoryService` | JSON persistence (`data/memory_state.json`) | Thread-safe blackboard memory for multi-agent traces and ledgers |
| **Frontend UI** | Streamlit | 1.62.0 | University demonstration interface with interactive panels |
| **Testing Framework** | `pytest` | 9.1.1 | 31 automated unit and integration tests |
| **Interactive Notebook** | Jupyter Notebook | `.ipynb` (v4 format) | Mandatory executed notebook with 23 complete sections |

---

## 4. Multi-Agent Architecture

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

---

## 5. Conceptual Primer for Beginners

### A. What is an AI Agent?
An AI agent is an autonomous software component assigned a clear persona, specific responsibilities, bounded tools, and access to state. Unlike monolithic scripts, each agent specializes in one domain: the Policy Agent never computes budget balances, and the Budget Agent never fabricates regulatory clauses.

### B. Tools and Function Calling
Tools are deterministic Python functions called by agents to perform exact actions. In this project:
- `calculate_demand_score()`: Deterministically calculates normalized reader demand.
- `PolicyRetriever.retrieve()`: Computes TF-IDF cosine similarity over regulatory texts.
- `BudgetCalculator.check_affordability()`: Performs exact fiscal checks using Python `Decimal`.

### C. What is an Executor?
In Microsoft Agent Framework, an `Executor` is a node in the workflow graph that consumes typed inputs, executes handler methods marked with `@handler`, emits messages using `ctx.send_message()`, or yields terminal outputs via `ctx.yield_output()`.

### D. Workflow Graphs, Fan-Out, and Fan-In
- **Workflow Graph:** Directed graph linking executors together. Built using `WorkflowBuilder`.
- **Fan-Out (`WorkflowBuilder.add_fan_out_edges`):** Distributes the validated book request from `IntakeWorkflowExecutor` concurrently to three specialist executors (`PolicyWorkflowExecutor`, `DemandWorkflowExecutor`, and `BudgetWorkflowExecutor`).
- **Fan-In (`WorkflowBuilder.add_fan_in_edges`):** Synchronizes multiple incoming concurrent streams. The `ManagerWorkflowExecutor` is only invoked once all three specialist executors have finished, receiving a aggregated list of results.

---

## 6. The Five Specialized Agents

### 1. Request Intake Agent (`agents/intake_agent.py`)
- **Inputs:** Raw user dictionary with `book_title`, `requester`, `price`, and optional `category`.
- **Logic:** Validates that `book_title` and `requester` are non-empty, and `price` is positive. Assigns a unique Request ID (e.g. `REQ001`).
- **Outputs:** Structured, validated request record registered in shared memory.

### 2. Collection Policy Retrieval Agent (`agents/policy_agent.py`)
- **Inputs:** Validated book title, category, and price.
- **Logic:** Searches the 12-document acquisition policy corpus via Local TF-IDF Cosine Similarity. Detects duplicate copy restrictions (`POL-002`), curricular scope alignment (`POL-001`), and non-academic exclusions (`POL-003`).
- **Outputs:** Retrieved document ID, policy clause, relevance score, policy status (`COMPLIANT`, `VIOLATION`, or `INSUFFICIENT_EVIDENCE`), and grounded explanation.

### 3. Demand Agent (`agents/demand_agent.py`)
- **Inputs:** Book title and category.
- **Logic:** Queries `data/circulation_history.csv` and invokes `demand_statistics.py`. Applies the formula:
  $$\text{Demand Score} = (\text{Checkout Score} \times 0.70) + (\text{Reservation Score} \times 0.30)$$
  where $\text{Checkout Score} = \min(\text{checkouts} / 100, 1.0) \times 100$ and $\text{Reservation Score} = \min(\text{reservations} / 30, 1.0) \times 100$.
- **Outputs:** Numeric score ($0 - 100$), classification (`HIGH`, `MEDIUM`, or `LOW`), historical circulation evidence, and analytical summary.

### 4. Budget Agent (`agents/budget_agent.py`)
- **Inputs:** Book price and current remaining budget.
- **Logic:** Calls `BudgetCalculator.check_affordability()` using Python `Decimal`. Calculates whether $\text{price} \le \text{remaining\_budget}$ and projected remaining balance.
- **Important Constraint:** Does *not* deduct money or approve purchases independently.

### 5. Acquisitions Manager (`agents/acquisition_manager.py`)
- **Inputs:** Aggregated findings from Policy, Demand, and Budget agents.
- **Logic:** Enforces deterministic precedence hierarchy:
  1. Confirmed policy violation $\rightarrow$ **REJECT**
  2. Confirmed duplicate $\rightarrow$ **REJECT**
  3. Confirmed out-of-scope recreational request $\rightarrow$ **REJECT**
  4. Missing or failed specialist findings $\rightarrow$ **DEFER**
  5. Inconclusive or low-confidence policy evidence $\rightarrow$ **DEFER**
  6. Demand score below HIGH threshold ($< 70.0$) $\rightarrow$ **DEFER**
  7. Insufficient available budget balance $\rightarrow$ **DEFER**
  8. All requirements satisfied $\rightarrow$ **BUY**
- **Financial Update:** Deducts approved purchase cost from budget if and only if final verdict is `BUY`. Updates shared memory.

---

## 7. RAG Implementation (Local TF-IDF)

Local Retrieval-Augmented Generation provides explainability and regulatory grounding without external paid embedding APIs:
1. **Corpus:** 12 structured markdown policy files stored in `data/policies/`.
2. **Vectorization:** `TfidfVectorizer` (scikit-learn) with unigrams and bigrams, stop-words removal, and sublinear TF scaling.
3. **Similarity Metric:** Cosine similarity between the query vector and document index vectors.
4. **Confidence Threshold:** A cutoff threshold of `0.12` separates grounded matches from low-confidence queries.
5. **No Hallucination:** If confidence is below threshold, the agent reports `INSUFFICIENT_EVIDENCE` rather than inventing clauses.

---

## 8. Shared Memory Blackboard (`memory/shared_memory.py`)

Shared memory acts as an application-level blackboard shared by all five agents:
- **Thread Safety:** Protected via Python `threading.RLock`.
- **Persistence:** Serializes to `data/memory_state.json`. Persists across restarts.
- **Stored Data:**
  - Initial budget and real-time remaining balance.
  - Approved purchase ledgers.
  - Validated request records.
  - Specialist findings (Policy, Demand, Budget).
  - Committee final decisions and chronological execution traces.

---

## 9. Baseline Evaluation: Exactly 10 Requests

The system is tested sequentially against the 10 benchmark requests defined in the specification. Each approved purchase updates the budget available for subsequent requests:

| ID | Book Title | Price | Expected Decision | Actual Decision | Status | Budget Before | Budget After | Policy Clause |
|:---:|:---|---:|:---:|:---:|:---:|---:|---:|:---|
| **R01** | Artificial Intelligence | ₹2,500.00 | **BUY** | **BUY** | **PASS** | ₹20,000.00 | ₹17,500.00 | `CLAUSE-SCOPE-1.1` |
| **R02** | Data Structures | ₹1,800.00 | **BUY** | **BUY** | **PASS** | ₹17,500.00 | ₹15,700.00 | `CLAUSE-SCOPE-1.1` |
| **R03** | Rare Academic Reference | ₹3,000.00 | **DEFER** | **DEFER** | **PASS** | ₹15,700.00 | ₹15,700.00 | `CLAUSE-DEM-4.1` |
| **R04** | Existing Database Systems Duplicate | ₹2,200.00 | **REJECT** | **REJECT** | **PASS** | ₹15,700.00 | ₹15,700.00 | `CLAUSE-DUP-2.1` |
| **R05** | Cybersecurity Fundamentals | ₹4,500.00 | **BUY** | **BUY** | **PASS** | ₹15,700.00 | ₹11,200.00 | `CLAUSE-SEC-9.1` |
| **R06** | Unrelated Cooking Collection | ₹1,500.00 | **REJECT** | **REJECT** | **PASS** | ₹11,200.00 | ₹11,200.00 | `CLAUSE-EXCL-3.1` |
| **R07** | Cloud Computing | ₹6,000.00 | **BUY** | **BUY** | **PASS** | ₹11,200.00 | ₹5,200.00 | `CLAUSE-CLOUD-8.1` |
| **R08** | Robotics Research | ₹7,000.00 | **DEFER** | **DEFER** | **PASS** | ₹5,200.00 | ₹5,200.00 | `CLAUSE-BUD-5.1` |
| **R09** | Python Programming | ₹2,000.00 | **BUY** | **BUY** | **PASS** | ₹5,200.00 | ₹3,200.00 | `CLAUSE-PROG-11.1` |
| **R10** | Advanced Quantum Computing | ₹5,000.00 | **DEFER** | **DEFER** | **PASS** | ₹3,200.00 | ₹3,200.00 | `CLAUSE-DEM-4.1` |

### Ground Truth Financial Verification
- **Total Approved Expenditure:** ₹2,500 + ₹1,800 + ₹4,500 + ₹6,000 + ₹2,000 = **₹16,800.00**
- **Final Remaining Budget:** ₹20,000.00 - ₹16,800.00 = **₹3,200.00**
- **Decision Breakdown:** BUY: 5, DEFER: 3, REJECT: 2
- **Decision Accuracy:** **100.0% (10/10 PASS)**
- **Budget Integrity:** Mathematical verification confirmed: $\text{Budget} \ge 0.00$.

---

## 10. Project Folder Structure

```text
Library/
│
├── app.py                     # Streamlit web dashboard
├── build_notebook.py          # Generator & runner for demonstration notebook
├── requirements.txt           # Python dependencies
├── .env.example               # Template for environment variables
├── .gitignore                 # Excluded files and directories
├── README.md                  # Comprehensive academic & technical documentation
│
├── agents/                    # 5 Specialized Agent modules
│   ├── __init__.py
│   ├── intake_agent.py        # Agent 1: Request Intake Agent
│   ├── policy_agent.py        # Agent 2: Collection Policy Retrieval Agent
│   ├── demand_agent.py        # Agent 3: Demand Agent
│   ├── budget_agent.py        # Agent 4: Budget Agent
│   ├── acquisition_manager.py # Agent 5: Acquisitions Manager
│   └── llm_client.py          # Groq client factory & deterministic fallback
│
├── workflows/                 # Microsoft Agent Framework orchestration
│   ├── __init__.py
│   └── acquisition_workflow.py# WorkflowBuilder, Executors, fan-out/fan-in graph
│
├── tools/                     # Deterministic execution tools
│   ├── __init__.py
│   ├── demand_statistics.py   # Demand score calculation & circulation lookup
│   └── budget_calculator.py   # Decimal financial tracking & deduction audits
│
├── rag/                       # Local RAG engine
│   ├── __init__.py
│   ├── document_loader.py     # Markdown policy document parser
│   └── retrieval.py           # TF-IDF & Cosine Similarity vector retriever
│
├── memory/                    # Persistent shared memory blackboard
│   ├── __init__.py
│   └── shared_memory.py       # Thread-safe blackboard & JSON state serializer
│
├── evaluation/                # Automated evaluation suite
│   ├── __init__.py
│   ├── test_cases.json        # Exactly 10 benchmark test cases
│   └── evaluate.py            # Sequential evaluation runner & reporting
│
├── data/                      # Synthetic data store
│   ├── circulation_history.csv# 15 circulation & reservation records
│   ├── book_requests.json     # 10 book request specifications
│   ├── memory_state.json      # Persistent shared memory snapshot
│   └── policies/              # 12 synthetic library acquisition policies
│       ├── policy_01.md       # POL-001: Academic Curriculum Alignment
│       ├── policy_02.md       # POL-002: Duplicate Acquisition Prohibition
│       ├── policy_03.md       # POL-003: Non-Academic Scope Exclusions
│       ├── policy_04.md       # POL-004: Minimum Demand Circulation Benchmarks
│       ├── policy_05.md       # POL-005: Fiscal Solvency & Budget Ceiling
│       ├── policy_06.md       # POL-006: Emerging Technologies & Quantum
│       ├── policy_07.md       # POL-007: High-Cost Acquisitions & Committee
│       ├── policy_08.md       # POL-008: Cloud Infrastructure Engineering
│       ├── policy_09.md       # POL-009: Cybersecurity & Information Assurance
│       ├── policy_10.md       # POL-010: Rare Academic Reference & Archives
│       ├── policy_11.md       # POL-011: Programming Languages
│       └── policy_12.md       # POL-012: Robotics & Automation
│
├── notebooks/                 # Demonstration Notebook
│   └── Library_Acquisition_Multi_Agent_Demo.ipynb # Executed notebook with real outputs
│
└── tests/                     # Automated pytest test suite (31 tests)
    ├── __init__.py
    ├── test_intake.py         # Unit tests for Request Intake Agent
    ├── test_policy_retrieval.py# Unit tests for RAG retriever & Policy Agent
    ├── test_demand.py         # Unit tests for demand score formulas & tool
    ├── test_budget.py         # Unit tests for Decimal budget tracking & limits
    ├── test_workflow.py       # Integration tests for Agent Framework workflow
    └── test_evaluation.py     # Full benchmark evaluation test (100% target)
```

---

## 11. Installation & Setup Instructions

### Prerequisites
- Python 3.12 or higher (Python 3.14 fully supported).
- Windows, macOS, or Linux.

### Step 1: Clone or Navigate to Project
```bash
cd "c:\Users\chilu\OneDrive\Desktop\Library"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your `.env` contains:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
GROQ_BASE_URL=https://api.groq.com/openai/v1
INITIAL_BUDGET=20000.00
```
*(Note: If `GROQ_API_KEY` is omitted or offline, the system automatically activates **Deterministic Demo Mode**, keeping all agent interfaces, workflow logic, and decision rules 100% operational).*

---

## 12. How to Run and Demonstrate

### A. Run Automated Pytest Suite (31 Tests)
```bash
python -m pytest -v
```
All 31 unit and integration tests execute and pass cleanly.

### B. Run the 10-Case Benchmark Evaluation
```bash
python -m evaluation.evaluate
```
Outputs the tabular comparison, confirms 100% accuracy, ₹16,800.00 approved spending, and ₹3,200.00 remaining budget.

### C. Launch the Streamlit Frontend
```bash
streamlit run app.py
```
Opens the interactive web dashboard at `http://localhost:8501`. Features include:
- Interactive book request submission with immediate multi-agent visualization.
- One-click 10-case evaluation benchmark with summary metrics and charts.
- RAG Policy Explorer with vector search.
- Circulation dataset table and bar charts.
- Live shared memory blackboard inspection.

### D. Open and Run the Jupyter Notebook
```bash
jupyter notebook notebooks/Library_Acquisition_Multi_Agent_Demo.ipynb
```
The notebook is pre-executed with real outputs saved for all 23 required sections.

To re-generate and execute the notebook from scratch:
```bash
python build_notebook.py
```

---

## 13. System Limitations

1. **Synthetic Scope:** Policy documents and circulation datasets are synthetically generated for academic demonstration within CSE476.
2. **TF-IDF Keyword Dependence:** The local RAG retrieval relies on lexical and n-gram TF-IDF representations. It excels on targeted curricular terminology but does not employ dense neural embeddings.
3. **Single Currency:** The current budget calculator assumes Indian Rupees (INR / ₹) with 2-decimal precision. Multi-currency foreign publisher conversions are not modeled.
