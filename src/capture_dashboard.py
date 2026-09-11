"""Capture the four SOC dashboard views to figures/dashboard_*.png with headless Microsoft Edge.

Requires the dashboard to be running (`python -m src.app`). Uses the dashboard's kiosk mode
(?view=<view>&demo=1) so each view is driven automatically before the screenshot is taken.
An isolated temporary browser profile is used; the user's Edge profile is never touched.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from src.config import FIG_DIR

EDGE_CANDIDATES = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                   Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]
BASE = "http://localhost:8000/"
# name -> (query string, window height, virtual-time budget ms)
VIEWS = {
    "telemetry": ("?view=telemetry", 1560, 6000),
    # SSE never idles, so kiosk mode pauses the feed after 45 events before the budget runs.
    "live_siem": ("?view=stream&demo=1&rate=12&events=45", 1100, 8000),
    "manual_inspector": ("?view=inspector&demo=1&preset=1", 1000, 6000),
    "batch_prediction": ("?view=batch&demo=1", 1180, 12000),
}


def main() -> int:
    edge = next((p for p in EDGE_CANDIDATES if p.exists()), None)
    if edge is None:
        sys.exit("Microsoft Edge not found.")
    profile = Path(tempfile.mkdtemp(prefix="soc-capture-"))
    try:
        for name, (query, height, budget) in VIEWS.items():
            out = FIG_DIR / f"dashboard_{name}.png"
            subprocess.run([str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            f"--user-data-dir={profile}", "--force-device-scale-factor=2",
                            f"--window-size=1440,{height}", f"--virtual-time-budget={budget}",
                            f"--screenshot={out}", BASE + query], check=True, timeout=120,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"saved {out} ({out.stat().st_size / 1024:.0f} KB)")
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
