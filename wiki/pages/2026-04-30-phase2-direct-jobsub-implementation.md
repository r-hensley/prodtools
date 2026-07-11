---
title: Phase 2 implementation plan — direct jobsub_submit driver
tags: [decision, plan, submission, jobsub_submit, mu2ejobsub, phase2, runjob]
sources: []
updated: 2026-04-30
---

# Phase 2 Implementation Plan: Direct `jobsub_submit` Driver

**Date:** 2026-04-30
**Type:** Implementation plan
**Status:** Proposed (revised post-review 2026-04-30)
**Parent:** [[2026-04-29-remove-poms-from-submit-loop]]

## Review history

Three review agents ran 2026-04-30. Findings folded into the
"Correctness blockers" and "Scope tightening" sections below.
The user's stated goal is a fully Perl-free pipeline; the
review surfaced concrete gaps that must be addressed in this
plan before implementation, but does not change the goal.

## Goal

Replace the Perl `mu2ejobsub` + `mu2egrid::impl/mu2ejobsub.sh` worker
shim with prodtools-native Python that drives `jobsub_submit` directly.
Driving rationale: enable per-job `pushOutput` SAM registration on the
worker (matching POMS+runmu2e behavior), without keeping POMS in the loop.

## Why now

Phase 1 (`utils/submit.py` + `bin/submit_map`) is functionally
validated end-to-end: a 2-job BeamSplitter cluster (91222054) was
submitted via prodtools→mu2ejobsub→jobsub_submit on 2026-04-30.
Outputs land in outstage but are NOT registered in SAM — `mu2ejobsub.sh`
does not call pushOutput.

Phase 2 closes that gap. With direct invocation we control the worker
script, and that script can use prodtools' existing
`prod_utils.push_data()` / `push_logs()` to register outputs per job.

## What's reusable (already in prodtools)

The Phase 2 review surfaced that most worker-side logic already
exists. Reuse as-is:

| Component | Source | Use |
|---|---|---|
| `Mu2eJobFCL.generate_fcl(index)` | `utils/jobfcl.py` | per-job fcl materialization |
| `Mu2eJobIO.job_inputs(index)` / `.job_outputs(index)` | `utils/jobiodetail.py` | per-job I/O discovery |
| `prod_utils.push_data(outputs, infiles, simjob_setup, track_parents)` | `utils/prod_utils.py:769` | SAM registration via pushOutput |
| `prod_utils.push_logs(fcl, simjob_setup)` | `utils/prod_utils.py:803` | log upload |
| `prod_utils.build_mu2e_cmd(fcl, simjob_setup, args)` | `utils/prod_utils.py:593` | `mu2e -c` command construction |
| `_job_index_from_fname()` | `utils/prod_utils.py:78` | sequencer-based index parsing |

Net new build is ~3 components.

## Implementation

### Step 1 — Extend `utils/runmu2e.py` with direct mode

**~80 LOC diff** (NOT a separate file). Adds a "direct" mode to the
existing worker entry; keeps the POMS-mode (`--jobdesc` + `fname` env)
intact.

Rationale: `runmu2e.py` and a hypothetical `runjob.py` would share
~80% of the code. Only 4 things actually differ:
- job index source (`fname` sequencer vs `$PROCESS` → `jobset[PROCESS]`)
- jobdef path resolution (CLI arg vs `$CONDOR_DIR_INPUT/$MU2EGRID_JOBDEF`)
- ifdh stage-in step (skipped in POMS mode; required in direct mode)
- failure handling (push_output failure ignored in POMS mode;
  hard-fail in direct mode) and manifest emission (direct mode only)

Mode dispatch:
- POMS mode: `runmu2e --jobdesc <json>` + `fname` env (existing)
- Direct mode: `MU2EGRID_JOBDEF` and `MU2EGRID_OPSJSON` env present,
  `$PROCESS` set, no `--jobdesc` → take direct path

New code paths in `runmu2e.py`:
1. `_resolve_direct_index()`: read `$CONDOR_DIR_INPUT/$MU2EGRID_OPSJSON`,
   return `jobset[int(os.environ['PROCESS'])]`.
2. `_direct_stage_inputs(jobdef, index, inspec)`: ifdh stage-in driven
   by `Mu2eJobIO(jobdef).job_inputs(index)` and the inspec map.
3. `_emit_manifest(log_path, output_files)`: port of `addManifest`
   from `mu2ejobsub.sh:44-56`. Pin `LC_ALL=C`, use `sha256sum < log`
   for selfcheck (CB4).
4. Wrap `push_data` / `push_logs` calls in `_direct_push_with_retry()`:
   3 retries with 30s exponential backoff; non-zero return → exit 1
   (CB2).
5. `_direct_main()`: orchestrates the above; called from `main()` when
   direct mode is detected.

POMS-mode behavior is unchanged; existing `_dispatch_and_execute` is
called only on the POMS path.

`bin/runmu2e` (existing wrapper) keeps working for POMS; jobsub-side
will pass `file://<repo>/bin/runmu2e` as the executable.

### Step 2 — Submit-side argv builder (`utils/jobsub_argv.py`)

**~200 LOC.** Pure-function `build_argv(jobdef, jobset, opts) → list[str]`.

Replicates the Perl side of `mu2ejobsub` (lines 290–371):
- Outstage path computation: `$wftop/$USER/workflow/$wfproject/outstage`
  with role-aware default (`/pnfs/mu2e/persistent/users` for Production,
  `/pnfs/mu2e/scratch/users` otherwise)
- Token-dir computation (`/pnfs/mu2e/...` → `/mu2e/...`)
- Predefined-args → singularity image (`al9` →
  `fnal-wn-el9:latest`)
- Error-delay scaling (1s if njobs≤10, else 1800s)
- Inspec JSON synthesis (dataset → `(protocol, location)` map)
- All `MU2EGRID_*` env exports
- Final argv: jobsub flags + `-l priority` + singularity +
  `-e` chain + `--need-storage-modify <token-dir>` + `-N njobs` +
  `-f dropbox://<jobdef>` + `-f dropbox://<inspec>` +
  `file://<our worker script>`

### Step 3 — Wire `submit.py` (`--backend` flag)

**~50 LOC diff.** Add `--backend {mu2ejobsub,direct}`:
- `mu2ejobsub` (default): current behavior, preserved as fallback
- `direct`: call `jobsub_argv.build()` + `subprocess.run(['jobsub_submit', ...])`.
  Skip Perl entirely.

Default stays `mu2ejobsub` until `direct` is shadow-validated.

### Step 4 — Shadow validation

Submit same POMS-map entry both ways on the 2-job BeamSplitter test:
- `bin/submit_map --map ... --entry 11 --backend mu2ejobsub`
- `bin/submit_map --map ... --entry 11 --backend direct`

Diff:
- **Outstage tree** structure (should match modulo timestamps)
- **SAM registrations**: direct path adds them; mu2ejobsub doesn't —
  this is the actual win
- **Per-job logs**: manifest format must match
  `mu2eClusterCheckAndMove` parser

## What changes for the worker

`mu2ejobsub.sh` (the Perl-side worker) does:
- ifdh stage-in via `mu2ejobiodetail --prestage-spec` + `ifdh cp -f`
- `mu2ejobfcl` for per-job fcl
- `mu2e -c`
- atomic outstage via random tmp-dir + `ifdh rename`
- SHA256 manifest in log via `addManifest`
- JSON sidecar via `printJson.sh --parents`
- ifdh stage-out to `$MU2EGRID_WFOUTSTAGE/<cluster>/<thousands>/<index>/`
- **No pushOutput** — files just sit in outstage

`runjob.py` does:
- ifdh stage-in driven by `jobiodetail.job_inputs(index)`
- `Mu2eJobFCL.generate_fcl(index)` for per-job fcl
- `mu2e -c` via `build_mu2e_cmd`
- `push_data()` — runs pushOutput, registers in SAM with parents
- `push_logs()` — uploads log
- SHA256 manifest in log (ported from `addManifest`)

## Validation matrix

| Aspect | mu2ejobsub.sh (today) | runjob.py (Phase 2) |
|---|---|---|
| Per-job fcl | `mu2ejobfcl` Perl CLI | `Mu2eJobFCL.generate_fcl()` Python |
| Per-job inputs | `mu2ejobiodetail --prestage-spec` | `Mu2eJobIO.job_inputs()` |
| ifdh stage-in | `ifdh cp -f spec` | `ifdh cp` per file from inspec map |
| `mu2e -c` | bash time-wrapped | `build_mu2e_cmd` |
| Outstage layout | `$WFOUTSTAGE/<cluster>/<thousands>/<index>` | only for log push (`push_logs`) |
| SAM-side dataset path | n/a | resolved by `pushOutput` from `dh.location` |
| SHA256 manifest | `addManifest` (bash) | port to Python (`_emit_manifest`) |
| JSON sidecar | `printJson.sh --parents` | regenerated by `pushOutput` internally |
| **SAM registration** | **none** | **`push_data()` (the new value)** |

## Correctness blockers (must address before coding)

These came out of the post-2026-04-30 review. None are negotiable.

### CB1 — SAM/dCache token scope

`--need-storage-modify <dir>` adds dCache `storage.modify` scope on
that directory. The mu2ejobsub Perl path passes only WFOUTSTAGE
because its worker shim writes outputs only to outstage. Direct mode
runs `pushOutput` on the worker, which writes to
`/pnfs/mu2e/<area>/datasets/...` — a path the WFOUTSTAGE-only token
does NOT cover. Symptom: `gfal-copy error: HTTP 403 - DESTINATION
MAKE_PARENT - Permission refused` on first push attempt.

**Resolution (2026-05-02, after smoke test cluster 27987658):**
`utils/jobsub_argv.output_storage_dirs(outputs)` derives one
`/mu2e/<area>/datasets` scope per unique location in
`outputs[].location` and emits a separate `--need-storage-modify`
flag for each. WFOUTSTAGE token stays as-is for log/manifest staging.

Open question: SAM `samweb file-declare` may need a separate
compute.modify scope. The smoke test will tell us once the dCache
write succeeds.

### CB2 — `push_output()` silently swallows failures

`utils/prod_utils.py:765-767` warns and returns the exit code, but
`runmu2e._dispatch_and_execute` ignores it. On a worker without POMS
supervising, transient samweb hiccups → cluster reports success with
unregistered files — exactly the failure mode Phase 2 is meant to fix.
**Action:** `runjob.py` treats `push_data` / `push_logs` non-zero as
job failure (exit non-zero, condor sees failure). Add retry loop with
exponential backoff inside `push_output` (3 retries, 30s base).

### CB3 — jobset PROCESS→index mapping

When `--jobs i1,i7,i42` is used, the Perl pipeline writes the jobset
array into the ops JSON, and `mu2ejobmap --clusterpars` (Perl, in
mu2ejobtools) maps `$PROCESS` (0..N-1) → real index. Our worker has
no equivalent.
**Action:** `runjob.py` reads the ops JSON's `jobset[PROCESS]` to
get the real index. Pure dict lookup, no Perl needed. Spec the ops
JSON as a Phase 2 deliverable, not just inspec.

### CB4 — Manifest format is byte-exact

`mu2eClusterCheckAndMove` regex-parses the manifest. Naïve port
breaks downstream tooling silently. Specifically:
- Sentinel: `^# mu2egrid manifest *$`
- Selfcheck: `^# mu2egrid manifest selfcheck: <hex> *- *$`
  (the trailing ` -` comes from `sha256sum < $manifest`, NOT
  `sha256sum $manifest` which emits `<hex>  filename`)
- `ls -al` output parsed positionally — pin `LC_ALL=C`
- Manifest covers `<file>` AND `<file>.json` pairs

**Action:** port `addManifest` faithfully (including the
fd-redirect dance to write manifest after log is closed for
normal output). Add a unit test that runs a real
`mu2eClusterCheckAndMove` against our manifest output.

### CB5 — JSON sidecars are not redundant with `push_data()`

`pushOutput` itself shells `printJson.sh` to compute `dh.sha256`,
`dh.first_run_event`, runs/subruns, `GenEventCount` via
`mu2e -c file_info_dumper`. So sidecars are regenerated under the
hood. If SimJob env was unsetup before push_data runs, push fails.
**Action:** `runjob.py` MUST keep SimJob sourced when calling
`push_data` and `push_logs`. Treat as hard contract; assert in code.

### CB6 — UPS package versions on the worker

The Perl resolves `IFDH_VERSION`, `MU2EGRID_MU2EJOBTOOLS_VERSION`,
`MU2EGRID_MU2EFILENAME_VERSION` via `ups list -K version` and ships
as env vars; the worker uses them in `setup -B <pkg> $VERSION`.
Empty values trigger 30-min error sleeps.
**Action:** since Phase 2 worker uses `muse setup ops` + the prodtools
helpers (which pin their own versions), we drop the per-package
`setup -B` calls entirely. ifdh comes from `muse setup ops`. Drop
all three env vars from the argv. Spec this clearly so the worker
script doesn't accidentally `setup -B`.

### CB7 — EXPERIMENT and IFDH_VERSION env vars

Perl explicitly pushes `-e EXPERIMENT=mu2e` and
`-e IFDH_VERSION=...`. The "all `MU2EGRID_*`" handwave misses both.
**Action:** argv builder explicitly emits `-e EXPERIMENT=mu2e`.
Drop `IFDH_VERSION` per CB6.

### CB8 — `CONDOR_DIR_INPUT` for dropbox files

`-f dropbox://<file>` lands the file under `$CONDOR_DIR_INPUT`,
not cwd. Without this, `runjob.py` will not find the jobdef.
**Action:** worker resolves jobdef path via
`os.environ['CONDOR_DIR_INPUT'] + '/' + os.environ['MU2EGRID_JOBDEF']`.
Same for ops JSON.

### CB9 — Outstage `mkdir` from submitter side

The Perl creates `$wftop/$USER/workflow/$wfproject/outstage` on
PNFS via `File::Path::make_path` from the submitter. Even with
per-job pushOutput, log push and any cluster-level artifacts need
this path. `ifdh mkdir_p` is recursive but a wrong wftop default
creates files where SAM can't see them.
**Action:** keep the make_path call in the argv builder. Use the
same role-aware default as the Perl
(`/pnfs/mu2e/persistent/users` for Production,
`/pnfs/mu2e/scratch/users` otherwise).

### CB10 — `fname` coupling for non-jobdef modes

`runmu2e.py` parses `fname` (per-job filename) to derive index in
`process_template` and `process_direct_input`. POMS sets fname per
PROCESS. Phase 2 worker going `$PROCESS`-only handles jobdef mode
cleanly but breaks template/direct-input modes.
**Action:** Phase 2 v1 supports JOBDEF MODE ONLY. Template /
direct-input / g4bl modes stay on the `mu2ejobsub` backend. Spec
this as an explicit scope cut. POMS-map entries with no `njobs`
(direct-input) or `fcl_template` (template) get rejected by
`--backend direct` with a clear error.

## Scope tightening (Phase 2 v1)

To make this a tractable bite-sized delivery rather than a "rewrite
all of mu2egrid" effort:

- **In scope:** jobdef-mode normal entries (have `tarball` +
  `njobs`). The vast majority of production POMS-map entries.
- **Out of scope:** template mode (`fcl_template`), direct-input
  mode (`tarball` without `njobs`), g4bl mode (`runner: "g4bl"`),
  HPC sites (`MU2EGRID_HPC`). These keep using `--backend mu2ejobsub`.
- **Out of scope:** `--prestage-spec` for arbitrary file lists
  (POMS-map doesn't use this; mu2ejobsub does).

## Risks (now in addition to CB above)

1. **Manifest format drift.** `mu2eClusterCheckAndMove` parses the
   exact `addManifest` log format. Our port must produce
   byte-equivalent output (modulo timestamps).

2. **ifdh retry/escalation behavior.** `mu2ejobsub.sh` retries with
   `IFDH_DEBUG=10` on first failure. Need to replicate or accept
   different retry semantics.

3. **Atomic outstage.** `mu2ejobsub.sh` writes to a random tmp-dir
   then `ifdh rename` so partial outputs never appear at the final
   path. Must port faithfully.

4. **`push_data` parent tracking.** Currently uses POMS-style
   `parents_list.txt` from the `infiles` env var (set by POMS).
   Need to construct it from `Mu2eJobIO.job_inputs(index)` instead.

5. **Token lifecycle on the worker.** `jobsub_submit` provides
   `--need-storage-modify` token; `runjob.py` must not assume the
   submitter's token is present.

6. **Outputs from a failed job.** `runmu2e` skips `push_data` on
   `mu2e -c` failure but still pushes logs. Replicate that.

## Done criteria

Phase 2 v1 (jobdef-mode only):

- 2-job test cluster submitted via `--backend direct --entry 11`
  (BeamSplitter) lands outputs AND registers them in SAM with
  correct parents.
- `mu2eClusterCheckAndMove` accepts our manifest format
  (validate by running it on the test cluster's logs).
- `push_data` / `push_logs` failure → job exits non-zero, condor
  records failure (CB2 verified).
- SAM token scope sufficient for `samweb file-declare` (CB1).
- `--backend mu2ejobsub` still works (no Phase 1 regression).
- POMS-map entries that aren't jobdef-mode (template, direct-input,
  g4bl) get a clear "use --backend mu2ejobsub" error (CB10).

## Validation gates (must pass before promoting `direct` to default)

1. **1-job parity**: same entry, same outputs, byte-identical
   manifest hash modulo timestamps.
2. **100-job shadow**: `--backend mu2ejobsub` and `--backend direct`
   on the same entry, diff SAM-registered file counts. Direct should
   register 100, mu2ejobsub should register 0 (it doesn't push).
3. **Token expiry simulation**: kill the worker token mid-job,
   verify `push_data` retries and ultimately fails the job
   (does NOT silently pass).
4. **Manifest validator**: run `mu2eClusterCheckAndMove` against
   100-job shadow output; zero parser errors.
5. **1000-job real campaign** with `--backend direct`, full SAM
   registration, recovery loop tested.

## Ownership cost (accepted)

By replacing `mu2egrid::impl/mu2ejobsub.sh` we take ownership of:
- ifdh stage-in/out semantics on the worker
- atomic outstage (tmp-dir + ifdh rename)
- SHA256 manifest format (with `mu2eClusterCheckAndMove` parser
  contract)
- Token lifecycle on the worker
- condor schedd / jobsub_lite changes that previously came for free
  via upstream `mu2egrid` updates from Andrei Gaponenko

This was reviewed and accepted. Driver: a fully Perl-free pipeline
is a stated team goal; tracking upstream Perl indefinitely is not
acceptable. Consequence: `runjob.py` and `jobsub_argv.py` need ongoing
maintenance — we cannot fire-and-forget. They become part of
prodtools' core surface.

## Out of scope

- Replacing `jobsub_submit` itself (Fermilab-owned)
- Eliminating the Perl `mu2egrid` package — `jobsub_submit` itself
  may still pull it via UPS
- Removing the `mu2ejobsub` backend — stays as fallback

## Alternatives rejected

- **Post-hoc pushOutput from login node** — simpler, but registers
  per-cluster instead of per-job; failed jobs leave junk needing
  filtering. Considered for Phase 1 but user wants per-job model.
- **Forking `mu2egrid` to add a worker hook** — divergence risk
  from upstream package; user explicitly does not want Perl path.
