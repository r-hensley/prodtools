# Run1Ban-001 primaries added — provenance

Decision recorded 2026-06-14. Four entries added to
`data/Run1B/primary_muon.json` (after the existing Run1Bai-001 block,
before the MuCap1809keV entry):

- CeEndpoint @ Run1Ban-001 (njobs=2000, events=1M, run=1470)
- FlateMinus @ Run1Ban-001 (njobs=2000, events=1M, 50-110 MeV)
- FlatGamma  @ Run1Ban-001 (njobs=2000, events=1M, 50-110 MeV)
- NoPrimary  @ Run1Ban     (njobs=20000, events=5000)

Common:
- bFieldFile: bfgeom_DSOff.txt
- inputFile:  geom_run1_b_v40.txt   (NOT v06 like Run1Bai precedent)
- StrawGasSteps: []
- MinimumSumCaloStepE: 20
- MinimumPartMom: 0 (resampler primaries); NoPrimary has no PrimaryFilter
- simjob_setup: SimJob/Run1Ban
- owner: mu2e

Diffs from Run1Bai-001 precedent (data/Run1B/primary_muon.json lines 148-241):
- geom v40 not v06
- run 1470 not 1460
- input MuminusStopsCat.Run1Ban not Run1Bai
- simjob_setup Run1Ban not Run1Bai

Local smokes (oksuzian, 2026-06-14):
- mu2e -c cnf.mu2e.CeEndpoint.Run1Ban-001.0.fcl --nevts 1   -> status 0
- mu2e -c cnf.mu2e.FlateMinus.Run1Ban-001.0.fcl --nevts 1    -> status 0
- mu2e -c cnf.mu2e.FlatGamma.Run1Ban-001.0.fcl --nevts 1     -> status 0
- mu2e -c cnf.mu2e.NoPrimary.Run1Ban.0.fcl --nevts 1         -> status 0

Resamplers read xroot://fndcadoor.fnal.gov//pnfs/.../MuminusStopsCat/Run1Ban/art/95/76/...001470_00000010.art
(verified live during smoke).

Not yet pushed to production as of provenance write.
