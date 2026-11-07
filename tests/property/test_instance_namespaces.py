"""The instance namespace map is injective, and Ouroboros's namespaces are reserved to it (DI-2).

N(i) is what instance i owns, read by `namespaces_of` off the config the real loader builds: its
data dir, ingestion spool, supervisor lock, levers file, exhaust lane and every other path it
writes; the sources it reads (vault, transcripts, dialogue lanes); the Keychain items it reads; its
launchd labels; its backup repository; its Vault server. The invariant: for instances i ≠ j,
Ouroboros among them, `shared(N(i), N(j))` is empty, where every location compares as a location
(one inside the other counts as shared). Ids are generated, not chosen; the named instances
declare nothing.

The controls give the check teeth. With the loader's own refusal switched off, five broken
derivations each fail the property: one that ignores the id, one that hands a named instance
Ouroboros's namespaces (the hazard of issue #25), and three under which an undeclared vault,
exhaust lane or Vault server falls back to Ouroboros's (#25 in the read direction, reports landing
in Ouroboros's lane, a named instance reaching Ouroboros's Vault). With the refusal on, the loader
refuses the last four itself.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import Phase, given, settings
from hypothesis import strategies as st

from core.kernel.config import loader

IDS = st.from_regex(loader._INSTANCE_ID, fullmatch=True).filter(lambda s: s != loader.OUROBOROS)
OUROBOROS_REPOSITORY = "s3:s3.us-east-1.amazonaws.com/example-ouroboros-backups"
NAMED_BASE = "s3:s3.us-east-1.amazonaws.com/example-instance-backups"


def _declare(tmp: Path, ids: list[str]) -> None:
    """Declare exactly these named instances on the host: one overlay each under the config dir's
    instances/, where the loader looks for every other instance when it loads one."""
    declared = tmp / "config" / "instances"
    declared.mkdir(parents=True, exist_ok=True)
    for old in declared.glob("*.toml"):
        old.unlink()
    for iid in ids:
        (declared / f"{iid}.toml").write_text(f'[instance]\nid = "{iid}"\n'
                                              f'[backup]\nrepository = "{NAMED_BASE}/{iid}"\n')


def _namespaces(tmp: Path, instance_id: str | None) -> loader.Namespaces:
    """N(instance) from the real loader, Ouroboros's when `instance_id` is None. A named load also
    checks itself against every other declared instance (`_declare`)."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(loader, "_CONFIG_DIR", tmp / "config")
        mp.setattr(loader, "_INSTANCE_OVERLAY", tmp / "ouroboros.toml")
        mp.setattr(loader, "LEVERS_OVERLAY", tmp / "levers.toml")
        mp.delenv(loader.OVERLAY_ENV, raising=False)
        if instance_id is not None:
            mp.setenv(loader.OVERLAY_ENV, str(tmp / "config" / "instances" / f"{instance_id}.toml"))
        return loader.namespaces_of(loader.load_config())


def _disjoint(of: dict[str, loader.Namespaces]) -> None:
    for i, a in of.items():
        assert loader.shared(a, a), f"{i} shares nothing with itself, so the check is vacuous"
    for (i, a), (j, b) in itertools.combinations(of.items(), 2):
        both = loader.shared(a, b)
        assert not both, f"{i} and {j} share {both}"


def _the_property(tmp: Path, *, min_named: int, shrink: bool = True) -> Callable[[], None]:
    (tmp / "ouroboros.toml").write_text(f'[backup]\nrepository = "{OUROBOROS_REPOSITORY}"\n')
    phases = tuple(Phase) if shrink else (Phase.explicit, Phase.generate)

    @settings(max_examples=40, deadline=None, database=None, phases=phases)
    @given(st.lists(IDS, min_size=min_named, max_size=3, unique=True))
    def holds(ids: list[str]) -> None:
        _declare(tmp, ids)                    # side by side: each load checks the others too
        of = {loader.OUROBOROS: _namespaces(tmp, None)}
        of |= {i: _namespaces(tmp, i) for i in ids}
        _disjoint(of)

    return holds


def test_the_namespace_map_is_injective_and_ouroboros_reserved(tmp_path) -> None:
    _the_property(tmp_path, min_named=1)()


def test_the_namespace_map_is_injective_over_pairs_of_named_ids(tmp_path) -> None:
    """At least two named instances declared on one host: every pair of them is disjoint, and the
    loader, which checks each against all the others, loads every one."""
    _the_property(tmp_path, min_named=2)()


def _ignore_the_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """A broken derivation: every named instance gets one root, one item prefix, one label."""
    def root(self: loader.InstanceConfig) -> Path:
        return loader.REPO_ROOT / "instances" / "one" if self.named else loader.REPO_ROOT

    monkeypatch.setattr(loader.InstanceConfig, "root", property(root))
    monkeypatch.setattr(loader.InstanceConfig, "secret",
                        lambda self, name: f"one.{name}" if self.named else name)
    monkeypatch.setattr(loader.InstanceConfig, "label",
                        lambda self, role: loader.LABEL_PREFIX + (f"one.{role}" if self.named
                                                                  else role))


def _be_ouroboros(monkeypatch: pytest.MonkeyPatch) -> None:
    """The hazard of issue #25 as a derivation: a named instance gets Ouroboros's namespaces."""
    monkeypatch.setattr(loader.InstanceConfig, "root", property(lambda self: loader.REPO_ROOT))
    monkeypatch.setattr(loader.InstanceConfig, "secret", lambda self, name: name)
    monkeypatch.setattr(loader.InstanceConfig, "label",
                        lambda self, role: loader.LABEL_PREFIX + role)


def _inherit_ouroboros_vault(monkeypatch: pytest.MonkeyPatch) -> None:
    """The read-direction hazard as a derivation: an undeclared vault falls back to the committed
    default, which is Ouroboros's vault root."""
    default = Path(loader._read(loader._DEFAULTS)["ingestion"]["vault"]["path"]).expanduser()
    real = loader._own_source
    monkeypatch.setattr(loader, "_own_source",
                        lambda instance, name: default if name == "vault" else real(instance, name))


def _inherit_ouroboros_lane(monkeypatch: pytest.MonkeyPatch) -> None:
    """The exhaust lane falling back to the committed default, which is Ouroboros's lane."""
    default = Path(loader._read(loader._DEFAULTS)["exhaust"]["path"]).expanduser()
    real = loader._own_source
    monkeypatch.setattr(loader, "_own_source",
                        lambda instance, name: default if name == "exhaust"
                        else real(instance, name))


def _inherit_ouroboros_vault_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """A named instance that names no Vault falling back to the committed default address, the
    Vault on this host, which is Ouroboros's."""
    default = str(loader._read(loader._DEFAULTS)["secrets"]["addr"])
    monkeypatch.setattr(loader, "_own_vault_addr", lambda instance: default)


@pytest.mark.parametrize(("break_it", "min_named", "shared_what"), [
    (_ignore_the_id, 2, "location"),
    (_be_ouroboros, 1, "location"),
    (_inherit_ouroboros_vault, 1, r"location \S*\.mind-palace/vault and"),
    (_inherit_ouroboros_lane, 1, r"location \S*\.mind-palace/exhaust and"),
    (_inherit_ouroboros_vault_server, 1, "Vault server loopback:8200"),
])
def test_control_a_broken_derivation_fails_the_property(monkeypatch, tmp_path, break_it,
                                                        min_named, shared_what) -> None:
    break_it(monkeypatch)
    monkeypatch.setattr(loader, "_refuse_shared", lambda cfg, source: None)
    with pytest.raises(AssertionError, match=shared_what):   # a failure needs no shrinking here
        _the_property(tmp_path, min_named=min_named, shrink=False)()


@pytest.mark.parametrize("break_it", [_be_ouroboros, _inherit_ouroboros_vault,
                                      _inherit_ouroboros_lane, _inherit_ouroboros_vault_server])
def test_control_the_loader_refuses_the_hazard_itself(monkeypatch, tmp_path, break_it) -> None:
    break_it(monkeypatch)
    (tmp_path / "ouroboros.toml").write_text(f'[backup]\nrepository = "{OUROBOROS_REPOSITORY}"\n')
    _declare(tmp_path, ["bench"])
    with pytest.raises(loader.InstanceOverlayError, match="would share"):
        _namespaces(tmp_path, "bench")


def test_control_the_loader_refuses_two_named_instances_one_derivation(monkeypatch,
                                                                       tmp_path) -> None:
    """With the id ignored, two declared named instances collide with each other though neither
    touches Ouroboros: the loader, checking each against the other, refuses."""
    _ignore_the_id(monkeypatch)
    (tmp_path / "ouroboros.toml").write_text(f'[backup]\nrepository = "{OUROBOROS_REPOSITORY}"\n')
    _declare(tmp_path, ["one", "two"])
    with pytest.raises(loader.InstanceOverlayError, match="would share these with 'two'"):
        _namespaces(tmp_path, "one")


@settings(max_examples=60, deadline=None, database=None)
@given(IDS, st.sampled_from(["", "/"]))
def test_no_named_instance_writes_ouroboros_repository(tmp_path_factory, iid, slash) -> None:
    """Ouroboros's repository, or a location inside it, refuses outright for any id; a location of
    the instance's own beside it loads."""
    tmp = tmp_path_factory.mktemp("repo")
    (tmp / "ouroboros.toml").write_text(f'[backup]\nrepository = "{OUROBOROS_REPOSITORY}"\n')
    for repository in (OUROBOROS_REPOSITORY + slash, f"{OUROBOROS_REPOSITORY}/{iid}{slash}"):
        overlay = tmp / "named.toml"
        overlay.write_text(f'[instance]\nid = "{iid}"\n[backup]\nrepository = "{repository}"\n')
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(loader, "_INSTANCE_OVERLAY", tmp / "ouroboros.toml")
            mp.setenv(loader.OVERLAY_ENV, str(overlay))
            with pytest.raises(loader.InstanceOverlayError):
                loader.load_config()
    own = f"{OUROBOROS_REPOSITORY}-instances/{iid}{slash}"
    overlay.write_text(f'[instance]\nid = "{iid}"\n[backup]\nrepository = "{own}"\n')
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(loader, "_INSTANCE_OVERLAY", tmp / "ouroboros.toml")
        mp.setenv(loader.OVERLAY_ENV, str(overlay))
        assert loader.load_config().backup.repository == own


def _spellings(a: int) -> list[str]:
    """Ways to write the IPv4 address `a` that the C resolver's inet_aton reads as `a`."""
    b = a.to_bytes(4, "big")
    return [".".join(map(str, b)), str(a), hex(a), "0" + format(a, "o"),
            f"{b[0]}.{a & 0xFFFFFF}", f"{b[0]}.{b[1]}.{a & 0xFFFF}",
            ".".join(hex(x) for x in b), ".".join("0" + format(x, "o") for x in b),
            str(a + (1 << 32))]


@settings(max_examples=300, deadline=None, database=None)
@given(st.integers(0, 0xFFFFFFFF))
def test_every_ipv4_spelling_is_one_host(a) -> None:
    """Every spelling of one IPv4 address is one host, this machine's addresses one loopback; the
    parse agrees with the platform's own `inet_aton` on each spelling the platform accepts. The
    last spelling wraps past 32 bits: BSD's `inet_aton` (macOS) reads its low bits, glibc's
    refuses it, and the parse keeps BSD's reading, the wider of the two."""
    import ipaddress
    import socket

    expected = ("loopback" if ipaddress.IPv4Address(a).is_loopback or a == 0
                else str(ipaddress.IPv4Address(a)))
    for spelling in _spellings(a):
        assert loader._canonical_host(spelling) == expected, spelling
        if len(spelling) < 20:
            try:
                packed = socket.inet_aton(spelling)
            except OSError:      # glibc refuses the wrapped spelling; nothing on it to compare
                continue
            assert int.from_bytes(packed, "big") == a, spelling
