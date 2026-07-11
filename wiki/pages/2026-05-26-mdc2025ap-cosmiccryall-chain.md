---
title: MDC2025ap CosmicCRYAll chain + cosmic-vs-stop divergence
tags: [decision, mdc2025, cosmic, chain, poms-map]
sources: [in-session edit 2026-05-26, S2Resampler.fcl in SimJob/MDC2025ap, primary/prolog.fcl in SimJob/MDC2025ap, Offline v13_14_00]
updated: 2026-05-26
---

# MDC2025ap CosmicCRYAll chain + cosmic-vs-stop divergence

**Source:** in-session work 2026-05-26 on branch `field-off-option`;
modified `data/mdc2025/primary_muon.json`; pushed cnf
`cnf.mu2e.CosmicCRYAll.MDC2025ap.0.tar` as the sole entry in new POMS
map `MDC2025-027.json`.
**Date:** 2026-05-26
**Type:** decision

## Summary

Added the MDC2025ap CosmicCRYAll cosmic-resampling primary, matching
the existing MDC2025ac CosmicCRYAll in sizing (50k jobs × 500k events)
and consuming `sim.mu2e.CosmicDSStopsCRYAll.MDC2025ab.art` upstream.

What makes this entry non-trivial: the cosmic chain
(`Production/JobConfig/cosmic/S2Resampler.fcl`) **does not** inherit
the StopParticle conveniences. It's the first MDC2025ap entry whose
fcl chain is rooted outside `StopParticle.fcl`, so the inheritance
rules documented for the RPC/Pbar primaries do not apply. Three
specific divergences bit during this push and are captured here so the
next cosmic entry doesn't repeat them.

A second lesson — independent of cosmics — surfaced during recovery:
**`outloc` lives in the POMS map, not the cnf.** A wrong-outloc push
is fixed by editing `MDC<campaign>-NNN.json` in place; no SAM
retire / dCache delete / re-push is required.

## Cosmic chain vs StopParticle chain — three divergences

Every prior MDC2025ap primary in this repo (RPC*, Pbar*, Flat*, Ce*,
RMC*, DIO*, IPA*) ultimately includes
`Production/JobConfig/primary/StopParticle.fcl`. CosmicCRYAll
(`S2Resampler.fcl`) does not. The practical consequences:

### 1. `outputs.PrimaryOutput.fileName` is REQUIRED

`primary/prolog.fcl:205` sets `Primary.PrimaryOutput.fileName = @nil`.
StopParticle-chain fcls override this internally before reaching
json2jobdef; `S2Resampler.fcl:29` only re-exports `PrimaryOutput`
without supplying a `fileName`. Consequence:

```
subprocess.CalledProcessError: Command '['fhicl-get', '--atom-as',
  'string', 'outputs.PrimaryOutput.fileName', 'template.fcl']'
  returned non-zero exit status 1.
```

at `json2jobdef`. Fix is an explicit entry override:

```json
"fcl_overrides": {
  "outputs.PrimaryOutput.fileName":
    "dts.owner.CosmicCRYAll.version.sequencer.art"
}
```

`mu2ejobfcl` substitutes the `owner`, `version`, and `sequencer`
placeholders at job time.

### 2. `bFieldFile` is NOT inherited

StopParticle-chain entries inherit `bfgeom_no_tsu_ps_v01.txt` via
`StopParticle.fcl:41` (see [[reference-rpc-primary-inherits-bfgeom]]).
The cosmic chain inherits Offline's default
(`standardServices.fcl:44`) which is the full `bfgeom_v01.txt`
(TS+PS). For cosmic-ray showers that don't traverse the upstream
beamline this is a perf cost, not a physics issue. Override is
**optional**:

```json
"fcl_overrides": {
  "services.GeometryService.bFieldFile":
    "Offline/Mu2eG4/geom/bfgeom_no_tsu_ps_v01.txt"
}
```

CosmicCRYAll MDC2025ap omits this override (matching the minimal
entry pattern) — accept the perf hit for now; revisit if grid CPU
shows up as the bottleneck.

### 3. `inputFile` defaults differ in name but not in target

`S2Resampler.fcl:46` sets
`services.GeometryService.inputFile: Production/JobConfig/cosmic/geom_cosmic.txt`,
which itself includes `Offline/Mu2eG4/geom/geom_common.txt` — and in
v13_14_00, `geom_common.txt` is a redirect to
`geom_run1_a_stickman.txt` (Stickman production target). So the
effective default is Stickman, same as the MDC2025ap RPC/Pbar
entries.

Overriding to `geom_run1_a.txt` would pin the older Hayman target
(physics-equivalent for muon-stop downstream physics). The MDC2025ac
CosmicCRYAll override is the Hayman variant; CosmicCRYAll MDC2025ap
**inherits Stickman** — same Hayman/Stickman acceptable split as
documented for the ap-only RPC/Pbar family in
`reference_run1_geom_overrides_in_mdc2025_primaries.md`.

## Entry shape — `data/mdc2025/primary_muon.json`

```json
{
  "desc": "CosmicCRYAll",
  "dsconf": "MDC2025ap",
  "fcl": "Production/JobConfig/cosmic/S2Resampler.fcl",
  "fcl_overrides": {
    "outputs.PrimaryOutput.fileName":
      "dts.owner.CosmicCRYAll.version.sequencer.art"
  },
  "resampler_name": "CosmicResampler",
  "input_data": {"sim.mu2e.CosmicDSStopsCRYAll.MDC2025ab.art": 1},
  "njobs": 50000,
  "events": 500000,
  "run": 1430,
  "simjob_setup":
    "/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/MDC2025ap/setup.sh",
  "owner": "mu2e",
  "inloc": "disk",
  "outloc": {"*.art": "tape"},
  "sequential_aux": true
}
```

`resampler_name: "CosmicResampler"` matches the resampler module
declared in `S2Resampler.fcl`.

## Sizing rationale

50k × 500k = 2.5e10 cosmic events. Matches the MDC2025ac CosmicCRYAll
entry directly — same physics, same statistical ask, no reason to
rescale on the ap musing. This is by far the largest single entry
across all 12 MDC2025ap primaries pushed this session (next-largest:
ExtractedCRY 20k jobs).

## Input residency caveat

`sim.mu2e.CosmicDSStopsCRYAll.MDC2025ab.art` (20k files) is on
`/pnfs/mu2e/tape`:

| State | Count | % |
|---|---|---|
| ONLINE_AND_NEARLINE (disk+tape) | 11,270 | 56% |
| NEARLINE (tape only) | 8,730 | 44% |

Entry tags `inloc: disk` but 44% of files are not on disk at submission
time. Before launching the 50k-job batch through POMS, either:
- prestage with `/prestage sim.mu2e.CosmicDSStopsCRYAll.MDC2025ab.art`
  (pins disk for 14 days; 20k files is well under the 100k/day cap), or
- flip `inloc` to `tape` if submit_map routes the read differently for
  tape (verify before flipping).

As of 2026-05-26 the dataset is not fully staged; submission would
either fail xrootd reads or run slowly until enstore catches up.

## Production push status

- Cnf `cnf.mu2e.CosmicCRYAll.MDC2025ap.0.tar` pushed 2026-05-26 via
  `/mu2epro-run MDC2025ap json2jobdef --prod --json
  data/mdc2025/primary_muon.json --desc CosmicCRYAll --dsconf
  MDC2025ap --jobdefs .../MDC2025-027.json`.
- Allocated as the sole entry in new POMS map
  `MDC2025-027.json` (njobs=50000); `MDC2025-026.json` was already at
  66,700 njobs across 17 entries and adding 50k would have exceeded
  the 100k cap.
- First push landed with `outloc=disk` in the map. Corrected to
  `tape` via in-place edit of `MDC2025-027.json` (see below) — no
  SAM/dCache mutation needed.

## outloc-recovery procedure (not cosmic-specific)

`outloc` is read from the POMS map at submission time by `submit_map`
and routes per-job `pushOutput`. The cnf
(`cnf.mu2e.<desc>.<dsconf>.0.tar`) carries only the fcl template and
job metadata — it is `outloc`-agnostic. So a wrong-outloc-after-push
is a metadata-only fix:

```bash
ksu mu2epro -e /bin/bash -c '
python3 -c "
import json
p=\"/exp/mu2e/app/users/mu2epro/production_manager/poms_map/MDC2025-027.json\"
d=json.load(open(p))
for e in d:
    if \"CosmicCRYAll\" in e.get(\"tarball\",\"\"):
        for o in e.get(\"outputs\",[]):
            if o.get(\"location\")==\"disk\":
                o[\"location\"]=\"tape\"
json.dump(d, open(p,\"w\"), indent=4)
"
'
```

No need to retire the cnf from SAM, gfal-rm the cnf from dCache,
delete the SAM definition, or re-run `json2jobdef --prod`.

**Schema gotcha.** The source `data/<campaign>/*.json` shape uses
`"outloc": {"*.art": "disk"}` (dict). The POMS map entry uses
`"outputs": [{"dataset": "*.art", "location": "disk"}]` (list of
dicts). `json2jobdef` does the transformation when it writes the map.
First-time fix attempt this session used the source-side schema on
the map and silently no-op'd — keep the two shapes straight when
editing the map directly.

## Relation to other wiki pages

- [[2026-05-22-mdc2025ap-rpcexternal-chain]] and
  [[2026-05-23-mdc2025ap-pbarstgun-chain]] — sister MDC2025ap chains.
  Both root in `StopParticle.fcl` and inherit `bfgeom_no_tsu_ps_v01.txt`
  / a valid `PrimaryOutput.fileName`. CosmicCRYAll is the first
  MDC2025ap entry that diverges from those conventions — the
  divergence section above is the diff vs those pages' inheritance
  story.
- [[reference-rpc-primary-inherits-bfgeom]] — explicitly does NOT
  apply to cosmic chains. This page is the counterexample.
- [[json2jobdef-staging-workflow]] — the resampler-beam entry shape
  (input_data + resampler_name + sequential_aux) is reused here; only
  the fcl-override block differs.

## Follow-ups

- Decide on prestaging vs `inloc` flip before submitting through POMS
  (see "Input residency caveat" above).
- If a downstream digi/mix/reco chain for `dts.mu2e.CosmicCRYAll.MDC2025ap.art`
  is wanted, sibling entries would be added to `data/mdc2025/reco.json`
  etc. — not requested this session.
- Promote the `outloc` recovery procedure to a separate ops page if
  it gets reused; for now it's documented here and in memory
  (`reference_outloc_lives_in_poms_map_not_cnf.md`).
