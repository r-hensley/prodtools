# Run1B datasets — current catalog and provenance

This page catalogs the current Run1B v40, detector-solenoid-off DIGI Monte
Carlo datasets, their Run1Baw MCS reconstruction, and the `Run1B-013/-014/-015`
EventNtuple generation. It records source construction, mixing, production
filters, timing windows, and analysis and normalization caveats.

The [historical dataset catalog](run1b_datasets_historical.md) preserves older
NTS definitions and software/branch differences for reproducing earlier work.
The DIGI and MCS datasets below remain inputs to the current ntuples.

**Original full provenance audit: 24 September 2026 at 23:46:57 UTC.**
**Current MCS counts and NTS catalog/configuration/parent coverage rechecked:
2026-11-06 04:56:36 UTC.** Earlier DIGI/source-generation details retain their original
audit scope. File and event counts are point-in-time catalog observations;
they establish neither physical exposure nor dCache locality.

## Quick interpretation

- `CeEndpointMix1BB` is the conversion-electron-like signal sample with Run1 one-booster-batch beam-background overlay.  The plain `CeEndpoint` definition uses the same primary DTS library and is its useful overlay ablation.
- `FlateMinus` and `FlatGamma` are flat-kinematics detector-response samples, not physical DIO or RMC spectra.  Their mixed/plain pairs reuse the same primary DTS libraries.
- `CosmicCRYAll` is the inclusive, multi-particle CRY cosmic sample.  The listed plain and mixed definitions are **not** a clean overlay-only pair: their stage-2 source geometries differ (v03 versus v40).
- `MuCapNeutronTailCalo`, `MuCapProtonTailCalo`, and `PolyFlatGammaCalo` are deliberately high-energy, calorimeter-directed stress samples.  They are not rate samples.
- `RPCExternal` and `RPCInternal` are radiative-pion-capture photon and internal-conversion-pair samples.  They require the stored RPC survival/event weight and use an early 300 ns digitization start.
- `NoPrimaryMix1BB` has no physics primary; its physics content is the mixed beam-background libraries.  `-001` is high-calo enriched from a 5-billion-event source, `-002` is the unfiltered 100-million-event normal-window control, and `-003` is the corresponding early-time variant.
- The Run1Baw `mcs...-KL` definitions are no-field KinematicLine reconstruction outputs.  `-KL` does not mean the events passed a line-fit filter: the final reconstruction path omits `KLFilter` and retains every successfully processed input event.
- The Run1Baw `nts...-KL` definitions are standardized EventNtuple ROOT files made one-for-one from MCS files.  They are analysis conveniences, not a second reconstruction and not replacements for every custom analysis branch.
- The current `Run1B-013/-014/-015` definitions re-ntuple all fifteen Run1Baw MCS families with EventNtuple `v06_16_00`. They include event-weight and calorimeter-truth/linking fixes, and add no independent exposure. Older NTS generations are listed in the [historical catalog](run1b_datasets_historical.md).

## Name components

- **`dig`** — Detector digitization output.  These files are inputs to reconstruction; they are not reconstructed `mcs` files.

- **`mcs`** — Reconstructed Monte Carlo ART output.  The Run1Baw definitions below contain the no-field KinematicLine reconstruction products.

- **`-KL`** — KinematicLine/KKLine reconstruction family and output naming.  It is not an event-selection claim.

- **`nts`** — EventNtuple ROOT output made from MCS.  SAM does not register event-count metadata for these ROOT definitions; parent-MCS coverage is used below.

- **`Mix1BB`** — The primary event is mixed with the Run1 single-booster-batch beam-background model.  The overlay contains `MuBeamFlash`, `EleBeamFlash`, `NeutralsFlash`, and `MuStopPileup` components.  It does not mean exactly one background particle or one library event.

- **no `Mix1BB`** — Primary-only digitization, with no beam-background overlay.

- **`Run1Ban`, `Run1Bap`, `Run1Baq`, `Run1Bav`, `Run1Baw`** — Production/configuration tags used for these Run1B datasets, not independent top-level campaigns and not generator names.  The Run1Bav DIGIs were made with the consolidated `MDC2025av` SimJob release; Run1Baw labels the downstream reconstruction/ntuple production.

- **`Run1B-013`, `Run1B-014`, `Run1B-015`** — Current NTS output-configuration tags. Their direct parents are existing `Run1Baw_best_v1_5` MCS definitions; they do not identify another reconstruction pass. Earlier `Run1B-010/-011/-012` output tags are documented in the historical catalog.

- **`best_v1_4` / `best_v1_5`** — `Sim_best` conditions purpose and version.

## Common production conditions

All sixteen generated DIGI FCLs explicitly select
`Offline/Mu2eG4/geom/geom_run1_b_v40.txt` and the DS-off field file
`Offline/Mu2eG4/geom/bfgeom_DSOff.txt`.  This describes the DIGI job;
the plain cosmic dataset has an older v03 upstream DTS geometry, documented below.

| Campaign | DIGI Offline backing | Conditions | Tracker/calo digitization window | Important distinctions |
| --- | --- | --- | --- | --- |
| `Run1Ban` | `v13_17_10` | `Sim_best/v1_4` | 450–1650 ns | Standard four-component 1BB overlay; no later explicit neutral-flash factor of 0.01. |
| `Run1Bap` | `v13_32_10` | `Sim_best/v1_5` | **300–1650 ns** | Early-time RPC production. The neutral-flash parent is Run1Baq; other overlay parents are Run1Ban. |
| `Run1Baq` | `v13_34_10` | `Sim_best/v1_5` | 450–1650 ns | Explicit `NeutralsFlashMixer.meanEventsPerPOTFactors: [0.01]`. |
| `Run1Bav -001` | `v13_35_00` | `Sim_best/v1_5` | 450–1650 ns | Run1Baq NoPrimary source; active high-calo filter. |
| `Run1Bav -002` | `v13_35_00` | `Sim_best/v1_5` | 450–1650 ns | Older Run1Ban NoPrimary source; null high-calo filter. |
| `Run1Bav -003` | `v13_35_00` | `Sim_best/v1_5` | **300–1650 ns** | Same source/filter design as -002, with explicit 300 ns tracker and calorimeter start overrides. |

The generated mixed-job FCLs set `PBISim.extendedMean: 5.92e6` and
`PBISim.cutMax: 35.5e6`.  These generated overrides are the effective
values for these productions.

## DIGI dataset catalog

| Dataset definition | Files | Saved events | Sample meaning and recommended use |
| --- | --- | --- | --- |
| `dig.mu2e.CeEndpointMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 | 1,326,786 | Approximately 105 MeV/c conversion-electron-like primaries from stopped Al muons, plus 1BB. Signal-like/stress sample. |
| `dig.mu2e.CeEndpoint.Run1Ban_best_v1_4-000.art` | 19 | 1,184,477 | Same `dts.mu2e.CeEndpoint.Run1Ban-001.art` primary library, without beam overlay. Overlay ablation for the mixed CE sample. |
| `dig.mu2e.CosmicCRYAllMix1BB.Run1Ban_best_v1_4-000.art` | 995 | 2,351,533 | Inclusive multi-particle CRY showers resampled through Run1Ban v40 stage 2, plus 1BB. Cosmic stress/background sample. The Run1Ban DTS `CosmicLivetime` is stored as zero because of an integer-truncation bug; use the documented true 22.9 s per contributing DTS file. |
| `dig.mu2e.CosmicCRYAll.Run1Ban_best_v1_4-000.art` | 100 | 115,931,437 | Inclusive CRY without beam overlay, but sourced from the much larger Run1Bah **v03** stage-2 DTS production. Not a geometry-controlled mixed/plain partner. Run1Bah stored livetime is 22.4% low; use 114.5 s per contributing DTS file or multiply the stored value by 1.289. |
| `dig.mu2e.FlateMinusMix1BB.Run1Ban_best_v1_4-000.art` | 1,998 | 704,053 | Flat 50–110 MeV/c electrons at stopped-Al-muon positions/times, plus 1BB. Electron-response/training stress sample; not physical DIO. |
| `dig.mu2e.FlateMinus.Run1Ban_best_v1_4-000.art` | 19 | 570,932 | Same flat-electron DTS library, without beam overlay. Overlay ablation for the mixed flat-electron sample. |
| `dig.mu2e.FlatGammaMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 | 1,039,674 | Flat 50–110 MeV/c photons at stopped-Al-muon positions/times, plus 1BB. Photon-response stress sample; not physical RMC. |
| `dig.mu2e.FlatGamma.Run1Ban_best_v1_4-000.art` | 19 | 897,555 | Same flat-photon DTS library, without beam overlay. Overlay ablation for the mixed flat-photon sample. |
| `dig.mu2e.MuCapNeutronTailCaloMix1BB.Run1Baq_best_v1_5.art` | 1,000 | 154,086 | Muon-capture neutrons above 60 MeV kinetic energy from `SchroederNeutronSpectrum.txt`, aimed nearly along +z toward the calorimeter, plus 1BB. High-energy neutron/calorimeter response stress sample, not a rate sample. |
| `dig.mu2e.MuCapProtonTailCaloMix1BB.Run1Baq_best_v1_5.art` | 200 | 158,688 | Muon-capture protons above 60 MeV kinetic energy from the `ejectedProtons` spectrum, aimed nearly along +z, plus 1BB. High-energy proton/calorimeter response stress sample, not a rate sample. |
| `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-001.art` | 20,000 | 344,196,254 | No physics primary; beam-background overlay only. Produced from 5.0 billion Run1Baq empty source events and filtered on a CaloShowerStep cluster above 50 MeV. High-calo-enriched tail; normalize from the processed source exposure, not saved count. |
| `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-002.art` | 2,000 | 100,000,000 | No physics primary; beam-background overlay only. Uses 100 million older Run1Ban empty source events, a null calo filter, and the normal window. Inclusive/control sample for filter-efficiency and sculpting checks. |
| `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-003.art` | 2,000 | 100,000,000 | Same source and null-filter design as -002, but with 300–1650 ns tracker/calo digitization. Early-time RPC occupancy/timing variant; independent random mixing/digitization means it need not be event-bitwise-identical to -002. |
| `dig.mu2e.PolyFlatGammaCaloMix1BB.Run1Baq_best_v1_5.art` | 200 | 5,249,814 | Flat 50–110 MeV/c photons at muon stops in COL5 polyethylene/carbon, aimed nearly along +z, plus 1BB. Poly-stop photon/calorimeter response sample; not a physical photon spectrum or rate. |
| `dig.mu2e.RPCExternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 | 643,155 | External radiative pion capture: a Bistirlich-spectrum 50–139.5 MeV photon at a stopped-pion position, plus 1BB. Early-time RPC photon sample; apply the RPC survival/event weight. |
| `dig.mu2e.RPCInternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 | 230,559 | Internal radiative pion capture: the sampled virtual photon converts to an electron-positron pair using the Kroll–Wada model, plus 1BB. Early-time RPC pair sample; apply the RPC survival/event weight. |

## Reconstructed products

The Run1Baw production reconstructs the DIGIs above into `mcs...-KL`
ART files and then converts available MCS files into `nts...-KL`
EventNtuple ROOT files.  The exact parent definitions are listed below; the
Run1Baw tag is an output-production label and does not replace the parent DIGI
provenance.

### MCS configuration and geometry

All fifteen registered generated reconstruction FCL payloads are byte-identical.
They include `Production/JobConfig/recoMC/NoFieldRun1B.fcl`, select
`Sim_best/v1_5`, name `geom_run1_b_v40.txt` and
`bfgeom_DSOff.txt`, and write `KinematicLineOutput`.  Their
`jobpars.json` setup environments nevertheless split into two groups:

| MCS definitions | Registered reconstruction setup | Offline backing | Resolved geometry reported by the job |
| --- | --- | --- | --- |
| All except NoPrimary `-001/-002` | `SimJob/Run1Baq/setup.sh` | `v13_34_10` | `geom_run1_b_v40.txt`: 21,486 lines, framework hash `1848509147153137480` |
| NoPrimary `-001/-002` | `SimJob/MDC2025aw/setup.sh` | `v13_36_00` | `geom_run1_b_v40.txt`: 21,840 lines, framework hash `2036620008520853265` |

The DS-off field has the same logged 67-line/hash signature in both groups, but
the expanded geometry does not.  A common `v40` filename is therefore
not proof of a byte-identical reconstruction geometry.  Comparisons involving
the NoPrimary MCS and another Run1Baw family should retain this
release/geometry-domain caveat.

The base configuration defines `KLFilter`, but the final
`NoFieldRun1B.fcl` explicitly rewrites `RecoPath` without that
module.  `KinematicLineOutput.SelectEvents: ["RecoPath"]` therefore
means successful path execution, not a successful KKLine fit.  Representative
logs and aggregate counts show all successfully processed parent-DIGI events
written to MCS.

### Live MCS catalog

MCS file and event counts were rechecked with the current NTS audit. The
September provenance audit found no retired MCS records in these definitions.
Expected files are the exact DIGI inputs recorded in the registered
reconstruction CNF.

| MCS definition | Parent DIGI definition | Files / expected | Saved events | Status |
| --- | --- | --- | --- | --- |
| `mcs.mu2e.CeEndpoint-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CeEndpoint.Run1Ban_best_v1_4-000.art` | 19 / 19 | 1,184,477 | Complete |
| `mcs.mu2e.CeEndpointMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CeEndpointMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 / 1,999 | 1,326,786 | Complete |
| `mcs.mu2e.CosmicCRYAll-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CosmicCRYAll.Run1Ban_best_v1_4-000.art` | 100 / 100 | 115,931,437 | Complete now; an earlier 98/100 catalog snapshot was transient |
| `mcs.mu2e.CosmicCRYAllMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CosmicCRYAllMix1BB.Run1Ban_best_v1_4-000.art` | 995 / 995 | 2,351,533 | Complete |
| `mcs.mu2e.FlatGamma-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlatGamma.Run1Ban_best_v1_4-000.art` | 19 / 19 | 897,555 | Complete |
| `mcs.mu2e.FlatGammaMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlatGammaMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 / 1,999 | 1,039,674 | Complete |
| `mcs.mu2e.FlateMinus-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlateMinus.Run1Ban_best_v1_4-000.art` | 19 / 19 | 570,932 | Complete |
| `mcs.mu2e.FlateMinusMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlateMinusMix1BB.Run1Ban_best_v1_4-000.art` | 1,998 / 1,998 | 704,053 | Complete |
| `mcs.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.MuCapNeutronTailCaloMix1BB.Run1Baq_best_v1_5.art` | 1,000 / 1,000 | 154,086 | Complete |
| `mcs.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.MuCapProtonTailCaloMix1BB.Run1Baq_best_v1_5.art` | 200 / 200 | 158,688 | Complete |
| `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-001.art` | `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-001.art` | 20,000 / 20,000 | 344,196,254 | Complete |
| `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-002.art` | `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-002.art` | **1,998 / 2,000** | **99,900,000** | Missing sequencers `001470_00000445` and `001470_00001443`; registered retries fail with ROOT-basket read/corruption errors |
| `mcs.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.PolyFlatGammaCaloMix1BB.Run1Baq_best_v1_5.art` | 200 / 200 | 5,249,814 | Complete |
| `mcs.mu2e.RPCExternalMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.RPCExternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 / 5,000 | 643,155 | Complete |
| `mcs.mu2e.RPCInternalMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.RPCInternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 / 5,000 | 230,559 | Complete |

The September audit found incomplete dataset-wide MetaCat lineage for 270
`FlateMinusMix1BB-KL` MCS records and NoPrimary `-001`
sequencer `001470_00004188`: those records have no direct
`parents:` entry.  Their output names/event totals and the immutable
CNF input lists still align with the parent definitions above.  This is a catalog
provenance-link gap, not missing physics files. No Run1Baw MCS definition for
NoPrimary `-003` is registered at the November 6
check; the September provenance audit also found no reconstruction log or CNF
for that variant.

#### Why NoPrimary `-002` has only 1,998 MCS files

The two absent outputs are not a reconstruction selection or failed
KinematicLine fits. They correspond to DIGI sequencers `001470_00000445` and
`001470_00001443`. Registered reconstruction attempts open and process those
inputs but terminate during ROOT input finalization with `FileReadError` from
`TBasket::Streamer` and an invalid negative `fKeylen` (`-23569` and `-27091`,
respectively). Repeated attempts fail on the same two inputs, which points to
persistent ROOT basket/key corruption in those DIGI files rather than a
transient worker failure.

The latest registered failure logs are named:

```text
log.mu2e.NoPrimaryMix1BB-reco.Run1Baw_best_v1_5-002.1473-1787896828.log
log.mu2e.NoPrimaryMix1BB-reco.Run1Baw_best_v1_5-002.1330-1787897216.log
```

Consequently, all readable inputs produced MCS output: 1,998 files and
99,900,000 events. The current NTS generation covers those 1,998 available MCS
files, as do the two historical generations. Re-ntupling cannot recover the missing 100,000
source events without repaired or reproduced DIGI inputs.

### NTS configuration and live catalog

The current generation is `Run1B-013`, `Run1B-014`, and `Run1B-015`, made with
EventNtuple `v06_16_00`. These are regenerated ntuples of the existing Run1Baw
MCS events. They add no independent simulation exposure and do not rerun
reconstruction. The earlier `Run1Baw_best_v1_5` and `Run1B-010/-011/-012` NTS
tables are preserved in the [historical catalog](run1b_datasets_historical.md).

For new analyses, start with this generation and check the branches and weights
used by the analysis. The catalog and configuration checks below establish
provenance and file coverage; they do not certify tree-entry counts or physics
validation of every output.

| NTS configuration | Analysis setup | Backing release | EventNtuple | Direct inputs |
| --- | --- | --- | --- | --- |
| `Run1B-013` | `AnalysisMDC2025/v02_03_01` | `SimJob/MDC2025bb` | `v06_16_00` | The thirteen non-NoPrimary Run1Baw MCS families |
| `Run1B-014` | `AnalysisMDC2025/v02_03_01` | `SimJob/MDC2025bb` | `v06_16_00` | NoPrimary Run1Baw MCS `-001`, high-calo enriched |
| `Run1B-015` | `AnalysisMDC2025/v02_03_01` | `SimJob/MDC2025bb` | `v06_16_00` | NoPrimary Run1Baw MCS `-002`, inclusive 450 ns control |

The three registered CNFs include
`EventNtuple/fcl/from_mcs-Run1B.fcl`. Their `jobpars.json` files select the
analysis setup above; its installed EventNtuple checkout is tag `v06_16_00`,
commit `70b124c6077c332cdaf4be9fbca0f6206b491ed3`.

#### Why use the regenerated ntuples

Relative to `v06_14_03`, this release includes analysis-relevant corrections:

- [PR #419](https://github.com/Mu2e/EventNtuple/pull/419) refreshes the current event's weight handles before filling `evtwt`; the earlier order could fill stale or invalid weights. This is especially relevant to the RPC survival weights.
- [PR #420](https://github.com/Mu2e/EventNtuple/pull/420) fills `calomcsim.prirel`, the relationship to the event primary, so calorimeter clusters from primary descendants can be identified without relying on SimParticle IDs alone.
- [PR #433](https://github.com/Mu2e/EventNtuple/pull/433) uses collection/`Ptr` identity when linking calorimeter hits, reco digis, and digis, avoiding fragile value-based matching for the configured collection.

These changes explain the technical value of regenerating the ntuples. The
specific production request for `Run1B-013/-014/-015` has not been independently
confirmed. The full [release comparison](https://github.com/Mu2e/EventNtuple/compare/v06_14_03...v06_16_00)
and [tagged Run1B wrapper](https://github.com/Mu2e/EventNtuple/blob/v06_16_00/fcl/from_mcs-Run1B.fcl)
record the source changes and effective configuration.

The wrapper still merges `KKLine`, `ProtonKKLine`, and `CosmicKKLine` into
`trk`, stores the four named time-cluster collections and the three line-seed
collections, and uses `geom_common.txt`. The v40/DS-off reconstruction provenance
remains that of the parent MCS. TrkQual and TrkPID are not configured for these
merged tracks (`mvaTags` and `mvaBranches` are empty), and TrkDtDt filling is off.
The default `calo.mc.entrantTag` is empty, so the optional
`calohitsmc.entrantSimIds` feature is not populated by this wrapper.
`cosmicLivetime.include` is also false; cosmic normalization still needs upstream
production provenance. These defaults are recorded in the wrapper and the
[tagged prolog](https://github.com/Mu2e/EventNtuple/blob/v06_16_00/fcl/prolog.fcl).

#### Current NTS definitions and coverage

**Catalog and direct-parent audit: 2026-11-06 04:56:36 UTC.** All 40,546 active NTS files
have exactly one same-family, same-sequencer MCS parent and the expected
registered CNF parent. Every file in the fifteen corresponding active MCS
definitions is covered exactly once. SAM and MetaCat file counts agree, and
there are no retired NTS records in these definitions at this check.

SAM reports NTS `Event count: None`, meaning unavailable event-count metadata.
The covered-MCS-event column is the SAM event total of the fully covered parent
definition, not an independently measured ROOT tree-entry count. Sizes use
decimal GB (`10^9` bytes); the complete NTS generation totals 1,740,931,257,563
bytes (about 1.74 TB). Catalog registration does not establish dCache locality.

| NTS definition | Direct MCS parent | NTS / MCS files | Covered MCS events | NTS size (GB) |
| --- | --- | --- | --- | --- |
| `nts.mu2e.CeEndpoint-KL.Run1B-013.root` | `mcs.mu2e.CeEndpoint-KL.Run1Baw_best_v1_5.art` | 19 / 19 | 1,184,477 | 19.46 |
| `nts.mu2e.CeEndpointMix1BB-KL.Run1B-013.root` | `mcs.mu2e.CeEndpointMix1BB-KL.Run1Baw_best_v1_5.art` | 1,999 / 1,999 | 1,326,786 | 27.41 |
| `nts.mu2e.CosmicCRYAll-KL.Run1B-013.root` | `mcs.mu2e.CosmicCRYAll-KL.Run1Baw_best_v1_5.art` | 100 / 100 | 115,931,437 | 196.09 |
| `nts.mu2e.CosmicCRYAllMix1BB-KL.Run1B-013.root` | `mcs.mu2e.CosmicCRYAllMix1BB-KL.Run1Baw_best_v1_5.art` | 995 / 995 | 2,351,533 | 16.78 |
| `nts.mu2e.FlatGamma-KL.Run1B-013.root` | `mcs.mu2e.FlatGamma-KL.Run1Baw_best_v1_5.art` | 19 / 19 | 897,555 | 1.53 |
| `nts.mu2e.FlatGammaMix1BB-KL.Run1B-013.root` | `mcs.mu2e.FlatGammaMix1BB-KL.Run1Baw_best_v1_5.art` | 1,999 / 1,999 | 1,039,674 | 9.82 |
| `nts.mu2e.FlateMinus-KL.Run1B-013.root` | `mcs.mu2e.FlateMinus-KL.Run1Baw_best_v1_5.art` | 19 / 19 | 570,932 | 9.58 |
| `nts.mu2e.FlateMinusMix1BB-KL.Run1B-013.root` | `mcs.mu2e.FlateMinusMix1BB-KL.Run1Baw_best_v1_5.art` | 1,998 / 1,998 | 704,053 | 14.64 |
| `nts.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1B-013.root` | `mcs.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 1,000 / 1,000 | 154,086 | 1.36 |
| `nts.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1B-013.root` | `mcs.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 200 / 200 | 158,688 | 2.72 |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-014.root` | `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-001.art` | 20,000 / 20,000 | 344,196,254 | 1,176.07 |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-015.root` | `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-002.art` | 1,998 / 1,998 | 99,900,000 | 205.32 |
| `nts.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1B-013.root` | `mcs.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 200 / 200 | 5,249,814 | 45.19 |
| `nts.mu2e.RPCExternalMix1BB-KL.Run1B-013.root` | `mcs.mu2e.RPCExternalMix1BB-KL.Run1Baw_best_v1_5.art` | 5,000 / 5,000 | 643,155 | 9.00 |
| `nts.mu2e.RPCInternalMix1BB-KL.Run1B-013.root` | `mcs.mu2e.RPCInternalMix1BB-KL.Run1Baw_best_v1_5.art` | 5,000 / 5,000 | 230,559 | 5.96 |

Every row is complete relative to its current MCS definition. In particular,
`Run1B-015` covers all 1,998 available NoPrimary `-002` MCS files, while the
upstream reconstruction remains 1,998/2,000 planned. Re-ntupling cannot recover
the two missing DIGI-to-MCS outputs described above. Different NTS generations
overlap in events; use one representation for an analysis rather than counting
them as independent samples.

## Source generation and filtering

The primary DTS definitions are themselves selected detector-step samples.  Their
registered event counts are therefore not the number of generator trials.

| Family | Primary DTS definition | Configured generator/resampler trials | Retained DTS events | Source efficiency | Source construction |
| --- | --- | --- | --- | --- | --- |
| CE mixed/plain | `dts.mu2e.CeEndpoint.Run1Ban-001.art` | 2,000,000,000 | 3,326,758 | 0.1663% | Endpoint electron from a stopped Al muon; calorimeter-oriented source filter. |
| Cosmic mixed | `dts.mu2e.CosmicCRYAll.Run1Ban.art` | 100,000,000 | 2,899,101 | 2.899% | Resamples the common CRY stage-1 library using Run1Ban v40 stage-2 simulation/filter. |
| Cosmic plain | `dts.mu2e.CosmicCRYAll.Run1Bah.art` | 4,977,000,000 | 141,353,437 | 2.840% | Resamples the same stage-1 library using Run1Bah v03 stage-2 simulation/filter. |
| Flat electron mixed/plain | `dts.mu2e.FlateMinus.Run1Ban-001.art` | 1,999,000,000 | 3,049,553 | 0.1526% | Flat 50–110 MeV/c electron; calorimeter-oriented source filter. |
| Flat photon mixed/plain | `dts.mu2e.FlatGamma.Run1Ban-001.art` | 2,000,000,000 | 2,608,176 | 0.1304% | Flat 50–110 MeV/c photon; calorimeter-oriented source filter. |
| Neutron tail | `dts.mu2e.MuCapNeutronTailCalo.Run1Baq.art` | 125,000,000 | 4,768,912 | 3.815% | Capture-neutron spectrum; kinetic energy above 60 MeV and `0.99 < cos(theta_z) < 1`. |
| Proton tail | `dts.mu2e.MuCapProtonTailCalo.Run1Baq.art` | 100,000,000 | 3,721,921 | 3.722% | Ejected-proton spectrum; kinetic energy above 60 MeV and `0.99 < cos(theta_z) < 1`. |
| NoPrimary -001 | `dts.mu2e.NoPrimary.Run1Baq.art` | 5,000,000,000 | 5,000,000,000 | 100.0% | Empty events; the later mixing job supplies all physics content. |
| NoPrimary -002/-003 | `dts.mu2e.NoPrimary.Run1Ban.art` | 100,000,000 | 100,000,000 | 100.0% | Empty events; the later mixing job supplies all physics content. |
| Poly photon | `dts.mu2e.PolyFlatGammaCalo.Run1Baq.art` | 100,000,000 | 11,669,927 | 11.67% | Flat 50–110 MeV/c photon from COL5 poly/C muon stops, aimed nearly along +z. |
| RPC external | `dts.mu2e.RPCExternal.Run1Bap.art` | 5,000,000,000 | 5,729,464 | 0.1146% | Bistirlich photon at a stopped-pion position; standard 45 MeV calo-rich source filter. |
| RPC internal | `dts.mu2e.RPCInternal.Run1Bap.art` | 5,000,000,000 | 4,165,776 | 0.08332% | Kroll–Wada internal-conversion pair; standard 45 MeV calo-rich source filter. |

The configured-trials column is reconstructed from job count times
`source.maxEvents`.  It is a generator/resampling trial count, **not**
an equivalent POT, stopped-muon exposure, or physical normalization.

For CE, the flat samples, capture tails, and poly photon, the source driver disables
tracker-step alternatives and configures a 20 MeV single-particle calorimeter-step
threshold; the inherited total-calorimeter threshold remains 45 MeV.  RPC retains
the standard 45 MeV calo thresholds.  These source datasets are deliberately
detector-response enriched.

## CRYAll details and geometry warning

Both cosmic stage-2 sources resample
`sim.mu2e.CosmicDSStopsCRYAll.MDC2025ab.art` (20,000 files and
2,585,823,777 registered events).  The stage-1 configuration generates correlated
CRY showers at the surface and propagates them toward the DS/CRV stage-1 boundary.
Its exact CRY configuration enables muons, neutrons, protons, photons, electrons,
pions, and kaons.  This is the meaning of `CRYAll`.

The registered DIGI `jobpars.json` files show:

- `CosmicCRYAllMix1BB` reads `dts.mu2e.CosmicCRYAll.Run1Ban.art`, whose source CNF uses `geom_run1_b_v40.txt`;
- plain `CosmicCRYAll` reads `dts.mu2e.CosmicCRYAll.Run1Bah.art`, whose source CNF uses `geom_run1_b_v03.txt`.

Although both final DIGI FCLs specify v40, the detector steps were already made in
stage 2.  The listed plain/mixed comparison therefore changes source statistics and
source-stage geometry in addition to removing beam overlay.  A clean cosmic overlay
ablation needs a plain DIGI made from the Run1Ban v40 DTS source, or an explicitly
validated equivalent.

The stage-2 cosmic sources also have a known integer-truncation bug in their stored
`CosmicLivetime` products; see
[Offline PR #1940](https://github.com/Mu2e/Offline/pull/1940) for the corresponding
code correction:

- Run1Bah stores 88.8 s/file instead of the true 114.5 s/file.  Multiply the stored livetime by 1.289, or use 114.5 s per contributing DTS file.
- Run1Ban evaluates `floor(100000/129291)=0`, so its stored livetime is exactly zero and cannot be fixed with a multiplicative correction.  Use the documented true 22.9 s per contributing DTS file and the exact downstream job provenance.

Do not normalize either cosmic DIGI from raw saved-event count.  See the Run1B
cosmic table and warning on [MDC2025](https://mu2ewiki.fnal.gov/wiki/MDC2025).

## DIGI output selection

Most definitions on this page are not inclusive copies of their DTS inputs.  The
Run1B no-field digitization epilog saves the no-field calorimeter-focused trigger
menu (`calo_cluster_60`, `70`, `75`,
`80`, and `apr_TC_calo`) plus the
`TriggerableCaloPath`, with
`TriggerableCalo.MinParticleEnergy=60 MeV`.  This final DIGI selection is
separate from the earlier source-DTS filter.

The corrected MDC2025av NoPrimary configuration instead selects successful
`DigitizePath` events:

- `-001` has `CaloDtsClusterFilter.NullFilter=false`.  It clusters `CaloShowerStep` energy and requires a cluster above 50 MeV, using `MinimumStepTime=400 ns`, `TimeWindow=100 ns`, and `SpaceWindow=80 mm`.
- `-002` and `-003` have `NullFilter=true` and save all 100 million successful digitizations.

The `-001` 50 MeV variable is therefore a truth-step cluster, not a
reconstructed calorimeter cluster and not an analysis quantity such as
`lead_calo_energy`.

## Analysis and normalization cautions

1. Raw saved-event count is not physical exposure.  Use the appropriate generator count, source exposure, cosmic livetime, event weight, and rate model.
1. CE is a signal-kinematics sample.  A physical CE yield also needs stopped-muon exposure and an assumed conversion rate.
1. Flat electron/photon, directed tail, poly-photon, and RPC datasets are biased in kinematics and/or source selection.  Use them for response, efficiency, classifier support, and failure-mode studies rather than raw-rate estimates.
1. RPC generation turns pion decay off during transport and records the exponential survival correction as an event weight.  Ignoring the weight changes the time/rate model.
1. Normalize NoPrimary `-001` from 5.0 billion processed source events, not 344.2 million saved events.  Use `-002` to measure production-filter efficiency and feature/score sculpting.  Do not concatenate `-001` and `-002` with unit event weights.
1. `-002` and `-003` are the best pair here for studying the configured 450 ns versus 300 ns start, but independent random mixing/digitization can still cause event-level differences.

## How to reproduce the provenance check

`listNewDatasets` is supplied by prodtools, not by `muse setup ops` alone. On a
GPVM, use an installed prodtools release with the operations environment:

```bash
mu2einit
muse setup ops
source /cvmfs/mu2e.opensciencegrid.org/bin/prodtools/v3.3.4/bin/setup.sh
listNewDatasets --filetype root --days 30 | grep Run1B
```

For a specific definition, compare the SAM summary with active and
active-plus-retired MetaCat counts:

```bash
samweb list-definition-files --summary dig.mu2e.CeEndpointMix1BB.Run1Ban_best_v1_4-000.art
metacat query -s \
  "files from mu2e:dig.mu2e.CeEndpointMix1BB.Run1Ban_best_v1_4-000.art"
metacat query -r -s \
  "files from mu2e:dig.mu2e.CeEndpointMix1BB.Run1Ban_best_v1_4-000.art"
```

The compact registered production evidence is the CNF tarball. It contains the
generated FCL and `jobpars.json`, including the exact setup and source grouping.
Resolve the current catalog location rather than copying a hard-coded storage
path:

```bash
samweb locate-file \
  cnf.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-003.0.tar

CNF=/path/reported/by/samweb/cnf.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-003.0.tar
tar -xOf "$CNF" mu2e.fcl
tar -xOf "$CNF" jobpars.json
```

For comparison, locate
`cnf.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-002.0.tar` the same way.

The `-003` generated FCL explicitly sets tracker,
`CaloShowerROMaker`, and `CaloDigiMaker`
`digitizationStart: 300`.  The `-002` generated FCL has no
start override and inherits 450 ns from Offline `v13_35_00`:

```text
/cvmfs/mu2e.opensciencegrid.org/Musings/Offline/v13_35_00/Offline/TrackerConditions/fcl/prolog.fcl
/cvmfs/mu2e.opensciencegrid.org/Musings/Offline/v13_35_00/Offline/CaloReco/fcl/common.fcl
/cvmfs/mu2e.opensciencegrid.org/Musings/Offline/v13_35_00/Offline/CaloMC/fcl/prolog.fcl
```

For the reconstructed MCS definitions, inspect both the generated FCL and
`jobpars.json`; the latter is where the Run1Baq versus MDC2025aw setup split
appears. The relevant registered tarball names are:

```text
cnf.mu2e.CeEndpointMix1BB-reco.Run1Baw_best_v1_5.0.tar
cnf.mu2e.NoPrimaryMix1BB-reco.Run1Baw_best_v1_5-001.0.tar
```

The current EventNtuple configurations are registered separately:

```text
cnf.mu2e.evnt.Run1B-013.0.tar
cnf.mu2e.evnt.Run1B-014.0.tar
cnf.mu2e.evnt.Run1B-015.0.tar
```

Their `mu2e.fcl` members include the same Run1B wrapper; `jobpars.json` records
`AnalysisMDC2025/v02_03_01/setup.sh`. Historical CNF names are retained in the
[historical catalog](run1b_datasets_historical.md#registered-configurations).

For direct lineage and represented parent-event totals:

```bash
metacat query \
  "parents(files from mu2e:nts.mu2e.NoPrimaryMix1BB-KL.Run1B-014.root)"
samweb list-files --summary \
  "isparentof: (defname: nts.mu2e.NoPrimaryMix1BB-KL.Run1B-014.root)"
```

The MetaCat parent query includes both MCS and CNF parents. To reproduce the
one-to-one coverage check, list each NTS definition with `metacat query -j -P`,
compare every file's parent IDs with the expected MCS IDs and CNF ID, check the
sequencers, and require each MCS ID exactly once. Equal aggregate counts alone
do not establish that coverage. For a dataset-wide MCS audit, also compare output
sequencers with the immutable CNF input list because missing direct catalog
links are not recovered by querying retired records.

## See also

- [Historical Run1B dataset catalog](run1b_datasets_historical.md)
- [Datasets](https://mu2ewiki.fnal.gov/wiki/Datasets)
- [MDC2025](https://mu2ewiki.fnal.gov/wiki/MDC2025)
- [RunNumbers](https://mu2ewiki.fnal.gov/wiki/RunNumbers)
- [Generators](https://mu2ewiki.fnal.gov/wiki/Generators)
- [Mixing](https://mu2ewiki.fnal.gov/wiki/Mixing)
- [Mixing and Resampling](https://mu2ewiki.fnal.gov/wiki/Mixing_and_Resampling)
- [FileNames](https://mu2ewiki.fnal.gov/wiki/FileNames)
