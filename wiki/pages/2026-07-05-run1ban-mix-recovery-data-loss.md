---
title: Run1Ban NoPrimaryMix1BB recovery data loss (54 outputs)
tags: [incident, run1b, mixing, recovery, pushoutput, sam, dcache]
sources: []
updated: 2026-07-09
---

# Run1Ban mix recovery data loss — 54 outputs (Jul 2026)

**Dataset:** `dig.mu2e.NoPrimaryMix1BB.Run1Ban_best_v1_4-000.art` — 19,946/20,000
files in SAM. Siblings hit too: CeEndpointMix1BB −1, FlateMinusMix1BB −1,
FlatGammaMix1BB −1, CosmicCRYAllMix1BB −5 (**62 missing campaign-wide**).
**Investigated 2026-07-09** (session with full SAM-forensics trail; exemplar
file `001470_00016543`).

## Mechanism (four layers)

**L1 — exposure engine (bookkeeping loophole).** POMS `sim_drain` recovery
re-queued *completed* indices campaign-wide, repeatedly. Round map from log
create-dates (log-name epochs = job end times): Jun 28/29/30: 218/6,506/32,208
logs (originals + first recovery storm), Jul 1: 3,598, Jul 4: 916, Jul 5: 7,456,
Jul 6: 431. 51,333 logs for 20,000 outputs. User closed this loophole in the
metacat-era submission system.

**L2 — destructive re-run design (pushOutput).** OfflineOps v00_04_02
`pushOutput` `checkTimes`/`recover`: a job that finds its output already
existing checks the file age against **`recoverDelay = 3600` s (one hour)**.
Older → treated as a dead job's leftover: `gfal-rm` + `retireSam` + rewrite +
re-declare. Younger → exit 3 (*"this job must fail, to cause continued
recoveries"*) — which keeps POMS retrying until the age gate opens. Net effect
with L1: **6,240 needless delete+rewrite cycles of good data** (records ever =
19,946 active + 6,293 retired = 26,239; originals declared = 19,999 — index
8470 never declared anything; re-declares = 6,240; retires = 6,240 paired + 53
dangling = 6,293 ✓). Index 16366 was clobbered **twice in one round** (records
created Jun 29 23:54 → retired Jul 5 01:01; created 01:01 → retired 03:46 —
a 2h45m-old verified rewrite deleted again; created 03:46 → lost).

**L3 — the actual loss (off-grid, dCache-side).** The 53 lost files are exactly
the rewrites whose *final* write landed in **[Jul 4 23:30 – Jul 5 00:19 UTC]**
(+1 at 03:46) — the first wave of the last big round. Each was CRC-verified
against dCache and SAM-declared (pushOutput exit 0; verified in logs). They then
**physically vanished from dCache between Jul 5 and Jul 9 with zero SAM
activity**: none of the 53 records was ever retired by a grid job (all
grid-side retires in the dataset are paired with re-declares at grid times),
and no jobs ran after Jul 6. Victims are index-clustered (12829–13346,
17321–18003 — same submission batches) and interleaved minute-by-minute with
surviving rewrites (~5–10 % in-window casualty rate). Leading hypothesis: a
dCache write-pool lost its **unflushed** replicas (rewritten files need a fresh
tape flush; the originals' tape copies died with their retired file-ids), with
namespace entries cleaned up afterwards; alternative: an external cleanup
script deleted the paths. **dCache billing / ops incident records for ~Jul 5
00:20–04:00 decide** — no SAM-side data can.

**L4 — visibility (the mop-up sweep).** On **2026-07-09 21:59:26–33 UTC**
(16:59 CDT) an off-grid sweep retired all 53 dangling records in one
sorted-by-sequencer burst (~7 records/s). SAM `Retired Date` is faithful
(calibrated: job-1's record shows retire at Jul 4 23:32:36, matching the
recovering job's `Removed` log line to the second). The sweep touched only the
danglers. This is why the dataset now shows clean "missing" instead of dangling
records. Identify what cron/script ran at 16:59 CDT on 2026-07-09.

## Why "two jobs with the same index, both declaring success"

By design under L1+L2: the second job is a recovery re-run of a completed
index; it deletes the >1h-old good output and rewrites it, then declares
success. Both logs look normal because both *were* normal for their code paths.
There is **no third grid job** for the lost indices (only-2-logs verified via
parentage and index-name join for all 54): the "third actor" is off-grid —
the L3 file remover plus the L4 record sweep. A crashed/killed grid job leaves
no log in SAM (the log is pushed last), but it also could not have caused this:
grid-side deletion (`recover()`) retires the record 1–2 s after the `rm`, and
none of the 53 records shows a grid-time retire.

## Evidence trail (reproducible queries)

- Retired records: `samweb list-files --fileinfo "file_name <fn> with
  availability retired"`; per-id dates via `samweb get-metadata <file_id>`.
- Exemplar 16543: rec 106262575 created Jun 29 21:15:42, retired Jul 4
  23:32:36 (by the recovering job — matches its log); rec 106440575 created
  Jul 4 23:32:38 (size matches the rewrite in the job workdir listing),
  retired **Jul 9 21:59:30 by the sweep**; physical path absent.
- Round map: `count-files "dh.dataset=log.… and create_date >= 'D' and
  create_date < 'D+1'"`.
- Index↔sequencer map: frozen input list in the cnf's `jobpars.json`
  (`tbs.inputs`), local index = line number; log names are
  `<local-index>-<end-epoch>`.
- The 54: one (`001470_00000000`, idx 8470) never declared any record in any
  round (infant mortality, plain re-run); the other 53 are the L3 victims.

## Sequencers lost (dig.mu2e.NoPrimaryMix1BB.Run1Ban_best_v1_4-000)

001470_00000000 (never produced) plus:
00002342 00002576 00002747 00002800 00002866 00002904 00003056 00003144
00003204 00015975 00016014 00016020 00016113 00016123 00016152 00016158
00016164 00016245 00016254 00016290 00016326 00016354 00016359 00016366
00016380 00016401 00016413 00016424 00016492 00016511 00016538 00016543
00016544 00016580 00016600 00016659 00016728 00016741 00016743 00016760
00016769 00016814 00016818 00016830 00016843 00016883 00016909 00016966
00016975 00017158 00017258 00017645 00017675 (all run 1470)

## Fixes / follow-ups

1. **L1 closed** by the user in the metacat-era submission control (verify
   before resubmit). This alone removes ~all exposure.
2. **Make `recover()` non-destructive**: `checkTimes` already fetches the
   dCache CRC — compare it to the SAM/local metadata checksum and **skip the
   rewrite when the existing file is good**, instead of age-gating.
   Delete-before-rewrite must go (write-temp-then-rename, or rm only after the
   replacement is verified+declared). `recoverDelay=3600` is shorter than
   normal tape-flush latency — even granting the design, it guarantees
   double-clobber between rounds >1 h apart.
3. **Ask dCache ops / billing** about deletions or pool incidents covering the
   53 paths, window Jul 5 00:20–04:00 (create times above); this pins L3.
4. **Identify the 16:59 CDT Jul 9 sweep** (benign mop-up, but should be a
   known actor).
5. **Re-run the 54** — deterministic cnf ⇒ physics-identical outputs (not
   byte-identical: embedded timestamps). Targeted submission of 54 indices;
   avoid the POMS drain path until L1-fixed tooling is in use.
6. Same audit for the 4 sibling datasets (−8 files, likely same window).

## Related

- [[poms-reference]] — the recovery machinery involved
- [[justin-vs-prodtools]] — "recovery as a property" contrast; justIN's
  file-state reset avoids clobber-recovery entirely
- [[predictive-naming-proposal]] — expected-vs-produced accounting would have
  caught the loss immediately (54 predicted names with no files)
- [[metacat-reference]] — the successor stack whose submission control closes L1
