module

public import Palace.Superconnection
public import PalaceTest.Attack
public meta import Palace.Superconnection
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Superconnection`

The Plausible attacks and negative controls for `Palace/Superconnection.lean`, run on exact shadows
over ℤ on `Fin 3`: note maps from lists, citation relations without loops from bits, cochains from
lists of integers. The transports, the coboundary and the divergence are the model's, transcribed
over ℤ; each control is a nearby false law that an attack of the same shape must refute. They run
when this module builds (`lake test`).
-/

@[expose] public section

namespace Palace.Transport.Attack

/-- The notes of one time, in order. -/
def notes : List (Fin 3) := List.finRange 3

/-- A note map from a list. -/
def mapOf (l : List (Fin 3)) (a : Fin 3) : Fin 3 := l.getD a.val 0

/-- A permutation of the notes, the `k mod 6`th. -/
def permOf (k : ℕ) : Fin 3 → Fin 3 :=
  [![0, 1, 2], ![0, 2, 1], ![1, 0, 2], ![1, 2, 0], ![2, 0, 1], ![2, 1, 0]].getD (k % 6) ![0, 1, 2]

/-- A citation relation from bits, without loops. -/
def relOf (bs : List Bool) (u v : Fin 3) : Bool := bs.getD (3 * u.val + v.val) false && u != v

/-- A citation relation with the image of another added: the citations `σ` carries forward, so
that `σ` satisfies F1 from `X`. -/
def withImage (σ : Fin 3 → Fin 3) (X Y : Fin 3 → Fin 3 → Bool) (u' v' : Fin 3) : Bool :=
  Y u' v' || (u' != v' && notes.any fun u ↦ notes.any fun v ↦ X u v && σ u == u' && σ v == v')

/-- A note cochain from a list. -/
def vOf (l : List ℤ) (a : Fin 3) : ℤ := l.getD a.val 0

/-- An edge cochain from a list. -/
def eOf (l : List ℤ) (u v : Fin 3) : ℤ := l.getD (3 * u.val + v.val) 0

/-- The edge transport `mask X (pullEdge σ X' ψ)` over ℤ. -/
def tE (σ : Fin 3 → Fin 3) (X X' : Fin 3 → Fin 3 → Bool) (ψ : Fin 3 → Fin 3 → ℤ)
    (u v : Fin 3) : ℤ :=
  if X u v && X' (σ u) (σ v) then ψ (σ u) (σ v) else 0

/-- The coboundary read on the citations, `mask X (coboundary φ)`, over ℤ. -/
def dE (X : Fin 3 → Fin 3 → Bool) (φ : Fin 3 → ℤ) (u v : Fin 3) : ℤ :=
  if X u v then φ v - φ u else 0

/-- The divergence `div X ψ` over ℤ. -/
def divZ (X : Fin 3 → Fin 3 → Bool) (ψ : Fin 3 → Fin 3 → ℤ) (a : Fin 3) : ℤ :=
  (notes.map fun x ↦ (if X x a then ψ x a else 0) - (if X a x then ψ a x else 0)).sum

/-- Two edge cochains agree on every pair. -/
def sameE (f g : Fin 3 → Fin 3 → ℤ) : Bool := notes.all fun u ↦ notes.all fun v ↦ f u v == g u v

/-- `[d, τ] = 0` at a note cochain: the transport of the drop is the drop of the transport. -/
def commutes (σ : Fin 3 → Fin 3) (X X' : Fin 3 → Fin 3 → Bool) (φ : Fin 3 → ℤ) : Bool :=
  sameE (dE X fun a ↦ φ (σ a)) (tE σ X X' (dE X' φ))

/-- No citation restored: what `σ₀₂` carries to the last time `σ₀₁` carried to the middle one. -/
def noRestore (σ₀₁ σ₀₂ : Fin 3 → Fin 3) (XA XB XC : Fin 3 → Fin 3 → Bool) : Bool :=
  notes.all fun u ↦ notes.all fun v ↦ !(XA u v && XC (σ₀₂ u) (σ₀₂ v)) || XB (σ₀₁ u) (σ₀₁ v)

/-- Undirected reachability on three notes: a path of at most two citations either way. -/
def reach (X : Fin 3 → Fin 3 → Bool) (u v : Fin 3) : Bool :=
  u == v || X u v || X v u || notes.any fun w ↦ (X u w || X w u) && (X w v || X v w)

/-- Every citation's ends stay in one component of the target's citations. -/
def connected (σ : Fin 3 → Fin 3) (X X' : Fin 3 → Fin 3 → Bool) : Bool :=
  notes.all fun u ↦ notes.all fun v ↦ !X u v || reach X' (σ u) (σ v)

/-- A note cochain constant on the components of `X`: a value per component, read at the least
note the component holds. -/
def onComponents (X : Fin 3 → Fin 3 → Bool) (l : List ℤ) (b : Fin 3) : ℤ :=
  vOf l (if reach X b 0 then 0 else if reach X b 1 then 1 else 2)

/-! ### Attacks -/

/- TRN-12: with the notes composing (F2) and no citation restored, the edge transports compose,
`τ₀₁ τ₁₂ = τ₀₂`. -/
#eval survives (∀ s01 s12 : List (Fin 3), ∀ xa xb xc : List Bool, ∀ ψ : List ℤ,
  noRestore (mapOf s01) (mapOf s12 ∘ mapOf s01) (relOf xa) (relOf xb) (relOf xc) = true →
    sameE (tE (mapOf s01) (relOf xa) (relOf xb) (tE (mapOf s12) (relOf xb) (relOf xc) (eOf ψ)))
      (tE (mapOf s12 ∘ mapOf s01) (relOf xa) (relOf xc) (eOf ψ)) = true) 288

/- TRN-12 control: F2 alone; a citation severed at the middle time and restored breaks it. -/
#eval refuted (∀ s01 s12 : List (Fin 3), ∀ xa xb xc : List Bool, ∀ ψ : List ℤ,
  sameE (tE (mapOf s01) (relOf xa) (relOf xb) (tE (mapOf s12) (relOf xb) (relOf xc) (eOf ψ)))
    (tE (mapOf s12 ∘ mapOf s01) (relOf xa) (relOf xc) (eOf ψ)) = true) 289

/- TRN-13: on a window whose transports carry every citation forward (F1, by construction) and
compose (F2), `𝔸` is flat: `[d, τ] = 0` on all three pairs and `τ₀₁ τ₁₂ = τ₀₂`. -/
#eval survives (∀ s01 s12 : List (Fin 3), ∀ xa xb xc : List Bool, ∀ φ ψ : List ℤ,
  let XA := relOf xa
  let XB := withImage (mapOf s01) XA (relOf xb)
  let XC := withImage (mapOf s12) XB (relOf xc)
  (commutes (mapOf s01) XA XB (vOf φ) && commutes (mapOf s12) XB XC (vOf φ) &&
    commutes (mapOf s12 ∘ mapOf s01) XA XC (vOf φ) &&
    sameE (tE (mapOf s01) XA XB (tE (mapOf s12) XB XC (eOf ψ)))
      (tE (mapOf s12 ∘ mapOf s01) XA XC (eOf ψ))) = true) 290

/- TRN-13 control: the middle time's citations not closed under the transport, so F1 can fail. -/
#eval refuted (∀ s01 s12 : List (Fin 3), ∀ xa xb xc : List Bool, ∀ φ ψ : List ℤ,
  let XA := relOf xa
  let XB := relOf xb
  let XC := withImage (mapOf s12) XB (relOf xc)
  (commutes (mapOf s01) XA XB (vOf φ) && commutes (mapOf s12) XB XC (vOf φ) &&
    commutes (mapOf s12 ∘ mapOf s01) XA XC (vOf φ) &&
    sameE (tE (mapOf s01) XA XB (tE (mapOf s12) XB XC (eOf ψ)))
      (tE (mapOf s12 ∘ mapOf s01) XA XC (eOf ψ))) = true) 291

/- TRN-14, the class: when every citation's ends stay in one component of the target, the
curvature vanishes on the target's locally constant note cochains. -/
#eval survives (∀ s : List (Fin 3), ∀ xa xb : List Bool, ∀ l : List ℤ,
  connected (mapOf s) (relOf xa) (relOf xb) = true →
    commutes (mapOf s) (relOf xa) (relOf xb) (onComponents (relOf xb) l) = true) 292

/- TRN-14 control: without the connection, a citation whose ends land in two components keeps its
curvature on a locally constant cochain. -/
#eval refuted (∀ s : List (Fin 3), ∀ xa xb : List Bool, ∀ l : List ℤ,
  commutes (mapOf s) (relOf xa) (relOf xb) (onComponents (relOf xb) l) = true) 293

/- TRN-15: a transport bijective on notes, carrying exactly the source's citations, commutes with
`δ`: `σ^* δ' = δ σ^*`. -/
#eval survives (∀ k : ℕ, ∀ xa : List Bool, ∀ ψ : List ℤ,
  notes.all (fun a ↦ divZ (withImage (permOf k) (relOf xa) fun _ _ ↦ false) (eOf ψ) (permOf k a) ==
    divZ (relOf xa)
      (tE (permOf k) (relOf xa) (withImage (permOf k) (relOf xa) fun _ _ ↦ false) (eOf ψ)) a)
    = true) 294

/- TRN-15 control: a merge, still a chain map onto the image of the citations, does not. -/
#eval refuted (∀ s : List (Fin 3), ∀ xa : List Bool, ∀ ψ : List ℤ,
  notes.all (fun a ↦ divZ (withImage (mapOf s) (relOf xa) fun _ _ ↦ false) (eOf ψ) (mapOf s a) ==
    divZ (relOf xa)
      (tE (mapOf s) (relOf xa) (withImage (mapOf s) (relOf xa) fun _ _ ↦ false) (eOf ψ)) a)
    = true) 295

/- TRN-15 control: a bijection with a new citation at the later time does not either. -/
#eval refuted (∀ k : ℕ, ∀ xa xb : List Bool, ∀ ψ : List ℤ,
  notes.all (fun a ↦ divZ (withImage (permOf k) (relOf xa) (relOf xb)) (eOf ψ) (permOf k a) ==
    divZ (relOf xa)
      (tE (permOf k) (relOf xa) (withImage (permOf k) (relOf xa) (relOf xb)) (eOf ψ)) a)
    = true) 296

end Palace.Transport.Attack
