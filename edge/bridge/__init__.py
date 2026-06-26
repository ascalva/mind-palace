"""Zone B — research-airlock bridge (BUILD-SPEC §16; Invariant 2 & 11).

The only component that touches the airlock S3 bucket. It carries **de-identified criteria**
out and **public literature** in, as opaque JSON, over the filesystem handoff the sealed core
writes. It has no vault handle and the core never imports it — network and private data never
share a component.
"""

from edge.bridge.bridge import ResearchBridge, build_bridge
from edge.bridge.protocol import S3Client

__all__ = ["ResearchBridge", "S3Client", "build_bridge"]
