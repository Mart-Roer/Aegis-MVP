import time
import math
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from backend import run_zkp_attestation
from backend_stage1 import run_stage1_psi_cardinality

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
    stage1 = run_stage1_psi_cardinality(case_id, "Bank Alpha")
    psi = {
        "stage": stage1.get("stage", 1),
        "entity_id": stage1.get("entity_id", case_id),
        "match_count": stage1.get("matched_bank_count", 0),
        "passed": stage1.get("matched_bank_count", 0) >= 1,
        "matched_banks": [],
        "token_preview": stage1.get("technical_trace", {}).get("query_token_preview"),
        "psi_token": stage1.get("technical_trace", {}).get("query_token_preview"),
    }
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
            "label": "CUST-1047<br><span style='font-size:11px;color:#94a3b8'>Bank Alpha</span>",
            "bank": "Bank Alpha",
            "type": "origin",
            "x": 0.08,
            "y": 0.52,
            "color": "#dc2626",
        },
        "entity_a": {
            "label": "Entity A Trading<br><span style='font-size:11px;color:#94a3b8'>Bank Beta</span>",
            "bank": "Bank Beta",
            "type": "intermediary",
            "x": 0.32,
            "y": 0.78,
            "color": "#475569",
        },
        "logistics": {
            "label": "Logistics D<br><span style='font-size:11px;color:#94a3b8'>Bank Theta</span>",
            "bank": "Bank Theta",
            "type": "intermediary",
            "x": 0.56,
            "y": 0.78,
            "color": "#475569",
        },
        "delta": {
            "label": "CUST-1047<br><span style='font-size:11px;color:#94a3b8'>Matched account · Bank Delta</span>",
            "bank": "Matched account · Bank Delta",
            "type": "matched",
            "x": 0.88,
            "y": 0.78,
            "color": "#f97316",
        },
        "consulting": {
            "label": "Entity C Consulting<br><span style='font-size:11px;color:#94a3b8'>Bank Zeta</span>",
            "bank": "Bank Zeta",
            "type": "intermediary",
            "x": 0.32,
            "y": 0.28,
            "color": "#475569",
        },
        "account_b": {
            "label": "Account B<br><span style='font-size:11px;color:#94a3b8'>Bank Eta</span>",
            "bank": "Bank Eta",
            "type": "intermediary",
            "x": 0.56,
            "y": 0.28,
            "color": "#475569",
        },
        "gamma": {
            "label": "CUST-1047<br><span style='font-size:11px;color:#94a3b8'>Matched account · Bank Gamma</span>",
            "bank": "Matched account · Bank Gamma",
            "type": "matched",
            "x": 0.88,
            "y": 0.28,
            "color": "#f97316",
        },
    }

    edges = [
        ("alpha", "entity_a", "€26.0k · 4 tx", 26000, "4 tx"),
        ("entity_a", "logistics", "€15.5k · 3 tx", 15500, "3 tx"),
        ("logistics", "delta", "€14.9k · 3 tx", 14900, "3 tx"),
        ("alpha", "consulting", "€17.5k · 5 tx", 17500, "5 tx"),
        ("consulting", "account_b", "€10.8k · 4 tx", 10800, "4 tx"),
        ("account_b", "gamma", "€10.3k · 4 tx", 10300, "4 tx"),
    ]

    label_positions = {
        ("alpha", "entity_a"): {"x": 0.20, "y": 0.88},
        ("entity_a", "logistics"): {"x": 0.44, "y": 0.88},
        ("logistics", "delta"): {"x": 0.72, "y": 0.88},
        ("alpha", "consulting"): {"x": 0.20, "y": 0.38},
        ("consulting", "account_b"): {"x": 0.44, "y": 0.38},
        ("account_b", "gamma"): {"x": 0.72, "y": 0.38},
    }

    fig = go.Figure()

    for source, target, label, amount, tx in edges:
        x0, y0 = nodes[source]["x"], nodes[source]["y"]
        x1, y1 = nodes[target]["x"], nodes[target]["y"]
        width = max(1.5, min(4.0, 1.0 + amount / 7000))

        hovertext = (
            f"From: {nodes[source]['label'].replace('<br>', ' ')}<br>"
            f"To: {nodes[target]['label'].replace('<br>', ' ')}<br>"
            f"Amount: {label.split(' · ')[0]}<br>"
            f"Transactions: {tx}<br>"
            f"Time window: {'10 days' if source == 'alpha' and target == 'entity_a' else '6 days' if source == 'entity_a' and target == 'logistics' else '5 days' if source == 'logistics' and target == 'delta' else '12 days' if source == 'alpha' and target == 'consulting' else '4 days' if source == 'consulting' and target == 'account_b' else '3 days'}<br>"
            f"Pattern signal: {'Trade-looking payment from flagged customer' if source == 'alpha' and target == 'entity_a' else 'Funds moved onward through intermediary' if source == 'entity_a' and target == 'logistics' else 'Funds reappear at matched customer account' if source == 'logistics' and target == 'delta' else 'Service-looking payment from flagged customer' if source == 'alpha' and target == 'consulting' else 'Possible pass-through account' if source == 'consulting' and target == 'account_b' else 'Rapid onward movement to matched customer account'}<br>"
            f"Disclosure level: {'Full disclosure' if target in ['delta', 'gamma'] else 'Controlled / pseudonymised'}"
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
            arrowhead=3,
            arrowsize=0.75,
            arrowwidth=width,
            arrowcolor="rgba(148,163,184,0.8)",
            opacity=0.9,
            standoff=14,
            startstandoff=8,
        )

        if (source, target) in label_positions:
            pos = label_positions[(source, target)]
            fig.add_annotation(
                x=pos["x"],
                y=pos["y"],
                text=label,
                showarrow=False,
                font=dict(size=11, color="#ffffff"),
                bgcolor="#0f172a",
                bordercolor="#334155",
                borderwidth=1,
                borderpad=5,
                opacity=0.95,
            )

    node_x = [node["x"] for node in nodes.values()]
    node_y = [node["y"] for node in nodes.values()]
    node_text = [node["label"] for node in nodes.values()]
    node_hover = [
        f"{node['label'].replace('<br>', ' ')}<br>"
        f"Bank: {node['bank']}<br>"
        f"Disclosure level: {'Full disclosure' if node['type'] != 'intermediary' else 'Controlled / pseudonymised'}"
        for node in nodes.values()
    ]
    node_colors = [node["color"] for node in nodes.values()]

    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(size=58, color=node_colors, line=dict(color="#0f172a", width=2)),
        text=node_text,
        textposition="top center",
        textfont=dict(color="#f8fafc", size=12),
        hoverinfo="text",
        hovertext=node_hover,
        showlegend=False,
    ))

    fig.update_layout(
        title="CUST-1047 Network View",
        title_x=0.0,
        title_font=dict(size=16, color="#f8fafc"),
        paper_bgcolor="rgba(15,23,42,0.95)",
        plot_bgcolor="rgba(15,23,42,0.95)",
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0.0, 1.0]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0.0, 1.0]),
        height=600,
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
        },
        {
            "From": "Entity A Trading / Bank Beta",
            "To": "Logistics D / Bank Theta",
            "Aggregate value": "€15.5k",
            "Number of transactions": "3 tx",
            "Time window": "6 days",
            "Pattern signal": "split onward transfer",
        },
        {
            "From": "Logistics D / Bank Theta",
            "To": "CUST-1047 / Bank Delta",
            "Aggregate value": "€14.9k",
            "Number of transactions": "3 tx",
            "Time window": "5 days",
            "Pattern signal": "funds reappear at matched customer",
        },
        {
            "From": "CUST-1047 / Bank Alpha",
            "To": "Entity C Consulting / Bank Zeta",
            "Aggregate value": "€17.5k",
            "Number of transactions": "5 tx",
            "Time window": "12 days",
            "Pattern signal": "repeated service-looking payments",
        },
        {
            "From": "Entity C Consulting / Bank Zeta",
            "To": "Account B / Bank Eta",
            "Aggregate value": "€10.8k",
            "Number of transactions": "4 tx",
            "Time window": "4 days",
            "Pattern signal": "possible transit/pass-through account",
        },
        {
            "From": "Account B / Bank Eta",
            "To": "CUST-1047 / Bank Gamma",
            "Aggregate value": "€10.3k",
            "Number of transactions": "4 tx",
            "Time window": "3 days",
            "Pattern signal": "rapid onward movement to matched customer",
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
# Investigator view
# ---------------------------------------------------------------------------

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

        left_col, right_col = st.columns([3, 2])
        with left_col:
            st.markdown(
                """
                <div style='background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:18px'>
                    <div style='color:#7dd3fc;font-size:12px;font-weight:700;letter-spacing:0.08em;margin-bottom:10px'>
                        Investigation summary
                    </div>
                    <div style='color:#cbd5e1;font-size:13px;line-height:1.8'>
                        Selected case: <strong>CUST-1047</strong><br>
                        Originating institution: <strong>Bank Alpha</strong><br>
                        Stage 1 result: <strong>Match found at 2 other consortium banks</strong><br>
                        Stage 2 result: <strong>2 anonymous confirmations</strong><br>
                        Aggregate concern: <strong>High</strong><br>
                        Disclosure mode: <strong>Controlled Stage 3 network view unlocked</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right_col:
            metric_a, metric_b = st.columns(2)
            metric_a.metric("Matched banks", "2")
            metric_b.metric("Intermediary entities", "4")
            st.metric("Reappearing value", "€25,200")

        fig = build_stage3_network()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        legend_cols = st.columns(4)
        legend_items = [
            ("Red node", "Originating flagged customer account", "#ef4444"),
            ("Orange node", "Same customer at another matched bank", "#f97316"),
            ("Grey node", "Controlled / pseudonymised counterparty", "#94a3b8"),
            ("Arrow direction", "Observed money flow", "#cbd5e1"),
        ]
        for col, (title, desc, color) in zip(legend_cols, legend_items):
            col.markdown(
                f"""
                <div style='display:inline-flex;flex-direction:column;align-items:flex-start;
                            white-space:nowrap;background:#0f172a;border:1px solid #1e293b;
                            border-radius:10px;padding:10px 16px;margin-bottom:8px;line-height:1.3;'>
                    <div style='font-size:12px;font-weight:700;color:{color};margin-bottom:4px'>
                        {title}
                    </div>
                    <div style='color:#cbd5e1;font-size:13px'>
                        {desc}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### CUST-1047 Transactions Database")
        transactions = pd.DataFrame(get_stage3_transactions())
        st.dataframe(transactions, use_container_width=True, hide_index=True)
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
