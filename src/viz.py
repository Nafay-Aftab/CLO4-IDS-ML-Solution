"""Shared figure style: validated reference palette, hairline chrome, 300-DPI export."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from src.config import FIG_DIR, FIG_DPI  # noqa: E402

# Fixed identity mapping used by every figure: Normal = slot 1, Attack = slot 2.
NORMAL = "#2a78d6"
ATTACK = "#eb6834"
ACCENT = "#1baf7a"   # slot 3 — third series only (e.g. F1 curve)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
CRITICAL = "#d03b3b"

DIVERGING = LinearSegmentedColormap.from_list("blue_gray_red", ["#184f95", "#2a78d6", "#f0efec", "#e34948", "#a12d2d"])
SEQUENTIAL = LinearSegmentedColormap.from_list("blue_seq", ["#f0efec", "#9ec5f4", "#3987e5", "#1c5cab", "#0d366b"])


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": INK_2,
        "axes.titlecolor": INK, "axes.titlesize": 12, "axes.titleweight": "semibold",
        "axes.titlelocation": "left", "axes.titlepad": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
        "legend.frameon": False, "legend.labelcolor": INK_2,
        "lines.linewidth": 2, "lines.solid_capstyle": "round",
    })


def save(fig, name: str) -> str:
    path = FIG_DIR / name
    # Respect the figure's own facecolor (rcParams would repaint dark figures with the light surface).
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return str(path)


apply_style()
