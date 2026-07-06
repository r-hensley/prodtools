"""POMS-map entry accessors.

POMS-map files (`/exp/mu2e/app/users/mu2epro/production_manager/poms_map/MDC*.json`)
are lists of entries with stable shape:

    {
        "tarball":  "cnf.mu2e.<desc>.<dsconf>.<index>.tar",   # required
        "outputs":  [ {"dataset": "...", "location": "tape|disk|scratch"}, ... ],  # required
        "njobs":    <int>,                                    # optional
        "inloc":    "tape|disk|scratch|dir:<path>|none",      # optional, defaults 'none'
    }

These helpers enforce fail-loud access on the required fields and the
documented sentinel defaults on the optional ones. Use them instead of
bare `entry[...]` or `entry.get(...)` so a malformed POMS-map is caught
at the boundary, not as a downstream crash.
"""

from typing import Optional

from utils.job_common import Mu2eName


def tarball_of(entry: dict) -> str:
    """Return the cnf tarball name. Fail loud if missing or not a cnf tarball."""
    if "tarball" not in entry:
        raise ValueError("POMS entry missing required field: 'tarball'")
    name = entry["tarball"]
    try:
        n = Mu2eName.parse(name)
    except ValueError as exc:
        raise ValueError(f"POMS entry 'tarball' is not a valid Mu2e name: {name!r}: {exc}")
    if not n.is_tarball:
        raise ValueError(f"POMS entry 'tarball' is not a cnf tarball: {name!r}")
    return name


def outputs_of(entry: dict) -> list:
    """Return the outputs list. Fail loud if missing."""
    if "outputs" not in entry:
        raise ValueError("POMS entry missing required field: 'outputs'")
    return entry["outputs"]


def njobs_of(entry: dict, default: Optional[int] = None) -> Optional[int]:
    """Return njobs, or `default` if absent.

    njobs is informational at the POMS-map layer (the authoritative count
    comes from the cnf tarball at submission time). Pass an explicit
    default at the call site for diagnostic or dry-run paths.
    """
    return entry.get("njobs", default)


def inloc_of(entry: dict, default: str = "none") -> str:
    """Return inloc, defaulting to the documented 'none' sentinel."""
    return entry.get("inloc", default)
