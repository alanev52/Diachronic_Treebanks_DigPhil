"""Figure: Grex scope/conclusion ratios per period, Late Modern Swedish (1700-1950).
Counts from tab:occurences (contemporary data excluded). 95% Wilson confidence intervals.
Panel (b) shows som and vilken on a broken y-axis so that both curves stay readable.

Run:  python3 make_figure.py
Out:  Ratio_occurences_scope.pdf (for the paper) and .png (for slides)
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import PercentFormatter, MaxNLocator

# ---- data: (scope, conclusion) per period ---------------------------------
periods = ["1700–49", "1750–99", "1800–49", "1850–99", "1900–50"]
rel_scope = [995, 1355, 1174, 1418, 1046]
counts = {
    "aux":    ([402, 525, 276, 577, 464], [181, 57, 30, 116, 94]),
    "som":    (rel_scope, [980, 1288, 1119, 1285, 963]),
    "vilken": (rel_scope, [14, 66, 51, 132, 83]),
    "neg":    ([210, 261, 209, 259, 256], [6, 11, 5, 3, 5]),
    "obj":    ([265, 211, 240, 305, 305], [6, 12, 3, 0, 1]),
}

periods = ["1700–49", "1750–99", "1800–49", "1850–99", "1900–50"]
rel_scope = [994, 1355, 1172, 1418, 1046]
periods = ["1700–49", "1750–99", "1800–49", "1850–99", "1900–50"]
rel_scope = [994, 1355, 1172, 1418, 1046]
counts = {
    "aux":    ([401, 525, 276, 577, 464], [181, 57, 30, 116, 94]),
    "som":    (rel_scope, [980, 1288, 1119, 1285, 963]),
    "vilken": (rel_scope, [14, 66, 51, 132, 83]),
    "neg":    ([201, 248, 205, 254, 252], [5, 11, 5, 6, 6]),
    "obj":    ([265, 211, 240, 305, 305], [6, 12, 3, 0, 1]),
}

BLUE, ORANGE = "#4C72B0", "#DD8452"   # colour-blind-safe pair


def wilson(k, n, z=1.96):
    """Proportion and 95% Wilson score interval."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return p, c - h, c + h


def draw(ax, k, n, color, label=None):
    p, lo, hi = wilson(k, n)
    ax.fill_between(x, lo, hi, color=color, alpha=0.18, lw=0)
    ax.plot(x, p, "o-", color=color, ms=3, lw=1.2, label=label)


def style(ax, step=None):
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    if step:
        ax.yaxis.set_major_locator(plt.MultipleLocator(step))
    else:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xticks(x)
    ax.set_xlim(-0.3, len(x) - 0.7)


plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 8.5,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "mathtext.fontset": "stix",
})

x = np.arange(len(periods))
fig = plt.figure(figsize=(3.1, 3.0))
gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.42)

# ---- (a) ha-omission: plot omission = scope - aux present ------------------
ax_a = fig.add_subplot(gs[0, 0])
n, k = counts["aux"]
draw(ax_a, np.array(n) - np.array(k), n, BLUE)
ax_a.set_ylim(0, 1)
style(ax_a, step=0.2)
ax_a.set_title("(a) Aux-omission", loc="left", pad=3)
ax_a.set_xticklabels([])

# ---- (b) som vs vilken on a broken y-axis ----------------------------------
sub = gs[0, 1].subgridspec(2, 1, hspace=0.12)
ax_top = fig.add_subplot(sub[0])   # som
ax_bot = fig.add_subplot(sub[1])   # vilken
draw(ax_top, counts["som"][1], rel_scope, ORANGE, "$som$")
draw(ax_bot, counts["vilken"][1], rel_scope, BLUE, "$vilken$")
ax_top.set_ylim(0.87, 1.0)
ax_bot.set_ylim(0.0, 0.13)
style(ax_top, step=0.05)
style(ax_bot, step=0.05)
ax_top.set_xticklabels([])
ax_bot.set_xticklabels([])
ax_top.spines["bottom"].set_visible(False)
ax_top.tick_params(axis="x", length=0)
ax_top.set_title("(b) rel. pronouns", loc="left", pad=3)
# inline labels instead of a legend
ax_top.text(x[-1] + 0.05, 0.875, "$som$", color=ORANGE, fontsize=7.5, va="bottom", ha="right")
ax_bot.text(x[0] - 0.1, 0.125, "$vilken$", color=BLUE, fontsize=7.5, va="top", ha="left")
# diagonal break marks
kw = dict(marker=[(-1, -0.5), (1, 0.5)], markersize=5, linestyle="none",
          color="k", mec="k", mew=0.8, clip_on=False)
ax_top.plot([0], [0], transform=ax_top.transAxes, **kw)
ax_bot.plot([0], [1], transform=ax_bot.transAxes, **kw)

# ---- (c) negation, (d) object between aux and verb -------------------------
for cell, key, title in [(gs[1, 0], "neg", "(c) V-Neg in Sub.Cl."),
                         (gs[1, 1], "obj", "(d) Aux-Obj-V")]:
    ax = fig.add_subplot(cell)
    n, k = counts[key]
    draw(ax, k, n, BLUE)
    ax.set_ylim(bottom=0)
    style(ax)
    ax.set_title(title, loc="left", pad=3)
    ax.set_xticklabels(periods, rotation=45, ha="right")

fig.subplots_adjust(left=0.12, right=0.98, top=0.94, bottom=0.14)
fig.savefig("Ratio_occurences_scope.pdf")
fig.savefig("Ratio_occurences_scope.png", dpi=300)
print("Saved Ratio_occurences_scope.pdf and .png")
