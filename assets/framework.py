"""Generate the finvariant framework figure (academic style).

The flow: statements in the canonical schema, the invariants check() verifies,
the AuditReport, and how it is consumed.
Run:  python assets/framework.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})

INK = "#1f2d3d"
MUT = "#5b6b7b"
NEUT_F, NEUT_E = "#eef1f4", "#9aa7b3"
ANA_F, ANA_E = "#eef3f8", "#3b6ea5"
RES_F, RES_E = "#d4e4f4", "#2c5f8a"
OPT_F, OPT_E = "#e3f1ec", "#3a8f78"
CONT_F, CONT_E = "#f7f9fb", "#c9d2db"
BAN_F, BAN_E = "#f5f7f9", "#cdd6df"
ARROW = "#7c8a99"

fig, ax = plt.subplots(figsize=(12, 6.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, text, fill, edge, fs=8.2, bold=False, tcol=INK):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.35,rounding_size=1.4",
        linewidth=1.25, edgecolor=edge, facecolor=fill, zorder=2))
    ax.text(x, y, text, ha="center", va="center", color=tcol, fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=5)


def arrow(x0, y0, x1, y1, color=ARROW, lw=1.15):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=1,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                shrinkA=1, shrinkB=1))


ax.text(3, 97.5, "finvariant", fontsize=13.5, fontweight="bold", color=INK,
        ha="left")
ax.text(3, 93.3, "deterministic integrity checks for financial statements",
        fontsize=9.5, color=MUT, ha="left", fontstyle="italic")

for x, t in [(12, "Inputs"), (43, "check()  verifies"), (73, "Result"),
             (92, "Consumption")]:
    ax.text(x, 88, t, ha="center", fontsize=9.5, color=MUT, fontstyle="italic")

# inputs
for y, t in [(74, "Income statement"), (61, "Balance sheet"), (48, "Cash flow")]:
    box(12, y, 18, 8.5, t, NEUT_F, NEUT_E, fs=8.3)
ax.text(12, 39, "canonical schema  ·  1+ periods", ha="center",
        fontsize=7.4, color=MUT, fontstyle="italic")

# invariants container
ax.add_patch(FancyBboxPatch((25, 38), 36, 46,
             boxstyle="round,pad=0.4,rounding_size=1.6",
             linewidth=1.3, edgecolor=CONT_E, facecolor=CONT_F, zorder=0))
invs = [
    (76, "Footing    ·    subtotals = sum of line items"),
    (66, "Accounting equation    ·    assets = liabilities + equity"),
    (56, "Cash tie-outs    ·    net change · ending · beginning"),
    (46, "Articulation    ·    net income · retained earnings"),
]
for y, t in invs:
    box(43, y, 32, 7.2, t, ANA_F, ANA_E, fs=7.4)

# result
box(73, 61, 20, 40,
    "AuditReport\n\nok  ·  findings\n(expected vs actual)\ncounts\n\n"
    "meta\nversion · input hash\ntimestamp",
    RES_F, RES_E, fs=8.3, bold=True)

# consumption
cons = [(74, "r.ok\npass / fail gate"), (61, "summary()\nplain-text verdict"),
        (48, "to_dict()\nJSON, versioned")]
for y, t in cons:
    box(92, y, 15, 9, t, OPT_F, OPT_E, fs=7.8)

# arrows: inputs converge into check(), check() to result, result fans to consumption
for y in (74, 61, 48):
    arrow(21.2, y, 24.6, 61)
arrow(61.2, 61, 62.8, 61)
for y in (74, 61, 48):
    arrow(83.2, 61, 84.4, y)

# banner
box(50, 13.5, 74, 8.4,
    "computed from the accounting identities    ·    zero runtime dependencies\n"
    "validated against real published statements "
    "(Apple · Tesla · NVIDIA · Microsoft · Amazon · Meta)",
    BAN_F, BAN_E, fs=8.0, tcol=MUT)

fig.savefig("assets/framework.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("wrote assets/framework.png")
