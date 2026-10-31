import Palace

/-!
# Axiom audit

`lake env lean Audit.lean` lists the axioms behind every declaration in the `Palace` modules and
fails if any rests on an axiom other than Lean's three standard ones (`propext`,
`Classical.choice`, `Quot.sound`) or on `sorryAx`. It reports how many depend on `sorry`; the
budget in `sorry-budget` caps the textual count (dn-mathematical-foundations §2.4).
-/

open Lean Elab Command

elab "#audit_palace" : command => do
  let env ← getEnv
  let standard := #[``propext, ``Classical.choice, ``Quot.sound]
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
  logInfo m!"{checked} declarations audited; non-standard axioms: none; \
    depending on sorry: {sorried.size} {sorried.toList}"

#audit_palace
