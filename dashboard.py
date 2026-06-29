import streamlit as st
import json
import html
from src.config import OUTPUT

st.set_page_config(page_title="SEBI Regulatory Compiler", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], button, input, textarea { font-family: 'Inter', -apple-system, sans-serif; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { visibility: hidden; height: 0; }
.block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1080px; }
h1,h2,h3,h4,h5 { color:#0f172a; font-weight:600; letter-spacing:-0.015em; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e7ebf0; border-radius:12px; padding:18px 20px; }
[data-testid="stMetricValue"] { font-weight:600; font-size:1.7rem; color:#0f172a; font-variant-numeric:tabular-nums; }
[data-testid="stMetricLabel"] { color:#64748b; font-weight:500; }
[data-testid="stExpander"] { border:1px solid #e7ebf0; border-radius:12px; margin-bottom:8px; box-shadow:none; background:#fff; }
[data-testid="stExpander"] summary { padding:14px 18px; font-weight:500; color:#0f172a; }
[data-testid="stExpander"] summary:hover { color:#1d4ed8; }
[data-testid="stSidebar"] { background:#f8fafc; border-right:1px solid #e7ebf0; }
.meta { color:#64748b; font-size:0.9rem; }
.verbatim { background:#f8fafc; border:1px solid #e7ebf0; border-left:3px solid #94a3b8; padding:12px 16px; border-radius:8px; color:#475569; font-size:0.88rem; line-height:1.55; margin-top:8px; }
.clause { font-family:ui-monospace,Menlo,monospace; background:#eef2ff; color:#1d4ed8; padding:1px 7px; border-radius:5px; font-size:0.82rem; }
.pill { font-size:0.72rem; font-weight:600; padding:2px 9px; border-radius:999px; }
.pill-new { background:#ecfdf5; color:#047857; } .pill-mod { background:#fffbeb; color:#b45309; } .pill-rem { background:#fef2f2; color:#b91c1c; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Regulatory Compiler")
    st.markdown('<p class="meta">Track 2 · Agentic Compliance</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**About**")
    st.markdown('<p class="meta">Extracts source-cited obligations from SEBI circulars, detects what changes between versions, and flags compliance gaps.</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<p class="meta">Llama 3.3 70B · Pydantic</p>', unsafe_allow_html=True)

st.markdown("## SEBI Regulatory Compiler")
st.markdown('<p class="meta" style="margin-top:-12px;">Agentic RegTech Compliance · Securities Market TechSprint 2026</p>', unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3 = st.tabs(["Obligations", "Change Impact", "Gap Detection"])

def esc(v):
    return html.escape(str(v)) if v not in (None, "") else "—"

# ── Obligations ──
with tab1:
    st.markdown("#### 2025 Obligation Graph")
    st.markdown('<p class="meta">Master Circular for Investment Advisers · SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94</p>', unsafe_allow_html=True)
    path = OUTPUT / "obligations_2025.json"
    if not path.exists():
        st.info("No obligations yet. Run extract_full.py, then refresh.")
    else:
        obligations = json.load(open(path))
        fc = {}
        for o in obligations:
            fc[o.get("frequency","not_specified")] = fc.get(o.get("frequency","not_specified"),0)+1
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total", len(obligations))
        c2.metric("Ongoing", fc.get("ongoing",0))
        c3.metric("Annual", fc.get("annual",0))
        c4.metric("Event-driven", fc.get("event_driven",0))
        st.write("")
        f1,f2 = st.columns([1,2])
        freq = f1.selectbox("Frequency", ["All","ongoing","one_time","annual","quarterly","half_yearly","event_driven","not_specified"])
        search = f2.text_input("Search")
        rows = obligations
        if freq != "All": rows = [o for o in rows if o.get("frequency")==freq]
        if search: rows = [o for o in rows if search.lower() in json.dumps(o).lower()]
        st.markdown(f'<p class="meta">{len(rows)} of {len(obligations)} obligations</p>', unsafe_allow_html=True)
        for o in rows:
            with st.expander(f"{o['obligation_id']}   ·   {o['title']}"):
                a,b = st.columns(2)
                a.markdown("**Required action**"); a.write(o.get("required_action","—"))
                b.markdown("**Evidence**"); b.write(o.get("evidence","—"))
                st.markdown(f'<p class="meta">Frequency: {esc(o.get("frequency"))} &nbsp;·&nbsp; Deadline: {esc(o.get("deadline"))}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="meta">Trigger: {esc(o.get("trigger"))}</p>', unsafe_allow_html=True)
                st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)

# ── Change Impact ──
with tab2:
    st.markdown("#### Change Impact · 2024 to 2025")
    rp = OUTPUT / "change_impact_report.json"
    if not rp.exists():
        st.info("No change report yet. Run extract_2024.py, then diff_engine.py, then refresh.")
    else:
        r = json.load(open(rp)); s = r["summary"]
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("2024", s["total_2024"]); c2.metric("2025", s["total_2025"])
        c3.metric("New", s["added"]); c4.metric("Modified", s["modified"]); c5.metric("Removed", s["removed"])
        st.write("")
        if r["added"]:
            st.markdown(f'<h5><span class="pill pill-new">New</span>&nbsp;&nbsp;{s["added"]} added in 2025</h5>', unsafe_allow_html=True)
            for o in r["added"]:
                with st.expander(f"{o['obligation_id']}   ·   {o['title']}"):
                    st.write(o.get("required_action","—"))
                    st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)
        if r["modified"]:
            st.markdown(f'<h5><span class="pill pill-mod">Modified</span>&nbsp;&nbsp;{s["modified"]} changed</h5>', unsafe_allow_html=True)
            for o in r["modified"]:
                with st.expander(f"{o['obligation_id']}   ·   {o['title']}"):
                    for field, ch in o["changes"].items():
                        st.markdown(f"**{field}**")
                        st.markdown(f'<p class="meta">Before — {esc(ch["before"])}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p style="color:#047857;">After — {esc(ch["after"])}</p>', unsafe_allow_html=True)
        if r["removed"]:
            st.markdown(f'<h5><span class="pill pill-rem">Removed</span>&nbsp;&nbsp;{s["removed"]} no longer present</h5>', unsafe_allow_html=True)
            for o in r["removed"]:
                with st.expander(f"{o['obligation_id']}   ·   {o['title']}"):
                    st.write(o.get("required_action","—"))

# ── Gap Detection ──
with tab3:
    st.markdown("#### Gap Detection")
    st.markdown('<p class="meta">Obligations with missing evidence or undefined timing</p>', unsafe_allow_html=True)
    path = OUTPUT / "obligations_2025.json"
    if not path.exists():
        st.info("No obligations yet. Run extract_full.py, then refresh.")
    else:
        obligations = json.load(open(path))
        no_ev = [o for o in obligations if not o.get("evidence") or o.get("evidence")=="N/A"]
        no_dl = [o for o in obligations if o.get("frequency") in ["one_time","event_driven"] and not o.get("deadline")]
        c1,c2 = st.columns(2)
        c1.metric("Missing evidence", len(no_ev))
        c2.metric("Triggered, no deadline", len(no_dl))
        st.write("")
        if no_ev:
            st.markdown(f"##### Missing evidence ({len(no_ev)})")
            for o in no_ev:
                with st.expander(f"{o['obligation_id']}   ·   {o['title']}"):
                    st.write(o.get("required_action","—"))
                    st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)
        if no_dl:
            st.markdown(f"##### Triggered with no deadline ({len(no_dl)})")
            for o in no_dl:
                with st.expander(f"{o['obligation_id']}   ·   {o['title']}"):
                    st.markdown(f'<p class="meta">Trigger: {esc(o.get("trigger"))}</p>', unsafe_allow_html=True)
                    st.write(o.get("required_action","—"))