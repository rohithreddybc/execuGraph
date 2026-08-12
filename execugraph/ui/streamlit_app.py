"""Streamlit interactive demo for ExecuGraph.

Run with::

    streamlit run -m execugraph.ui.streamlit_app

(or, if installed: ``streamlit run execugraph/ui/streamlit_app.py``)

Reads its LLM backend from the same YAML config files as the CLI runner.
Set ``EXECUGRAPH_CONFIG`` to point at a config file (default
``configs/default.yaml``).
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
import yaml

from execugraph.benchmarks.base import Problem
from execugraph.graph.workflow import WorkflowDeps
from execugraph.llm.base import CostAccumulator
from execugraph.llm.factory import build_backend
from execugraph.pipelines import run_multi_agent

st.set_page_config(page_title="ExecuGraph", page_icon="⧈", layout="wide")
st.title("⧈ ExecuGraph")
st.caption("A multi-agent, execution-grounded code synthesis framework.")


@st.cache_resource
def _build_deps() -> WorkflowDeps:
    cfg_path = Path(os.environ.get("EXECUGRAPH_CONFIG", "configs/default.yaml"))
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    p = build_backend(cfg["models"]["planner"])
    g = build_backend(cfg["models"]["generator"])
    r = build_backend(cfg["models"].get("reviewer", cfg["models"]["planner"]))
    o = build_backend(cfg["models"].get("optimizer", cfg["models"]["generator"]))
    e = build_backend(cfg["models"].get("explainer", cfg["models"]["planner"]))
    return WorkflowDeps(
        planner_llm=p, generator_llm=g, reviewer_llm=r, optimizer_llm=o, explainer_llm=e,
        cost=CostAccumulator(),
        timeout_s=cfg.get("execution", {}).get("timeout_s", 5.0),
    )


col1, col2 = st.columns([3, 1])
with col1:
    problem = st.text_area(
        "Problem statement",
        height=140,
        placeholder="Describe the backend / DSA problem you want a function for…",
    )
with col2:
    retry_budget = st.slider("Retry budget", 0, 4, 2)
    enable_planner = st.checkbox("Planner", value=True)
    enable_reviewer = st.checkbox("Reviewer", value=True)
    enable_optimizer = st.checkbox("Optimizer", value=True)

run = st.button("Run ExecuGraph", type="primary", disabled=not problem.strip())

if run:
    deps = _build_deps()
    p = Problem(
        id="adhoc",
        category="adhoc",
        source="user",
        statement=problem.strip(),
        primary_function="solve",
        signature_aliases=["solve", "main", "f"],
        tests=[],  # falls back to the LLM-generated test path
        selection_rationale="user-supplied",
    )
    with st.spinner("Running multi-agent workflow…"):
        out = run_multi_agent(
            p, deps,
            retry_budget=retry_budget,
            enable_planner=enable_planner,
            enable_reviewer=enable_reviewer,
            enable_optimizer=enable_optimizer,
        )

    ev = out.get("evaluation", {})
    if ev.get("passed"):
        st.success("Evaluator: passed.")
    else:
        st.error(f"Evaluator: failed ({ev.get('error_class', '?')}). See trace below.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", "passed" if ev.get("passed") else "failed")
    c2.metric("Retries used", out.get("retries", 0))
    c3.metric("LLM calls", out.get("cost", {}).get("calls", 0))
    c4.metric("Wallclock (s)", f"{out.get('cost', {}).get('wallclock_s', 0):.1f}")

    if out.get("plan"):
        with st.expander("Plan", expanded=False):
            st.write(out["plan"])
    st.subheader("Generated code")
    st.code(out.get("code", ""), language="python")
    if out.get("review"):
        with st.expander("Reviewer (advisory)", expanded=False):
            st.json(out["review"])
    with st.expander("Test results", expanded=False):
        st.json(ev.get("test_results", []))
    if out.get("explanation"):
        with st.expander("Explanation", expanded=False):
            st.write(out["explanation"])
    with st.expander("Execution trace (logs)", expanded=False):
        for line in out.get("logs", []):
            st.text(line)
