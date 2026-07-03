import streamlit as st
import json
import html
import base64
import subprocess
import requests
from src.config import OUTPUT, ROOT
from sebi_monitor import check_for_new_circulars

st.set_page_config(page_title="SEBI Regulatory Compiler", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');
html, body, [class*="css"], button, input, textarea { font-family: 'Inter', -apple-system, sans-serif; font-size: 13.5px; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { visibility: hidden; height: 0; }
/* Do NOT display:none the header itself -- it hosts the sidebar's
   collapse/reopen control. Hiding the whole element leaves no way to
   reopen a collapsed sidebar. Instead give content enough top clearance
   (see .block-container padding-top) and let this stay a plain white bar. */
.block-container { padding-top: 4rem; padding-bottom: 2rem; max-width: 96%; }
h1,h2,h3,h4,h5 { font-family:'Fraunces', Georgia, serif; color:#0f172a; font-weight:600; letter-spacing:-0.01em; }
h5 { font-size: 1rem; margin-bottom: 0.4rem; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e7ebf0; border-radius:10px; padding:10px 14px; }
[data-testid="stMetricValue"] { font-family:'Fraunces', Georgia, serif; font-weight:600; font-size:1.4rem; color:#0f172a; font-variant-numeric:tabular-nums; }
[data-testid="stMetricLabel"] { color:#64748b; font-weight:500; font-size:0.78rem; }
[data-testid="stExpander"] { border:1px solid #e7ebf0; border-radius:10px; margin-bottom:6px; box-shadow:none; background:#fff; transition:border-color 0.15s ease; }
[data-testid="stExpander"]:hover { border-color:#94a3b8; }
[data-testid="stExpander"] summary { padding:9px 14px; font-weight:500; color:#0f172a; font-size:0.86rem; }
[data-testid="stExpander"] summary:hover { color:#1d4ed8; }
[data-testid="stExpander"] .streamlit-expanderContent { padding:0.3rem 1rem 0.9rem; }
[data-testid="stSidebar"] { background:#f8fafc; border-right:1px solid #e7ebf0; width: 232px !important; }
[data-testid="stSidebar"] .block-container { padding-top: 1.1rem; padding-left: 0.9rem; padding-right: 0.9rem; }
[data-testid="stSidebarUserContent"] { padding-top: 0; }
.meta { color:#64748b; font-size:0.86rem; }
.verbatim { background:#f8fafc; border:1px solid #e7ebf0; border-left:3px solid #94a3b8; padding:10px 14px; border-radius:8px; color:#475569; font-size:0.85rem; line-height:1.5; margin-top:8px; }
.clause { font-family:ui-monospace,Menlo,monospace; background:#eef2ff; color:#1d4ed8; padding:1px 7px; border-radius:5px; font-size:0.8rem; }
.pill { font-size:0.7rem; font-weight:600; padding:2px 9px; border-radius:999px; }
.pill-new { background:#eff6ff; color:#1d4ed8; } .pill-mod { background:#fffbeb; color:#b45309; } .pill-rem { background:#fef2f2; color:#b91c1c; }
.pill-grounded { background:#eff6ff; color:#1d4ed8; } .pill-partial { background:#fffbeb; color:#b45309; } .pill-flagged { background:#fef2f2; color:#b91c1c; }
.pill-ok { background:#eff6ff; color:#1d4ed8; } .pill-bad { background:#fef2f2; color:#b91c1c; }
.pill-neutral { background:#f1f5f9; color:#475569; }
.big-stat { font-family:'Fraunces', Georgia, serif; font-size:2.3rem; font-weight:700; color:#1d4ed8; line-height:1; }
.big-stat-sub { color:#64748b; font-size:0.82rem; margin-top:4px; }
.mono { font-family:ui-monospace,Menlo,monospace; font-size:0.78rem; color:#475569; }
.stat-card { background:#fff; border:1px solid #e7ebf0; border-radius:10px; padding:12px 16px; height:100%; }
.stat-card .stat-value { font-family:'Fraunces', Georgia, serif; font-size:22px; font-weight:600; color:#0f172a; line-height:1.1; }
.stat-card .stat-label { font-size:10.5px; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.05em; margin-top:4px; }
.risk-seg { height:9px; border-radius:999px; overflow:hidden; display:flex; width:100%; }
.risk-seg > div { height:100%; }
.swatch { display:inline-block; width:8px; height:8px; border-radius:2px; margin-right:5px; }
.chain { position:relative; padding-left:30px; margin-top:6px; }
.chain-item { position:relative; margin-bottom:18px; }
.chain-item:last-child { margin-bottom:0; }
.chain-item:not(:last-child)::after { content:''; position:absolute; left:-21px; top:20px; width:2px; height:calc(100% + 18px); background:#dbe2ea; }
.chain-dot { position:absolute; left:-30px; top:0; width:20px; height:20px; border-radius:50%; background:#1d4ed8; color:#fff; font-family:'Fraunces',Georgia,serif; font-weight:700; font-size:10px; display:flex; align-items:center; justify-content:center; z-index:1; }
.chain-dot.broken { background:#b91c1c; }
.chain-card { border:1px solid #e7ebf0; border-radius:10px; padding:12px 16px; background:#fff; }
.chain-card.broken { border-color:#fecaca; background:#fef7f7; }
.chain-event { font-family:'Fraunces',Georgia,serif; font-weight:600; font-size:14.5px; color:#0f172a; text-transform:capitalize; }
.chain-hashline { font-family:ui-monospace,Menlo,monospace; font-size:11px; color:#94a3b8; margin-top:6px; }
.chain-hashline b { color:#1d4ed8; }

/* -- app shell: header -- */
.app-title { font-family:'Fraunces', Georgia, serif; font-weight:600; font-size:1.2rem; color:#0f172a; line-height:1.2; }
.app-subtitle { color:#64748b; font-size:0.78rem; margin-top:1px; }

/* -- sidebar nav buttons -- */
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    justify-content: flex-start; text-align:left; font-weight:500; font-size:0.85rem;
    padding: 0.35rem 0.7rem; border-radius:8px; height:auto; min-height:36px;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button img { vertical-align:middle; margin-right:8px; }
[data-testid="stSidebar"] div[data-testid="stButton"] button p { display:inline; }
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"] {
    background:transparent; border:1px solid transparent; color:#334155;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"]:hover {
    background:#eef2f7; border-color:#e7ebf0; color:#0f172a;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
    background:#eff6ff !important; border:1px solid #bfdbfe !important; color:#1d4ed8 !important;
    box-shadow:none !important; font-weight:600;
}
[data-testid="stSidebar"] hr { margin: 0.6rem 0; }

/* -- header search + actions -- */
[data-testid="stTextInput"] input { font-size:0.85rem; padding: 0.35rem 0.7rem; }

/* -- compact inline nav-link buttons in the main content area (not sidebar) -- */
[data-testid="stMain"] div[data-testid="stButton"] button {
    padding: 0.2rem 0.7rem; font-size: 0.8rem; min-height: 1.9rem;
}

/* -- backup nav row: quiet text links, not a second nav bar -- */
[data-testid="stMain"] div[data-testid="stButton"] button[kind="tertiary"],
[data-testid="stMain"] div[data-testid="stButton"] button[kind="primary"] {
    min-height: 1.3rem; padding: 0.05rem 0.4rem;
}
[data-testid="stMain"] button[kind="tertiary"] {
    color:#94a3b8; font-weight:500; font-size:0.76rem; background:transparent; border:none; box-shadow:none;
}
[data-testid="stMain"] button[kind="tertiary"]:hover { color:#1d4ed8; background:transparent; }
[data-testid="stMain"] button[kind="primary"] {
    background:transparent !important; border:none !important; box-shadow:none !important;
    color:#1d4ed8 !important; font-weight:700 !important; font-size:0.76rem !important;
}

/* -- density: cut default vertical gaps between stacked elements -- */
[data-testid="stVerticalBlock"] { gap: 0.32rem; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Icons -- minimal Feather-style monoline SVGs, rendered as base64 data-URI
# images inside st.button labels (Streamlit renders Markdown images in
# button labels at font-height, so this is a real inline-SVG icon on a real
# clickable widget rather than an HTML overlay hack).
# --------------------------------------------------------------------------
ICON_PATHS = {
    "overview": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "due": '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 15"/>',
    "changed": '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
    "register": '<path d="M9 2h6a1 1 0 0 1 1 1v2H8V3a1 1 0 0 1 1-1z"/><rect x="5" y="4" width="14" height="18" rx="2"/><polyline points="9 12 11 14 15 10"/>',
    "all": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
    "ops": '<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="12" r="2.5"/><path d="M6 8.5V15.5"/><path d="M8.2 7L15.8 10.8"/><path d="M8.2 17L15.8 13.2"/>',
    "trust": '<path d="M12 2l8 4v6c0 5-3.5 9-8 10-4.5-1-8-5-8-10V6z"/><polyline points="9 12 11 14 15 10"/>',
    "search": '<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
}

def icon_svg(name, size=16, color="#475569"):
    paths = ICON_PATHS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )

def icon_data_uri(name, size=16, color="#475569"):
    svg = icon_svg(name, size=size, color=color)
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

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

def load_manifest():
    p = ROOT / "data" / "raw" / "circulars" / "manifest.json"
    return json.load(open(p)) if p.exists() else {}

def get_notification_trigger():
    """Pure function, no Streamlit calls -- so a future email/Slack/webhook
    integration can import and reuse this exact trigger condition without
    pulling in Streamlit. Returns (should_notify, severity)."""
    narrative = load_json("change_narrative.json")
    if not narrative:
        return False, None
    severity = narrative.get("severity")
    return severity in ("High", "Critical"), severity

def severity_pill_class(severity):
    return {"Critical": "pill-rem", "High": "pill-mod"}.get(severity, "pill-neutral")

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

# Hardcoded from output/known_circulars.json / data/raw/circulars/manifest.json --
# the small set of circulars this project actually has a real, verified SEBI
# URL for. Matched by a stable reference-number fragment rather than fuzzy
# string comparison at render time, since source_circular text varies in
# formatting across extraction runs (e.g. "SEBI/HO/..." vs "HO/...") even when
# citing the same circular.
CIRCULAR_URL_MAP = {
    "I/4300/2026": "https://www.sebi.gov.in/legal/master-circulars/feb-2026/master-circular-for-investment-advisers_99569.html",
}

def source_circular_link(source_circular):
    if not source_circular:
        return None
    for key, url in CIRCULAR_URL_MAP.items():
        if key in source_circular:
            return url
    return None

def render_source_provenance(o):
    """Shared source-traceability block: the LLM's quoted verbatim text, the
    independently-matched excerpt from the raw source PDF (proves the match
    exists in context, not just that the model repeated its own quote), and
    a link to the real source circular where one is on file. Used by All
    Obligations and Trust & Audit."""
    if o.get("verbatim_text"):
        st.markdown(f'<div class="verbatim">{esc(o.get("verbatim_text"))}</div>', unsafe_allow_html=True)
    if o.get("source_excerpt"):
        st.markdown('<p class="meta" style="margin-top:8px;margin-bottom:2px;">Matched in source PDF</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="verbatim">&hellip;{esc(o.get("source_excerpt"))}&hellip;</div>', unsafe_allow_html=True)
    url = source_circular_link(o.get("source_circular"))
    if url:
        st.markdown(
            f'<p class="meta" style="margin-top:6px;"><a href="{url}" target="_blank" rel="noopener">View source circular &rarr;</a></p>',
            unsafe_allow_html=True,
        )

def stat_card(value, label, value_color=None):
    """Flat, uniformly-bordered stat card: number + label carry the weight.
    Every card shares the same neutral frame -- color is reserved for the
    number itself, and only where it's a genuine signal (e.g. a risk count),
    not decoration on every card."""
    color = f"color:{value_color};" if value_color else ""
    return (
        f'<div class="stat-card">'
        f'<div class="stat-value" style="{color}">{value}</div>'
        f'<div class="stat-label">{label}</div>'
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

PIPELINE_STAGES = [
    ("PDF", "pdfplumber -- no OCR"),
    ("Chunked LLM Extraction", "qwen2.5:7b via Ollama"),
    ("Schema Validation", "Pydantic"),
    ("Grounding Verification", "rapidfuzz vs source PDF"),
    ("Risk/Department Enrichment", "keyword rules"),
    ("Rule Engine + Compliance Register", "operations.py"),
    ("Diff Engine", "2024 vs 2025"),
    ("Audit Log", "hash chain"),
    ("Dashboard", "this app"),
]

def pipeline_diagram(stages, cols=3, box_w=284, box_h=62, gap_x=36, gap_y=44):
    """Snake-layout SVG flow diagram of the ACTUAL pipeline stages, same raw-SVG
    technique as progress_ring() -- no external diagramming library. Stages
    wrap left-to-right, then right-to-left, so any number of stages fits a
    fixed-width card instead of one long unreadable row."""
    n = len(stages)
    rows = -(-n // cols)
    positions = []
    for i in range(n):
        row, pos = divmod(i, cols)
        col = pos if row % 2 == 0 else cols - 1 - pos
        positions.append((col * (box_w + gap_x), row * (box_h + gap_y)))
    width = cols * box_w + (cols - 1) * gap_x
    height = rows * box_h + (rows - 1) * gap_y

    parts = [
        f'<svg width="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<defs><marker id="pdArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" '
        'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#94a3b8"/></marker></defs>',
    ]
    for i in range(1, n):
        x0, y0 = positions[i - 1]
        x1, y1 = positions[i]
        row_prev, row_curr = (i - 1) // cols, i // cols
        if row_prev == row_curr:
            going_right = row_prev % 2 == 0
            y = y0 + box_h / 2
            sx, ex = (x0 + box_w, x1 - 6) if going_right else (x0, x1 + box_w + 6)
            parts.append(f'<line x1="{sx}" y1="{y}" x2="{ex}" y2="{y}" stroke="#94a3b8" stroke-width="1.75" marker-end="url(#pdArrow)"/>')
        else:
            x = x0 + box_w / 2
            parts.append(f'<line x1="{x}" y1="{y0 + box_h}" x2="{x}" y2="{y1 - 6}" stroke="#94a3b8" stroke-width="1.75" marker-end="url(#pdArrow)"/>')

    for i, (label, sub) in enumerate(stages):
        x, y = positions[i]
        parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" fill="#fff" stroke="#e7ebf0" stroke-width="1.5"/>')
        parts.append(
            f'<text x="{x + 14}" y="{y + box_h/2 - 4}" font-family="ui-monospace,Menlo,monospace" '
            f'font-size="12" font-weight="600" fill="#0f172a">{i+1}. {html.escape(label)}</text>'
        )
        parts.append(
            f'<text x="{x + 14}" y="{y + box_h/2 + 15}" font-family="ui-monospace,Menlo,monospace" '
            f'font-size="10.5" fill="#64748b">{html.escape(sub)}</text>'
        )
    parts.append('</svg>')
    return "".join(parts)

def render_hash_chain(log, valid, broken_at):
    """The product's signature visual (see design direction) -- each audit
    event as a numbered block on a connected rail, showing the literal
    cryptographic linkage (this block's own hash vs. the prev_hash it was
    built from) rather than just a hash blob. Built as one HTML string (not
    one st.markdown per block) so the connecting rail renders as a single
    continuous line in the DOM instead of breaking at each Streamlit widget;
    raw JSON detail uses a native <details> disclosure for the same reason.
    Chronological order (oldest first) so the rail reads top-to-bottom as
    "this produced that", like a ledger."""
    items = []
    for e in log:
        broken = (not valid) and broken_at is not None and e["index"] >= broken_at
        details_json = html.escape(json.dumps(e["details"], indent=2))
        items.append(
            f'<div class="chain-item">'
            f'<div class="chain-dot{" broken" if broken else ""}">{e["index"]}</div>'
            f'<div class="chain-card{" broken" if broken else ""}">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;">'
            f'<span class="chain-event">{esc(e["event_type"].replace("_", " "))}</span>'
            f'<span class="mono">{esc(e["timestamp"][:19])}</span>'
            f'</div>'
            f'<div class="chain-hashline">prev <span>{esc(e["prev_hash"][-12:])}</span> &rarr; hash <b>{esc(e["hash"][-12:])}</b></div>'
            + ('<div style="margin-top:6px;"><span class="pill pill-bad">Chain broken from here</span></div>' if broken else '')
            + '<details style="margin-top:8px;"><summary style="cursor:pointer;font-size:12px;color:#64748b;">Raw event details</summary>'
            + f'<pre class="mono" style="white-space:pre-wrap;margin-top:6px;">{details_json}</pre></details>'
            + '</div></div>'
        )
    st.markdown(f'<div class="chain">{"".join(items)}</div>', unsafe_allow_html=True)

# Keep in sync with run_auto_pipeline.py's STATUS_STEPS.
PIPELINE_RUN_STEPS = [
    ("search", "Search"), ("download", "Download"), ("extract", "Extract"),
    ("verify", "Verify"), ("build_rules", "Build Rules"),
    ("update_register", "Update Register"), ("complete", "Complete"),
]

def pipeline_status_diagram(current_step):
    """Same raw-SVG technique as progress_ring()/pipeline_diagram() -- a
    single-row step tracker for run_auto_pipeline.py's live status, with a
    checkmark for every step already passed."""
    n = len(PIPELINE_RUN_STEPS)
    box_w, box_h, gap = 122, 50, 12
    width = n * box_w + (n - 1) * gap
    current_idx = next((i for i, (k, _) in enumerate(PIPELINE_RUN_STEPS) if k == current_step), None)
    parts = [f'<svg width="100%" viewBox="0 0 {width} {box_h}" xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace,Menlo,monospace">']
    for i, (key, label) in enumerate(PIPELINE_RUN_STEPS):
        x = i * (box_w + gap)
        if current_idx is None:
            state = "pending"
        elif i < current_idx or (i == current_idx and key == "complete"):
            state = "done"
        elif i == current_idx:
            state = "active"
        else:
            state = "pending"
        stroke = "#e7ebf0" if state == "pending" else "#1d4ed8"
        bg = "#fff" if state == "pending" else "#eff6ff"
        text_fill = "#94a3b8" if state == "pending" else ("#1d4ed8" if state == "active" else "#0f172a")
        mark = "✓" if state == "done" else str(i + 1)
        if i < n - 1:
            parts.append(f'<line x1="{x + box_w + 2}" y1="{box_h/2}" x2="{x + box_w + gap - 2}" y2="{box_h/2}" stroke="#cbd5e1" stroke-width="1.5"/>')
        parts.append(f'<rect x="{x}" y="0" width="{box_w}" height="{box_h}" rx="8" fill="{bg}" stroke="{stroke}" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + box_w/2}" y="21" text-anchor="middle" font-size="12" font-weight="700" fill="{text_fill}">{mark}</text>')
        parts.append(f'<text x="{x + box_w/2}" y="37" text-anchor="middle" font-size="10.5" fill="{text_fill}">{html.escape(label)}</text>')
    parts.append('</svg>')
    return "".join(parts)

def ollama_reachable():
    try:
        requests.get("http://localhost:11434", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

# Condensed 5-node view of the same run_auto_pipeline.py steps
# PIPELINE_RUN_STEPS tracks, for the Overview teaser strip. Maps a real
# STATUS_STEPS value to (done_upto, active_idx) in the condensed chain --
# done_upto is the highest condensed index already completed, active_idx is
# the one currently in progress (None if the real step has no exact
# condensed equivalent, e.g. build_rules/update_register fall between
# "Verified" and "Complete"). "search" (still checking, nothing detected
# yet) has no entry on purpose, so a run that never got past search renders
# no partially-filled chain.
CONDENSED_RUN_STEPS = ["Detected", "Downloaded", "Extracted", "Verified", "Complete"]
CONDENSED_STEP_MAP = {
    "download": (0, 1), "extract": (1, 2), "verify": (2, 3),
    "build_rules": (3, None), "update_register": (3, None), "complete": (4, None),
}

def automation_run_strip(done_upto, active_idx, box_w=92, box_h=28, gap=4):
    """Quiet horizontal step indicator for the Overview teaser -- small dots
    on a thin connecting line, not a row of buttons. A status accent, not a
    centerpiece."""
    n = len(CONDENSED_RUN_STEPS)
    width = n * box_w + (n - 1) * gap
    dot_y = 7
    parts = [f'<svg width="100%" viewBox="0 0 {width} {box_h}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,-apple-system,sans-serif">']
    for i, label in enumerate(CONDENSED_RUN_STEPS):
        cx = i * (box_w + gap) + box_w / 2
        if i == active_idx:
            state = "active"
        elif i <= done_upto:
            state = "done"
        else:
            state = "pending"
        if i < n - 1:
            x0, x1 = cx + 6, cx + box_w + gap - 6
            line_color = "#1d4ed8" if state == "done" else "#e2e8f0"
            parts.append(f'<line x1="{x0}" y1="{dot_y}" x2="{x1}" y2="{dot_y}" stroke="{line_color}" stroke-width="1.5"/>')
        if state == "done":
            parts.append(f'<circle cx="{cx}" cy="{dot_y}" r="4.5" fill="#1d4ed8"/>')
            parts.append(f'<path d="M {cx-2.1},{dot_y} l 1.3,1.4 l 2.4,-2.7" stroke="#fff" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        elif state == "active":
            parts.append(f'<circle cx="{cx}" cy="{dot_y}" r="4.5" fill="#fff" stroke="#1d4ed8" stroke-width="1.6"/>')
            parts.append(f'<circle cx="{cx}" cy="{dot_y}" r="1.8" fill="#1d4ed8"/>')
        else:
            parts.append(f'<circle cx="{cx}" cy="{dot_y}" r="4" fill="#fff" stroke="#cbd5e1" stroke-width="1.4"/>')
        text_fill = "#0f172a" if state in ("done", "active") else "#94a3b8"
        weight = "600" if state == "active" else "500"
        parts.append(f'<text x="{cx}" y="{box_h - 3}" text-anchor="middle" font-size="9.5" font-weight="{weight}" fill="{text_fill}">{html.escape(label)}</text>')
    parts.append('</svg>')
    return "".join(parts)

RISK_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
def by_risk(items):
    return sorted(items, key=lambda o: RISK_RANK.get(o.get("risk_band"), 9))

def compute_gaps(obligations):
    """Shared gap-detection logic -- used by both Overview's 'What to do
    next' panel and My Register, so the two views never disagree about what
    counts as a gap. no_ev: no evidence on file. no_dl: a triggered
    (one_time/event_driven) obligation with no stated time limit."""
    no_ev = [o for o in obligations if not o.get("evidence") or o.get("evidence") == "N/A"]
    no_dl = [o for o in obligations if o.get("frequency") in ["one_time", "event_driven"] and not o.get("deadline")]
    return no_ev, no_dl

def gap_ids_for(obligations):
    no_ev, no_dl = compute_gaps(obligations)
    return {o["obligation_id"] for o in no_ev} | {o["obligation_id"] for o in no_dl}

def render_narrative_card(narrative):
    """Shared executive-narrative card markup -- used by both Overview and
    What Changed, so the two views never drift out of sync."""
    actions_html = "".join(f"<li>{esc(a)}</li>" for a in narrative.get("required_actions", []))
    affected_html = ", ".join(esc(a) for a in narrative.get("whos_affected", [])) or "-"
    st.markdown(
        f'<div style="border:1px solid #e7ebf0;border-radius:12px;padding:18px 20px;margin-bottom:1.25rem;background:#fff;">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
        f'<span class="pill {severity_pill_class(narrative.get("severity"))}">{esc(narrative.get("severity"))} severity</span>'
        f'<span style="font-weight:600;color:#0f172a;">Executive summary</span></div>'
        f'<p style="color:#334155;font-size:0.92rem;line-height:1.6;"><b>What changed:</b> {esc(narrative.get("what_changed"))}</p>'
        f'<p style="color:#334155;font-size:0.92rem;line-height:1.6;"><b>Why it matters:</b> {esc(narrative.get("why_it_matters"))}</p>'
        f'<p class="meta"><b>Who\'s affected:</b> {affected_html}</p>'
        + (f'<p class="meta" style="margin-bottom:4px;"><b>Required actions:</b></p><ul class="meta" style="margin-top:0;">{actions_html}</ul>' if actions_html else "")
        + '</div>',
        unsafe_allow_html=True,
    )

EVENT_LABELS = {
    "extraction_2025": "Extracted 2025 obligations",
    "extraction_2024": "Extracted 2024 obligations",
    "diff_2024_2025": "Computed 2024 to 2025 diff",
    "operations_register_built": "Built compliance register",
    "executable_rules_built": "Built executable rules",
    "auto_pipeline_circular_processed": "Processed new circular via automation",
    "change_narrative_generated": "Generated executive change narrative",
    "sebi_monitor_change_detected": "Detected new circular on SEBI site",
}

def humanize_event(event_type):
    return EVENT_LABELS.get(event_type, event_type.replace("_", " ").capitalize())

def last_automation_run():
    """Real 'last run' info for the Overview teaser strip. Prefers the live
    pipeline_status.json (present while run_auto_pipeline.py is actively
    running), and falls back to the audit log's own record of the last
    completed run -- so a finished run whose status file was since cleaned
    up still shows real state instead of nothing."""
    run_status = load_json("pipeline_status.json")
    if run_status:
        r_step = run_status.get("step")
        r_detail = run_status.get("detail") or ""
        r_when = (run_status.get("updated_at") or "")[:19]
        if r_step == "error":
            return {"svg": "", "text": f"Last run hit an error -- {r_detail}", "when": r_when, "details": {}}
        if r_step == "complete" and r_detail.lower().startswith("no "):
            return {"svg": "", "text": r_detail, "when": r_when, "details": {}}
        condensed = CONDENSED_STEP_MAP.get(r_step)
        if condensed is None:
            return {"svg": "", "text": "A check is in progress…", "when": r_when, "details": {}}
        return {"svg": automation_run_strip(*condensed), "text": r_detail, "when": r_when, "details": {}}

    audit = load_json("audit_log.json") or []
    last_processed = next((e for e in reversed(audit) if e["event_type"] == "auto_pipeline_circular_processed"), None)
    if not last_processed:
        return None
    d = last_processed["details"]
    cs = d.get("change_summary", {})
    text = (
        f"{d.get('circular_reference','')} processed — {d.get('obligation_count','?')} obligations extracted, "
        f"{cs.get('added','?')} new / {cs.get('modified','?')} modified / {cs.get('removed','?')} removed vs. prior version"
    )
    return {"svg": automation_run_strip(4, None), "text": text, "when": last_processed["timestamp"][:19], "details": d}

def run_check_for_new_circulars():
    """Shared handler for the header's and the Automation block's 'Check for
    new circulars' buttons -- both write to the same session_state key so
    either entry point shows the same result."""
    try:
        found, _latest = check_for_new_circulars()
        st.session_state["_new_circular_alerts"] = found
    except Exception as e:
        st.session_state["_new_circular_alerts"] = None
        st.session_state["_new_circular_error"] = str(e)

# --------------------------------------------------------------------------
# App shell: sidebar navigation + header bar
# --------------------------------------------------------------------------
NAV_ITEMS = [
    ("overview", "Overview"),
    ("due", "What's Due"),
    ("changed", "What Changed"),
    ("register", "My Register"),
    ("all", "All Obligations"),
    ("ops", "Pipeline Operations"),
    ("trust", "Trust & Audit"),
]

if "page" not in st.session_state:
    st.session_state.page = "overview"

def nav_to(page_key):
    st.session_state.page = page_key
    st.rerun()

# Loaded once at module scope -- used by the sidebar badge and by whichever
# page body actually renders this run, so the data is never fetched twice
# in the same script run.
_obligations, _verified = load_best("obligations_2025")
_register_firm_sel = st.session_state.get("_register_firm_value", "All")
if _obligations:
    _applicable_for_badge = (
        _obligations if _register_firm_sel == "All"
        else [o for o in _obligations if _register_firm_sel in (o.get("applies_to") or [])]
    )
    _register_badge = len(gap_ids_for(_applicable_for_badge))
else:
    _register_badge = None

NAV_BADGES = {"register": _register_badge}

with st.sidebar:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">'
        '<span style="font-family:\'Fraunces\',Georgia,serif;font-weight:700;font-size:1.05rem;color:#0f172a;">Regulatory Compiler</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<p class="meta" style="margin-top:0;">Track 2 &middot; Agentic Compliance</p>', unsafe_allow_html=True)
    st.divider()

    for key, label in NAV_ITEMS:
        active = st.session_state.page == key
        badge = NAV_BADGES.get(key)
        icon_color = "#1d4ed8" if active else "#64748b"
        btn_label = f'![]({icon_data_uri(key, color=icon_color)}) {label}'
        if badge is not None:
            btn_label += f'  `{badge}`'
        if st.button(btn_label, key=f"nav_{key}", type="primary" if active else "secondary", use_container_width=True):
            nav_to(key)

    st.divider()
    st.markdown('<p class="meta" style="margin-bottom:4px;">AUTOMATION</p>', unsafe_allow_html=True)
    zap_label = f'![]({icon_data_uri("zap", color="#1d4ed8")}) Auto Search & Update'
    if st.button(zap_label, key="sidebar_automation", use_container_width=True):
        nav_to("overview")
    st.markdown('<p class="meta" style="font-size:0.72rem;margin-top:2px;">Jumps to the Automation panel on Overview.</p>', unsafe_allow_html=True)

# -- Header bar: title + search only -- no duplicate actions, no identity chrome --
col_title, col_search, col_spacer = st.columns([2.4, 2.8, 2.4], vertical_alignment="center")
with col_title:
    st.markdown(
        '<div class="app-title">SEBI Regulatory Compiler</div>'
        '<div class="app-subtitle">Agentic RegTech Compliance &middot; Securities Market TechSprint 2026</div>',
        unsafe_allow_html=True,
    )
with col_search:
    def _handle_header_search():
        q = st.session_state.get("header_search", "").strip()
        if q:
            st.session_state["all_search"] = q
            st.session_state["header_search"] = ""
            st.session_state["page"] = "all"
    st.text_input(
        "Search", key="header_search", placeholder="Search all obligations, then press Enter…",
        label_visibility="collapsed", on_change=_handle_header_search,
    )

# -- Backup nav row: always-visible, independent of the collapsible sidebar.
# The sidebar has broken invisibly twice now (collapsed with no reopen,
# CSS regressions) -- this row calls the exact same nav_to() the sidebar
# uses, so a sidebar rendering issue can never fully strand a user on one
# page again. Deliberately plain (tertiary buttons, small text) so it reads
# as a quiet backup, not a second real nav bar.
_backup_cols = st.columns(len(NAV_ITEMS))
for _bcol, (_bkey, _blabel) in zip(_backup_cols, NAV_ITEMS):
    with _bcol:
        _bactive = st.session_state.page == _bkey
        if st.button(
            _blabel, key=f"backup_nav_{_bkey}",
            type="primary" if _bactive else "tertiary", use_container_width=True,
        ):
            nav_to(_bkey)

# --------------------------------------------------------------------------
# Page bodies
# --------------------------------------------------------------------------

def render_overview():
    obligations, verified = _obligations, _verified
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh -- your snapshot will appear here.")
        return

    n = len(obligations)
    has_risk = any(o.get("risk_band") for o in obligations)
    urgent = sum(1 for o in obligations if o.get("risk_band") in ("Critical", "High"))
    gap_ids = gap_ids_for(obligations)
    grounded = sum(1 for o in obligations if o.get("grounding_band") == "grounded")
    partial = sum(1 for o in obligations if o.get("grounding_band") == "partial")
    flagged = sum(1 for o in obligations if o.get("grounding_band") == "flagged")
    traceable_pct = round(100 * (grounded + partial) / n, 1) if verified and n else None

    saved = load_json("compliance_status.json") or {}
    statuses = [saved.get(o["obligation_id"], "Not started") for o in obligations]
    compliant = statuses.count("Compliant")
    na = statuses.count("N/A")
    scored = n - na
    pct = int(round(100 * compliant / scored)) if scored else 0

    # -- Row 1: KPI strip --
    cards = (
        '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:8px;">'
        + stat_card(n, "Total obligations")
        + stat_card(urgent if has_risk else "-", "Critical / High risk", value_color="#b91c1c" if has_risk and urgent else None)
        + stat_card(f"{pct}%", "Compliance score")
        + stat_card(len(gap_ids), "Gaps flagged", value_color="#b45309" if gap_ids else None)
        + stat_card(f"{traceable_pct}%" if traceable_pct is not None else "-", "Source-traceable")
        + '</div>'
    )
    st.markdown(cards, unsafe_allow_html=True)

    # -- Compact severity banner (full narrative behind an expander) --
    narrative = load_json("change_narrative.json")
    if narrative:
        sev = narrative.get("severity")
        what = narrative.get("what_changed", "")
        short = (what[:150] + "…") if len(what) > 150 else what
        accent = "#b91c1c" if sev == "Critical" else "#b45309" if sev == "High" else "#1d4ed8"
        st.markdown(
            f'<div style="border:1px solid #e7ebf0;border-left:3px solid {accent};background:#fff;border-radius:8px;'
            f'padding:8px 14px;margin-bottom:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
            f'<span class="pill {severity_pill_class(sev)}">{esc(sev)}</span>'
            f'<span style="font-size:12.5px;color:#334155;">{esc(short)}</span></div>',
            unsafe_allow_html=True,
        )
        with st.expander("View full executive summary"):
            render_narrative_card(narrative)

    # -- Row 2: Recent Circular Ingestion (left) / Priority obligations (right) --
    col_l, col_r = st.columns([1.5, 1])
    with col_l:
        manifest = load_manifest()
        latest_circular = max(manifest.values(), key=lambda v: v.get("processed_at", "")) if manifest else None
        run_info = last_automation_run()

        if latest_circular:
            ref = (run_info.get("details") or {}).get("circular_reference", "") if run_info else ""
            header_line = (
                f'<div style="font-weight:600;color:#0f172a;font-size:13.5px;">{esc(latest_circular["title"])}</div>'
                f'<div class="meta" style="margin-top:1px;">{esc(latest_circular.get("category",""))} &middot; {esc(latest_circular.get("date",""))}'
                + (f' &middot; <span class="mono">{esc(ref)}</span>' if ref else '') + '</div>'
            )
        else:
            header_line = '<p class="meta" style="margin:0;">No circular ingested yet.</p>'

        if run_info:
            strip_html = run_info["svg"]
            run_text = f'<p class="meta" style="margin-top:6px;margin-bottom:0;">{esc(run_info["text"])} &middot; <span class="mono">{esc(run_info["when"])}</span></p>'
        else:
            strip_html = ""
            run_text = '<p class="meta" style="margin:0;">No automation run recorded yet.</p>'

        mini = (
            '<div style="display:flex;gap:26px;margin-top:10px;">'
            f'<div><div style="font-size:17px;font-weight:600;color:#0f172a;">{n}</div><div style="font-size:10.5px;color:#64748b;">obligations extracted</div></div>'
            f'<div><div style="font-size:17px;font-weight:600;color:#0f172a;">{f"{traceable_pct}%" if traceable_pct is not None else "-"}</div><div style="font-size:10.5px;color:#64748b;">verified traceable</div></div>'
            f'<div><div style="font-size:17px;font-weight:600;color:#0f172a;">{flagged if verified else "-"}</div><div style="font-size:10.5px;color:#64748b;">flagged for review</div></div>'
            '</div>'
        )
        st.markdown(
            '<div class="stat-card">'
            '<h5 style="margin-top:0;">Recent Circular Ingestion</h5>'
            + header_line
            + (f'<div style="margin-top:10px;">{strip_html}</div>' if strip_html else '')
            + run_text + mini + '</div>',
            unsafe_allow_html=True,
        )

    with col_r:
        eligible_upcoming = by_risk([o for o in obligations if o.get("deadline") or o.get("trigger")])
        top5 = eligible_upcoming[:5]
        if top5:
            rows = "".join(
                f'<div style="padding:2px 0;border-bottom:1px solid #f1f5f9;">'
                f'<div style="font-size:12.5px;color:#0f172a;font-weight:500;line-height:1.25;">{esc(o.get("title"))}</div>'
                f'{" ".join(b for b in [risk_badge(o), freq_badge(o)] if b)}'
                f'<div class="meta" style="margin-top:1px;font-size:11px;">'
                f'{"Time limit" if o.get("deadline") else "Triggered when"}: {esc(o.get("deadline") or o.get("trigger"))}</div>'
                f'</div>'
                for o in top5
            )
        else:
            rows = '<p class="meta" style="margin:0;">No obligations with a stated deadline or trigger yet.</p>'
        st.markdown(
            '<div class="stat-card"><h5 style="margin-top:0;">Priority obligations</h5>'
            '<p class="meta" style="font-size:11px;margin:0 0 4px;">Highest risk, shown in SEBI\'s own relative wording -- no calendar dates are projected.</p>'
            + rows + '</div>',
            unsafe_allow_html=True,
        )
        if st.button("View all in What's Due →", key="link_due"):
            nav_to("due")

    # -- Row 3: Recent activity (left) / What to do next (right) --
    col_a, col_b = st.columns(2)
    with col_a:
        audit = load_json("audit_log.json") or []
        if audit:
            rows = "".join(
                f'<div style="padding:4px 0;border-bottom:1px solid #f1f5f9;font-size:12px;">'
                f'<span class="mono">{esc(e["timestamp"][:19])}</span> &middot; {esc(humanize_event(e["event_type"]))}</div>'
                for e in list(reversed(audit))[:4]
            )
        else:
            rows = '<p class="meta" style="margin:0;">No pipeline activity recorded yet.</p>'
        st.markdown(f'<div class="stat-card"><h5 style="margin-top:0;">Recent activity</h5>{rows}</div>', unsafe_allow_html=True)

    with col_b:
        if has_risk:
            no_ev, no_dl = compute_gaps(obligations)
            urgent_untouched = [
                o for o in obligations
                if o.get("risk_band") in ("Critical", "High")
                and saved.get(o["obligation_id"], "Not started") == "Not started"
            ]
            next_items = []
            if urgent_untouched:
                next_items.append(f"{len(urgent_untouched)} Critical/High-risk obligation(s) not yet started.")
            if no_ev:
                next_items.append(f"{len(no_ev)} obligation(s) have no evidence on file.")
            if no_dl:
                next_items.append(f"{len(no_dl)} triggered obligation(s) have no deadline stated.")
            next_body = (
                '<ul class="meta" style="margin:0;padding-left:1.1em;">' + "".join(f"<li>{esc(x)}</li>" for x in next_items) + '</ul>'
                if next_items else '<p class="meta" style="margin:0;">Nothing needs attention right now.</p>'
            )
        else:
            next_body = '<p class="meta" style="margin:0;">Run operations.py to see risk-based prioritisation here.</p>'

        r = load_json("change_impact_report.json")
        if r:
            s = r["summary"]
            changes_line = f'<p class="meta" style="margin:6px 0 0;">{s["added"]} new &middot; {s["modified"]} modified &middot; {s["removed"]} removed since the prior circular.</p>'
        else:
            changes_line = ""
        st.markdown(f'<div class="stat-card"><h5 style="margin-top:0;">What to do next</h5>{next_body}{changes_line}</div>', unsafe_allow_html=True)
        if r and st.button("View in What Changed →", key="link_changed"):
            nav_to("changed")

    # -- Automation (reachable from the sidebar's Auto Search & Update card) --
    st.write("")
    with st.container(border=True):
        st.markdown('<div id="automation-section"></div>', unsafe_allow_html=True)
        st.markdown("##### Automation")
        st.markdown('<p class="meta">Checking is always safe -- it only reads SEBI\'s live listing. Running the full pipeline needs a local Ollama instance.</p>', unsafe_allow_html=True)

        if st.button("Check for new circulars", key="ov_check_circulars"):
            run_check_for_new_circulars()

        alerts_found = st.session_state.get("_new_circular_alerts")
        _check_err = st.session_state.get("_new_circular_error")
        if _check_err:
            st.error(f"Could not reach SEBI's listing page: {_check_err}")
        elif alerts_found:
            st.warning(
                f"{len(alerts_found)} new circular(s) detected: "
                + ", ".join(f"{cat} ({row['date']})" for cat, _prev, row in alerts_found)
            )
        elif alerts_found is not None:
            st.success("No changes — all tracked circulars match the last known version.")

        if alerts_found:
            if ollama_reachable():
                if st.button("Run full pipeline now", key="ov_run_pipeline"):
                    subprocess.Popen(["python3", "run_auto_pipeline.py"], cwd=str(ROOT))
                    st.success("Pipeline launched in the background. Use \"Refresh status\" below to check progress.")
            else:
                st.info("Local extraction not available here -- run `python3 run_auto_pipeline.py` from your terminal.")

        st.write("")
        st.button("Refresh status", key="ov_refresh_status")
        run_status = load_json("pipeline_status.json")
        if run_status:
            if run_status.get("step") == "error":
                st.error(f"Pipeline error: {run_status.get('detail','')}")
            else:
                st.markdown(pipeline_status_diagram(run_status.get("step")), unsafe_allow_html=True)
                st.markdown(
                    f'<p class="meta" style="margin-top:6px;">{esc(run_status.get("detail"))} &middot; '
                    f'<span class="mono">{esc((run_status.get("updated_at") or "")[:19])}</span></p>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<p class="meta">No pipeline run recorded yet.</p>', unsafe_allow_html=True)


def render_due():
    st.markdown("#### What's Due")
    st.markdown('<p class="meta">Your obligations organised by when they come due -- the recurring filing rhythm, the event-triggered deadlines, and the continuous duties.</p>', unsafe_allow_html=True)
    obligations, verified = _obligations, _verified
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh.")
        return

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


def render_changed():
    st.markdown("#### What Changed - 2024 to 2025")
    st.markdown('<p class="meta">What changed in the new circular, and exactly what it now requires you to do.</p>', unsafe_allow_html=True)

    narrative = load_json("change_narrative.json")
    if narrative:
        render_narrative_card(narrative)

    r = load_json("change_impact_report.json")
    if not r:
        st.info("No change report yet. Run extract_2024.py, then diff_engine.py, then refresh.")
        return

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


def render_register():
    st.markdown("#### My Register")
    st.markdown('<p class="meta">Filter to the obligations that bind your firm, track where you stand on each one, and see what still needs attention.</p>', unsafe_allow_html=True)
    obligations, verified = _obligations, _verified
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh.")
        return

    firm_labels = {
        "investment_adviser": "Investment Adviser",
        "stock_broker": "Stock Broker",
        "research_analyst": "Research Analyst",
    }
    STATUSES = ["Not started", "In progress", "Compliant", "N/A"]

    # Streamlit forgets a widget's session_state value once a script run goes
    # by without that widget being instantiated -- which now happens every
    # time the sidebar nav switches to a different page. So unsaved
    # selections must be mirrored into plain (non-widget) session_state
    # entries that survive regardless of which page is currently rendering,
    # and used as the widgets' `index` default instead of relying on the
    # widget's own key still being populated.
    saved = load_json("compliance_status.json") or {}
    if "_register_status_overrides" not in st.session_state:
        st.session_state["_register_status_overrides"] = {}
    overrides = st.session_state["_register_status_overrides"]

    def current_status(oid):
        return overrides.get(oid, saved.get(oid, "Not started"))

    def sync_status(oid):
        st.session_state["_register_status_overrides"][oid] = st.session_state[f"status_{oid}"]

    if "_register_firm_value" not in st.session_state:
        st.session_state["_register_firm_value"] = "All"

    def sync_firm():
        st.session_state["_register_firm_value"] = st.session_state["register_firm"]

    firm_options = ["All"] + list(firm_labels.keys())
    firm = st.selectbox(
        "Your firm type",
        firm_options,
        index=firm_options.index(st.session_state["_register_firm_value"]),
        format_func=lambda k: "All firm types" if k == "All" else firm_labels.get(k, k),
        key="register_firm",
        on_change=sync_firm,
    )
    if firm == "All":
        applicable = obligations
    else:
        applicable = [o for o in obligations if firm in (o.get("applies_to") or [])]

    no_ev, no_dl = compute_gaps(applicable)
    gap_ids = {o["obligation_id"] for o in no_ev} | {o["obligation_id"] for o in no_dl}

    counts = {s: 0 for s in STATUSES}
    for o in applicable:
        s = current_status(o["obligation_id"])
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
        out = {o["obligation_id"]: current_status(o["obligation_id"]) for o in obligations}
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
            st.selectbox(
                "Status", STATUSES, index=STATUSES.index(current_status(oid)),
                key=f"status_{oid}", on_change=sync_status, args=(oid,),
            )
            if o.get("source_clause"):
                st.markdown(f'Source: <span class="clause">{esc(o.get("source_clause"))}</span>', unsafe_allow_html=True)


def render_all():
    st.markdown("#### All Obligations")
    st.markdown('<p class="meta">The complete 2025 obligation graph -- browse, search, and filter by any dimension. For your day-to-day view, use My Register.</p>', unsafe_allow_html=True)
    obligations, verified = _obligations, _verified
    if obligations is None:
        st.info("No obligations yet. Run extract_full.py, then refresh.")
        return

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
    search = st.text_input("Search", key="all_search")
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
            render_source_provenance(o)


def render_ops():
    st.markdown("#### Pipeline Operations")
    st.markdown('<p class="meta">Compliance register and executable rules -- the machine-checkable core the rest of this dashboard is built on. See What\'s Due for the calendar view.</p>', unsafe_allow_html=True)

    st.markdown("##### How a circular becomes this dashboard")
    st.markdown('<p class="meta">The actual stages this pipeline runs, in order -- direct PDF text extraction only, no OCR fallback.</p>', unsafe_allow_html=True)
    st.markdown(pipeline_diagram(PIPELINE_STAGES), unsafe_allow_html=True)
    st.write("")

    register = load_json("compliance_register.json")
    rules = load_json("executable_rules.json")
    if not register:
        st.info("Not built yet. Run: python operations.py")
        return

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


def render_trust():
    obligations_for_summary, _ = _obligations, _verified
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
    obligations, verified = _obligations, _verified
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
                        render_source_provenance(o)

    st.divider()
    st.markdown("#### Audit Trail")
    st.markdown('<p class="meta">A hash-chained, tamper-evident log of every pipeline run. Altering any past entry breaks the chain from that point forward.</p>', unsafe_allow_html=True)
    log = load_json("audit_log.json")
    if not log:
        st.info("No audit log yet. Run: python build_audit_log.py")
        return

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
    render_hash_chain(log, valid, broken_at)


PAGE_RENDERERS = {
    "overview": render_overview,
    "due": render_due,
    "changed": render_changed,
    "register": render_register,
    "all": render_all,
    "ops": render_ops,
    "trust": render_trust,
}

PAGE_RENDERERS[st.session_state.page]()
