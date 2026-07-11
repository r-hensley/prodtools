---
title: Run1Bak resampler_beam additions (DS-off, v40 geom)
tags: [campaign, decision, run1b]
sources: [2026-05-19-run1bak-resampler-additions]
updated: 2026-05-19
---

# Run1Bak resampler_beam additions (DS-off, v40 geom)

**Source:** in-session edit 2026-05-19 on branch `field-off-option`; modified `data/Run1B/resampler_beam.json`
**Date ingested:** 2026-05-19
**Type:** decision

## Summary

Appended four new entries to `data/Run1B/resampler_beam.json`
(NeutralsFlash, MuBeamFlash, EleBeamFlash, MuStopPileup) under
dsconf `Run1Bak`, pointing at the new geometry
`Offline/Mu2eG4/geom/geom_run1_b_v40.txt` paired with
`bfgeom_DSOff.txt` (field-off). Run number bumped to `1470`,
extending the per-campaign-letter cadence (Baa=1440 → Bah=1450 →
Bai=1460 → Bak=1470). `simjob_setup` set to
`/cvmfs/.../Musings/SimJob/Run1Bak/setup.sh`.

The originals (Run1Baa / Run1Baa1 at `geom_run1_b_v01.txt`,
run 1440) are **preserved** — the four Run1Bak entries are
appended alongside, not replacing. This keeps existing
downstream consumers of `sim.mu2e.{Neutrals,MuBeamCat,
EleBeamCat,MuminusStopsCat}.Run1Baa*.art` valid while a parallel
Run1Bak field-off chain is built up.

Pion-chain entries in the same file (`PhysicalPionStops`,
`RPCExternal`) were intentionally **excluded** — pions are not part of
this remake. Other non-geom-override entries
(`PiMinusFilter`, `RPCInternalPhysical`, `RPCExternalPhysical`,
`PiTargetStops`, `NeutralsFlashCat`) were left untouched.

## Key Takeaways

- Additive pattern: new dsconf appended; originals kept; no in-place
  mutation. Avoids invalidating in-flight production of Run1Baa
  outputs.
- DS-off variant chosen on `field-off-option` branch. The Run1Bak
  musing ships both `geom_run1_b_v40.txt` (default) and
  `geom_run1_b_ds_on_v40.txt`; only the DS-off pairing (default geom
  + explicit `bfgeom_DSOff.txt`) was added.
- Run-number cadence: campaigns advance by 10 per letter
  (Baa=1440, Bah=1450, Bai=1460, Bak=1470). New campaign entries
  should follow this convention.
- `input_data` refs were **not** rewired — the new Run1Bak resampler
  entries still consume upstream `MDC2025ae3` / `Run1Baa` outputs.
  A fully-independent Run1Bak chain would require remaking the
  upstream `sim.mu2e.*.Run1Baa*.art` inputs at Run1Bak first.
- Scope restricted to `resampler_beam.json` — other Run1B files
  (`stage1.json`, `primary_muon.json`, `digi.json`, `mix.json`,
  `reco.json`, `resampler_beam_mixing.json`, etc.) have many more
  geom overrides; those bumps are deferred.

## Entities Touched

- [[run1bak-campaign]] — new campaign page seeded by this ingest.

## Relation to Other Wiki Pages

- [[json2jobdef-staging-workflow]] — the staging-config model that
  the resampler_beam.json edits conform to. Entry shape (dsconf, fcl,
  fcl_overrides, input_data, simjob_setup, outloc, sequential_aux)
  matches the patterns documented there for resampler stages.
- [[prodtools-prd]] — the Offline chain
  (`primary → digi → mix → reco → evntuple`) referenced in the PRD
  has resampler_beam as a stage-1 feeder; this ingest is a
  campaign-bump within that chain, not a structural change.

## Validation

- Local smoke (`mu2e -c cnf.mu2e.NeutralsFlash.Run1Bak.0.fcl -n 5`)
  against the real xroot input
  `sim.mu2e.Neutrals.MDC2025ae3.001430_00000001.art` completed with
  status 0 (CPU 29 s, VmPeak 2.5 GB). All 5 events were filtered
  out by `EarlyPrescaleFilter` / `DetStepFilter` — expected prescale
  behavior, not an error. Confirms `geom_run1_b_v40.txt` +
  `bfgeom_DSOff.txt` load cleanly under the `Run1Bak` SimJob and that
  the resampler reads the upstream `MDC2025ae3` source through
  xrootd. Token requirement: oksuzian bearer token at
  `/run/user/<uid>/bt_u<uid>` (refreshed via `htgettoken -a
  htvaultprod.fnal.gov -i mu2e`).
- 1-event local smoke (`mu2e -c ... -n 1`) fails with `Mu2eG4::endSubRun()
  Error: inconsistent simStage: 1 vs 0` for both the new Run1Bak
  entries **and** the production-validated Run1Baa originals. This is
  a pre-existing local-smoke artifact of the resampler stage with a
  too-small event budget, not a Run1Bak regression — use `-n 5` or
  larger when smoking resampler fcls locally.
- The other three Run1Bak entries (MuBeamFlash, EleBeamFlash,
  MuStopPileup) were **not** runtime-validated against xroot input as
  of this writing; only NeutralsFlash was. They should pass by the
  same logic (identical override pattern, same musing), but a real
  test before production push is advisable.

## Follow-ups

- If the field-off remake needs a fully-independent chain, the
  upstream `MuBeamCat`, `EleBeamCat`, `MuminusStopsCat`, and
  `Neutrals` datasets must be regenerated at Run1Bak first, then
  the `input_data` refs in these four entries repointed.
- Downstream stages (`primary_muon.json`, `digi.json`, `mix.json`,
  `reco.json`, `resampler_beam_mixing.json`) carry many more
  `geom_run1_b_vNN.txt` overrides. A full Run1Bak chain would
  cascade through all of them with dsconf renames
  (`Run1Bak_best_v1_N`) and input_data rewires.
- Pion entries (PhysicalPionStops, RPCExternal) are out of scope
  here; if/when a pion field-off variant is needed, append
  separately following the same additive pattern.
