---
title: MDC2025ap RPCExternal chain (non-Physical RPC at MDC2025)
tags: [decision, mdc2025, rpc, chain]
sources: [2026-05-22-mdc2025ap-rpcexternal-chain]
updated: 2026-05-23
---

# MDC2025ap RPCExternal chain (non-Physical RPC at MDC2025)

**Source:** in-session edit 2026-05-22 on branch `field-off-option`; modified `data/mdc2025/resampler_beam.json`
**Date ingested:** 2026-05-22
**Type:** decision

## Summary

Added a single `RPCExternal` entry to `data/mdc2025/resampler_beam.json`
to produce `dts.mu2e.RPCExternal.MDC2025ap.art` — the MDC2025 analog of
`dts.mu2e.RPCExternal.MDC2020aw.art`. Pre-edit, MDC2025 production
shipped only the *Physical* RPC variants (`RPCExternalPhysical`,
`RPCInternalPhysical`) consuming `sim.mu2e.PhysicalPionStops.MDC2025ac.art`;
the non-Physical (flat-time) RPCExternal had no MDC2025 counterpart.

The full chain was already in place except for the final stage:
`sim.mu2e.PiTargetStops.MDC2025ac.art` → `TargetPiStopPreFilter.fcl` →
`sim.mu2e.PiMinusFilter.MDC2025ac.art` (both registered in SAM). The
new entry plugs `RPCExternal.fcl` onto `PiMinusFilter.MDC2025ac` and
writes `dts.mu2e.RPCExternal.MDC2025ap.art`. Mirrors the existing
`RPCExternalPhysical` shape (5000 jobs × 1M events, disk/disk,
`sequential_aux`, `TargetPiStopResampler`) with three swaps: fcl,
input dataset, dsconf/simjob bumped to MDC2025ap.

Uses `bfgeom_no_tsu_ps_v01.txt` (TS-upstream + PS field zeroed),
inherited via `RPCExternal.fcl` → `RPC.fcl` →
`TargetPiStopParticle.fcl` → `StopParticle.fcl` — no `fcl_overrides`
needed (an earlier draft carried a redundant override; dropped
2026-05-23). This matches the MDC2020aw RPCExternal cnf and the
existing `RPCPhysicalStops` entry in the same file — but is **not**
the same as `bfgeom_DSOff.txt` used by the Run1Bak entries. Despite
the `field-off-option` branch name, this entry is partial-PS-off,
not full field-off.

## Key Takeaways

- **MDC2025 renamed `PiTargetFilt` → `PiMinusFilter`.** Same
  `TargetPiStopPreFilter.fcl`, just a desc rename. Not obvious from
  the names; future "where's the MDC2025 PiTargetFilt?" questions
  should look for PiMinusFilter.
- **The non-Physical RPCExternal chain was a gap, not a deletion.**
  MDC2025 production intentionally moved to the Physical variants
  (true pion time distribution) but didn't drop the underlying fcl
  (`RPCExternal.fcl` still ships in MDC2025ap musing). Adding the
  entry is purely additive.
- **dsconf-vs-simjob convention for new entries:** existing
  RPC*Physical entries pin MDC2025af; the new entry pins MDC2025ap
  (latest at time of writing). Per the "latest SimJob in new
  entries" feedback rule, forward-only — older entries are not
  rewritten.
- **Geometry rabbit hole:** three field-related geom files now live
  in MDC2025 entries — default (full field), `bfgeom_no_tsu_ps_v01.txt`
  (PS+TSu zeroed), and `bfgeom_DSOff.txt` (DS off, used in
  `data/Run1B/resampler_beam.json` Run1Bak entries). The latter two
  are NOT interchangeable.
- **No downstream entries yet.** Producing `dts.mu2e.RPCExternal.MDC2025ap.art`
  is one step; making it useful requires matching digi/mix/reco/ntuple
  stages at MDC2025ap, which were not added in this edit.

## Entities Touched

- (this is the first MDC2025 chain-extension page; no campaign page exists yet for MDC2025ap)

## Relation to Other Wiki Pages

- [[json2jobdef-staging-workflow]] — the staging-config model
  this edit conforms to. Entry shape matches the patterns documented
  there for primary-stage resampler entries.
- [[2026-05-19-run1bak-resampler-additions]] — that page explicitly
  deferred pion entries (PhysicalPionStops, RPCExternal) as
  out-of-scope for the Run1Bak field-off remake. This ingest fills the
  *MDC2025ap* side of that gap, not the Run1Bak side; Run1Bak pion
  entries remain deferred.
- [[prodtools-prd]] — the Offline chain primary → digi → mix → reco
  → evntuple referenced in the PRD has resampler_beam as the
  primary-stage feeder; this edit is a campaign-bump within that
  chain, not a structural change.

## Validation

Local smoke 2026-05-23 (oksuzian, branch `field-off-option`):

1. **cnf build** via `/stage-entry resampler_beam --simjob-version MDC2025ap
   --desc RPCExternal --dsconf MDC2025ap` → produced
   `cnf.mu2e.RPCExternal.MDC2025ap.0.tar` clean.
2. **fcldump --local-jobdef** on the cnf rendered the expected fcl:
   includes `RPCExternal.fcl`, applies `bfgeom_no_tsu_ps_v01.txt`
   override, `MaxEventsToSkip: 132689` (auto-derived from the
   `PiMinusFilter.MDC2025ac` dataset size), resampler input
   `sim.mu2e.PiMinusFilter.MDC2025ac.001430_00000005.art` (xroot,
   tape), output `dts.mu2e.RPCExternal.MDC2025ap.001430_00000000.art`,
   `firstRun: 1430`, `baseSeed: 1`.
3. **mu2e -c ... -n 5** completed status 0. CPU 33 s, VmPeak 2.57 GB.
   All 5 events were filtered out by `PrimaryFilter` — expected
   prescale behavior at low statistics (matches the Run1Bak page's
   `-n ≥ 5` rule for resampler stages; the
   `Mu2eG4::endSubRun() inconsistent simStage` artifact did not
   trigger).

Token: refreshed via `htgettoken -a htvaultprod.fnal.gov -i mu2e
--nooidc` (kerberos non-interactive path), stored at
`/run/user/<uid>/bt_u<uid>`.

Confirms: the entry is wireable end-to-end; MDC2025ap musing + the
non-Physical `RPCExternal.fcl` + the `PiMinusFilter.MDC2025ac` input
all compose cleanly.

**Production push completed 2026-05-23 11:23 CDT** (mu2epro via
`/mu2epro-run json2jobdef --prod`):
- cnf `cnf.mu2e.RPCExternal.MDC2025ap.0.tar` declared in SAM,
  located at `/pnfs/mu2e/persistent/datasets/phy-etc/cnf/mu2e/RPCExternal/MDC2025ap/tar/e8/0b`
- Extended `/exp/mu2e/app/users/mu2epro/production_manager/poms_map/MDC2025-026.json`
  (pre-existing 5000-job `NeutralsFlash.Run1Bak` entry; total now
  10,000 jobs, well under 100k cap)
- Index definition `iMDC2025-026` recreated covering both entries
- `pushOutput` exit 0, single redundant `bFieldFile` override removed
  before push (inheritance noted in [[reference-rpc-primary-inherits-bfgeom]])

## RPCInternal companion entry (2026-05-23)

Added a parallel `RPCInternal` entry in the same file, identical
shape to `RPCExternal` (same `PiMinusFilter.MDC2025ac` input, same
`TargetPiStopResampler`, same 5000×1M, same MDC2025ap dsconf/simjob).
The only fcl difference upstream is `RPCType: "mu2eInternalRPC"` vs
`"mu2eExternalRPC"` and the output filename token. Include chain is
identical — `RPCInternal.fcl` → `RPC.fcl` → `TargetPiStopParticle.fcl`
→ `StopParticle.fcl` — so the bfgeom inheritance discussion above
applies unchanged. No `fcl_overrides` needed.

**Production push completed 2026-05-23 12:00 CDT** (same workflow
as RPCExternal, ~37 min later):
- cnf `cnf.mu2e.RPCInternal.MDC2025ap.0.tar` declared in SAM,
  located at `/pnfs/mu2e/persistent/datasets/phy-etc/cnf/mu2e/RPCInternal/MDC2025ap/tar/34/77`
- `MDC2025-026.json` now holds 3 entries (NeutralsFlash.Run1Bak,
  RPCExternal.MDC2025ap, RPCInternal.MDC2025ap) totaling 15,000
  jobs
- Index definition `iMDC2025-026` recreated
- `pushOutput` exit 0

## Follow-ups

- Add downstream MDC2025ap entries (digi.json, mix.json, reco.json,
  evntuple.json) consuming `dts.mu2e.RPCExternal.MDC2025ap.art` and
  `dts.mu2e.RPCInternal.MDC2025ap.art` if a full chain is wanted.
- If the partial-field geom is not the intent, drop the inherited
  setting at the fcl level or swap to `bfgeom_DSOff.txt` (full
  field-off, matching Run1Bak choice).
