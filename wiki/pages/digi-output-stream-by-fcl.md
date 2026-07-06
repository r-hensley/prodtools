---
title: Digitize output stream schema by fcl
tags: [reference, digi, fcl-overrides, mdc2025]
sources: []
updated: 2026-05-29
---

# Digitize output stream schema by fcl

Which `outputs.*.fileName` keys exist depends on which digitize fcl
the entry includes. Overriding the wrong key is silently a no-op:
the override sits in the rendered fcl matching no declared stream,
and the default `dig.owner.desc.version.sequencer.art` template
leaks through. Sometimes that produces an output file named
literally `desc` (bug). Sometimes it produces a correctly-named
file by coincidence (bug, masked).

The `json2jobdef` cnf output-filename validator catches the literal
`desc` form. The coincidence form persists silently — found by
diffing an entry against the output it actually produced.

## The map

| fcl                                       | output stream(s)                   | override keys                                                   |
|-------------------------------------------|------------------------------------|-----------------------------------------------------------------|
| `Production/JobConfig/digitize/OnSpill.fcl`    | `TriggeredOutput`, `TriggerableOutput` | `outputs.TriggeredOutput.fileName`, `outputs.TriggerableOutput.fileName` |
| `Production/JobConfig/digitize/Extracted.fcl`  | `Output` (single)                  | `outputs.Output.fileName`                                       |
| `Production/JobConfig/digitize/NoField.fcl`    | `Output` (single)                  | `outputs.Output.fileName`                                       |
| `Production/JobConfig/digitize/OffSpill.fcl`   | `TriggeredOutput`, `TriggerableOutput` | (same as OnSpill — verified for ap; an+ confirmed)              |

Source of truth:
`/cvmfs/.../SimJob/MDC2025ap/Production/JobConfig/digitize/prolog.fcl:240` —
`Digitize.Outputs : { Output : @local::Digitize.Output }`. OnSpill
overrides this with `outputs.TriggeredOutput`+`outputs.TriggerableOutput`
declarations in its own prolog chain (`Spill.fcl` → split). Extracted
includes NoField directly and stays single-stream.

## How the bug bites

When MDC2025ap `CosmicCRYExtracted` was first cloned from the
MDC2025af entry:

```json
"fcl_overrides": {
  "outputs.TriggeredOutput.fileName": "dig.owner.{desc}Triggered.version.sequencer.art",
  "outputs.TriggerableOutput.fileName": "/dev/null",
  ...
}
```

`json2jobdef` failed validation with:

```
outputs.Output.fileName = 'dig.oksuzian.desc.MDC2025ap_best_v1_1.001400_00000003.art'
contains unsubstituted placeholder 'desc'
```

— because `Output` (the real stream) had no override, so the default
template `dig.owner.desc.version.sequencer.art` rendered with `desc`
unsubstituted. The TriggeredOutput/TriggerableOutput overrides
attached to keys that don't exist in the rendered fcl.

## The fix

```json
"fcl_overrides": {
  "outputs.Output.fileName": "dig.owner.{desc}.version.sequencer.art",
  "services.DbService.purpose": "Sim_best",
  "services.DbService.version": "v1_1"
}
```

Note: the historical MDC2025af `CosmicCRYExtracted` entry
(`data/mdc2025/digi.json:80-96`) **still has the wrong shape** as of
this writing. It happened to produce sane SAM dataset names anyway —
either the cnf validator hadn't shipped yet, or jobs were submitted
before strict validation. Worth scrubbing next time someone touches
that entry.

## Cross-references

- [[reference-rpc-primary-inherits-bfgeom]] — separate gotcha, primary
  fcl side, similar "the include chain set it for you" pattern.
- `reference_reco_output_suffix_overrides.md` (memory) — reco-stage
  multi-output override gotcha (suffixes glued to `description`).
- `reference_digi_extracted_single_output.md` (memory) — short-form
  summary.

## How to verify a new entry

1. Run `json2jobdef --verbose --json <file> --desc <X> --dsconf <Y>`
   locally first. The validator fires on `desc` not being substituted.
2. `fcldump --local-jobdef <cnf>.tar --index 0` and grep
   `outputs\..*\.fileName` in the rendered fcl. Every line should
   contain the resolved dataset name, no template tokens.
3. `mu2e -c <fcl> --nevts 1` to confirm the fcl is parseable end-to-end
   (catches typos in override keys that don't fail validation but
   do fail art).
