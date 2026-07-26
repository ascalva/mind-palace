"""Zone A — model serving (BUILD-SPEC §5, §7).

Two lifecycles kept separate: the *model* lifecycle (pull/update + the two-slot loader)
lives here; the *agent* lifecycle (the factory + registry) arrives in Phase 5. Nothing
is baked into Ollama — personas and params are injected at request time.
"""

from core.models.inference import InferenceClient, build_inference_client
from core.models.llama_server_client import (
    ContextOverflowError,
    LlamaServerClient,
    LlamaServerError,
)
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import Message, OllamaClient, OllamaError
from core.models.registry import MemoryCeilingError, Registry, get_registry
from core.models.server import ModelServer, build_model_server

__all__ = [
    "ContextOverflowError",
    "InferenceClient",
    "LlamaServerClient",
    "LlamaServerError",
    "Message",
    "MemoryCeilingError",
    "ModelServer",
    "OllamaClient",
    "OllamaError",
    "Registry",
    "TwoSlotLoader",
    "build_inference_client",
    "build_model_server",
    "get_registry",
]
