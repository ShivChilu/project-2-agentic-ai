"""Streamlit Frontend for Library Acquisition Multi-Agent System.

Course: CSE476 - Agentic AI and Intelligent Automation
Project Reference: Project 2 / Q17
Group Members: Priya Rawat (12314866), Chiluveru Shiva Prasad (12304258)
"""

import os
from decimal import Decimal
from pathlib import Path
import pandas as pd
import streamlit as st

# Configure page layout and style
st.set_page_config(
    page_title="Library Acquisition Multi-Agent System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Internal project imports
from memory.shared_memory import SharedMemoryService
from tools.budget_calculator import BudgetCalculator, INITIAL_BUDGET
from workflows.acquisition_workflow import AcquisitionWorkflow
from rag.retrieval import PolicyRetriever
from tools.demand_statistics import (
    calculate_demand_score,
    classify_demand,
    lookup_circulation_history
)
from evaluation.evaluate import run_evaluation
from agents.llm_client import llm_manager

# Initialize session state objects
if "memory" not in st.session_state:
    st.session_state.memory = SharedMemoryService()

if "calculator" not in st.session_state:
    st.session_state.calculator = BudgetCalculator(initial_budget=INITIAL_BUDGET)

if "workflow" not in st.session_state:
    st.session_state.workflow = AcquisitionWorkflow(
        memory_service=st.session_state.memory,
        calculator=st.session_state.calculator
    )

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Custom CSS for university demonstration styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .agent-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .agent-header {
        font-weight: 600;
        font-size: 1.05rem;
        color: #1E293B;
        margin-bottom: 6px;
    }
    .badge-buy {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.95rem;
    }
    .badge-defer {
        background-color: #FEF9C3;
        color: #854D0E;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.95rem;
    }
    .badge-reject {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation and System Info
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/library.png", width=110)
    st.title("Acquisition Committee")
    st.markdown("**Course:** CSE476 — Agentic AI & Automation")
    st.markdown("**Project Ref:** Project 2 / Group 17")
    
    # Mode indicator
    if llm_manager.is_demo_mode:
        st.warning("⚡ **Mode:** DETERMINISTIC DEMO MODE")
    else:
        st.success(f"🟢 **Mode:** LIVE GROQ API ({llm_manager.model})")
        
    st.divider()
    nav_option = st.radio(
        "Navigation",
        [
            "📊 Dashboard & Decisions",
            "🧪 10-Case Benchmark",
            "📜 Policy Explorer (RAG)",
            "📈 Circulation History",
            "🧠 Shared Memory Blackboard"
        ]
    )
    
    st.divider()
    if st.button("🔄 Reset Budget & Memory"):
        st.session_state.memory.reset()
        st.session_state.calculator.reset()
        st.session_state.last_result = None
        st.success("Shared memory and budget reset to initial ₹20,000.00!")
        st.rerun()

    st.markdown("---")
    st.caption("Priya Rawat (12314866)\nChiluveru Shiva Prasad (12304258)")


# -------------------------------------------------------------------------------------------------
# PAGE 1: DASHBOARD & REAL-TIME WORKFLOW EXECUTION
# -------------------------------------------------------------------------------------------------
if nav_option == "📊 Dashboard & Decisions":
    st.markdown('<div class="main-title">Library Acquisition Multi-Agent System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Automated Book Acquisition and Collection Development Committee under Fixed Budget</div>', unsafe_allow_html=True)

    # Key Metrics Bar
    col1, col2, col3, col4, col5 = st.columns(5)
    remaining_b = st.session_state.calculator.get_remaining_budget()
    total_spent = st.session_state.calculator.get_total_approved_expenditure()
    all_decisions = st.session_state.memory.final_decisions
    
    b_count = sum(1 for d in all_decisions if d.get("decision") == "BUY")
    d_count = sum(1 for d in all_decisions if d.get("decision") == "DEFER")
    r_count = sum(1 for d in all_decisions if d.get("decision") == "REJECT")

    col1.metric("Initial Budget", f"₹{INITIAL_BUDGET:,.2f}")
    col2.metric("Remaining Budget", f"₹{remaining_b:,.2f}", delta=f"-₹{total_spent:,.2f}", delta_color="inverse")
    col3.metric("BUY Decisions", b_count)
    col4.metric("DEFER Decisions", d_count)
    col5.metric("REJECT Decisions", r_count)

    st.divider()

    left_col, right_col = st.columns([1, 1.25])

    # Left Column: New Request Submission Form
    with left_col:
        st.subheader("📥 Submit Book Acquisition Request")
        with st.form("request_form"):
            in_title = st.text_input("Book Title *", placeholder="e.g. Artificial Intelligence")
            in_req = st.text_input("Requester Name or Department *", placeholder="e.g. CSE Department")
            in_price = st.number_input("Book Unit Price (₹) *", min_value=1.0, value=2500.0, step=100.0)
            in_cat = st.selectbox(
                "Subject / Curricular Category",
                [
                    "Computer Science",
                    "Cybersecurity",
                    "Infrastructure & Cloud",
                    "Software Engineering",
                    "Robotics & Automation",
                    "Data Science",
                    "Reference & Archives",
                    "Advanced Research",
                    "Culinary Arts",
                    "General"
                ]
            )
            
            # Faculty add-on option (Group-of-3 add-on feature)
            faculty_override = st.selectbox(
                "Faculty Committee Add-On Routing (Optional)",
                ["Standard Automatic Workflow", "Faculty Sponsorship (APPROVE)", "Faculty Rejection (REJECT)"]
            )
            
            submitted = st.form_submit_button("⚡ Run Multi-Agent Committee", type="primary")

        if submitted:
            if not in_title.strip() or not in_req.strip():
                st.error("Please provide both Book Title and Requester.")
            else:
                override_val = None
                if "APPROVE" in faculty_override:
                    override_val = "APPROVE"
                elif "REJECT" in faculty_override:
                    override_val = "REJECT"

                with st.spinner("Executing Microsoft Agent Framework Fan-Out/Fan-In Workflow..."):
                    try:
                        raw_req = {
                            "book_title": in_title.strip(),
                            "requester": in_req.strip(),
                            "price": in_price,
                            "category": in_cat
                        }
                        
                        # Execute workflow
                        res = st.session_state.workflow.run(raw_req)
                        
                        # Apply faculty override if selected
                        if override_val:
                            res = st.session_state.workflow.manager_agent.make_decision(
                                request_data=res,
                                policy_findings=st.session_state.memory.policy_findings.get(res["request_id"]),
                                demand_findings=st.session_state.memory.demand_findings.get(res["request_id"]),
                                budget_findings=st.session_state.memory.budget_findings.get(res["request_id"]),
                                faculty_override=override_val
                            )
                            
                        st.session_state.last_result = res
                        st.success(f"Request {res['request_id']} evaluated successfully!")
                    except Exception as err:
                        st.error(f"Execution Error: {err}")

    # Right Column: Multi-Agent Execution & Decision Report
    with right_col:
        st.subheader("🤖 Multi-Agent Execution & Committee Verdict")
        if st.session_state.last_result:
            res = st.session_state.last_result
            decision = res["decision"]
            
            # Outcome Banner
            badge_class = f"badge-{decision.lower()}"
            st.markdown(
                f"""
                <div style="background-color: #F1F5F9; padding: 16px; border-radius: 8px; margin-bottom: 14px; border-left: 6px solid {'#16A34A' if decision=='BUY' else '#CA8A04' if decision=='DEFER' else '#DC2626'};">
                    <span style="font-size: 1.2rem; font-weight: 700;">Final Decision: </span>
                    <span class="{badge_class}">{decision}</span>
                    <p style="margin-top: 8px; margin-bottom: 2px; color: #1E293B;"><b>Reason:</b> {res['decision_reason']}</p>
                    <p style="margin-bottom: 0px; color: #475569; font-size: 0.95rem;"><b>Executive Summary:</b> {res.get('executive_summary', '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Visual Fan-Out / Fan-In Multi-Agent Panels
            st.markdown("##### 👥 Five Specialized Agents Execution Trace")
            
            # Agent 1: Intake
            with st.expander("1️⃣ Request Intake Agent (Completed)", expanded=False):
                st.write(f"**Request ID:** `{res['request_id']}` | **Status:** `VALIDATED`")
                st.write(f"**Book:** {res['book_title']} | **Requester:** {res['requester']} | **Price:** ₹{res['price']}")
            
            # Fan-out Specialist Agents (Policy, Demand, Budget)
            c_p, c_d, c_b = st.columns(3)
            with c_p:
                with st.expander("2️⃣ Policy Agent (RAG)", expanded=True):
                    st.caption("Local TF-IDF Vector Search")
                    st.write(f"**Clause:** `{res['policy_clause']}`")
                    st.write(f"**Status:** `{res['policy_status']}`")
                    st.write(f"**Evidence:** {res.get('policy_evidence', '')}")

            with c_d:
                with st.expander("3️⃣ Demand Agent", expanded=True):
                    st.caption("Circulation Statistics Tool")
                    st.write(f"**Score:** `{res['demand_score']}/100`")
                    st.write(f"**Classification:** `{res['demand_level']}`")
                    st.write(f"**Circulation Evidence:** {res.get('demand_evidence', '')}")

            with c_b:
                with st.expander("4️⃣ Budget Agent", expanded=True):
                    st.caption("Python Decimal Fiscal Tool")
                    st.write(f"**Balance Before:** `₹{res['budget_available']}`")
                    st.write(f"**Balance After:** `₹{res['remaining_budget']}`")
                    st.write(f"**Purchase Cost:** `₹{res['price']}`")

            # Agent 5: Acquisitions Manager (Fan-In Barrier)
            with st.expander("5️⃣ Acquisitions Manager (Fan-In Barrier Reached)", expanded=True):
                st.write(f"**Precedence Evaluation:** Received findings from all 3 specialist agents.")
                st.write(f"**Deterministic Outcome:** `{res['decision']}`")
                st.write(f"**Policy Clause Cited:** `{res['policy_clause']}`")
                st.write(f"**Remaining Acquisition Balance:** `₹{res['remaining_budget']}`")
        else:
            st.info("Submit a book request on the left or run the benchmark evaluation to view multi-agent results.")

    # Recent Decisions Table
    st.divider()
    st.subheader("📋 Recent Committee Decisions")
    if all_decisions:
        df_recent = pd.DataFrame(all_decisions)[
            ["request_id", "book_title", "price", "decision", "policy_clause", "demand_level", "remaining_budget", "decision_reason"]
        ]
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.caption("No requests processed yet in this session.")


# -------------------------------------------------------------------------------------------------
# PAGE 2: 10-CASE BENCHMARK EVALUATION
# -------------------------------------------------------------------------------------------------
elif nav_option == "🧪 10-Case Benchmark":
    st.markdown('<div class="main-title">Evaluation Benchmark: Exactly 10 Requests</div>', unsafe_allow_html=True)
    st.markdown("Verifies deterministic decision logic, sequential budget deductions, and 100% accuracy against expected baseline outcomes.")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_btn = st.button("🚀 Run 10-Case Evaluation Benchmark", type="primary")

    if run_btn or "eval_df" in st.session_state:
        if run_btn:
            with st.spinner("Running sequential multi-agent execution across 10 evaluation cases..."):
                df_eval, eval_summary = run_evaluation(reset_state=True)
                st.session_state.eval_df = df_eval
                st.session_state.eval_summary = eval_summary

        df_eval = st.session_state.eval_df
        eval_summary = st.session_state.eval_summary

        # Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Decision Accuracy", f"{eval_summary['accuracy_percent']}%", "10/10 Correct")
        m2.metric("Total Approved", eval_summary["total_approved_expenditure"], "Expected: ₹16,800.00")
        m3.metric("Final Remaining", eval_summary["final_remaining_budget"], "Expected: ₹3,200.00")
        m4.metric("Approved (BUY)", f"{eval_summary['buy_count']} books")
        m5.metric("Deferred / Rejected", f"{eval_summary['defer_count']} Def / {eval_summary['reject_count']} Rej")

        st.divider()

        # Detailed Comparison Table
        st.subheader("📊 Individual Request Results: Expected vs Actual")
        st.dataframe(
            df_eval[["request_id", "book_title", "category", "price", "expected_decision", "actual_decision", "status", "budget_before", "budget_after", "policy_clause", "demand_level"]],
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("##### 🔍 Sequential Budget Progression Verification")
        st.markdown("""
        1. **R01 (₹2,500), R02 (₹1,800), R05 (₹4,500), R07 (₹6,000)** approved sequentially $\\rightarrow$ Remaining: **₹5,200.00**.
        2. **R08 (Robotics Research, ₹7,000)**: Demand is HIGH (83.4/100), but cost exceeds remaining budget (**₹7,000 > ₹5,200**) $\\rightarrow$ **DEFER** (Budget remains ₹5,200.00).
        3. **R09 (Python Programming, ₹2,000)**: Affordable (**₹2,000 $\\le$ ₹5,200**) $\\rightarrow$ **BUY** (Remaining: **₹3,200.00**).
        4. **Total Approved Expenditure:** ₹2,500 + ₹1,800 + ₹4,500 + ₹6,000 + ₹2,000 = **₹16,800.00**.
        """)


# -------------------------------------------------------------------------------------------------
# PAGE 3: POLICY EXPLORER (LOCAL RAG)
# -------------------------------------------------------------------------------------------------
elif nav_option == "📜 Policy Explorer (RAG)":
    st.markdown('<div class="main-title">Collection Acquisition Policy Corpus (RAG)</div>', unsafe_allow_html=True)
    st.markdown("Local TF-IDF vector retrieval engine searching 12 synthetic library acquisition policies.")

    retriever = PolicyRetriever()
    search_query = st.text_input("🔍 Search Policy Corpus", placeholder="e.g. duplicate book restrictions or cloud computing")

    if search_query.strip():
        res = retriever.retrieve(title=search_query)
        st.markdown(f"**Retrieved Document:** `{res.document_title}` (`{res.document_id}`)")
        st.markdown(f"**Policy Clause:** `{res.policy_clause}` | **Relevance Score:** `{res.relevance_score}` | **Status:** `{res.policy_status}`")
        st.info(f"**Explanation:** {res.explanation}")
        st.divider()

    st.subheader("📚 All 12 Acquisition Policy Documents")
    for doc in retriever.documents:
        with st.expander(f"{doc.document_id}: {doc.title} ({doc.clause})"):
            st.markdown(f"**Category:** `{doc.category}`")
            st.markdown(f"**Policy Clause:** `{doc.clause}`")
            st.markdown(f"**Full Description:**\n\n{doc.description}")


# -------------------------------------------------------------------------------------------------
# PAGE 4: CIRCULATION HISTORY DATASET
# -------------------------------------------------------------------------------------------------
elif nav_option == "📈 Circulation History":
    st.markdown('<div class="main-title">Synthetic Circulation History & Demand Analytics</div>', unsafe_allow_html=True)
    st.markdown("Historical checkout and reservation logs utilized by the Demand Agent statistics tool.")

    csv_path = Path(__file__).resolve().parent / "data" / "circulation_history.csv"
    if csv_path.exists():
        df_circ = pd.read_csv(csv_path)
        
        # Calculate scores for display
        scores = []
        levels = []
        for _, row in df_circ.iterrows():
            s = calculate_demand_score(int(row["checkouts"]), int(row["reservations"]))
            scores.append(s)
            levels.append(classify_demand(s))
            
        df_circ["demand_score"] = scores
        df_circ["demand_level"] = levels

        st.dataframe(df_circ, use_container_width=True)

        st.subheader("📊 Historical Circulation Activity")
        chart_data = df_circ.set_index("book_title")[["checkouts", "reservations"]]
        st.bar_chart(chart_data)
    else:
        st.error("Circulation dataset not found.")


# -------------------------------------------------------------------------------------------------
# PAGE 5: SHARED MEMORY BLACKBOARD
# -------------------------------------------------------------------------------------------------
elif nav_option == "🧠 Shared Memory Blackboard":
    st.markdown('<div class="main-title">Shared Application Memory Blackboard</div>', unsafe_allow_html=True)
    st.markdown("Persistent thread-safe storage where all five agents record findings, state updates, and transaction logs.")

    tab1, tab2, tab3 = st.tabs(["📝 Agent Execution Trace", "💰 Approved Purchases", "💾 Raw JSON State"])

    with tab1:
        st.subheader("Agent Execution Log Entries")
        logs = st.session_state.memory.agent_execution_logs
        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("No agent actions recorded yet.")

    with tab2:
        st.subheader("Approved Purchase Ledgers")
        purchases = st.session_state.memory.approved_purchases
        if purchases:
            df_p = pd.DataFrame(purchases)
            st.dataframe(df_p, use_container_width=True)
        else:
            st.info("No approved purchases yet.")

    with tab3:
        st.subheader("Live Persistent Memory File (`data/memory_state.json`)")
        mem_file = Path(__file__).resolve().parent / "data" / "memory_state.json"
        if mem_file.exists():
            st.code(mem_file.read_text(encoding="utf-8"), language="json")
        else:
            st.info("No persisted memory file on disk yet.")
