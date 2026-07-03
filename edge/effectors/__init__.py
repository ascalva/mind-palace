"""Zone B — the effector surface (Track G; hands-and-the-effector-layer.md).

Hands live HERE, never in the sealed core: anything that can ever touch the network belongs
in edge (CONVENTIONS). Sensing-only (β = 0) until the blast-radius classes above it are
earned (§4's graduated rollout); each effector is a reviewed native hand — re-implemented
in this repo, never live-installed third-party skill code (§1: mine the ecosystem, don't
adopt the runtime)."""

from edge.effectors.sensing import SensingEffector, build_sensing_effector

__all__ = ["SensingEffector", "build_sensing_effector"]
