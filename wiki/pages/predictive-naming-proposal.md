---
title: Predictive output naming — proposal
tags: [decision, proposal, naming, chain]
sources: []
updated: 2026-07-07
---

# Predictive output naming — proposal (NOT implemented)

**Status:** proposal, 2026-07-07. Sketched on user request ("input files
define output filenames"). No code written.

## Principle

For a chain hop `input dataset + stage fcl → output dataset(s)`, five of
the six Mu2eName fields are derivable; only dsconf is policy:

| field | source |
|---|---|
| tier | stage (digi/mix → dig, reco → mcs, ntuple → nts, cat → same) |
| owner | submitter class (mu2epro → mu2e) |
| description | input desc + per-fcl transform (+pbeam, +Triggered/Triggerable, -KL/-LH/-CH, +Cat) |
| dsconf | **policy** — latest SimJob + conditions series; nts = next free series (SAM lookup, see [[../pages/run1ban-campaign|campaign pages]] and memory reference_ntuple_dsconf_series) |
| sequencer | 1:1 → inherited from input file; merge → job index (Mu2eJobBase arithmetic) |
| extension | stage |

## Gap today

The per-fcl suffix knowledge (which output streams, which desc suffixes)
is quadruplicated: upstream Production fcls, hand-written fcl_overrides in
`data/*.json`, memory notes, and [[digi-output-stream-by-fcl]]. Incidents
caused by the split:
- MDC2025af CosmicCRYExtracted: silently-dead override keys (fcl has a
  single `Output` stream, entry assumed Triggered/Triggerable) — see
  [[digi-output-stream-by-fcl]].
- Reco multi-output `-LH`/`-CH`: pushOutput rejects malformed names when
  the explicit per-output override is missing
  (memory reference_reco_output_suffix_overrides).

## Design

1. **Per-fcl naming table** (data-driven, lives beside `templates/` — the
   existing policy home; do NOT create a second policy module):
   `fcl → {tier, streams: [{output_key, desc_suffix}], ext}`.
2. **`predict_outputs(input_dataset, fcl, dsconf) -> [Mu2eName]`** — pure
   function on top of the table + Mu2eName grammar.
3. **json2jobdef integration**: when an entry has no explicit output
   fileName overrides, inject predicted ones. Keep
   `validate_output_filenames` as the guard.
4. **Predict-vs-fcl cross-check** at build time: predicted outputs must
   match the fhicl-get-derived set; mismatch = loud build error. This
   turns the CosmicCRYExtracted bug class into an impossible state.
   Prediction replaces the *hand-written* half only — the fcl stays
   ground truth, and an fcl missing from the table fails loud (repo
   no-fallbacks policy).
5. **Downstream consumers** (later): `--skip-produced`, mkrecovery, and
   chain planning work from predicted names without opening cnf tarballs;
   subsumes the deferred "jobquery output_datasets derivation" item and
   removes several per-entry fhicl-get calls.

## Effect on config surface

Entries shrink toward `{input_data, fcl, dsconf}`; chain-emit templates
get thinner (naming moves out of them). Endpoint: `latestDatasets --emit`
plus the table covers a whole chain hop with zero hand-written names.

## n→1 (merge) semantics

Merge hops (artcat, digi merge, mixing's primary inputs) split cleanly
into two prediction levels:

- **Dataset level: fully predictable pre-build.** Merge factor never
  appears in the name; expected output file count = `ceil(n_in/merge)` =
  `job_common.tbs_capacity()`. Completeness/skip-produced checks need no
  cnf.
- **File level: predictable only once the input list is frozen.** Job i's
  output sequencer = sequencer of the first file in slice
  `[i*merge, (i+1)*merge)` (`Mu2eJobBase.sequencer(i)` — already
  implemented; jobfcl --target and mkrecovery rely on it). Ordering of
  the frozen list + merge factor are part of the mapping, so pre-build
  file names are undefined — the cnf IS the file-level prediction.

Corollary: **never extend an n→1 campaign in place** — appending inputs
re-slices and renames outputs mid-dataset. `--extend`'s
exclude-processed + version-suffix-bump behavior is the correct and
only-safe semantics; predictive naming makes the reason explicit (same
dataset name ⇒ same frozen list).

Reverse map is lossy for n→1: an output name encodes only its first
parent; full parentage stays in SAM metadata (famtree), not the grammar.

## Freezing the input list by definition

The file-level gap above closes if the frozen list is a pure function of
the input dataset name. Two ingredients:

1. **Canonical order.** Input list ≝ lexicographically sorted membership
   (fixed-width sequencers ⇒ lexicographic = run/subrun order). Status
   quo 2026-07-07: random branch sorts before its deterministic shuffle,
   `max_nfiles` sorts, but the **default branch writes raw SAM return
   order** (`json2jobdef._create_inputs_file`) — reproducible in
   practice, guaranteed by nothing. Fix = one `sorted()`; forward-only
   behavior change on the build path — land deliberately.
2. **Membership freeze point.** Preferred: *completeness is the freeze* —
   SAM is append-only, so a complete dataset has final membership; chain
   hops already fire on completeness, this just makes it an asserted
   invariant (json2jobdef may fail loud when consuming a growing dataset
   without --extend). Formal alternative: SAM snapshots (immutable id,
   freeze-first, record in jobpars) — held in reserve. Partial
   consumption: --extend version suffixes are the freeze units; each cnf
   freezes the exclusion-complement of its predecessors.

Payoff: exact file-level predictions pre-build for complete inputs, and
**reproducible cnfs** (rebuild ⇒ byte-identical jobpars.json) — the
byte-compare harness becomes a permanent invariant instead of a
session-local check.

Caveats: file retirement breaks membership purity (snapshot-immune;
completeness policy detects as count mismatch); random-selection
entries have deterministic seeds but a growing domain still changes the
sample — they need the completeness freeze too.

## Open questions

- nts dsconf series allocation: lookup is mechanizable but allocation
  needs care against concurrent pushes (today it's a human samweb query).
- Table maintenance: per Production release or per fcl path? Suffix sets
  have changed across releases (Extracted single-Output vs OnSpill
  Triggered/Triggerable) — the cross-check (4) is what catches drift.
- Where g4bl fits: decoupled from the Offline chain (memory
  reference_g4bl_decoupled_from_offline) — out of scope.

## Related

- [[digi-output-stream-by-fcl]] — the stream-suffix knowledge to absorb
- [[mu2ename-unified-grammar]] — the grammar this builds on
- [[json2jobdef-staging-workflow]] — the config surface this shrinks
