"""The id-mint migration — durable `id::` identity + version re-key (bp-034; oq-0019 B; §11 ruling).

The owner-run, offline, idempotent, reversible migrator that mints a durable Logseq `id::` into each
vault note lacking a stable id AND re-keys that note's version history from `source_path` to the
minted id, so no lineage forks at the identity switch — now or on any future rename (the A6 payoff,
temporal-retrieval-algebra.md §2.4). It mirrors `core/ingest/purge.py`: a deliberate, owner-gated
(`confirm=True`, fail-closed), offline act — NEVER the watcher's default, NEVER fired in a build
session. The owner runs it once, corpus-wide, with the daemon DOWN (a live-store migration is
deploy-coupled — finding-0066).

Three primitives + one orchestrator:
  * `preview()`  — Item 13: pure read. Enumerate the mint set (no-stable-id notes), the re-key plan,
                   and a pre-state manifest (per-chain `(seq, digest)`) for verification. Mutates
                   nothing.
  * `mint()`     — Item 15: byte-preserving `id:: <uuid4>` insertion (one line added, nothing else).
                   Idempotent-skip any note that already carries a stable id.
  * `run()`      — Item 16: backup → dry-run → [confirm] → PER-NOTE (mint-then-rekey) → rescan →
                   verify no lineage forked → report. Refuses unless the daemon is down.

Why per-note mint-then-rekey and not "re-key all stores, then mint all notes" (the §6 amendment):
the batch order has a crash window — a chain re-keyed to id₁ never written into its note, so a naive
re-run mints a fresh id₂ and orphans the id₁ chain. Minting a note FIRST, then re-keying that note's
chain from its ACTUAL state (its `id::` vs which key holds its chain), makes any interleaving
converge — the re-key `old` is always the note's `source_path` (a chain lives under either its
source_path, un-migrated, or its own id::, already migrated → CHECK ORDER (ii) no-op).

Zone A, no network (the seal holds); the script `scripts/mint_ids.py` is the owner-facing entry.
"""

from __future__ import annotations

import os
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from core.ingest.logseq import ParsedNote, iter_vault, parse_note
from core.ingest.sync import VaultSync
from core.stores.authored_supersession import OwnerDeclaration
from core.stores.versions import VersionStore


class MintRefusedError(RuntimeError):
    """The migration was refused by a safety gate — no `confirm`, a live daemon, or a note whose
    structure the byte-preserving minter cannot place an `id::` into safely (§10: never guess a
    format that could corrupt an authored note). The `PurgeRefusedError` pattern: fail-closed,
    named, never a silent partial write."""


# ── id detection (the skip decision + the re-key target) ───────────────────────────────────────
# Two notions, deliberately distinct:
#   * has_stable_id — for the MINT/skip decision: a Logseq `id::` OR a YAML `id:` front-matter key.
#     Either means "already identified" → the minter skips it (idempotent; keeps repo design-notes
#     and findings, already `id:`-stamped, untouched — parked decision 3).
#   * logseq_id     — the durable identity bp-031 RESOLUTION reads back (`properties['id']`), i.e.
#     the re-key TARGET. A YAML-only note has no `id::`, so it is skipped from re-keying too (it was
#     never on the id::-identity surface).


def logseq_id(parsed: ParsedNote) -> str | None:
    """The note's durable `id::` value (what bp-031 resolution reads back), or None if absent."""
    return parsed.properties.get("id") or None


def _yaml_front_matter(text: str) -> str | None:
    """The YAML front-matter block body if the note OPENS with one (`---` … `---`), else None."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def has_yaml_id(text: str) -> bool:
    """Does the note's YAML front-matter (if any) carry an `id:` key? Repo docs do (`id: dn-…`)."""
    fm = _yaml_front_matter(text)
    if fm is None:
        return False
    return any(line.split(":", 1)[0].strip() == "id" for line in fm.splitlines() if ":" in line)


def has_stable_id(parsed: ParsedNote) -> bool:
    """True if the note already carries a durable id — a Logseq `id::` OR a YAML `id:` — so the
    minter SKIPS it (idempotent). This is what keeps repo design-notes/findings untouched."""
    return logseq_id(parsed) is not None or has_yaml_id(parsed.text)


def _insert_id_line(raw: bytes, note_id: str) -> bytes:
    """Return `raw` with one `id:: <note_id>` Logseq page-property line prepended — byte-preserving
    except that single added line (everything else is untouched at the byte level). REFUSES a note
    that opens with a YAML front-matter block: mixing an `id::` into a `---` document is the
    ambiguous case §10 forbids guessing at — surface it (via the dry-run) rather than corrupt it."""
    if raw.lstrip()[:3] == b"---":
        raise MintRefusedError(
            "mint refused: note opens with a YAML front-matter block — id:: placement is ambiguous "
            "(§10); add `id:` to the front-matter by hand rather than let the minter guess."
        )
    return b"id:: " + note_id.encode("ascii") + b"\n" + raw


# ── plan structures ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NotePlan:
    """One note's place in the migration: where its chain lives now, and where it must end up."""
    source_path: str
    current_doc_id: str          # the doc_id its version chain is keyed under today (== source_path
                                 # unless a mechanism diverged it — usually == source_path here)
    target_id: str | None        # the durable id:: it should be filed under; None ⇒ to be minted
    action: str                  # "mint" | "rekey-only" | "skip"


@dataclass(frozen=True)
class ChainSnapshot:
    """A per-chain pre-state manifest (§4a): the `(version_seq, digest)` sequence, so verification
    checks CARRIED CONTENT equality (old key emptiness alone is necessary but not sufficient)."""
    doc_id: str
    rows: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class MigrationPlan:
    mint_set: tuple[str, ...]              # source_paths that will get an id:: minted
    rekey: tuple[NotePlan, ...]            # notes whose chain must move source_path → target id::
    skipped: tuple[str, ...]              # already-identified + correctly-filed notes (no work)
    pre_state: tuple[ChainSnapshot, ...]   # keyed by the note's CURRENT doc_id (§4a manifest)

    def pre_state_for(self, doc_id: str) -> tuple[tuple[int, str], ...]:
        for snap in self.pre_state:
            if snap.doc_id == doc_id:
                return snap.rows
        return ()


def preview(sync: VaultSync) -> MigrationPlan:
    """Item 13 — the migration's auditable plan, computed by PURE READ (opens no write handle,
    mutates no store or file). Enumerates: (a) the mint set — vault notes lacking a stable id — and
    (b) the re-key plan — for every in-scope note, `source_path → its durable id::` where the chain
    is not already filed there. Emits the §4a pre-state manifest so `run()` can verify carried
    content, not merely old-key emptiness."""
    catalog = sync.catalog
    versions = _require_versions(sync)
    mint_set: list[str] = []
    rekey: list[NotePlan] = []
    skipped: list[str] = []
    snaps: dict[str, tuple[tuple[int, str], ...]] = {}

    for path in iter_vault(sync.vault, pattern=sync.pattern, exclude_dirs=sync.exclude_dirs):
        parsed = parse_note(path, sync.vault)
        sp = parsed.source_path
        current = catalog.doc_id_for(sp)
        snaps[current] = tuple((v.version_seq, v.digest) for v in versions.history(current))
        lid = logseq_id(parsed)
        if lid is None and not has_yaml_id(parsed.text):
            mint_set.append(sp)
            rekey.append(NotePlan(sp, current, target_id=None, action="mint"))
        elif lid is not None and (current != lid or versions.current(sp) is not None):
            # carries an id:: but its chain is NOT yet filed under it (hand-added id, or unmigrated)
            rekey.append(NotePlan(sp, current, target_id=lid, action="rekey-only"))
        else:
            skipped.append(sp)                        # already identified + filed, or YAML-only

    pre_state = tuple(ChainSnapshot(doc_id=k, rows=v) for k, v in snaps.items() if v)
    return MigrationPlan(tuple(mint_set), tuple(rekey), tuple(skipped), pre_state)


def mint(sync: VaultSync, source_paths: tuple[str, ...] | list[str]) -> dict[str, str]:
    """Item 15 — insert a durable `id:: <uuid4>` into each named note, byte-preserving except the
    single added line. Idempotent-skip any note that gained a stable id since the preview (checked
    here). Writes ONLY under the vault (the caller passes vault-scoped source_paths). Returns the
    `source_path → minted id` map the re-key consumes."""
    minted: dict[str, str] = {}
    for sp in source_paths:
        path = Path(sp)
        parsed = parse_note(path, sync.vault)
        if has_stable_id(parsed):                     # gained an id since the preview → skip
            continue
        note_id = str(uuid.uuid4())                   # Logseq's own convention (parked decision 2)
        path.write_bytes(_insert_id_line(path.read_bytes(), note_id))
        minted[sp] = note_id
    return minted


@dataclass(frozen=True)
class MintReport:
    minted: dict[str, str] = field(default_factory=dict)   # source_path → newly minted id::
    rekeyed: int = 0                                        # notes whose chain moved to its id::
    rescan: str = ""                                        # the post-migration rescan tally
    verified: bool = False                                  # no lineage forked (the whole point)
    backup_dir: str = ""                                    # where pre-migration state was copied

    def __str__(self) -> str:
        return (f"minted={len(self.minted)} rekeyed={self.rekeyed} verified={self.verified} "
                f"rescan=({self.rescan}) backup={self.backup_dir}")


def run(sync: VaultSync, *, declaration: OwnerDeclaration, confirm: bool = False,
        backup_dir: Path, run_ledger: object | None = None) -> MintReport:
    """Item 16 — the offline, `confirm`-gated, reversible orchestration. Order (§6, the crash-safe
    per-note amendment):

        daemon-down + confirm gates → backup(vault + version/catalog stores) → dry-run plan →
        PER NOTE { mint id:: (if none) → re-key ITS chain source_path→id:: on both stores } →
        rescan → VERIFY no lineage forked (against the §4a manifest) → report.

    Fail-closed: refuses unless `confirm=True`, unless the daemon is down (a live daemon would race
    the re-key against the watcher's re-ingest — finding-0066), and unless every backup is readable
    + non-empty before any mutation. Reversible: `restore_from_backup(backup_dir, sync)` reproduces
    the pre-migration state exactly (the integration test rehearses this). The re-key is owner-
    authorized (`declaration`); a machine caller is refused at each store boundary."""
    catalog = sync.catalog
    versions = _require_versions(sync)

    if run_ledger is not None and _daemon_is_up(run_ledger):
        raise MintRefusedError(
            "mint refused: a live daemon is running — this is an OFFLINE migration (finding-0066). "
            "Bring it down first (`palace stop`, or launchctl bootout under KeepAlive)."
        )
    if not confirm:
        raise MintRefusedError(
            "mint_ids is owner-gated and writes the authored corpus — pass confirm=True to proceed "
            "(dry-run first via preview()/`--dry-run`)."
        )

    plan = preview(sync)                                     # §4a pre-state, before mutating
    _backup(sync, backup_dir)                                # §4c: copy + verify before any write

    minted: dict[str, str] = {}
    rekeyed = 0
    # The plan reflects the ACTUAL current state (nothing mutated since preview) — so a re-run after
    # a crash re-derives each note's target from its own id::, which is what makes it converge (§6).
    for np in plan.rekey:
        sp = np.source_path
        path = Path(sp)
        target = logseq_id(parse_note(path, sync.vault))
        if target is None:                                   # not yet minted → mint, then re-key
            note_id = str(uuid.uuid4())
            path.write_bytes(_insert_id_line(path.read_bytes(), note_id))
            minted[sp] = note_id
            target = note_id
        # Re-key THIS note's chain from its actual current key. `old = source_path` universally: a
        # chain lives under its source_path (unmigrated) or its own id:: (migrated → CHECK ORDER
        # (ii) no-op). Owner-gated on both stores; a merge/collision is refused, never silent.
        moved = versions.migrate_rekey_doc_id(sp, target, declaration=declaration)
        catalog.migrate_rekey_doc_id(sp, target, declaration=declaration)
        if moved:
            rekeyed += 1

    report = sync.rescan()                                   # the "id added" amendment lands here
    verified = _verify_no_fork(sync, plan)
    return MintReport(minted=minted, rekeyed=rekeyed, rescan=str(report), verified=verified,
                      backup_dir=str(backup_dir))


# ── verification (§4a: carried content, not just old-key emptiness) ─────────────────────────────

def _verify_no_fork(sync: VaultSync, plan: MigrationPlan) -> bool:
    """Every migrated note's history is ONE continuous chain under its durable id, with NO orphaned
    `source_path` chain, and the carried content (`(seq, digest)` prefix) equals the pre-migration
    manifest. This is the migration's one job — the falsifier is a surviving fork."""
    catalog = sync.catalog
    versions = _require_versions(sync)
    for np in plan.rekey:
        sp = np.source_path
        target = catalog.doc_id_for(sp)                      # the durable id it now resolves to
        if target == sp:
            return False                                     # never got a durable id (mint/rekey)
        if versions.current(sp) is not None:
            return False                                     # orphaned source_path chain (a FORK)
        pre = plan.pre_state_for(sp)                         # its chain snapshot under the old key
        post = tuple((v.version_seq, v.digest) for v in versions.history(target))
        if post[:len(pre)] != pre:                           # carried content must be a prefix
            return False
    return True


# ── reversibility: backup + restore (§4b/§4c) ──────────────────────────────────────────────────

_STORE_SUFFIXES = ("", "-wal", "-shm")                        # a WAL sqlite is 3 sidecar files


def _store_paths(sync: VaultSync) -> list[Path]:
    """The re-key targets to back up (versions + catalog sqlite). Vector/raw self-heal or are
    digest-safe (§3 Q1) and re-derive from raw via rescan, so they need no backup here."""
    return [_require_versions(sync).path, sync.catalog.path]


def _backup(sync: VaultSync, backup_dir: Path) -> None:
    """Copy the vault + the version/catalog stores to `backup_dir` BEFORE any mutation, and verify
    each copy is readable + non-empty (§4c). Daemon is down → no concurrent writer; a WAL checkpoint
    first folds the -wal into the main db so the copy is consistent."""
    vault_bak = backup_dir / "vault"
    stores_bak = backup_dir / "stores"
    stores_bak.mkdir(parents=True, exist_ok=True)
    _checkpoint(sync)
    for store_path in _store_paths(sync):
        for suffix in _STORE_SUFFIXES:
            src = Path(str(store_path) + suffix)
            if src.exists():
                shutil.copy2(src, stores_bak / src.name)
    shutil.copytree(sync.vault, vault_bak, dirs_exist_ok=True)
    # §4c: the backups must be readable + non-empty before we touch anything.
    for store_path in _store_paths(sync):
        copied = stores_bak / store_path.name
        if not copied.exists() or copied.stat().st_size == 0:
            raise MintRefusedError(f"mint refused: store backup {copied} is missing or empty")
    if not any(vault_bak.rglob("*")):
        raise MintRefusedError(f"mint refused: vault backup {vault_bak} is empty")


def restore_from_backup(backup_dir: Path, sync: VaultSync) -> None:
    """Reverse a migration: copy the backed-up stores + vault back over the live ones. The stores
    must be CLOSED first (SQLite holds the file); the caller re-opens after. The integration test
    exercises this to prove reversibility (§4b) — it is not merely asserted."""
    stores_bak = backup_dir / "stores"
    vault_bak = backup_dir / "vault"
    for store_path in _store_paths(sync):
        for suffix in _STORE_SUFFIXES:
            live = Path(str(store_path) + suffix)
            saved = stores_bak / (store_path.name + suffix)
            if saved.exists():
                shutil.copy2(saved, live)
            elif live.exists():
                live.unlink()                                # a -wal absent at backup time
    for existing in list(sync.vault.rglob("*")):
        if existing.is_file():
            existing.unlink()
    shutil.copytree(vault_bak, sync.vault, dirs_exist_ok=True)


# ── small internals ────────────────────────────────────────────────────────────────────────────

def _require_versions(sync: VaultSync) -> VersionStore:
    if sync.version_store is None:
        raise MintRefusedError("mint refused: VaultSync has no version_store (nothing to re-key)")
    return sync.version_store


def _checkpoint(sync: VaultSync) -> None:
    """Fold each store's WAL into its main db so a file copy is a consistent snapshot."""
    for store, attr in ((sync.catalog, "_conn"), (_require_versions(sync), "_conn")):
        conn = getattr(store, attr, None)
        if conn is not None:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.commit()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)                                      # signal 0 = liveness probe
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                                          # exists, owned by another user
    return True


def _daemon_is_up(run_ledger: object) -> bool:
    """Is a palace daemon LIVE? The run ledger's newest run is still active (never marked stopped)
    AND its pid is alive. A crashed run (active row, dead pid) counts as down — the migration may
    proceed (a crashed daemon is not racing us). Mirrors `launcher._pid_alive` + run ledger."""
    last = getattr(run_ledger, "last", lambda: None)()
    if last is None:
        return False
    return bool(getattr(last, "active", False)) and _pid_alive(int(getattr(last, "pid", -1)))
