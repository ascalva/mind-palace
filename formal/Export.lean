import LeanExport.Basic

/-!
# The library, exported

Writes to standard out the NDJSON export of every `Palace` declaration and everything it uses,
from `Init` up, in the format of Lean's `leanexport`. `check.sh` replays it from nothing through
Lean's kernel and the independent checkers bundled with Lean.

The compiler's `_unsafe_rec` helpers are left out: they implement recursive definitions for
compiled code only, no safe declaration can mention them, and nanoda refuses unsafe and partial
definitions outright.

The export checks itself before it writes, since a checker that accepts an empty export proves
nothing: every theorem `comparator.json` judges is among the declarations exported, every module
of the library contributes at least one, and what is left out is the unsafe helpers alone. It
reports its counts on standard error, and `check.sh` holds them to the axiom audit's.

Run: `lake env lean --run Export.lean > palace.ndjson` from `formal/`, after `lake build`.
-/

open Lean

def main : IO UInt32 := do
  initSearchPath (← findSysroot)
  let env ← importModules #[{ module := `Palace }] {}
  let mut palace : Array Name := #[]
  let mut leftOut : Nat := 0
  let mut modules : Std.HashSet Name := {}
  for (name, info) in env.constants.map₁.toList do
    let some idx := env.getModuleIdxFor? name | continue
    let some mod := env.header.moduleNames[idx.toNat]? | continue
    unless (`Palace).isPrefixOf mod do continue
    let safe : Bool := match info with
      | .defnInfo v => v.safety == DefinitionSafety.safe
      | _ => !info.isUnsafe
    if safe then
      palace := palace.push name
      modules := modules.insert mod
    else
      leftOut := leftOut + 1
  let exported : Std.HashSet Name := palace.foldl (·.insert ·) {}
  let judged ← match Json.parse (← IO.FS.readFile "comparator.json") with
    | .ok j => match j.getObjValAs? (Array String) "theorem_names" with
      | .ok names => pure (names.map String.toName)
      | .error e => throw (IO.userError s!"comparator.json: {e}")
    | .error e => throw (IO.userError s!"comparator.json: {e}")
  let missing := judged.filter (!exported.contains ·)
  let silent := env.header.moduleNames.filter fun m ↦
    (`Palace).isPrefixOf m && m != `Palace && !modules.contains m
  unless missing.isEmpty && silent.isEmpty do
    IO.eprintln s!"export incomplete: judged theorems not exported {missing.toList}; \
      modules with nothing exported {silent.toList}"
    return 1
  IO.eprintln s!"export: {palace.size} Palace declarations, {leftOut} unsafe left out; \
    the {judged.size} judged theorems and all {modules.size} modules among them"
  LeanExport.dumpEnv env palace.toList
  return 0
