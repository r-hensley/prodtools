---
title: input_data max_nfiles cap (per-dataset file limit)
tags: [reference, json2jobdef, input_data, mix, smoke-testing]
sources: [in-session edit 2026-05-27, utils/json2jobdef.py _write_sam_inputs]
updated: 2026-05-27
---

# input_data `max_nfiles` cap (per-dataset file limit)

**Source:** in-session work 2026-05-27 on branch `field-off-option`;
modified `utils/json2jobdef.py`.
**Date:** 2026-05-27
**Type:** reference / decision

## Summary

Added an optional `max_nfiles` key inside the nested-dict value form of
`input_data` entries. When set, `json2jobdef` writes at most that many
files per dataset into `inputs.txt`. Useful for:

- Smoke tests against a real dataset without consuming the full
  upstream stack (e.g. `dts.mu2e.CosmicCRYSignalAll.MDC2020ar.art`).
- Statistically capping a contribution to a mix without splitting the
  source.
- Cheap "first N" subset runs without `samSplit`.

## Shape

Plain int form still works (unchanged):

```json
{"dts.mu2e.FlateMinus.MDC2020bb.art": 1}
```

Dict form opts into the cap:

```json
{"dts.mu2e.CosmicCRYSignalAll.MDC2020ar.art": {"merge_factor": 1, "max_nfiles": 500}}
```

Combinable with the existing `{"count": N, "random": bool}` shape:

```json
{"dts.mu2e.MuminusStopsCat.MDC2020at.art": {"count": 5, "random": true, "max_nfiles": 200}}
```

## Why nested-dict, not a sibling key

The natural first-instinct shape — adding `max_nfiles` as a sibling key
in the same dict alongside the dataset, like
`{"dts.mu2e...art": 1, "max_nfiles": 500}` — **doesn't fit the
parser**. `_write_sam_inputs` at `utils/json2jobdef.py` loops
`for dataset, merge_factor in input_data.items()`, which would treat
`"max_nfiles"` as a dataset name and query SAM for it. Adding a sibling
top-level key would require special-casing the loop at every
consumption site.

The nested-dict-value form was already established by `{"count": N,
"random": True}`, `{"chunk_lines": N}`, and `{"split_lines": N}`. Reuse
that precedent. **Rule of thumb for the next `input_data` option:** put
it inside the value dict; do not add sibling keys to the
`{dataset: value}` map.

## Semantics

- **Non-random branch:** `files = sorted(files)[:max_nfiles]`. Sorted
  first so the cap is deterministic across SAM-list reorderings (the
  same first-N you get this Tuesday is the same first-N next Tuesday).
- **Random branch:** `total_needed = min(per_job × njobs, max_nfiles)`.
  Bounds the deterministic pseudo-random sample size.
- **Validation:** must be a positive int. `max_nfiles: 0`, negative, or
  non-int → `ValueError` at parse time.
- **`njobs` is NOT recomputed.** It's the entry author's responsibility
  to keep `merge_factor × njobs ≤ max_nfiles`. This matches the
  existing non-random behavior — `json2jobdef` doesn't second-guess
  your `njobs`.

## Where it lives

- `utils/json2jobdef.py` — `_write_sam_inputs()`. Only modification
  needed; all downstream tools (`runmu2e`, `submit_map`, `jobfcl`,
  `mkrecovery`) consume `inputs.txt` / the jobdefs tarball, not the
  source JSON, so the cap propagates transparently.

## Related

- [[input-data-dir-shape]] — `inloc: "dir:<path>"` for cvmfs-resident
  inputs. Disjoint from this cap (no SAM lookup).
- [[input-data-chunk-mode]] — `chunk_lines` runtime chunking. Different
  problem (synthesizes per-job slices from a single file), different
  branch in the parser.
- [[json2jobdef-staging-workflow]] — overview of `input_data` shapes
  across stages.
