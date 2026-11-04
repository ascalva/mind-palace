module

public import Palace.Magnetic.Defs
public import Palace.Balance.Defs

/-!
# The magnetic Laplacian's ground in the code: BRG-7, the statements

`docs/design-notes/magnetic-laplacian.md` §2.1 grounds the deferred operator in code the palace
already runs: its `θ = 0` fiber is `laplacian.py`'s `laplacian`, its fiber with phase `π` on the
negative entries is `signed_laplacian`, and LAP-5's balance theorem is its kernel theorem with
structure group ℤ/2.

These are the theorems of `Palace/Magnetic.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as
stated here, from the standard axioms alone. The note's other results are proved in the same file
and cited from the note; no code relies on them yet, so the ledger has no row for them.
-/

@[expose] public section

open Matrix

namespace Palace.Magnetic

variable {V : Type*}

section Fibers

variable [Fintype V] [DecidableEq V]

/-- **BRG-7** At `θ = 0` the magnetic Laplacian is the Laplacian `D − A`: `q = 0` is the built
operator, exactly. -/
theorem magLap_zero (w : Matrix V V ℝ) :
    magLap w (fun _ _ ↦ 0) = (lap w).map Complex.ofReal := sorry

/-- **BRG-7** With weights `|A|` and phase `π` on the negative entries, the magnetic Laplacian is
the signed Laplacian `D̄ − A`: the transports are the signs. -/
theorem magLap_signPhase (A : Matrix V V ℝ) :
    magLap (A.map abs) (signPhase A) = (signedLap A).map Complex.ofReal := sorry

end Fibers

/-- **BRG-7** LAP-5's balance theorem is the kernel theorem with structure group ℤ/2: on a
connected support, a symmetric signed matrix is balanced iff the connection with phase `π` on
its negative entries is flux-trivial and no self-loop is negative. -/
theorem balanced_iff_fluxTrivial_signPhase [Finite V] (A : Matrix V V ℝ) (hA : A.IsSymm)
    (hc : (support A).Connected) :
    Balanced A ↔ FluxTrivial (support A) (signPhase A) ∧ ∀ u, 0 ≤ A u u := sorry

end Palace.Magnetic
