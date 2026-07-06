---
title: Run1Ban self-contained MuminusStopsCat rebuild via MuBeamResampler side output
tags: [decision, run1b, run1ban]
sources: [2026-06-07-run1ban-mustop-rebuild-chain]
updated: 2026-06-07
---

# Run1Ban self-contained MuminusStopsCat rebuild via MuBeamResampler side output

**Source:** in-session edits 2026-06-06 → 2026-06-07 on branch `field-off-option`; modified `data/Run1B/resampler_beam_mixing.json` and `data/Run1B/merge_filter.json`
**Date ingested:** 2026-06-07
**Type:** decision

## Summary

The new Run1Ban field-off resamplers in `data/Run1B/resampler_beam_mixing.json` (NeutralsFlash / MuBeamFlash / EleBeamFlash / MuStopPileup at dsconf `Run1Ban-001`, run 1470, geom `geom_run1_b_v40.txt`, `bfgeom_DSOff.txt`) cannot reuse the existing `sim.mu2e.MuminusStopsCat.Run1Bai.art` as the resampler source for `MuStopPileup`: the older `Run1Bai` cat does not propagate the particle content required by the Run1Ban resampler geometry/field combination. A new `MuminusStopsCat.Run1Ban` must be produced before the Run1Ban `MuStopPileup` entry is runnable.

The chain is now **self-contained inside the Run1Ban-001 family**, with no upstream regeneration needed. The key insight is that `Production/JobConfig/pileup/MuBeamResampler.fcl` already emits five outputs in a single job — `MuBeamFlash`, `EarlyMuBeamFlash`, `TargetStops`, `PolyStops`, and `IPAStops` — so the `MuBeamFlash@Run1Ban-001` resampler entry simultaneously produces `sim.mu2e.TargetStops.Run1Ban-001.art` as a side output. No separate "TargetStops producer" entry is needed.

The full Run1Ban MuminusStopsCat rebuild chain is now three steps in two files:

1. **`MuBeamFlash@Run1Ban-001`** (existing, in `resampler_beam_mixing.json`) — already emits `sim.mu2e.TargetStops.Run1Ban-001.art`.
2. **`TargetStopsCat@Run1Ban-001`** (new, in `merge_filter.json`) — `artcat.fcl` merges 2500 `TargetStops.Run1Ban-001` files into `sim.mu2e.TargetStopsCat.Run1Ban-001.art`.
3. **`MuonStopSelector@Run1Ban`** (new, in `merge_filter.json`) — `pileup/MuonStopSelector.fcl` applies `ParticleCodeFilter` (`[13, "uninitialized", "muMinusCaptureAtRest"]`) to `TargetStopsCat.Run1Ban-001` and emits `sim.mu2e.MuminusStopsCat.Run1Ban.art` (and `MuplusStopsCat.Run1Ban` as a second output stream).

The `MuStopPileup@Run1Ban-001` entry in `resampler_beam_mixing.json` then consumes `sim.mu2e.MuminusStopsCat.Run1Ban.art`.

## Investigation that produced the insight

Initial drafts wired the new TargetStopsCat entry to `sim.mu2e.TargetStops.Run1Baa1.art` (4999 files, disk-resident), reusing the old Run1Baa1 stops via artcat → MuonStopSelector. After the user constraint **"start from sim.mu2e.TargetStops.Run1Ban.art"** (no Run1Ban version of TargetStops on SAM at the time), the question became: which fcl produces `sim.mu2e.TargetStops.<dsconf>.art` at all?

- Searched `data/Run1B/*.json` for `TargetStops` references — only consumers (resamplers, artcat), no producer entry.
- Searched `Production/JobConfig/primary/`, `pileup/`, `beam/` in the Run1Ban musing — `TargetStopParticle.fcl` is the resampler base (consumer); no obvious dedicated producer fcl.
- SAM lineage of `sim.mu2e.TargetStops.Run1Bai-007.001460_00000000.art` showed parents = `sim.mu2e.MuBeamCat.Run1Bai.001460_00000115.art` (MuBeamCat is the upstream, not a separate "stops producer").
- Reading `MuBeamResampler.fcl` end-to-end revealed five `RootOutput` blocks: `TargetStopOutput`, `PolyStopOutput`, `IPAStopOutput`, `FlashOutput`, `EarlyFlashOutput`. `TargetStops` is one of MuBeamResampler's outputs, not a separate stage.

So the existing `MuBeamFlash@Run1Ban-001` entry already produces `sim.mu2e.TargetStops.Run1Ban-001.art`, and the chain shortens to two new entries instead of three.

## Key Takeaways

- **One MuBeamResampler job, five output streams.** Don't add a "TargetStops producer" entry for any Run1B/MDC2025 campaign — the same `MuBeamResampler@<dsconf>` entry emits `MuBeamFlash`, `EarlyMuBeamFlash`, `TargetStops`, `PolyStops`, and `IPAStops` simultaneously. The dsconf on the side outputs matches the job's dsconf.
- **MuminusStopsCat chain pattern (Run1B convention).** `MuBeamResampler@<dsconf>` → `artcat@<dsconf>` over its `TargetStops` side output → `MuonStopSelector@<dsconf>` → `MuminusStopsCat.<dsconf>`. The Run1Bai precedent is split across `merge_beam_pileup.json` (TargetStopsCat) and `merge_filter.json` (MuonStopSelector); the Run1Ban version places both in `merge_filter.json`.
- **MuonStopSelector is purely particle-ID filtering**, not physics-dependent. It uses `ParticleCodeFilter` to split TargetStopFilter into mu− and mu+ streams. So the "doesn't propagate the right particles" constraint is satisfied by ensuring the *upstream* TargetStops carries the right content (i.e., comes from the matching-geometry MuBeamResampler), not by changing the selector.
- **Cross-campaign reuse breaks at geometry boundaries.** `MuminusStopsCat.Run1Bai` (geom v06) cannot feed Run1Ban resamplers (geom v40). When introducing a new geometry, the MuminusStopsCat must be rebuilt from a TargetStops produced under that geometry — even though MuonStopSelector itself doesn't read geometry.
- **dsconf naming for the new chain:** intermediate Cat keeps the side-output dsconf (`Run1Ban-001`); the final MuminusStopsCat uses the campaign dsconf (`Run1Ban`). This matches the Run1Bai precedent (`TargetStopsCat.Run1Bai-003` → `MuminusStopsCat.Run1Bai`).

## Pattern correction during the work

Initial draft (committed and then revised on 2026-06-07): TargetStopsCat entry used `dsconf: "Run1Ban"` and `input_data: sim.mu2e.TargetStops.Run1Baa1.art`. Both were wrong:

- The dsconf should be `Run1Ban-001` to match the resampler-job dsconf that produces the upstream `TargetStops.Run1Ban-001`.
- The input should be `sim.mu2e.TargetStops.Run1Ban-001.art` (Run1Ban-self-produced), not the Run1Baa1 leftover.

The corrected entries (verified in file as of 2026-06-07):

```json
{
  "desc": "TargetStopsCat",
  "dsconf": "Run1Ban-001",
  "input_data": {"sim.mu2e.TargetStops.Run1Ban-001.art": 2500},
  "fcl": "Production/JobConfig/common/artcat.fcl",
  "inloc": "disk",
  "fcl_overrides": {
    "outputs.out.fileName": "sim.owner.TargetStopsCat.version.sequence.art"
  },
  "outloc": {"*.art": "tape"},
  "simjob_setup": "/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/Run1Ban/setup.sh"
},
{
  "desc": "MuonStopSelector",
  "dsconf": "Run1Ban",
  "input_data": {"sim.mu2e.TargetStopsCat.Run1Ban-001.art": 1},
  "fcl": "Production/JobConfig/pileup/MuonStopSelector.fcl",
  "inloc": "tape",
  "outloc": {"*.art": "tape"},
  "simjob_setup": "/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/Run1Ban/setup.sh"
}
```

## Entities Touched

- [[run1ban-campaign]] — new Run1Ban campaign page (sibling of [[run1bak-campaign]]; same `v40` geometry but a separate musing release with its own dsconf series).
- [[2026-05-19-run1bak-resampler-additions]] — sister field-off campaign at Run1Bak (also `v40` + DS-off). Run1Ban differs in that it builds a self-contained MuminusStopsCat instead of reusing upstream Run1Baa stops.

## Relation to Other Wiki Pages

- [[json2jobdef-staging-workflow]] — entry shapes and dsconf flow that the new merge_filter entries conform to. Reinforces the "merge_filter.json holds artcat + selector entries that bridge resampler side outputs into downstream chains" usage pattern.
- [[run1bak-campaign]] — Run1Bak is the prior +10-cadence field-off campaign and **reused** upstream `MuminusStopsCat.Run1Baa.art`. The Run1Ban work makes the opposite choice: self-contained rebuild rather than reuse. The two campaigns live side by side at run 1470 with different musings.
- [[digi-output-stream-by-fcl]] — related multi-output-fcl pattern at the digi stage. This decision extends the same theme at the resampler stage: a single fcl can emit many independently-named outputs, and downstream entries should consume the appropriate side stream rather than spinning up a parallel producer.

## EleBeam / MuBeam reuse is safe — collected at TS3, not at DS

A back-and-forth during the 2026-06-07 push asked whether `EleBeamCat.Run1Bai` / `MuBeamCat.Run1Bai` need a Run1Ban rebuild before being used as seeds for `EleBeamFlash@Run1Ban-001` / `MuBeamFlash@Run1Ban-001`. The answer is **no**, but the reasoning depends on a non-obvious cut-tree override.

Tracing the actual collection point:

- The base `Production/JobConfig/beam/POT.fcl` sets `Mu2eG4CommonCut = union[deltaElectrons, Beam.DetectorRegionCuts]`, and base `DetectorRegionCuts` (`prolog.fcl`) writes `Beam` when a charged particle enters `inVolume DS2Vacuum`.
- BUT `epilog_1b.fcl` patches the cut tree in two places:
  ```
  pars[1].pars[2].pars:                  [ TS2Vacuum, Coll31, Coll32, ... ]    # removes TS3/TS4/TS5 Vacuum from kill list
  pars[1].pars[3].pars[0].pars[0].pars:  [ TS3Vacuum ]                          # replaces inVolume[DS2Vacuum] with inVolume[TS3Vacuum]
  ```
- So under Run1B, `Beam.*` is actually written **at TS3Vacuum entry**, not at DS2Vacuum.
- `BeamSplitter.fcl` is `ParticleCodeFilter` only — no G4 stepping, just event-level mu± vs not-mu± split of the already-written `Beam` collection. So `EleBeamCat`/`MuBeamCat` inherit the TS3 collection point.

Therefore `EleBeamCat.Run1Bai` and `MuBeamCat.Run1Bai` are collected upstream of any DS geometry. v06 vs v40 differences are DS-region; the TS region (and the kill-list / write-volume in `epilog_1b.fcl`) are identical between Run1Bai and Run1Ban musings. **Reuse is safe.** The same reasoning extends to `Neutrals.MDC2025ae3` (Neutrals are collected outside the kill region as a default-true clause, also upstream of DS).

This is in contrast to `MuminusStopsCat`, which is genuinely stopped particles at the stopping target inside the DS — those DO require a Run1Ban rebuild (this whole page).

## Production push status (2026-06-07)

All three Run1Ban-001 stage-A producers pushed to `MDC2025-029.json` (15000 jobs total, 85000 headroom):

- `cnf.mu2e.MuBeamFlash.Run1Ban-001.0.tar` — 5000 jobs
- `cnf.mu2e.EleBeamFlash.Run1Ban-001.0.tar` — 5000 jobs
- `cnf.mu2e.NeutralsFlash.Run1Ban-001.0.tar` — 5000 jobs

Each smoke-tested locally with `mu2e -c ... --nevts 5` to status 0 before push.

Stage B/C/D (TargetStopsCat → MuonStopSelector → MuStopPileup) remain blocked on `sim.mu2e.TargetStops.Run1Ban-001.art` landing in SAM as the side output of the MuBeamFlash grid jobs.

## Open Questions

- **Run-number convention.** Run1Bak and Run1Ban both use `run: 1470`. They differ only by musing release (and therefore by which Offline build / `geom_run1_b_v40.txt` revision is in effect). If both need to coexist in production, do they actually carry distinct run ranges, or is the campaign-letter the only disambiguator? Worth confirming with the Run1B team before pushing.
- **Local smoke for MuStopPileup@Run1Ban-001.** MuBeamFlash/EleBeamFlash/NeutralsFlash were validated against existing upstream Cat inputs. MuStopPileup@Run1Ban-001 cannot be runtime-tested against `MuminusStopsCat.Run1Ban` until the new chain produces it (chicken-and-egg). Pre-prod plan: smoke MuBeamResampler@Run1Ban-001 to confirm TargetStops side output, then incrementally validate TargetStopsCat → MuonStopSelector → MuStopPileup.

## Downstream consumers

`MuminusStopsCat.Run1Ban` is the input for the Run1Ban-001 primary
entries; see [[2026-06-14-run1ban-primaries-added]] (CeEndpoint,
FlateMinus, FlatGamma, NoPrimary).
