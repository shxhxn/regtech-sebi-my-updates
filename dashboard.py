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
[data-testid="stMetric"] { background:#fff; border:1px solid #e7ebf0; border-radius:12px; padding:18px 20px; transition:transform 0.15s ease, box-shadow 0.15s ease; }
[data-testid="stMetric"]:hover { transform:translateY(-3px); box-shadow:0 4px 14px rgba(15,23,42,0.08); }
[data-testid="stMetricValue"] { font-weight:600; font-size:1.7rem; color:#0f172a; font-variant-numeric:tabular-nums; }
[data-testid="stMetricLabel"] { color:#64748b; font-weight:500; }
[data-testid="stExpander"] { border:1px solid #e7ebf0; border-radius:12px; margin-bottom:8px; box-shadow:none; background:#fff; transition:box-shadow 0.15s ease, border-color 0.15s ease; }
[data-testid="stExpander"]:hover { border-color:#cbd5e1; box-shadow:0 2px 10px rgba(15,23,42,0.05); }
[data-testid="stExpander"] summary { padding:14px 18px; font-weight:500; color:#0f172a; }
[data-testid="stExpander"] summary:hover { color:#1d4ed8; }
[data-testid="stSidebar"] { background:#f8fafc; border-right:1px solid #e7ebf0; }
.meta { color:#64748b; font-size:0.9rem; }
.verbatim { background:#f8fafc; border:1px solid #e7ebf0; border-left:3px solid #94a3b8; padding:12px 16px; border-radius:8px; color:#475569; font-size:0.88rem; line-height:1.55; margin-top:8px; }
.clause { font-family:ui-monospace,Menlo,monospace; background:#eef2ff; color:#1d4ed8; padding:1px 7px; border-radius:5px; font-size:0.82rem; }
.pill { font-size:0.72rem; font-weight:600; padding:2px 9px; border-radius:999px; }
.pill-new { background:#eff6ff; color:#1d4ed8; } .pill-mod { background:#fffbeb; color:#b45309; } .pill-rem { background:#fef2f2; color:#b91c1c; }
.pill-grounded { background:#eff6ff; color:#1d4ed8; } .pill-partial { background:#fffbeb; color:#b45309; } .pill-flagged { background:#fef2f2; color:#b91c1c; }
.pill-ok { background:#eff6ff; color:#1d4ed8; } .pill-bad { background:#fef2f2; color:#b91c1c; }
.pill-neutral { background:#f1f5f9; color:#475569; }
.big-stat { font-size:2.6rem; font-weight:700; color:#1d4ed8; line-height:1; }
.big-stat-sub { color:#64748b; font-size:0.85rem; margin-top:4px; }
.mono { font-family:ui-monospace,Menlo,monospace; font-size:0.8rem; color:#475569; }
.stat-card { background:#fff; border:1px solid #e7ebf0; border-radius:12px; padding:16px 18px; transition:transform 0.15s ease, box-shadow 0.15s ease; }
.stat-card:hover { transform:translateY(-3px); box-shadow:0 4px 14px rgba(15,23,42,0.08); }
.stat-icon { width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:10px; }
.risk-seg { height:10px; border-radius:999px; overflow:hidden; display:flex; width:100%; }
.risk-seg > div { height:100%; }
.swatch { display:inline-block; width:8px; height:8px; border-radius:2px; margin-right:5px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Regulatory Compiler")
    st.markdown('<p class="meta">Track 2 · Agentic Compliance</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**About**")
    st.markdown('<p class="meta">Extracts source-cited obligations from SEBI circulars, independently verifies each one, tracks fulfilment, detects changes between versions, and maintains a tamper-evident audit trail.</p>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<p class="meta">Self-hosted LLM via Ollama · Pydantic · rapidfuzz · sentence-transformers</p>', unsafe_allow_html=True)

st.markdown("## SEBI Regulatory Compiler")
st.markdown('<p class="meta" style="margin-top:-12px;">Agentic RegTech Compliance · Securities Market TechSprint 2026</p>', unsafe_allow_html=True)
st.write("")

tab_overview, tab_due, tab_changed, tab_register, tab_all, tab_ops, tab_trust = st.tabs(
    ["Overview", "What's Due", "What Changed", "My Register", "All Obligations", "Pipeline Operations", "Trust & Audit"])

def esc(v):
    return html.escape(str(v)) if v not in (None, "") else "-"

def load_best(name):
    vpath = OUTPUT / f"{name}_verified.json"
    ppath = OUTPUT / f"{name}.json"
    if vpath.exists() and ppath.exists() and ppath.stat().st_mtime > vpath.stat().st_mtime:
        # The raw file was written more recently than the verified file --
        # the verified file is a leftover from a PRIOR extraction run (e.g.
        # before a re-extraction). Trusting it would show confidently wrong
        # numbers, so fall back to the fresh (unverified) data instead.
        return json.load(open(ppath)), False
    if vpath.exists():
        return json.load(open(vpath)), True
    if ppath.exists():
        return json.load(open(ppath)), False
    return None, False

def load_json(name):
    p = OUTPUT / name
    return json.load(open(p)) if p.exists() else None

def risk_badge(o):
    """Single shared risk-severity pill, used everywhere risk shows up.
    Critical=red, High=amber carry real warning meaning and stay distinct
    from the blue brand accent. Low uses neutral gray (not blue) so it
    doesn't collide visually with Medium."""
    band = o.get("risk_band")
    if not band:
        return ""
    if band == "Critical":
        return f'<span class="pill pill-rem">{band} risk</span>'
    if band == "High":
        return f'<span class="pill pill-mod">{band} risk</span>'
    if band == "Medium":
        return f'<span class="pill" style="background:#eef2ff;color:#1d4ed8;">{band} risk</span>'
    if band == "Low":
        return f'<span class="pill pill-neutral">{band} risk</span>'
    return ""

def freq_badge(o):
    if not o.get("frequency"):
        return ""
    return f'<span class="pill" style="background:#f1f5f9;color:#475569;">{o.get("frequency")}</span>'

# -- Small inline-SVG icon set (no external font dependency -- can't 404 or flash) --
ICONS = {
    "doc": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/></svg>',
    "alert": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4 L21 20 L3 20 Z"/><line x1="12" y1="10" x2="12" y2="15"/><circle cx="12" cy="17.5" r="0.6" fill="currentColor" stroke="none"/></svg>',
    "check": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="8 12 11 15 16 9"/></svg>',
    "shield": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 L19 6 V11 C19 16 16 19 12 21 C8 19 5 16 5 11 V6 Z"/><path d="M8.5 12 L11 14.5 L16 9"/></svg>',
}

def stat_card(icon_key, value, label, bg, fg):
    return (
        f'<div class="stat-card">'
        f'<div class="stat-icon" style="background:{bg};color:{fg};">{ICONS[icon_key]}</div>'
        f'<div style="font-size:22px;font-weight:600;color:#0f172a;">{value}</div>'
        f'<div style="font-size:13px;color:#64748b;">{label}</div>'
        f'</div>'
    )

def progress_ring(pct, size=100, label="compliant"):
    r = 42
    circumference = 2 * 3.14159265 * r
    offset = circumference * (1 - pct / 100)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 100 100">'
        f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#e7ebf0" stroke-width="9"/>'
        f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#1d4ed8" stroke-width="9" stroke-linecap="round" '
        f'stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}" transform="rotate(-90 50 50)"/>'
        f'<text x="50" y="47" text-anchor="middle" font-size="20" font-weight="600" fill="#0f172a">{pct}%</text>'
        f'<text x="50" y="63" text-anchor="middle" font-size="9" fill="#64748b">{label}</text>'
        f'</svg>'
    )

def risk_distribution_bar(obligations):
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for o in obligations:
        b = o.get("risk_band")
        if b in counts:
            counts[b] += 1
    total = sum(counts.values())
    if not total:
        return None
    colors = {"Critical": "#b91c1c", "High": "#b45309", "Medium": "#1d4ed8", "Low": "#94a3b8"}
    segs = "".join(
        f'<div style="width:{100*counts[k]/total:.1f}%;background:{colors[k]};"></div>'
        for k in counts if counts[k] > 0
    )
    legend = " ".join(
        f'<span style="margin-right:14px;font-size:12px;color:#64748b;">'
        f'<span class="swatch" style="background:{colors[k]};"></span>{k} {counts[k]}</span>'
        for k in counts if counts[k] > 0
    )
    return f'<div class="risk-seg">{segs}</div><div style="margin-top:8px;">{legend}</div>'

# -- Overview --
with tab_overview:
    st.markdown("#### Overview")
    obligations, verified = load_best("obligations_2025")
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh -- your snapshot will appear here.")
    else:
        n = len(obligations)
        has_risk = any(o.get("risk_band") for o in obligations)
        urgent = sum(1 for o in obligations if o.get("risk_band") in ("Critical", "High"))
        traceable = sum(1 for o in obligations if o.get("grounding_band") in ("grounded", "partial"))
        traceable_pct = round(100 * traceable / n, 1) if n else None

        saved = load_json("compliance_status.json") or {}
        statuses = [saved.get(o["obligation_id"], "Not started") for o in obligations]
        compliant = statuses.count("Compliant")
        in_progress = statuses.count("In progress")
        not_started = statuses.count("Not started")
        na = statuses.count("N/A")
        scored = n - na
        pct = int(round(100 * compliant / scored)) if scored else 0

        cards = (
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:1.75rem;">'
            + stat_card("doc", n, "Total obligations", "#eff6ff", "#1d4ed8")
            + stat_card("alert", urgent if has_risk else "-", "Critical / High risk", "#fef2f2", "#b91c1c")
            + stat_card("check", f"{compliant}/{n}", "Marked compliant", "#eff6ff", "#1d4ed8")
            + stat_card("shield", f'{traceable_pct}%' if traceable_pct is not None else "-", "Source-traceable", "#eff6ff", "#1d4ed8")
            + '</div>'
        )
        st.markdown(cards, unsafe_allow_html=True)

        col_ring, col_bar = st.columns([1, 1.4])
        with col_ring:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:16px;">{progress_ring(pct)}'
                f'<div><div style="font-size:14px;font-weight:600;color:#0f172a;margin-bottom:4px;">Compliance posture</div>'
                f'<div style="font-size:12.5px;color:#64748b;line-height:1.6;">{compliant} compliant &middot; {in_progress} in progress &middot; {not_started} not started</div></div></div>',
                unsafe_allow_html=True,
            )
        with col_bar:
            if has_risk:
                st.markdown('<div style="font-size:13px;color:#64748b;margin-bottom:6px;">Risk distribution</div>', unsafe_allow_html=True)
                bar_html = risk_distribution_bar(obligations)
                if bar_html:
                    st.markdown(bar_html, unsafe_allow_html=True)
            else:
                st.markdown('<p class="meta">Run operations.py to see risk distribution here.</p>', unsafe_allow_html=True)

        st.write("")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### Needs attention")
            if has_risk:
                urgent_untouched = [
                    o for o in obligations
                    if o.get("risk_band") in ("Critical", "High")
                    and saved.get(o["obligation_id"], "Not started") == "Not started"
                ]
                if urgent_untouched:
                    st.markdown(f'<p class="meta">{len(urgent_untouched)} Critical or High-risk obligation(s) not yet started. See My Register.</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p class="meta">No high-risk obligations are sitting untouched right now.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="meta">Run operations.py to see risk-based prioritisation here.</p>', unsafe_allow_html=True)
        with col_b:
            st.markdown("##### Recent changes")
            r = load_json("change_impact_report.json")
            if r:
                s = r["summary"]
                st.markdown(f'<p class="meta">{s["added"]} new, {s["modified"]} modified, {s["removed"]} removed since the 2024 circular. See What Changed.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="meta">Run the 2024 extraction and diff engine to see what changed here.</p>', unsafe_allow_html=True)

# -- What's Due --
with tab_due:
    st.markdown("#### What's Due")
    st.markdown('<p class="meta">Your obligations organised by when they come due -- the recurring filing rhythm, the event-triggered deadlines, and the continuous duties.</p>', unsafe_allow_html=True)
    obligations, verified = load_best("obligations_2025")
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh.")
    else:
        RECURRING = ["monthly", "quarterly", "half_yearly", "annual"]
        recurring = [o for o in obligations if o.get("frequency") in RECURRING]
        event = [o for o in obligations if o.get("frequency") == "event_driven"]
        ongoing = [o for o in obligations if o.get("frequency") == "ongoing"]
        onetime = [o for o in obligations if o.get("frequency") == "one_time"]
        with_dl = [o for o in obligations if o.get("deadline")]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Recurring", len(recurring))
        m2.metric("Event-driven", len(event))
        m3.metric("Ongoing duties", len(ongoing))
        m4.metric("With explicit deadline", len(with_dl))

        st.markdown('<p class="meta">SEBI deadlines are mostly relative to a trigger ("within 30 days of ...") rather than fixed dates, so this view organises by cadence and shows each stated time limit, rather than projecting exact calendar dates.</p>', unsafe_allow_html=True)
        st.divider()

        view = st.radio("View", ["All", "Recurring", "Event-driven", "Ongoing", "One-time"], horizontal=True)

        risk_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        def by_risk(items):
            return sorted(items, key=lambda o: risk_rank.get(o.get("risk_band"), 9))

        def render_ob(o, show_trigger=False):
            with st.expander(f"{o.get('title','')}"):
                st.markdown(f'<p class="mono">{esc(o["obligation_id"])}</p>', unsafe_allow_html=True)
                badges = " ".join(b for b in [risk_badge(o), freq_badge(o)] if b)
                if badges:
                    st.markdown(badges, unsafe_allow_html=True)
                    st.write("")
                st.markdown(f"**{o.get('required_action','-')}**")
                if show_trigger and o.get("trigger"):
                    st.markdown(f'<p class="meta">Triggered when: {esc(o.get("trigger"))}</p>', unsafe_allow_html=True)
                if o.get("deadline"):
                    st.markdown(f'<p class="meta">Time limit: {esc(o.get("deadline"))}</p>', unsafe_allow_html=True)
                if o.get("source_clause"):
                    st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)

        period_labels = {"monthly": "Monthly", "quarterly": "Quarterly", "half_yearly": "Half-yearly", "annual": "Annual"}

        if view in ("All", "Recurring") and recurring:
            st.markdown('<h5>Recurring obligations</h5>', unsafe_allow_html=True)
            for period in RECURRING:
                group = by_risk([o for o in recurring if o.get("frequency") == period])
                if group:
                    st.markdown(f'<p class="meta" style="margin-top:10px;"><b>{period_labels[period]}</b> &middot; {len(group)} obligation(s)</p>', unsafe_allow_html=True)
                    for o in group:
                        render_ob(o)

        if view in ("All", "Event-driven") and event:
            st.write("")
            st.markdown('<h5>Event-driven obligations</h5>', unsafe_allow_html=True)
            st.markdown('<p class="meta">Triggered by a specific event -- the clock starts when the event happens.</p>', unsafe_allow_html=True)
            for o in by_risk(event):
                render_ob(o, show_trigger=True)

        if view in ("All", "Ongoing") and ongoing:
            st.write("")
            st.markdown('<h5>Ongoing duties</h5>', unsafe_allow_html=True)
            st.markdown('<p class="meta">Continuous obligations with no single deadline -- they must hold true at all times.</p>', unsafe_allow_html=True)
            for o in by_risk(ongoing):
                render_ob(o)

        if view in ("All", "One-time") and onetime:
            st.write("")
            st.markdown('<h5>One-time obligations</h5>', unsafe_allow_html=True)
            for o in by_risk(onetime):
                render_ob(o)

        shown_any = (
            (view in ("All", "Recurring") and recurring)
            or (view in ("All", "Event-driven") and event)
            or (view in ("All", "Ongoing") and ongoing)
            or (view in ("All", "One-time") and onetime)
        )
        if not shown_any:
            st.info("No obligations in this view.")

# -- What Changed --
with tab_changed:
    st.markdown("#### What Changed - 2024 to 2025")
    st.markdown('<p class="meta">What changed in the new circular, and exactly what it now requires you to do.</p>', unsafe_allow_html=True)
    r = load_json("change_impact_report.json")
    if not r:
        st.info("No change report yet. Run extract_2024.py, then diff_engine.py, then refresh.")
    else:
        s = r["summary"]
        has_reworded = "reworded" in s
        n_cols = 7 if has_reworded and "modified_via_semantic_match" in s else (6 if has_reworded else 5)
        cols = st.columns(n_cols)
        cols[0].metric("2024", s["total_2024"]); cols[1].metric("2025", s["total_2025"])
        cols[2].metric("New", s["added"]); cols[3].metric("Modified", s["modified"]); cols[4].metric("Removed", s["removed"])
        next_col = 5
        if has_reworded:
            cols[next_col].metric("Reworded", s["reworded"], help="Regulation unchanged -- only our generated summary/evidence text was independently regenerated")
            next_col += 1
        if "modified_via_semantic_match" in s:
            cols[next_col].metric("Via semantic match", s["modified_via_semantic_match"], help="Obligations recognized as the same despite a changed ID or reworded text")
        st.write("")

        if r["added"]:
            st.markdown(f'<h5><span class="pill pill-new">New</span>&nbsp;&nbsp;{s["added"]} obligation(s) added in 2025</h5>', unsafe_allow_html=True)
            for o in r["added"]:
                title = o.get("title") or (o.get("required_action") or "")[:60]
                with st.expander(title):
                    st.markdown(f'<p class="mono">{esc(o["obligation_id"])}</p>', unsafe_allow_html=True)
                    badges = " ".join(b for b in [risk_badge(o), freq_badge(o)] if b)
                    if badges:
                        st.markdown(badges, unsafe_allow_html=True)
                        st.write("")
                    st.markdown(f"**{o.get('required_action','-')}**")
                    if o.get("deadline"):
                        st.markdown(f'<p class="meta">Deadline: {esc(o.get("deadline"))}</p>', unsafe_allow_html=True)
                    if o.get("source_clause"):
                        st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)
                    if o.get("verbatim_text"):
                        st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)

        if r["modified"]:
            st.write("")
            st.markdown(f'<h5><span class="pill pill-mod">Modified</span>&nbsp;&nbsp;{s["modified"]} obligation(s) genuinely changed</h5>', unsafe_allow_html=True)
            st.markdown('<p class="meta">The source clause text itself, or its frequency/deadline, changed -- this needs a look.</p>', unsafe_allow_html=True)
            for o in r["modified"]:
                label = o.get('title','')
                if o.get("match_type") == "semantic":
                    label += f"   (matched via semantic similarity, {o.get('semantic_similarity')})"
                with st.expander(label):
                    st.markdown(f'<p class="mono">{esc(o["obligation_id"])}</p>', unsafe_allow_html=True)
                    badges = " ".join(b for b in [risk_badge(o), freq_badge(o)] if b)
                    if badges:
                        st.markdown(badges, unsafe_allow_html=True)
                        st.write("")
                    for field, ch in o["changes"].items():
                        st.markdown(f"**{field.replace('_',' ').title()}**")
                        st.markdown(f'<p class="meta">Before &nbsp;&middot;&nbsp; {esc(ch.get("before"))}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p style="color:#1d4ed8;">After &nbsp;&middot;&nbsp; {esc(ch.get("after"))}</p>', unsafe_allow_html=True)

        if r.get("reworded"):
            st.write("")
            st.markdown(f'<h5><span class="pill pill-neutral">Reworded</span>&nbsp;&nbsp;{s.get("reworded",0)} obligation(s) unchanged in substance</h5>', unsafe_allow_html=True)
            st.markdown('<p class="meta">The actual regulatory text is confirmed the same -- only our own generated summary/evidence wording came out differently between the two independent extraction runs. Nothing to act on.</p>', unsafe_allow_html=True)
            for o in r["reworded"]:
                label = o.get('title','')
                if o.get("match_type") == "semantic":
                    label += f"   (matched via semantic similarity, {o.get('semantic_similarity')})"
                with st.expander(label):
                    st.markdown(f'<p class="mono">{esc(o["obligation_id"])}</p>', unsafe_allow_html=True)
                    for field, ch in o["changes"].items():
                        st.markdown(f"**{field.replace('_',' ').title()}**")
                        st.markdown(f'<p class="meta">Before &nbsp;&middot;&nbsp; {esc(ch.get("before"))}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="meta">After &nbsp;&middot;&nbsp; {esc(ch.get("after"))}</p>', unsafe_allow_html=True)

        if r["removed"]:
            st.write("")
            st.markdown(f'<h5><span class="pill pill-rem">Removed</span>&nbsp;&nbsp;{s["removed"]} no longer present</h5>', unsafe_allow_html=True)
            for o in r["removed"]:
                with st.expander(f"{o.get('title','')}"):
                    st.markdown(f'<p class="mono">{esc(o["obligation_id"])}</p>', unsafe_allow_html=True)
                    st.markdown(f"No longer required: **{o.get('required_action','-')}**")
                    if o.get("source_clause"):
                        st.markdown(f'Was: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)

# -- My Register (Features 3+4, with Gap Detection folded in) --
with tab_register:
    st.markdown("#### My Register")
    st.markdown('<p class="meta">Filter to the obligations that bind your firm, track where you stand on each one, and see what still needs attention.</p>', unsafe_allow_html=True)
    obligations, verified = load_best("obligations_2025")
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh.")
    else:
        firm_labels = {
            "investment_adviser": "Investment Adviser",
            "stock_broker": "Stock Broker",
            "research_analyst": "Research Analyst",
        }
        STATUSES = ["Not started", "In progress", "Compliant", "N/A"]

        saved = load_json("compliance_status.json") or {}
        for o in obligations:
            k = f"status_{o['obligation_id']}"
            if k not in st.session_state:
                st.session_state[k] = saved.get(o["obligation_id"], "Not started")

        firm = st.selectbox(
            "Your firm type",
            ["All"] + list(firm_labels.keys()),
            format_func=lambda k: "All firm types" if k == "All" else firm_labels.get(k, k),
        )
        if firm == "All":
            applicable = obligations
        else:
            applicable = [o for o in obligations if firm in (o.get("applies_to") or [])]

        no_ev = [o for o in applicable if not o.get("evidence") or o.get("evidence") == "N/A"]
        no_dl = [o for o in applicable if o.get("frequency") in ["one_time", "event_driven"] and not o.get("deadline")]
        gap_ids = {o["obligation_id"] for o in no_ev} | {o["obligation_id"] for o in no_dl}

        counts = {s: 0 for s in STATUSES}
        for o in applicable:
            s = st.session_state.get(f"status_{o['obligation_id']}", "Not started")
            counts[s] = counts.get(s, 0) + 1
        scored = len(applicable) - counts["N/A"]
        pct = int(round(100 * counts["Compliant"] / scored)) if scored else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Applies to you", len(applicable))
        m2.metric("Compliant", counts["Compliant"])
        m3.metric("In progress", counts["In progress"])
        m4.metric("Gaps flagged", len(gap_ids))

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:16px;margin:0.5rem 0 1rem;">{progress_ring(pct, size=84)}'
            f'<div style="font-size:13px;color:#64748b;">of applicable obligations marked compliant</div></div>',
            unsafe_allow_html=True,
        )

        show_gaps_only = st.checkbox(f"Show only the {len(gap_ids)} obligation(s) with a gap (missing evidence or no deadline set)")

        if st.button("Save progress"):
            out = {o["obligation_id"]: st.session_state.get(f"status_{o['obligation_id']}", "Not started") for o in obligations}
            with open(OUTPUT / "compliance_status.json", "w") as f:
                json.dump(out, f, indent=2)
            st.success("Saved to output/compliance_status.json")

        st.divider()

        rows = [o for o in applicable if o["obligation_id"] in gap_ids] if show_gaps_only else applicable

        for o in rows:
            oid = o["obligation_id"]
            with st.expander(f"{o.get('title','')}"):
                st.markdown(f'<p class="mono">{esc(oid)}</p>', unsafe_allow_html=True)
                badges = " ".join(b for b in [risk_badge(o), freq_badge(o)] if b)
                for at in (o.get("applies_to") or []):
                    badges += f' <span class="pill" style="background:#eef2ff;color:#1d4ed8;">{firm_labels.get(at, at)}</span>'
                if oid in gap_ids:
                    badges += ' <span class="pill pill-mod">Gap</span>'
                if badges.strip():
                    st.markdown(badges, unsafe_allow_html=True)
                    st.write("")
                st.markdown(f"**{o.get('required_action','-')}**")
                if oid in {x["obligation_id"] for x in no_ev}:
                    st.markdown('<p class="meta">No evidence on file.</p>', unsafe_allow_html=True)
                if oid in {x["obligation_id"] for x in no_dl}:
                    st.markdown('<p class="meta">No deadline set for this triggered obligation.</p>', unsafe_allow_html=True)
                st.selectbox("Status", STATUSES, key=f"status_{oid}")
                if o.get("source_clause"):
                    st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)

# -- All Obligations --
with tab_all:
    st.markdown("#### All Obligations")
    st.markdown('<p class="meta">The complete 2025 obligation graph -- browse, search, and filter by any dimension. For your day-to-day view, use My Register.</p>', unsafe_allow_html=True)
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
            with st.expander(f"{o['title']}"):
                st.markdown(f'<p class="mono">{esc(o["obligation_id"])}</p>', unsafe_allow_html=True)
                badges = []
                rb_html = risk_badge(o)
                if rb_html:
                    badges.append(rb_html)
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

# -- Pipeline Operations --
with tab_ops:
    st.markdown("#### Pipeline Operations")
    st.markdown('<p class="meta">Compliance register and executable rules -- the machine-checkable core the rest of this dashboard is built on. See What\'s Due for the calendar view.</p>', unsafe_allow_html=True)
    register = load_json("compliance_register.json")
    rules = load_json("executable_rules.json")
    if not register:
        st.info("Not built yet. Run: python operations.py")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Register entries", len(register))
        c2.metric("Executable rules", len(rules) if rules else 0)
        st.write("")
        st.markdown("##### Sample executable rule")
        if rules:
            st.json(rules[0])
        st.write("")
        st.markdown("##### Register status overview")
        saved_status = load_json("compliance_status.json") or {}
        statuses = {}
        for r_ in register:
            live_status = saved_status.get(r_["obligation_id"], "Not started")
            statuses[live_status] = statuses.get(live_status, 0) + 1
        st.write(statuses)

# -- Trust & Audit --
with tab_trust:
    obligations_for_summary, _ = load_best("obligations_2025")
    if obligations_for_summary:
        n_summ = len(obligations_for_summary)
        traceable_summ = sum(1 for o in obligations_for_summary if o.get("grounding_band") in ("grounded", "partial"))
        with_deadline = sum(1 for o in obligations_for_summary if o.get("deadline"))
        high_or_critical = sum(1 for o in obligations_for_summary if o.get("risk_band") in ("Critical", "High"))
        rb = {}
        for o in obligations_for_summary:
            band = o.get("risk_band")
            if band:
                rb[band] = rb.get(band, 0) + 1

        st.markdown("#### Executive Overview")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Total obligations", n_summ)
        e2.metric("High / Critical risk", high_or_critical)
        e3.metric("With deadline", with_deadline)
        e4.metric("Verifiably traceable", f'{round(100*traceable_summ/n_summ, 1) if n_summ else 0}%')
        st.markdown(
            f'<p class="meta">Risk profile: '
            f'<span class="pill pill-rem">Critical {rb.get("Critical",0)}</span>&nbsp;'
            f'<span class="pill pill-mod">High {rb.get("High",0)}</span>&nbsp;'
            f'<span class="pill" style="background:#eef2ff;color:#1d4ed8;">Medium {rb.get("Medium",0)}</span>&nbsp;'
            f'<span class="pill pill-neutral">Low {rb.get("Low",0)}</span></p>',
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
                    with st.expander(f"{o['title']}   .   score {o.get('grounding_score')}"):
                        st.markdown(f'<p class="mono">{esc(o["obligation_id"])}</p>', unsafe_allow_html=True)
                        st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)

    st.divider()
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
