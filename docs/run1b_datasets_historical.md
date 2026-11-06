# Run1B datasets — historical NTS generations

Use the [current catalog](run1b_datasets_current.md) for the
`Run1B-013/-014/-015` EventNtuple generation, current parent coverage, and the
DIGI/MCS source and normalization provenance shared by these samples.

This page preserves superseded NTS representations for reproducing earlier
analyses, comparing software versions, and using code tied to an older schema.
Historical status here does not imply that SAM or MetaCat has retired the files,
or that the files have been removed from storage.

The tables below retain the September 2026 catalog observations: the full
provenance check was 24 September at 23:46:57 UTC, and the `v06_14_03` listing
was refreshed on 29 September at 23:22 UTC. Their references to current MCS
coverage and status describe those snapshots, not a new availability check.

## Successors and reasons to use the current generation

| Historical NTS set | EventNtuple | Current successor |
| --- | --- | --- |
| Non-NoPrimary `Run1Baw_best_v1_5` and `Run1B-010` | `v06_13_02` or `v06_14_03` | Same description with `Run1B-013` |
| NoPrimary `Run1Baw_best_v1_5-001` and `Run1B-011` | `v06_13_02` or `v06_14_03` | `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-014.root` |
| NoPrimary `Run1Baw_best_v1_5-002` and `Run1B-012` | `v06_13_02` or `v06_14_03` | `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-015.root` |

The current generation uses EventNtuple `v06_16_00`, which includes the
[current-event weight correction](https://github.com/Mu2e/EventNtuple/pull/419),
[calorimeter primary-relationship filling](https://github.com/Mu2e/EventNtuple/pull/420),
and [calorimeter link correction](https://github.com/Mu2e/EventNtuple/pull/433).
In particular, `v06_14_03` predates the `evtwt` correction; validate any historical
weight-dependent result before reuse. Keep the original release and branch
semantics explicit when reproducing a historical analysis.

All these NTS generations reuse the same MCS populations. They are overlapping
representations, not independent exposure. Historical NTS files and their
successors must not be counted as separate simulated samples.

## Preserved September 2026 NTS catalog

### NTS configuration and live catalog

There are **two different EventNtuple generations** in the tables below. The
second is not a new simulation or reconstruction sample: it reads some of the
same Run1Baw MCS files as the first. It is a newer representation of overlapping
events, made with a different EventNtuple release and a materially different
Run1B wrapper.

| NTS set | Analysis setup | EventNtuple | MCS inputs | Relationship |
| --- | --- | --- | --- | --- |
| `Run1Baw_best_v1_5` | `AnalysisMDC2025/v02_01_00`, backing `SimJob/MDC2025av` | `v06_13_02` | Fifteen Run1Baw MCS families | First NTS production; complete relative to the current MCS definitions. |
| `Run1B-010`, `Run1B-011`, `Run1B-012` | `AnalysisMDC2025/v02_02_01`, backing `SimJob/MDC2025ax` | `v06_14_03` | All fifteen current Run1Baw MCS families | Complete re-ntupling pass relative to the current MCS definitions; overlapping events and newer schema. |

The wrapper has the same path, `EventNtuple/fcl/from_mcs-Run1B.fcl`, in both
releases, but not the same contents. The
[EventNtuple `v06_13_02...v06_14_03` comparison](https://github.com/Mu2e/EventNtuple/compare/v06_13_02...v06_14_03)
confirms these analysis-relevant differences:

| Output content | `v06_13_02` (`Run1Baw_best_v1_5`) | `v06_14_03` (`Run1B-010/-011/-012`) |
| --- | --- | --- |
| `trk` branch | `KKLine` only | Merges `KKLine`, `ProtonKKLine`, and `CosmicKKLine` into `trk` |
| Time clusters | `timeclusters` is `SimpleTimeCluster` | `timeclusters` is `CalTimeClusterFinder`; also adds `protontimeclusters`, `tztimeclusters`, and `tphitimeclusters` |
| Time-cluster hits | Not stored as separate branches | Adds `timeclustershits` and `protontimeclustershits` |
| Straight-line seeds | No line-seed branches | Adds `lineseeds`, `protonlineseeds`, and `cosmiclineseeds` |
| Other additions | Earlier MC/calorimeter schema | Adds the `primary` SimParticle branch, time-cluster `edep`, and calorimeter-cluster `secondMoment`, `e1`, `e2`, `e9`, and `e25` |
| TrkQual, TrkPID, TrkDtDt | Not stored | Still not stored |

In particular, `trk` and `timeclusters` do not have identical meanings across
the two generations even though the branch names are reused. An analysis that
reads either branch must treat the EventNtuple versions separately or explicitly
harmonize those collections.

Both NTS generations use `geom_common.txt` and do not rerun reconstruction;
their v40/DS-off reconstruction provenance comes from the parent MCS. Both also
set `cosmicLivetime.include: false`, so cosmic exposure must come from upstream
production provenance rather than an NTS livetime branch.

SAM reports no event-count metadata for the ROOT NTS definitions.  “Represented
events” below is the exact event total of the same-sequencer MCS parents covered
by each NTS definition. For the `v06_13_02` production, representative logs confirm
one tree fill per successfully processed MCS event.

#### `v06_13_02` NTS definitions

| NTS definition | NTS / current MCS files | Represented / current MCS events | Status |
| --- | --- | --- | --- |
| `nts.mu2e.CeEndpoint-KL.Run1Baw_best_v1_5.root` | 19 / 19 | 1,184,477 / 1,184,477 | Complete |
| `nts.mu2e.CeEndpointMix1BB-KL.Run1Baw_best_v1_5.root` | 1,999 / 1,999 | 1,326,786 / 1,326,786 | Complete |
| `nts.mu2e.CosmicCRYAll-KL.Run1Baw_best_v1_5.root` | 100 / 100 | 115,931,437 / 115,931,437 | Complete now |
| `nts.mu2e.CosmicCRYAllMix1BB-KL.Run1Baw_best_v1_5.root` | 995 / 995 | 2,351,533 / 2,351,533 | Complete |
| `nts.mu2e.FlatGamma-KL.Run1Baw_best_v1_5.root` | 19 / 19 | 897,555 / 897,555 | Complete |
| `nts.mu2e.FlatGammaMix1BB-KL.Run1Baw_best_v1_5.root` | 1,999 / 1,999 | 1,039,674 / 1,039,674 | Complete |
| `nts.mu2e.FlateMinus-KL.Run1Baw_best_v1_5.root` | 19 / 19 | 570,932 / 570,932 | Complete |
| `nts.mu2e.FlateMinusMix1BB-KL.Run1Baw_best_v1_5.root` | 1,998 / 1,998 | 704,053 / 704,053 | Complete |
| `nts.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1Baw_best_v1_5.root` | 1,000 / 1,000 | 154,086 / 154,086 | Complete |
| `nts.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1Baw_best_v1_5.root` | 200 / 200 | 158,688 / 158,688 | Complete |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-001.root` | 20,000 / 20,000 | 344,196,254 / 344,196,254 | Complete |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-002.root` | 1,998 / 1,998 | 99,900,000 / 99,900,000 | Complete relative to current MCS; the upstream MCS remains 1,998/2,000 planned |
| `nts.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1Baw_best_v1_5.root` | 200 / 200 | 5,249,814 / 5,249,814 | Complete |
| `nts.mu2e.RPCExternalMix1BB-KL.Run1Baw_best_v1_5.root` | 5,000 / 5,000 | 643,155 / 643,155 | Complete |
| `nts.mu2e.RPCInternalMix1BB-KL.Run1Baw_best_v1_5.root` | 5,000 / 5,000 | 230,559 / 230,559 | Complete |

All fifteen `v06_13_02` definitions now have complete file coverage relative to
their current MCS definitions. The NoPrimary `-002` NTS definition is complete
relative to the 1,998 available MCS files, while that upstream MCS production
remains 1,998/2,000 planned. No NoPrimary `-003` MCS, NTS, or EventNtuple CNF
exists at this snapshot.

#### `v06_14_03` NTS re-ntupling definitions

These definitions began appearing on 24 September 2026. The initial four-row
snapshot was still being produced; the 29 September `listNewDatasets` result
contains all fifteen expected families at their current MCS file counts.
“Represented events” are the event totals of the corresponding current MCS
definitions; SAM reports the NTS `Event count` as `None`, not zero.

| NTS definition | Direct MCS parent | NTS / current MCS files | Represented / current MCS events | Status at snapshot |
| --- | --- | --- | --- | --- |
| `nts.mu2e.CeEndpoint-KL.Run1B-010.root` | `mcs.mu2e.CeEndpoint-KL.Run1Baw_best_v1_5.art` | 19 / 19 | 1,184,477 / 1,184,477 | Complete |
| `nts.mu2e.CeEndpointMix1BB-KL.Run1B-010.root` | `mcs.mu2e.CeEndpointMix1BB-KL.Run1Baw_best_v1_5.art` | 1,999 / 1,999 | 1,326,786 / 1,326,786 | Complete |
| `nts.mu2e.CosmicCRYAll-KL.Run1B-010.root` | `mcs.mu2e.CosmicCRYAll-KL.Run1Baw_best_v1_5.art` | 100 / 100 | 115,931,437 / 115,931,437 | Complete |
| `nts.mu2e.CosmicCRYAllMix1BB-KL.Run1B-010.root` | `mcs.mu2e.CosmicCRYAllMix1BB-KL.Run1Baw_best_v1_5.art` | 995 / 995 | 2,351,533 / 2,351,533 | Complete |
| `nts.mu2e.FlatGamma-KL.Run1B-010.root` | `mcs.mu2e.FlatGamma-KL.Run1Baw_best_v1_5.art` | 19 / 19 | 897,555 / 897,555 | Complete |
| `nts.mu2e.FlatGammaMix1BB-KL.Run1B-010.root` | `mcs.mu2e.FlatGammaMix1BB-KL.Run1Baw_best_v1_5.art` | 1,999 / 1,999 | 1,039,674 / 1,039,674 | Complete |
| `nts.mu2e.FlateMinus-KL.Run1B-010.root` | `mcs.mu2e.FlateMinus-KL.Run1Baw_best_v1_5.art` | 19 / 19 | 570,932 / 570,932 | Complete |
| `nts.mu2e.FlateMinusMix1BB-KL.Run1B-010.root` | `mcs.mu2e.FlateMinusMix1BB-KL.Run1Baw_best_v1_5.art` | 1,998 / 1,998 | 704,053 / 704,053 | Complete |
| `nts.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1B-010.root` | `mcs.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 1,000 / 1,000 | 154,086 / 154,086 | Complete |
| `nts.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1B-010.root` | `mcs.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 200 / 200 | 158,688 / 158,688 | Complete |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-011.root` | `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-001.art` | 20,000 / 20,000 | 344,196,254 / 344,196,254 | Complete |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-012.root` | `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-002.art` | 1,998 / 1,998 | 99,900,000 / 99,900,000 | Complete relative to current MCS; upstream MCS remains 1,998/2,000 planned |
| `nts.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1B-010.root` | `mcs.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 200 / 200 | 5,249,814 / 5,249,814 | Complete |
| `nts.mu2e.RPCExternalMix1BB-KL.Run1B-010.root` | `mcs.mu2e.RPCExternalMix1BB-KL.Run1Baw_best_v1_5.art` | 5,000 / 5,000 | 643,155 / 643,155 | Complete |
| `nts.mu2e.RPCInternalMix1BB-KL.Run1B-010.root` | `mcs.mu2e.RPCInternalMix1BB-KL.Run1Baw_best_v1_5.art` | 5,000 / 5,000 | 230,559 / 230,559 | Complete |

All fifteen definitions now cover their current same-family MCS definitions.
These files overlap events already represented by the `v06_13_02` outputs; they
are not additional independent exposure. Do not concatenate the two generations
without event de-duplication, and do not mix their `trk` or `timeclusters`
branches without explicit schema and collection harmonization.

## Registered configurations

The original NTS production is recorded in
`cnf.mu2e.evnt.Run1Baw_best_v1_5.0.tar`. The second generation is recorded in:

```text
cnf.mu2e.evnt.Run1B-010.0.tar
cnf.mu2e.evnt.Run1B-011.0.tar
cnf.mu2e.evnt.Run1B-012.0.tar
```

These registered tarballs contain `mu2e.fcl` and `jobpars.json`. Resolve their
locations with `samweb locate-file` and inspect those text members when
reproducing the exact production setup. The [current catalog's provenance
commands](run1b_datasets_current.md#how-to-reproduce-the-provenance-check)
also apply to historical definitions when their exact names are substituted.

## See also

- [Current Run1B dataset catalog and source provenance](run1b_datasets_current.md)
- [EventNtuple v06_13_02 to v06_14_03](https://github.com/Mu2e/EventNtuple/compare/v06_13_02...v06_14_03)
- [EventNtuple v06_14_03 to v06_16_00](https://github.com/Mu2e/EventNtuple/compare/v06_14_03...v06_16_00)
