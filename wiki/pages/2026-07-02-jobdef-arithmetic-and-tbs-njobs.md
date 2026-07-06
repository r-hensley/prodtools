---
title: "Decision: jobdef arithmetic lives once in Mu2eJobBase; tarballs carry tbs.njobs"
tags: [decision, prodtools, jobdef, refactor]
sources: []
updated: 2026-07-02
---

# Decision: jobdef arithmetic lives once in Mu2eJobBase; tarballs carry tbs.njobs

**Date:** 2026-07-02
**Status:** implemented (uncommitted at time of writing; 292 unit tests green,
smoke-verified with a real `json2jobdef` build of NoPrimary/Run1Bai)

## Decision 1 — one implementation of the per-index job arithmetic

`sequencer()`, `job_outputs()`, `job_event_settings()`, `job_seed()`, and
`njobs()` now live **once**, in `Mu2eJobBase` (`utils/job_common.py`), and are
inherited by `Mu2eJobPars` (introspection) and `Mu2eJobFCL` (FCL generation).
`utils/jobiodetail.py` (`Mu2eJobIO`) is **deleted**; its consumers
(`mkrecovery`, `submit`, `prod_utils`, `db_builder`, `jobdef_lookup`) now use
`Mu2eJobPars`.

### Why

The worker names its real output files through `Mu2eJobFCL.generate_fcl`, so
jobfcl's semantics are ground truth by definition. But three divergent copies
existed:

- `jobiodetail.Mu2eJobIO.sequencer` lacked `sequencer_from_index`,
  PBISequence's `source.runNumber`, and consulted primary inputs *before*
  `event_id` (jobfcl does the reverse). Consequence: **mkrecovery, submit,
  db_builder and jobdef_lookup could disagree with the worker** about output
  filenames — e.g. for any mix jobdef whose parent dataset has holes,
  mkrecovery predicted parent-derived sequencers while the worker wrote
  position-derived ones, silently breaking recovery.
- `jobiodetail.job_outputs` skipped the `.owner./.version./{desc}`
  substitutions.
- `jobquery.Mu2eJobPars.sequencer` was a literal stub (`seq_{index:06d}`) and
  `output_files()` built malformed names from it.
- `jobfcl.njobs` answered 0 for samplinginput (resampler) jobdefs;
  `jobquery.njobs` had the samplinginput branch but a dead top-level-`njobs`
  reader and silent `merge_factor=1` fallbacks (now fail loud).

Regression tests: `TestJobArithmeticConsolidation` in `test/test_unit.py`.

## Decision 2 — the tarball is self-descriptive: `tbs.njobs`

**Rule: whatever job count `json2jobdef` resolves for the map entry is also
embedded in the tarball as `tbs.njobs`** (`jobdef._resolve_njobs`). The
declared config value wins after validation against the capacity derived from
the frozen input lists (declared > capacity fails loud at build time); `-1`
or absent means "embed the derived value".

| Jobdef kind | `tbs.njobs` | Notes |
|---|---|---|
| Generator (event_id) | declared value | previously lived only in the POMS map |
| Input-driven / sampling | resolved value | declared cap if set, else derived ceil; can never go stale (file list frozen in same tarball) |
| Generic tarball (`{desc}`) | absent | genuinely open-ended, 1 job per fname; absence stays load-bearing (direct-input trigger) |
| Legacy tarballs in SAM | absent | readers keep the derive-else-0 fallthrough forever |

Reader contract (`Mu2eJobBase.njobs()`): `tbs.njobs` → derived from `inputs`
→ derived from `samplinginput` → `0`. **0 means "open-ended, not a property
of this jobdef"** — the count is a submit-time decision, authoritative in the
POMS map. It is a documented sentinel, not a fallback.

### Why

The direct-submission backend (`submit.py`) already declares "njobs from the
cnf is authoritative; POMS-map's field is informational" and reads the cnf
unconditionally — so it **could not submit generator jobdefs at all**
(`njobs()==0` → empty jobset). Embedding closes that hole and aligns with the
remove-POMS-from-the-submit-loop direction: in a POMS-free world there is no
map to be the "somewhere else". POMS-path behavior is untouched (POMS drives
off the map + index def and never opens the tarball).

### Alternatives considered

- **Keep njobs map-only (status quo)** — rejected: direct backend broken for
  generators; provenance requires hunting mutable map files for a
  SAM-archived artifact.
- **Embed for generators only** — superseded by the uniform "what goes in the
  map entry goes in the tarball" rule; uniformity also preserves declared
  caps (< derived capacity) for input-driven entries.
- **Top-level `njobs` key** — rejected; prodtools format extensions live
  under `tbs` (`sequencer_from_index`, `event_id_per_index`, `chunk_mode`);
  top-level stays Perl-pure (`code`, `setup`, `tbs`, `jobname`).

## Consequences / behavior changes

- `test/compare_tarballs.sh` jq-diffs now apply `del(.tbs.njobs)` — same
  treatment other prodtools extension keys would need.
- `jobfcl` CLI on **new** generator tarballs now clamps `--index` to the
  declared njobs (finite jobset). Extending a generator campaign in direct
  mode beyond the declared count (relaxing `_compute_jobset`) is a deliberate
  follow-up, not done here. POMS-mode extension (map edit + `mkidxdef`) is
  unaffected.
- `jobdef` CLI one-offs don't take a declared njobs flag; only the
  `json2jobdef` path embeds declared counts. CLI-built input-driven jobdefs
  still get the derived value embedded.
- `mkrecovery`/`db_builder`/`jobdef_lookup`/`submit` now compute output names
  with worker semantics (correctness fix, see Decision 1).

## Descoped

Source-type detection remains dual-engine (`jobdef._get_source_type` via
`fhicl-get` at build time vs `jobfcl._get_source_type` substring match at
read time). Unifying means recording `source_type` in `jobpars.json` — a
format change to take deliberately, like `tbs.njobs` was, if/when needed.

## Related

- [[2026-04-29-remove-poms-from-submit-loop]] — the direction this supports
- [[2026-04-30-phase2-direct-jobsub-implementation]] — the backend that
  needed self-descriptive tarballs
- [[json2jobdef-staging-workflow]] — where declared `njobs` enters configs
