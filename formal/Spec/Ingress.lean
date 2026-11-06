module

public import Palace.Ingress.Defs

/-!
# The ingress, the statements

The laws of `Palace/Ingress.lean` the ledger cites (docs/LAWS.md §XII, ING-1 and ING-7), each with
its proof left as `sorry`, over the keyed model of `Palace/Ingress/Defs.lean`. `lake comparator`
checks that the `Palace` library proves each one exactly as stated here, from the standard axioms
alone. What the statements cover: admissibility of a command as `core/sentence/types.py` requires
it, the write bit on a plane above the clause's scope, and the Ambassador's grant as written
(ING-1); and the landing order the code keeps, the idempotence key written last, so a run
interrupted after any step converges under re-run, in the model's stage order and in any order of
the steps before the key (the code writes the version row before the attestation), with the
controls that a key written while some of the command's rows are not held, first or after the
plane's rows as the audit's defect 1 wrote it, is never repaired (ING-7). The other laws of the
family (ING-2, 3, 5, 6 and 8 to 12) stay design theorems of `Palace/Ingress.lean` until code relies
on them.
-/

@[expose] public section

open Finset

namespace Palace.Ingress

variable {R D G : Type*} [DecidableEq R] [DecidableEq D] [DecidableEq G]

open Palace.Query in
/-- **ING-1** A command is admissible under a grant iff a granted plane lies above its scope, at its
clock and window, and carries the write bit. -/
theorem command_admissible_iff_write {Rg H : Type*} (g : List CQ.Scope) (c : Clause)
    (hc : IsCommand c) :
    Sentence.Admissible g (Sentence.clause c : Sentence Rg H)
      ↔ ∃ p ∈ g, c.req.Le p ∧ p.authority.storeWrite = 1 :=
  sorry

open Palace.Query in
/-- **ING-1** A read-only grant admits no command. -/
theorem readonly_admits_no_command {Rg H : Type*} (g : List CQ.Scope)
    (hg : ∀ p ∈ g, p.authority.storeWrite = 0) (c : Clause) (hc : IsCommand c) :
    ¬ Sentence.Admissible g (Sentence.clause c : Sentence Rg H) :=
  sorry

/-- **ING-1** The Ambassador's grant as written admits a projection-event command on the mirror:
its first plane carries the write bit there (dn-ingress D2). -/
theorem ambassador_admits_projection_command :
    CQ.admits CQ.ambassador (commandScope {.mirrorAuthored} .projectionEvent) :=
  sorry

/-- **ING-1** The Ambassador's grant as written refuses a commit-clock command: its commit plane
carries no write bit, and the order is false across clocks (dn-ingress D2, §8). -/
theorem ambassador_refuses_commit_command :
    ¬ CQ.admits CQ.ambassador (commandScope {.reference} .commit) :=
  sorry

/-- **ING-7** With the key written last, a fresh run interrupted after any step converges: the next
run lands exactly the uninterrupted run's state. -/
theorem ingest_prefix_converges (x : Source R D G) (s : State R D G) (hs : Fresh x s) (k : ℕ) :
    ingest x (run (x.steps.take k) s) = ingest x s :=
  sorry

/-- **ING-7** In the code's order: the code writes a version row before an attestation, which the
model's stage order does not; a fresh run that stopped after any of its steps but its key, in any
order and any number of times, converges under re-run all the same. The key last is all the law
needs. -/
theorem ingest_after_nonkey (x : Source R D G) (s : State R D G) (hs : Fresh x s)
    (w : List (Step R D G))
    (hw : ∀ a ∈ w, a = Step.land x.ident x.digest ∨ ∃ t ∈ x.stages, a = Step.rows t) :
    ingest x (run w s) = ingest x s :=
  sorry

/-- **ING-7** The control at its extreme: with the key written first, a run interrupted right after
it is never repaired, since the next run reads the key and lands nothing. -/
theorem key_first_does_not_converge (x : Source R D G) (s : State R D G) (hs : Fresh x s)
    (hx : ¬ x.rows ⊆ s.rows) :
    ingest x (run (x.stepsKeyFirst.take 1) s) ≠ ingest x s :=
  sorry

/-- **ING-7** The control in the audit's defect 1's own order: a key written after some steps, the
plane's rows in the defect, and before the attestation and the version row, the run interrupted
right after it, is never repaired when some of the command's rows are not yet held, since the
next run reads the key and lands nothing. -/
theorem key_early_does_not_converge (x : Source R D G) (s : State R D G) (hs : Fresh x s)
    (v : List (Step R D G)) (hx : ¬ x.rows ⊆ (run v s).rows) :
    ingest x (run (v ++ [Step.key x.ident x.digest]) s) ≠ ingest x s :=
  sorry

end Palace.Ingress
