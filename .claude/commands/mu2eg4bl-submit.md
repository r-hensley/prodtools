---
description: Submit a g4bl smoke cluster via upstream mu2eg4bl (mu2egrid v8) with the three flags it actually needs in 2026 — UPS version, SL7 container, and the storage-modify scope that prevents silent dCache 403s
argument-hint: [--scripts-dir D] [--in F] [--tar T] [--njobs N] [--events-per-job M] [extra mu2eg4bl flags]
allowed-tools: Bash
---

# Submit a `mu2eg4bl` smoke cluster (2026-correct flags)

`mu2eg4bl` (`/cvmfs/.../mu2egrid/v8_03_02/bin/mu2eg4bl`) was authored
before Mu2e's bearer-token migration. The bare invocation it documents
in `--help` looks reasonable but **silently loses output** in 2026
because (a) UPS G4beamline v3_08 is SL7-built and crashes on the default
AL9 worker container, and (b) the default worker bearer token has no
`storage.modify` scope for the user's outstage path, so `copyback.sh`
catches an HTTP 403 from dCache and **exits 0 anyway**. See memory
`reference_mu2eg4bl_needs_storage_modify.md` for the full diagnosis.

This skill wraps the corrected invocation: three required extra flags,
plus auto-build of `Geometry.tar` from `Geometry/` when missing, plus
token presence check.

For production-style g4bl work prefer the prodtools native-AL9 runner:
`/stage-entry g4bl --desc <D> --dsconf <C>` (see
`wiki/pages/g4bl-runner.md`). This skill is for one-off beamline studies
that need to stay on the upstream `mu2eg4bl` codepath.

## Usage

```
/mu2eg4bl-submit [--scripts-dir D] [--in F] [--tar T] [--njobs N] [--events-per-job M] [extra-flags]
```

- `--scripts-dir D` — directory to submit from. Default:
  `/exp/mu2e/app/users/$USER/G4BeamlineScripts`. Must contain the `--in`
  file and (if not pre-built) the `Geometry/` subdir.
- `--in F` — g4bl input. Default: `Mu2E.in`. Resolved relative to
  `--scripts-dir`.
- `--tar T` — geometry tarball. Default: `Geometry.tar`. If absent but
  `<scripts-dir>/Geometry/` exists, the skill builds it (`tar cf
  Geometry.tar Geometry/`).
- `--njobs N` — number of grid jobs. Default: `3`.
- `--events-per-job M` — events each job runs. Default: `10`.
- Any other flags pass through to `mu2eg4bl` verbatim
  (`--memory`, `--expected-lifetime`, `--site`, `--priority`, etc.).

The three flags the skill **always** appends (and you should not
override unless you know why):

- `--g4bl-version=v3_08` (UPS version string; **not** spack's `v3_08b`).
- `--predefined-args=sl7` (worker container; AL9 default lacks
  `libssl.so.10` that the UPS binary needs).
- `--jobsub-arg=--need-storage-modify=/mu2e/scratch/users/$USER/outstage`
  (issues the worker token a `storage.modify` scope for the user
  outstage path so the dCache PUT actually succeeds).

## Examples

```
# Default smoke cluster (3 jobs × 10 events of /exp/.../G4BeamlineScripts/Mu2E.in)
/mu2eg4bl-submit

# Bigger batch from a different scripts dir
/mu2eg4bl-submit --scripts-dir /exp/mu2e/app/users/$USER/beam_study \
                 --in BeamScan.in --njobs 20 --events-per-job 1000

# With extra jobsub knobs
/mu2eg4bl-submit --njobs 5 --events-per-job 100 \
                 --memory 4000MB --expected-lifetime 8h
```

## Instructions

You are given `$ARGUMENTS`. Follow these steps:

1. **Parse args.** Set defaults:
   - `SCRIPTS_DIR = /exp/mu2e/app/users/$USER/G4BeamlineScripts`
   - `IN = Mu2E.in`
   - `TAR = Geometry.tar`
   - `NJOBS = 3`
   - `EVENTS_PER_JOB = 10`
   Strip `--scripts-dir`, `--in`, `--tar`, `--njobs`, `--events-per-job`
   from the arg list; keep the rest as `EXTRA`.

2. **Refuse the three auto-flags in `EXTRA`.** If the user passed any of
   `--g4bl-version`, `--predefined-args`, or `--need-storage-modify`
   themselves, stop and tell them this skill enforces 2026-correct
   defaults; if they need a different combination they should call
   `mu2eg4bl` directly. (Edge case: a user knowingly running a
   non-default scope path is one direct invocation away.)

3. **Validate inputs.** Resolve `IN` and `TAR` against `SCRIPTS_DIR`.
   - If `SCRIPTS_DIR` doesn't exist → exit with a clear error.
   - If `<SCRIPTS_DIR>/<IN>` doesn't exist → exit with a clear error.
   - If `<SCRIPTS_DIR>/<TAR>` doesn't exist, check for
     `<SCRIPTS_DIR>/Geometry/`. If present, build the tar:
     `(cd <SCRIPTS_DIR> && tar cf <TAR> Geometry/)` and report the
     size. If neither tar nor Geometry/ exists, exit with an error.

4. **Verify bearer token.** Check for token at the standard paths
   (`/run/user/$(id -u)/bt_u$(id -u)` first, fall back to
   `/tmp/bt_u$(id -u)`). If neither exists, **stop** and tell the user:

   ```
   No bearer token found. Run this in the prompt:
     ! htgettoken -i mu2e -a htvaultprod.fnal.gov
   Then re-invoke /mu2eg4bl-submit.
   ```

   If a token is present, run `httokendecode -H 2>&1 | head -3` to
   confirm it's parseable. Don't try to renew the token from here —
   token refresh is interactive.

5. **Submit.** Source the Mu2e environment, set up `mu2egrid`, `cd`
   into `SCRIPTS_DIR`, and run:

   ```bash
   mu2eg4bl \
     --in=<IN> \
     --tar=<TAR> \
     --njobs=<NJOBS> \
     --events-per-job=<EVENTS_PER_JOB> \
     --g4bl-version=v3_08 \
     --predefined-args=sl7 \
     --jobsub-arg=--need-storage-modify=/mu2e/scratch/users/$USER/outstage \
     <EXTRA>
   ```

   Capture the cluster ID from the line `<N> job(s) submitted to
   cluster <CLUSTER>.` If submission fails, surface the full stderr —
   don't paper over it.

6. **Report.** Print a short summary:
   - Cluster id (`<CLUSTER>.0@jobsub05.fnal.gov`)
   - Expected outstage:
     `/pnfs/mu2e/scratch/users/$USER/outstage/<jobname>.<CLUSTER>/`
     where `<jobname>` is derived from the `--in` basename (typically
     `Mu2E` for `Mu2E.in`)
   - Monitor command:
     `condor_q -name jobsub05.fnal.gov -constraint 'ClusterId==<CLUSTER>' -af ProcId JobStatus`
   - Wall-time expectation: ~3–5 min per job for a 10-event smoke

   **Do not** auto-monitor or auto-fetch logs — let the user decide
   when to check. Grid jobs may sit Idle for minutes to hours
   depending on FermiGrid load.

## Notes

- The `jobsub_q --jobid <CLUSTER>@schedd` output can transiently show
  `0 total` even while jobs are running. Use
  `condor_q -name jobsub05.fnal.gov -constraint 'ClusterId==<N>'` as
  ground truth.
- Failure signature when `--need-storage-modify` is missing: jobs
  ExitCode=0, condor_history shows success, outstage directory is
  never created on PNFS. `jobsub_fetchlog` followed by
  `grep "HTTP 403" *.err` confirms it.
- Token scopes are not all pre-allocated: `htvaultprod.fnal.gov` will
  issue arbitrary `storage.modify:/mu2e/scratch/users/<user>/outstage`
  scopes on request (contrary to what
  `reference_dcache_token_scopes.md` previously implied for production
  paths).
- The prodtools g4bl runner (`data/<campaign>/g4bl.json` +
  `json2jobdef`) avoids this entire trap: native AL9 spack, scope
  handling via `runmu2e.py` direct mode, outputs registered in SAM.
  Use it for anything that needs to be tracked, recovered, or
  published. See `wiki/pages/g4bl-runner.md`.
