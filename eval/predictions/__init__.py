"""Pre-registered prediction experiments: the ledger, the scorer and the controls
(`docs/design-notes/dn-prediction-ledger.md`).

An experiment is one ledger file whose first record is its protocol: the arms it compares, the
families of questions it asks, the comparison that decides it and the bar it must clear. What an
experiment is about is its own business; nothing here knows. Machinery, not corpus: nothing under
`core/` imports this package, it opens no store, and it touches no network.
`python -m eval.predictions --help` for the commands.
"""

from eval.predictions.ledger import (
    Comparison,
    Ledger,
    LedgerCorrupt,
    LedgerError,
    Prediction,
    Protocol,
    Question,
    Resolution,
    Void,
)
from eval.predictions.scoring import Blinded, Growth, growth, growth_report, pilot, report, table

__all__ = [
    "Blinded",
    "Comparison",
    "Growth",
    "Ledger",
    "LedgerCorrupt",
    "LedgerError",
    "Prediction",
    "Protocol",
    "Question",
    "Resolution",
    "Void",
    "growth",
    "growth_report",
    "pilot",
    "report",
    "table",
]
