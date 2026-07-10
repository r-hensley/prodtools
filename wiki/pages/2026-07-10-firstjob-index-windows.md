---
title: firstjob index windows — statistics expansion without seed collisions
tags: [decision, jobdef, poms, seeds, expansion, resampler]
sources: []
updated: 2026-07-10
---

# `firstjob` index windows (implemented 2026-07-10)

**Decision:** a POMS-map entry may carry `"firstjob": F`, windowing the
entry into its cnf's index space: the entry's `njobs` global slots run
cnf indices `[F, F+njobs)` instead of `[0, njobs)`. This is the
supported mechanism for extending a dataset's statistics through POMS.

## Why

The per-job seed is flat: `baseSeed = 1 + cnf index` (verified in both
prodtools `job_common.job_seed` and upstream Perl `Mu2eJobPars::job_seed`;
SeedService policy `autoIncrement` seeds engines from baseSeed alone).
`firstSubRun = index` likewise. Consequences:

- **The `version` key gives no statistical independence.** It only
  renames the tarball (`cnf...{version}.tar`, `jobdef.py`) and by
  convention bumps `run` — neither enters the RNG. A version-bumped
  entry re-runs local indices 0..N-1 → baseSeed 1..N → **duplicate
  physics** on the same input. Historical generations
  (Run1Baa/ag/ai/an, run +10 each) were independent only because each
  also swapped the input stops catalog.
- **The old dispatch hard-coded window start 0**
  (`local = global - cumulative`), so no map entry could reach fresh
  indices; only direct `mu2ejobsub --firstjob` could.
- **Bumping njobs on the existing entry** (5000 → 5000+N) would work
  arithmetically but re-inserts the completed 0..4999 into the drained
  index range — the exact L1/L2 clobber exposure of
  [[2026-07-05-run1ban-mix-recovery-data-loss]].

The tarball is a pure function `cnf(index) → job`; the *window* is a
dispatch property and therefore lives in the map, not the tarball
(a tarball-embedded offset would force a new tarball per expansion,
recreating the version-key mess). Capacity (`tbs.njobs`,
[[2026-07-02-jobdef-arithmetic-and-tbs-njobs]]) stays in the tarball;
the map picks the window within it.

## Semantics

- `local = global − cumulative + firstjob` (`prod_utils.resolve_map_index`,
  extracted pure + unit-tested).
- Entry validation: `firstjob` int ≥ 0, requires `njobs` (no generic
  entries); closed cnfs capacity-checked (`firstjob + njobs ≤ tbs.njobs`);
  open-ended cnfs (resamplers/generators) unrestricted.
- Same tarball may appear once **per window** in a map
  (json2jobdef dedupe key is now `(tarball, firstjob)`).
- mu2ejobsub backend maps a windowed entry to
  `--firstjob F --njobs M` (native support, mu2egrid v8_03_02
  `mu2ejobsub:202-211`); plain entries keep `--all`.
- Direct backend: jobset stays 0-based (PROCESS space); the offset is
  applied worker-side by `resolve_map_index` since the entry ships in
  `ops['jobdesc']`.
- `mkrecovery`: expected names generated over `[F, F+njobs)`; recovery
  (index-dataset) definition undoes the offset
  (`global = cumulative + (local − F)`). Single-tarball mode grew
  `--firstjob`.
- `db_builder`: Job.njobs stores the **window end** (`firstjob + njobs`)
  — windows tile from 0, so the highest window end is the expected file
  count for completeness math.

## Expansion recipe (e.g. MuStopPileup.Run1Ban 5000 → 5000+N)

1. Existing cnf untouched — **no retire, no rebuild, no new version**.
2. New map entry: `{tarball: cnf.mu2e.MuStopPileup.Run1Ban-001.0.tar,
   firstjob: 5000, njobs: N, inloc: …, outputs: […]}` in the
   current/latest map; `mkidxdef --prod` resizes `i<map>`.
3. Jobs run cnf indices 5000+ → baseSeed 5001+, sequencers
   `001470_00005000+`, same dataset.
4. Downstream Cat must **append** (artcat only the new files) — never
   re-Cat in place ([[predictive-naming-proposal]] n→1 rule).

Files touched: `utils/{poms_entry,prod_utils,json2jobdef,submit,
mkrecovery,db_builder}.py`, tests in `test/test_unit.py` (§34),
`docs/EXAMPLES_schema.md` tribal-knowledge bullet.

## Related

- [[2026-07-05-run1ban-mix-recovery-data-loss]] — why not to re-expose
  completed indices to recovery
- [[2026-07-02-jobdef-arithmetic-and-tbs-njobs]] — capacity vs window
- [[poms-reference]] — index-dataset dispatch machinery
- [[run1ban-campaign]] — first intended use (MuStopPileup expansion)
