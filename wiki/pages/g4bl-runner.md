---
title: g4bl runner architecture (native AL9 spack)
tags: [reference, runner, g4bl, spack, al9]
sources: [2026-04-27-g4bl-runner-integration]
updated: 2026-05-05
---

# g4bl runner architecture

`prodtools` schedules Geant4 Beamline (`g4bl`) jobs alongside its
Offline-stage runners but the execution path is independent: no
`mu2e -c`, no SAM-art FCL pipeline. Output is `.root` (`nts.mu2e.*`
tier per metacat convention).

g4bl's place in the prodtools chain is documented in
[[json2jobdef-staging-workflow]] §"g4bl is decoupled". This page
covers **how the runner actually works** today and why.

## Current execution path (post-`401e3da`, native AL9 spack)

`utils/prod_utils.py:process_g4bl_jobdef` builds a small bash script
and runs it via `subprocess.Popen`:

```
bash -c '
  unset SPACK_ENV PYTHONHOME PYTHONPATH
  source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh > /dev/null 2>&1
  eval "$(spack load --sh g4beamline)"
  cd <embed_dir>
  g4bl <main_input> viewer=none histoFile=<seq>.root \
       Num_Events=<N> First_Event=<F>
'
```

- **No apptainer / no SL7 container.** Workers already run on AL9
  (`fnal-wn-el9` outer container set by `poms/fermigrid.cfg`); g4bl
  3.08b has a native AL9 build available via spack.
- **`unset SPACK_ENV`** is mandatory before sourcing. `bin/runmu2e`
  invokes `muse setup ops` before launching the Python subprocess,
  which activates the `ops-019` spack env; without unsetting,
  `spack load g4beamline` searches only `ops-019` (no g4beamline
  there) and fails with "matches no installed packages". See memory
  `reference_spack_env_after_muse_setup.md`.
- **`unset PYTHON*`** before sourcing — g4bl spack-load itself runs
  Python; AL9-mu2e PYTHONHOME/PATH leaks confuse it.
- **`g4bl key=value` (CLI)**, NOT `param key=value`. Same issue as
  the older 3.08 SL7 build: 3.08b rejects the `param` form on the
  command line — see memory
  `reference_g4bl_param_unset_semantics.md`. The `param` form is
  input-file syntax only.

## What changed in `401e3da` (2026-04-28)

Commit `Switch g4bl runner to native AL9 spack; minimize POMS map shape`
removed ~50 LOC of container wrapping:

| Concern | Before `401e3da` (SL7/apptainer) | After `401e3da` (native AL9 spack) |
|---|---|---|
| Container | `apptainer exec --cleanenv` against `/cvmfs/singularity.opensciencegrid.org/fermilab/fnal-dev-sl7:latest` | None — runs in the `fnal-wn-el9` worker outer container |
| Binds | HOME, `/tmp` (whole), `embed_dir`, `/cvmfs` | None (worker FS already has `/cvmfs`, `/tmp`, etc.) |
| Env hygiene | `--cleanenv` (drops PYTHONHOME / UPS_DIR / PRODUCTS that leaked from AL9 parent into SL7) | `unset SPACK_ENV PYTHON*` before sourcing (selective; same intent, but no container barrier needed) |
| Container override | `DEFAULT_G4BL_CONTAINER` constant + opt-in `container` JSON field | Removed |
| SL7-detection | `_is_inside_sl7()` (read `/etc/redhat-release`, skip wrap when grid Condor scheduled job inside SL7 directly via `poms/g4bl.cfg`'s `+SingularityImage`) | Removed |
| POMS submit cfg | `poms/g4bl.cfg` (sets `+SingularityImage` outer container to `fnal-dev-sl7`) | Deleted; reuses `poms/fermigrid.cfg` |
| LOC in `process_g4bl_jobdef` | ~120 LOC | ~70 LOC |

The pre-`401e3da` path is captured in `wiki/raw/2026-04-27-g4bl-runner-integration.md`
for institutional record. Don't cite it as current state.

## Why two SL7 gotchas became unnecessary

The 2026-04-27 raw notes flagged two gotchas that were specific to
the apptainer/SL7 wrap and don't apply now:

- **A.** `--cleanenv` mandatory when launching apptainer from a
  Python subprocess whose parent had AL9 mu2e env sourced. Symptom:
  `bash: setup: command not found` at line 3 of the runner script
  because UPS init silently failed under leaked AL9 PYTHONHOME.
- **B.** `/tmp` had to be bound *wholesale*, not just the per-job
  output subdir, because UPS init in `setupmu2e-art.sh` uses `/tmp`
  for scratch.

Both are gone with the native AL9 path. The replacement gotchas
(SPACK_ENV unset, `param` CLI form) are documented in their own
memory entries.

## POMS map shape (also minimized in `401e3da`)

Production `data/<campaign>/g4bl.json` carries 5 fields per entry
(matching the `MDC2025-NNN.json` map convention):

```json
{
  "runner": "g4bl",
  "tarball": "...",      // built once by g4bl_jobdef
  "njobs": <N>,
  "inloc": "none",
  "outputs": [{"dataset": "nts.mu2e.G4blPOT.TESTaa.root", "location": "disk"}]
}
```

Runtime config (`desc`, `dsconf`, `main_input`, `events_per_job`)
lives in `jobpars.json` *inside* the tarball — the tarball is
self-describing for grid replay. Embed_dir mode (local smoke) keeps
the full schema since there's no tarball.

`validate_jobdesc` enforces:
- `tarball` mode → require only `outputs`
- `embed_dir` mode → require `desc`, `dsconf`, `main_input`,
  `events_per_job`, `outputs`

No fallbacks. Missing required fields fail loudly per the
no-fallbacks discipline (memory `feedback_no_fallbacks.md`).

## Naming & dsconf convention

- Output tier: `nts.mu2e.*` (canonical Mu2e ntuple tier; matches
  metacat convention). Was `g4bl.mu2e.*` pre-`401e3da`.
- `desc`: `G4blPOT` (descriptive of POT physics, not an art-side
  musing tag). Was `Mu2EBeamline` / `Mu2EBeamlineSmoke` pre-`401e3da`.
- `dsconf`: `TESTaa` (test marker; clearly out-of-band of MDC
  campaigns). Was `MDC2025ai_g4bl_v1_0` pre-`401e3da` — that form
  conflated g4bl with the Offline SimJob versioning, misleading
  given g4bl doesn't share the SimJob pipeline.

## Demonstrator artifacts (from `401e3da`)

- Tarball SAM-declared at
  `/pnfs/mu2e/tape/phy-etc/cnf/mu2e/G4blPOT/TESTaa/tar/c7/74/`
- POMS map: `G4BL-000.json` (separate map family from `MDC2025-NNN`)
- SAM index def: `iG4BL-000` (1 file)

## Related

- `utils/prod_utils.py:process_g4bl_jobdef` (current implementation)
- Memory `reference_g4bl_decoupled_from_offline.md` (place in chain)
- Memory `reference_spack_env_after_muse_setup.md` (SPACK_ENV gotcha)
- Memory `reference_g4bl_param_unset_semantics.md` (CLI param form)
- Memory `feedback_no_fallbacks.md` (validation discipline)
- `wiki/raw/2026-04-27-g4bl-runner-integration.md` (pre-`401e3da` history)
