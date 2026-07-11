---
title: Run1Ban-001 primaries (CeEndpoint, FlateMinus, FlatGamma, NoPrimary) added
tags: [decision, campaign, run1ban]
sources: [2026-06-14-run1ban-primaries-added]
updated: 2026-06-14
---

# Run1Ban-001 primaries (CeEndpoint, FlateMinus, FlatGamma, NoPrimary) added

**Source:** `data/Run1B/primary_muon.json` (entries appended 2026-06-14)
**Date ingested:** 2026-06-14
**Type:** decision

## Summary

Four primary-stage entries were added to `data/Run1B/primary_muon.json`
to produce the field-off signal/background primaries for the Run1Ban
chain on top of the just-completed [[2026-06-07-run1ban-mustop-rebuild-chain]]
pool. The four entries — `CeEndpoint`, `FlateMinus`, `FlatGamma` (all
`dsconf=Run1Ban-001`) and `NoPrimary` (`dsconf=Run1Ban`) — mirror the
existing Run1Bai-001 block shape but with three deliberate divergences:
geometry file `geom_run1_b_v40.txt` instead of `v06`, run number `1470`
instead of `1460`, and input dataset `sim.mu2e.MuminusStopsCat.Run1Ban.art`
instead of the Run1Bai counterpart. `simjob_setup` is `SimJob/Run1Ban`
and outputs go to disk.

All four were locally smoke-verified with `mu2e -c <cnf>.fcl --nevts 1`
on 2026-06-14 reading `MuminusStopsCat.Run1Ban` via xrootd from
`/pnfs/.../tape/...` — Art exited with status 0 in all cases. The
resampler primaries (`inloc=resilient`) consume `MuminusStopsCat.Run1Ban`
through `TargetStopResampler`; `NoPrimary` (`inloc=disk`) needs no
upstream art input.

The total of 26000 new jobs (3 × 2000 resampler primaries + 20000
NoPrimary) extends `MDC2025-029.json` from 20004 → 46004, still under
the 100k cap, so the existing map is the push target.

## Key Takeaways

- Run1Ban primaries diverge from the Run1Bai precedent on geom (v40 vs
  v06), run number (1470 vs 1460), input pool (Run1Ban vs Run1Bai),
  and SimJob tag. Filter settings (`StrawGasSteps=[]`,
  `MinimumSumCaloStepE=20`, `MinimumPartMom=0`) and momentum windows
  (50–110 MeV for FlateMinus/FlatGamma) are copied verbatim.
- Geom `v40` matches what
  [[2026-05-22-mdc2025ap-rpcexternal-chain]] (no, see
  `resampler_beam_mixing.json` Run1Ban-001 entries) established for
  the Run1Ban mixing chain; a single geom is the deliberate choice
  across the Run1Ban dsconf namespace.
- `MuminusStopsCat.Run1Ban` was produced by
  [[2026-06-07-run1ban-mustop-rebuild-chain]]; these primary entries
  are the first downstream consumers of that pool.
- Smokes were one-event reads against tape via xrootd
  (`xroot://fndcadoor.fnal.gov//pnfs/.../MuminusStopsCat/Run1Ban/art/95/76/`).
  No upstream missing-data issues.
- 26000 new jobs fit the existing `MDC2025-029.json` POMS map; the
  100k cap rule applies (see `feedback_extend_existing_poms_map`).

## Entities Touched

- [[run1ban-campaign]] — new downstream stage producing physics primaries
- [[2026-06-07-run1ban-mustop-rebuild-chain]] — upstream pool consumer

## Relation to Other Wiki Pages

- Closes the open question implicit in
  [[2026-06-07-run1ban-mustop-rebuild-chain]] — "what consumes the
  Run1Ban MuminusStopsCat pool?" The four primaries here are the
  first consumers.
- Parallels Run1Bai-001 primary entries in `data/Run1B/primary_muon.json`
  lines 148-241 but is **not** a copy: see Key Takeaways for the
  three deliberate divergences.
