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
.pill-grounded { background:#ecfdf5; color:#047857; } .pill-partial { background:#fffbeb; color:#b45309; } .pill-flagged { background:#fef2f2; color:#b91c1c; }
.big-stat { font-size:2.6rem; font-weight:700; color:#047857; line-height:1; }
.big-stat-sub { color:#64748b; font-size:0.85rem; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Regulatory Compiler")
    st.markdown('<p class="meta">Track 2 · Agentic Compliance</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**About**")
    st.markdown('<p class="meta">Extracts source-cited obligations from SEBI circulars, independently verifies each one against the source text, detects what changes between versions, and flags compliance gaps.</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<p class="meta">Llama 3.3 70B · Pydantic · rapidfuzz</p>', unsafe_allow_html=True)

st.markdown("## SEBI Regulatory Compiler")
st.markdown('<p class="meta" style="margin-top:-12px;">Agentic RegTech Compliance · Securities Market TechSprint 2026</p>', unsafe_allow_html=True)
st.write("")

tab0, tab1, tab2, tab3 = st.tabs(["Trust & Verification", "Obligations", "Change Impact", "Gap Detection"])

def esc(v):
    return html.escape(str(v)) if v not in (None, "") else "—"

def load_best(name):
    """Prefer the verified file (has grounding/confidence) if it exists, else fall back."""
    vpath = OUTPUT / f"{name}_verified.json"
    ppath = OUTPUT / f"{name}.json"
    if vpath.exists():
        return json.load(open(vpath)), True
    if ppath.exists():
        return json.load(open(ppath)), False
    return None, False

# -- Trust & Verification --
with tab0:
    st.markdown("#### Trust & Verification")
    st.markdown('<p class="meta">Every obligation is independently checked against the source PDF -- not just asserted by the model.</p>', unsafe_allow_html=True)

    obligations, verified = load_best("obligations_2025")
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then verify.py, then refresh.")
    elif not verified:
        st.warning("Obligations found, but not yet verified. Run: python verify.py")
    else:
        n = len(obligations)
        grounded = sum(1 for o in obligations if o.get("grounding_band") == "grounded")
        partial = sum(1 for o in obligations if o.get("grounding_band") == "partial")
        flagged = sum(1 for o in obligations if o.get("grounding_band") == "flagged")
        traceable_pct = round(100 * (grounded + partial) / n, 1) if n else 0

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f'<div class="big-stat">{traceable_pct}%</div>', unsafe_allow_html=True)
            st.markdown('<div class="big-stat-sub">of obligations independently verified as traceable to source text</div>', unsafe_allow_html=True)
        with c2:
            st.write("")
            a, b, cc = st.columns(3)
            a.metric("Grounded", grounded, help="Verbatim text matches the source PDF exactly (allowing for spacing/formatting)")
            b.metric("Partial", partial, help="Substantially present in the source, minor wording variance")
            cc.metric("Flagged for review", flagged, help="Could not be confidently matched to the source text")

        st.write("")
        st.markdown("##### How this works")
        st.markdown(
            '<p class="meta">After extraction, every obligation\'s <code>verbatim_text</code> is checked against '
            'the actual source PDF using exact, despaced, and fuzzy matching. This is deterministic Python -- no AI '
            'involved in the check itself -- so it independently catches anything the model may have misquoted or '
            'invented. Obligations are also scored on completeness and clause quality to produce a confidence band.</p>',
            unsafe_allow_html=True)

        if flagged:
            st.write("")
            st.markdown(f"##### Flagged for human review ({flagged})")
            for o in obligations:
                if o.get("grounding_band") == "flagged":
                    with st.expander(f"{o['obligation_id']}   .   {o['title']}   .   score {o.get('grounding_score')}"):
                        st.markdown(f'<span class="pill pill-flagged">Score {o.get("grounding_score")}</span>', unsafe_allow_html=True)
                        st.markdown("**Claimed verbatim text:**")
                        st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)
                        st.markdown(f'<p class="meta" style="margin-top:8px;">Source clause: <span class="clause">{esc(o.get("source_clause"))}</span></p>', unsafe_allow_html=True)
        else:
            st.success("No obligations flagged in this run.")

# -- Obligations --
with tab1:
    st.markdown("#### 2025 Obligation Graph")
    st.markdown('<p class="meta">Master Circular for Investment Advisers - SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94</p>', unsafe_allow_html=True)
    obligations, verified = load_best("obligations_2025")
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh.")
    else:
        fc = {}
        for o in obligations:
            fc[o.get("frequency","not_specified")] = fc.get(o.get("frequency","not_specified"),0)+1
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total", len(obligations))
        c2.metric("Ongoing", fc.get("ongoing",0))
        c3.metric("Annual", fc.get("annual",0))
        c4.metric("Event-driven", fc.get("event_driven",0))
        st.write("")
        f1,f2,f3 = st.columns([1,1,2])
        freq = f1.selectbox("Frequency", ["All","ongoing","one_time","monthly","quarterly","half_yearly","annual","event_driven","not_specified"])
        trust_opts = ["All","grounded","partial","flagged"] if verified else ["All"]
        trust = f2.selectbox("Trust", trust_opts, disabled=not verified)
        search = f3.text_input("Search")
        rows = obligations
        if freq != "All": rows = [o for o in rows if o.get("frequency")==freq]
        if verified and trust != "All": rows = [o for o in rows if o.get("grounding_band")==trust]
        if search: rows = [o for o in rows if search.lower() in json.dumps(o).lower()]
        st.markdown(f'<p class="meta">{len(rows)} of {len(obligations)} obligations</p>', unsafe_allow_html=True)
        for o in rows:
            with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                if verified:
                    st.markdown(f'<span class="pill pill-{o.get("grounding_band","")}">{o.get("grounding_band","")} - {o.get("grounding_score","")}</span>&nbsp;&nbsp;<span class="meta">confidence: {o.get("confidence","")}% ({o.get("confidence_band","")})</span>', unsafe_allow_html=True)
                    st.write("")
                a,b = st.columns(2)
                a.markdown("**Required action**"); a.write(o.get("required_action","-"))
                b.markdown("**Evidence**"); b.write(o.get("evidence","-"))
                st.markdown(f'<p class="meta">Frequency: {esc(o.get("frequency"))} &nbsp;.&nbsp; Deadline: {esc(o.get("deadline"))}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="meta">Trigger: {esc(o.get("trigger"))}</p>', unsafe_allow_html=True)
                st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)

# -- Change Impact --
with tab2:
    st.markdown("#### Change Impact - 2024 to 2025")
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
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.write(o.get("required_action","-"))
                    st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)
        if r["modified"]:
            st.markdown(f'<h5><span class="pill pill-mod">Modified</span>&nbsp;&nbsp;{s["modified"]} changed</h5>', unsafe_allow_html=True)
            for o in r["modified"]:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    for field, ch in o["changes"].items():
                        st.markdown(f"**{field}**")
                        st.markdown(f'<p class="meta">Before -- {esc(ch["before"])}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p style="color:#047857;">After -- {esc(ch["after"])}</p>', unsafe_allow_html=True)
        if r["removed"]:
            st.markdown(f'<h5><span class="pill pill-rem">Removed</span>&nbsp;&nbsp;{s["removed"]} no longer present</h5>', unsafe_allow_html=True)
            for o in r["removed"]:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.write(o.get("required_action","-"))

# -- Gap Detection --
with tab3:
    st.markdown("#### Gap Detection")
    st.markdown('<p class="meta">Obligations with missing evidence or undefined timing</p>', unsafe_allow_html=True)
    obligations, verified = load_best("obligations_2025")
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh.")
    else:
        no_ev = [o for o in obligations if not o.get("evidence") or o.get("evidence")=="N/A"]
        no_dl = [o for o in obligations if o.get("frequency") in ["one_time","event_driven"] and not o.get("deadline")]
        c1,c2 = st.columns(2)
        c1.metric("Missing evidence", len(no_ev))
        c2.metric("Triggered, no deadline", len(no_dl))
        st.write("")
        if no_ev:
            st.markdown(f"##### Missing evidence ({len(no_ev)})")
            for o in no_ev:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.write(o.get("required_action","-"))
                    st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)
        if no_dl:
            st.markdown(f"##### Triggered with no deadline ({len(no_dl)})")
            for o in no_dl:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.markdown(f'<p class="meta">Trigger: {esc(o.get("trigger"))}</p>', unsafe_allow_html=True)
                    st.write(o.get("required_action","-"))
