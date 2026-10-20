CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1150px;}
.hero {background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
       padding: 28px 32px; border-radius: 16px; margin-bottom: 20px;}
.hero h1 {color: #FFFFFF; margin: 0; font-size: 2.1rem;}
.hero p {color: #E0E7FF; margin: 6px 0 0 0; font-size: 1.05rem;}
.card {background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px;
       padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
       text-align: center; min-height: 210px;
       display: flex; flex-direction: column; justify-content: center;}
.card .label {color: #6B7280; font-size: 0.8rem; text-transform: uppercase;
              letter-spacing: 0.06em; margin-bottom: 6px;}
.card .value {font-size: 2rem; font-weight: 700; color: #111827; white-space: nowrap}
.ring {width: 120px; height: 120px; border-radius: 50%; margin: 0 auto;
       display: flex; align-items: center; justify-content: center;}
.ring-inner {width: 92px; height: 92px; border-radius: 50%; background: #FFFFFF;
             display: flex; align-items: center; justify-content: center;
             font-size: 1.6rem; font-weight: 700; color: #111827;}
.chip {display: inline-block; padding: 6px 12px; margin: 4px;
       border-radius: 999px; font-size: 0.85rem; font-weight: 500;}
.chip-ok {background: #DCFCE7; color: #166534;}
.chip-miss {background: #FEE2E2; color: #991B1B;}
</style>
"""


def hero(title, subtitle):
    return f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>'


def card(label, value):
    return (f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value">{value}</div></div>')


def score_ring(pct, color):
    return (f'<div class="card"><div class="label">ATS score</div>'
            f'<div class="ring" style="background: conic-gradient('
            f'{color} {pct}%, #E5E7EB 0)">'
            f'<div class="ring-inner">{pct}%</div></div></div>')


def chips(skills, kind):
    css = "chip-ok" if kind == "ok" else "chip-miss"
    return "".join(f'<span class="chip {css}">{s}</span>' for s in skills)


def score_color(pct, target):
    if pct >= target:
        return "#16A34A"
    if pct >= 70:
        return "#F59E0B"
    return "#DC2626"