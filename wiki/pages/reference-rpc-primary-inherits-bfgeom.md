---
title: Primary stop fcls inherit bfgeom_no_tsu_ps_v01.txt
tags: [reference, fcl, geometry, rpc, pbar, mdc2025]
sources: []
updated: 2026-05-23
---

# Primary stop fcls inherit bfgeom_no_tsu_ps_v01.txt

**Rule:** Do not add `services.GeometryService.bFieldFile:
"Offline/Mu2eG4/geom/bfgeom_no_tsu_ps_v01.txt"` as an
`fcl_overrides` block on RPC* / Pbar* / TargetStop primary entries
in `data/<campaign>/*.json`. The include chain already sets it.

## Include chain (MDC2025ap example)

```
Production/JobConfig/primary/RPCExternal.fcl
  → Production/JobConfig/primary/RPC.fcl
    → Production/JobConfig/primary/TargetPiStopParticle.fcl
      → Production/JobConfig/primary/StopParticle.fcl
        line 41: services.GeometryService.bFieldFile :
                 "Offline/Mu2eG4/geom/bfgeom_no_tsu_ps_v01.txt"
```

Same chain applies to:
- `RPCExternal.fcl`, `RPCInternal.fcl`, `RPCExternalPhysical.fcl`,
  `RPCInternalPhysical.fcl` (via `RPC.fcl`).
- `pbar/PbarSTGunStops.fcl` (sets the field file directly on its
  own line — verified in MDC2025ap musing).
- `PbarResampling.fcl` (sets it via the same TargetStop chain).

## Why the rule exists

Repeated overrides in `fcl_overrides` are dead code: they restate
what the fcl already sets. They:
- bloat staging-config JSON (`data/mdc2025/resampler_beam.json` is
  already busy)
- mask the inheritance relationship from readers
- create a maintenance trap: if the musing changes its default
  field file, the JSON override silently keeps the old value

## How to apply

When adding a new entry to `data/<campaign>/*.json` for any primary
stop chain (RPC*, Pbar*, TargetStop*), grep the fcl include chain
for `bFieldFile`. If it's already set, leave `fcl_overrides`
without the bfgeom line (or omit the block entirely). Only add it
when the fcl does NOT inherit a field file or when you intentionally
need a different one (e.g., `bfgeom_DSOff.txt` for Run1Bak field-off
work — see [[2026-05-19-run1bak-resampler-additions]]).

## Related

- [[2026-05-22-mdc2025ap-rpcexternal-chain]] — first decision page
  where this inheritance was made explicit (RPCExternal +
  RPCInternal entries).
- [[2026-05-23-mdc2025ap-pbarstgun-chain]] — applied the same rule
  to PbarSTGunStops and PbarResampling entries.
- [[json2jobdef-staging-workflow]] — broader workflow context for
  `fcl_overrides` placement.
