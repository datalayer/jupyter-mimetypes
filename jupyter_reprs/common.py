from __future__ import annotations

import binascii
import logging
from typing import Any, Callable, TypeVar

import pyarrow as pa

GENERIC_REPR_METHOD = "_repr_mimebundle_"
ARROW_FILE_MIMETYPE = "application/vnd.apache.arrow.file"
ARROW_STREAM_MIMETYPE = "application/vnd.apache.arrow.stream"
DEFAULT_DATA_MIMETYPE = ARROW_STREAM_MIMETYPE

T = TypeVar("T")


logger = logging.getLogger("jupyter_reprs")


def format_object(
    obj,
    include=None,
    exclude=None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from IPython.core.interactiveshell import InteractiveShell

    if not InteractiveShell.initialized():
        return {}, {}

    format_dict = {}
    md_dict = {}

    for format_type, formatter in InteractiveShell.instance().display_formatter.formatters.items():
        if include and format_type not in include:
            continue
        if exclude and format_type in exclude:
            continue

        md = None
        data = formatter(obj)

        # formatters can return raw data or (data, metadata)
        if isinstance(data, tuple) and len(data) == 2:
            data, md = data

        if data is not None:
            format_dict[format_type] = data
        if md is not None:
            md_dict[format_type] = md
    return format_dict, md_dict


_FROM_ARROW_MAPPING: dict[str, Callable[[pa.Table], Any]] = {}


def _patch_repr_with_arrow(
    variable_type: type[T],
    to_arrow: Callable[[T], pa.Table],
    from_arrow: Callable[[pa.Table], T] | None = None,
) -> None:
    _old_repr = getattr(variable_type, GENERIC_REPR_METHOD, None)

    serialized_type = _get_serialized_type(variable_type)
    if from_arrow:
        _FROM_ARROW_MAPPING[".".join(str(s) for s in serialized_type)] = from_arrow

    def _new_repr(self, include=None, exclude=None):
        data, metadata = (
            format_object(self, include=include, exclude=exclude)
            if _old_repr is None
            else _old_repr(include=include, exclude=exclude)
        )

        if ARROW_STREAM_MIMETYPE in (
            include or {ARROW_STREAM_MIMETYPE}
        ) and ARROW_STREAM_MIMETYPE not in (exclude or set()):
            try:
                table = to_arrow(self)
                sink = pa.BufferOutputStream()

                with pa.ipc.new_stream(sink, table.schema) as writer:
                    writer.write_table(table)
                buffer = sink.getvalue()
                # Handle ourselves the encoding of bytes to avoid issue
                # Otherwise Jupyter kernel will encode bytes in a uncontrolled
                # way
                data[ARROW_STREAM_MIMETYPE] = binascii.b2a_base64(buffer.to_pybytes()).decode(
                    "utf-8"
                )
                metadata[ARROW_STREAM_MIMETYPE] = {"type": serialized_type}
            except BaseException as e:
                logger.debug("Failed to serialized '%s' to arrow stream.", self, exc_info=e)

        return data, metadata

    setattr(variable_type, GENERIC_REPR_METHOD, _new_repr)


def _get_serialized_type(variable_type: type) -> tuple[str | None, str]:
    """Serialize a Python type as tuple[module, name]."""
    return (
        getattr(variable_type, "__module__", None),
        variable_type.__qualname__,
    )


def mimebundle_to_object(bundle: tuple[dict, dict]) -> Any:
    data, metadata = bundle
    if ARROW_STREAM_MIMETYPE in data:
        raw = binascii.a2b_base64(data[ARROW_STREAM_MIMETYPE].encode("utf-8"))
        buf = pa.py_buffer(raw)
        variable_type = metadata.get(ARROW_STREAM_MIMETYPE, {}).get("type")
        from_arrow = _FROM_ARROW_MAPPING.get(".".join(str(s) for s in variable_type))
        with pa.ipc.open_stream(buf) as reader:
            if from_arrow is None:
                if (variable_type[0] or "").startswith("pandas."):
                    dataframe = reader.read_pandas()
                    if variable_type[1] == "Series":
                        return dataframe.get(dataframe.columns[0])
                    else:
                        return dataframe
            else:
                return from_arrow(reader.read_all())
