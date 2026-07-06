---
description: Trace a SAM dataset's family tree (parents back to upstream) and render a mermaid graph — sources Mu2e env automatically
argument-hint: <dataset-or-file> [--png|--svg] [--stats] [--max-files N]
allowed-tools: Bash
---

# Trace SAM dataset family tree

Thin wrapper over `bin/famtree` that does the Mu2e env setup so you
can ask "where did this dataset come from?" in one command. Encodes:

- `source setupmu2e-art.sh && muse setup ops` (samweb + python deps)
- `bash bin/famtree <name>` (the entry point has a bash shebang that
  dispatches to the Python implementation)
- Run in a `/tmp` workdir so the generated `.md` (and `.png`/`.svg`
  if requested) lands somewhere predictable and doesn't pollute the
  repo tree
- After the run, **read the rendered `<name>.md`** and inline the
  mermaid block back to the user so the lineage shows up in the chat
  without them having to open the file

## Usage

```
/famtree <dataset-or-file> [--png|--svg] [--stats] [--max-files N]
```

- `<dataset-or-file>` — full SAM file basename
  (e.g. `dts.mu2e.RPCExternal.MDC2020aw.001202_00000000.art`) **or**
  dataset name without run/subrun
  (e.g. `dts.mu2e.RPCExternal.MDC2020aw.art`). famtree auto-detects
  which it is and, for a dataset, picks the first file as the sample.
- `--png` / `--svg` — render the mermaid to a binary image via
  `mmdc` (must be on PATH; usually not present on Mu2e nodes — omit
  unless you've installed it).
- `--stats` — annotate nodes with efficiency stats sampled from
  the first N files (default 10).
- `--max-files N` — sample size for `--stats`.

## Examples

```
# 2020-era RPCExternal lineage
/famtree dts.mu2e.RPCExternal.MDC2020aw.art

# Compare a 2025 sibling chain
/famtree dts.mu2e.RPCExternalPhysical.MDC2025af.art

# Specific file (same result — famtree strips run/subrun internally)
/famtree dts.mu2e.RPCExternal.MDC2020aw.001202_00000000.art

# With efficiency stats sampled from 20 files
/famtree mcs.mu2e.CeEndpointMix1BBTriggered.MDC2025am_best_v1_3.art --stats --max-files 20
```

## Instructions

You are given `$ARGUMENTS`. Follow these steps.

### 1. Parse args

- First positional token is `TARGET` (dataset or file name). If
  missing, print Usage and exit.
- Everything else is `EXTRA_ARGS` (passed through verbatim).

### 2. Resolve repo root + workdir

- `REPO=$PWD` at invocation time.
- `WORKDIR=/tmp/famtree.$$` (per-invocation; doesn't pollute repo).
  Create it.

### 3. Run

Execute as a single Bash command so the sourced env is live for the
famtree call:

```bash
mkdir -p <WORKDIR> && cd <WORKDIR> \
  && source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh > /dev/null 2>&1 \
  && muse setup ops > /dev/null 2>&1 \
  && bash <REPO>/bin/famtree <TARGET> <EXTRA_ARGS> 2>&1
```

The script writes the mermaid graph to `<dataset-stem>.md` in the
workdir and prints status lines (which file it sampled, where the
diagram was written).

### 4. Inline the result

After the run, locate the produced `.md` (the famtree output line
"Mermaid diagram saved to <file>" tells you the path). Read that
file with the Read tool and embed the mermaid block in the response
so the lineage is visible without the user opening anything.

If `--png` / `--svg` was requested, also report the binary file path
(don't try to read it).

### 5. Report

Render the mermaid graph inline, then add a one-line interpretation:
the upstream-to-downstream chain in arrow form
(`PiBeam → PiBeamCat → PiTargetStops → PiTargetFilt → RPCExternal`).
Make it easy to compare across datasets without the user parsing
mermaid syntax.

## Notes

- famtree reads SAM metadata via `samweb file-lineage --ancestors` —
  no Offline / SimJob musing setup needed, just `muse setup ops`.
- For datasets with no SAM metadata yet (e.g. brand-new local
  outputs), famtree will error; use `fcldump --target <file>` /
  `fcldump --dataset <ds>` instead to inspect the parent fcl
  directly.
- For the *forward* direction (what consumes a given dataset), there
  is no built-in tool; use `samweb list-files
  "ischildof: (file_name <name>)"` against a sample file.
- The workdir is `/tmp/famtree.$$` — short-lived but not
  auto-cleaned. If you want to keep an artifact, copy it out.
