---
title: Run1Bak campaign
tags: [campaign, run1b]
sources: [2026-05-19-run1bak-resampler-additions, 2026-06-07-run1ban-mustop-rebuild-chain]
updated: 2026-06-07
---

# Run1Bak campaign

## Description

Run1Bak is a Run1B-series simulation campaign keyed on
SimJob musing `Run1Bak` at
`/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/Run1Bak/`. It
introduces geometry version `v40` for the Run1B beam geometry
(`Offline/Mu2eG4/geom/geom_run1_b_v40.txt`) and, in its first
material use here, the **field-off (DS-off) variant** paired with
`bfgeom_DSOff.txt`. A DS-on variant geom file
(`geom_run1_b_ds_on_v40.txt`) ships in the same musing but is not
yet wired into any `data/Run1B/*.json` entry.

The musing also ships:

- `geom_run1_b_v40.txt` — base Run1B v40 geometry (default).
- `geom_run1_b_ds_on_v40.txt` — explicit DS-on counterpart.
- `bfgeom_DSOff.txt` — DS-off bfield overlay (carries over from
  prior Run1B musings; used by all the new entries).

## Run-number convention

Run1Bak entries use **run = 1470**. This continues the +10-per-letter
cadence used by earlier Run1B campaigns:

| Campaign | Geom | Run |
|---|---|---|
| Run1Baa  | v01 | 1440 |
| Run1Bah  | v03 | 1450 |
| Run1Bai  | v06 | 1460 |
| Run1Bak  | v40 | 1470 |

New entries added under Run1Bak should keep `run: 1470` unless there
is a specific reason to diverge.

## Current entries

As of 2026-05-19, Run1Bak has four entries, all in
`data/Run1B/resampler_beam.json`, all field-off:

- `NeutralsFlash` — consumes `sim.mu2e.Neutrals.MDC2025ae3.art`
- `MuBeamFlash`   — consumes `sim.mu2e.MuBeamCat.Run1Baa.art`
- `EleBeamFlash`  — consumes `sim.mu2e.EleBeamCat.Run1Baa.art`
- `MuStopPileup`  — consumes `sim.mu2e.MuminusStopsCat.Run1Baa.art`

All four are additive (originals at Run1Baa / Run1Baa1 preserved);
all four point `input_data` at the **existing upstream Run1B***
outputs rather than at Run1Bak upstream (no Run1Bak upstream chain
exists yet).

## Out of scope (so far)

- **Pion chain.** `PhysicalPionStops` and `RPCExternal` in the same
  `resampler_beam.json` were intentionally not added at Run1Bak.
- **Downstream stages.** `primary_muon.json`, `digi.json`,
  `mix.json`, `reco.json`, `resampler_beam_mixing.json`,
  `stage1.json` carry many more `geom_run1_b_vNN.txt` overrides.
  None has been bumped to v40.
- **DS-on variant.** No entry uses `geom_run1_b_ds_on_v40.txt` yet.

## Appearances in Sources

- [[2026-05-19-run1bak-resampler-additions]] — the additive ingest
  that seeded the campaign.

## Related

- [[run1ban-campaign]] — sister field-off campaign on `Run1Ban`
  musing at the same `v40` geometry / run 1470 slot; opposite
  upstream choice (Run1Ban rebuilds MuminusStopsCat self-contained;
  Run1Bak reuses Run1Baa stops). See
  [[2026-06-07-run1ban-mustop-rebuild-chain]] for the rebuild
  rationale.
- [[json2jobdef-staging-workflow]] — entry-shape and dsconf-flow
  reference; Run1Bak entries follow this model.
- [[prodtools-prd]] — Offline chain context
  (`primary → digi → mix → reco → evntuple`); resampler_beam is a
  stage-1 feeder.
