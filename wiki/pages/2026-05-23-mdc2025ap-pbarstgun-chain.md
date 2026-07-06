---
title: MDC2025ap PbarSTGun chain (2025-era remake of MDC2020ar)
tags: [decision, mdc2025, pbar, chain]
sources: [famtree dts.mu2e.PbarSTGun.MDC2020ar.art, in-session edit 2026-05-23]
updated: 2026-05-23
---

# MDC2025ap PbarSTGun chain (2025-era remake of MDC2020ar)

**Source:** in-session work 2026-05-23 on branch `field-off-option`;
modified `data/mdc2025/stage1.json` and `data/mdc2025/resampler_beam.json`
**Date:** 2026-05-23
**Type:** decision

## Summary

Rebuilt the antiproton stopping-target chain that 2020 published as
`dts.mu2e.PbarSTGun.MDC2020ar.art`. Pre-edit, the MDC2025 era had
**zero** Pbar artifacts in SAM — `samweb list-files` returned 0 hits
for every desc/dsconf combination tried (`PbarSTGun`, `PbarResampling`,
`PbarSTGunStops`, `stoppedSimpleAntiprotons`). The 2020 chain was
also absent from `prodtools/data/` — it predated this repo or was
wired manually, so this is the first time the chain appears as a
prodtools staging entry.

## 2020 vs 2025 fcl naming (renamed in MDC2025)

The physics is unchanged (the `pbar/PbarSTGunStops.fcl` in
`MDC2020ar` and `MDC2025ap` musings are byte-identical), but the
output descs were renamed:

| Stage | 2020 fcl                                | 2020 output desc                      | 2025 fcl                                | 2025 output desc          |
|-------|-----------------------------------------|---------------------------------------|-----------------------------------------|---------------------------|
| 0 sim | `pbar/PbarSTGunStops.fcl`               | `sim.*.stoppedSimpleAntiprotons.*`    | `pbar/PbarSTGunStops.fcl`               | `sim.*.PbarSTGunStops.*`  |
| 1 dts | (the 2020 chain had a second dts pass)  | `dts.*.PbarSTGun.*`                   | `primary/PbarResampling.fcl`            | `dts.*.PbarResampling.*`  |

So the 2025-era output of the equivalent chain is
`dts.mu2e.PbarResampling.MDC2025ap.art`, NOT
`dts.mu2e.PbarSTGun.MDC2025ap.art`. Decision: follow the fcl
defaults rather than override `outputs.PrimaryOutput.fileName` to
preserve the old desc — the rename was intentional in MDC2025 and
preserving the 2020 string would fight the musing.

## Entry shapes

### Stage 0 — `data/mdc2025/stage1.json`

```json
{
  "desc": "PbarSTGunStops",
  "dsconf": "MDC2025ap",
  "fcl": "Production/JobConfig/pbar/PbarSTGunStops.fcl",
  "njobs": 200, "events": 10000, "run": 1430,
  "outloc": {"*.art": "disk"},
  "simjob_setup": "/cvmfs/.../MDC2025ap/setup.sh",
  "owner": "mu2e"
}
```

Empty-event generator (`SimpleAntiprotonGun`). No `input_data`, no
`resampler_name`. The fcl already sets
`services.GeometryService.bFieldFile: bfgeom_no_tsu_ps_v01.txt` so
no `fcl_overrides` are needed — same inheritance pattern as the
RPC* entries documented in [[2026-05-22-mdc2025ap-rpcexternal-chain]]
and [[reference-rpc-primary-inherits-bfgeom]].

### Stage 1 — `data/mdc2025/resampler_beam.json`

```json
{
  "desc": "PbarResampling",
  "dsconf": "MDC2025ap",
  "fcl": "Production/JobConfig/primary/PbarResampling.fcl",
  "resampler_name": "TargetStopResampler",
  "input_data": {"sim.mu2e.PbarSTGunStops.MDC2025ap.art": 1},
  "njobs": 500, "events": 100000, "run": 1430,
  "inloc": "disk", "outloc": {"*.art": "disk"},
  "simjob_setup": "/cvmfs/.../MDC2025ap/setup.sh",
  "owner": "mu2e", "sequential_aux": true
}
```

Consumes stage 0 via `TargetStopResampler` (matches the resampler
declared in `PbarResampling.fcl`'s `physics.filters` block).

## Sizing rationale (matches 2020 scale, not RPC scale)

- Stage 0: 200 × 10k = 2e6 input events. 2020 sim had 100 files /
  ~10k events each (~1e6 output events post-filter). Doubling
  joins to match modern conventions while keeping a tight footprint.
- Stage 1: 500 × 100k = 5e7 resampled events. 2020 dts had 200
  files / ~640k events; this is ~2.5× larger, still modest.

Both intentionally smaller than the RPC* entries (5000 × 1M) since
the 2020 pbar chain was modest and there's no explicit request to
scale up. Easy to bump `njobs` in place if more stats are needed.

## Validation

Stage 0 local smoke 2026-05-23 (oksuzian, branch `field-off-option`):
- `bin/json2jobdef --json data/mdc2025/stage1.json --desc PbarSTGunStops --dsconf MDC2025ap` → produced `cnf.mu2e.PbarSTGunStops.MDC2025ap.0.tar` clean
- `bin/fcldump --local-jobdef` rendered expected fcl: `firstRun: 1430`, `maxEvents: 10000`, output `sim.mu2e.PbarSTGunStops.MDC2025ap.001430_00000000.art`
- `mu2e -c ... -n 5` exit 0, **5/5 events passed `tgtFilter`** (high acceptance — the antiproton gun is targeted at the stopping target, unlike beam-based stops that filter heavily). CPU 31 s, VmPeak 2.28 GB. Output 94 KB.

Stage 1 validation deferred — cnf build requires stage 0 files in
SAM, which is pending grid completion.

## Production push status

- **Stage 0 (PbarSTGunStops) pushed 2026-05-23 14:16 CDT:** cnf
  declared in SAM, located at
  `/pnfs/mu2e/persistent/datasets/phy-etc/cnf/mu2e/PbarSTGunStops/MDC2025ap/tar/4c/90`.
  Added to `MDC2025-026.json` (now 4 entries: NeutralsFlash.Run1Bak,
  RPCExternal.MDC2025ap, RPCInternal.MDC2025ap, PbarSTGunStops.MDC2025ap;
  15,200 total njobs).
- **Stage 1 (PbarResampling) drafted but NOT pushed.** Blocked
  until 200 stage-0 grid jobs land `sim.mu2e.PbarSTGunStops.MDC2025ap.art`
  in SAM (json2jobdef needs the file count for `MaxEventsToSkip`).
  Resume sequence: wait for grid → re-issue `/mu2epro-run json2jobdef
  --json .../resampler_beam.json --desc PbarResampling --dsconf
  MDC2025ap --prod --jobdefs .../MDC2025-NNN.json`.

## Relation to other wiki pages

- [[2026-05-22-mdc2025ap-rpcexternal-chain]] — sister chain at same
  campaign/musing. Same conventions (no bfgeom override, run=1430,
  MDC2025ap dsconf/simjob, mu2epro push workflow). RPC* and Pbar*
  are independent — they share the musing but not inputs.
- [[reference-rpc-primary-inherits-bfgeom]] — the bfgeom inheritance
  rule applies to Pbar entries too: `PbarSTGunStops.fcl` directly
  sets the field file (line 76 in the musing copy), so no
  `fcl_overrides` block is needed.
- [[json2jobdef-staging-workflow]] — entry shapes used here conform
  to the documented stage1 (empty-event primary) and resampler-beam
  (dts resampling) patterns.

## 2026-05-24 update — stages 0 + 1 both live

- **Stage 0 complete**: `sim.mu2e.PbarSTGunStops.MDC2025ap.art` → 200/200
  files in SAM (matches `njobs: 200`).
- **Stage 1 smoke**: `mu2e -c -n 2` on locally-built
  `cnf.mu2e.PbarResampling.MDC2025ap.0.tar` exited 0 (CPU 33 s,
  VmPeak 2.6 GB). Required a fresh user bearer token (`getToken`
  before `muse setup ops`); without it xrootd reads of stage-0
  `/pnfs/...` files failed with `Auth failed: No protocols left to
  try`. The `mu2e-run` skill was patched to call `getToken` between
  `setupmu2e-art.sh` and `muse setup ops` so future smokes don't hit
  this.
- **Stage 1 prod push**: `json2jobdef --prod --jobdefs .../MDC2025-026.json`
  extended map in place; cnf declared in SAM and copied to
  `/pnfs/mu2e/persistent/datasets/phy-etc/cnf/mu2e/PbarResampling/MDC2025ap/tar/52/bd/`.
  Map MDC2025-026 now 6 entries / 35,700 njobs (added 500 for
  PbarResampling). Index definition `iMDC2025-026` recreated.

## Follow-ups

- If a full antiproton-physics chain is wanted, downstream stages
  (digi/mix/reco/evntuple) for `dts.mu2e.PbarResampling.MDC2025ap.art`
  would be the next additions — but those weren't requested in this
  session.
- Decide whether to also bump sizing (currently modest at 2e6 / 5e7
  events) once initial files exist and statistical needs become
  clearer.
