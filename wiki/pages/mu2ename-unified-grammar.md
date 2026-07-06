---
title: Mu2eName — unified Mu2e dot-name value object
tags: [decision, reference, refactor, naming]
sources: []
updated: 2026-05-29
---

## Summary

`utils/job_common.Mu2eName` is the single value object for the Mu2e
dot-name grammar — file, dataset, and tarball — with both **parse**
and **build** entry points and ~10 derivation methods. It replaced
two half-classes (`Mu2eFilename`, `Mu2eDSName`) and absorbed
~30 hand-rolled `.split('.')` reads plus ~15 hand-rolled f-string
builders across the `utils/` tree.

`Mu2eFilename` remains as an alias of `Mu2eName` so the Perl-parity
contract on `relpathname()` stays traceable.

## Shape

The grammar covers three forms:

| Form     | Fields | Example                                                  |
|----------|--------|----------------------------------------------------------|
| FILE     | 6      | `dts.mu2e.CeEndpoint.Run1Bab.001440_00001234.art`        |
| DATASET  | 5      | `dts.mu2e.CeEndpoint.Run1Bab.art`                        |
| TARBALL  | 6      | `cnf.mu2e.CeEndpoint.MDC2025af_best_v1_3.42.tar`         |

Sequencer (when present) is one opaque chunk (`NNNNNN_NNNNNNNN`,
never contains `.`). Tarball slot 4 is an integer index, not a
sequencer.

## Interface (selected)

```python
Mu2eName.parse(s)            # accepts any of the three forms
Mu2eName.build(tier=..., owner=..., description=..., dsconf=...,
               sequencer=None, extension=...)

# discriminators
.is_dataset / .is_file / .is_tarball

# sub-field conventions
.index                      # int for tarballs; raises otherwise
.campaign                   # MDC2025af | Run1Bab
.dsconf_base                # 'MDC2025af_best_v1_3' → 'MDC2025af'
.dsconf_version             # 'MDC2025af_best_v1_3' → 'best_v1_3'

# tier semantics (folds the old jobsub_argv._TIER_TO_OWNER_CLASS)
.tier_class                 # sim/etc/dat/nts umbrella

# derivations (all return new Mu2eName)
.dataset                    # drop sequencer; idempotent
.with_sequencer(seq) / .with_extension(ext) / .as_tier(t)
.log_dataset()              # cnf tarball → log dataset

# path / parity
.relpathname()              # SHA256-prefixed (Perl Mu2eFilename->relpathname)
.basename() / str(n)
```

## Error policy

`parse()` is **fail-loud** — `ValueError` on any field count outside
`{5, 6}`, on `.index` of a non-tarball, on `.log_dataset()` of a
non-tarball, on building with a `.` in any field.

Two sites are *deliberately lenient* and wrap `parse()` in
`try/except ValueError → None`:

- `latestDatasets.parse_name` — SAM may return arbitrary strings
- `jobsub_argv.description_from_tarball` / `campaign_from_tarball` — POMS
  map paths can be non-Mu2e (e.g. `mu2eg4bl/...`)

Leniency stays at the caller boundary, never inside the type.

## Why-not-alternatives

- **Three sibling types** (`Mu2eFile` / `Mu2eDataset` / `Mu2eTarball`)
  rejected: the three forms differ by one optional field; three types
  triplicate path logic, parity methods, and tests for no semantic
  gain.
- **Read-only object** rejected: would have kept the duplicated
  *builders* (`jobfcl.py:148` == `stash_utils.py:70` byte-for-byte
  before the refactor) — the highest-value half of the dedup.
- **Free functions** rejected: existing code already leaned class-based
  for this concept; a value object with derivations matches house style
  and lets callers pass one carrier around instead of dict/tuple
  plumbing.
- **New `Mu2eName` class beside the old `Mu2eFilename`** rejected:
  would have required a transitional shim and broken the Perl-parity
  association on the original symbol. Extending in place + alias was
  shim-free.

## Where it lives

- Class: `utils/job_common.py` (also: `Mu2eFilename` alias,
  `_TIER_TO_OWNER_CLASS` module constant used by `.tier_class`).
- Tests: `test/test_unit.py` — `TestMu2eFilename` (pinned legacy
  contract) + `TestMu2eName` (extended interface, 21 cases including
  fail-loud, round-trip, log_dataset byte-equality, tier_class parity).
- Perl parity: `test/parity_test.sh` (`relpathname()` is unchanged
  byte-for-byte).

## Migration scope

19 files migrated, ~45 call sites collapsed. Five `.split('.')` sites
remain in `utils/` and are explicitly NOT Mu2e names (FHiCL key path
in `jobdef.py`, the parser itself in `job_common.py`).

`jobsub_argv._TIER_TO_OWNER_CLASS` was deleted (now on
`Mu2eName.tier_class`); a leftover historical comment in
`jobsub_argv.py:67-69` points at the new home.

## Related

- [[json2jobdef-staging-workflow]] — dsconf flow uses `.dsconf_base` /
  `.dsconf_version`
- [[2026-04-30-phase2-direct-jobsub-implementation]] — `tier_class`
  drives the direct-mode storage-modify scope
- [[outloc-lives-in-poms-map-not-cnf]] — cnf naming and `.log_dataset()`
  derivation
