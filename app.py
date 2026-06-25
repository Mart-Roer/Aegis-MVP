import time
import math
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from backend import (
    run_psi_query, run_zkp_attestation, get_transaction_graph,
    get_consortium_stats, get_bank_entities, BANKS,
)

st.set_page_config(page_title="Aegis", layout="wide", page_icon="🛡️")

_CSS = """
<style>
#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}

[data-testid="stSidebar"] {
    background-color: #0f2044 !important;
    border-right: 1px solid #1e3a5f;
}

div.stButton > button {
    background-color: #f97316;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    padding: 0.45rem 1.2rem;
}
div.stButton > button:hover,
div.stButton > button:active {
    background-color: #ea580c !important;
    color: #ffffff !important;
    border: none !important;
}

hr { border-color: #1e3a5f !important; opacity: 0.5; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Case metadata — PSI / ZKP / graph data lives in backend.py
# ---------------------------------------------------------------------------

CASES = {
    "CUST-1047": {
        "type": "Import/export business",
        "alert_source": "Transaction monitoring",
        "alert_reason": "Trade payments inconsistent with expected business activity",
        "internal_risk": "High",
    },
    "CUST-2198": {
        "type": "Individual customer",
        "alert_source": "Transaction monitoring",
        "alert_reason": "Structured deposits followed by outbound transfers",
        "internal_risk": "Medium",
    },
    "CUST-3321": {
        "type": "SME",
        "alert_source": "Behavioural monitoring",
        "alert_reason": "Dormant account became active with rapid payment flows",
        "internal_risk": "High",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_amsterdam():
    return datetime.now(ZoneInfo("Europe/Amsterdam"))

def fmt_time(ts_iso):
    return datetime.fromisoformat(ts_iso).strftime("%H:%M")

def get_psi_result(case_id):
    psi = run_psi_query(case_id)
    if case_id == "CUST-1047":
        psi["match_count"] = 2
        psi["passed"] = psi["match_count"] >= 1
        psi["matched_banks"] = ["Bank Gamma", "Bank Delta"]
    else:
        psi["matched_banks"] = []
    return psi

def get_zkp_result(case_id):
    zkp = run_zkp_attestation(case_id)
    if case_id == "CUST-1047":
        zkp["anonymous_confirmations"] = 2
        zkp["aggregate_risk"] = "High"
        zkp["passed"] = zkp["anonymous_confirmations"] >= 1 and zkp["aggregate_risk"] == "High"
    return zkp

def build_stage3_network():
    nodes = {
        "alpha": {
            "label": "CUST-1047\nBank Alpha",
            "pos": (0.0, 0.0),
            "color": "#dc2626",
            "border": "#fca5a5",
            "hover": (
                "From: CUST-1047 / Bank Alpha<br>"
                "Disclosure level: Full disclosure<br>"
                "Reason: Originating flagged account at Bank Alpha"
            ),
        },
        "a_trading": {
            "label": "Entity A Trading\nBank Beta",
            "pos": (1.6, 1.0),
            "color": "#475569",
            "border": "#94a3b8",
            "hover": (
                "From: Entity A Trading / Bank Beta<br>"
                "Disclosure level: Controlled / pseudonymised<br>"
                "Reason: Included to understand the network pattern"
            ),
        },
        "logistics": {
            "label": "Logistics D\nBank Theta",
            "pos": (1.6, -1.2),
            "color": "#475569",
            "border": "#94a3b8",
            "hover": (
                "From: Logistics D / Bank Theta<br>"
                "Disclosure level: Controlled / pseudonymised<br>"
                "Reason: Included to understand the network pattern"
            ),
        },
        "consulting": {
            "label": "Entity C Consulting\nBank Zeta",
            "pos": (3.2, 0.0),
            "color": "#475569",
            "border": "#94a3b8",
            "hover": (
                "From: Entity C Consulting / Bank Zeta<br>"
                "Disclosure level: Controlled / pseudonymised<br>"
                "Reason: Included to understand the network pattern"
            ),
        },
        "account_b": {
            "label": "Account B\nBank Eta",
            "pos": (4.5, 0.0),
            "color": "#475569",
            "border": "#94a3b8",
            "hover": (
                "From: Account B / Bank Eta<br>"
                "Disclosure level: Controlled / pseudonymised<br>"
                "Reason: Included to understand the network pattern"
            ),
        },
        "gamma": {
            "label": "CUST-1047\nBank Gamma",
            "pos": (6.2, 1.0),
            "color": "#f97316",
            "border": "#fb923c",
            "hover": (
                "From: CUST-1047 / Bank Gamma<br>"
                "Disclosure level: Full disclosure<br>"
                "Reason: Same customer matched at another consortium bank"
            ),
        },
        "delta": {
            "label": "CUST-1047\nBank Delta",
            "pos": (6.2, -1.0),
            "color": "#f97316",
            "border": "#fb923c",
            "hover": (
                "From: CUST-1047 / Bank Delta<br>"
                "Disclosure level: Full disclosure<br>"
                "Reason: Same customer matched at another consortium bank"
            ),
        },
    }

    edges = [
        {
            "from": "alpha",
            "to": "a_trading",
            "value": 26.0,
            "label": "€26.0k / 4 tx",
            "display_label": "€26.0k",
            "show_label": True,
            "time_window": "10 days",
            "pattern": "repeated trade-looking payments",
            "disclosure": "Controlled / pseudonymised",
        },
        {
            "from": "a_trading",
            "to": "logistics",
            "value": 15.5,
            "label": "€15.5k / 3 tx",
            "display_label": "",
            "show_label": False,
            "time_window": "6 days",
            "pattern": "split onward transfer",
            "disclosure": "Controlled / pseudonymised",
        },
        {
            "from": "logistics",
            "to": "delta",
            "value": 14.9,
            "label": "€14.9k / 3 tx",
            "display_label": "€14.9k",
            "show_label": True,
            "time_window": "5 days",
            "pattern": "funds reappear at matched customer account",
            "disclosure": "Full disclosure",
        },
        {
            "from": "a_trading",
            "to": "consulting",
            "value": 9.2,
            "label": "€9.2k / 2 tx",
            "display_label": "",
            "show_label": False,
            "time_window": "4 days",
            "pattern": "shared intermediary in both paths",
            "disclosure": "Controlled / pseudonymised",
        },
        {
            "from": "alpha",
            "to": "consulting",
            "value": 17.5,
            "label": "€17.5k / 5 tx",
            "display_label": "€17.5k",
            "show_label": True,
            "time_window": "12 days",
            "pattern": "repeated service-looking payments",
            "disclosure": "Controlled / pseudonymised",
        },
        {
            "from": "consulting",
            "to": "account_b",
            "value": 10.8,
            "label": "€10.8k / 4 tx",
            "display_label": "",
            "show_label": False,
            "time_window": "4 days",
            "pattern": "possible transit/pass-through account",
            "disclosure": "Controlled / pseudonymised",
        },
        {
            "from": "account_b",
            "to": "gamma",
            "value": 10.3,
            "label": "€10.3k / 4 tx",
            "display_label": "€10.3k",
            "show_label": True,
            "time_window": "3 days",
            "pattern": "rapid onward movement to matched customer account",
            "disclosure": "Full disclosure",
        },
        {
            "from": "consulting",
            "to": "delta",
            "value": 6.1,
            "label": "€6.1k / 2 tx",
            "display_label": "",
            "show_label": False,
            "time_window": "2 days",
            "pattern": "secondary convergence into matched customer account",
            "disclosure": "Full disclosure",
        },
    ]

    fig = go.Figure()

    for edge in edges:
        x0, y0 = nodes[edge["from"]]["pos"]
        x1, y1 = nodes[edge["to"]]["pos"]
        width = max(1.5, min(5.5, edge["value"] / 5.5 + 1.5))

        hovertext = (
            f"<b>From:</b> {nodes[edge['from']]['label'].replace(chr(10), ' ')}<br>"
            f"<b>To:</b> {nodes[edge['to']]['label'].replace(chr(10), ' ')}<br>"
            f"<b>Aggregate value:</b> {edge['label'].split(' / ')[0]}<br>"
            f"<b>Transactions:</b> {edge['label'].split(' / ')[1]}<br>"
            f"<b>Time window:</b> {edge['time_window']}<br>"
            f"<b>Pattern signal:</b> {edge['pattern']}<br>"
            f"<b>Disclosure level:</b> {edge['disclosure']}"
        )

        fig.add_trace(go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line=dict(width=1.0, color="rgba(148,163,184,0.45)"),
            hoverinfo="text",
            text=[hovertext],
            showlegend=False,
        ))

        fig.add_annotation(
            x=x1,
            y=y1,
            ax=x0,
            ay=y0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=0.8,
            arrowwidth=width,
            arrowcolor="rgba(148,163,184,0.75)",
            opacity=0.88,
            standoff=16,
            startstandoff=12,
        )

        if edge["show_label"]:
            fig.add_annotation(
                x=(x0 + x1) / 2,
                y=(y0 + y1) / 2,
                text=edge["display_label"],
                showarrow=False,
                align="center",
                font=dict(size=11, color="#ffffff"),
                bgcolor="rgba(15,23,42,0.95)",
                bordercolor="#334155",
                borderwidth=1,
                borderpad=4,
                opacity=0.98,
                yshift=10,
            )

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_border = []
    node_hover = []
    for node_info in nodes.values():
        x, y = node_info["pos"]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node_info["label"])
        node_color.append(node_info["color"])
        node_border.append(node_info["border"])
        node_hover.append(node_info["hover"])

    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=54,
            color=node_color,
            line=dict(color=node_border, width=2),
        ),
        text=node_text,
        textposition="top center",
        textfont=dict(color="#f8fafc", size=11),
        hoverinfo="text",
        hovertext=node_hover,
        showlegend=False,
    ))

    fig.update_layout(
        title="Controlled Stage 3 network view",
        title_x=0.0,
        title_font=dict(size=16, color="#f8fafc"),
        plot_bgcolor="rgba(15,23,42,0.95)",
        paper_bgcolor="rgba(15,23,42,0.95)",
        margin=dict(l=10, r=10, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.4, 6.6]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.8, 1.6]),
        height=640,
    )

    return fig

def get_stage3_transactions():
    return [
        {
            "From": "CUST-1047 / Bank Alpha",
            "To": "Entity A Trading / Bank Beta",
            "Aggregate value": "€26.0k",
            "Number of transactions": "4 tx",
            "Time window": "10 days",
            "Pattern signal": "repeated trade-looking payments",
            "Disclosure level": "Controlled / pseudonymised",
        },
        {
            "From": "Entity A Trading / Bank Beta",
            "To": "Logistics D / Bank Theta",
            "Aggregate value": "€15.5k",
            "Number of transactions": "3 tx",
            "Time window": "6 days",
            "Pattern signal": "split onward transfer",
            "Disclosure level": "Controlled / pseudonymised",
        },
        {
            "From": "Logistics D / Bank Theta",
            "To": "CUST-1047 / Bank Delta",
            "Aggregate value": "€14.9k",
            "Number of transactions": "3 tx",
            "Time window": "5 days",
            "Pattern signal": "funds reappear at matched customer account",
            "Disclosure level": "Full disclosure",
        },
        {
            "From": "Entity A Trading / Bank Beta",
            "To": "Entity C Consulting / Bank Zeta",
            "Aggregate value": "€9.2k",
            "Number of transactions": "2 tx",
            "Time window": "4 days",
            "Pattern signal": "shared intermediary in both paths",
            "Disclosure level": "Controlled / pseudonymised",
        },
        {
            "From": "CUST-1047 / Bank Alpha",
            "To": "Entity C Consulting / Bank Zeta",
            "Aggregate value": "€17.5k",
            "Number of transactions": "5 tx",
            "Time window": "12 days",
            "Pattern signal": "repeated service-looking payments",
            "Disclosure level": "Controlled / pseudonymised",
        },
        {
            "From": "Entity C Consulting / Bank Zeta",
            "To": "Account B / Bank Eta",
            "Aggregate value": "€10.8k",
            "Number of transactions": "4 tx",
            "Time window": "4 days",
            "Pattern signal": "possible transit/pass-through account",
            "Disclosure level": "Controlled / pseudonymised",
        },
        {
            "From": "Account B / Bank Eta",
            "To": "CUST-1047 / Bank Gamma",
            "Aggregate value": "€10.3k",
            "Number of transactions": "4 tx",
            "Time window": "3 days",
            "Pattern signal": "rapid onward movement to matched customer account",
            "Disclosure level": "Full disclosure",
        },
        {
            "From": "Entity C Consulting / Bank Zeta",
            "To": "CUST-1047 / Bank Delta",
            "Aggregate value": "€6.1k",
            "Number of transactions": "2 tx",
            "Time window": "2 days",
            "Pattern signal": "secondary convergence into matched customer account",
            "Disclosure level": "Full disclosure",
        },
    ]

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "results" not in st.session_state:
    st.session_state["results"] = {}

def get_case_state(case_id):
    if case_id not in st.session_state["results"]:
        st.session_state["results"][case_id] = {
            "stage1_run": False, "stage1_pass": False,
            "stage2_run": False, "stage2_pass": False,
            "stage3_viewed": False,
            "active_stage": 1,
            "timeline": [{"ts": now_amsterdam().isoformat(), "text": "Case flagged by Bank Alpha"}],
        }
    return st.session_state["results"][case_id]

def save_case_state(case_id, state):
    st.session_state["results"][case_id] = state

def add_timeline_event(case_id, text):
    s = get_case_state(case_id)
    s["timeline"].append({"ts": now_amsterdam().isoformat(), "text": text})
    save_case_state(case_id, s)

# ---------------------------------------------------------------------------
# Sidebar — global, outside tabs
# ---------------------------------------------------------------------------

st.sidebar.title("Case queue")
st.sidebar.markdown("Select case")

selected = st.sidebar.selectbox("Select case", list(CASES.keys()))
entity = CASES[selected]

st.sidebar.markdown("**Case summary**")
st.sidebar.write(f"- ID: {selected}")
st.sidebar.write(f"- Type: {entity['type']}")
st.sidebar.write(f"- Alert source: {entity['alert_source']}")
st.sidebar.write(f"- Alert reason: {entity['alert_reason']}")
st.sidebar.markdown("---")
st.sidebar.caption("Bank Alpha · Investigations interface")

# Normalise case state
state = get_case_state(selected)
if state["stage1_run"] and not state["stage1_pass"] and state.get("active_stage", 1) > 1:
    state["active_stage"] = 1
if state["stage2_run"] and not state["stage2_pass"] and state.get("active_stage", 1) > 2:
    state["active_stage"] = 2
save_case_state(selected, state)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_inv, tab_net = st.tabs(["🔍 Investigator", "🌐 Consortium Network"])

# ============================================================
# TAB 1 — Investigator (Bank Alpha view)
# ============================================================

with tab_inv:

    st.title("Aegis Investigator")
    st.markdown("Investigation workspace")

    badge_flagged  = "<div style='margin-bottom:6px'><span style='background:#7f1d1d;color:#fca5a5;padding:6px 10px;border-radius:12px;font-weight:600'>Flagged</span></div>"
    badge_eligible = "<div><span style='background:#1e3a5f;color:#93c5fd;padding:6px 10px;border-radius:12px'>Eligible for consortium check</span></div>"

    st.header(selected)
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.write(f"- Type: **{entity['type']}**")
        st.write(f"- Alert source: **{entity['alert_source']}**")
        st.write(f"- Alert reason: **{entity['alert_reason']}**")
    with col_b:
        st.markdown(badge_flagged + badge_eligible, unsafe_allow_html=True)

    st.markdown("---")

    def render_stage_label(name, status, active=False):
        lock_closed = (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="11" width="18" height="10" rx="2" ry="2"/>'
            '<path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
        )
        lock_open = (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="11" width="18" height="10" rx="2" ry="2"/>'
            '<path d="M8 11V7a4 4 0 0 1 8-1"/><path d="M8 11h8"/></svg>'
        )
        check_mark = (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M5 13l4 4L19 7"/></svg>'
        )
        if status == "completed":
            icon = check_mark
            icon_color = "#22c55e"
            bg = "#052e16"
            border = "#22c55e"
        elif status == "available":
            icon = lock_open
            icon_color = "#93c5fd" if active else "#94a3b8"
            bg = "#0c2a4a" if active else "#0f1f3d"
            border = "#3b82f6" if active else "#334155"
        else:
            icon = lock_closed
            icon_color = "#94a3b8"
            bg = "#0a1625"
            border = "#1e2d45"

        return (
            f"<div style='padding:10px;border-radius:8px;background:{bg};"
            f"border:1.5px solid {border};text-align:center'>"
            f"<div style='display:flex;align-items:center;justify-content:center;gap:10px'>"
            f"<span style='color:{icon_color};display:inline-flex;align-items:center;"
            f"justify-content:center;width:34px;height:34px'>{icon}</span>"
            f"<span style='font-size:14px;color:#e2e8f0;line-height:1.2;'>{name}</span>"
            f"</div></div>"
        )

    s1 = "available" if not state["stage1_run"] else ("completed" if state["stage1_pass"] else "failed")
    s2 = "locked"
    if s1 == "completed":
        s2 = "available" if not state["stage2_run"] else ("completed" if state["stage2_pass"] else "failed")
    s3 = "locked"
    if s2 == "completed":
        s3 = "available" if not state["stage3_viewed"] else "completed"

    active = state.get("active_stage", 1)
    if active == 2 and s2 == "locked":
        active = 1
    if active == 3 and s3 == "locked":
        active = 1
    state["active_stage"] = active
    save_case_state(selected, state)

    tc1, tc2, tc3 = st.columns(3)
    tc1.markdown(render_stage_label("Stage 1 — Consortium Match Check", s1, active == 1), unsafe_allow_html=True)
    tc2.markdown(render_stage_label("Stage 2 — Risk Attestation",       s2, active == 2), unsafe_allow_html=True)
    tc3.markdown(render_stage_label("Stage 3 — Controlled Network View",s3, active == 3), unsafe_allow_html=True)

    st.markdown("---")

    def goto_stage(n):
        ns = get_case_state(selected)
        if n == 2 and ns["stage1_run"] and ns["stage1_pass"]:
            ns["active_stage"] = 2
        if n == 3 and ns["stage2_run"] and ns["stage2_pass"]:
            ns["active_stage"] = 3
        save_case_state(selected, ns)
        st.rerun()

    def show_stage1():
        st.subheader("Stage 1 — Consortium Match Check")
        st.write("Check whether this entity appears across the consortium.")
        st.info("Institution identities are not disclosed. Only the match count is returned.")
        if state["stage1_run"]:
            psi = get_psi_result(selected)
            st.write(f"- Match count: **{psi['match_count']}**")
            if state["stage1_pass"]:
                st.success("Match confirmed — escalation available.")
                if st.button("Continue to risk attestation", key="to_stage2"):
                    goto_stage(2)
            else:
                st.error("No consortium match found. Cross-bank escalation is not available for this case.")
        else:
            if st.button("Run match check"):
                with st.spinner("Checking consortium matches..."):
                    time.sleep(0.6)
                psi = get_psi_result(selected)
                ns = get_case_state(selected)
                ns.update({
                    "stage1_run": True, "stage1_pass": psi["passed"],
                    "stage2_run": False, "stage2_pass": False,
                    "stage3_viewed": False, "active_stage": 1,
                })
                save_case_state(selected, ns)
                add_timeline_event(selected, "Consortium match check completed")
                if not psi["passed"]:
                    add_timeline_event(selected, "No consortium match found")
                st.rerun()

    def show_stage2():
        st.subheader("Stage 2 — Risk Attestation")
        st.write("Verify whether anonymous consortium risk signals exist for this entity.")
        st.info("Risk signals are aggregated and source institutions remain hidden.")
        if not (state["stage1_run"] and state["stage1_pass"]):
            st.warning("Risk attestation is locked until consortium match is confirmed.")
            return
        if state["stage2_run"]:
            zkp = get_zkp_result(selected)
            st.write(f"- Anonymous confirmations: **{zkp['anonymous_confirmations']}**")
            st.write(f"- Aggregate concern: **{zkp['aggregate_risk']}**")
            if state["stage2_pass"]:
                st.success("Attestation verified — high concern confirmed.")
                if st.button("Continue to controlled network view", key="to_stage3"):
                    goto_stage(3)
            else:
                st.error("Consortium presence found, but risk attestation not sufficient for network disclosure.")
        else:
            if st.button("Verify risk attestation"):
                with st.spinner("Verifying attestation..."):
                    time.sleep(0.6)
                zkp = get_zkp_result(selected)
                ns = get_case_state(selected)
                ns.update({"stage2_run": True, "stage2_pass": zkp["passed"], "active_stage": 2, "stage3_viewed": False})
                save_case_state(selected, ns)
                add_timeline_event(selected, "Risk attestation verified" if zkp["passed"] else "Controlled network view not authorised")
                st.rerun()

    def show_stage3():
        st.subheader("Stage 3 — Controlled Network View")
        st.write("Review approved cross-institutional network indicators.")
        st.info("Network details are available only after prior-stage approval.")
        if not (state["stage1_run"] and state["stage1_pass"] and state["stage2_run"] and state["stage2_pass"]):
            st.warning("Controlled network view is locked until prior stages complete.")
            return
        if state.get("stage3_viewed"):
            st.success("Controlled network view opened.")
            psi = get_psi_result(selected)
            zkp = get_zkp_result(selected)

            summary_card = f"""
            <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:18px;margin-bottom:18px'>
                <div style='color:#7dd3fc;font-size:12px;font-weight:700;letter-spacing:0.08em;margin-bottom:10px'>Investigation summary</div>
                <div style='color:#e2e8f0;font-size:14px;font-weight:700;margin-bottom:12px'>Selected case: {selected}</div>
                <div style='color:#cbd5e1;font-size:13px;line-height:1.7'>
                    Originating institution: Bank Alpha<br>
                    Stage 1 result: Match found at {psi["match_count"]} other consortium banks<br>
                    Matched institutions: {", ".join(psi["matched_banks"] or ["N/A"])}<br>
                    Stage 2 result: {zkp["anonymous_confirmations"]} anonymous confirmations<br>
                    Aggregate concern: {zkp["aggregate_risk"]}<br>
                    Disclosure mode: Controlled Stage 3 network view unlocked
                </div>
            </div>
            """

            insight_card = f"""
            <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:18px;margin-bottom:18px'>
                <div style='color:#f8fafc;font-size:13px;font-weight:700;margin-bottom:10px'>Network insight</div>
                <div style='color:#cbd5e1;font-size:13px;line-height:1.7'>
                    Bank Alpha initially saw only outgoing payments from <strong>CUST-1047</strong>. Stage 3 reveals that these funds are split through intermediaries and reappear in matched <strong>CUST-1047</strong> accounts at Bank Gamma and Bank Delta. This indicates a cross-bank layering and convergence pattern that would not be visible to a single institution.
                </div>
            </div>
            """

            legend_card = """
            <div style='display:flex;flex-wrap:wrap;gap:12px;margin-bottom:16px'>
                <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;max-width:260px;'>
                    <div style='color:#ef4444;font-size:13px;font-weight:700;margin-bottom:6px'>Red node</div>
                    <div style='color:#cbd5e1;font-size:13px'>Originating flagged customer account</div>
                </div>
                <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;max-width:260px;'>
                    <div style='color:#f97316;font-size:13px;font-weight:700;margin-bottom:6px'>Orange node</div>
                    <div style='color:#cbd5e1;font-size:13px'>Same customer at another matched bank</div>
                </div>
                <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;max-width:260px;'>
                    <div style='color:#94a3b8;font-size:13px;font-weight:700;margin-bottom:6px'>Grey node</div>
                    <div style='color:#cbd5e1;font-size:13px'>Controlled / pseudonymised counterparty</div>
                </div>
                <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;max-width:260px;'>
                    <div style='color:#cbd5e1;font-size:13px;font-weight:700;margin-bottom:6px'>Arrow direction</div>
                    <div style='color:#cbd5e1;font-size:13px'>Observed money flow</div>
                </div>
            </div>
            """

            st.markdown("<div style='display:flex;gap:18px;flex-wrap:wrap'>"
                        f"<div style='flex:1 1 420px'>{summary_card}</div>"
                        f"<div style='flex:1 1 320px'>{insight_card}</div>"
                        "</div>", unsafe_allow_html=True)

            st.markdown(legend_card, unsafe_allow_html=True)
            fig = build_stage3_network()
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            st.markdown(
                "Each arrow aggregates multiple transactions over a short time window. Thicker arrows indicate higher total value moved. "
                "Red nodes show the originating flagged account. Orange nodes show matched accounts of the same customer at other banks. "
                "Grey nodes are controlled / pseudonymised counterparties included because they are necessary to understand the network pattern."
            )

            st.markdown(
                """
                <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:16px;margin-top:18px'>
                    <div style='color:#7dd3fc;font-size:12px;font-weight:700;letter-spacing:0.08em;margin-bottom:10px'>Diagram legend</div>
                    <div style='color:#cbd5e1;font-size:13px;line-height:1.7'>
                        <strong style='color:#ef4444'>Red node</strong>: originating flagged customer account<br>
                        <strong style='color:#f97316'>Orange node</strong>: same customer at another matched bank<br>
                        <strong style='color:#94a3b8'>Grey node</strong>: controlled / pseudonymised counterparty<br>
                        <strong>Arrow direction</strong>: observed money flow<br>
                        <strong>Thicker arrow</strong>: higher aggregate value<br>
                        <strong>Hover</strong>: transaction count, time window, and pattern signal
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            transactions = pd.DataFrame(get_stage3_transactions())
            st.dataframe(transactions, use_container_width=True, hide_index=True)

            st.info(
                "Each edge aggregates several transactions over a short time window. "
                "Thicker lines indicate higher total value. Full-disclosure nodes meet "
                "the risk threshold after Stage 1 and Stage 2. Controlled nodes remain "
                "pseudonymised but are included because they are necessary to understand "
                "the transaction pattern."
            )
        else:
            if st.button("Open controlled network view"):
                ns = get_case_state(selected)
                ns["stage3_viewed"] = True
                ns["active_stage"] = 3
                save_case_state(selected, ns)
                add_timeline_event(selected, "Controlled network view opened")
                st.rerun()

    active = get_case_state(selected).get("active_stage", 1)
    if active == 1:
        show_stage1()
    elif active == 2:
        show_stage2()
    elif active == 3:
        show_stage3()

    st.markdown("---")

    left, right = st.columns([1.6, 1])
    with left:
        st.markdown("### Case timeline · Amsterdam time")
        for ev in get_case_state(selected).get("timeline", []):
            st.write(f"- {fmt_time(ev['ts'])} — {ev['text']}")
    with right:
        st.markdown("### Case details")
        st.write(f"- ID: **{selected}**")
        st.write(f"- Type: **{entity['type']}**")
        st.write(f"- Alert source: **{entity['alert_source']}**")
        st.write(f"- Alert reason: **{entity['alert_reason']}**")
        st.write(f"- Case status: **Flagged**")
        st.write(f"- Aegis status: **Eligible for consortium check**")

    st.markdown("---")
    st.caption("Prototype environment · No live customer data")

# ============================================================
# TAB 2 — Consortium Network (Aegis internal view)
# ============================================================

with tab_net:

    st.title("Consortium Network")
    st.markdown(
        f"Network topology and protocol signal flow · Aegis internal view · "
        f"Active case: **{selected}**"
    )
    st.markdown("---")

    # ── Topology diagram ─────────────────────────────────────────────────

    stats    = get_consortium_stats()
    bank_ids = list(BANKS.keys())
    n        = len(bank_ids)
    angles   = [2 * math.pi * i / n - math.pi / 2 for i in range(n)]
    bx       = [math.cos(a) for a in angles]
    by       = [math.sin(a) for a in angles]

    edge_x, edge_y = [], []
    for x, y in zip(bx, by):
        edge_x += [x, 0, None]
        edge_y += [y, 0, None]

    _RC = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}

    def _bank_hover(bank_id: str) -> str:
        bank = BANKS[bank_id]
        ents = get_bank_entities(bank_id)
        lines = [
            f"<b>{bank['name']} · {bank['country']}</b>",
            f"<span style='color:#94a3b8'>{len(ents)} monitored entities · internal view only</span>",
            " ",
        ]
        for e in ents:
            color = _RC.get(e["Risk"], "#94a3b8")
            lines.append(
                f"<b>{e['ID']}</b>  {e['Name']}<br>"
                f"<span style='color:#64748b'>{e['Type']} · {e['Country']} · </span>"
                f"<span style='color:{color}'><b>{e['Risk']}</b></span>"
            )
        lines += [
            " ",
            "<span style='color:#475569;font-size:11px'>"
            "🔒 This data is not shared with other consortium members</span>",
        ]
        return "<br>".join(lines)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=1.5, color="#2e5f8a"),
        hoverinfo="none",
    ))

    fig.add_trace(go.Scatter(
        x=bx, y=by,
        mode="markers+text",
        marker=dict(size=44, color="#1e3a5f", line=dict(color="#60a5fa", width=2)),
        text=[BANKS[b]["name"] for b in bank_ids],
        textposition="top center",
        textfont=dict(color="#e2e8f0", size=12),
        hovertext=[_bank_hover(b) for b in bank_ids],
        hoverinfo="text",
        hoverlabel=dict(bgcolor="#0f2044", bordercolor="#1e3a5f", font=dict(size=12, color="#e2e8f0")),
        name="",
    ))

    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode="markers+text",
        marker=dict(size=64, color="#f97316", line=dict(color="#ea580c", width=3)),
        text=["Aegis"],
        textposition="middle center",
        textfont=dict(color="#ffffff", size=14),
        hovertext=[
            "<b>Aegis</b><br>"
            "Privacy-preserving AML intermediary<br>"
            "Processes hashed tokens only<br>"
            "No raw entity data ever stored"
        ],
        hoverinfo="text",
        hoverlabel=dict(bgcolor="#7c2d12", bordercolor="#f97316", font=dict(size=12, color="#fed7aa")),
        name="",
    ))

    fig.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=10, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.7, 1.7]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.7, 1.7]),
        height=460,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Protocol signal flow ──────────────────────────────────────────────

    st.markdown("### Protocol signal flow")
    st.markdown(
        f"How Aegis enables cross-bank AML collaboration without sharing raw data — "
        f"illustrated for case **{selected}**."
    )

    psi = get_psi_result(selected)
    zkp = run_zkp_attestation(selected)
    stage3_unlocked = psi["passed"] and zkp["passed"]

    # helper: one anonymous signal row in the ZKP card
    def _signal_row(level: str) -> str:
        color = _RC.get(level, "#94a3b8")
        return (
            f"<div style='display:flex;align-items:center;gap:8px;margin:3px 0'>"
            f"<div style='background:#1e3a5f;border-radius:3px;padding:2px 8px;"
            f"font-size:11px;color:#475569;min-width:72px'>Bank ████</div>"
            f"<div style='color:{color};font-size:13px;font-weight:600'>⚡ {level}</div>"
            f"<div style='color:#475569;font-size:11px'>→ Aegis</div>"
            f"</div>"
        )

    # ── Stage 1 card ──
    s1_card = f"""
    <div style='background:#0f1f3d;border:1px solid #1e3a5f;border-radius:10px;padding:16px'>
        <div style='color:#60a5fa;font-size:11px;font-weight:700;letter-spacing:0.08em;margin-bottom:4px'>STAGE 1</div>
        <div style='color:#e2e8f0;font-size:15px;font-weight:700;margin-bottom:14px'>PSI — Match Check</div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Bank Alpha sends</div>
        <div style='background:#0a1625;border:1px solid #22c55e;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            <div style='color:#86efac;font-size:13px'>SHA-256 hash of entity ID</div>
            <div style='color:#4ade80;font-family:monospace;font-size:11px'>{psi["psi_token"]}...</div>
            <div style='color:#166534;font-size:11px;margin-top:2px'>Raw ID never leaves Bank Alpha</div>
        </div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Aegis computes</div>
        <div style='background:#1c1005;border:1px solid #f97316;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            <div style='color:#fdba74;font-size:13px'>Intersection count</div>
            <div style='color:#92400e;font-size:11px'>Checks hash against {n - 1} member hash sets</div>
            <div style='color:#92400e;font-size:11px'>Aegis never sees raw entity data</div>
        </div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Bank Alpha receives</div>
        <div style='background:#0a1625;border:1px solid #22c55e;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            <div style='color:#86efac;font-size:13px'>Match count: <b>{psi["match_count"]}</b></div>
            <div style='color:#166534;font-size:11px'>No bank names · No entity data</div>
        </div>

        <div style='background:#1e3a5f;border-radius:6px;padding:8px 10px'>
            <div style='color:#93c5fd;font-size:11px'>🔒 Other banks learn nothing. No member knows that another bank queried.</div>
        </div>
    </div>
    """

    # ── Stage 2 card ──
    anon_signals = zkp.get("anonymous_signals", [])
    if anon_signals:
        signal_rows = "".join(_signal_row(lvl) for lvl in anon_signals)
        signal_rows += f"<div style='color:#475569;font-size:11px;margin-top:6px'>↓ Aggregated by Aegis — bank identities discarded</div>"
    else:
        signal_rows = "<div style='color:#475569;font-size:12px;font-style:italic'>No signals received for this case</div>"

    s2_card = f"""
    <div style='background:#0f1f3d;border:1px solid #1e3a5f;border-radius:10px;padding:16px'>
        <div style='color:#60a5fa;font-size:11px;font-weight:700;letter-spacing:0.08em;margin-bottom:4px'>STAGE 2</div>
        <div style='color:#e2e8f0;font-size:15px;font-weight:700;margin-bottom:14px'>ZKP — Risk Attestation</div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Bank Alpha sends</div>
        <div style='background:#0a1625;border:1px solid #22c55e;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            <div style='color:#86efac;font-size:13px'>Same SHA-256 hash</div>
            <div style='color:#4ade80;font-family:monospace;font-size:11px'>{psi["psi_token"]}...</div>
        </div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Anonymous signals from matching banks</div>
        <div style='background:#0a1625;border:1px solid #1e3a5f;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            {signal_rows}
        </div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Bank Alpha receives</div>
        <div style='background:#0a1625;border:1px solid #22c55e;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            <div style='color:#86efac;font-size:13px'>Confirmations: <b>{zkp["anonymous_confirmations"]}</b> · Aggregate risk: <b>{zkp["aggregate_risk"]}</b></div>
            <div style='color:#166534;font-size:11px'>Source banks not attributable</div>
        </div>

        <div style='background:#1e3a5f;border-radius:6px;padding:8px 10px'>
            <div style='color:#93c5fd;font-size:11px'>🔒 Risk signals are structurally unlinkable to their source institutions.</div>
        </div>
    </div>
    """

    # ── Stage 3 card ──
    if stage3_unlocked:
        s3_gate = (
            "<div style='background:#052e16;border:1px solid #22c55e;border-radius:6px;"
            "padding:8px 12px;margin-bottom:10px'>"
            "<div style='color:#86efac;font-size:13px'>🔓 Unlocked for this case</div>"
            "<div style='color:#166534;font-size:11px'>Stages 1 and 2 both passed their thresholds</div>"
            "</div>"
        )
    else:
        s3_gate = (
            "<div style='background:#0c1a2e;border:1px solid #334155;border-radius:6px;"
            "padding:8px 12px;margin-bottom:10px'>"
            "<div style='color:#64748b;font-size:13px'>🔒 Locked for this case</div>"
            "<div style='color:#475569;font-size:11px'>Proportionality threshold not met</div>"
            "</div>"
        )

    s3_card = f"""
    <div style='background:#0f1f3d;border:1px solid #1e3a5f;border-radius:10px;padding:16px'>
        <div style='color:#60a5fa;font-size:11px;font-weight:700;letter-spacing:0.08em;margin-bottom:4px'>STAGE 3</div>
        <div style='color:#e2e8f0;font-size:15px;font-weight:700;margin-bottom:14px'>Controlled Network View</div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Unlocks when</div>
        <div style='background:#0a1625;border:1px solid #1e3a5f;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            <div style='color:#cbd5e1;font-size:13px'>Stage 1 ≥ 1 match</div>
            <div style='color:#cbd5e1;font-size:13px'>Stage 2 aggregate = High</div>
        </div>

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>Current status</div>
        {s3_gate}

        <div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>If unlocked, Bank Alpha receives</div>
        <div style='background:#0a1625;border:1px solid #1e3a5f;border-radius:6px;padding:8px 12px;margin-bottom:10px'>
            <div style='color:#94a3b8;font-size:13px'>Cross-bank transaction network</div>
            <div style='color:#475569;font-size:11px'>Account IDs anonymised · Synthetic demo data</div>
        </div>

        <div style='background:#1e3a5f;border-radius:6px;padding:8px 10px'>
            <div style='color:#93c5fd;font-size:11px'>🔒 Proportionality gate: disclosure only when prior stages justify escalation. GDPR Art. 6(1)(c).</div>
        </div>
    </div>
    """

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(s1_card, unsafe_allow_html=True)
    with c2:
        st.markdown(s2_card, unsafe_allow_html=True)
    with c3:
        st.markdown(s3_card, unsafe_allow_html=True)

    st.markdown("---")

    # ── Consortium member table ───────────────────────────────────────────

    st.markdown("### Consortium members")
    rows = [
        {
            "Bank":               BANKS[b]["name"],
            "Country":            BANKS[b]["country"],
            "Monitored entities": stats[b]["monitored_count"],
            "Status":             "Active",
        }
        for b in bank_ids
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption("Aegis internal view · Not visible to member institutions")
