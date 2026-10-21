"""Renders assets/terminal.svg: a two-pane terminal running kubectl against me.

Project ages are computed at render time, so the weekly workflow keeps them current.
"""
import random
import sys
from datetime import date
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "terminal.svg"

# Palette of ismd.dev.
INK, PAPER, QUIET, MUTED = "#292438", "#f3effb", "#cec6db", "#9d94b1"
LIME, LILAC, LINE = "#d6f578", "#c6b4f6", "#514960"

W = 860
CW = 8.4  # monospace advance at 14px; typed commands are pinned to it with textLength
LH = 21
Y0 = 84
SPLIT = 412
PANES = (28, SPLIT + 20)

LEFT_CMD = "kubectl get engineer ismd -o yaml"
RIGHT_CMD = "kubectl get projects"

# (indent, [(class, text), ...])
ENGINEER = [
    (0, [("k", "apiVersion"), ("p", ": "), ("v", "people.ismd.dev/v1")]),
    (0, [("k", "kind"), ("p", ": "), ("v", "Engineer")]),
    (0, [("k", "metadata"), ("p", ":")]),
    (2, [("k", "name"), ("p", ": "), ("v", "vladimir-kostelei")]),
    (2, [("k", "namespace"), ("p", ": "), ("v", "internet")]),
    (2, [("k", "labels"), ("p", ": {"), ("k", "role"), ("p", ": "), ("v", "software-engineer"), ("p", "}")]),
    (2, [("k", "annotations"), ("p", ": {"), ("k", "yandex.ru/tech-lead"), ("p", ": "), ("v", "8y"), ("p", "}")]),
    (0, [("k", "spec"), ("p", ":")]),
    (2, [("k", "languages"), ("p", ": ["), ("v", "go, typescript, python, elisp"), ("p", "]")]),
    (2, [("k", "platform"), ("p", ": ["), ("v", "k8s, terraform, helm"), ("p", "]")]),
    (2, [("k", "certifications"), ("p", ": ["), ("v", "CKA"), ("p", "]")]),
    (2, [("k", "editor"), ("p", ": "), ("v", "emacs")]),
    (0, [("k", "status"), ("p", ":")]),
    (2, [("k", "phase"), ("p", ": "), ("s", "Running")]),
    (2, [("k", "building"), ("p", ": "), ("v", "linktheca")]),
]

# (name, stack, status, created)
PROJECTS = [
    ("linktheca", "go", "Running", date(2026, 4, 10)),
    ("preview-tab.el", "elisp", "Running", date(2026, 8, 19)),
    ("blackarch-docker", "docker", "Running", date(2026, 1, 11)),
    ("hugo-theme-vng-blue", "hugo", "Running", date(2025, 1, 22)),
    ("coding-overhead.com", "hugo", "Running", date(2024, 10, 7)),
    ("dotfiles", "chezmoi", "Running", date(2025, 12, 14)),
    ("screenshotgun", "c++/qt", "Completed", date(2014, 6, 16)),
]


def k8s_age(created, today):
    """Day-resolution port of HumanDuration from k8s.io/apimachinery."""
    days = (today - created).days
    if days < 365 * 2:
        return f"{days}d"
    years, rest = divmod(days, 365)
    if days < 365 * 8 and rest:
        return f"{years}y{rest}d"
    return f"{years}y"


def keystrokes(cmd, seed):
    """keyTimes for typing cmd: uneven gaps, a pause before each flag."""
    rng = random.Random(seed)
    gaps = [rng.uniform(0.6, 1.4) * (3 if cmd[i:i + 2] == " -" else 1) for i in range(len(cmd))]
    total, acc, times = sum(gaps), 0.0, [0.0]
    for g in gaps:
        acc += g
        times.append(acc / total)
    times[-1] = 1.0
    return ";".join(f"{t:.4f}" for t in times)


def spans(parts):
    return "".join(f'<tspan class="{c}">{escape(t)}</tspan>' for c, t in parts)


def row(x, y, delay, body):
    return (f'<g class="out" style="animation-delay:{delay:.2f}s" transform="translate(0 {y})">'
            f'<text x="{x:.1f}" xml:space="preserve">{body}</text></g>')


def typed_command(pane, cmd, begin, dur, seed):
    """Prompt, the command revealed keystroke by keystroke, and the cursor riding along."""
    x0 = PANES[pane]
    cx = x0 + 2 * CW
    kt = keystrokes(cmd, seed)
    widths = ";".join(f"{i * CW:.1f}" for i in range(len(cmd) + 1))
    xs = ";".join(f"{cx + i * CW:.1f}" for i in range(len(cmd) + 1))
    timing = f'begin="{begin}s" dur="{dur}s" calcMode="discrete" keyTimes="{kt}" fill="freeze"'
    return f'''  <clipPath id="typed-{pane}">
    <rect x="{cx:.1f}" y="-18" width="0" height="26"><animate attributeName="width" values="{widths}" {timing}/></rect>
  </clipPath>
  <g transform="translate(0 {Y0})">
    <text class="prompt" x="{x0}">$</text>
    <text class="cmd" x="{cx:.1f}" textLength="{len(cmd) * CW:.1f}" lengthAdjust="spacing" clip-path="url(#typed-{pane})">{cmd}</text>
    <rect class="typing-cursor cursor-{pane}" x="{cx:.1f}" y="-13" width="{CW}" height="17">
      <animate attributeName="x" values="{xs}" {timing}/>
      <set attributeName="visibility" to="hidden" begin="{begin + dur + 0.3:.2f}s" fill="freeze"/>
    </rect>
  </g>'''


def render(today):
    # Timeline: left pane types and prints, focus moves right, right pane types and prints.
    l_type, l_dur = 0.6, 1.4
    l_out = l_type + l_dur + 0.35
    l_prompt = l_out + len(ENGINEER) * 0.04 + 0.1
    focus = l_prompt + 0.45
    r_type, r_dur = focus + 0.3, 0.9
    r_out = r_type + r_dur + 0.35
    r_prompt = r_out + (len(PROJECTS) + 1) * 0.05 + 0.1

    left_last = Y0 + (len(ENGINEER) + 1) * LH
    right_last = Y0 + (len(PROJECTS) + 2) * LH
    h = left_last + 30

    body = [typed_command(0, LEFT_CMD, l_type, l_dur, seed=7)]
    for i, (indent, parts) in enumerate(ENGINEER):
        body.append(row(PANES[0] + indent * CW, Y0 + (i + 1) * LH, l_out + i * 0.04, spans(parts)))
    body.append(f'''  <g class="appear" style="animation-delay:{l_prompt:.2f}s" transform="translate(0 {left_last})">
    <text class="prompt" x="{PANES[0]}">$</text>
    <rect class="unfocus" style="animation-delay:{focus:.2f}s" x="{PANES[0] + 2 * CW:.1f}" y="-13" width="{CW}" height="17"/>
  </g>''')

    body.append(typed_command(1, RIGHT_CMD, r_type, r_dur, seed=3))
    table = [("NAME", "STACK", "STATUS", "AGE")]
    table += [(n, s, st, k8s_age(c, today)) for n, s, st, c in PROJECTS]
    cols = [max(len(r[i]) for r in table) + 2 for i in range(3)]
    for i, (name, stack, status, age) in enumerate(table):
        if i == 0:
            line = f'<tspan class="h">{"".join(c.ljust(w) for c, w in zip((name, stack, status), cols))}{age}</tspan>'
        else:
            state = "s" if status == "Running" else "c"
            line = (f'<tspan class="v">{escape(name.ljust(cols[0]))}</tspan>'
                    f'<tspan class="p">{stack.ljust(cols[1])}</tspan>'
                    f'<tspan class="{state}">{status.ljust(cols[2])}</tspan>'
                    f'<tspan class="v">{age}</tspan>')
        body.append(row(PANES[1], Y0 + (i + 1) * LH, r_out + i * 0.05, line))
    body.append(f'''  <g class="appear" style="animation-delay:{r_prompt:.2f}s" transform="translate(0 {right_last})">
    <text class="prompt" x="{PANES[1]}">$</text>
    <rect class="blink" style="animation-delay:{r_prompt:.2f}s" x="{PANES[1] + 2 * CW:.1f}" y="-13" width="{CW}" height="17"/>
  </g>''')

    content = "\n".join(body)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-labelledby="title desc">
  <title id="title">$ kubectl get engineer ismd</title>
  <desc id="desc">Vladimir Kostelei: software/platform engineer somewhere on the Internet, eight years at Yandex as a tech lead, CKA-certified. Projects: {", ".join(p[0] for p in PROJECTS)}.</desc>
  <defs>
    <radialGradient id="glow-lilac" cx="0.94" cy="0.08" r="0.62">
      <stop offset="0" stop-color="#9680ce" stop-opacity="0.22"/>
      <stop offset="1" stop-color="#9680ce" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow-lime" cx="0.02" cy="0.98" r="0.5">
      <stop offset="0" stop-color="#bad76e" stop-opacity="0.09"/>
      <stop offset="1" stop-color="#bad76e" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="window"><rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="14"/></clipPath>
  </defs>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, "Cascadia Mono", Consolas, "Liberation Mono", "DejaVu Sans Mono", monospace; font-size: 14px; fill: {PAPER}; }}
    .title {{ font-size: 12px; fill: {MUTED}; }}
    .prompt {{ fill: {LIME}; font-weight: 700; }}
    .k {{ fill: {LILAC}; }}
    .v {{ fill: {PAPER}; }}
    .p {{ fill: {QUIET}; fill-opacity: 0.7; }}
    .c {{ fill: {MUTED}; font-style: italic; }}
    .s {{ fill: {LIME}; font-weight: 700; }}
    .h {{ fill: {MUTED}; }}
    rect.typing-cursor, rect.unfocus, rect.blink {{ fill: {LIME}; fill-opacity: 0.9; stroke: {LIME}; stroke-width: 1; }}
    /* Unfocused panes show a hollow cursor, like a real terminal. */
    rect.cursor-1 {{ fill-opacity: 0; animation: focus 0s {focus:.2f}s forwards; }}
    rect.unfocus {{ animation: unfocus 0s forwards; }}
    .out, .appear {{ animation: appear 0.18s ease-out both; }}
    .blink {{ animation: blink 1.1s step-end infinite; }}
    @keyframes appear {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes focus {{ to {{ fill-opacity: 0.9; }} }}
    @keyframes unfocus {{ to {{ fill-opacity: 0; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .out, .appear, .blink {{ animation: none; }}
      rect.unfocus {{ animation: none; fill-opacity: 0; }}
      .cmd {{ clip-path: none; }}
      .typing-cursor {{ display: none; }}
    }}
  </style>

  <g clip-path="url(#window)">
    <rect width="{W}" height="{h}" fill="{INK}"/>
    <rect width="{W}" height="{h}" fill="url(#glow-lilac)"/>
    <rect width="{W}" height="{h}" fill="url(#glow-lime)"/>
    <path d="M{W - 250} -10 L{W - 250 + h * 0.47:.0f} {h + 10}" stroke="{LILAC}" stroke-opacity="0.14"/>
    <path d="M{W - 175} -10 L{W - 175 + h * 0.47:.0f} {h + 10}" stroke="{LIME}" stroke-opacity="0.08"/>
    <path d="M0 46.5 H{W} M{SPLIT + 0.5} 47 V{h}" stroke="{LINE}" stroke-opacity="0.8"/>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="14" fill="none" stroke="{LINE}"/>

  <circle cx="26" cy="24" r="6" fill="{LILAC}" fill-opacity="0.85"/>
  <circle cx="46" cy="24" r="6" fill="{LIME}" fill-opacity="0.85"/>
  <circle cx="66" cy="24" r="6" fill="{LINE}"/>
  <text class="title" x="{W / 2}" y="28" text-anchor="middle">ismd@internet: ~ — tmux</text>

{content}
</svg>
'''


if __name__ == "__main__":
    today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    OUT.write_text(render(today))
