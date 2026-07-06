---
title: Add direct submission path alongside POMS
tags: [decision, plan, submission, poms, mu2ejobsub, jobsub_submit]
sources: []
updated: 2026-04-29
---

# Plan: Add direct submission path alongside POMS

**Date:** 2026-04-29
**Type:** ADR / implementation plan
**Status:** Proposed (reviewed 2026-04-29)

## Goal
prodtools gains a self-contained submit→track→recover loop that
bypasses POMS. The existing POMS path is preserved — both coexist,
chosen per campaign or per run.

## Context

Today's split of responsibilities:

- **prodtools** builds cnf tarballs (`json2jobdef`) and writes a
  POMS-map JSON (e.g., `poms_map/MDC2025-NNN.json`).
- **POMS** reads that map, runs `mu2ejobsub` per entry on a managed
  schedule, monitors clusters, runs recoveries.
- **prodtools** ingests POMS state back via `pomsMonitor` /
  `db_builder` to track completeness — but the SAM-side completeness
  signal (`jobiodetail --outputs` × samweb) never actually depends
  on POMS.

The direct-submit path adds an alternative dispatcher that sits next
to POMS, not in place of it.

## POMS-map JSON — full schema

The plan must handle the complete entry shape, not just the common
case. Union across all production maps (986 entries surveyed):

| Field | Type | Required | Description |
|---|---|---|---|
| `tarball` | string | most modes | cnf tarball name |
| `njobs` | int | normal mode | Job count. **Absent** in direct-input mode |
| `inloc` | string | always | `"tape"`, `"disk"`, `"none"`, `"dir:<path>"` |
| `outputs` | array | always | `[{dataset: glob, location: "tape"\|"disk"}, ...]` |
| `runner` | string | rare | Dispatch override, e.g. `"g4bl"` |
| `fcl_template` | string | template mode | FCL path (no tarball) |
| `setup_script` | string | template mode | SimJob setup script |
| `indef` | string | rare | Explicit input SAM definition |
| `template_overrides` | object | rare | Key-value overrides for template expansion |

**Dispatch modes** (from `prod_utils.validate_jobdesc()`):
- **Normal**: `tarball` + `njobs` present
- **Direct-input**: `tarball` present, no `njobs`
- **Template**: `fcl_template` present (no tarball at all)
- **g4bl**: `runner: "g4bl"`

Phase 1 `submit.py` must handle normal mode. Direct-input, template,
and g4bl modes should be explicitly scoped out with a clear error
message ("use POMS for template-mode entries") or handled if
straightforward.

## Phase 1 — Direct-submit driver (keep `mu2ejobsub` Perl)

Fastest to value: removes POMS dependency for submission while
keeping `mu2ejobsub` (upstream `mu2egrid` package) as the
worker-side wrapper.

### New artifacts
- `utils/submit.py` — POMS-map entry → `mu2ejobsub` argv builder +
  invoker. Reads the same POMS-map JSON that `json2jobdef --jobdefs`
  produces.
- `bin/submit_map` — wrapper script (same idiom as `bin/runmu2e`).
  Modes: `--all` (every entry in the map), `--entry N` (single
  entry by index), `--dry-run` (print argv, don't submit),
  `--max-concurrent N` (throttle: submit at most N total jobs across
  entries to replace POMS `maxConcurrent=5000`).
- `utils/submission_db.py` — extend `poms_db` ORM with a `source`
  discriminator rather than creating a separate DB. This lets
  `pomsMonitor`/`db_builder`/`listNewDatasets` query both POMS-
  sourced and direct-submit records through the same interface.
  Core fields: `(id, cnf_tarball, jobset_spec, condor_cluster,
  submitted_at, parent_id, status, source)`.
  `parent_id` links recoveries to their original.
  **Location:** under `/exp/mu2e/app/users/mu2epro/` for production
  (group-writable); user-local for test submissions.
  **Concurrency:** `fcntl.flock` advisory lock on DB writes —
  SQLite WAL on GPFS is unreliable without it.
- `utils/recover.py` — reuse `mkrecovery.find_missing_indices()`
  for the diff logic. Multi-entry maps require offset-aware index
  aggregation (same as `mkrecovery --jobdesc` does today).
  Resubmit via `mu2ejobsub --jobs=i1,i2,...` per tarball.
  No SAM `etc.mu2e.index` dataset needed.
  **Guard:** require all condor jobs in the cluster to reach terminal
  state (`condor_history`) before recovery is eligible. Add
  `--min-age HOURS` flag (default 4h) to prevent double-submit from
  SAM registration latency.
- `bin/recover` — wrapper.
- `bin/submit_status` — query the submissions DB + `condor_q` /
  `condor_history` + SAM-side completeness. Graceful degradation
  when `condor_q` is unavailable (fall back to SAM-only).

### Reuse from existing code
- `mkrecovery.find_missing_indices()` — core recovery diff logic
- `prod_utils._fetch_file_local()` — mdh copy for tarballs
- `prod_utils._extract_simjob_setup()` — reads setup from tarball
- `prod_utils.validate_jobdesc()` — validates map entry structure
- `prod_utils.run()` — command executor with streaming output
- `poms_db.get_db_session()` / ORM `Base` — extend, don't fork

### Touch points (additive, no existing code broken)
- `utils/poms_db.py` — add `source` column to `Job` model (or new
  `Submission` model alongside existing tables).
- `utils/pomsMonitor.py`, `utils/db_builder.py`,
  `utils/listNewDatasets.py --completeness` — teach them to also
  read direct-submit records. POMS-map ingestion stays as-is.
- `EXAMPLES.md` / `docs/EXAMPLES_schema.md` — add `submit_map`,
  `recover`, `submit_status` invocations; run `/refresh-examples`.

### Preserved (unchanged)
- Full POMS path: POMS-map JSON generation, POMS dispatch,
  `pomsMonitor`, `mkrecovery` with SAM index datasets — all stay
  functional.
- Per-entry config in `data/<campaign>/*.json`.
- `mu2ejobsub` behaviors: token handling, outstage layout,
  singularity image selection.
- SAM-side completeness (works identically for both paths).

### Risks and mitigations
- **Crash mid-loop → partial submissions.** Write to DB *before*
  invoking `mu2ejobsub` with status `pending`, update to
  `submitted` + cluster ID on return. On restart, `submit_map`
  detects `pending` rows with no cluster ID and either skips or
  re-queries. Resume/idempotency: `--resume` flag re-reads the map
  and skips entries whose tarballs already have a `submitted` row.
- **Condor cluster ID parsing** from `mu2ejobsub` stdout — copy
  the regex from `mu2egrid`.
- **Token expiry mid-loop** on big maps — pre-flight
  `httokendecode` check with minimum remaining lifetime threshold
  (e.g., 1h per 10 entries).
- **No throttling** — `--max-concurrent` flag replaces POMS
  `maxConcurrent`. Check `condor_q -totals` before each entry and
  sleep if over limit.
- **SQLite on GPFS** — advisory lock (`fcntl.flock`) on every
  write transaction. Per-map DB file as fallback if corruption
  persists.

### Done criteria
- Submit one full POMS-map entry end-to-end via `bin/submit_map`,
  outputs land in PNFS, registered in SAM.
- Run a recovery via `bin/recover` against deliberately-killed jobs.
- `submit_status` shows completeness matching `listNewDatasets`.
- Existing POMS path still works (no regressions).

## Phase 2 — Replace `mu2ejobsub` with Python

Only after Phase 1 is validated. This is the de-Perl chunk. The POMS
path is unaffected — it continues to call the upstream `mu2ejobsub`.

### What `mu2ejobsub` actually does (from source review)

Submit-side:
- Scrubs all `MU2EGRID_*` env vars before starting
- Reads the cnf tarball via `Mu2eJobPars` to extract `njobs()`,
  `input_datasets()` for building the inspec map
- Builds an **ops JSON** containing the resolved jobset (array of
  indices) and inspec (per-dataset protocol+location map from
  `--location`/`--protocol` flags)
- Resolves UPS "current" versions of `mu2efilename` and
  `mu2ejobtools` at submit time
- Creates outstage directory on PNFS via `File::Path::make_path`
- Auto-scales `--error-delay` (1s for ≤10 jobs, 1800s for >10)
- Passes `--need-storage-modify <token-dir>` for write scope
- Full argv includes ~15 `-e MU2EGRID_*=...` env exports +
  `dropbox://` transfers for ops JSON and jobdef tarball

Worker-side (`mu2egrid::impl/`):
- CVMFS freshness check (`cvmfs-uptodate`)
- `$PROCESS` normalization (falls back to `SLURM_PROCID` for HPC)
- `mu2ejobmap --clusterpars` resolves `$PROCESS` → job index via
  ops JSON (NOT a 1:1 identity)
- Atomic outstage via random tmp-dir + `ifdh rename`
- ifdh retry with debug escalation (`IFDH_DEBUG=10` on first fail)
- SHA256 manifest (`addManifest`) appended to log — downstream
  `mu2eClusterCheckAndMove` depends on this exact format
- JSON metadata sidecar creation (`printJson.sh --parents`)
- `IFDH_CP_UNLINK_ON_ERROR=1` workaround
- File retirement on payload failure (partial outputs not declared)

### New artifacts
- `utils/jobsub_argv.py` — pure-Python argv-builder replicating all
  of the above submit-side behaviors: env scrubbing, ops JSON
  synthesis, UPS version resolution, outstage mkdir, token-dir
  computation, error-delay scaling, inspec map construction.
- `utils/worker/run_job.sh` — replacement worker entry script.
  Must replicate: CVMFS check, `$PROCESS` normalization, index
  resolution (replace `mu2ejobmap` with Python equivalent or
  embedded logic), per-job fcl materialization (via `jobfcl`),
  ifdh stage-in with retry + debug escalation, `mu2e -c` execution,
  JSON metadata sidecar creation, SHA256 manifest in log,
  atomic outstage (tmp-dir + ifdh rename), error-delay sleep,
  file retirement on failure.
- Unit tests against known-good `mu2ejobsub --dry-run --verbose`
  outputs to prove argv parity.

### Touch points
- `utils/submit.py` gains a `--backend {mu2ejobsub,direct}` flag.
  Default stays `mu2ejobsub` until `direct` is validated.
- The worker shim becomes `run_job.sh`, transferred via
  `--input-file`.

### Risks
- **Phase 2 scope is large.** The worker-side logic is ~500 lines
  of battle-tested Perl/bash with subtle behaviors (manifest format,
  atomic rename, ifdh escalation). Each is a regression site.
- Mitigation: shadow-run Phase 2 for one campaign — submit identical
  maps with both backends, diff outstage trees — before retiring
  Phase 1's `mu2ejobsub` path.
- Validate manifest format against `mu2eClusterCheckAndMove` (it
  parses specific SHA256 line formats).

### Done criteria
- One campaign run end-to-end with `--backend direct`, no Perl in
  the submit or worker path.
- `--backend mu2ejobsub` (and POMS path) still work.
- Outstage tree from `direct` backend is byte-identical in structure
  to `mu2ejobsub` backend (modulo timestamps).

## Out of scope
- Replacing `jobsub_submit` itself (Fermilab-owned, already Python).
- Cron / scheduled submission — keep manual for both phases.
- Removing the POMS path — stays indefinitely as supported
  alternative.

## Alternatives considered
- **Remove POMS entirely.** Deferred: no reason to break working
  campaigns. Parallel path is lower-risk.
- **Port `mu2ejobsub` first (Phase 2 before Phase 1).** Rejected:
  doesn't address the primary pain (POMS as out-of-band dependency)
  and delays the useful deliverable.
- **Keep SAM `etc.mu2e.index` datasets for direct-submit
  recoveries.** Not needed — `jobsub_submit --jobs=...` accepts
  indices directly. Can re-add if recovery provenance becomes a need.
- **Separate `submission_db.py` with standalone SQLite.** Rejected
  in favor of extending `poms_db` ORM — avoids parallel query paths
  and keeps `pomsMonitor`/`listNewDatasets` unified.
