"""
FAM-FIOS UI kit: global styles and small presentational helpers for the Streamlit app.

Everything here is visual only — no application state or business logic.
"""

import base64
import html
import io
from typing import Iterable, Optional, Sequence

import streamlit as st

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    QRCODE_AVAILABLE = False


_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --ff-bg: #0B1220;
    --ff-surface: #111A2E;
    --ff-surface-2: #16213A;
    --ff-border: #22304D;
    --ff-border-strong: #2E3F63;
    --ff-text: #E6EAF2;
    --ff-text-muted: #94A3B8;
    --ff-text-subtle: #64748B;
    --ff-primary: #3B82F6;
    --ff-primary-soft: rgba(59, 130, 246, 0.12);
    --ff-success: #10B981;
    --ff-warning: #F59E0B;
    --ff-danger: #EF4444;
    --ff-radius: 12px;
    --ff-radius-sm: 8px;
}

html, body, [class*="st-"], .stMarkdown, .stText, button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
code, pre, .stCode, [data-testid="stCode"] * {
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace !important;
}
/* Keep Streamlit's icon font for expander arrows etc. */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-icons"] {
    font-family: 'Material Symbols Rounded' !important;
}

/* Layout */
.block-container {
    padding-top: 2.25rem !important;
    padding-bottom: 4rem !important;
    max-width: 1440px;
}
header[data-testid="stHeader"] {
    background: transparent;
}
footer, #MainMenu { visibility: hidden; }

/* Typography */
h1, h2, h3, h4, h5 { letter-spacing: -0.015em; color: var(--ff-text); }
.stMarkdown p, .stMarkdown li { line-height: 1.6; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--ff-text-muted) !important; }
hr { border-color: var(--ff-border) !important; margin: 1.5rem 0 !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0D1526;
    border-right: 1px solid var(--ff-border);
}
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1.25rem;
}
section[data-testid="stSidebar"] hr { margin: 1rem 0 !important; }

/* Sidebar navigation: render the portal radio as a menu */
section[data-testid="stSidebar"] [role="radiogroup"] { gap: 2px; }
section[data-testid="stSidebar"] [role="radiogroup"] > label {
    padding: 9px 12px;
    border-radius: var(--ff-radius-sm);
    margin: 0;
    width: 100%;
    transition: background 0.15s ease;
    cursor: pointer;
}
section[data-testid="stSidebar"] [role="radiogroup"] > label:hover { background: var(--ff-surface-2); }
section[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child:not(:has([data-testid="stMarkdownContainer"])),
section[data-testid="stSidebar"] [role="radiogroup"] div:has(+ [data-testid="stMarkdownContainer"]) { display: none; }
section[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
    background: var(--ff-primary-soft);
    box-shadow: inset 2px 0 0 var(--ff-primary);
}
section[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p {
    color: #DBE7FF; font-weight: 600;
}
section[data-testid="stSidebar"] [role="radiogroup"] p { font-size: 14px; }

/* Buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: var(--ff-radius-sm);
    font-weight: 500;
    border: 1px solid var(--ff-border-strong);
    transition: all 0.15s ease;
    min-height: 2.6rem;
}
.stButton > button p { white-space: normal; line-height: 1.35; }
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: var(--ff-primary);
    color: #DBE7FF;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: var(--ff-primary);
    border-color: var(--ff-primary);
    color: #FFFFFF;
}
.stButton > button[kind="primary"]:hover {
    background: #2563EB;
    border-color: #2563EB;
    color: #FFFFFF;
}

/* Inputs */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
    border-radius: var(--ff-radius-sm) !important;
}
label[data-testid="stWidgetLabel"] p { font-size: 13px; font-weight: 500; color: #CBD5E1; }

/* Metrics as KPI cards */
[data-testid="stMetric"] {
    background: var(--ff-surface);
    border: 1px solid var(--ff-border);
    border-radius: var(--ff-radius);
    padding: 16px 18px;
}
[data-testid="stMetricLabel"] p {
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ff-text-muted) !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] > div { white-space: normal !important; overflow-wrap: anywhere; line-height: 1.25; }
[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* Bordered containers as cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--ff-radius) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
    border-color: var(--ff-border) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid var(--ff-border);
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    height: auto;
    padding: 10px 14px;
    border-radius: var(--ff-radius-sm) var(--ff-radius-sm) 0 0;
    font-size: 14px;
    font-weight: 500;
    color: var(--ff-text-muted);
}
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--ff-text); }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--ff-primary); }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem; }

/* Alerts, expanders, tables */
[data-testid="stAlert"], [data-testid="stNotification"] { border-radius: var(--ff-radius) !important; }
[data-testid="stExpander"] details {
    border-radius: var(--ff-radius) !important;
    border-color: var(--ff-border) !important;
    background: var(--ff-surface);
}
[data-testid="stExpander"] summary p { font-weight: 500; }
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--ff-border);
    border-radius: var(--ff-radius);
    overflow: hidden;
}
[data-testid="stProgress"] > div > div > div { border-radius: 999px; }

/* Horizontal radios read as segmented choices */
.stRadio [role="radiogroup"][aria-orientation="horizontal"] { gap: 8px; flex-wrap: wrap; }

/* --- Custom components --- */
.ff-brand { display: flex; align-items: center; gap: 12px; margin: 4px 0 6px 0; }
.ff-brand-mark {
    width: 38px; height: 38px; border-radius: 10px;
    background: linear-gradient(135deg, #3B82F6, #6366F1);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; color: #fff; font-size: 15px; letter-spacing: -0.02em;
}
.ff-brand-name { font-weight: 700; font-size: 17px; color: var(--ff-text); line-height: 1.1; }
.ff-brand-tag { font-size: 12px; color: var(--ff-text-muted); line-height: 1.3; }

.ff-nav-label {
    font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ff-text-subtle); margin: 4px 0 8px 2px;
}

.ff-page-header { margin: 0 0 1.5rem 0; padding-bottom: 1.25rem; border-bottom: 1px solid var(--ff-border); }
.ff-eyebrow {
    font-size: 12px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ff-primary); margin-bottom: 6px;
}
.ff-page-title { font-size: 30px; font-weight: 700; letter-spacing: -0.02em; color: var(--ff-text); line-height: 1.2; }
.ff-page-subtitle { font-size: 15px; color: var(--ff-text-muted); margin-top: 8px; max-width: 880px; line-height: 1.6; }
.ff-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.ff-chip {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 500; color: #CBD5E1;
    background: var(--ff-surface); border: 1px solid var(--ff-border);
    padding: 4px 10px; border-radius: 999px;
}
.ff-chip b { color: var(--ff-text); font-weight: 600; }
.ff-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }

.ff-section { margin: 0.75rem 0 0.75rem 0; }
.ff-section-title { font-size: 19px; font-weight: 600; color: var(--ff-text); letter-spacing: -0.01em; }
.ff-section-title.l4 { font-size: 16px; }
.ff-section-title.l5 { font-size: 14px; color: #CBD5E1; }
.ff-section-caption { font-size: 13px; color: var(--ff-text-muted); margin-top: 4px; }
.ff-step {
    display: inline-block; font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
    color: var(--ff-primary); background: var(--ff-primary-soft);
    padding: 2px 8px; border-radius: 6px; margin-right: 8px; vertical-align: middle;
}

.ff-stepper { display: flex; align-items: center; gap: 0; margin: 0 0 1.5rem 0; flex-wrap: wrap; }
.ff-stepper-item { display: flex; align-items: center; gap: 10px; }
.ff-stepper-num {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 600;
    border: 1px solid var(--ff-border-strong); color: var(--ff-text-muted); background: var(--ff-surface);
}
.ff-stepper-text { font-size: 14px; color: var(--ff-text-muted); font-weight: 500; }
.ff-stepper-item.done .ff-stepper-num { background: var(--ff-success); border-color: var(--ff-success); color: #fff; }
.ff-stepper-item.done .ff-stepper-text { color: #CBD5E1; }
.ff-stepper-item.active .ff-stepper-num { background: var(--ff-primary); border-color: var(--ff-primary); color: #fff; }
.ff-stepper-item.active .ff-stepper-text { color: var(--ff-text); font-weight: 600; }
.ff-stepper-line { width: 48px; height: 1px; background: var(--ff-border-strong); margin: 0 14px; }

.ff-kv-list { display: flex; flex-direction: column; gap: 8px; }
.ff-kv { display: flex; justify-content: space-between; gap: 16px; font-size: 14px; }
.ff-kv-k { color: var(--ff-text-muted); white-space: nowrap; }
.ff-kv-v { color: var(--ff-text); text-align: right; font-weight: 500; }
.ff-kv-total { margin-top: 6px; padding-top: 10px; border-top: 1px solid var(--ff-border); }
.ff-kv-total .ff-kv-k { color: var(--ff-text); font-weight: 600; font-size: 15px; }
.ff-kv-total .ff-kv-v { font-size: 20px; font-weight: 700; }

.ff-pass {
    background: linear-gradient(145deg, #111A2E 0%, #172554 100%);
    border: 1px solid var(--ff-border-strong);
    border-radius: 16px; padding: 22px 24px; position: relative; overflow: hidden;
}
.ff-pass::after {
    content: ""; position: absolute; right: -60px; top: -60px; width: 200px; height: 200px;
    border-radius: 50%; background: radial-gradient(circle, rgba(59,130,246,0.25), transparent 70%);
}
.ff-pass-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
.ff-pass-label { font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ff-text-muted); }
.ff-pass-name { font-size: 22px; font-weight: 700; color: #fff; margin-top: 2px; }
.ff-pass-status {
    font-size: 11px; font-weight: 600; letter-spacing: 0.06em; color: #6EE7B7;
    background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.35);
    padding: 4px 10px; border-radius: 999px; white-space: nowrap;
}
.ff-pass-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 20px; }
.ff-pass-value { font-size: 14px; color: var(--ff-text); font-weight: 500; margin-top: 2px; word-break: break-word; }
.ff-pass-foot {
    display: flex; justify-content: space-between; align-items: center; gap: 16px;
    margin-top: 18px; padding-top: 16px; border-top: 1px dashed var(--ff-border-strong);
}
.ff-pass-id { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #CBD5E1; }
.ff-pass-qr { background: #fff; border-radius: 8px; padding: 6px; line-height: 0; }

.ff-qr-card {
    background: var(--ff-surface); border: 1px solid var(--ff-border); border-radius: var(--ff-radius);
    padding: 18px; display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.ff-qr-img { background: #fff; padding: 10px; border-radius: 10px; line-height: 0; }
.ff-qr-caption { font-size: 13px; color: var(--ff-text-muted); text-align: center; }
.ff-qr-amount { font-size: 18px; font-weight: 700; color: var(--ff-text); }

@media (max-width: 768px) {
    .ff-page-title { font-size: 24px; }
    .ff-stepper-line { width: 20px; margin: 0 8px; }
    .ff-pass-grid { grid-template-columns: 1fr; }
}
</style>
"""


def _e(value) -> str:
    """HTML-escapes any value for safe interpolation."""
    return html.escape(str(value), quote=True)


def inject_global_styles() -> None:
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def sidebar_brand(name: str, tagline: str) -> None:
    st.sidebar.markdown(
        f"""
        <div class="ff-brand">
            <div class="ff-brand-mark">FF</div>
            <div>
                <div class="ff-brand-name">{_e(name)}</div>
                <div class="ff-brand-tag">{_e(tagline)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_label(text: str, container=None) -> None:
    (container or st).markdown(f'<div class="ff-nav-label">{_e(text)}</div>', unsafe_allow_html=True)


def chip(label: str, value: str = "", dot_color: Optional[str] = None) -> str:
    """Returns HTML for a small metadata chip, for use with page_header(chips=...)."""
    dot = f'<span class="ff-dot" style="background:{_e(dot_color)}"></span>' if dot_color else ""
    val = f" <b>{_e(value)}</b>" if value else ""
    return f'<span class="ff-chip">{dot}{_e(label)}{val}</span>'


def page_header(
    title: str,
    subtitle: Optional[str] = None,
    eyebrow: Optional[str] = None,
    chips: Optional[Iterable[str]] = None,
) -> None:
    eyebrow_html = f'<div class="ff-eyebrow">{_e(eyebrow)}</div>' if eyebrow else ""
    subtitle_html = f'<div class="ff-page-subtitle">{_e(subtitle)}</div>' if subtitle else ""
    chips_html = f'<div class="ff-chips">{"".join(chips)}</div>' if chips else ""
    st.markdown(
        f'<div class="ff-page-header">{eyebrow_html}<div class="ff-page-title">{_e(title)}</div>'
        f"{subtitle_html}{chips_html}</div>",
        unsafe_allow_html=True,
    )


def section_header(title: str, caption: Optional[str] = None, level: int = 3, step: Optional[int] = None) -> None:
    step_html = f'<span class="ff-step">STEP {int(step)}</span>' if step else ""
    caption_html = f'<div class="ff-section-caption">{_e(caption)}</div>' if caption else ""
    level_cls = "" if level <= 3 else f" l{min(level, 5)}"
    st.markdown(
        f'<div class="ff-section"><div class="ff-section-title{level_cls}">{step_html}{_e(title)}</div>'
        f"{caption_html}</div>",
        unsafe_allow_html=True,
    )


def kv_rows(rows: Sequence[tuple], total: Optional[tuple] = None) -> None:
    """Renders label/value pairs as aligned rows, with an optional emphasized total row."""
    body = "".join(
        f'<div class="ff-kv"><span class="ff-kv-k">{_e(k)}</span><span class="ff-kv-v">{_e(v)}</span></div>'
        for k, v in rows
    )
    if total:
        body += (
            f'<div class="ff-kv ff-kv-total"><span class="ff-kv-k">{_e(total[0])}</span>'
            f'<span class="ff-kv-v">{_e(total[1])}</span></div>'
        )
    st.markdown(f'<div class="ff-kv-list">{body}</div>', unsafe_allow_html=True)


def step_indicator(steps: Sequence[str], active_index: int) -> None:
    parts = []
    for i, label in enumerate(steps):
        state = "done" if i < active_index else ("active" if i == active_index else "")
        num = "&#10003;" if i < active_index else str(i + 1)
        parts.append(
            f'<div class="ff-stepper-item {state}"><div class="ff-stepper-num">{num}</div>'
            f'<div class="ff-stepper-text">{_e(label)}</div></div>'
        )
        if i < len(steps) - 1:
            parts.append('<div class="ff-stepper-line"></div>')
    st.markdown(f'<div class="ff-stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


def qr_data_uri(payload: str, box_size: int = 6) -> Optional[str]:
    """Renders payload as a PNG QR code data URI, or None if qrcode isn't installed."""
    if not QRCODE_AVAILABLE:
        return None
    qr = qrcode.QRCode(border=1, box_size=box_size, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B1220", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def upi_qr_card(vpa: str, payee_name: str, amount: float, note: str) -> None:
    from urllib.parse import quote
    upi_uri = f"upi://pay?pa={quote(vpa)}&pn={quote(payee_name)}&am={amount:.2f}&cu=INR&tn={quote(note)}"
    uri = qr_data_uri(upi_uri, box_size=6)
    img_html = (
        f'<div class="ff-qr-img"><img src="{uri}" width="200" height="200" alt="UPI QR code"/></div>'
        if uri else '<div class="ff-qr-caption">QR code unavailable</div>'
    )
    st.markdown(
        f"""
        <div class="ff-qr-card">
            {img_html}
            <div class="ff-qr-amount">₹{amount:,.2f}</div>
            <div class="ff-qr-caption">Scan with any UPI app &middot; BHIM, Google Pay, PhonePe, Paytm</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def membership_pass(
    member_name: str,
    member_id: str,
    gym_name: str,
    location: str,
    address: str,
    phone: str,
    plan: str,
    amount_paid: str,
    valid_until: str,
) -> None:
    uri = qr_data_uri(f"FAMFIOS:{member_id}", box_size=3)
    qr_html = f'<div class="ff-pass-qr"><img src="{uri}" width="84" height="84" alt="Pass QR"/></div>' if uri else ""
    fields = [
        ("Facility", gym_name),
        ("City & Branch", location),
        ("Plan", plan),
        ("Amount Paid", amount_paid),
        ("Valid Until", valid_until),
        ("Phone", phone),
    ]
    grid = "".join(
        f'<div><div class="ff-pass-label">{_e(k)}</div><div class="ff-pass-value">{_e(v)}</div></div>'
        for k, v in fields
        if v and str(v).strip() not in ("—", "-")
    )
    st.markdown(
        f"""
        <div class="ff-pass">
            <div class="ff-pass-head">
                <div>
                    <div class="ff-pass-label">Digital Fitness Pass</div>
                    <div class="ff-pass-name">{_e(member_name)}</div>
                </div>
                <div class="ff-pass-status">ACTIVE</div>
            </div>
            <div class="ff-pass-grid">{grid}</div>
            <div class="ff-pass-foot">
                <div>
                    <div class="ff-pass-label">Member ID</div>
                    <div class="ff-pass-id">{_e(member_id)}</div>
                    <div class="ff-pass-label" style="margin-top:8px; text-transform:none; letter-spacing:0;">{_e(address)}</div>
                </div>
                {qr_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
