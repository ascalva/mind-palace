"""A fake sandbox runner for cold tests — exercises the pool/broker without Podman.

Records what it was asked to start/reset/destroy so tests can assert pool lifecycle behavior
(lazy warming, reuse, discard-on-unhealthy) deterministically.
"""

from __future__ import annotations

from core.sandbox import ExecResult


class FakeRunner:
    def __init__(self, result=None):
        self.result = result or ExecResult("out", "", 0)
        self.started, self.reset_calls, self.destroyed = [], [], []
        self._n = 0

    def available(self):
        return True

    def run_once(self, spec, policy):
        return self.result

    def start(self, policy, limits, image):
        self._n += 1
        cid = f"c{self._n}"
        self.started.append(cid)
        return cid

    def exec_in(self, container, spec):
        return self.result

    def reset(self, container):
        self.reset_calls.append(container)

    def destroy(self, container):
        self.destroyed.append(container)
