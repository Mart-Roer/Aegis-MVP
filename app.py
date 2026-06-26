import time
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd
from aegis_backend import get_backend  # real consortium/Merkle/routing checks

st.set_page_config(page_title="Aegis Investigator", layout="wide")

# --- Synthetic in-code dataset (case queue) ---
SYNTHETIC_ENTITIES = {
    "CUST-1047": {
        "type": "Import/export business",
        "alert_source": "Transaction monitoring",
        "alert_reason": "Trade payments inconsistent with expected business activity",
        "internal_risk": "High",
        "matching_banks": 3,
        "anonymous_confirmations": 2,
        "aggregate_risk": "High",
        "transactions": [
            {"from": "CUST-1047", "to": "Entity A", "amount": 25000, "note": "trade payments"},
            {"from": "Entity A", "to": "Account B", "amount": 24000, "note": "circular transfer"},
            {"from": "Account B", "to": "Entity C", "amount": 23000, "note": "repeat payments"},
        ],
    },
    "CUST-2198": {
        "type": "Individual customer",
        "alert_source": "Transaction monitoring",
        "alert_reason": "Structured deposits followed by outbound transfers",
        "internal_risk": "Medium",
        "matching_banks": 0,
        "anonymous_confirmations": 0,
        "aggregate_risk": "Low",
        "transactions": [
            {"from": "CUST-2198", "to": "ACC-2198-1", "amount": 1200, "note": "single transfer"},
        ],
    },
    "CUST-3321": {
        "type": "SME",
        "alert_source": "Behavioural monitoring",
        "alert_reason": "Dormant account became active with rapid payment flows",
        "internal_risk": "High",
        "matching_banks": 1,
        "anonymous_confirmations": 0,
        "aggregate_risk": "Low",
        "transactions": [
            {"from": "CUST-3321", "to": "ACC-3321-1", "amount": 4000, "note": "cash flow"},
            {"from": "ACC-3321-1", "to": "ACC-3321-2", "amount": 3900, "note": "transfer"},
        ],
    },
}

# --- Helpers: Amsterdam time and timeline management ---
def now_amsterdam():
    return datetime.now(ZoneInfo("Europe/Amsterdam"))

def format_time_amsterdam(ts_iso):
    dt = datetime.fromisoformat(ts_iso)
    return dt.strftime("%H:%M")

# --- Session state for per-case workflow results ---
if "results" not in st.session_state:
    st.session_state["results"] = {}

def get_case_state(case_id):
    # default state includes initial timeline event (case flagged)
    if case_id not in st.session_state["results"]:
        initial = now_amsterdam().isoformat()
        st.session_state["results"][case_id] = {
            "stage1_run": False, "stage1_pass": False,
            "stage2_run": False, "stage2_pass": False,
            "stage3_viewed": False,
            "active_stage": 1,
            "timeline": [{"ts": initial, "text": "Case flagged by Bank Alpha"}]
        }
    return st.session_state["results"][case_id]

def save_case_state(case_id, state):
    st.session_state["results"][case_id] = state

def add_timeline_event(case_id, text):
    state = get_case_state(case_id)
    state["timeline"].append({"ts": now_amsterdam().isoformat(), "text": text})
    save_case_state(case_id, state)

# --- Sidebar: case queue ---
st.sidebar.title("Case queue")
st.sidebar.markdown("Select case")

cases = list(SYNTHETIC_ENTITIES.keys())
selected = st.sidebar.selectbox("Select case", cases)
entity = SYNTHETIC_ENTITIES[selected]

st.sidebar.markdown("**Case summary**")
st.sidebar.write(f"- ID: {selected}")
st.sidebar.write(f"- Type: {entity['type']}")
st.sidebar.write(f"- Alert source: {entity['alert_source']}")
st.sidebar.write(f"- Alert reason: {entity['alert_reason']}")
st.sidebar.markdown("---")
st.sidebar.caption("Bank Alpha · Investigations interface")

# --- Load case state ---
state = get_case_state(selected)

# Ensure active_stage is valid given current pass/fail state
if state["stage1_run"] and (not state["stage1_pass"]) and state.get("active_stage",1) > 1:
    state["active_stage"] = 1
if state["stage2_run"] and (not state["stage2_pass"]) and state.get("active_stage",1) > 2:
    state["active_stage"] = 2
save_case_state(selected, state)

# --- Main header (product-like) ---
st.title("Aegis Investigator")
st.markdown("Investigation workspace")

# Case header with badges (separate lines)
badge_flagged = "<div style='margin-bottom:6px'><span style='background:#ffe8e8;color:#a30000;padding:6px 10px;border-radius:12px;font-weight:600'>Flagged</span></div>"
badge_eligible = "<div><span style='background:#eef2ff;color:#1f4ed8;padding:6px 10px;border-radius:12px'>Eligible for consortium check</span></div>"

st.header(selected)
col_a, col_b = st.columns([3,1])
with col_a:
    st.write(f"- Type: **{entity['type']}**")
    st.write(f"- Alert source: **{entity['alert_source']}**")
    st.write(f"- Alert reason: **{entity['alert_reason']}**")
with col_b:
    # show badges stacked to avoid wrapping/cutting
    st.markdown(badge_flagged + badge_eligible, unsafe_allow_html=True)

st.markdown("---")

# --- Compact progress tracker ---
tracker_col1, tracker_col2, tracker_col3 = st.columns([1,1,1])

def render_stage_label(name, status, active=False):
    # Icons: ✅ completed, 🔓 available, 🔒 locked, ❌ failed
    if status == "completed":
        icon = "✅"
        bg = "#e6ffed"
        border = "#2d8a4d"
    elif status == "failed":
        icon = "❌"
        bg = "#fff4e6"
        border = "#d97706"
    elif status == "available":
        icon = "🔓"
        bg = "#eef6ff" if active else "#ffffff"
        border = "#4c9aff" if active else "#e6eef8"
    else:
        icon = "🔒"
        bg = "#f5f7fa"
        border = "#d1d5db"
    html = f"""
    <div style="padding:8px;border-radius:6px;background:{bg};border:1.5px solid {border};text-align:center">
      <div style="font-size:15px">{icon} <strong style="font-size:14px">{name}</strong></div>
    </div>
    """
    return html

# compute statuses
s1 = "available" if not state["stage1_run"] else ("completed" if state["stage1_pass"] else "failed")
s2 = "locked"
if s1 == "completed":
    s2 = "available" if not state["stage2_run"] else ("completed" if state["stage2_pass"] else "failed")
s3 = "locked"
if s2 == "completed":
    s3 = "available" if not state["stage3_viewed"] else "completed"

active = state.get("active_stage", 1)
# normalize active to first available if current active is not allowed
if active == 2 and s2 == "locked":
    active = 1
if active == 3 and s3 == "locked":
    active = 1
state["active_stage"] = active
save_case_state(selected, state)

tracker_col1.markdown(render_stage_label("Stage 1 — Consortium Match Check", s1, active=(active==1)), unsafe_allow_html=True)
tracker_col2.markdown(render_stage_label("Stage 2 — Risk Attestation", s2, active=(active==2)), unsafe_allow_html=True)
tracker_col3.markdown(render_stage_label("Stage 3 — Controlled Network View", s3, active=(active==3)), unsafe_allow_html=True)

st.markdown("---")

# --- Main content: show only active stage panel ---
def show_stage1():
    st.subheader("Stage 1 — Consortium Match Check")
    st.write("Check whether this entity appears across the consortium.")
    st.info("Institution identities are not disclosed. Only the match count is returned.")
    # Real check: sealed query routed blindly through Aegis, verified against
    # each member's pre-registered Merkle root (see aegis_backend.py).
    matching = get_backend().stage1_match_count(selected, entity["matching_banks"])
    if state["stage1_run"]:
        st.write(f"- Match count: **{matching}**")
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
            passed = matching >= 1
            new_state = get_case_state(selected)
            new_state.update({
                "stage1_run": True, "stage1_pass": passed,
                "stage2_run": False, "stage2_pass": False,
                "stage3_viewed": False,
                "active_stage": 1
            })
            save_case_state(selected, new_state)
            # timeline events
            add_timeline_event(selected, "Consortium match check completed")
            if not passed:
                add_timeline_event(selected, "No consortium match found")
            st.rerun()

def show_stage2():
    st.subheader("Stage 2 — Risk Attestation")
    st.write("Verify whether anonymous consortium risk signals exist for this entity.")
    st.info("Risk signals are aggregated and source institutions remain hidden.")
    locked2 = not (state["stage1_run"] and state["stage1_pass"])
    if locked2:
        st.warning("Risk attestation is locked until consortium match is confirmed.")
        return
    if state["stage2_run"]:
        confirmations, risk = get_backend().stage2_attestation(selected, entity["anonymous_confirmations"])
        st.write(f"- Anonymous confirmations: **{confirmations}**")
        st.write(f"- Aggregate concern: **{risk}**")
        if state["stage2_pass"]:
            st.success("Attestation verified — high concern confirmed.")
            if st.button("Continue to controlled network view", key="to_stage3"):
                goto_stage(3)
        else:
            st.error("Consortium presence was found, but anonymous risk attestation was not sufficient for controlled network disclosure.")
    else:
        if st.button("Verify risk attestation"):
            with st.spinner("Verifying attestation..."):
                time.sleep(0.6)
            confirmations, risk = get_backend().stage2_attestation(selected, entity["anonymous_confirmations"])
            passed2 = (confirmations >= 1) and (risk in ["High", "Critical"])
            new_state = get_case_state(selected)
            new_state.update({"stage2_run": True, "stage2_pass": passed2, "active_stage": 2, "stage3_viewed": False})
            save_case_state(selected, new_state)
            # timeline events
            if passed2:
                add_timeline_event(selected, "Risk attestation verified")
            else:
                add_timeline_event(selected, "Controlled network view not authorized")
            st.rerun()

def show_stage3():
    st.subheader("Stage 3 — Controlled Network View")
    st.write("Review approved cross-institutional network indicators.")
    st.info("Network details are available only after prior-stage approval.")
    locked3 = not (state["stage1_run"] and state["stage1_pass"] and state["stage2_run"] and state["stage2_pass"])
    if locked3:
        st.warning("Controlled network view is locked until prior stages complete.")
        return
    if state.get("stage3_viewed", False):
        st.success("Controlled network view opened.")
        df = pd.DataFrame(entity["transactions"])
        st.dataframe(df)
    else:
        if st.button("Open controlled network view"):
            new_state = get_case_state(selected)
            new_state["stage3_viewed"] = True
            new_state["active_stage"] = 3
            save_case_state(selected, new_state)
            add_timeline_event(selected, "Controlled network view opened")
            st.rerun()

def goto_stage(n):
    new_state = get_case_state(selected)
    if n == 2 and (new_state["stage1_run"] and new_state["stage1_pass"]):
        new_state["active_stage"] = 2
    if n == 3 and (new_state["stage2_run"] and new_state["stage2_pass"]):
        new_state["active_stage"] = 3
    save_case_state(selected, new_state)
    st.rerun()

# show the active stage panel
active = get_case_state(selected).get("active_stage", 1)
if active == 1:
    show_stage1()
elif active == 2:
    show_stage2()
elif active == 3:
    show_stage3()

st.markdown("---")

# --- Case timeline (Amsterdam time) and case details ---
left, right = st.columns([1.6,1])
with left:
    st.markdown("### Case timeline · Amsterdam time")
    tl = get_case_state(selected).get("timeline", [])
    # render timeline entries newest last
    for ev in tl:
        t = format_time_amsterdam(ev["ts"])
        st.write(f"- {t} — {ev['text']}")
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
