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
        if status == "completed":
            icon, bg, border = "✅", "#052e16", "#22c55e"
        elif status == "failed":
            icon, bg, border = "❌", "#431407", "#f97316"
        elif status == "available":
            icon, bg, border = ("🔓", "#0c2a4a", "#3b82f6") if active else ("🔓", "#0f1f3d", "#334155")
        else:
            icon, bg, border = "🔒", "#0a1625", "#1e2d45"
        return (
            f"<div style='padding:8px;border-radius:6px;background:{bg};"
            f"border:1.5px solid {border};text-align:center'>"
            f"<div style='font-size:15px;color:#e2e8f0'>"
            f"{icon} <strong style='font-size:14px'>{name}</strong></div></div>"
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
            psi = run_psi_query(selected)
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
                psi = run_psi_query(selected)
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
            zkp = run_zkp_attestation(selected)
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
                zkp = run_zkp_attestation(selected)
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
            df = pd.DataFrame(get_transaction_graph(selected))
            st.dataframe(df)
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

    psi = run_psi_query(selected)
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
