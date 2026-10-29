"""Local type stubs for `pyarrow.parquet` — see `stubs/pyarrow/__init__.pyi`."""

from os import PathLike

from pyarrow import Table

def read_table(source: str | PathLike[str]) -> Table: ...
