---
title: "File-location resolver module + SAM query module (implemented 2026-07-06)"
tags: [decision, plan, prodtools, refactor, sam, dcache]
sources: []
updated: 2026-07-06
---

# File-location resolver + SAM query module

**Status: IMPLEMENTED 2026-07-06** (approved 2026-07-03, "Do 1 and 2").
Candidates #1 and #3 from the 2026-07-02 architecture review, done together
in one session. Candidate #2 (jobdef arithmetic) was already done — see
[[2026-07-02-jobdef-arithmetic-and-tbs-njobs]]. Implementation summary at
the bottom of this page.

## Goal

One deep module answering **"given a Mu2e filename and an inloc, where does
it live and how do I read/stage/write it"**, sitting on top of one module
that owns **all SAM access and the query-dimension grammar**. Callers stop
touching path grammar, `SAMWebClient`, and dimension strings entirely.

## Evidence (current anchors, post-arithmetic-refactor)

Four resolution mechanisms across five modules, plus a broken seam:

- `utils/jobfcl.py:114` `_locate_file` — branches on inloc: `dir:` prefix
  slice, stash CVMFS path build, resilient path + gfal2 stat, SAM locate.
  `utils/jobfcl.py:169` `_format_filename` — second layer applying the
  `/pnfs/ → xroot://fndcadoor...` transform.
- **Seam break:** `utils/jobfcl.py:141` constructs a raw
  `SAMWebClient(experiment='mu2e')` (import at `:19`), duplicating
  `samweb_wrapper.locate_file_full`'s locate-and-filter logic inside the
  hottest consumer (every worker fcl generation).
- `utils/stash_utils.py:63` `_subpath`, `:73` `read_path_for_file`, `:192`
  `resilient_path_for_file` — parallel stash/resilient path builders;
  jobfcl does NOT call them (duplicate grammar).
- `utils/datasetFileList.py:22` `_dataset_dir` — independently hard-codes
  the `/pnfs/mu2e/{persistent,tape,scratch}/datasets/...` layout.
- `utils/prod_utils.py:92` `_fetch_file_local` — `mdh copy-file` staging;
  the worker's `--copy_input` branch resolves through this while the
  streaming branch resolves through jobfcl — two engines for the same file.
- `utils/jobsub_argv.py:75` `storage_scope_for_file` — re-derives the same
  `phy/usr` + `tier_class` dCache layout as token scopes. A layout change
  today means editing this AND datasetFileList; a miss silently 403s
  pushOutput.
- Third SAM access mechanism: `utils/latestDatasets.py:96` shells out to
  the `samweb` CLI (`count-files`) — different auth/env/error modes from
  both the wrapper and the raw client.
- Query grammar composed ad hoc in 14 files (grep `dh.dataset|defname:`):
  datasetFileList, db_builder, famtree, genFilterEff, jobdef_lookup,
  json2jobdef, latestDatasets, listNewDatasets, logparser, mixing_utils,
  mkrecovery, prod_utils, samweb_wrapper, stash_utils. Inconsistent syntax:
  `dh.dataset=X` vs `dh.dataset X` vs `defname:`, `event_count>0` appended
  in some sites and a toggle in others.
- `samweb_wrapper.py` itself is shallow: 1:1 pass-through whose only real
  behavior is error-swallowing (`return []`/`0` on exception) — plus a
  second pass-through layer of module-level functions.

## Proposed shape (to be grilled at implementation time)

**SAM query module** (deepen `samweb_wrapper` in place, keep the name):
- Named query constructors so no caller writes a dimension string:
  `files_in_dataset(ds, with_events=False)`, `file_count(ds)`,
  `dataset_exists(ds)`, `children_of(file)`, `definition_files(defname)`, …
- Becomes the ONLY SAM access path: absorb jobfcl's raw client and
  latestDatasets' CLI subprocess.
- Decide per method: swallow-and-default vs fail loud (no-fallbacks
  discipline says fail loud unless the caller has a documented reason).
- This is the real seam for the eventual samweb→MetaCat migration (open
  question in [[prodtools-prd]] §13): two adapters, one interface.

**File-location resolver** (new module, e.g. `utils/file_resolver.py`):
- Interface sketch: given filename (+ inloc + protocol), answer
  `read_path()` / `read_url()` (xroot), `stage_command()` (mdh),
  `storage_scope()` (token), `dataset_dir()`.
- Adapters behind the seam per inloc: `dir:` literal, stash (CVMFS),
  resilient (gfal2 stat + SAM-location xroot fallback — preserve the
  behavior documented in memory `reference_inloc_resilient_resolution`),
  disk/tape (SAM locate, `remove_storage_prefix`, xroot transform).
- Consumes only the SAM query module — never `samweb_client` directly.
- Callers to migrate: `jobfcl` (`_locate_file`/`_format_filename`),
  `prod_utils._fetch_file_local` + worker copy-input branch, `stash_utils`
  path builders, `datasetFileList._dataset_dir`,
  `jobsub_argv.storage_scope_for_file` (unify with
  `Mu2eName.tier_class` — the layout table already lives in job_common).

**Preserve bug-for-bug on the worker path.** The resolver must reproduce
current jobfcl behavior exactly (including quirks) — the worker's inner
loop is production-critical. Byte-identical fcl output for a set of real
cnf tarballs (mix, resampler, generic, dir:, stash, resilient, tape) is
the acceptance test; unit tests get a fake-SAM adapter.

## Open design questions (grill before coding)

1. Resolver granularity: one module-level function set vs a small class
   holding (inloc, proto) like `Mu2eJobFCL` does today.
2. Does `Mu2eJobFCL` keep thin `_locate_file`/`_format_filename` shims
   delegating to the resolver (zero interface change), or do callers move?
   Recommend shims first, migrate later.
3. Error-mode policy per SAM query method (fail loud vs default) — audit
   the 14 call sites' actual tolerance.
4. gfal2 dependency placement (currently lazily imported inside jobfcl).
5. Whether `mdh` staging belongs behind the same seam or stays a separate
   executor concern (overlaps with review candidate #4).

## Non-goals

- No MetaCat adapter yet — just make the seam real enough that one can be
  added as a second adapter.
- No behavior change to inloc semantics (resilient fallback, tape xroot
  reads of disk-cached files, etc.).
- Candidate #4 (submit/runmu2e pure-core extraction) and #5 (prod_utils
  split) stay separate; #5 partially falls out of this work.

## Remaining small items from the review (independent quick wins)

- `chain_emit.py:290` hand-splits dataset names — last core-path bypass of
  `Mu2eName`.
- Owner-default `USER→mu2e` massage still copied in `jobdef.py` (×2) and
  `json2jobdef.py` (jobfcl's copy already consolidated into `Mu2eJobBase`).
- Deferred from the arithmetic refactor: `_compute_jobset` clamp relaxation
  for open-ended jobdefs (direct-mode extension past declared njobs);
  source-type detection unification (needs a tarball-format decision).

## Implementation (2026-07-06)

### What landed

**SAM query module** — `samweb_wrapper.py` deepened in place:

- `q_*` query-string builders own ALL dimension grammar: `q_dataset`
  (with_events / availability), `q_definition`, `q_dataset_below_sequencer`,
  `q_dataset_files_named`, `q_dataset_like`, `q_parents_of_dataset`,
  `q_children_of_file`, `q_recent_files`. Callers needing a query as data
  (e.g. `create_definition`) use a builder; nobody hand-writes
  `dh.dataset ...` anymore (repo-wide grep clean).
- Named query methods (+ module-level conveniences): `files_in_dataset`,
  `dataset_file_count`, `dataset_summary`, `definition_file_count`,
  `parents_of_dataset`, `children_of_file`, `files_like`,
  `locate_file_strict`, `definitions_matching(defname=, user=)`.
- Absorbed both rogue SAM access paths: jobfcl's raw
  `SAMWebClient(experiment='mu2e')` (via `locate_file_strict`) and
  latestDatasets' `samweb` CLI subprocesses (via `definitions_matching` /
  `dataset_file_count`).
- `SAMWebWrapper.__init__` now resolves the experiment explicitly
  (`SAM_EXPERIMENT` → `EXPERIMENT` → `'mu2e'`), preserving jobfcl's
  worker-safe hardcoded-experiment guarantee.

**File resolver** — new `utils/file_resolver.py`:

- Module-level path grammar (single home): `dataset_subpath`,
  `stash_read_path` / `stash_write_path` / `resilient_path` (+ roots),
  `dataset_dir` (physical /pnfs layout; tape has NO `datasets/` component),
  `storage_scope` (token scopes; ALWAYS have `datasets/`, intentionally
  differing from the tape physical layout), `xroot_read_url`,
  `resilient_file_exists` (gfal2, lazy import).
- `FileResolver(inloc, proto)` class with `locate()` / `url()` reproducing
  the historical `Mu2eJobFCL._locate_file` / `_format_filename` behavior
  bug-for-bug (including the `xroot://` read vs `root://` stat prefix
  discrepancy).
- Pure at import time: samweb/gfal2 imported lazily, so `dir:`-mode
  resolution and pure-function consumers work without the ops env.

**Migrated callers**: `jobfcl` (thin shims retained — zero interface
change), `stash_utils` (all path builders delegate; SAM via named queries),
`datasetFileList._dataset_dir`, `jobsub_argv.storage_scope_for_file`
(delegate kept for `submit.py`), plus dimension-string sites in
json2jobdef, mkrecovery, mixing_utils, jobdef_lookup, db_builder,
prod_utils, listNewDatasets, famtree, genFilterEff, latestDatasets.

### Open questions → decisions

1. **Granularity**: small `FileResolver(inloc, proto)` class for the
   per-jobdef flow + module-level pure functions for the path grammar.
2. **Shims**: kept — `Mu2eJobFCL._locate_file`/`_format_filename` delegate;
   callers unchanged.
3. **Error modes**: named query methods FAIL LOUD (no-fallbacks
   discipline); legacy generic passthroughs (`list_files`, `count_files`,
   `describe_definition`, ...) keep their swallow-and-default behavior
   because callers rely on it (e.g. `prod_utils` uses
   `describe_definition() == ''` as an existence probe). Cosmetic
   consumers that can tolerate absence now handle it visibly (e.g.
   listNewDatasets' size column try/excepts to 'N/A' with a comment).
4. **gfal2**: stays lazily imported, now inside
   `file_resolver.resilient_file_exists`.
5. **mdh staging**: left in `prod_utils._fetch_file_local` — executor
   concern, candidate #4 territory.

### Verification

- **Byte-identical fcl**: 8 (tarball × inloc × proto) combos on the 3 real
  local NoPrimaryMix1BB cnfs (v1_4-000, v1_5-000, v1_5-001) —
  resilient/root, tape/root, tape/file, dir:/file, stash/root — all
  IDENTICAL before vs after (10 primary + 29 pileup files resolved per
  mixing fcl, exercising resilient-hit, SAM-locate, and dir: paths).
- **Unit tests**: 292 tests, identical pass state to pre-refactor baseline
  (11 pre-existing pomsMonitor/SQLAlchemy import errors, unrelated). Test
  mocks updated to patch the new seam
  (`utils.samweb_wrapper.locate_file_strict`, `files_in_dataset`, ...).

### Still open (unchanged from plan)

- `chain_emit.py:290` Mu2eName bypass; owner-default USER→mu2e copies in
  `jobdef.py`/`json2jobdef.py`; `_compute_jobset` clamp relaxation;
  source-type detection unification.
- MetaCat second adapter — the seam now exists (`samweb_wrapper` is the
  only SAM access path).

## Related

- [[2026-07-02-jobdef-arithmetic-and-tbs-njobs]] — completed candidate #2
- [[prodtools-prd]] — §13 MetaCat migration open question
- [[metacat-reference]] — target of the future second adapter
- memory `reference_inloc_resilient_resolution` — resilient fallback
  semantics the resolver must preserve
- memory `reference_dcache_token_scopes` — scope layout the resolver owns
