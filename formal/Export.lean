import LeanExport.Basic

/-!
# The library, exported

Writes to standard out the NDJSON export of every `Palace` declaration and everything it uses,
from `Init` up, in the format of Lean's `leanexport`. `check.sh` replays it from nothing through
Lean's kernel and the independent checkers bundled with Lean.

The compiler's `_unsafe_rec` helpers are left out: they implement recursive definitions for
compiled code only, no safe declaration can mention them, and nanoda refuses unsafe and partial
definitions outright.

Run: `lake env lean --run Export.lean > palace.ndjson` from `formal/`, after `lake build`.
-/

open Lean

def main : IO Unit := do
  initSearchPath (← findSysroot)
  let env ← importModules #[{ module := `Palace }] {}
  let palace := env.constants.map₁.toList.filterMap fun (name, info) => do
    let idx ← env.getModuleIdxFor? name
    let mod ← env.header.moduleNames[idx.toNat]?
    let safe := match info with
      | .defnInfo v => v.safety == .safe
      | _ => !info.isUnsafe
    if (`Palace).isPrefixOf mod && safe then some name else none
  LeanExport.dumpEnv env palace
