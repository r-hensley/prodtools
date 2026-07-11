# Source: MDC2025ap RPCExternal chain addition

**Captured:** 2026-05-22
**Type:** in-session decision, branch `field-off-option`
**Edited file:** `data/mdc2025/resampler_beam.json`

## Trigger

User question: "Do we have any RPCExternal dts datasets?" surfaced
that MDC2025 production carries `RPCExternalPhysical` /
`RPCInternalPhysical` (using `sim.mu2e.PhysicalPionStops.MDC2025ac.art`)
but no non-Physical (flat-time) `RPCExternal` analog of
`dts.mu2e.RPCExternal.MDC2020aw.art`.

## Chain comparison (MDC2020aw → MDC2025)

| stage | MDC2020aw artifact | MDC2025 artifact | status pre-edit |
|-------|--------------------|------------------|------------------|
| upstream sim | sim.mu2e.PiTargetStops.MDC2020aw.art | sim.mu2e.PiTargetStops.MDC2025ac.art | both in SAM |
| PreFilter (`TargetPiStopPreFilter.fcl`) | sim.mu2e.PiTargetFilt.MDC2020aw.art | sim.mu2e.PiMinusFilter.MDC2025ac.art | both in SAM (renamed in MDC2025) |
| primary (`RPCExternal.fcl`) | dts.mu2e.RPCExternal.MDC2020aw.art | (missing) | gap |

Confirmed via `fcldump --dataset` on both MDC2020aw stages:
- PiTargetFilt cnf reads PiTargetStops → writes
  `sim.mu2e.PiTargetFilt.MDC2020aw.001202_*.art`
- RPCExternal cnf reads PiTargetFilt → writes
  `dts.mu2e.RPCExternal.MDC2020aw.001202_*.art`,
  carries `MaxEventsToSkip: 87570` and `bfgeom_no_tsu_ps_v01.txt`.

## Entry added

```json
{
    "desc": "RPCExternal",
    "dsconf": "MDC2025ap",
    "fcl": "Production/JobConfig/primary/RPCExternal.fcl",
    "fcl_overrides": {
        "services.GeometryService.bFieldFile": "Offline/Mu2eG4/geom/bfgeom_no_tsu_ps_v01.txt"
    },
    "resampler_name": "TargetPiStopResampler",
    "input_data": {"sim.mu2e.PiMinusFilter.MDC2025ac.art": 1},
    "njobs": 5000,
    "events": 1000000,
    "run": 1430,
    "inloc": "disk",
    "outloc": {"*.art": "disk"},
    "simjob_setup": "/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/MDC2025ap/setup.sh",
    "owner": "mu2e",
    "sequential_aux": true
}
```

Mirrors the existing `RPCExternalPhysical` entry (index 8) with three
swaps: fcl, input dataset, dsconf/simjob bumped to MDC2025ap.

## Geometry note

`bfgeom_no_tsu_ps_v01.txt` zeros only the TS-upstream and PS B-fields
(consistent with the MDC2020aw RPCExternal cnf and the existing
`RPCPhysicalStops` entry in the same file). It is NOT the same as
`bfgeom_DSOff.txt` used by the Run1Bak field-off entries — those
zero the Detector Solenoid field. Despite the `field-off-option`
branch name, this entry carries the partial-PS-off geometry, not
full field-off.

## Why MDC2025ap (not MDC2025af like the Physical entries)

Per the "latest SimJob in new entries" feedback memory: new
`data/<campaign>/*.json` entries should target the latest SimJob
release. MDC2025ap is current. Existing `RPCExternalPhysical` entries
at MDC2025af are not rewritten (forward-only convention).

## Out of scope

- MDC2025ap reco/digi/mix/ntuple entries consuming
  `dts.mu2e.RPCExternal.MDC2025ap.art` (downstream chain).
- Local smoke test against PiMinusFilter input.
- Run1Bak pion variants (still deferred per
  2026-05-19-run1bak-resampler-additions follow-ups).
