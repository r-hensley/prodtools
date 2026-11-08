# Run1B datasets — current catalog

Run1B v40, detector-solenoid-off DIGI, KinematicLine MCS reconstruction, and
`Run1B-013/-014/-015` ntuples. Older ntuple generations and release differences
are in the [historical catalog](run1b_datasets_historical.md).

**Catalog counts checked 8 November 2026, 21:25 UTC.** Configuration provenance
was audited in September, with current NTS and MuCap1809 configurations checked
6–8 November. File counts are active catalog members. dCache locality
and ROOT/ART payload contents require separate checks.

<a id="quick-interpretation"></a>
<a id="name-components"></a>

`dig` contains digitization, `mcs` contains reconstructed MC, and `nts` contains
EventNtuple ROOT output. `-KL` identifies KinematicLine reconstruction.
`Mix1BB` adds Run1 single-booster-batch beam background from muon, electron,
neutral-flash and stopped-muon pileup libraries. Plain samples omit that overlay.
Production tags identify configurations, and `best_v1_4/v1_5` identifies the
`Sim_best` conditions version.

## Common production conditions

DIGI configurations select `geom_run1_b_v40.txt` and `bfgeom_DSOff.txt`.
The plain cosmic sample has v03 detector steps upstream of digitization.

| DIGI production | Offline backing | Conditions | Tracker/calo window | Configuration detail |
| --- | --- | --- | --- | --- |
| `Run1Ban` | `v13_17_10` | `Sim_best/v1_4` | 450–1650 ns | Four-component 1BB overlay. |
| `Run1Bap` | `v13_32_10` | `Sim_best/v1_5` | 300–1650 ns | RPC. Neutral-flash library from Run1Baq, other overlay libraries from Run1Ban. |
| `Run1Baq` | `v13_34_10` | `Sim_best/v1_5` | 450–1650 ns | Neutral-flash `meanEventsPerPOTFactors: [0.01]`. |
| `Run1Bav -001/-002` | `v13_35_00` | `Sim_best/v1_5` | 450–1650 ns | Filtered/inclusive NoPrimary controls. |
| `Run1Bav -003` | `v13_35_00` | `Sim_best/v1_5` | 300–1650 ns | Explicit tracker and calo start overrides. |
| `Run1Baw` MuCap1809 | `v13_36_00` | `Sim_best/v1_5` | 450–1650 ns | Mixed sample: neutral-flash `simStageEfficiencyTags: []`, `meanEventsPerProton: 1e-07`. |

Mixed-job overrides set `PBISim.extendedMean=5.92e6` and `cutMax=35.5e6`.

## DIGI dataset catalog

| Dataset definition | Files | Saved events | Sample |
| --- | --- | --- | --- |
| `dig.mu2e.CeEndpointMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 | 1,326,786 | Endpoint electrons from stopped Al muons + 1BB. |
| `dig.mu2e.CeEndpoint.Run1Ban_best_v1_4-000.art` | 19 | 1,184,477 | Same CE source, primary-only. |
| `dig.mu2e.CosmicCRYAllMix1BB.Run1Ban_best_v1_4-000.art` | 995 | 2,351,533 | CRY showers from the v40 stage-2 source + 1BB. |
| `dig.mu2e.CosmicCRYAll.Run1Ban_best_v1_4-000.art` | 100 | 115,931,437 | Primary-only CRY showers from the older v03 stage-2 source. |
| `dig.mu2e.FlateMinusMix1BB.Run1Ban_best_v1_4-000.art` | 1,998 | 704,053 | Flat 50–110 MeV/c electrons + 1BB. |
| `dig.mu2e.FlateMinus.Run1Ban_best_v1_4-000.art` | 19 | 570,932 | Same flat-electron source, primary-only. |
| `dig.mu2e.FlatGammaMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 | 1,039,674 | Flat 50–110 MeV/c photons + 1BB. |
| `dig.mu2e.FlatGamma.Run1Ban_best_v1_4-000.art` | 19 | 897,555 | Same flat-photon source, primary-only. |
| `dig.mu2e.MuCap1809keVCaloMix1BB.Run1Baw_best_v1_5.art` | 1,000 | 2,259,321 | Calorimeter-directed 1.809 MeV capture photons + 1BB. |
| `dig.mu2e.MuCap1809keVCalo.Run1Baw_best_v1_5.art` | 10 | 2,259,321 | Same capture-photon source, primary-only. |
| `dig.mu2e.MuCapNeutronTailCaloMix1BB.Run1Baq_best_v1_5.art` | 1,000 | 154,086 | Capture neutrons above 60 MeV, directed toward the calorimeter + 1BB. |
| `dig.mu2e.MuCapProtonTailCaloMix1BB.Run1Baq_best_v1_5.art` | 200 | 158,688 | Capture protons above 60 MeV, directed toward the calorimeter + 1BB. |
| `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-001.art` | 20,000 | 344,196,254 | Beam overlay with a >50 MeV truth-step calo-cluster filter. Source has 5 billion empty events. |
| `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-002.art` | 2,000 | 100,000,000 | Inclusive beam overlay, 100 million empty source events, 450 ns start. |
| `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-003.art` | 2,000 | 100,000,000 | Inclusive beam overlay, same source as -002, 300 ns start. |
| `dig.mu2e.PolyFlatGammaCaloMix1BB.Run1Baq_best_v1_5.art` | 200 | 5,249,814 | Flat 50–110 MeV/c photons from COL5 poly/C muon stops, directed toward the calorimeter + 1BB. |
| `dig.mu2e.RPCExternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 | 643,155 | Bistirlich-spectrum 50–139.5 MeV capture photons + 1BB. Apply the RPC survival weight. |
| `dig.mu2e.RPCInternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 | 230,559 | Kroll–Wada internal-conversion electron–positron pairs + 1BB. Apply the RPC survival weight. |

## Reconstructed products

### MCS configuration and geometry

Registered MCS FCLs include `Production/JobConfig/recoMC/NoFieldRun1B.fcl`,
select `Sim_best/v1_5`, v40 geometry and DS off, and write `KinematicLineOutput`.
The final `RecoPath` omits `KLFilter`, so saved events can contain failed or
absent KKLine fits.

| MCS families | Registered setup | Offline backing |
| --- | --- | --- |
| CE, cosmic, flat electron/photon, capture tails, poly photon, RPC | `SimJob/Run1Baq` | `v13_34_10` |
| NoPrimary `-001/-002`, MuCap1809 plain/mixed | `SimJob/MDC2025aw` | `v13_36_00` |

September job logs show different expanded geometry between these releases
despite the shared v40 filename. Retain this qualification in cross-family
comparisons.

### Live MCS catalog

Expected outputs are the job count in the registered reconstruction CNF.
MuCap1809 mixed merges 20 DIGI files per job, producing 50 outputs from all
1,000 DIGI inputs.

| MCS definition | Parent DIGI definition | Files / expected outputs | Saved events |
| --- | --- | --- | --- |
| `mcs.mu2e.CeEndpoint-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CeEndpoint.Run1Ban_best_v1_4-000.art` | 19 / 19 | 1,184,477 |
| `mcs.mu2e.CeEndpointMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CeEndpointMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 / 1,999 | 1,326,786 |
| `mcs.mu2e.CosmicCRYAll-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CosmicCRYAll.Run1Ban_best_v1_4-000.art` | 100 / 100 | 115,931,437 |
| `mcs.mu2e.CosmicCRYAllMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.CosmicCRYAllMix1BB.Run1Ban_best_v1_4-000.art` | 995 / 995 | 2,351,533 |
| `mcs.mu2e.FlatGamma-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlatGamma.Run1Ban_best_v1_4-000.art` | 19 / 19 | 897,555 |
| `mcs.mu2e.FlatGammaMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlatGammaMix1BB.Run1Ban_best_v1_4-000.art` | 1,999 / 1,999 | 1,039,674 |
| `mcs.mu2e.FlateMinus-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlateMinus.Run1Ban_best_v1_4-000.art` | 19 / 19 | 570,932 |
| `mcs.mu2e.FlateMinusMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.FlateMinusMix1BB.Run1Ban_best_v1_4-000.art` | 1,998 / 1,998 | 704,053 |
| `mcs.mu2e.MuCap1809keVCalo-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.MuCap1809keVCalo.Run1Baw_best_v1_5.art` | 10 / 10 | 2,259,321 |
| `mcs.mu2e.MuCap1809keVCaloMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.MuCap1809keVCaloMix1BB.Run1Baw_best_v1_5.art` | 50 / 50 | 2,259,321 |
| `mcs.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.MuCapNeutronTailCaloMix1BB.Run1Baq_best_v1_5.art` | 1,000 / 1,000 | 154,086 |
| `mcs.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.MuCapProtonTailCaloMix1BB.Run1Baq_best_v1_5.art` | 200 / 200 | 158,688 |
| `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-001.art` | `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-001.art` | 20,000 / 20,000 | 344,196,254 |
| `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-002.art` | `dig.mu2e.NoPrimaryMix1BB.Run1Bav_best_v1_5-002.art` | 1,998 / 2,000 | 99,900,000 |
| `mcs.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.PolyFlatGammaCaloMix1BB.Run1Baq_best_v1_5.art` | 200 / 200 | 5,249,814 |
| `mcs.mu2e.RPCExternalMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.RPCExternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 / 5,000 | 643,155 |
| `mcs.mu2e.RPCInternalMix1BB-KL.Run1Baw_best_v1_5.art` | `dig.mu2e.RPCInternalMix1BB.Run1Bap_best_v1_5-000.art` | 5,000 / 5,000 | 230,559 |

<a id="why-noprimary--002-has-only-1998-mcs-files"></a>

NoPrimary `-002` lacks sequencers `001470_00000445` and `001470_00001443`
after repeated ROOT input-read failures. NoPrimary `-003` has no observed
Run1Baw MCS counterpart. The September audit also found missing direct parent
links for 270 FlateMinusMix1BB MCS records and NoPrimary `-001` sequencer
`001470_00004188`; the registered input lists provide their intended mapping.
The new MuCap1809 mixed DIGI has five unresolved parent IDs, while its 1,000
primary DTS links and downstream MCS links were resolved.

### NTS configuration and live catalog

All three tags use `AnalysisMDC2025/v02_03_01`, backed by `SimJob/MDC2025bb`
and EventNtuple `v06_16_00`. `Run1B-014` reads NoPrimary MCS `-001`,
`Run1B-015` reads NoPrimary `-002`, and `Run1B-013` reads the other listed families.
The registered CNFs include `EventNtuple/fcl/from_mcs-Run1B.fcl`.

The wrapper merges `KKLine`, `ProtonKKLine` and `CosmicKKLine` into `trk`.
Merged-track TrkQual/TrkPID, TrkDtDt, calorimeter `entrantSimIds` and cosmic
livetime filling are disabled. Time-cluster and line-seed collections are retained.
[Wrapper](https://github.com/Mu2e/EventNtuple/blob/v06_16_00/fcl/from_mcs-Run1B.fcl),
[defaults](https://github.com/Mu2e/EventNtuple/blob/v06_16_00/fcl/prolog.fcl).

#### Current NTS definitions and coverage

SAM NTS `Event count: None` denotes unavailable event metadata. Covered MCS
events below come from fully covered parent definitions; ROOT tree entries
require an output-content check. Sizes use decimal GB.

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
| `nts.mu2e.MuCap1809keVCalo-KL.Run1B-013.root` | `mcs.mu2e.MuCap1809keVCalo-KL.Run1Baw_best_v1_5.art` | 10 / 10 | 2,259,321 | 0.78 |
| `nts.mu2e.MuCap1809keVCaloMix1BB-KL.Run1B-013.root` | `mcs.mu2e.MuCap1809keVCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 50 / 50 | 2,259,321 | 6.23 |
| `nts.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1B-013.root` | `mcs.mu2e.MuCapNeutronTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 1,000 / 1,000 | 154,086 | 1.36 |
| `nts.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1B-013.root` | `mcs.mu2e.MuCapProtonTailCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 200 / 200 | 158,688 | 2.72 |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-014.root` | `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-001.art` | 20,000 / 20,000 | 344,196,254 | 1,176.07 |
| `nts.mu2e.NoPrimaryMix1BB-KL.Run1B-015.root` | `mcs.mu2e.NoPrimaryMix1BB-KL.Run1Baw_best_v1_5-002.art` | 1,998 / 1,998 | 99,900,000 | 205.32 |
| `nts.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1B-013.root` | `mcs.mu2e.PolyFlatGammaCaloMix1BB-KL.Run1Baw_best_v1_5.art` | 200 / 200 | 5,249,814 | 45.19 |
| `nts.mu2e.RPCExternalMix1BB-KL.Run1B-013.root` | `mcs.mu2e.RPCExternalMix1BB-KL.Run1Baw_best_v1_5.art` | 5,000 / 5,000 | 643,155 | 9.00 |
| `nts.mu2e.RPCInternalMix1BB-KL.Run1B-013.root` | `mcs.mu2e.RPCInternalMix1BB-KL.Run1Baw_best_v1_5.art` | 5,000 / 5,000 | 230,559 | 5.96 |

Direct-parent audits establish one-to-one coverage of the current MCS files.
`Run1B-015` covers all 1,998 available NoPrimary MCS files, inheriting the
upstream two-file shortfall.
Ntuple generations reuse the same MCS events and add no independent exposure.

## Source generation and filtering

DTS stores selected detector steps. Configured trials are job count times
`source.maxEvents`; physical normalization also needs the production's source
exposure or weights.

| Primary DTS definition | Configured trials | Retained DTS events | Source |
| --- | --- | --- | --- |
| `dts.mu2e.CeEndpoint.Run1Ban-001.art` | 2,000,000,000 | 3,326,758 | Endpoint electron from a stopped Al muon; calorimeter-oriented source filter. |
| `dts.mu2e.CosmicCRYAll.Run1Ban.art` | 100,000,000 | 2,899,101 | Resamples the common CRY stage-1 library using Run1Ban v40 stage-2 simulation/filter. |
| `dts.mu2e.CosmicCRYAll.Run1Bah.art` | 4,977,000,000 | 141,353,437 | Resamples the same stage-1 library using Run1Bah v03 stage-2 simulation/filter. |
| `dts.mu2e.FlateMinus.Run1Ban-001.art` | 1,999,000,000 | 3,049,553 | Flat 50–110 MeV/c electron; calorimeter-oriented source filter. |
| `dts.mu2e.FlatGamma.Run1Ban-001.art` | 2,000,000,000 | 2,608,176 | Flat 50–110 MeV/c photon; calorimeter-oriented source filter. |
| `dts.mu2e.MuCap1809keVCalo.Run1Baw.art` | 10,000,000 | 2,259,321 | 1.809 MeV capture photons directed toward the calorimeter. |
| `dts.mu2e.MuCapNeutronTailCalo.Run1Baq.art` | 125,000,000 | 4,768,912 | Capture-neutron spectrum; kinetic energy above 60 MeV and `0.99 < cos(theta_z) < 1`. |
| `dts.mu2e.MuCapProtonTailCalo.Run1Baq.art` | 100,000,000 | 3,721,921 | Ejected-proton spectrum; kinetic energy above 60 MeV and `0.99 < cos(theta_z) < 1`. |
| `dts.mu2e.NoPrimary.Run1Baq.art` | 5,000,000,000 | 5,000,000,000 | Empty events; the later mixing job supplies all physics content. |
| `dts.mu2e.NoPrimary.Run1Ban.art` | 100,000,000 | 100,000,000 | Empty events; the later mixing job supplies all physics content. |
| `dts.mu2e.PolyFlatGammaCalo.Run1Baq.art` | 100,000,000 | 11,669,927 | Flat 50–110 MeV/c photon from COL5 poly/C muon stops, aimed nearly along +z. |
| `dts.mu2e.RPCExternal.Run1Bap.art` | 5,000,000,000 | 5,729,464 | Bistirlich photon at a stopped-pion position; standard 45 MeV calo-rich source filter. |
| `dts.mu2e.RPCInternal.Run1Bap.art` | 5,000,000,000 | 4,165,776 | Kroll–Wada internal-conversion pair; standard 45 MeV calo-rich source filter. |

CE, flat electron/photon, capture-tail and poly-photon source drivers disable
tracker-step alternatives, set a 20 MeV single-particle calo-step threshold and
retain the 45 MeV total-calo threshold. RPC retains the standard 45 MeV calo
thresholds. MuCap1809 uses 0.1 MeV calo-energy thresholds and
`0.99 <= cos(theta_z) <= 1`.

## CRYAll details and geometry warning

Both cosmic sources resample `sim.mu2e.CosmicDSStopsCRYAll.MDC2025ab.art`,
containing correlated CRY muons, neutrons, protons, photons, electrons, pions
and kaons. Mixed DIGI uses Run1Ban v40 stage-2 DTS; plain DIGI uses Run1Bah v03.
Their comparison changes source geometry and statistics as well as overlay.

| Cosmic DTS source | Stored livetime issue | Normalization |
| --- | --- | --- |
| Run1Bah, plain | 88.8 s/file stored | Use 114.5 s per contributing DTS file, or multiply stored livetime by 1.289. |
| Run1Ban, mixed | Integer truncation stores zero | Use 22.9 s per contributing DTS file and the exact downstream input list. |

The source correction is documented in
[Offline PR #1940](https://github.com/Mu2e/Offline/pull/1940) and the
[MDC2025 cosmic table](https://mu2ewiki.fnal.gov/wiki/MDC2025).

## DIGI output selection

The usual no-field DIGI epilog accepts the calo-focused trigger menu
(`calo_cluster_60/70/75/80`, `apr_TC_calo`) or `TriggerableCaloPath`, whose
`MinParticleEnergy` is 60 MeV. This follows the earlier DTS selection.

NoPrimary uses `DigitizePath` selection. Its `-001` filter requires a truth-step
calo cluster above 50 MeV, with `MinimumStepTime=400 ns`, `TimeWindow=100 ns`
and `SpaceWindow=80 mm`. The cluster uses `CaloShowerStep` energy. Variants
`-002/-003` set `NullFilter=true` and retain successful digitizations.
Both MuCap1809 DIGIs override the trigger epilog with `mixing/NoPrimary.fcl`,
retaining successful `DigitizePath` events.

## Analysis and normalization cautions

- Normalize CE using stopped-muon exposure and the assumed conversion rate.
- Flat, directed-tail, poly-photon and source-filtered samples require their
  generation/selection corrections for rate estimates.
- Apply the stored RPC survival weight, which accounts for pion decay disabled
  during transport. Use the corrected current ntuple generation for `evtwt`.
- Normalize NoPrimary `-001` from its 5 billion source events. Use `-002` as
  the inclusive filter-efficiency control. Combining the two requires weights.
- NoPrimary `-002/-003` compare 450 ns and 300 ns digitization starts, with
  independent random mixing and digitization.

## How to reproduce the provenance check

On a configured GPVM, compare SAM with active and active-plus-retired MetaCat
membership for the exact definition.

```bash
source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh
setup metacat 3.38.0
setup sam_web_client

definition=nts.mu2e.MuCap1809keVCaloMix1BB-KL.Run1B-013.root
samweb list-definition-files --summary "$definition"
metacat query -s "files from mu2e:$definition"
metacat query -r -s "files from mu2e:$definition"
metacat query -j -P "files from mu2e:$definition"
```

Use the per-file parent IDs to check unique MCS coverage. Resolve registered
CNFs through SAM and inspect both the FCL and setup/input grouping.

```bash
samweb locate-file cnf.mu2e.evnt.Run1B-013.0.tar
CNF=/path/reported/by/samweb/cnf.mu2e.evnt.Run1B-013.0.tar
tar -tf "$CNF"
tar -xOf "$CNF" mu2e.fcl
tar -xOf "$CNF" jobpars.json
```

## See also

- [Historical Run1B ntuples](run1b_datasets_historical.md)
- [Mu2e datasets](https://mu2ewiki.fnal.gov/wiki/Datasets)
- [Mixing and resampling](https://mu2ewiki.fnal.gov/wiki/Mixing_and_Resampling)
