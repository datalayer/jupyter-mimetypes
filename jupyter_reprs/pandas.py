from __future__ import annotations

import logging

import pyarrow as pa

from .common import _patch_repr_with_arrow

logger = logging.getLogger("jupyter_kernels")


def _patch_pandas():
    import pandas

    # Patch pandas.DataFrame
    _patch_repr_with_arrow(pandas.DataFrame, pa.Table.from_pandas)

    # Patch pandas.Series
    _patch_repr_with_arrow(
        pandas.Series,
        lambda s: pa.Table.from_arrays([pa.Array.from_pandas(s)], names=[str(s.name)]),
    )


try:
    _patch_pandas()
except ImportError:
    ...
