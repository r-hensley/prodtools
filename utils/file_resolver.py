#!/usr/bin/env python3
"""
file_resolver.py: given a Mu2e filename and an inloc, where does it
live and how do I read it.

This module owns the dCache/CVMFS path grammar (stash, resilient,
dataset dirs, token scopes) and the per-inloc location logic that used
to be spread across jobfcl, stash_utils, datasetFileList, and
jobsub_argv. SAM access goes exclusively through samweb_wrapper.

Import cost: the module itself is pure (no samweb_client / gfal2 at
import time). SAM and gfal2 are imported lazily on first use, so
pure-function consumers (jobsub_argv, unit tests) and dir:-mode
resolution work without the Mu2e ops environment.
"""

import os
import re
from typing import Optional

from .job_common import Mu2eName, remove_storage_prefix

# xrootd door prefixes. The fcl read URL uses the `xroot://` scheme and
# the gfal2 stat URL uses `root://` — both are accepted by xrootd and
# both predate this module; preserved as-is because worker fcl output
# must stay byte-identical.
XROOT_READ_PREFIX = 'xroot://fndcadoor.fnal.gov//pnfs/fnal.gov/usr/'
XROOT_STAT_PREFIX = 'root://fndcadoor.fnal.gov//pnfs/fnal.gov/usr/'


# ---------------------------------------------------------------------------
# Roots (env-overridable)
# ---------------------------------------------------------------------------

def stash_read_root() -> str:
    """StashCache CVMFS read root (used by grid jobs in FCL)."""
    return os.environ.get(
        "MU2E_STASH_READ",
        "/cvmfs/mu2e.osgstorage.org/pnfs/fnal.gov/usr/mu2e/persistent/stash"
    )


def stash_write_root() -> str:
    """StashCache dCache write root (used when copying files in)."""
    return os.environ.get("MU2E_STASH_WRITE", "/pnfs/mu2e/persistent/stash")


def resilient_root() -> str:
    """Resilient dCache root (write and direct-read on interactive nodes)."""
    return os.environ.get("MU2E_RESILIENT", "/pnfs/mu2e/resilient")


# ---------------------------------------------------------------------------
# Path grammar
# ---------------------------------------------------------------------------

def dataset_subpath(filename: str) -> str:
    """Dataset-derived sub-path for a file, relative to a stash/resilient
    root: datasets/<tier>/<owner>/<description>/<dsconf>/<ext>/<filename>."""
    ds_path = str(Mu2eName.parse(filename).dataset).replace('.', '/')
    return f"datasets/{ds_path}/{filename}"


def stash_read_path(filename: str) -> str:
    """Full CVMFS read path for a file on stash."""
    return f"{stash_read_root()}/{dataset_subpath(filename)}"


def stash_write_path(filename: str) -> str:
    """Full dCache write path for a file on stash."""
    return f"{stash_write_root()}/{dataset_subpath(filename)}"


def resilient_path(filename: str) -> str:
    """Full /pnfs/ path for a file in resilient storage."""
    return f"{resilient_root()}/{dataset_subpath(filename)}"


def dataset_dir(dsname: str, location: str) -> str:
    """Absolute /pnfs directory for a Mu2e dataset at the given location.

    Physical layout: tape has no `datasets/` component, unlike
    disk/scratch (and unlike the token-scope paths — see storage_scope).
    Returns '' for unknown locations.
    """
    n = Mu2eName.parse(dsname)
    owner_prefix = "phy" if n.owner == "mu2e" else "usr"
    base_path = f"{owner_prefix}-{n.tier_class}"
    ds_path = dsname.replace('.', '/')
    if location == 'disk':
        return f"/pnfs/mu2e/persistent/datasets/{base_path}/{ds_path}"
    if location == 'tape':
        return f"/pnfs/mu2e/tape/{base_path}/{ds_path}"
    if location == 'scratch':
        return f"/pnfs/mu2e/scratch/datasets/{base_path}/{ds_path}"
    return ""


# Mu2e standard location → dCache area name (under `/pnfs/mu2e/<area>/`).
# Mirrors Mu2eFNBase::location_root values.
LOCATION_AREA = {
    "tape": "tape",
    "disk": "persistent",
    "scratch": "scratch",
    "resilient": "resilient",
}


def storage_scope(filename: str, location) -> Optional[str]:
    """Narrowest dCache token scope covering writes of `filename` to
    `location`: /mu2e/<area>/datasets/<owner-class>-<tier>/<tier>/<owner>.

    Token-scope paths include `datasets/` for every area — matching
    htvault's pre-allocated scopes — which intentionally differs from the
    physical tape layout (no `datasets/` component; see dataset_dir).

    Why narrowest: htvault rejects `--need-storage-modify
    /mu2e/scratch/datasets` as too broad with `PermissionError: Unable to
    add 'storage.modify:...' scope given initial scope '[...]'`. Available
    scopes are pre-allocated per (area, tier, owner) tuple.

    Returns None for `dir:<path>` locations, unknown locations, or
    unparseable filenames.
    """
    if not location or str(location).startswith("dir:"):
        return None
    area = LOCATION_AREA.get(location)
    if not area:
        return None
    try:
        n = Mu2eName.parse(filename)
    except ValueError:
        return None
    if n.is_dataset:
        return None
    owner_prefix = "phy" if n.owner == "mu2e" else "usr"
    return f"/mu2e/{area}/datasets/{owner_prefix}-{n.tier_class}/{n.tier}/{n.owner}"


def xroot_read_url(pnfs_path: str) -> str:
    """Rewrite a /pnfs/ path to the xrootd read URL used in worker fcl."""
    return pnfs_path.replace('/pnfs/', XROOT_READ_PREFIX, 1)


# ---------------------------------------------------------------------------
# Existence probes
# ---------------------------------------------------------------------------

def resilient_file_exists(pnfs_path: str) -> bool:
    """Check if a resilient /pnfs/ file exists via gfal2 xrootd.

    Uses gfal2 Python bindings for reliable xrootd access that works on
    both interactive nodes and grid worker nodes (no POSIX dCache
    required). Returns False if gfal2 is unavailable or the stat fails,
    causing the caller to fall through to SAM lookup.
    """
    xroot_url = pnfs_path.replace('/pnfs/', XROOT_STAT_PREFIX, 1)
    try:
        import gfal2
        ctx = gfal2.creat_context()
        ctx.stat(xroot_url)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class FileResolver:
    """Resolve Mu2e filenames to physical paths / read URLs for a fixed
    (inloc, proto) pair — the per-jobdef configuration jobfcl runs with.

    locate() and url() reproduce the historical Mu2eJobFCL behavior
    exactly (the worker's inner loop is production-critical):
    - dir:<path>  → literal join, no existence check
    - stash       → CVMFS path if present, else SAM fallback
    - resilient   → /pnfs path if gfal2-stat succeeds, else SAM fallback
    - disk/tape   → SAM locate, preferring the requested location_type
    """

    def __init__(self, inloc: str = 'tape', proto: str = 'file'):
        self.inloc = inloc
        self.proto = proto

    def locate(self, filename: str) -> str:
        """Physical path for a file (no protocol formatting)."""
        if self.inloc.startswith('dir:'):
            local_dir = self.inloc[4:].rstrip('/')
            return f"{local_dir}/{filename}"

        # Resolve stash path from filename — no SAM involved.
        # If file not found on stash, fall back to SAM-based lookup.
        if self.inloc == 'stash':
            stash_path = stash_read_path(filename)
            if os.path.exists(stash_path):
                return stash_path

        if self.inloc == 'resilient':
            res_path = resilient_path(filename)
            if resilient_file_exists(res_path):
                return res_path

        return self._locate_via_sam(filename)

    def _locate_via_sam(self, filename: str) -> str:
        from .samweb_wrapper import locate_file_strict
        try:
            locations = locate_file_strict(filename)
        except Exception as e:
            raise ValueError(f"Could not locate file: {filename}: {e}")

        if not locations:
            raise ValueError(f"Could not locate file: {filename}")

        # Prefer the requested location type (disk/tape); otherwise fall
        # back to the first available location.
        preferred = [loc for loc in locations
                     if loc.get('location_type') == self.inloc]
        selected = preferred[0] if preferred else locations[0]

        path = selected.get('full_path', '')
        if not path:
            raise ValueError(f"Could not determine path for file: {filename}")
        return path

    def url(self, filename: str) -> str:
        """Read path/URL for a file, formatted per the resolver's proto."""
        # Stash paths are always plain CVMFS paths — ignore proto. If the
        # file fell back to SAM, apply the root protocol below.
        if self.inloc == 'stash':
            path = self.locate(filename)
            if path.startswith(stash_read_root()):
                return path
            physical_path = path
        elif self.inloc == 'resilient':
            # Resilient disk has no CVMFS mirror — always use xrootd
            physical_path = self.locate(filename)
        elif self.proto == 'file':
            return self.locate(filename)
        elif self.proto != 'root':
            return filename
        else:
            physical_path = self.locate(filename)

        clean_path = remove_storage_prefix(physical_path)

        # Remove file location suffix like (2290@fm4794l8) if present
        clean_path = re.sub(r'\([^)]+\)$', '', clean_path)

        if not clean_path.endswith(filename):
            clean_path = clean_path + '/' + filename

        if clean_path.startswith('/pnfs/'):
            return xroot_read_url(clean_path)

        raise ValueError(
            f"Error: root protocol requested but a file pathname does not start with /pnfs: {clean_path}"
        )
