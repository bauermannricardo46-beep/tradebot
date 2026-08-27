from __future__ import annotations

"""Automatic DEMO bootstrap/execution guard.

This module is intentionally small: the API lifespan owns the asyncio loop,
while DemoEngine owns persistence.  The bootstrap only makes the default DEMO
state self-starting and removes UI/manual-click dependency.
"""


def force_demo_auto_start(demo, execution) -> None:
    # A fresh installation starts in DEMO/AUTO.  An explicit user disable is
    # still respected because this function only runs at process startup.
    if execution.get().get("mode") == "DEMO":
        try:
            demo.set_enabled(True)
        except Exception:
            pass
        demo.enabled = True


def auto_candidates(candidates):
    """Return scanner candidates in deterministic strongest-first order.

    Confidence labels are display metadata here; the scanner's structural
    validity has already been established upstream.
    """
    return sorted(
        [c for c in (candidates or []) if c is not None],
        key=lambda c: (
            float(getattr(c, "probability", 0.0)),
            float(getattr(c, "expected_value_r", 0.0)),
            float(getattr(c, "confidence", 0.0)),
        ),
        reverse=True,
    )
