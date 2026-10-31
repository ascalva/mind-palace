import Plausible

/-!
# Counterexample attacks

Every L1 statement carries a Plausible attack (dn-mathematical-foundations §2.4): its executable
instance over exact arithmetic is run on random inputs before anyone tries to prove it.

Plausible's own suite reports success once a single instance passes its guards, so an attack whose
guard almost never holds looks the same as a thorough one. These helpers run the same sizes and
retries but count: `survives` fails the build on a counterexample and also when fewer than
`minTested` instances passed their guards. `refuted` is the negative control: it fails the build
unless a counterexample is found, which shows that an attack of the same shape catches a
mis-stated law. The seed is fixed, so a build is reproducible.
-/

open Plausible Plausible.Decorations

namespace Palace

/-- The attack configuration: a fixed seed and more instances than Plausible's default. -/
def attackConfig (seed : Nat) : Configuration :=
  { numInst := 500, randomSeed := some seed, quiet := true }

/-- What an attack saw: instances whose guards held, instances discarded, any counterexample. -/
structure Tally where
  tested : Nat := 0
  discarded : Nat := 0
  counterexample : Option (List String × Nat) := none

/-- Plausible's suite with counts: `cfg.numInst` instances of growing size, each retried until
its guards hold or `cfg.numRetries` runs out, stopping at the first counterexample. -/
def tally (p : Prop) [Testable p] (cfg : Configuration) : Gen Tally := do
  let mut t : Tally := {}
  for n in List.range cfg.numInst do
    let size := n * cfg.maxSize / cfg.numInst
    match ← retry ((Testable.runProp p cfg true).resize fun _ ↦ size) cfg.numRetries with
    | .success _ => t := { t with tested := t.tested + 1 }
    | .gaveUp _ => t := { t with discarded := t.discarded + 1 }
    | .failure _ xs shrinks => return { t with counterexample := some (xs, shrinks) }
  return t

/-- Run `tally` with `seed`. -/
def runTally (p : Prop) [Testable p] (seed : Nat) : IO Tally :=
  runRandWith seed (tally p (attackConfig seed))

/-- Attack `p`: the build fails on a counterexample, or when fewer than `minTested` instances
passed their guards. -/
def survives (p : Prop) (seed : Nat := 1) (minTested : Nat := 100)
    (p' : Decorations.DecorationsOf p := by mk_decorations) [Testable p'] :
    Lean.CoreM PUnit := do
  let t ← runTally p' seed
  if let some (xs, shrinks) := t.counterexample then
    Lean.throwError (Testable.formatFailure "attack found a counterexample" xs shrinks)
  if t.tested < minTested then
    Lean.throwError m!"attack too weak: guards held in {t.tested} of \
      {t.tested + t.discarded} instances, fewer than {minTested}"
  Lean.logInfo m!"attack survived: {t.tested} tested, {t.discarded} discarded, seed {seed}"

/-- Negative control: the build fails unless a counterexample to `p` is found. -/
def refuted (p : Prop) (seed : Nat := 1)
    (p' : Decorations.DecorationsOf p := by mk_decorations) [Testable p'] :
    Lean.CoreM PUnit := do
  let t ← runTally p' seed
  match t.counterexample with
  | some (xs, _) =>
    Lean.logInfo m!"control refuted, as it must be, after {t.tested} instances: {xs}"
  | none =>
    Lean.throwError m!"negative control not refuted in {t.tested} instances: \
      an attack of this shape has no teeth"

end Palace
