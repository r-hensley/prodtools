---
title: prodtools — Product Requirements Document (descriptive)
tags: [reference, overview, prd, prodtools]
sources: []
updated: 2026-05-05
---

# prodtools — Product Requirements Document

A descriptive PRD: **what prodtools is today**, who uses it, what it
integrates with, and what's in flight. Not a forward-looking strategy
document — for current decisions in progress see the ADR-style
proposal pages cross-linked under §10.

This is a synthesis, not a source of truth. CLI flags live in
`EXAMPLES.md` (regenerated from code via `/refresh-examples`); the
staging-config model lives in [[json2jobdef-staging-workflow]];
operational gotchas live in per-project memory. This page links them
into one shape.

## 1. Problem statement

Mu2e production runs a multi-stage Offline simulation/reconstruction
chain per campaign (primary → digi → mix → reco → evntuple, plus
pileup resamplers and merge filters), each producing SAM-registered
artifacts that feed the next stage. **g4bl** (Geant4 Beamline) is a
separate beamline-simulation tool that prodtools also schedules; it
runs `g4bl` natively on AL9 via `spack load g4beamline` (not
`mu2e -c`, no SL7/apptainer wrap since commit `401e3da`) and emits
`.root` output. No other `data/<campaign>/<stage>.json` consumes
g4bl outputs as input today — treat g4bl as a parallel pipeline, not
stage 0 of the Offline chain. Each stage has dozens of
parameter knobs (FCL overrides, pileup datasets, dsconf calibration
versions, simjob releases, output locations, dCache token scopes).
Doing this by hand at the FCL level is impractical and error-prone.

**prodtools** is the Mu2e team's command-line system for turning
per-stage JSON config catalogs into POMS-dispatched grid jobs that
write to production SAM. It also bundles the introspection,
monitoring, recovery, and data-movement utilities the production team
uses around that core flow.

## 2. Users (personas)

**P1 — Production operations lead** (runs as `mu2epro` via `ksu`).
Manages live campaigns, pushes new stages to POMS maps, monitors
completeness, allocates or extends `MDC2025-NNN.json` maps, runs
`mkidxdef --prod` for SAM index defs, handles failure recoveries.
Primary skills: `/mu2epro-run`, `/poms-push`, `/recent-datasets`.

**P2 — Individual physicist / analyst** (runs as their FNAL.GOV
account). Drafts new stage entries in `data/<campaign>/*.json`,
generates cnfs locally for smoke tests, runs `mu2e -c` against tape
inputs to validate, debugs FCL behavior. Never touches production
SAM directly. Primary skills: `/mu2e-run`, `/stage-entry`,
`/wiki-query`.

**P3 — Tool developer** (FNAL.GOV account, with commit access to
`Mu2e/Production` and to this repo). Maintains `bin/`, `utils/`, the
JSON schema, the `EXAMPLES.md` regeneration pipeline, the staging
workflow docs, the wiki. Primary skills: `/refresh-examples`,
`/wiki-ingest`, `/wiki-update`, `/wiki-lint`, `/parallel-audit`.

## 3. Goals

- Turn `data/<campaign>/<stage>.json` entries into SAM-declared cnf
  tarballs and POMS-dispatchable map files with one CLI call.
- Make the **same JSON** drive every stage of the chain (g4bl →
  evntuple), so a campaign is editable as a coherent whole.
- Insulate physicists from POMS internals: only the production lead
  needs to know map numbers, dropbox paths, or `mkidxdef`.
- Capture per-stage gotchas (calibrations, simjob version drift, token
  scopes) as memory + wiki rather than tribal knowledge.
- Let new stages be added by example: copy an existing entry, edit
  it, run `/stage-entry`.

## 4. Non-goals (today)

- Replacing POMS dispatch logic itself (under exploration in §10's
  Phase 2 work; not currently a goal of the prodtools repo).
- Owning the FCL physics — `Production/JobConfig/*` lives upstream in
  `Mu2e/Production`. prodtools only assembles parameter overrides
  and references those FCLs.
- Owning the SimJob releases — those ship via cvmfs from
  `Mu2e/Production` PRs.
- Web UI for end users — `pomsMonitorWeb` exists but is operational
  scaffolding, not a product surface.

## 5. Capabilities (commands)

**Config creation:**
`json2jobdef`, `jobdef`. The first reads a per-stage
JSON and emits one `cnf.*.tar` per `input_data` element (plus a
`jobdefs_list.json` summary); it expands array-valued template fields
into the parameter cross-product internally. `jobdef` is the low-level
direct-flag form for one-offs.

**Introspection:**
`jobfcl`, `fcldump`, `jobquery`, `mkidxdef`, `datasetFileList`,
`listNewDatasets`, `latestDatasets`. These resolve a cnf or dataset
name into FCL text, parent files, SAM coverage, or recent-activity
listings.

**Monitoring:**
`pomsMonitor` (SQLite-backed POMS-state cache), `pomsMonitorWeb`
(Flask dashboard), `famtree` (parentage Mermaid/PNG diagrams),
`logparser` (per-dataset CPU/mem aggregates), `genFilterEff`
(Proditions-table generation efficiency).

**Execution:**
`runmu2e` (worker entry — runs one job from a `jobdefs_list.json`
slot). `submit_map` (driver that turns a jobdefs list into grid
submissions; supports `mu2ejobsub` and direct `jobsub_submit`
backends, the latter in flight per §10).

**Recovery & data movement:**
`mkrecovery` (build SAM defs over missing files for a re-run),
`copy_to_stash` (push to StashCache or resilient dCache).

Every command above is documented in `EXAMPLES.md` (canonical CLI
reference, ~830 lines, regenerated from source).

## 6. Capabilities (Claude Code skills)

`.claude/commands/*.md` — slash skills wrapping the commands with
sensible defaults and account/env discipline:

| Skill | Purpose |
|---|---|
| `/mu2e-run` | Source the Mu2e env + SimJob and run a prodtools command as the user. |
| `/mu2epro-run` | Same, as `mu2epro` via `ksu` in `/tmp` workdir. Required for `--prod`/`--pushout`. Warns before destructive flags. |
| `/stage-entry` | Validate a stage name + dispatch `json2jobdef --json data/<campaign>/<stage>.json` with selectors. |
| `/poms-push` | Plan a production push (extend existing map vs allocate new) before delegating to `/mu2epro-run`. |
| `/refresh-examples` | Regenerate `EXAMPLES.md` from current code against `docs/EXAMPLES_schema.md`. |
| `/wiki-init`, `/wiki-ingest`, `/wiki-query`, `/wiki-update`, `/wiki-lint` | Operational-knowledge stewardship. |
| `/parallel-audit` | Spawn N parallel Explore agents on independent slices, synthesize a punch list. |
| `/retire-file` | Produce the (mu2epro) command to retire a SAM file + remove from dCache. |
| `/recent-datasets` | List recent datasets with completeness; sources `pyenv ana` for the SQLAlchemy-using path. |

## 7. Core data flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Author edits data/<campaign>/<stage>.json                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │  /stage-entry  or  /mu2e-run json2jobdef
┌──────────────────────▼──────────────────────────────────────────┐
│ cnf.mu2e.<desc>.<dsconf>.<idx>.tar  +  jobdefs_list.json         │
│ (one cnf per input_data element, cross-product expansion)        │
└──────────────────────┬──────────────────────────────────────────┘
                       │  jobfcl + mu2e -c    ← local smoke
                       │  /poms-push → /mu2epro-run json2jobdef --prod
┌──────────────────────▼──────────────────────────────────────────┐
│ pushOutput: cnf → /pnfs/.../phy-etc/cnf/...   (SAM-registered)   │
│ jobdefs appended to MDC2025-NNN.json POMS map                    │
│ mkidxdef --prod recreates iMDC2025-NNN SAM index                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │  POMS scan
┌──────────────────────▼──────────────────────────────────────────┐
│ submit_map  →  jobsub_submit  →  HTCondor workers                │
│ runmu2e on worker → mu2e -c → outputs → pushOutput → SAM         │
└──────────────────────┬──────────────────────────────────────────┘
                       │  outputs become input_data of next stage
                       ▼
            (primary → digi → mix → reco → evntuple)
            + parallel: resampler_beam, resampler_stm, merge_filter
```

**g4bl runs a separate path:** `data/mdc2025/g4bl.json` →
g4bl runner (native AL9, spack-loaded `g4beamline`, not `mu2e -c`)
→ `.root` output (e.g. `nts.mu2e.G4blPOT.*.root`). Architecture
detail in [[g4bl-runner]] (current state + the `401e3da` SL7-removal
diff). No `data/<campaign>/<stage>.json` references g4bl outputs as
input, so within prodtools' visibility g4bl outputs are terminal.
Whether/how downstream tools outside this repo consume them is not
documented here.

For per-stage entry shapes, dsconf flow, and the DbService /
SimJob-version rules: [[json2jobdef-staging-workflow]].

## 8. External integration surface

| System | Role | Touchpoint |
|---|---|---|
| **SAM** | File catalog, dataset defs, parentage | `samweb` CLI + `samweb_client` Python |
| **MetaCat** | Successor data catalog (MQL queries) | CLI + read-only MCP server (commissioned 2026-04-24); see [[metacat-reference]] |
| **POMS** | Campaign/stage orchestration, dispatch | `poms_client` library + dropbox at `/exp/mu2e/app/users/mu2epro/production_manager/poms_map/`; see [[poms-reference]] |
| **dCache** | File store: tape / persistent / scratch / resilient | `mdh`, `gfal-*`, xrootd; bearer-token scoped per (area, owner-class, tier, owner) — see memory `reference_dcache_token_scopes.md` |
| **cvmfs** | Read-only software (`Musings/SimJob/<release>`, `Offline`, `DataFiles/*`) | sourcing scripts, FCL `#include`, `dir:/cvmfs/...` input locations |
| **htvault / htgettoken** | Bearer-token issuance | `htgettoken -a htvaultprod.fnal.gov -i mu2e`; tokens at `/run/user/<uid>/bt_u<uid>` and `/tmp/bt_token_mu2e_*` |
| **mu2ejobsub / jobsub_lite** | HTCondor submission backend | Phase 1 = Perl `mu2ejobsub` shim; Phase 2 = direct `jobsub_submit` (in flight, §10) |
| **GitHub** | Source for Offline, Production, aitools | Out-of-band PRs that ship to cvmfs via Fermilab publishing; prodtools only consumes |

## 9. Accounts, auth, environment

**Accounts:**
- **User account** (e.g. `oksuzian@FNAL.GOV`) — kerberos via FNAL.GOV; reads everywhere; cannot push to production SAM, write the POMS dropbox, or own `mu2e`-namespaced datasets.
- **`mu2epro@FNAL.GOV`** — production identity reached via `ksu mu2epro` (requires `~mu2epro/.k5users` membership). Owns SAM writes and the POMS dropbox. Memory rule: **never run `htgettoken` for `mu2epro`** (`feedback_never_get_mu2epro_token.md`); the production token is provisioned out-of-band at `/tmp/bt_token_mu2e_production_<uid>`.

**Auth:** Bearer tokens (htvaultprod.fnal.gov) — Mu2e migrated off
`voms-proxy-init` (`feedback_no_voms_proxy_init.md`). Scopes are
narrowly pre-allocated per (area, owner-class, tier, owner); `--need-storage-modify`
in jobsub args derives them from cnf output filenames automatically.

**Environment setup chain** (in order):
```
source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh
muse setup ops
muse setup SimJob <release>           # e.g. MDC2025am
setup OfflineOps                      # adds pushOutput; needed for --pushout / --prod
pyenv ana                             # only for SQLAlchemy-using tools (pomsMonitor, listNewDatasets --completeness)
```
Gotchas: `SPACK_ENV` set by `muse setup ops` blocks `spack load` in
later subprocesses (`reference_spack_env_after_muse_setup.md`).

**File-path conventions:**
- Code: `/exp/mu2e/app/users/<user>/...`
- POMS maps: `/exp/mu2e/app/users/mu2epro/production_manager/poms_map/MDC2025-NNN.json`
- Tape: `/pnfs/mu2e/tape/phy-{sim,dat,etc,nts}/<tier>/mu2e/<desc>/<dsconf>/...`
- Persistent (cnf, ntuples): `/pnfs/mu2e/persistent/datasets/phy-{sim,etc,nts,dat}/...`
- Scratch: `/pnfs/mu2e/scratch/users/<user>/...`
- Tokens: `/tmp/bt_token_mu2e_*`, `/run/user/<uid>/bt_u<uid>`

## 10. In-flight work (roadmap signals)

ADR-style proposal pages live in `wiki/pages/`:

- [[2026-04-29-remove-poms-from-submit-loop]] — phased plan to drop POMS from the submit loop. Phase 1 = Python `submit_map` + local SQLite state, keeps `mu2ejobsub`. Phase 2 = drop `mu2ejobsub`, drive `jobsub_submit` directly.
- [[2026-04-30-phase2-direct-jobsub-implementation]] — concrete Phase 2 plan: `utils/runjob.py` worker (uses `jobfcl`/`jobiodetail`/`push_data`), `utils/jobsub_argv.py` argv builder, `--backend direct` in `submit_map`. Driving win: per-job pushOutput SAM registration on the worker.
- [[2026-04-21-fold-pbi-into-json2jobdef]] — retired the standalone `gen_pbi_sequence` tool by adding `split_lines` and `chunk_mode` input_data shapes.
- [[2026-04-21-extend-jobdef-per-index-overrides]] — `event_id_per_index` enabling per-index linear `offset + index × step` overrides for any FCL key.

Untracked WIP files (`git status`): `utils/submit.py`,
`utils/jobsub_argv.py`, `bin/runjob.sh`, `bin/submit_map`,
`bin/latestDatasets`, `utils/latestDatasets.py`, the
`/stage-entry` skill, the new staging-workflow wiki page,
`data/mdc2030/` (new campaign folder, not yet populated).

Phase 2 direct submission has been validated end-to-end as `oksuzian`
under POMS; production cutover is the open question. See memory
`reference_phase2_direct_submit.md`.

## 11. Operational gotcha categories

(Each links to one or more memory entries — consult them, not this
list, for specifics.)

| Category | Examples |
|---|---|
| Token scope mismatches | `reference_dcache_token_scopes.md`; stale Analysis token used for tape reads observed 2026-05-05 |
| Calibration `EMPTY -1/-1/-1` | `reference_reco_dbservice_overrides.md`; reco entries need explicit `Sim_best`/`v<N>` |
| SimJob version drift | `reference_mdc2025aj_trig_config_drift.md` (mix broken on aj); `reference_mdc2025am_reco_verified.md` (am clean for reco); `feedback_latest_simjob_in_new_entries.md` (forward-only "latest" rule) |
| PBI source-param compatibility | `reference_pbi_event_offset_prs.md`; pre-aj musings reject `firstSubRunNumber`/`firstEventNumber` |
| Spack env conflicts | `reference_spack_env_after_muse_setup.md` |
| `json2jobdef --index` semantics | `reference_json2jobdef_index_is_flat.md`; flat input position, not entry index |
| g4bl `param -unset` no-ops | `reference_g4bl_param_unset_semantics.md` |
| No-fallbacks discipline | `feedback_no_fallbacks.md` |

## 12. Repository layout

| Path | Contents |
|---|---|
| `bin/` | Executable wrappers — one per command in §5 plus shell helpers (`setup.sh`, `runjob.sh`, `install_prodtools.sh`). |
| `utils/` | Python implementations behind the wrappers (`json2jobdef.py`, `runmu2e.py`, `samweb_wrapper.py`, etc.). |
| `data/<campaign>/*.json` | Per-stage entry catalogs — the source of truth for what gets generated. Campaigns: `mdc2020`, `mdc2025`, `mdc2030`, `Run1B`. |
| `fcl/` | FCL fragments / staging / smoke-test FCLs. |
| `poms/` | POMS submit configs (`main.cfg`, `prolog.cfg`, `fermigrid.cfg`); `g4bl.cfg` retired 2026-04-28 once g4bl gained native AL9 spack. |
| `wiki/` | Operational wiki — `pages/`, `raw/`, `index.md`, `log.md`, `overview.md`, `SCHEMA.md`. |
| `docs/` | `EXAMPLES_schema.md` (source for the regenerated reference) plus the `EXAMPLES.md` artifact. |
| `.claude/commands/` | Slash-skill definitions (§6). |
| `test/` | Parity tests — byte-for-byte equivalence vs the Perl reference; requires SimJob env. |
| `web/` | `pomsMonitorWeb` Flask app + static. |
| `CLAUDE.md` | Repo-level instructions for Claude Code (consult `EXAMPLES.md` first; use `/mu2e-run` vs `/mu2epro-run`; memory + wiki discipline). |

## 13. Open questions

- **Phase 2 cutover criteria.** What's the threshold for switching production from `mu2ejobsub` to direct `jobsub_submit`? Currently shadow-validated per `reference_phase2_direct_submit.md`; no formal go/no-go.
- **Cross-purpose POMS map extension.** `MDC2025-025` was extended on 2026-05-05 to hold an unrelated MDC2025am reco campaign alongside the PBI chain. The "extend in place" rule (`feedback_extend_existing_poms_map.md`) was scoped to "later stages of the same workflow" — we now have a precedent for cross-purpose extension; convention should be revisited.
- **MetaCat migration depth.** Read-only MCP is in place; how much of `samweb_wrapper.py` should migrate to `metacat_client`?
- **Pre-existing broken wiki slugs** flagged in lint reports since 2026-04-22: `[[2026-04-21-pbi-sequence-implementation]]` and `[[2026-04-24-mu2e-aitools-skills]]`. Either publish synthesis pages or scrub the references. (Third historical slug, `run1bai-campaign`, was a typo for [[run1bak-campaign]] and has been corrected.)

## Related

- [[json2jobdef-staging-workflow]] — staging-config model in detail
- [[poms-reference]] — POMS data model + lifecycle
- [[metacat-reference]] — samweb→metacat bridge, MQL
- [[pbi-sequence-workflow]] — concrete deep-dive on one stage chain
- [[input-data-chunk-mode]], [[input-data-dir-shape]] — input_data shapes
- `EXAMPLES.md` (root) — canonical CLI reference
