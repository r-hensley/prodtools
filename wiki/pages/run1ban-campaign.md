---
title: Run1Ban campaign
tags: [campaign, run1b, run1ban]
sources: [2026-06-07-run1ban-mustop-rebuild-chain, 2026-06-14-run1ban-primaries-added, 2026-06-15-run1ban-stm-resampler-port]
updated: 2026-07-03
---

# Run1Ban campaign

## Description

Run1Ban is a Run1B-series simulation campaign keyed on SimJob musing
`Run1Ban` at `/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/Run1Ban/`.
Like its sibling [[run1bak-campaign]], it uses geometry `v40`
(`Offline/Mu2eG4/geom/geom_run1_b_v40.txt`) paired with the field-off
overlay `bfgeom_DSOff.txt`, and run number `1470`. The two campaigns
differ by musing release (and therefore by Offline build / geom-file
revision in effect), not by knob shape.

The defining choice that separates Run1Ban from Run1Bak is **self-contained
upstream regeneration**: Run1Bak reuses `MuminusStopsCat.Run1Baa` as
the resampler source for its MuStopPileup entry; Run1Ban rebuilds
`MuminusStopsCat.Run1Ban` from its own geometry by chaining its
`MuBeamFlash@Run1Ban-001` resampler side output through `artcat` and
`MuonStopSelector`. The rationale is that the older `Run1Bai`
(`v06` geometry) MuminusStopsCat does not propagate the particle
content required by the Run1Ban (`v40`) resamplers — even though
MuonStopSelector itself is geometry-independent, the upstream
TargetStops it filters must come from the matching-geometry
MuBeamResampler.

## Current entries

As of 2026-06-07:

**`data/Run1B/resampler_beam_mixing.json` — Run1Ban-001 (4 entries, all field-off, run 1470)**

- `NeutralsFlash` — `NeutralsResampler.fcl`, consumes `sim.mu2e.Neutrals.MDC2025ae3.art`
- `MuBeamFlash` — `MuBeamResampler.fcl`, consumes `sim.mu2e.MuBeamCat.Run1Bai.art`; emits `MuBeamFlash`, `EarlyMuBeamFlash`, `TargetStops`, `PolyStops`, `IPAStops` as side outputs
- `EleBeamFlash` — `EleBeamResampler.fcl`, consumes `sim.mu2e.EleBeamCat.Run1Bai.art`
- `MuStopPileup` — `MuStopPileup.fcl`, consumes `sim.mu2e.MuminusStopsCat.Run1Ban.art` (produced by the merge_filter chain below; chicken-and-egg until the chain runs)

**`data/Run1B/merge_filter.json` — Run1Ban-001 / Run1Ban (2 entries, the MuminusStopsCat-rebuild chain)**

- `TargetStopsCat@Run1Ban-001` — `artcat.fcl` over 2500 `sim.mu2e.TargetStops.Run1Ban-001.art` files (side output of `MuBeamFlash@Run1Ban-001`), outputs `sim.mu2e.TargetStopsCat.Run1Ban-001.art`
- `MuonStopSelector@Run1Ban` — `MuonStopSelector.fcl` (ParticleCodeFilter on TargetStopFilter); reads `sim.mu2e.TargetStopsCat.Run1Ban-001.art`, emits `sim.mu2e.MuminusStopsCat.Run1Ban.art` (and `MuplusStopsCat.Run1Ban` as a second output stream)

**`data/Run1B/primary_muon.json` — Run1Ban-001 primaries (4 entries, run 1470, geom v40)**

Added 2026-06-14; see [[2026-06-14-run1ban-primaries-added]] for
provenance and divergences from the Run1Bai-001 precedent.

- `CeEndpoint@Run1Ban-001` — CeEndpoint.fcl, 2000 × 1M, resilient→disk
- `FlateMinus@Run1Ban-001` — FlateMinus.fcl, 2000 × 1M (50–110 MeV), resilient→disk
- `FlatGamma@Run1Ban-001` — FlatGamma.fcl, 2000 × 1M (50–110 MeV), resilient→disk
- `NoPrimary@Run1Ban` — NoPrimary.fcl, 20000 × 5000, disk→disk (no resampler input)

All four read `sim.mu2e.MuminusStopsCat.Run1Ban.art` via
`TargetStopResampler` (except NoPrimary, which uses no upstream art
input). Locally smoke-verified 2026-06-14 (mu2e -c --nevts 1 → Art
status 0).

**`data/Run1B/resampler_stm.json` — Run1Ban-001 STM stage (3 entries, run 1470, geom v40)**

Added 2026-06-15; see [[2026-06-15-run1ban-stm-resampler-port]] for
provenance. All three use `BeamTo2VD.fcl` / `BeamTo2VD1809.fcl` and
produce two output streams (VD101 + VD116) per job.

- `STMBeamToVDEle@Run1Ban-001` — BeamTo2VD.fcl, beamResampler, consumes `sim.mu2e.EleBeamCat.Run1Bai.art`, 5000 × 200000, tape→disk
- `STMBeamToVDMu@Run1Ban-001` — BeamTo2VD.fcl, beamResampler, consumes `sim.mu2e.MuBeamCat.Run1Bai.art`, 5000 × 200000, tape→disk
- `STMBeamToVDTarget@Run1Ban-001` — BeamTo2VD1809.fcl, TargetStopResampler, consumes `sim.mu2e.TargetStopsCat.Run1Ban-001.art`, 5000 × 200000, tape→disk

`STMNeutralsToVD` (4th MDC2025ai entry) skipped — no
Run1Ban-named NeutralsCat exists.

## Downstream: mixing → reco → evnt (dsconf `Run1Ban_best_v1_4-000`)

Added 2026-06-28. The downstream chain runs at the mix-build dsconf
`Run1Ban_best_v1_4-000` (not the primary `Run1Ban` dsconf).

**Mixing (`data/Run1B/mix.json`)** — `Mix1BB` (one beam bunch, `OneBB.fcl`).
Signal entry blends five primaries: CeEndpoint, FlateMinus, FlatGamma,
CosmicCRYAll, plus a separate NoPrimary entry. Pushed to the POMS map
`MDC2025-032`. Conditions: `Sim_best/v1_4` with `nearestMatch:true` **and** a
published `textFile` overlay `Production/data/SimEfficiencies2_Run1Ban.txt`
(run 1470 misses 6 `v1_4` tables; the textFile fixes SimEfficiencies2 exactly,
nearestMatch covers TrkPanelStatus + 4 CRV). **Runtime blocker:** the
SimEfficiencies2 table must contain every stage in each mixer's
`simStageEfficiencyTags` chain — the first published file omitted `NeutralsCat`
and crashed `NeutralsFlashMixer` at run 1470 with `Unphysical
SimStageEfficiency value -1`; re-publish with the `NeutralsCat` row before mix
jobs can run.

**Generic reco + evnt cnfs** — both are `generic_tarball` (1:1 direct-input,
no POMS index/njobs), recoing/ntupling any Run1Ban desc from its SAM input:

- **reco**: `cnf.mu2e.reco.Run1Ban_best_v1_4-000.0.tar` (already in SAM),
  fcl `Production/JobConfig/recoMC/NoFieldRun1B.fcl`, output
  `mcs.owner.{desc}-KL...` — the **`-KL`** suffix is `KinematicLineOutput`,
  the straight-line track fit used because the DS field is off
  (`bfgeom_DSOff.txt`). Jobdesc `poms_map/Run1Ban-reco.json`.
- **evnt**: `cnf.mu2e.evnt.Run1Ban_best_v1_4-000.0.tar` (built + pushed
  2026-06-28), fcl `EventNtuple/fcl/from_mcs-Run1B.fcl` (the Run1B
  straight-line ntuple, includes `from_mcs-extracted` + MC branches), via
  `AnalysisMDC2025/v02_00_00`. Jobdesc `poms_map/Run1Ban-evnt.json`. The
  generic evnt **cannot** ntuple `NoPrimary` — its default
  `EventNtupleEndPath` runs `genCountLogger`, which needs a GenEventCount that
  pure-pileup NoPrimary lacks; NoPrimary keeps a dedicated `evntuple.json`
  entry with `physics.EventNtupleEndPath:["EventNtuple"]`.

Chain: mix `dig.*Mix1BB` → reco `mcs.*Mix1BB-KL` → evnt `nts.*Mix1BB-KL`. The
reco/evnt have nothing to process until the Mix1BB jobs run (gated on the
SimEfficiencies2 `NeutralsCat` fix above).

**Update 2026-07-03: the `v1_4` SimEfficiencies2/textFile blocker above is
now avoidable — see the `v1_5` reprocessing below, which needs neither
`textFile` nor `nearestMatch`.** The `v1_4-000` entries stay as documented
(historical/in-production), not rewritten.

## NoPrimaryMix1BB reprocessing at `Run1Ban_best_v1_5-000` (2026-07-03)

A second `NoPrimaryMix1BB` entry, `Run1Ban_best_v1_5-000`, was added
alongside (not replacing) the `v1_4-000` production entry, with three
changes plus one production-tuning change:

- **`services.DbService.version: "v1_5"`, no `nearestMatch`/`textFile`.**
  `Sim_best/v1_5` (committed 2026-06-29) natively covers run 1470 for every
  table that `v1_4` was missing (`SimEfficiencies2`, `TrkPanelStatus`, 4 CRV
  tables) — confirmed via `dbTool verify-set`: 0 missing tables/IoVs. See
  memory `reference_sim_best_v1_4_run_coverage`.
- **`physics.filters.CaloDtsClusterFilter.NullFilter: false`** — the filter
  (inside `Mixing.PileupMixSequence`) now actually applies its
  energy/time/space-window cuts instead of no-op passing everything.
  Measured effect (500-event A/B against `v1_4`, same input files): ~94% of
  candidate pileup calo clusters rejected, output **~9.8x smaller**, job
  **~4x faster**. This is a real physics change to the mixed calorimeter
  pileup content, not just a performance tweak.
- **Along the way, fixed a real bug**: the mixing-stage `fcl_overrides`
  serializer (`utils/mixing_utils.py build_pileup_args`) rendered Python
  booleans as `False`/`True` (invalid FHiCL — needs lowercase), a bug
  affecting any mixing entry with a boolean override; the non-mixing path
  (`write_fcl_template`) was already correct via `json.dumps`. Fixed to
  match. See memory `reference_mixing_bool_override_bug`.
- **Job packaging: merge factor 10** (`input_data`: `{"dts.mu2e.NoPrimary.Run1Ban.art": 10}`)
  — 2000 jobs of 50,000 events each, instead of 20000 jobs of 5,000. This is
  the **first merge-factor>1 use in any `pbeam` mixing entry** across the
  whole repo. Validated via a full unbounded `mu2e -c` run (50000 events,
  exit 0, zero failures across all 4 pileup mixers/filters). The pileup
  file lists (1 MuBeamFlash / 25 EleBeamFlash / 1 Neutrals / 2 MuStopPileup
  files) get exhausted and wrap/reuse repeatedly within a job at this
  scale — confirmed this is pre-existing framework behavior (same warning
  occurs at the current `v1_4` merge=1 scale too), not a new risk. Total
  campaign output/CPU is essentially unchanged from the `v1_4` packaging
  (same 100M total events); merge=10 just trades per-job/file overhead for
  longer per-job wall time (~30 min vs ~3.7 min). See memory
  `reference_mixing_merge_factor_10_validated`.

Pushed to production 2026-07-03: `cnf.mu2e.NoPrimaryMix1BB.Run1Ban_best_v1_5-000.0.tar`,
2000 jobs, extending `MDC2025-032` (32599 → 34599 total).

## dsconf convention

- Side-output Cat keeps the **resampler-job dsconf**: `TargetStopsCat.Run1Ban-001` (matches `MuBeamFlash@Run1Ban-001`).
- The final MuminusStopsCat uses the **campaign dsconf**: `MuminusStopsCat.Run1Ban`.
- This mirrors the Run1Bai precedent (`TargetStopsCat.Run1Bai-003` → `MuminusStopsCat.Run1Bai`).

## Run-number convention

`run: 1470`, sharing the slot with [[run1bak-campaign]]. The
+10-per-letter cadence (Baa=1440, Bah=1450, Bai=1460, Bak=1470)
collapses when two musings share a `v40` geometry slot. Whether this
needs disambiguation in production runs is an open question on the
ingest page.

## Appearances in Sources

- [[2026-06-07-run1ban-mustop-rebuild-chain]] — establishing decision
  and chain shape.
- [[2026-06-14-run1ban-primaries-added]] — Run1Ban-001 primaries (CeEndpoint/FlateMinus/FlatGamma/NoPrimary).
- [[2026-06-15-run1ban-stm-resampler-port]] — 3 STM resampler entries (BeamToVDEle/Mu/Target) ported from MDC2025ai.

## Related

- [[run1bak-campaign]] — sister field-off campaign at the same run
  number; reuses upstream stops instead of rebuilding.
- [[json2jobdef-staging-workflow]] — entry-shape and dsconf-flow
  reference; Run1Ban entries follow this model.
- [[reference-rpc-primary-inherits-bfgeom]] — related fcl-inheritance
  pattern (different chain, same principle: don't override what
  upstream already sets).
