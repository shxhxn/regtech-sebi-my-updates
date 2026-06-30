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
.pill-ok { background:#ecfdf5; color:#047857; } .pill-bad { background:#fef2f2; color:#b91c1c; }
.big-stat { font-size:2.6rem; font-weight:700; color:#047857; line-height:1; }
.big-stat-sub { color:#64748b; font-size:0.85rem; margin-top:4px; }
.mono { font-family:ui-monospace,Menlo,monospace; font-size:0.8rem; color:#475569; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Regulatory Compiler")
    st.markdown('<p class="meta">Track 2 · Agentic Compliance</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**About**")
    st.markdown('<p class="meta">Extracts source-cited obligations from SEBI circulars, independently verifies each one, tracks fulfilment, detects changes between versions, and maintains a tamper-evident audit trail.</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<p class="meta">Llama 3.3 70B · Pydantic · rapidfuzz · sentence-transformers</p>', unsafe_allow_html=True)

st.markdown("## SEBI Regulatory Compiler")
st.markdown('<p class="meta" style="margin-top:-12px;">Agentic RegTech Compliance · Securities Market TechSprint 2026</p>', unsafe_allow_html=True)
st.write("")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Trust & Verification", "Obligations", "Change Impact", "Gap Detection", "Operations", "Audit Trail"])

def esc(v):
    return html.escape(str(v)) if v not in (None, "") else "-"

def load_best(name):
    vpath = OUTPUT / f"{name}_verified.json"
    ppath = OUTPUT / f"{name}.json"
    if vpath.exists():
        return json.load(open(vpath)), True
    if ppath.exists():
        return json.load(open(ppath)), False
    return None, False

def load_json(name):
    p = OUTPUT / name
    return json.load(open(p)) if p.exists() else None

# -- Trust & Verification --
with tab0:
    summ = load_json("executive_summary.json")
    if summ:
        st.markdown("#### Executive Overview")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Total obligations", summ.get("total_obligations", 0))
        e2.metric("High / Critical risk", summ.get("high_or_critical_risk", 0))
        e3.metric("With deadline", summ.get("with_explicit_deadline", 0))
        e4.metric("Verifiably traceable", f'{summ.get("verifiably_traceable_pct", 0)}%')
        rb = summ.get("risk_breakdown", {})
        st.markdown(
            f'<p class="meta">Risk profile: '
            f'<span class="pill pill-rem">Critical {rb.get("Critical",0)}</span>&nbsp;'
            f'<span class="pill pill-mod">High {rb.get("High",0)}</span>&nbsp;'
            f'<span class="pill" style="background:#eef2ff;color:#1d4ed8;">Medium {rb.get("Medium",0)}</span>&nbsp;'
            f'<span class="pill pill-ok">Low {rb.get("Low",0)}</span></p>',
            unsafe_allow_html=True)
        st.divider()

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
            a.metric("Grounded", grounded)
            b.metric("Partial", partial)
            cc.metric("Flagged for review", flagged)
        st.write("")
        st.markdown("##### How this works")
        st.markdown('<p class="meta">After extraction, every obligation\'s <code>verbatim_text</code> is checked against the actual source PDF using exact, despaced, and fuzzy matching -- deterministic Python, no AI in the check itself.</p>', unsafe_allow_html=True)
        if flagged:
            st.write("")
            st.markdown(f"##### Flagged for human review ({flagged})")
            for o in obligations:
                if o.get("grounding_band") == "flagged":
                    with st.expander(f"{o['obligation_id']}   .   {o['title']}   .   score {o.get('grounding_score')}"):
                        st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)

# -- Obligations --
with tab1:
    st.markdown("#### 2025 Obligation Graph")
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
        has_risk = any(o.get("risk_band") for o in obligations)
        risk_opts = ["All","Critical","High","Medium","Low"] if has_risk else ["All"]
        risk_sel = f2.selectbox("Risk", risk_opts, disabled=not has_risk)
        depts = sorted({o.get("department") for o in obligations if o.get("department")})
        dept_sel = f3.selectbox("Department", ["All"] + depts) if depts else "All"
        search = st.text_input("Search")
        rows = obligations
        if freq != "All": rows = [o for o in rows if o.get("frequency")==freq]
        if has_risk and risk_sel != "All": rows = [o for o in rows if o.get("risk_band")==risk_sel]
        if dept_sel != "All": rows = [o for o in rows if o.get("department")==dept_sel]
        if search: rows = [o for o in rows if search.lower() in json.dumps(o).lower()]
        st.markdown(f'<p class="meta">{len(rows)} of {len(obligations)} obligations</p>', unsafe_allow_html=True)
        for o in rows:
            with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                badges = []
                if o.get("risk_band"):
                    rmap = {"Critical":"pill-rem","High":"pill-mod","Medium":"","Low":"pill-ok"}
                    style = 'style="background:#eef2ff;color:#1d4ed8;"' if o.get("risk_band")=="Medium" else ""
                    badges.append(f'<span class="pill {rmap.get(o.get("risk_band"),"")}" {style}>{o.get("risk_band")} risk</span>')
                if o.get("department"):
                    badges.append(f'<span class="pill" style="background:#f1f5f9;color:#475569;">{o.get("department")}</span>')
                if verified:
                    badges.append(f'<span class="pill pill-{o.get("grounding_band","")}">{o.get("grounding_band","")} - {o.get("grounding_score","")}</span>')
                if badges:
                    st.markdown(" ".join(badges), unsafe_allow_html=True)
                    st.write("")
                a,b = st.columns(2)
                a.markdown("**Required action**"); a.write(o.get("required_action","-"))
                b.markdown("**Evidence**"); b.write(o.get("evidence","-"))
                st.markdown(f'<p class="meta">Frequency: {esc(o.get("frequency"))} . Deadline: {esc(o.get("deadline"))}</p>', unsafe_allow_html=True)
                st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)

# -- Change Impact --
with tab2:
    st.markdown("#### Change Impact - 2024 to 2025")
    r = load_json("change_impact_report.json")
    if not r:
        st.info("No change report yet. Run extract_2024.py, then diff_engine.py, then refresh.")
    else:
        s = r["summary"]
        cols = st.columns(6) if "modified_via_semantic_match" in s else st.columns(5)
        cols[0].metric("2024", s["total_2024"]); cols[1].metric("2025", s["total_2025"])
        cols[2].metric("New", s["added"]); cols[3].metric("Modified", s["modified"]); cols[4].metric("Removed", s["removed"])
        if "modified_via_semantic_match" in s:
            cols[5].metric("Via semantic match", s["modified_via_semantic_match"], help="Obligations recognized as the same despite a changed ID or reworded text")
        st.write("")
        if r["added"]:
            st.markdown(f'<h5><span class="pill pill-new">New</span>&nbsp;&nbsp;{s["added"]} added in 2025</h5>', unsafe_allow_html=True)
            for o in r["added"]:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.write(o.get("required_action","-"))
        if r["modified"]:
            st.markdown(f'<h5><span class="pill pill-mod">Modified</span>&nbsp;&nbsp;{s["modified"]} changed</h5>', unsafe_allow_html=True)
            for o in r["modified"]:
                label = f"{o['obligation_id']}   .   {o['title']}"
                if o.get("match_type") == "semantic":
                    label += f"   (matched via semantic similarity, {o.get('semantic_similarity')})"
                with st.expander(label):
                    for field, ch in o["changes"].items():
                        st.markdown(f"**{field}**")
                        st.markdown(f'<p class="meta">Before -- {esc(ch.get("before"))}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p style="color:#047857;">After -- {esc(ch.get("after"))}</p>', unsafe_allow_html=True)
        if r["removed"]:
            st.markdown(f'<h5><span class="pill pill-rem">Removed</span>&nbsp;&nbsp;{s["removed"]} no longer present</h5>', unsafe_allow_html=True)
            for o in r["removed"]:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.write(o.get("required_action","-"))

# -- Gap Detection --
with tab3:
    st.markdown("#### Gap Detection")
    obligations, verified = load_best("obligations_2025")
    if obligations is None:
        st.info("No obligations yet.")
    else:
        no_ev = [o for o in obligations if not o.get("evidence") or o.get("evidence")=="N/A"]
        no_dl = [o for o in obligations if o.get("frequency") in ["one_time","event_driven"] and not o.get("deadline")]
        c1,c2 = st.columns(2)
        c1.metric("Missing evidence", len(no_ev))
        c2.metric("Triggered, no deadline", len(no_dl))
        if no_ev:
            st.markdown(f"##### Missing evidence ({len(no_ev)})")
            for o in no_ev:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.write(o.get("required_action","-"))
        if no_dl:
            st.markdown(f"##### Triggered with no deadline ({len(no_dl)})")
            for o in no_dl:
                with st.expander(f"{o['obligation_id']}   .   {o['title']}"):
                    st.write(o.get("required_action","-"))

# -- Operations --
with tab4:
    st.markdown("#### Operations")
    st.markdown('<p class="meta">Compliance register, executable rules, and calendar -- turning the obligation graph into a working compliance system.</p>', unsafe_allow_html=True)
    register = load_json("compliance_register.json")
    rules = load_json("executable_rules.json")
    calendar = load_json("compliance_calendar.json")
    if not register:
        st.info("Not built yet. Run: python operations.py")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Register entries", len(register))
        c2.metric("Executable rules", len(rules) if rules else 0)
        c3.metric("Calendar buckets", len(calendar) if calendar else 0)
        st.write("")
        st.markdown("##### Compliance calendar")
        if calendar:
            for freq, items in calendar.items():
                with st.expander(f"{freq}   .   {len(items)} obligation(s)"):
                    for it in items[:30]:
                        dl = f" -- due {it['deadline']}" if it.get("deadline") else ""
                        st.markdown(f'<p class="meta">{esc(it["obligation_id"])}: {esc(it["title"])}{dl}</p>', unsafe_allow_html=True)
        st.write("")
        st.markdown("##### Sample executable rule")
        if rules:
            st.json(rules[0])
        st.write("")
        st.markdown("##### Register status overview")
        statuses = {}
        for r_ in register:
            statuses[r_["status"]] = statuses.get(r_["status"], 0) + 1
        st.write(statuses)

# -- Audit Trail --
with tab5:
    st.markdown("#### Audit Trail")
    st.markdown('<p class="meta">A hash-chained, tamper-evident log of every pipeline run. Altering any past entry breaks the chain from that point forward.</p>', unsafe_allow_html=True)
    log = load_json("audit_log.json")
    if not log:
        st.info("No audit log yet. Run: python build_audit_log.py")
    else:
        from src.audit_log import verify_chain
        valid, broken_at = verify_chain()
        c1, c2 = st.columns(2)
        c1.metric("Events logged", len(log))
        with c2:
            if valid:
                st.markdown('<span class="pill pill-ok">Chain verified intact</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="pill pill-bad">Tampering detected at index {broken_at}</span>', unsafe_allow_html=True)
        st.write("")
        for e in reversed(log):
            with st.expander(f"[{e['index']}] {e['timestamp'][:19]}   .   {e['event_type']}"):
                st.json(e["details"])
                st.markdown(f'<p class="mono">hash: {e["hash"][:32]}...</p>', unsafe_allow_html=True)
