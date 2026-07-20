# bp-078 — journal

## 2026-07-20 — minted at re-graduation (orchestrator, session-37, opus@high)

Re-graduated from `dn-plane-principals` (ratified `215070d`), which supersedes
`dn-ouroboros-principal` on warrant `finding-0116`. **bp-078 supersedes bp-076**
(three-place, `dn-supersession-lifecycle` shape): bp-076 was graduated from the
now-superseded two-principal note and, as written, would `chown`
`exhaust/reports/` `ouroboros`-write-only — re-introducing exactly finding-0116
(workflow can no longer place build reports). bp-076 flipped to `superseded`
(`superseded_by: bp-078`), stays inspectable; its journal's 8-point delta is the
checklist this plan discharges.

**All 8 deltas discharged:**
1. Four role accounts + shared group `palace` → §6 matrix, Item 6 runbook.
2. `exhaust/reports/` = `ouroboros-work` (finding-0116 fix) → §3 Q7, §6, Item 4/6.
3. Cockpit `sudo -u ouroboros-work -H claude` + credential grounding → §3 Q8/Q9
   (Q9 = THE sharp item, a legitimate spike; STOP-gate in §10 + Item 6), git
   signing under `-H` → §3 Q10.
4. pf anchor (block core off-host egress + lo0 carve-out) → §3 Q11, Item 3.
5. Shared-repo mechanics (setgid, `core.sharedRepository`, umask) → Item 6.
6. `data/` runtime ownership → §3 Q12 (decision: `chown` not relocate), Item 4/6.
7. Ambassador relocation → **DEFERRED** (§3 Q13, §9, §11): entangled with the
   `data/handoff`-inside-`data/` grounding and a zone-crossing code move; the
   `ouroboros-edge` USER is still created (forward-provision). Re-entry parked.
8. Per-plane ratchets (self-configuring skip/enforce) → Item 5.

**Grounding done at re-graduation (§3):** carried bp-076's launcher grounding
intact (Q1–Q3, Q5, Q6 unchanged by the four-user generalization). New:
- **Q10 (sharp catch):** git signing is currently GLOBAL, not repo-local —
  `user.signingkey=/Users/ascalva/.ssh/id_ed25519.pub`, `gpg.format=ssh`,
  `commit.gpgsign=true` in `~/.gitconfig`. Under `sudo -u … -H`, HOME changes and
  the global config is NOT read → signing silently breaks. This confirms the
  note §3.2 "repo-local, HOME-independent" prescription is *necessary*, not tidy,
  and pins the accepted residual to a concrete path (`ouroboros-work` reads
  `/Users/ascalva/.ssh/id_ed25519` or ssh-agent).
- **Q12:** `data/` is the daemon's live sink — four plists → `data/logs/*`
  (`com.mind-palace.palace.plist:60,63` + token-rotate/backup/vault) and
  `data/runs.sqlite` (`ops/lifecycle/runs.py:10`). Decision: `chown` to
  `ouroboros:palace`, not relocate; cockpit tails as a group reader
  (`cockpit.sh:26`).
- **Q13:** `interface.handoff_dir = "data/handoff"` is INSIDE `data/`
  (`config/defaults.toml:128`); the ambassador is wired in the daemon
  (`launcher.py:149-152`). The note's `palace-io` airlock split only pays off
  once edge is a distinct uid → why the relocation defers cleanly.

**BUILDER DISCIPLINE (loud):** this build performs NO migration step. Every
mutating act is owner-run from Item 6's runbook. The builder writes code + an
inert pf anchor + docs + tests that SUPPORT and PROVE the move; it never creates
a user/group, chowns, or touches launchd/keychain/pf/`.git/config`/Syncthing.
The finding-0118 lesson is baked into Item 4's invariant: exercise
`uv run scripts/verify_planes.py` end-to-end, not just the imported fns.

Est. 250k, opus@high (owner-set for the trust-boundary weight). If it doesn't fit
one session, file `spec-defect` and re-graduate — do NOT re-split mid-build.

Status: `proposed`. Awaiting the owner's `palace bless bp-078` + hand commit
(proposed→ready is owner-only, by hand).
