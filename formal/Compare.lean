import Lean

/-!
# The comparator's comparison, in-process

`lake comparator` is the judge of `Spec` against `Palace` (`comparator.json`). It builds and
exports both in a `bwrap` sandbox, compares them, checks the axioms, and replays the solution
through the kernel, and CI runs it. macOS has no `bwrap`, so `check.sh` runs this there instead:
the comparison step of `Lake.Check.compareAt`, over the two environments `lake build` produced.
The axioms are `Audit.lean`'s check and the kernel replay is `leanchecker`'s.

Every theorem named in `comparator.json` must have the same statement (name, universe parameters
and type) in both environments, and every constant those statements reach, through types and
definition bodies, must be the same constant in both.

Run: `lake env lean --run Compare.lean` from `formal/`, after `lake build Palace Spec`.
-/

open Lean

/-- The constants a constant mentions, as `Lake.Check.runForUsedConsts` walks them: its type, and
its value when it has one. -/
def usedConsts (info : ConstantInfo) : Array Name :=
  info.type.getUsedConstants ++ ((info.value? (allowOpaque := true)).map (·.getUsedConstants)).getD #[]

/-- Compare the statements of `targets` and everything they reach. Returns how many constants were
compared. -/
def compare (challenge solution : Environment) (targets : Array Name) : Except String Nat := do
  let targetSet : NameSet := targets.foldl (·.insert ·) {}
  let mut work : Array Name := #[]
  for t in targets do
    let some c := challenge.find? t | throw s!"not in Spec: {t}"
    let some s := solution.find? t | throw s!"not in Palace: {t}"
    let (.thmInfo _, .thmInfo _) := (c, s) | throw s!"not a theorem on both sides: {t}"
    unless c.toConstantVal == s.toConstantVal do throw s!"statements differ: {t}"
    work := work ++ c.type.getUsedConstants
  let mut seen : NameSet := {}
  while h : work.size > 0 do
    let n := work.back
    work := work.pop
    if seen.contains n then continue
    seen := seen.insert n
    let some c := challenge.find? n | throw s!"not in Spec: {n}"
    let some s := solution.find? n | throw s!"not in Palace: {n}"
    if targetSet.contains n then
      work := work ++ s.type.getUsedConstants
    else
      unless c == s do throw s!"constants differ: {n}"
      work := work ++ usedConsts s
  return seen.size

def main : IO UInt32 := do
  initSearchPath (← findSysroot)
  let cfg ← IO.ofExcept <| Json.parse (← IO.FS.readFile "comparator.json")
  let names ← IO.ofExcept <| cfg.getObjValAs? (Array String) "theorem_names"
  let challenge ← importModules #[{ module := `Spec }] {}
  let solution ← importModules #[{ module := `Palace }] {}
  match compare challenge solution (names.map String.toName) with
  | .ok n =>
    IO.println s!"Spec ⇄ Palace: {names.size} statements identical, {n} constants compared"
    return 0
  | .error e =>
    IO.eprintln s!"Spec ⇄ Palace: {e}"
    return 1
