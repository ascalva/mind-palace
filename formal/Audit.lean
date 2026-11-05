import Palace

/-!
# Axiom audit

`lake env lean Audit.lean` lists the axioms behind every declaration in the `Palace` modules and
fails if any rests on an axiom other than Lean's three standard ones (`propext`,
`Classical.choice`, `Quot.sound`), or if more depend on `sorryAx` than `sorry-budget` allows: a
`sorry` the textual count misses (one a tactic or an option produced) is caught here, through the
environment (dn-mathematical-foundations §2.4). It reports the count it audited, which `check.sh`
holds the export's to.
-/

open Lean Elab Command

elab "#audit_palace" : command => do
  let env ← getEnv
  let standard := #[``propext, ``Classical.choice, ``Quot.sound]
  let budget := (String.ofList ((← IO.FS.readFile "sorry-budget").toList.filter Char.isDigit)).toNat!
  let mut checked : Nat := 0
  let mut sorried : Array Name := #[]
  let mut escapes : Array (Name × Name) := #[]
  for (name, _) in env.constants.map₁.toList do
    let some idx := env.getModuleIdxFor? name | continue
    let some mod := env.header.moduleNames[idx.toNat]? | continue
    unless (`Palace).isPrefixOf mod do continue
    checked := checked + 1
    for ax in ← liftCoreM (collectAxioms name) do
      if ax == ``sorryAx then sorried := sorried.push name
      else unless standard.contains ax do escapes := escapes.push (name, ax)
  unless escapes.isEmpty do
    throwError m!"axiom escape: {escapes.toList}"
  if sorried.size > budget then
    throwError m!"{sorried.size} declarations depend on sorry, past the budget {budget}: \
      {sorried.toList}"
  logInfo m!"{checked} declarations audited; non-standard axioms: none; \
    depending on sorry: {sorried.size} {sorried.toList}"

#audit_palace
