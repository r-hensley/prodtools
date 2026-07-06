#!/usr/bin/env python3
"""
Direct-submit driver for Mu2e grid jobs.

Two backends:

- ``--backend mu2ejobsub`` (default, Phase 1): drives `mu2ejobsub` for each
  POMS-map entry. Worker uses the upstream Perl `mu2ejobsub.sh` shim, which
  does NOT call pushOutput.

- ``--backend direct`` (Phase 2): builds the `jobsub_submit` argv directly
  and ships our prodtools as a dropbox tarball. Worker bootstraps
  `bin/runjob.sh` → `utils/runmu2e.py` direct mode → per-job pushOutput.

Plans:
- wiki/pages/2026-04-29-remove-poms-from-submit-loop.md (Phase 1, POMS removal)
- wiki/pages/2026-04-30-phase2-direct-jobsub-implementation.md (Phase 2, direct)
"""

import argparse
import getpass
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.prod_utils import _fetch_file_local
from utils.job_common import Mu2eName, log_storage_location
from utils.poms_entry import tarball_of, outputs_of, njobs_of, inloc_of
from utils import jobsub_argv as _jobsub_argv

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUNJOB_SH = REPO_ROOT / 'bin' / 'runjob.sh'
DEFAULT_PRODTOOLS_TAR = Path('/tmp') / f'prodtools-{getpass.getuser()}.tar'


INLOC_TO_PROTOCOL = {
    'tape': 'ifdh',
    'disk': 'ifdh',
    'scratch': 'ifdh',
}


def build_mu2ejobsub_argv(entry, tarball_path, opts):
    """Map a POMS-map entry + options to mu2ejobsub CLI argv.

    This builds the flags we pass TO mu2ejobsub. mu2ejobsub itself
    then builds the jobsub_submit argv internally (ops JSON, env vars,
    UPS version lookups, outstage mkdir, etc.).

    Args:
        entry: dict from POMS-map JSON (tarball, njobs, inloc, outputs)
        tarball_path: absolute path to the locally-fetched cnf tarball
        opts: argparse namespace with dry_run, verbose, wfproject, role, etc.

    Returns:
        list[str]: mu2ejobsub argv (without the 'mu2ejobsub' command itself)
    """
    argv = ['--jobdef', str(tarball_path)]

    # Job set specification
    if 'njobs' in entry:
        argv.append('--all')

    # Input location and protocol
    inloc = inloc_of(entry)
    if inloc != 'none':
        argv.extend(['--default-location', inloc])
        protocol = INLOC_TO_PROTOCOL.get(inloc)
        if protocol is None and inloc.startswith('dir:'):
            protocol = 'ifdh'
        if protocol:
            argv.extend(['--default-protocol', protocol])

    # Workflow project
    tarball_name = tarball_of(entry)
    wfproject = opts.wfproject or _jobsub_argv.campaign_from_tarball(tarball_name)
    argv.extend(['--wfproject', wfproject])

    # Cluster name from tarball description
    clustername = _jobsub_argv.description_from_tarball(tarball_name)
    argv.extend(['--clustername', clustername])

    # Role
    if opts.role:
        argv.extend(['--role', opts.role])

    # Resource overrides
    if opts.disk:
        argv.extend(['--disk', opts.disk])
    if opts.memory:
        argv.extend(['--memory', opts.memory])
    if opts.expected_lifetime:
        argv.extend(['--expected-lifetime', opts.expected_lifetime])

    # Passthrough flags
    if opts.dry_run:
        argv.append('--dry-run')
    if opts.verbose:
        argv.append('--verbose')

    return argv


def _parse_cluster_id(stdout):
    """Parse condor cluster ID from mu2ejobsub / jobsub_submit output.

    jobsub_submit prints lines like:
        submitted to cluster 12345678
    or:
        Use job id 12345678.0@jobsub01.fnal.gov to retrieve output
    """
    for line in stdout.splitlines():
        m = re.search(r'submitted.*?cluster\s+(\d+)', line, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r'job\s+id\s+(\d+)\.', line, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _bundle_prodtools(out_path=DEFAULT_PRODTOOLS_TAR):
    """Tar `utils/` + `bin/` from this repo into a worker-shippable bundle.

    Used by the direct backend: the worker bootstraps `runjob.sh`, which
    extracts this tarball under `$_CONDOR_SCRATCH_DIR/prodtools/` and execs
    `utils/runmu2e.py` from there. Avoids depending on a cvmfs-published
    prodtools version that might not yet contain our changes.

    Skips tarring if `out_path` is already newer than every Python source
    file under utils/ — keeps repeated submissions cheap.
    """
    out = Path(out_path)
    sources = list((REPO_ROOT / 'utils').rglob('*.py')) + \
        list((REPO_ROOT / 'bin').glob('*'))
    if out.is_file():
        out_mtime = out.stat().st_mtime
        if all(s.stat().st_mtime <= out_mtime for s in sources if s.is_file()):
            return out

    print(f"Bundling prodtools → {out}")
    with tarfile.open(out, 'w') as tar:
        for sub in ('utils', 'bin'):
            src_dir = REPO_ROOT / sub
            for f in sorted(src_dir.rglob('*')):
                if not f.is_file():
                    continue
                if '__pycache__' in f.parts or f.suffix == '.pyc':
                    continue
                arcname = Path('prodtools') / f.relative_to(REPO_ROOT)
                tar.add(f, arcname=str(arcname))
    return out


def _read_input_datasets(tarball_path):
    """Pull the input dataset list from a cnf tarball (used to populate
    inspec). Imported lazily because Mu2eJobPars pulls in samweb_client
    via utils/__init__.py, which is fine at runtime but slow to import."""
    from utils.jobquery import Mu2eJobPars
    return Mu2eJobPars(str(tarball_path)).input_datasets()


def _read_njobs(tarball_path):
    """Authoritative job count — read from the cnf, not the POMS-map.
    The POMS-map field can be stale or absent for direct-input mode."""
    from utils.jobquery import Mu2eJobPars
    return Mu2eJobPars(str(tarball_path)).njobs()


def _read_output_filenames(tarball_path):
    """Per-job output basenames for index 0 (e.g.
    `sim.oksuzian.EleBeamCat.test01.001430_00000000.art`). Used by the
    direct backend to derive the correct token scopes per (area, tier,
    owner). Skips templates that resolved to a path (`/dev/null`)."""
    from utils.jobquery import Mu2eJobPars
    out = Mu2eJobPars(str(tarball_path)).job_outputs(0) or {}
    return [v for v in out.values() if v and "/" not in v]


def _compute_jobset(opts, njobs_total):
    """Resolve --first/--num into the list of job indices to submit.

    Default: every index 0..njobs_total-1 (== mu2ejobsub --all).
    --first N alone: 1 job at index N.
    --first N --num M: indices [N, N+M).
    """
    if opts.first is None and opts.num is None:
        return list(range(njobs_total))
    first = opts.first or 0
    num = opts.num if opts.num is not None else 1
    end = min(first + num, njobs_total)
    if first < 0 or first >= njobs_total or end <= first:
        raise ValueError(
            f"--first {first} --num {num} out of range for njobs_total={njobs_total}"
        )
    return list(range(first, end))


def submit_entry_direct(entry, idx, opts):
    """Direct-backend submission: build jobsub_submit argv from scratch
    via utils.jobsub_argv, ship our prodtools as a dropbox tarball, run
    `runjob.sh` on the worker. No `mu2ejobsub` involved.

    Returns the same dict shape as `submit_entry`.
    """
    tarball_name = tarball_of(entry)
    desc = _jobsub_argv.description_from_tarball(tarball_name)

    # Tarball must be locally accessible to ship via -f dropbox://.
    tarball_path = Path(tarball_name).resolve()
    if not tarball_path.is_file():
        if opts.dry_run:
            tarball_path = Path('/tmp') / tarball_name
        else:
            print(f"Fetching tarball: {tarball_name}")
            _fetch_file_local(tarball_name)
            tarball_path = Path(tarball_name).resolve()

    # njobs from the cnf is authoritative; POMS-map's field is informational.
    # output_filenames feeds the per-(area, tier, owner) token scope derivation
    # so pushOutput can MAKE_PARENT in `/pnfs/mu2e/<area>/datasets/...`.
    if opts.dry_run and not tarball_path.is_file():
        njobs_total = njobs_of(entry, default=1)
        input_datasets = []
        output_filenames = []
    else:
        njobs_total = _read_njobs(tarball_path)
        input_datasets = _read_input_datasets(tarball_path)
        output_filenames = _read_output_filenames(tarball_path)

    jobset = _compute_jobset(opts, njobs_total)

    print(f"\n{'='*60}")
    print(f"Entry {idx}: {desc} (cnf njobs={njobs_total}, submitting {len(jobset)})")
    print(f"  tarball: {tarball_name}")
    print(f"  inloc:   {inloc_of(entry)}")
    print(f"  jobset:  {jobset if len(jobset) <= 10 else f'[{jobset[0]}..{jobset[-1]}] ({len(jobset)} indices)'}")
    print(f"{'='*60}")

    # Synthesize ops JSON (jobs[] + inspec + jobdesc) and write to /tmp.
    # /tmp is the same FS jobsub_lite uses for its dropbox staging, so
    # this is fine for both local-test and mu2epro runs.
    ops = _jobsub_argv.build_ops_json(
        entry=entry,
        jobset=jobset,
        input_datasets=input_datasets,
    )
    ops_path = Path('/tmp') / f'ops-{getpass.getuser()}-{desc}-{os.getpid()}.json'
    ops_path.write_text(json.dumps(ops, indent=2) + '\n')
    print(f"Wrote ops JSON: {ops_path}")

    # Bundle prodtools so the worker has our patched runmu2e.py.
    prodtools_tar = _bundle_prodtools(opts.prodtools_tar or DEFAULT_PRODTOOLS_TAR)

    # Build the jobsub_submit argv. submitter is the effective UNIX user;
    # role auto-defaults to Production for mu2epro per jobsub_argv.role_for_user.
    submitter = getpass.getuser()
    # Token scopes for direct-mode pushOutput (CB1):
    #   - per data output: /mu2e/<area>/datasets/<owner-class>-<tier>/<tier>/<owner>
    #   - per log: same scheme with tier=log; logs share the first output's
    #     location (matches runmu2e._direct_dispatch's log_location choice).
    extra_scopes = list(_jobsub_argv.output_storage_dirs(
        output_filenames, outputs_of(entry)))
    if output_filenames:
        log_location = log_storage_location(entry)
        try:
            first_out = Mu2eName.parse(output_filenames[0])
        except ValueError:
            first_out = None
        if first_out is not None and first_out.is_file:
            log_fname = str(first_out.as_tier('log').with_extension('log'))
            log_scope = _jobsub_argv.storage_scope_for_file(log_fname, log_location)
            if log_scope:
                extra_scopes.append(log_scope)

    argv = _jobsub_argv.build_jobsub_argv(
        entry=entry,
        jobset=jobset,
        jobdef_path=str(tarball_path),
        ops_json_path=str(ops_path),
        prodtools_tar_path=str(prodtools_tar),
        worker_script_path=str(DEFAULT_RUNJOB_SH),
        submitter=submitter,
        extra_storage_modify=extra_scopes,
        role=opts.role,
        wftop=opts.wftop,
        wfproject=opts.wfproject,
        disk=opts.disk,
        memory=opts.memory,
        expected_lifetime=opts.expected_lifetime,
    )

    cmd = ['jobsub_submit'] + argv
    print(f"\nCommand: {' '.join(cmd)}")

    if opts.dry_run:
        print("[DRY RUN] Not submitting.")
        ops_path.unlink(missing_ok=True)
        return {
            'tarball': tarball_name,
            'cluster_id': None,
            'njobs': len(jobset),
            'status': 'dry_run',
        }

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"ERROR: jobsub_submit failed with exit code {result.returncode}")
        return {
            'tarball': tarball_name,
            'cluster_id': None,
            'njobs': len(jobset),
            'status': 'failed',
        }

    cluster_id = _parse_cluster_id(result.stdout)
    if cluster_id:
        print(f"Submitted cluster: {cluster_id}")
    else:
        print("WARNING: could not parse cluster ID from jobsub_submit output")

    return {
        'tarball': tarball_name,
        'cluster_id': cluster_id,
        'njobs': len(jobset),
        'status': 'submitted',
    }


def submit_entry(entry, idx, opts):
    """Dispatch on `opts.backend` to the appropriate per-entry submit path.

    Args:
        entry: dict from POMS-map JSON
        idx: entry index in the map (for display)
        opts: argparse namespace

    Returns:
        dict with keys: tarball, cluster_id, njobs, status
    """
    if opts.backend == 'direct':
        return submit_entry_direct(entry, idx, opts)
    return _submit_entry_mu2ejobsub(entry, idx, opts)


def _submit_entry_mu2ejobsub(entry, idx, opts):
    """Phase 1 backend: invoke `mu2ejobsub` with mapped flags."""
    tarball_name = tarball_of(entry)
    njobs = njobs_of(entry, default='?')  # diagnostic print only; '?' if absent
    desc = _jobsub_argv.description_from_tarball(tarball_name)

    print(f"\n{'='*60}")
    print(f"Entry {idx}: {desc} ({njobs} jobs)")
    print(f"  tarball: {tarball_name}")
    print(f"  inloc:   {inloc_of(entry)}")
    print(f"{'='*60}")

    # In dry-run mode, mu2ejobsub resolves the tarball itself via
    # find_file(), so we only need the basename. For real submissions,
    # fetch locally so mu2ejobsub gets an absolute path.
    if opts.dry_run:
        tarball_path = tarball_name
    else:
        tarball_path = Path(tarball_name).resolve()
        if not tarball_path.is_file():
            print(f"Fetching tarball: {tarball_name}")
            _fetch_file_local(tarball_name)
            tarball_path = Path(tarball_name).resolve()

    argv = build_mu2ejobsub_argv(entry, tarball_path, opts)

    cmd = ['mu2ejobsub'] + argv
    print(f"\nCommand: {' '.join(cmd)}")

    if opts.dry_run:
        print("[DRY RUN] Not submitting.")
        return {
            'tarball': tarball_name,
            'cluster_id': None,
            'njobs': njobs,
            'status': 'dry_run',
        }

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    # Print mu2ejobsub output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"ERROR: mu2ejobsub failed with exit code {result.returncode}")
        return {
            'tarball': tarball_name,
            'cluster_id': None,
            'njobs': njobs,
            'status': 'failed',
        }

    cluster_id = _parse_cluster_id(result.stdout)
    if cluster_id:
        print(f"Submitted cluster: {cluster_id}")
    else:
        print("WARNING: could not parse cluster ID from mu2ejobsub output")

    return {
        'tarball': tarball_name,
        'cluster_id': cluster_id,
        'njobs': njobs,
        'status': 'submitted',
    }


def _check_token():
    """Pre-flight token check. Returns True if valid, False otherwise."""
    try:
        result = subprocess.run(
            ['httokendecode'],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print("WARNING: httokendecode failed — token may be missing or expired")
            return False
        print("Token check: OK")
        return True
    except FileNotFoundError:
        print("WARNING: httokendecode not found — skipping token check")
        return True


def submit_map(map_path, opts):
    """Submit all (or selected) entries from a POMS-map JSON.

    Args:
        map_path: path to the POMS-map JSON
        opts: argparse namespace

    Returns:
        list of result dicts from submit_entry
    """
    with open(map_path) as f:
        entries = json.load(f)

    if not isinstance(entries, list):
        print(f"Error: {map_path} should contain a JSON array")
        sys.exit(1)

    if not entries:
        print(f"Error: {map_path} is empty")
        sys.exit(1)

    # Filter by --entry if specified
    if opts.entry is not None:
        if opts.entry < 0 or opts.entry >= len(entries):
            print(f"Error: --entry {opts.entry} out of range (map has {len(entries)} entries)")
            sys.exit(1)
        entries_to_submit = [(opts.entry, entries[opts.entry])]
    else:
        entries_to_submit = list(enumerate(entries))

    # Skip entries without njobs (generic/direct-input tarballs) unless
    # there's only one entry (direct-input mode)
    if len(entries_to_submit) > 1:
        filtered = []
        for idx, entry in entries_to_submit:
            if njobs_of(entry) is None:
                print(f"[INFO] Skipping entry {idx} ({entry.get('tarball', '?')}): no njobs (generic tarball)")
                continue
            filtered.append((idx, entry))
        entries_to_submit = filtered

    if not entries_to_submit:
        print("No submittable entries found.")
        return []

    print(f"Map: {map_path}")
    print(f"Entries to submit: {len(entries_to_submit)}")
    print(f"Total jobs: {sum(njobs_of(e, default=0) for _, e in entries_to_submit)}")

    # Pre-flight token check
    if not opts.dry_run:
        _check_token()

    submitter = getpass.getuser()
    print(f"Submitter: {submitter}")

    results = []
    for idx, entry in entries_to_submit:
        result = submit_entry(entry, idx, opts)
        results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    submitted = [r for r in results if r['status'] == 'submitted']
    failed = [r for r in results if r['status'] == 'failed']
    dry_run = [r for r in results if r['status'] == 'dry_run']

    if dry_run:
        print(f"  Dry run:   {len(dry_run)} entries")
    if submitted:
        print(f"  Submitted: {len(submitted)} entries")
        for r in submitted:
            print(f"    cluster {r['cluster_id']}: {_jobsub_argv.description_from_tarball(r['tarball'])} ({r['njobs']} jobs)")
    if failed:
        print(f"  Failed:    {len(failed)} entries")
        for r in failed:
            print(f"    {_jobsub_argv.description_from_tarball(r['tarball'])}: FAILED")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Submit Mu2e grid jobs from a POMS-map JSON via mu2ejobsub'
    )
    parser.add_argument('--map', required=True,
                        help='Path to POMS-map JSON (e.g., MDC2025-001.json)')
    parser.add_argument('--entry', type=int, default=None,
                        help='Submit only this entry index (0-based)')
    parser.add_argument('--backend', choices=('mu2ejobsub', 'direct'),
                        default='mu2ejobsub',
                        help='Submission backend. mu2ejobsub (default) uses '
                             'the Perl mu2ejobsub upstream; direct calls '
                             'jobsub_submit straight from prodtools and ships '
                             'our runjob.sh worker.')
    parser.add_argument('--first', type=int, default=None,
                        help='[direct] First job index to submit. With --num '
                             'submits a contiguous range; without --num '
                             'submits one job at this index.')
    parser.add_argument('--num', type=int, default=None,
                        help='[direct] Number of consecutive jobs from --first.')
    parser.add_argument('--wftop', default=None,
                        help='[direct] Outstage top dir (default: '
                             '/pnfs/mu2e/persistent/users for Production, '
                             '/pnfs/mu2e/scratch/users otherwise)')
    parser.add_argument('--wfproject', default=None,
                        help='Workflow project name (default: extracted from tarball dsconf)')
    parser.add_argument('--role', default=None,
                        help='Grid role (default: auto — Production for mu2epro)')
    parser.add_argument('--disk', default=None,
                        help='Disk request (default: 30GB)')
    parser.add_argument('--memory', default=None,
                        help='Memory request (default: 2000MB)')
    parser.add_argument('--expected-lifetime', default=None,
                        help='Expected lifetime (default: 24h)')
    parser.add_argument('--prodtools-tar', default=None,
                        help='[direct] Path for the prodtools bundle '
                             f'(default: {DEFAULT_PRODTOOLS_TAR}). Reused if '
                             'newer than every utils/*.py source file.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print the submission command without running it')
    parser.add_argument('--verbose', action='store_true',
                        help='Pass --verbose to mu2ejobsub (mu2ejobsub backend only)')

    args = parser.parse_args()

    if not Path(args.map).is_file():
        print(f"Error: map file not found: {args.map}")
        sys.exit(1)

    results = submit_map(args.map, args)

    failed = [r for r in results if r['status'] == 'failed']
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
