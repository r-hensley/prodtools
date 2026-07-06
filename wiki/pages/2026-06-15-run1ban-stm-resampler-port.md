---
title: Run1Ban STM resampler entries added
tags: [campaign, run1b, run1ban, stm, resampler]
sources: [2026-06-15-run1ban-stm-resampler-port]
updated: 2026-06-15
---

# Run1Ban STM resampler entries added

**Source:** session work 2026-06-15
**Date ingested:** 2026-06-15
**Type:** decision

## Summary

Ported 3 of 4 STM (Stopping Target Monitor) resampler entries from
`data/mdc2025/resampler_stm.json` (MDC2025ai) to a new
`data/Run1B/resampler_stm.json` for the Run1Ban field-off campaign.
The fourth MDC2025ai entry (`STMNeutralsToVD`) was deliberately
skipped — no equivalent Run1Ban-named `NeutralsCat` exists.

All three entries share the Run1Ban convention:
`dsconf=Run1Ban-001`, `simjob_setup=SimJob/Run1Ban`, `run=1470`,
`geom_run1_b_v40.txt`, `outloc *.art → disk`, `inloc=tape`,
`njobs=5000`, `events=200000`, `sequential_aux=true`.

Each entry produces **two** output streams per the `BeamTo2VD.fcl`
pattern (`compressedOutput101` for VD101, `compressedOutput116` for
VD116), so `fcl_overrides` declares both
`outputs.compressedOutput101.fileName` and
`outputs.compressedOutput116.fileName`. Production pushes registered
6 dataset names total (2 per cnf) into POMS map MDC2025-029.

## Key Takeaways

- **Beam inputs reuse Run1Bai cats.** STMBeamToVDEle consumes
  `sim.mu2e.EleBeamCat.Run1Bai.art` and STMBeamToVDMu consumes
  `sim.mu2e.MuBeamCat.Run1Bai.art` — the Run1Bai beam cats are
  reusable across Run1B field-off variants because beam collection
  happens at TS3Vacuum (per `epilog_1b.fcl`), upstream of DS where
  the field-off matters.
- **Target input comes from the Run1Ban-rebuilt chain.**
  STMBeamToVDTarget consumes
  `sim.mu2e.TargetStopsCat.Run1Ban-001.art` — the same cat produced
  by the [[2026-06-07-run1ban-mustop-rebuild-chain]] for the
  MuStopPileup entry. Chain-internal reuse, no chicken-and-egg.
- **Uniform sizing differs from MDC2025ai source.** MDC2025ai uses
  heterogeneous njobs (5k/20k/1k/20k) and one odd event count
  (1106516 for Ele). Run1Ban port normalized to 5000×200000 across
  all three, per user request — uniform per-job statistics.
- **events=200000 is consistent across all three entries.** Per-event
  CPU is roughly init-dominated at low N (20-event vs 100-event
  smokes); marginal cost per event is low, so 200k/job is comfortable
  within grid wall-time budgets.
- **Skipped STMNeutralsToVD.** No `sim.mu2e.NeutralsCat.Run1Ban*.art`
  source exists. Producing one would require a new Neutrals chain
  step; deferred until needed.

## Entities Touched

- [[run1ban-campaign]] — adds STM stage to entry inventory.

## Production push outcome

Pushed to `MDC2025-029.json` (extended in place per "always extend
latest until 100k jobs" rule) on 2026-06-15:

| index | desc              | njobs | events  | input                                       |
| ----- | ----------------- | ----- | ------- | ------------------------------------------- |
| [10]  | STMBeamToVDEle    | 5000  | 200000  | sim.mu2e.EleBeamCat.Run1Bai.art             |
| [11]  | STMBeamToVDMu     | 5000  | 200000  | sim.mu2e.MuBeamCat.Run1Bai.art              |
| [12]  | STMBeamToVDTarget | 5000  | 200000  | sim.mu2e.TargetStopsCat.Run1Ban-001.art     |

Map total: 46004 → 61004 jobs after the 3 pushes
(15000 added). Still under the 100k cap.

## Multi-output fcl convention

`BeamTo2VD.fcl` declares two `RootOutput` streams gated by separate
trigger paths (`STMCompressedPath` → VD101,
`STMCompressedPath116` → VD116). Both stream names must be
explicitly overridden in `fcl_overrides`:

```
"outputs.compressedOutput101.fileName": "dts.mu2e.{desc}101.Run1Ban-001.sequence.art",
"outputs.compressedOutput116.fileName": "dts.mu2e.{desc}116.Run1Ban-001.sequence.art"
```

This produces datasets `dts.mu2e.<desc>101.Run1Ban-001.<seq>.art` and
`dts.mu2e.<desc>116.Run1Ban-001.<seq>.art` — i.e. the STM port
follows the multi-output suffix pattern noted in
[[digi-output-stream-by-fcl]] for digi fcls, but here the suffix is
the VD number rather than Triggered/Triggerable.

## Relation to Other Wiki Pages

- Sister of [[2026-06-14-run1ban-primaries-added]] — same Run1Ban-001
  dsconf, same run/geom/SimJob; STM stage extends the Run1Ban-001
  inventory in MDC2025-029.
- Depends on [[2026-06-07-run1ban-mustop-rebuild-chain]] for
  STMBeamToVDTarget input (`TargetStopsCat.Run1Ban-001`).
- Multi-output override pattern relates to
  [[digi-output-stream-by-fcl]] — same principle (override every
  stream the fcl declares), different stream-name shape.

## Related

- [[run1ban-campaign]]
- [[run1bak-campaign]] — sister field-off campaign at the same run
  number; does not yet have STM entries.
