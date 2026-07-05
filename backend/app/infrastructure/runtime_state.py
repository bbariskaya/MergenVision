"""Global ML runtime readiness flag."""

from __future__ import annotations

_runtime_loaded = False


def mark_runtime_loaded() -> None:
    """Signal that the ML runtime (detector/recognizer/adapters) is loaded."""
    global _runtime_loaded
    _runtime_loaded = True


def is_runtime_loaded() -> bool:
    """Return whether the ML runtime has been loaded."""
    return _runtime_loaded
