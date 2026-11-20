"""An animated person walking a dog on a leash, as a self-contained SVG (no external files).

Used two ways in app.py: as the "Running..." indicator Streamlit shows in the top-right while the
script runs, and as the loading animation inside the Ask PawPal panel.
"""
from __future__ import annotations

import base64


def _swing(cx: int, cy: int, deg: int, dur: str = "0.6s", flip: bool = False) -> str:
    """SMIL animation rotating a limb back and forth around its top joint (cx, cy)."""
    a, b = (deg, -deg) if not flip else (-deg, deg)
    return (
        f'<animateTransform attributeName="transform" type="rotate" dur="{dur}" repeatCount="indefinite" '
        f'values="{a} {cx} {cy};{b} {cx} {cy};{a} {cx} {cy}"/>'
    )


WALK_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 72" width="200" height="72">
  <line x1="0" y1="64" x2="200" y2="64" stroke="#8a8a8a" stroke-width="2" stroke-dasharray="10 8" stroke-linecap="round">
    <animate attributeName="stroke-dashoffset" from="0" to="18" dur="0.6s" repeatCount="indefinite"/>
  </line>
  <g>
    <animateTransform attributeName="transform" type="translate" values="0 0;0 -1.5;0 0" dur="0.3s" repeatCount="indefinite"/>
    <!-- person -->
    <g stroke="#ff6b6b" stroke-width="4" stroke-linecap="round" fill="none">
      <circle cx="58" cy="14" r="7" fill="#ff6b6b" stroke="none"/>
      <line x1="58" y1="22" x2="58" y2="42"/>
      <line x1="58" y1="42" x2="58" y2="62">{_swing(58, 42, 28)}</line>
      <line x1="58" y1="42" x2="58" y2="62">{_swing(58, 42, 28, flip=True)}</line>
      <line x1="58" y1="28" x2="82" y2="38"/>
      <line x1="58" y1="28" x2="48" y2="40">{_swing(58, 28, 20)}</line>
    </g>
    <!-- leash -->
    <path d="M82 38 Q108 52 134 44" stroke="#b0b0b0" stroke-width="1.6" fill="none"/>
    <!-- dog -->
    <g stroke="#d98e3f" stroke-width="3.5" stroke-linecap="round" fill="#d98e3f">
      <ellipse cx="124" cy="46" rx="17" ry="8" stroke="none"/>
      <circle cx="144" cy="39" r="6.5" stroke="none"/>
      <polygon points="150,40 158,43 150,45" stroke="none"/>
      <polygon points="141,34 138,26 146,32" fill="#a8672a" stroke="none"/>
      <circle cx="146" cy="37" r="1.2" fill="#222" stroke="none"/>
      <line x1="108" y1="42" x2="100" y2="32" fill="none">{_swing(108, 42, 22, "0.25s")}</line>
      <line x1="114" y1="52" x2="114" y2="62" fill="none">{_swing(114, 52, 30)}</line>
      <line x1="120" y1="52" x2="120" y2="62" fill="none">{_swing(120, 52, 30, flip=True)}</line>
      <line x1="130" y1="52" x2="130" y2="62" fill="none">{_swing(130, 52, 30, flip=True)}</line>
      <line x1="136" y1="52" x2="136" y2="62" fill="none">{_swing(136, 52, 30)}</line>
    </g>
  </g>
</svg>"""

_B64 = base64.b64encode(WALK_SVG.encode()).decode()
DATA_URI = f"data:image/svg+xml;base64,{_B64}"

# Replaces Streamlit's own running-man indicator (shown whenever the script is running).
STATUS_WIDGET_CSS = f"""
<style>
[data-testid="stStatusWidget"] > * {{ display: none !important; }}
[data-testid="stStatusWidget"]::before {{
    content: "";
    display: block;
    width: 120px;
    height: 43px;
    background: url("{DATA_URI}") center / contain no-repeat;
}}
</style>
"""


def loading_html(message: str = "Walking over to the pet-care guide...") -> str:
    """HTML for the in-panel loading animation."""
    return (
        '<div style="text-align:center;padding:0.5rem 0">'
        f'<img src="{DATA_URI}" width="200" alt="A person walking a dog"/>'
        f'<div style="opacity:0.7;font-size:0.9rem">{message}</div></div>'
    )
