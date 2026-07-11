---
description: Check dCache residency for a Mu2e dataset and prestage from tape if needed (mdh-based; samweb fallback documented). Source: https://mu2ewiki.fnal.gov/wiki/Prestage
argument-hint: <DATASET> [DATASET2 ...] | --file <list.txt> | --check-only | --legacy-sam
allowed-tools: Bash
---

# Prestage a Mu2e dataset from tape

Thin wrapper over `mdh query-dcache` + `mdh prestage-files` that
handles the "is this dataset on disk, and if not pull it off tape"
question with one command. Mirrors the workflow documented at
https://mu2ewiki.fnal.gov/wiki/Prestage but encoded so you do not
need to remember the flags.

## Usage

```
/prestage <DATASET> [DATASET2 ...]
/prestage --file <list.txt>
/prestage --check-only <DATASET>
/prestage --legacy-sam <DEFNAME>
```

- Positional `DATASET` — one or more SAM/metacat dataset names
  (`tier.owner.desc.dsconf.format`). Multiple datasets are passed
  to `mdh prestage-files` in one invocation, which merges the
  request and walks tapes once per volume (saves robot/seek time —
  the wiki's "multiple small datasets" optimisation).
- `--file <list.txt>` — text file with one filename per line. Use
  for prestaging a subset of a dataset (the wiki's file-list form).
- `--check-only` — run `mdh query-dcache -o <DATASET>` only, report
  the ONLINE / ONLINE_AND_NEARLINE / NEARLINE breakdown, and stop.
  Do not issue a prestage request.
- `--legacy-sam <DEFNAME>` — fall back to the older SAM path:
  `samweb prestage-dataset --parallel=5 --defname=<DEFNAME>`.
  Only needed if `mdh` is unavailable in the env, or for an existing
  SAM dataset definition (not a raw dataset name).

## Instructions

1. **Parse argv.** Identify mode (default = prestage one-or-more
   datasets; `--file`, `--check-only`, `--legacy-sam` override).
   Validate that exactly one mode is selected.

2. **Source env** (only the parts needed for the chosen mode):

   ```bash
   source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh
   muse setup ops
   ```

   For `--legacy-sam`, also confirm `samweb` is on PATH (`muse
   setup ops` brings it in via `dhtools`). The user must already
   hold a valid bearer token at `/run/user/$(id -u)/bt_u$(id -u)` —
   `samweb prestage-dataset` writes to the SAM database and needs
   auth. **Never** run `htgettoken` for the `mu2epro` account; if
   the token is missing under mu2epro, stop and report.

3. **Size sanity check** (default + `--file` mode). Before issuing
   the prestage:

   ```bash
   for DS in $DATASETS; do
     N=$(samweb count-files "dh.dataset $DS" 2>/dev/null || echo "?")
     echo "$DS  $N files"
   done
   ```

   If any single dataset has > 100,000 files, **stop and warn**:
   the wiki rule is to coordinate with the production group and
   split via `samSplit DATASET TAG N` (N = ceil(Nfiles/100k))
   first. Do not auto-split — the subset definitions persist and
   would pollute SAM if generated speculatively.

4. **Check residency first** (skipped for `--legacy-sam`):

   ```bash
   mdh query-dcache -o <DATASET> | awk '
     /^ONLINE_AND_NEARLINE/ {a++} /^NEARLINE/ {b++} /^ONLINE$/ {c++}
     END {print "on disk + tape: " a "\non tape only:    " b "\non disk only:    " c}'
   ```

   - `ONLINE_AND_NEARLINE` → already prestaged
   - `NEARLINE` → on tape, needs prestage
   - `ONLINE` → very new, not yet on tape (no prestage required)

   If `--check-only`, stop here. Otherwise, if `NEARLINE` count is 0,
   report "already on disk, no prestage needed" and stop.

5. **Run the prestage:**

   Default / multi-dataset:
   ```bash
   mdh prestage-files -v <DATASET> [<DATASET2> ...]
   ```

   File-list:
   ```bash
   mdh prestage-files -v <list.txt>
   ```

   Legacy SAM:
   ```bash
   samweb prestage-dataset --parallel=5 --defname=<DEFNAME>
   ```

   `-v` prints the running on-disk fraction. The mdh request pins
   each file to disk for **14 days**. If interrupted, re-run with
   `-m` (resume mode) instead of `-v`:

   ```bash
   mdh prestage-files -m <DATASET>
   ```

6. **Set expectations.** Prestage throughput is ~100k files/day in
   good conditions; up to ~2 weeks during heavy enstore demand
   (per the wiki). Do not retry in a loop — the request is queued
   server-side and will progress on its own.

## Notes and pitfalls (from the wiki)

- **`ls` on the pnfs path does NOT trigger prestage.** Only the
  documented commands do.
- **Always check first** — `mdh query-dcache -o` is cheap. Don't
  blindly prestage a dataset that is already 100% on disk.
- **dCache last-accessed race:** `mdh prestage-files` updates
  last-accessed when it pulls a file from tape, but NOT when it
  finds the file already on disk. So a file reported "on disk" by
  the query *could* be purged shortly after if dCache is under
  pressure. For long gaps between check and use, re-check.
- **Multi-dataset job inputs (e.g. mix stages):** form one merged
  prestage request — `mdh prestage-files <DS1> <DS2> ... <DSN>`
  walks tape volumes once per volume, not once per dataset. The
  wiki cites MDC2020Dev mixing as the canonical case: 14 datasets
  in one request finished in ~1 hour vs. 14 separate hour-long
  prestages.
- **`samSplit` for >100k files:** creates `${USER}_${TAG}_X`
  subset definitions. Run one prestage per day (~100k/day cap).
- **The older SAM prestage path has a known bug (2023+):** SAM
  projects may stall near the end with a few files appearing
  hung. The fix is a station-restart ticket. Prefer the `mdh`
  path unless you specifically need a SAM dataset-definition
  workflow.

## Examples

Check first, then prestage if needed:
```
/prestage dts.mu2e.RPCExternal.MDC2025ap.art
```

Just check, don't pull:
```
/prestage --check-only dts.mu2e.CeEndpoint.MDC2025aj.art
```

Mixed-input prestage (single tape walk for all four datasets):
```
/prestage dts.mu2e.CeEndpoint.MDC2025aj.art \
          mix.mu2e.MuStops.MDC2025aj.art \
          mix.mu2e.PiStops.MDC2025aj.art \
          mix.mu2e.NeutralsFlash.MDC2025aj.art
```

Subset prestage from a file list:
```
/prestage --file /tmp/needed_files.txt
```

Legacy SAM path for an existing dataset definition:
```
/prestage --legacy-sam oksuzian_celike_chunk_0
```
